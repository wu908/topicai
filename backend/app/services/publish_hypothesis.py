"""Atomic locking of a publish candidate and its pre-publication judgment."""

import json
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.models.v2.publish_hypothesis import PublishHypothesisLock
from app.services.v2_utils import now, request_hash


class PublishHypothesisService:
    def __init__(self, db: Any):
        self.db = db

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
                    return {"project": dict(project), "hypothesis": dict(existing)}, True

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
                        "uncertainties_json,status,idempotency_key,request_hash,locked_at,"
                        "locked_by,created_at) VALUES ("
                        ":id,:owner,:project,:version,:problem,:promise,:behaviors,:basis,"
                        ":uncertainties,'locked',:key,:hash,:now,:owner,:now)"
                    ),
                    {
                        "id": hypothesis_id,
                        "owner": owner_user_id,
                        "project": project_id,
                        "version": body.content_version_id,
                        "problem": body.audience_problem.strip(),
                        "promise": body.reader_promise.strip(),
                        "behaviors": json.dumps(body.expected_behaviors, ensure_ascii=False),
                        "basis": json.dumps(body.basis_refs, ensure_ascii=False),
                        "uncertainties": json.dumps(body.uncertainties, ensure_ascii=False),
                        "key": body.idempotency_key,
                        "hash": digest,
                        "now": timestamp,
                    },
                )
                updated = await session.execute(
                    text(
                        "UPDATE content_projects SET status='ready_to_publish',"
                        "locked_publish_version_id=:version,publish_hypothesis_id=:hypothesis,"
                        "calibration_state='not_ready',last_action='publish_hypothesis_locked',"
                        "last_action_at=:now,updated_at=:now,version=version+1 "
                        "WHERE id=:project AND owner_user_id=:owner AND version=:expected"
                    ),
                    {
                        "version": body.content_version_id,
                        "hypothesis": hypothesis_id,
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
                    "project": dict(updated_project),
                    "hypothesis": dict(locked),
                }, False
