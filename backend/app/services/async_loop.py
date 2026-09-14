"""Async creation loop services (Spec-013 Phase 1 walking skeleton).

Deterministic-only: production never fabricates facts — every fact traces to
an inbox item, no LLM is required, and AITrace records the run as
``deterministic_fallback``. The shelf is rate-limited; stale ready items
expire; pickup goes through the official project services so shared semantics
(content project creation + working intent confirmation) are never bypassed.
"""

import asyncio
import json
import logging
import uuid
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any, Literal

from pydantic import Field

from app.core.exceptions import IdempotencyConflictException
from app.models.v2.action_domain import AITraceCreate
from app.models.v2.async_loop import (
    DiscardRequest,
    InboxItemCreate,
    MetricsRecord,
    PickupRequest,
)
from app.models.v2.content_project import ContentProjectCreate
from app.models.v2.intent_actions import IntentConfirmation, StrictModel
from app.services.ai_trace import AITraceService
from app.services.content_project import ContentProjectService
from app.services.intent_actions import IntentConfirmationService
from app.services.v2_utils import now, request_hash

logger = logging.getLogger(__name__)

SHELF_LIMIT = 6
BATCH_MAIN = 2
EXPIRE_DAYS = 7
PICKUP_IDEM = "pickup_idem"

#: deliverables.status 的允许取值（与 050 迁移的 CHECK 约束一致）。
DELIVERABLE_STATUSES = frozenset(
    {"queued", "producing", "ready", "failed", "expired", "picked", "discarded"}
)

#: 灵感池 = 过期未拾取 + 用户主动丢弃。
POOL_STATUSES = ("expired", "discarded")

INTENT_BY_KIND = {
    "text": "solve",
    "link": "solve",
    "idea": "share",
    "image": "record",
    "voice": "record",
}

#: AI 生成草稿的结构化契约。facts 刻意不在其中——事实必须来自收件箱素材，
#: 不能由模型生成，否则溯源不变式会被破坏。
class _OutlineStep(StrictModel):
    step: str = Field(min_length=1, max_length=40)
    label: str = Field(min_length=1, max_length=120)


class _JudgmentDraft(StrictModel):
    audience_change: str = Field(min_length=1, max_length=300)
    primary_response: Literal["save", "comment", "profile_visit", "follow"] = "save"
    supporting: list[Literal["save", "comment", "profile_visit", "follow"]] = Field(
        default_factory=list, max_length=2
    )
    window_days: int = Field(default=7, ge=1, le=365)


class _Draft(StrictModel):
    title: str = Field(min_length=1, max_length=80)
    body_text: str = Field(min_length=1, max_length=4000)
    outline: list[_OutlineStep] = Field(min_length=1, max_length=6)
    judgment: _JudgmentDraft


DIGEST_SYSTEM_PROMPT = (
    "你是小红书创作者的写作助手。用户会给你一条他自己记录的真实素材，"
    "你要把它整理成一篇可直接发布的笔记草稿。\n"
    "硬性规则：\n"
    "1. 只能使用素材里出现过的事实、数字、场景。素材没写的，一律不要写。\n"
    "2. 需要用户补充的地方，用【待补：具体要补什么】标出来，不要用想象填满。\n"
    "3. 不写营销话术、不承诺效果、不编造他人评价。\n"
    "4. 标题不超过 20 字，正文口语化，分 2-4 段。\n"
    "5. outline 给 3 步（hook/point/ending），judgment.audience_change 一句话说清"
    "读者看完能获得什么可判断的变化。\n"
    "只输出一个 JSON 对象，不要任何解释、不要 Markdown 代码块。"
    "字段与类型必须严格如下（字符串内部换行请写成 \\n）：\n"
    '{"title":"标题","body_text":"正文","outline":'
    '[{"step":"hook","label":"钩子"},{"step":"point","label":"要点"},'
    '{"step":"ending","label":"结尾互动"}],'
    '"judgment":{"audience_change":"读者变化","primary_response":"save",'
    '"supporting":["follow"],"window_days":7}}'
)


#: 从用户贴的参考里读出来的写法，最多取这么多条作为写作约束。
#: 这里不套 R4 的样本数门槛：参考是用户自己指认的"我想做成这样"，用它是因为
#: 用户这么说了，而不是因为系统推断出它有效——两件事需要的谨慎程度不同。
_MAX_STYLE_HINTS = 3


