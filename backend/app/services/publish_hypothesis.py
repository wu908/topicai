"""Atomic locking of a publish candidate and its pre-publication judgment."""

import json
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.models.v2.publish_hypothesis import (
    PublishHypothesisAmendmentCreate,
    PublishHypothesisLock,
)
from app.services.project_state import ProjectStateService
from app.services.v2_utils import (
    effective_intent_status,
    normalize_project_intent,
    now,
    request_hash,
)


class PublishHypothesisService:
    def __init__(self, db: Any):
        self.db = db

    async def list_amendments(
        self, owner_user_id: str, hypothesis_id: str
    ) -> list[dict[str, Any]]:
        await self._hypothesis(owner_user_id, hypothesis_id)
        rows = await self.db.fetch_all(
            "SELECT * FROM publish_hypothesis_amendments "
            "WHERE owner_user_id=:owner AND publish_hypothesis_id=:hypothesis "
            "ORDER BY created_at,id",
            {"owner": owner_user_id, "hypothesis": hypothesis_id},
        )
        return [dict(row) for row in rows]

    async def amend(
        self,
        owner_user_id: str,
        hypothesis_id: str,
        body: PublishHypothesisAmendmentCreate,
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(
            {"hypothesis_id": hypothesis_id, "body": body.model_dump(mode="json")}
        )
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                existing = (
                    await session.execute(
                        text(
                            "SELECT * FROM publish_hypothesis_amendments "
                            "WHERE owner_user_id=:owner AND idempotency_key=:key"
                        ),
                        {"owner": owner_user_id, "key": body.idempotency_key},
                    )
                ).mappings().first()
                if existing:
                    if existing["request_hash"] != digest:
                        raise IdempotencyConflictException()
                    return dict(existing), True

                hypothesis = (
                    await session.execute(
                        text(
                            "SELECT id,status FROM publish_hypotheses "
                            "WHERE id=:id AND owner_user_id=:owner"
                        ),
                        {"id": hypothesis_id, "owner": owner_user_id},
                    )
                ).mappings().first()
                if hypothesis is None:
                    raise ValueError("publish hypothesis not found")
                if hypothesis["status"] not in {"locked", "superseded"}:
                    raise ValueError("only a locked hypothesis can be amended")

                amendment_id = str(uuid.uuid4())
                timestamp = now()
                await session.execute(
                    text(
                        "INSERT INTO publish_hypothesis_amendments ("
                        "id,owner_user_id,publish_hypothesis_id,amendment_type,statement,"
                        "reason,created_by,idempotency_key,request_hash,created_at) VALUES ("
                        ":id,:owner,:hypothesis,:type,:statement,:reason,:owner,:key,:hash,:now)"
                    ),
                    {
                        "id": amendment_id,
                        "owner": owner_user_id,
                        "hypothesis": hypothesis_id,
                        "type": body.amendment_type,
                        "statement": body.statement.strip(),
                        "reason": body.reason.strip(),
                        "key": body.idempotency_key,
                        "hash": digest,
                        "now": timestamp,
                    },
                )
                created = (
                    await session.execute(
                        text(
                            "SELECT * FROM publish_hypothesis_amendments WHERE id=:id"
                        ),
                        {"id": amendment_id},
                    )
                ).mappings().one()
                return dict(created), False

    async def lock(
        self,
        owner_user_id: str,
        project_id: str,
        body: PublishHypothesisLock,
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                existing = (
                    await session.execute(
                        text(
                            "SELECT * FROM publish_hypotheses WHERE project_id=:project "
                            "AND owner_user_id=:owner AND idempotency_key=:key"
                        ),
                        {
                            "project": project_id,
                            "owner": owner_user_id,
                            "key": body.idempotency_key,
                        },
                    )
                ).mappings().first()
                if existing:
                    if existing["request_hash"] != digest:
                        raise IdempotencyConflictException()
                    project = (
                        await session.execute(
                            text(
                                "SELECT * FROM content_projects WHERE id=:id "
                                "AND owner_user_id=:owner"
                            ),
                            {"id": project_id, "owner": owner_user_id},
                        )
                    ).mappings().first()
                    if project is None:
                        raise ValueError(f"project not found: {project_id}")
                    return {
                        "project": normalize_project_intent(project),
                        "hypothesis": dict(existing),
                    }, True

                project = (
                    await session.execute(
                        text(
                            "SELECT * FROM content_projects WHERE id=:id "
                            "AND owner_user_id=:owner AND deleted_at IS NULL"
                        ),
                        {"id": project_id, "owner": owner_user_id},
                    )
                ).mappings().first()
                if project is None:
                    raise ValueError(f"project not found: {project_id}")
                if project["version"] != body.expected_project_version:
                    raise VersionConflictException(
                        project["version"], body.expected_project_version
                    )
                if effective_intent_status(project) != "working_confirmed":
                    raise ValueError("intent must be working confirmed before lock")
                if project["content_intent"] != body.content_intent.value:
                    raise ValueError("locked content intent must match the working intent")

                version = (
                    await session.execute(
                        text(
                            "SELECT id FROM content_versions WHERE id=:id "
                            "AND project_id=:project AND owner_user_id=:owner"
                        ),
                        {
                            "id": body.content_version_id,
                            "project": project_id,
                            "owner": owner_user_id,
                        },
                    )
                ).first()
                if version is None:
                    raise ValueError("content version not found")

                already_locked = (
                    await session.execute(
                        text(
                            "SELECT id FROM publish_hypotheses WHERE project_id=:project "
                            "AND content_version_id=:version"
                        ),
                        {"project": project_id, "version": body.content_version_id},
                    )
                ).first()
                if already_locked:
                    raise IdempotencyConflictException()

                hypothesis_id = str(uuid.uuid4())
                timestamp = now()
                await session.execute(
                    text(
                        "INSERT INTO publish_hypotheses ("
                        "id,owner_user_id,project_id,content_version_id,audience_problem,"
                        "reader_promise,expected_behaviors_json,basis_refs_json,"
                        "uncertainties_json,content_intent,audience_change,primary_response,"
                        "supporting_responses_json,observation_window_days,viewpoint_anchor,"
                        "continuation_promise,status,idempotency_key,request_hash,locked_at,"
                        "locked_by,created_at) VALUES ("
                        ":id,:owner,:project,:version,:problem,:promise,:behaviors,:basis,"
                        ":uncertainties,:intent,:change,:primary,:supporting,:window,"
                        ":viewpoint,:continuation,'locked',:key,:hash,:now,:owner,:now)"
                    ),
                    {
                        "id": hypothesis_id,
                        "owner": owner_user_id,
                        "project": project_id,
                        "version": body.content_version_id,
                        "problem": (body.audience_problem or "").strip(),
                        "promise": (body.reader_promise or "").strip(),
                        "behaviors": json.dumps(
                            [body.primary_response, *body.supporting_responses],
                            ensure_ascii=False,
                        ),
                        "basis": json.dumps(body.basis_refs, ensure_ascii=False),
                        "uncertainties": json.dumps(body.uncertainties, ensure_ascii=False),
                        "intent": body.content_intent.value,
                        "change": body.audience_change.strip(),
                        "primary": body.primary_response,
                        "supporting": json.dumps(
                            body.supporting_responses, ensure_ascii=False
                        ),
                        "window": body.observation_window_days,
                        "viewpoint": (
                            body.viewpoint_anchor.strip()
                            if body.viewpoint_anchor
                            else None
                        ),
                        "continuation": (
                            body.continuation_promise.strip()
                            if body.continuation_promise
                            else None
                        ),
                        "key": body.idempotency_key,
                        "hash": digest,
                        "now": timestamp,
                    },
                )
                updated = await session.execute(
                    text(
                        "UPDATE content_projects SET locked_publish_version_id=:version,"
                        "publish_hypothesis_id=:hypothesis,"
                        "content_intent=:intent,audience_change=:change,"
                        "intent_status='locked',intent_locked_at=:now,"
                        "calibration_state='not_ready' "
                        "WHERE id=:project AND owner_user_id=:owner AND version=:expected"
                    ),
                    {
                        "version": body.content_version_id,
                        "hypothesis": hypothesis_id,
                        "intent": body.content_intent.value,
                        "change": body.audience_change.strip(),
                        "now": timestamp,
                        "project": project_id,
                        "owner": owner_user_id,
                        "expected": body.expected_project_version,
                    },
                )
                if updated.rowcount != 1:
                    raise VersionConflictException(
                        project["version"], body.expected_project_version
                    )
                await ProjectStateService.apply(
                    session,
                    owner_user_id,
                    project,
                    to_status="ready_to_publish",
                    reason="publish_hypothesis_locked",
                    actor_type="user",
                    expected_version=body.expected_project_version,
                    idempotency_key=f"state:publish-hypothesis:{body.idempotency_key}",
                    digest=digest,
                    timestamp=timestamp,
                )
                locked = (
                    await session.execute(
                        text("SELECT * FROM publish_hypotheses WHERE id=:id"),
                        {"id": hypothesis_id},
                    )
                ).mappings().one()
                updated_project = (
                    await session.execute(
                        text("SELECT * FROM content_projects WHERE id=:id"),
                        {"id": project_id},
                    )
                ).mappings().one()
                return {
                    "project": normalize_project_intent(updated_project),
                    "hypothesis": dict(locked),
                }, False

    async def _hypothesis(
        self, owner_user_id: str, hypothesis_id: str
    ) -> dict[str, Any]:
        row = await self.db.fetch_one(
            "SELECT * FROM publish_hypotheses WHERE id=:id AND owner_user_id=:owner",
            {"id": hypothesis_id, "owner": owner_user_id},
        )
        if row is None:
            raise ValueError("publish hypothesis not found")
        return dict(row)
