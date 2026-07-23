"""Manual publication facts bound to a confirmed gate, version, and hypothesis."""

import json
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.models.v2.calibration import PublishRecordCreate
from app.services.v2_utils import now, request_hash


class PublicationService:
    def __init__(self, db: Any):
        self.db = db

    async def record(
        self, owner_user_id: str, project_id: str, body: PublishRecordCreate
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(
            {"project_id": project_id, "body": body.model_dump(mode="json")}
        )
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                existing = (
                    await session.execute(
                        text(
                            "SELECT * FROM publish_records_v2 "
                            "WHERE owner_user_id=:owner AND idempotency_key=:key"
                        ),
                        {"owner": owner_user_id, "key": body.idempotency_key},
                    )
                ).mappings().first()
                if existing:
                    if existing["request_hash"] != digest:
                        raise IdempotencyConflictException()
                    project = await self._project(session, owner_user_id, project_id)
                    return {"project": dict(project), "record": dict(existing)}, True

                project = await self._project(session, owner_user_id, project_id)
                if project["version"] != body.expected_project_version:
                    raise VersionConflictException(
                        project["version"], body.expected_project_version
                    )
                if project["status"] != "ready_to_publish":
                    raise ValueError("project is not ready to publish")
                if project["locked_publish_version_id"] != body.content_version_id:
                    raise ValueError("content version is not the locked publish version")
                if not project["publish_hypothesis_id"]:
                    raise ValueError("locked publish hypothesis is required")

                hypothesis = (
                    await session.execute(
                        text(
                            "SELECT id FROM publish_hypotheses WHERE id=:id "
                            "AND owner_user_id=:owner AND project_id=:project "
                            "AND content_version_id=:version AND status='locked'"
                        ),
                        {
                            "id": project["publish_hypothesis_id"],
                            "owner": owner_user_id,
                            "project": project_id,
                            "version": body.content_version_id,
                        },
                    )
                ).first()
                if hypothesis is None:
                    raise ValueError("locked publish hypothesis is invalid")

                gate = (
                    await session.execute(
                        text(
                            "SELECT hg.*,nba.ai_trace_id AS action_trace_id "
                            "FROM human_gates hg JOIN next_best_actions nba ON nba.id=hg.action_id "
                            "WHERE hg.id=:gate AND hg.owner_user_id=:owner "
                            "AND hg.project_id=:project AND hg.gate_type='publication' "
                            "AND hg.status='confirmed'"
                        ),
                        {
                            "gate": body.publication_gate_id,
                            "owner": owner_user_id,
                            "project": project_id,
                        },
                    )
                ).mappings().first()
                if gate is None:
                    raise ValueError("confirmed publication gate is required")
                gate_payload = json.loads(gate["payload_json"] or "{}")
                if (
                    gate_payload.get("content_version_id") != body.content_version_id
                    or gate_payload.get("publish_hypothesis_id")
                    != project["publish_hypothesis_id"]
                    or gate_payload.get("ai_trace_id") != gate["action_trace_id"]
                    or gate_payload.get("public_scope")
                    != {"platform": "xiaohongshu", "visibility": "public"}
                ):
                    raise ValueError("publication gate provenance does not match the locked release")

                record_id = str(uuid.uuid4())
                timestamp = now()
                await session.execute(
                    text(
                        "INSERT INTO publish_records_v2 ("
                        "id,owner_user_id,project_id,locked_version_id,"
                        "publish_hypothesis_id,publication_gate_id,ai_trace_id,platform,"
                        "note_url,published_at,recorded_at,"
                        "idempotency_key,request_hash,created_at) VALUES ("
                        ":id,:owner,:project,:version,:hypothesis,:gate,:trace,'xiaohongshu',:url,"
                        ":published,:now,:key,:hash,:now)"
                    ),
                    {
                        "id": record_id,
                        "owner": owner_user_id,
                        "project": project_id,
                        "version": body.content_version_id,
                        "hypothesis": project["publish_hypothesis_id"],
                        "gate": body.publication_gate_id,
                        "trace": gate["action_trace_id"],
                        "url": body.note_url,
                        "published": body.published_at,
                        "now": timestamp,
                        "key": body.idempotency_key,
                        "hash": digest,
                    },
                )
                updated = await session.execute(
                    text(
                        "UPDATE content_projects SET status='published',"
                        "last_action='publication_recorded',last_action_at=:now,"
                        "updated_at=:now,version=version+1 WHERE id=:project "
                        "AND owner_user_id=:owner AND version=:expected"
                    ),
                    {
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
                record = (
                    await session.execute(
                        text("SELECT * FROM publish_records_v2 WHERE id=:id"),
                        {"id": record_id},
                    )
                ).mappings().one()
                updated_project = (
                    await session.execute(
                        text("SELECT * FROM content_projects WHERE id=:id"),
                        {"id": project_id},
                    )
                ).mappings().one()
                return {"project": dict(updated_project), "record": dict(record)}, False

    @staticmethod
    async def _project(session, owner_user_id: str, project_id: str):
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
        return project
