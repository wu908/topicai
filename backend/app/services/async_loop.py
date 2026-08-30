"""Async creation loop services (Spec-013 Phase 1 walking skeleton).

Deterministic-only: production never fabricates facts — every fact traces to
an inbox item, no LLM is required, and AITrace records the run as
``deterministic_fallback``. The shelf is rate-limited; stale ready items
expire; pickup goes through the official project services so shared semantics
(content project creation + working intent confirmation) are never bypassed.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Any

from app.core.exceptions import IdempotencyConflictException
from app.models.v2.action_domain import AITraceCreate
from app.models.v2.async_loop import (
    DiscardRequest,
    InboxItemCreate,
    MetricsRecord,
    PickupRequest,
)
from app.models.v2.content_project import ContentProjectCreate
from app.models.v2.intent_actions import IntentConfirmation
from app.services.ai_trace import AITraceService
from app.services.content_project import ContentProjectService
from app.services.intent_actions import IntentConfirmationService
from app.services.v2_utils import now, request_hash

SHELF_LIMIT = 6
BATCH_MAIN = 2
EXPIRE_DAYS = 7
PICKUP_IDEM = "pickup_idem"

INTENT_BY_KIND = {
    "text": "solve",
    "link": "solve",
    "idea": "share",
    "image": "record",
    "voice": "record",
}

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
        self, owner: str, *, status: str = "ready"
    ) -> list[dict[str, Any]]:
        rows = await self.db.fetch_all(
            "SELECT * FROM deliverables WHERE owner_user_id=:owner AND status=:status "
            "ORDER BY created_at DESC, id",
            {"owner": owner, "status": status},
        )
        return [self._view(r) for r in rows]

    async def get(self, owner: str, deliverable_id: str) -> dict[str, Any]:
        row = await self._row(owner, deliverable_id)
        return self._view(row)

    async def digest(self, owner: str) -> dict[str, Any]:
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

        if not mains and not exploration:
            return {"thread_id": thread_id, "deliverables": []}

        await self._event(owner, thread_id, None, "queued", {"intake": len(items)})
        produced: list[dict[str, Any]] = []
        used: list[str] = []
        for item, is_exp in [(i, 0) for i in mains] + [(i, 1) for i in exploration]:
            view = await self._produce(owner, thread_id, item, is_exp)
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
        await self._trace(owner, thread_id, used)
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

    async def _produce(self, owner: str, thread_id: str,
                       item: Any, is_exploration: int) -> dict[str, Any]:
        deliverable_id = str(uuid.uuid4())
        ts = now()
        content = item["content"]
        title = item["title"] or content[:20]
        body_text = (
            f"{title}\n\n"
            f"{content}\n\n"
            "[请在发布前补充并确认具体细节：对照大纲逐条写下你亲身经历的版本，"
            "写不出的条目直接删除；当前版本不会虚构缺失经历。]"
        )
        facts = [{"statement": content[:200], "source_inbox_id": item["id"],
                  "note": "收件箱素材"}]
        judgment = {
            "audience_change": "看完能获得一个真实、可判断的变化",
            "primary_response": "save",
            "supporting": ["follow"],
            "window_days": 7,
        }
        precheck = PublishCheckService.run_precheck({
            "title": title, "body_text": body_text,
            "outline": OUTLINE, "facts": facts,
        })
        if not precheck["passed"]:
            # 承重墙：结构预检不过就不产 ready（无死路——记 needs_input 事件）
            await self._event(owner, thread_id, None, "needs_input",
                              {"reason": "precheck_failed", "issues": precheck["issues"]})
            return {}
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
                "outline": json.dumps(OUTLINE, ensure_ascii=False),
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
                           "precheck": "passed"})
        row = await self._row(owner, deliverable_id)
        return self._view(row)

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

    async def _trace(self, owner: str, thread_id: str, used: list[str]) -> None:
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
                        policy_version="async-loop-deterministic-v1",
                        model_identifier=None,
                        capability="deterministic_fallback",
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
                        limitations=[
                            "模型不可用；确定性骨架产出",
                            "细节仍需用户确认",
                        ],
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

    async def _picked_event(self, owner: str, row: Any, project_id: str | None,
                            event_type: str = "picked") -> None:
        await self.db.execute(
            "INSERT INTO production_events (id,owner_user_id,thread_id,deliverable_id,"
            "event_type,detail_json,created_at) VALUES "
            "(:id,:owner,:thread,:deliverable,:etype,:detail,:now)",
            {
                "id": str(uuid.uuid4()), "owner": owner, "thread": row["thread_id"],
                "deliverable": row["id"], "etype": event_type,
                "detail": json.dumps({"project_id": project_id}, ensure_ascii=False),
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
