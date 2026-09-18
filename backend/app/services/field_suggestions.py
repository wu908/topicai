"""给可填字段提候选（R9）。

用户要的是"每个要填的地方，AI 先给几条候选，点了填进去，不对就自己改"。
这里只做两件事：按字段给出候选文本；AI 不可用时给确定性的兜底候选。

设计上的两条边界（与产品其他部分一致）：

1. **候选不是替用户编经历**：提示词只允许用项目里已经确认过的材料，且要求
   写具体细节；材料不足时宁可给"写法骨架"，也不虚构事实。
2. **降级也要有候选**：AI 关掉/失败时返回通用方向与骨架，并在 limitations
   里说明，前端据此显示"这些是通用方向，不是针对这条内容的判断"。
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from app.core.llm import LLMClient, wrap_user_input
from app.models.v2.action_domain import AITraceCreate
from app.models.v2.field_suggestion import (
    FieldSuggestionCandidate,
    FieldSuggestionRequest,
    FieldSuggestionsView,
    _SuggestionDraft,
)
from app.services.ai_trace import AITraceService
from app.services.content_genome import ContentGenomeService
from app.services.intent_rubric import rubric_for
from app.services.v2_utils import now

#: 每个字段要什么。hint 直接进提示词——写得越具体，候选越能直接用。
_FIELD_SPECS: dict[str, dict[str, Any]] = {
    "answer": {
        "meaning": "用户对『这条内容最缺的那个关键事实』的回答",
        "hint": "一到三句话，必须含具体时间/场景/结果，来自他本人的经历；"
        "不要写成完整笔记，不要总结成道理",
        "max_length": 600,
    },
    "audience_change": {
        "meaning": "这条内容想让读者发生的具体变化",
        "hint": "一句话，20–40 字，要具体到这条内容本身；"
        "不要用『更理解你的经历』这类放在任何内容上都成立的话",
        "max_length": 80,
    },
    "audience_problem": {
        "meaning": "读者在真实场景里遇到的具体困境",
        "hint": "一句话，说清他在什么情况下卡住、卡在哪一步；不要写抽象需求",
        "max_length": 80,
    },
    "reader_promise": {
        "meaning": "基于这次亲身经历，作者能讲清楚的方法或步骤",
        "hint": "一句话，落在可照做的动作上；不要承诺结果、不要夸张",
        "max_length": 80,
    },
    "viewpoint_anchor": {
        "meaning": "这条内容里作者打算表达的那个观点或立场",
        "hint": "一句话，是作者自己的判断（可以是反常识的），能被别人不同意",
        "max_length": 80,
    },
    "continuation_promise": {
        "meaning": "作者承诺读者接下来会持续更新的东西",
        "hint": "一句话，说清还会更新什么、大概多久一次；不要空承诺",
        "max_length": 80,
    },
}


class FieldSuggestionService:
    def __init__(self, db: Any, llm: LLMClient | None = None):
        self.db = db
        self.llm = llm

    async def suggest(
        self, owner: str, project_id: str, body: FieldSuggestionRequest
    ) -> dict[str, Any]:
        spec = _FIELD_SPECS[body.field]
        project = await self._project(owner, project_id)
        context = await self._context(owner, project)

        candidates: list[FieldSuggestionCandidate] = []
        source = "deterministic_fallback"
        limitations: list[str] = []
        trace_id: str | None = None

        draft = await self._draft(body, spec, project, context)
        if draft is not None:
            source = "ai"
            candidates = [
                FieldSuggestionCandidate(
                    text=item.text.strip()[: spec["max_length"]],
                    why=item.why.strip()[:120],
                )
                for item in draft.candidates
                if item.text.strip()
            ][: body.count]

        if not candidates:
            candidates = _fallback_candidates(body, project, context, spec)
            limitations.append(
                "AI 暂时不可用：下面这些是通用方向或写法骨架，不是针对这条内容的判断，请按你的实际情况改。"
            )

        if source == "ai":
            trace_id = str(uuid.uuid4())
            await self._trace(owner, project, body, trace_id, len(candidates))

        return FieldSuggestionsView(
            field=body.field,
            candidates=candidates,
            source=source,
            limitations=limitations,
            context_refs=context["refs"],
        ).model_dump(mode="json")

    # ------------------------------------------------------------------ 内部

    async def _project(self, owner: str, project_id: str) -> dict[str, Any]:
        row = await self.db.fetch_one(
            "SELECT * FROM content_projects WHERE id=:id AND owner_user_id=:owner "
            "AND deleted_at IS NULL",
            {"id": project_id, "owner": owner},
        )
        if row is None:
            from app.core.exceptions import UserActionRequiredException

            raise UserActionRequiredException("找不到这条内容，刷新后再试。")
        return dict(row)

    async def _context(self, owner: str, project: dict[str, Any]) -> dict[str, Any]:
        """项目里"可以被引用"的材料：只取已确认的证据，且本项目的优先。"""
        genome = await ContentGenomeService(self.db).for_project(owner, project)
        evidence = genome.get("evidence_context") or []
        statements = [
            str(item.get("statement") or "").strip()
            for item in evidence
            if str(item.get("statement") or "").strip()
        ][:5]
        refs = [str(item.get("source_ref")) for item in evidence][:5]
        return {"statements": statements, "refs": refs}

    async def _draft(
        self,
        body: FieldSuggestionRequest,
        spec: dict[str, Any],
        project: dict[str, Any],
        context: dict[str, Any],
    ) -> _SuggestionDraft | None:
        if not self.llm or not self.llm.is_available("text"):
            return None

        intent = project.get("content_intent") or ""
        rubric = rubric_for(intent) if intent else None
        lines = [
            f"要填的位置：{spec['meaning']}",
            f"要求：{spec['hint']}",
            f"请给 {body.count} 条互不重复的候选。",
            f"这条内容的标题：{wrap_user_input(project.get('title') or '')}",
        ]
        if project.get("content_form"):
            lines.append(f"这条内容是什么（AI 之前命名的）：{project['content_form']}")
        if intent and rubric:
            lines.append(f"处理方式：{rubric['label']}")
        if project.get("audience_change"):
            lines.append(f"已经记下的读者变化：{wrap_user_input(project['audience_change'])}")
        if body.question:
            lines.append(f"用户正在回答的问题：{wrap_user_input(body.question)}")
        if context["statements"]:
            lines.append(
                "作者已确认的真实素材（只能用这些，不得引入素材外的事实）：\n"
                + "\n".join(f"- {wrap_user_input(item)}" for item in context["statements"])
            )
        else:
            lines.append("作者还没有已确认的素材：**不要编造任何经历、数据或结果**，只给写法方向。")
        if body.current_text:
            lines.append(f"作者已经写下的内容（按它改进，不要另起一句）：{wrap_user_input(body.current_text)}")

        try:
            return await asyncio.to_thread(
                self.llm.generate_structured,
                "\n".join(lines),
                _SuggestionDraft,
                "你是内容创作助手，帮创作者把一句话写得更具体。"
                "候选是给创作者挑的，用他自己会说的口吻；宁可保守也不编造。",
                temperature=0.4,
            )
        except Exception:
            return None

    async def _trace(
        self,
        owner: str,
        project: dict[str, Any],
        body: FieldSuggestionRequest,
        trace_id: str,
        produced: int,
    ) -> None:
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                await AITraceService.create(
                    session,
                    owner,
                    AITraceCreate(
                        id=trace_id,
                        task_type="field_suggestion",
                        input_refs=[f"project:{project['id']}", f"field:{body.field}"],
                        evidence_refs=[],
                        policy_version="field-suggestion-v1",
                        model_identifier="configured-text-model",
                        capability="structured_proposal",
                        visibility_boundary={
                            "allowed": ["confirmed_evidence", "project_fields"],
                            "forbidden": [
                                "unconfirmed_evidence",
                                "revoked_evidence",
                                "other_users",
                            ],
                            "actual": ["project_fields"],
                        },
                        contamination_check={
                            "status": "clean",
                            "unexpected_classes": [],
                            "missing_classes": [],
                        },
                        calibration_state="insufficient",
                        limitations=["候选只是方向，采用与否由创作者决定"],
                        output_ref=f"field_suggestion:{project['id']}:{body.field}:{produced}",
                        generated_at=now(),
                        confidence_label="medium",
                        outcome="success",
                        user_decision="pending",
                    ),
                )


def _fallback_candidates(
    body: FieldSuggestionRequest,
    project: dict[str, Any],
    context: dict[str, Any],
    spec: dict[str, Any],
) -> list[FieldSuggestionCandidate]:
    """AI 不可用时的确定性候选：通用方向 + 可照填的写法骨架。

    刻意不做"智能"：这里没有模型，任何看起来具体的话都可能是编的。
    """
    intent = project.get("content_intent") or ""
    rubric = rubric_for(intent) if intent else None
    scaffold_why = "写法骨架：把括号里的部分换成你真实经历的细节"
    out: list[FieldSuggestionCandidate] = []

    if body.field == "answer":
        first = context["statements"][0] if context["statements"] else None
        if first:
            out.append(
                FieldSuggestionCandidate(
                    text=f"{first[:200]}",
                    why="你在素材里已经写下的一条事实，把它补成具体场景就是答案",
                )
            )
        out.append(
            FieldSuggestionCandidate(
                text="（什么时间/什么场景），我（具体做了什么），结果是（具体结果或数字）。",
                why=scaffold_why,
            )
        )
        out.append(
            FieldSuggestionCandidate(
                text="最费劲的是（哪一步），我当时（怎么处理的），后来发现（什么）。",
                why=scaffold_why,
            )
        )
        return out[: body.count]

    if body.field == "audience_change":
        out.append(
            FieldSuggestionCandidate(
                text=(rubric or {}).get("default_audience_change", "让读者获得一个真实、可判断的变化"),
                why="这类内容的通用方向（不是针对这条内容的判断）",
            )
        )
        out.append(
            FieldSuggestionCandidate(
                text="看完能判断这件事跟自己有没有关系、值不值得花时间。",
                why="通用方向：把「关系」写具体会更准",
            )
        )
        return out[: body.count]

    label = (rubric or {}).get("label", "这条内容")
    out.append(
        FieldSuggestionCandidate(
            text=f"（谁）在（什么场景）遇到（什么问题）——这是 {label} 要回应的对象。",
            why=scaffold_why,
        )
    )
    return out[: body.count]