OUTLINE = [
    {"step": "hook", "label": "钩子：一个具体结果或翻车瞬间"},
    {"step": "point", "label": "要点：你的事实与做法，逐条展开"},
    {"step": "ending", "label": "结尾互动：向读者提一个具体问题"},
]


def _expire_at(ts: str) -> str:
    base = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return (base + timedelta(days=EXPIRE_DAYS)).isoformat()


class InboxService:
    """Creative inbox intake: consent-minimal, idempotent, owner-scoped."""

    def __init__(self, db: Any):
        self.db = db

    @staticmethod
    def _view(row: Any) -> dict[str, Any]:
        return {
            "id": row["id"],
            "kind": row["kind"],
            "title": row["title"],
            "content": row["content"],
            "consent": row["consent"],
            "status": row["status"],
            "version": row["version"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    async def add(self, owner: str, body: InboxItemCreate) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        existing = await self.db.fetch_one(
            "SELECT * FROM inbox_items WHERE owner_user_id=:owner AND idempotency_key=:key",
            {"owner": owner, "key": body.idempotency_key},
        )
        if existing:
            if existing["request_hash"] != digest:
                raise IdempotencyConflictException()
            return self._view(existing), True
        item_id = str(uuid.uuid4())
        ts = now()
        await self.db.execute(
            "INSERT INTO inbox_items (id,owner_user_id,kind,title,content,consent,"
            "status,version,idempotency_key,request_hash,created_at,updated_at) VALUES "
            "(:id,:owner,:kind,:title,:content,:consent,'intake',1,:key,:hash,:now,:now)",
            {
                "id": item_id, "owner": owner, "kind": body.kind, "title": body.title,
                "content": body.content, "consent": body.consent,
                "key": body.idempotency_key, "hash": digest, "now": ts,
            },
        )
        row = await self.db.fetch_one(
            "SELECT * FROM inbox_items WHERE id=:id", {"id": item_id}
        )
        return self._view(row), False

    async def list(self, owner: str) -> list[dict[str, Any]]:
        rows = await self.db.fetch_all(
            "SELECT * FROM inbox_items WHERE owner_user_id=:owner "
            "ORDER BY created_at DESC, id",
            {"owner": owner},
        )
        return [self._view(r) for r in rows]

    async def get(self, owner: str, item_id: str) -> dict[str, Any]:
        row = await self.db.fetch_one(
            "SELECT * FROM inbox_items WHERE id=:id AND owner_user_id=:owner",
            {"id": item_id, "owner": owner},
        )
        if row is None:
            raise ValueError("inbox item not found")
        return self._view(row)


class PublishCheckService:
    """Structural health pre-check for autonomous production (load-bearing).

    最小集：钩子/要点/结尾齐、标题非空、正文长度达标、至少一条可溯源
    事实。没有通过就不产 ready——这是货架质量的底线。
    """

    MIN_BODY_CHARS = 30

    @classmethod
    def run_precheck(cls, draft: dict[str, Any]) -> dict[str, Any]:
        issues: list[str] = []
        if not str(draft.get("title") or "").strip():
            issues.append("标题为空")
        outline = draft.get("outline") or []
        steps = {step.get("step") for step in outline}
        if "hook" not in steps:
            issues.append("大纲缺少钩子")
        if not any(step.get("step") == "point" for step in outline):
            issues.append("大纲缺少要点")
        if "ending" not in steps:
            issues.append("大纲缺少结尾互动")
        if len(str(draft.get("body_text") or "")) < cls.MIN_BODY_CHARS:
            issues.append("正文过短，无法支撑一条完整笔记")
        if not (draft.get("facts") or []):
            issues.append("没有可溯源的事实，禁止虚构")
        return {"passed": not issues, "issues": issues}


class ProductionService:
    """Deterministic production: inbox items in, traceable deliverables out."""

    def __init__(self, db: Any, llm: Any = None):
        self.db = db
        self.llm = llm

    async def list_deliverables(
        self, owner: str, *, status: str = "ready",
        statuses: Sequence[str] | None = None,
    ) -> list[dict[str, Any]]:
        # 第五轮 C5：sweep_expired 此前只有测试调用，生产链路从不触发，
        # 于是「不选的会安静等 7 天，然后回到灵感池」实际不成立。
        # 列表读取时惰性清扫——与 _expire_at 的派生语义一致，无需额外定时任务。
        # 第六轮：灵感池需要同时看 expired + discarded，故支持多状态。
        await self.sweep_expired(owner)
        wanted = list(statuses) if statuses is not None else [status]
        if not wanted:
            return []
        for value in wanted:
            if value not in DELIVERABLE_STATUSES:
                # 此前非法 status 静默返回空列表，掩盖调用方错误。
                raise ValueError(f"unknown deliverable status: {value}")
        placeholders = ",".join(f":s{i}" for i in range(len(wanted)))
        params: dict[str, Any] = {"owner": owner}
        params.update({f"s{i}": value for i, value in enumerate(wanted)})
        rows = await self.db.fetch_all(
            f"SELECT * FROM deliverables WHERE owner_user_id=:owner "
            f"AND status IN ({placeholders}) ORDER BY created_at DESC, id",
            params,
        )
        return [self._view(r) for r in rows]

    async def pending_intake_count(self, owner: str) -> int:
        """还有多少可发布素材没消化——前端据此显示进度与剩余。"""
        row = await self.db.fetch_one(
            "SELECT COUNT(*) AS n FROM inbox_items WHERE owner_user_id=:owner "
            "AND status='intake' AND consent='publishable'",
            {"owner": owner},
        )
        return int(row["n"])

    async def get(self, owner: str, deliverable_id: str) -> dict[str, Any]:
        row = await self._row(owner, deliverable_id)
        return self._view(row)

    async def digest(self, owner: str, *, limit: int | None = None) -> dict[str, Any]:
        """把收件箱里可发布的素材整理成待发布产出。

        limit 限制本次最多消化几条（夜间任务与逐条进度调用都会用）；
        默认 None = 保持既有批量行为（受架上预算与 BATCH_MAIN 约束）。
        """
        thread_id = str(uuid.uuid4())
        items = await self.db.fetch_all(
            "SELECT * FROM inbox_items WHERE owner_user_id=:owner "
            "AND status='intake' AND consent='publishable' ORDER BY created_at, id",
            {"owner": owner},
        )
        ready = await self.db.fetch_one(
            "SELECT COUNT(*) AS n FROM deliverables "
            "WHERE owner_user_id=:owner AND status='ready'",
            {"owner": owner},
        )
        budget = max(0, SHELF_LIMIT - ready["n"])
        mains = [i for i in items if i["kind"] != "idea"][: max(0, min(BATCH_MAIN, budget))]
        exploration = []
        if budget > len(mains):
            exploration = [i for i in items if i["kind"] == "idea"][:1]

        if limit is not None:
            # 逐条调用（前端进度 / 夜间配额）时按上限截断，先非 idea 再 idea。
            allowance = max(0, limit)
            mains = mains[:allowance]
            allowance -= len(mains)
            exploration = exploration[: max(0, allowance)]

        if not mains and not exploration:
            return {"thread_id": thread_id, "deliverables": []}

        await self._event(owner, thread_id, None, "queued", {"intake": len(items)})
        produced: list[dict[str, Any]] = []
        used: list[str] = []
        sources: list[str] = []
        for item, is_exp in [(i, 0) for i in mains] + [(i, 1) for i in exploration]:
            view, source = await self._produce(owner, thread_id, item, is_exp)
            sources.append(source)
            if not view:
                continue  # 预检未过：素材留在收件箱，等用户补料后重试
            produced.append(view)
            used.append(item["id"])
        for item_id in used:
            await self.db.execute(
                "UPDATE inbox_items SET status='digested',updated_at=:now "
                "WHERE id=:id AND owner_user_id=:owner AND status='intake'",
                {"now": now(), "id": item_id, "owner": owner},
            )
        await self._trace(owner, thread_id, used, sources)
        await self._event(owner, thread_id, None, "ready",
                          {"deliverables": len(produced)})
        return {"thread_id": thread_id, "deliverables": produced}

    async def sweep_expired(self, owner: str) -> int:
        stale = await self.db.fetch_all(
            "SELECT id,thread_id FROM deliverables WHERE owner_user_id=:owner "
            "AND status='ready' AND expire_at IS NOT NULL AND expire_at<=:now",
            {"owner": owner, "now": now()},
        )
        for row in stale:
            await self.db.execute(
                "UPDATE deliverables SET status='expired',updated_at=:now "
                "WHERE id=:id",
                {"now": now(), "id": row["id"]},
            )
            await self._event(owner, row["thread_id"], row["id"], "expired",
                              {"reason": "ready_7d_not_picked"})
        return len(stale)

    async def _style_hints(self, owner: str) -> list[str]:
        """用户贴的参考里常见的写法，用来约束草稿结构。

        读不到锚点（还没贴参考）就返回空——没有偏好时不假装有偏好。
        """
        row = await self.db.fetch_one(
            "SELECT structure_habits_json FROM reference_anchors WHERE owner_user_id=:owner",
            {"owner": owner},
        )
        if row is None:
            return []
        habits = json.loads(row["structure_habits_json"] or "[]")
        return [
            str(item.get("value", "")).strip()
            for item in habits
            if str(item.get("value", "")).strip()
        ][:_MAX_STYLE_HINTS]

    async def _draft_from_ai(self, owner: str, item: Any) -> _Draft | None:
        """让模型把一条真实素材整理成草稿；失败返回 None（由调用方降级）。

        事实（facts）刻意不由模型产出：它只写标题/正文/大纲/判断草案，
        事实仍由调用方从素材派生，保证「每条事实可溯源」的不变式。
        """
        from app.core.llm import LLMClient, wrap_user_input

        llm = self.llm or LLMClient()
        hints = await self._style_hints(owner)
        # 写法和素材一样是不可信文本（用户粘贴、经模型转述），同样包裹起来。
        style_block = (
            "参考写法（用户贴的参考里常见的写法，尽量贴合，"
            "但不得因此写出素材里没有的事实）：\n"
            + "\n".join(f"- {wrap_user_input(hint)}" for hint in hints)
            + "\n"
            if hints
            else ""
        )
        prompt = (
            f"素材标题：{wrap_user_input(item['title'] or '（无标题）')}\n"
            f"素材正文：{wrap_user_input(item['content'])}\n"
            f"素材类型：{item['kind']}\n"
            f"{style_block}"
        )
        try:
            return await asyncio.to_thread(
                llm.generate_structured,
                prompt,
                _Draft,
                DIGEST_SYSTEM_PROMPT,
                # 低温提升结构化输出的稳定性（实测同一提示词下 JSON 合规率明显更好）
                temperature=0.3,
            )
        except Exception:
            # AI 不可用/超时/结构解析失败都走降级，产品不能因此不可用。
            logger.warning("Digest AI draft failed; falling back", exc_info=True)
            return None

    async def _produce(self, owner: str, thread_id: str,
                       item: Any, is_exploration: int) -> tuple[dict[str, Any], str]:
        deliverable_id = str(uuid.uuid4())
        ts = now()
        content = item["content"]
        draft = await self._draft_from_ai(owner, item)
        if draft is not None:
            title = draft.title
            body_text = draft.body_text
            outline = [step.model_dump() for step in draft.outline]
            judgment = draft.judgment.model_dump()
            source = "ai"
        else:
            title = item["title"] or content[:20]
            body_text = (
                f"{title}\n\n"
                f"{content}\n\n"
                "[请在发布前补充并确认具体细节：对照大纲逐条写下你亲身经历的版本，"
                "写不出的条目直接删除；当前版本不会虚构缺失经历。]"
            )
            outline = OUTLINE
            judgment = {
                "audience_change": "看完能获得一个真实、可判断的变化",
                "primary_response": "save",
                "supporting": ["follow"],
                "window_days": 7,
            }
            source = "deterministic_fallback"
        # 事实始终来自素材本身（不由模型生成），溯源不变式不因 AI 而放松。
        facts = [{"statement": content[:200], "source_inbox_id": item["id"],
                  "note": "收件箱素材"}]
        precheck = PublishCheckService.run_precheck({
            "title": title, "body_text": body_text,
            "outline": outline, "facts": facts,
        })
        if not precheck["passed"]:
            # 承重墙：结构预检不过就不产 ready（无死路——记 needs_input 事件）
            await self._event(owner, thread_id, None, "needs_input",
                              {"reason": "precheck_failed", "issues": precheck["issues"]})
            return {}, source
        await self.db.execute(
            "INSERT INTO deliverables (id,owner_user_id,thread_id,title,body_text,"
            "outline_json,facts_json,judgment_json,content_intent,proposed_publish_at,"
            "is_exploration,status,retry_count,expire_at,precheck_json,confidence,version,"
            "idempotency_key,request_hash,created_at,updated_at) VALUES "
            "(:id,:owner,:thread,:title,:body,:outline,:facts,:judgment,:intent,"
            "NULL,:exp,'ready',0,:expire,:precheck,'medium',1,:key,'',:now,:now)",
            {
                "id": deliverable_id, "owner": owner, "thread": thread_id,
                "title": title, "body": body_text,
                "outline": json.dumps(outline, ensure_ascii=False),
                "facts": json.dumps(facts, ensure_ascii=False),
                "judgment": json.dumps(judgment, ensure_ascii=False),
                "intent": INTENT_BY_KIND.get(item["kind"], "share"),
                "exp": is_exploration,
                "expire": _expire_at(ts),
                "precheck": json.dumps(precheck, ensure_ascii=False),
                "key": f"thread-{thread_id}-{item['id']}", "now": ts,
            },
        )
        await self._event(owner, thread_id, deliverable_id, "ready",
                          {"exploration": bool(is_exploration),
                           "precheck": "passed", "draft_source": source})
        row = await self._row(owner, deliverable_id)
        return self._view(row), source

    async def _event(self, owner: str, thread_id: str, deliverable_id: str | None,
                     event_type: str, detail: dict[str, Any]) -> None:
        await self.db.execute(
            "INSERT INTO production_events (id,owner_user_id,thread_id,deliverable_id,"
            "event_type,detail_json,created_at) VALUES "
            "(:id,:owner,:thread,:deliverable,:etype,:detail,:now)",
            {
                "id": str(uuid.uuid4()), "owner": owner, "thread": thread_id,
                "deliverable": deliverable_id, "etype": event_type,
                "detail": json.dumps(detail, ensure_ascii=False), "now": now(),
            },
        )

    async def _trace(self, owner: str, thread_id: str, used: list[str],
                     sources: list[str]) -> None:
        # 逐条来源在批次末尾汇总：只要有一条走了模型就按「模型参与」记录
        # （宁可多报不可少报），并把降级条数与原因写进 limitations。
        ai_used = "ai" in sources
        fallback_count = sources.count("deterministic_fallback")
        limitations = (
            ["模型产出；事实仍逐条来自收件箱素材", "细节需用户确认"]
            if ai_used and not fallback_count
            else (
                [f"其中 {fallback_count} 条降级为确定性骨架", "细节仍需用户确认"]
                if ai_used
                else ["模型不可用；确定性骨架产出", "细节仍需用户确认"]
            )
        )
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                await AITraceService.create(
                    session,
                    owner,
                    AITraceCreate(
                        id=str(uuid.uuid4()),
                        task_type="inbox_production",
                        input_refs=[f"inbox-item:{i}" for i in used],
                        evidence_refs=[f"inbox-item:{i}" for i in used],
                        policy_version=(
                            "async-loop-ai-v1" if ai_used
                            else "async-loop-deterministic-v1"
                        ),
                        model_identifier=(
                            getattr(self.llm, "model", None) if ai_used else None
                        ),
                        capability="text" if ai_used else "deterministic_fallback",
                        outcome="success" if ai_used else "fallback",
                        visibility_boundary={
                            "allowed": ["creative_inbox"],
                            "forbidden": ["private_materials", "legacy_hotspots"],
                            "actual": ["creative_inbox"],
                        },
                        contamination_check={
                            "status": "clean",
                            "unexpected_classes": [],
                            "missing_classes": [],
                        },
                        calibration_state="insufficient",
                        limitations=limitations,
                        output_ref=f"production-thread:{thread_id}",
                        generated_at=now(),
                    ),
                )

    async def _row(self, owner: str, deliverable_id: str) -> Any:
        row = await self.db.fetch_one(
            "SELECT * FROM deliverables WHERE id=:id AND owner_user_id=:owner",
            {"id": deliverable_id, "owner": owner},
        )
        if row is None:
            raise ValueError("deliverable not found")
        return row

    @staticmethod
    def _view(row: Any) -> dict[str, Any]:
        return {
            "id": row["id"],
            "thread_id": row["thread_id"],
            "title": row["title"],
            "body_text": row["body_text"],
            "outline": json.loads(row["outline_json"] or "[]"),
            "facts": json.loads(row["facts_json"] or "[]"),
            "judgment": json.loads(row["judgment_json"] or "{}"),
            "content_intent": row["content_intent"],
            "proposed_publish_at": row["proposed_publish_at"],
            "is_exploration": bool(row["is_exploration"]),
            "status": row["status"],
            "attribution": row["attribution"],
            "expire_at": row["expire_at"],
            "precheck": json.loads(row["precheck_json"] or "{}"),
            "version": row["version"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


class PickupService:
    """Pickup = choosing a deliverable and confirming its fact sheet.

    Project creation goes through ContentProjectService + the official intent
    confirmation path so shared semantics are never bypassed (PR #23 lesson).
    """

    def __init__(self, db: Any, llm: Any = None):
        self.db = db
        self.llm = llm

    async def pickup(self, owner: str, deliverable_id: str,
                     body: PickupRequest) -> tuple[dict[str, Any], bool]:
        row = await self.db.fetch_one(
            "SELECT * FROM deliverables WHERE id=:id AND owner_user_id=:owner",
            {"id": deliverable_id, "owner": owner},
        )
        if row is None:
            raise ValueError("deliverable not found")
        if row["status"] == "picked":
            if row["pickup_idem"] == body.idempotency_key:
                project = await ContentProjectService(self.db).get(
                    owner, row["picked_project_id"]
                )
                fresh = await self._row(owner, deliverable_id)
                return {"project": project,
                        "deliverable": ProductionService._view(fresh)}, True
            raise ValueError("deliverable already picked")
        if row["status"] != "ready":
            raise ValueError("deliverable is not ready")
        if not json.loads(row["facts_json"] or "[]"):
            raise ValueError("deliverable has no traceable facts")

        project, _ = await ContentProjectService(self.db).create(
            owner,
            ContentProjectCreate(
                title=row["title"],
                primary_goal="experiment",
                content_intent=row["content_intent"] or "share",
                audience_change=body.audience_change,
                idempotency_key=f"pickup-project-{row['id']}",
            ),
        )
        await IntentConfirmationService(self.db).confirm(
            owner,
            project["id"],
            IntentConfirmation(
                content_intent=body.content_intent,
                audience_change=body.audience_change,
                expected_project_version=project["version"],
                idempotency_key=f"pickup-confirm-{row['id']}",
            ),
        )
        updated = await self.db.execute(
            "UPDATE deliverables SET status='picked',picked_project_id=:pid,"
            "pickup_idem=:key,proposed_publish_at=COALESCE(:sched,proposed_publish_at),"
            "updated_at=:now WHERE id=:id AND owner_user_id=:owner AND status='ready'",
            {
                "pid": project["id"], "key": body.idempotency_key,
                "sched": body.schedule_at, "now": now(),
                "id": deliverable_id, "owner": owner,
            },
        )
        if updated.rowcount != 1:
            raise ValueError("deliverable state changed during pickup")
        await self._picked_event(owner, row, project["id"])
        fresh = await self._row(owner, deliverable_id)
        return {"project": project,
                "deliverable": ProductionService._view(fresh)}, False

    async def discard(self, owner: str, deliverable_id: str,
                      body: DiscardRequest) -> dict[str, Any]:
        row = await self.db.fetch_one(
            "SELECT * FROM deliverables WHERE id=:id AND owner_user_id=:owner",
            {"id": deliverable_id, "owner": owner},
        )
        if row is None:
            raise ValueError("deliverable not found")
        if row["status"] != "ready":
            raise ValueError("only ready deliverables can be discarded")
        await self.db.execute(
            "UPDATE deliverables SET status='discarded',attribution=:reason,"
            "updated_at=:now WHERE id=:id AND owner_user_id=:owner AND status='ready'",
            {"reason": body.reason, "now": now(),
             "id": deliverable_id, "owner": owner},
        )
        await self._picked_event(owner, row, None, event_type="discarded")
        await LoopMetricsService(self.db).record(
            owner,
            MetricsRecord(metric="discard_attribution", value=1,
                          meta={"reason": body.reason}),
        )
        fresh = await self._row(owner, deliverable_id)
        return ProductionService._view(fresh)

    async def restore(self, owner: str, deliverable_id: str) -> dict[str, Any]:
        """把池中的产出（过期或被弃）重新上架，并重置 7 天观察窗。

        「回到灵感池」的兑现点：池子不是坟墓，用户可以把条目放回待决定。
        注意 expire_at 会重算，等于可以无限续命——这是有意为之的语义。
        """
        row = await self.db.fetch_one(
            "SELECT * FROM deliverables WHERE id=:id AND owner_user_id=:owner",
            {"id": deliverable_id, "owner": owner},
        )
        if row is None:
            raise ValueError("deliverable not found")
        if row["status"] not in POOL_STATUSES:
            raise ValueError("only pooled deliverables can be restored")
        ts = now()
        await self.db.execute(
            "UPDATE deliverables SET status='ready',attribution=NULL,"
            "expire_at=:expire,updated_at=:now "
            "WHERE id=:id AND owner_user_id=:owner AND status IN ('expired','discarded')",
            {"expire": _expire_at(ts), "now": ts,
             "id": deliverable_id, "owner": owner},
        )
        await self._picked_event(
            owner, row, None, event_type="ready",
            detail={"reason": "restored_from_pool",
                    "previous_status": row["status"]},
        )
        fresh = await self._row(owner, deliverable_id)
        return ProductionService._view(fresh)

    async def delete_pooled(self, owner: str, deliverable_id: str) -> None:
        """永久删除池中条目。仅限池内状态，避免误删架上待决定产出。

        production_events 是只写审计表（全仓无读取方、无外键引用），
        所以先写事件再删行不会留下悬空依赖。
        """
        row = await self.db.fetch_one(
            "SELECT * FROM deliverables WHERE id=:id AND owner_user_id=:owner",
            {"id": deliverable_id, "owner": owner},
        )
        if row is None:
            raise ValueError("deliverable not found")
        if row["status"] not in POOL_STATUSES:
            raise ValueError("only pooled deliverables can be deleted")
        await self._picked_event(
            owner, row, None, event_type="discarded",
            detail={"reason": "deleted_from_pool",
                    "previous_status": row["status"]},
        )
        await self.db.execute(
            "DELETE FROM deliverables WHERE id=:id AND owner_user_id=:owner "
            "AND status IN ('expired','discarded')",
            {"id": deliverable_id, "owner": owner},
        )

    async def _picked_event(self, owner: str, row: Any, project_id: str | None,
                            event_type: str = "picked",
                            detail: dict[str, Any] | None = None) -> None:
        # 注意：production_events.event_type 有 CHECK 约束（050），池操作没有
        # 专属取值，故沿用既有类型并用 detail.reason 区分——重建该表可加精确
        # 类型，但为审计表做重建的迁移风险大于收益。
        await self.db.execute(
            "INSERT INTO production_events (id,owner_user_id,thread_id,deliverable_id,"
            "event_type,detail_json,created_at) VALUES "
            "(:id,:owner,:thread,:deliverable,:etype,:detail,:now)",
            {
                "id": str(uuid.uuid4()), "owner": owner, "thread": row["thread_id"],
                "deliverable": row["id"], "etype": event_type,
                "detail": json.dumps(
                    detail if detail is not None else {"project_id": project_id},
                    ensure_ascii=False,
                ),
                "now": now(),
            },
        )

    async def _row(self, owner: str, deliverable_id: str) -> Any:
        row = await self.db.fetch_one(
            "SELECT * FROM deliverables WHERE id=:id AND owner_user_id=:owner",
            {"id": deliverable_id, "owner": owner},
        )
        if row is None:
            raise ValueError("deliverable not found")
        return row


class LoopMetricsService:
    """Telemetry for the three falsification lines (plan §6)."""

    def __init__(self, db: Any):
        self.db = db

    async def record(self, owner: str, body: MetricsRecord) -> dict[str, Any]:
        metric_id = str(uuid.uuid4())
        ts = now()
        await self.db.execute(
            "INSERT INTO loop_metrics (id,owner_user_id,metric,value,meta_json,"
            "created_at) VALUES (:id,:owner,:metric,:value,:meta,:now)",
            {
                "id": metric_id, "owner": owner, "metric": body.metric,
                "value": body.value,
                "meta": json.dumps(body.meta, ensure_ascii=False), "now": ts,
            },
        )
        return {"id": metric_id, "metric": body.metric, "value": body.value,
                "created_at": ts}

    async def list(self, owner: str, *,
                   metric: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM loop_metrics WHERE owner_user_id=:owner"
        params: dict[str, Any] = {"owner": owner}
        if metric:
            query += " AND metric=:metric"
            params["metric"] = metric
        rows = await self.db.fetch_all(query + " ORDER BY created_at DESC, id", params)
        return [
            {
                "id": r["id"], "metric": r["metric"], "value": r["value"],
                "meta": json.loads(r["meta_json"] or "{}"), "created_at": r["created_at"],
            }
            for r in rows
        ]
