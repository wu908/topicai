"""AI series candidates with explicit user confirmation and revocation."""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.core.llm import LLMClient, wrap_user_input
from app.models.v2.action_domain import AITraceCreate
from app.models.v2.creator_series import (
    SeriesCandidateCreate,
    SeriesDecision,
    SeriesDraft,
    SeriesRevocation,
)
from app.services.ai_trace import AITraceService
from app.services.creator_state import CreatorStateService
from app.services.v2_utils import effective_intent_status, now, request_hash

ELIGIBLE_SERIES_STATUSES = {"published", "awaiting_review", "settled"}


class CreatorSeriesService:
    def __init__(self, db: Any, llm: LLMClient | None = None):
        self.db = db
        self.llm = llm

    async def list(self, owner: str) -> list[dict[str, Any]]:
        rows = await self.db.fetch_all(
            "SELECT * FROM creator_series WHERE owner_user_id=:owner "
            "ORDER BY updated_at DESC",
            {"owner": owner},
        )
        return [self._normalize(item) for item in rows]

    async def propose(
        self, owner: str, body: SeriesCandidateCreate
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        existing = await self.db.fetch_one(
            "SELECT * FROM creator_series WHERE owner_user_id=:owner "
            "AND idempotency_key=:key",
            {"owner": owner, "key": body.idempotency_key},
        )
        if existing:
            if existing["request_hash"] != digest:
                raise IdempotencyConflictException()
            return self._normalize(existing), True

        projects = await self._eligible_projects(owner, body.source_project_ids)
        for project in projects:
            expected = body.expected_project_versions[project["id"]]
            if project["version"] != expected:
                raise VersionConflictException(project["version"], expected)
        # Spec-011: a series is connected by an ongoing audience promise, so its
        # members may differ in intent and format. The authoritative information
        # is the member sets; the scalar columns are a convenience read that only
        # carries a value when the members agree.
        member_intents = sorted({project["content_intent"] for project in projects})
        member_formats = sorted({project["content_format"] for project in projects})
        intent = member_intents[0] if len(member_intents) == 1 else None
        content_format = member_formats[0] if len(member_formats) == 1 else None
        scope = {
            "member_intents": member_intents,
            "member_formats": member_formats,
            "content_intent": intent,
            "format": content_format,
        }

        draft, proposal_source = await self._draft(projects)
        series_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        timestamp = now()
        source_ids = [project["id"] for project in projects]
        publish_refs = [f"publish-record:{project['publish_record_id']}" for project in projects]

        session = await self.db.get_session()
        async with session:
            async with session.begin():
                await AITraceService.create(
                    session,
                    owner,
                    AITraceCreate(
                        id=trace_id,
                        task_type="series_candidate",
                        input_refs=[
                            *[f"content-project:{item}" for item in source_ids],
                            *publish_refs,
                        ],
                        evidence_refs=publish_refs,
                        policy_version="series-candidate-v1",
                        model_identifier=(
                            "configured-text-model" if proposal_source == "ai" else None
                        ),
                        capability="structured_proposal",
                        visibility_boundary={
                            "allowed": [
                                "owner_published_projects",
                                "confirmed_project_intent",
                            ],
                            "forbidden": [
                                "draft_projects",
                                "other_users",
                                "deleted_projects",
                            ],
                            "actual": ["owner_published_projects"],
                        },
                        contamination_check={
                            "status": "clean",
                            "unexpected_classes": [],
                            "missing_classes": [],
                        },
                        calibration_state="insufficient",
                        limitations=draft.limitations,
                        output_ref=f"creator-series:{series_id}",
                        generated_at=timestamp,
                    ),
                )
                await session.execute(
                    text(
                        "INSERT INTO creator_series (id,owner_user_id,content_intent,content_format,"
                        "proposed_name,proposed_promise,proposed_rationale,"
                        "proposed_continuation_prompt,scope_json,source_project_ids_json,status,"
                        "proposal_source,ai_trace_id,limitations_json,version,idempotency_key,"
                        "request_hash,created_at,updated_at) VALUES "
                        "(:id,:owner,:intent,:format,:name,:promise,:rationale,:continuation,"
                        ":scope,:sources,'proposed',:proposal_source,:trace,:limitations,1,"
                        ":key,:hash,:now,:now)"
                    ),
                    {
                        "id": series_id,
                        "owner": owner,
                        "intent": intent,
                        "format": content_format,
                        "name": draft.name.strip(),
                        "promise": draft.promise.strip(),
                        "rationale": draft.rationale.strip(),
                        "continuation": draft.continuation_prompt.strip(),
                        "scope": json.dumps(scope, ensure_ascii=False),
                        "sources": json.dumps(source_ids, ensure_ascii=False),
                        "proposal_source": proposal_source,
                        "trace": trace_id,
                        "limitations": json.dumps(draft.limitations, ensure_ascii=False),
                        "key": body.idempotency_key,
                        "hash": digest,
                        "now": timestamp,
                    },
                )
                await self._event(
                    session,
                    owner,
                    series_id,
                    "proposed",
                    None,
                    "proposed",
                    1,
                    f"{body.idempotency_key}:proposed",
                    digest,
                    {"source_project_ids": source_ids, "proposal_source": proposal_source},
                    timestamp,
                )
        return await self.get(owner, series_id), False

    async def decide(
        self, owner: str, series_id: str, body: SeriesDecision
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        replay = await self._event_by_key(owner, body.idempotency_key)
        if replay:
            if replay["series_id"] != series_id or replay["request_hash"] != digest:
                raise IdempotencyConflictException()
            result = await self.get(owner, series_id)
            if replay["to_status"] == "confirmed" and result["status"] == "confirmed":
                result = await self._attach_creator_state(owner, result)
            return result, True
        series = await self._series(owner, series_id)
        if series["status"] != "proposed":
            raise ValueError("series candidate is no longer pending")
        if series["version"] != body.expected_series_version:
            raise VersionConflictException(series["version"], body.expected_series_version)
        if body.decision == "confirm":
            await self._assert_sources_available(owner, series)

        status = "confirmed" if body.decision == "confirm" else "rejected"
        name = (body.confirmed_name or series["proposed_name"]).strip()
        promise = (body.confirmed_promise or series["proposed_promise"]).strip()
        continuation = (
            body.confirmed_continuation_prompt or series["proposed_continuation_prompt"]
        ).strip()
        timestamp = now()
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                updated = await session.execute(
                    text(
                        "UPDATE creator_series SET status=:status,confirmed_name=:name,"
                        "confirmed_promise=:promise,confirmed_continuation_prompt=:continuation,"
                        "confirmed_at=:confirmed,updated_at=:now,version=version+1 "
                        "WHERE id=:id AND owner_user_id=:owner AND version=:expected "
                        "AND status='proposed'"
                    ),
                    {
                        "status": status,
                        "name": name if status == "confirmed" else None,
                        "promise": promise if status == "confirmed" else None,
                        "continuation": continuation if status == "confirmed" else None,
                        "confirmed": timestamp if status == "confirmed" else None,
                        "now": timestamp,
                        "id": series_id,
                        "owner": owner,
                        "expected": body.expected_series_version,
                    },
                )
                if updated.rowcount != 1:
                    raise VersionConflictException(
                        series["version"] + 1, body.expected_series_version
                    )
                await self._event(
                    session,
                    owner,
                    series_id,
                    status,
                    "proposed",
                    status,
                    series["version"] + 1,
                    body.idempotency_key,
                    digest,
                    {
                        "reason": body.reason,
                        "confirmed_name": name if status == "confirmed" else None,
                        "confirmed_promise": promise if status == "confirmed" else None,
                        "confirmed_continuation_prompt": (
                            continuation if status == "confirmed" else None
                        ),
                    },
                    timestamp,
                )
        result = await self.get(owner, series_id)
        if status == "confirmed":
            result = await self._attach_creator_state(owner, result)
        return result, False

    async def revoke(
        self, owner: str, series_id: str, body: SeriesRevocation
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        replay = await self._event_by_key(owner, body.idempotency_key)
        if replay:
            if replay["series_id"] != series_id or replay["request_hash"] != digest:
                raise IdempotencyConflictException()
            result = await self.get(owner, series_id)
            if replay["to_status"] == "revoked" and result["status"] == "revoked":
                result = await self._attach_creator_state(owner, result)
            return result, True
        series = await self._series(owner, series_id)
        if series["status"] != "confirmed":
            raise ValueError("only a confirmed series can be revoked")
        if series["version"] != body.expected_series_version:
            raise VersionConflictException(series["version"], body.expected_series_version)
        timestamp = now()
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                updated = await session.execute(
                    text(
                        "UPDATE creator_series SET status='revoked',revoked_at=:now,"
                        "updated_at=:now,version=version+1 WHERE id=:id AND owner_user_id=:owner "
                        "AND version=:expected AND status='confirmed'"
                    ),
                    {
                        "now": timestamp,
                        "id": series_id,
                        "owner": owner,
                        "expected": body.expected_series_version,
                    },
                )
                if updated.rowcount != 1:
                    raise VersionConflictException(
                        series["version"] + 1, body.expected_series_version
                    )
                await self._event(
                    session,
                    owner,
                    series_id,
                    "revoked",
                    "confirmed",
                    "revoked",
                    series["version"] + 1,
                    body.idempotency_key,
                    digest,
                    {"reason": body.reason},
                    timestamp,
                )
        result = await self._attach_creator_state(
            owner, await self.get(owner, series_id)
        )
        return result, False

    async def get(self, owner: str, series_id: str) -> dict[str, Any]:
        return self._normalize(await self._series(owner, series_id))

    async def get_usable(self, owner: str, series_id: str) -> dict[str, Any]:
        series = await self._series(owner, series_id)
        if series["status"] != "confirmed":
            raise ValueError("only a confirmed series can create an opportunity")
        await self._assert_sources_available(owner, series)
        return self._normalize(series)

    async def _attach_creator_state(
        self, owner: str, series: dict[str, Any]
    ) -> dict[str, Any]:
        state_service = CreatorStateService(self.db)
        source_ref = f"creator-series:{series['id']}"
        if series["status"] == "confirmed":
            creator_state = await state_service.append_validated_insight(
                owner,
                {
                    "statement": (
                        f"系列「{series['confirmed_name']}」："
                        f"{series['confirmed_promise']}"
                    ),
                    "source_ref": source_ref,
                    "source_type": "user_confirmed_series",
                    "content_intent": series["content_intent"],
                    "source_project_ids": series["source_project_ids"],
                },
            )
        elif series["status"] == "revoked":
            creator_state = await state_service.remove_validated_insight(owner, source_ref)
        else:
            return series
        return {**series, "creator_state": creator_state}

    async def _draft(
        self, projects: list[dict[str, Any]]
    ) -> tuple[SeriesDraft, str]:
        if self.llm and self.llm.is_available("text"):
            prompt = (
                "从以下同一创作者已经发布的内容项目中，提出一个可能的系列关系。"
                "不能只依据标题词语相似，必须说明共同读者价值和下一篇可延展方向。"
                "不得引入项目资料外的事实。返回 name、promise、rationale、"
                "continuation_prompt、limitations。\n"
                + "\n".join(
                    "- 标题: {title}; 意图: {intent}; 读者变化: {change}".format(
                        title=wrap_user_input(item["title"]),
                        intent=item["content_intent"],
                        change=wrap_user_input(item.get("audience_change") or "未填写"),
                    )
                    for item in projects
                )
            )
            try:
                draft = await asyncio.to_thread(
                    self.llm.generate_structured,
                    prompt,
                    SeriesDraft,
                    "你是内容系列识别助手。输出只是候选，必须等待用户确认。",
                )
                return draft, "ai"
            except Exception:
                pass
        first = projects[0]
        return (
            SeriesDraft(
                name=f"{first['title']}等{len(projects)}篇内容",
                promise=first.get("audience_change") or "请确认这些内容对读者的共同价值",
                rationale="模型不可用，仅保留用户选中的项目关系，没有推断共同主题。",
                continuation_prompt="请先确认这些内容为何属于同一系列",
                limitations=["模型不可用；当前候选未推断共同主题", "需要用户编辑或确认"],
            ),
            "deterministic_fallback",
        )

    async def _eligible_projects(
        self, owner: str, source_project_ids: list[str]
    ) -> list[dict[str, Any]]:
        projects: list[dict[str, Any]] = []
        for project_id in source_project_ids:
            row = await self.db.fetch_one(
                "SELECT p.*,pr.id AS publish_record_id FROM content_projects p "
                "JOIN publish_records_v2 pr ON pr.project_id=p.id "
                "AND pr.owner_user_id=p.owner_user_id "
                "WHERE p.id=:id AND p.owner_user_id=:owner AND p.deleted_at IS NULL "
                "AND p.archived_at IS NULL ORDER BY pr.created_at DESC LIMIT 1",
                {"id": project_id, "owner": owner},
            )
            if (
                row is None
                or effective_intent_status(row) not in {"working_confirmed", "locked"}
                or row["status"] not in ELIGIBLE_SERIES_STATUSES
                or not row.get("locked_publish_version_id")
            ):
                raise ValueError(
                    "series sources must be published projects with confirmed intent"
                )
            projects.append(dict(row))
        return projects

    async def _assert_sources_available(
        self, owner: str, series: dict[str, Any]
    ) -> None:
        source_ids = json.loads(series["source_project_ids_json"] or "[]")
        projects = await self._eligible_projects(owner, source_ids)
        if not projects:
            raise ValueError("series source projects are no longer available")
        # Spec-011: the member intent/format sets are authoritative, so drift is
        # detected by comparing those sets rather than the scalar columns (which
        # are NULL whenever the members disagree).
        scope = json.loads(series.get("scope_json") or "{}")
        stored_intents = sorted(
            scope.get("member_intents")
            or ([series["content_intent"]] if series["content_intent"] else [])
        )
        stored_formats = sorted(
            scope.get("member_formats")
            or ([series["content_format"]] if series["content_format"] else [])
        )
        current_intents = sorted({item["content_intent"] for item in projects})
        current_formats = sorted({item["content_format"] for item in projects})
        if current_intents != stored_intents or current_formats != stored_formats:
            raise ValueError("series source projects no longer match the candidate scope")

    async def _series(self, owner: str, series_id: str) -> dict[str, Any]:
        row = await self.db.fetch_one(
            "SELECT * FROM creator_series WHERE id=:id AND owner_user_id=:owner",
            {"id": series_id, "owner": owner},
        )
        if row is None:
            raise ValueError("creator series not found")
        return row

    async def _event_by_key(self, owner: str, key: str) -> dict[str, Any] | None:
        return await self.db.fetch_one(
            "SELECT * FROM creator_series_events WHERE owner_user_id=:owner "
            "AND idempotency_key=:key",
            {"owner": owner, "key": key},
        )

    @staticmethod
    async def _event(
        session,
        owner,
        series_id,
        event_type,
        from_status,
        to_status,
        version,
        key,
        digest,
        payload,
        timestamp,
    ):
        await session.execute(
            text(
                "INSERT INTO creator_series_events (id,owner_user_id,series_id,event_type,"
                "from_status,to_status,payload_json,series_version,idempotency_key,request_hash,"
                "created_at) VALUES (:id,:owner,:series,:event,:from_status,:to_status,:payload,"
                ":version,:key,:hash,:now)"
            ),
            {
                "id": str(uuid.uuid4()),
                "owner": owner,
                "series": series_id,
                "event": event_type,
                "from_status": from_status,
                "to_status": to_status,
                "payload": json.dumps(payload, ensure_ascii=False),
                "version": version,
                "key": key,
                "hash": digest,
                "now": timestamp,
            },
        )

    @staticmethod
    def _normalize(row: dict[str, Any]) -> dict[str, Any]:
        result = dict(row)
        result["scope"] = json.loads(result.pop("scope_json") or "{}")
        result["source_project_ids"] = json.loads(
            result.pop("source_project_ids_json") or "[]"
        )
        result["limitations"] = json.loads(result.pop("limitations_json") or "[]")
        return result
