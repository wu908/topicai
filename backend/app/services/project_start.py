"""Conversational project start (创建流程重构 R1).

用户在「开始一条内容」里只需要给**一句话**或**选一条已有素材**。
意图由模型从原料推断（不是让用户从固定枚举里选），并只回问**一个**
最有信息量的问题。模型不可用时降级为「不猜意图」——把意图留空交给
既有确认步骤，而不是塞一个默认值。

为什么这样设计（详见 docs/reviews/content-creation-flow-first-principles-2026-09-14.md）：
- 意图是系统的路由键（决定后续问题/素材清单/观察信号），让用户选等于
  让他替系统做数据建模，且后果在选择那刻不可见；
- 起点信息量太低是"到处都要问"的根本原因，所以入口接收件箱素材；
- 抽象结论（"希望读者发生什么变化"）不该在入口问，它由材料推导。
"""

import asyncio
import logging
from typing import Any, Literal

from pydantic import Field

from app.models.v2.content_project import ContentProjectCreate
from app.models.v2.intent_actions import StrictModel
from app.models.v2.project_start import (
    ProjectStartInference,
    ProjectStartRequest,
    ProjectStartView,
)
from app.services.content_project import ContentProjectService

logger = logging.getLogger(__name__)

#: 从素材起步时，素材默认私有——与「素材授权默认最小」的产品承诺一致：
#: 素材本身不公开，只有生成出来的内容才面向读者。
_DEFAULT_MATERIAL_PRIVACY = "private"


class _StartInference(StrictModel):
    """模型必须回的结构化推断。"""

    intent: Literal["solve", "share", "record"]
    reason: str = Field(min_length=1, max_length=200)
    confidence: Literal["high", "medium", "low"] = "medium"
    next_question: str = Field(min_length=1, max_length=200)


_START_SYSTEM_PROMPT = (
    "你是内容创作助手的意图判断模块。用户给你一句话或一条素材，你要判断"
    "这条内容最接近哪种意图，并指出现在最该问用户的**一个**问题。\n"
    "意图只有三类：\n"
    "- solve（解决）：教方法、讲怎么做到、解决一个具体问题\n"
    "- share（分享）：讲经历与感受、表达观点、展示作品或成果\n"
    "- record（记录）：记录一个过程、变化或进展\n"
    "规则：\n"
    "1. reason 用一句用户看得懂的话说明判断依据，不要用「意图」「路由」这类内部词。\n"
    "2. next_question 只问一个，且必须是**答了会改变接下来怎么写**的问题；\n"
    "   问具体的事（哪件事、卡在哪一步、试过什么），不要问抽象命题。\n"
    "3. 如果原料里已经有一个具体场景/细节，就直接围绕它追问，不要重复索要。\n"
    "4. 展示作品类内容没有「转折瞬间」，不要问改变看法之类的叙事问题。\n"
    "只输出一个 JSON 对象，不要解释、不要 Markdown 代码块。字段严格如下：\n"
    '{"intent":"share","reason":"听起来是分享一段真实经历",'
    '"confidence":"medium","next_question":"这件事里哪一步最费劲？"}'
)


class ProjectStartService:
    """「开始一条内容」：原料 → 推断 → 建项目（+ 挂素材）。"""

    def __init__(self, db: Any, llm: Any = None):
        self.db = db
        self.llm = llm

    async def _resolve_material(
        self, owner: str, body: ProjectStartRequest
    ) -> dict[str, Any] | None:
        """把请求解析成一段原料；来自收件箱时返回该素材行。"""
        if not body.inbox_item_id:
            return None
        row = await self.db.fetch_one(
            "SELECT * FROM inbox_items WHERE id=:id AND owner_user_id=:owner",
            {"id": body.inbox_item_id, "owner": owner},
        )
        if row is None:
            raise ValueError("inbox item not found")
        return row

    async def _infer(self, raw: str) -> ProjectStartInference:
        """推断意图与下一个问题；失败则给出不猜意图的降级结果。"""
        from app.core.llm import LLMClient, wrap_user_input

        llm = self.llm or LLMClient()
        try:
            draft = await asyncio.to_thread(
                llm.generate_structured,
                f"用户的内容原料：{wrap_user_input(raw)}",
                _StartInference,
                _START_SYSTEM_PROMPT,
                temperature=0.3,
            )
            return ProjectStartInference(
                intent=draft.intent,
                intent_label={"solve": "解决", "share": "分享", "record": "记录"}[
                    draft.intent
                ],
                reason=draft.reason,
                confidence=draft.confidence,
                next_question=draft.next_question,
                source="ai",
            )
        except Exception:
            # 降级：不猜意图（宁可空着让用户确认，也不塞一个可能错的默认值）
            logger.warning("Project start inference failed; not guessing", exc_info=True)
            return ProjectStartInference(
                intent=None,
                intent_label="",
                reason="这次没判断出来——不猜，你说了算。",
                confidence="low",
                next_question="这条内容里，哪个具体的事或结果是你最想说的？",
                source="deterministic_fallback",
            )

    async def start(self, owner: str, body: ProjectStartRequest) -> ProjectStartView:
        item = await self._resolve_material(owner, body)
        raw = (
            (item["content"] or item["title"] or "")
            if item is not None
            else (body.raw_input or "")
        ).strip()
        if not raw:
            raise ValueError("content source is empty")

        inference = await self._infer(raw)

        # 标题由原料提炼：用户不需要先给内容起名。
        title = (item["title"] if item is not None and item["title"] else raw[:40]).strip()
        created, _ = await ContentProjectService(self.db).create(
            owner,
            ContentProjectCreate(
                title=title,
                # 推断出意图就带上（工作台据此选问题集）；没推断出就留空，
                # 由既有的"确认内容目的"步骤让用户定。
                **({"content_intent": inference.intent} if inference.intent else {}),
                # 推断记录（R2）：状态机据此跳过重复的意图确认，并用这个
                # 针对当前材料的问题替代按意图固定的通用问题。
                **(
                    {
                        "start_inferred_intent": inference.intent,
                        "start_inferred_question": inference.next_question,
                        "start_inference_confidence": inference.confidence,
                    }
                    if inference.intent
                    else {}
                ),
                idempotency_key=body.idempotency_key,
            ),
        )

        material_id = None
        if item is not None:
            material_id = await self._attach_material(owner, created["id"], item)

        return ProjectStartView(
            project_id=created["id"],
            title=created["title"],
            inference=inference,
            material_id=material_id,
        )

    async def _attach_material(
        self, owner: str, project_id: str, item: Any
    ) -> str:
        """把收件箱素材挂到项目上——这样第一方证据进了溯源链，
        AI 后续就不用再向用户索要一遍。"""
        from app.models.v2.material import MaterialCreate
        from app.services.material import MaterialService

        material, _ = await MaterialService(self.db).create(
            owner,
            MaterialCreate(
                kind="text",
                title=(item["title"] or (item["content"] or "")[:40]).strip() or "收件箱素材",
                content=item["content"],
                privacy_level=_DEFAULT_MATERIAL_PRIVACY,
                project_id=project_id,
                idempotency_key=f"start-material-{item['id']}",
            ),
        )
        return material["id"]
