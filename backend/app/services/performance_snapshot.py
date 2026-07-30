"""Append-only, user-confirmed performance snapshots."""

import json
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.models.v2.calibration import PerformanceSnapshotCreate
from app.services.v2_utils import decode_json_fields, now, request_hash


class PerformanceSnapshotService:
    def __init__(self, db: Any):
        self.db = db

    async def append(
        self, owner_user_id: str, publish_record_id: str, body: PerformanceSnapshotCreate
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(
            {
                "publish_record_id": publish_record_id,
                "body": body.model_dump(mode="json"),
            }
        )
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                existing = (
                    await session.execute(
                        text(
                            "SELECT * FROM performance_snapshots_v2 "
                            "WHERE owner_user_id=:owner AND idempotency_key=:key"
                        ),
                        {"owner": owner_user_id, "key": body.idempotency_key},
                    )
                ).mappings().first()
                if existing:
                    if existing["request_hash"] != digest:
                        raise IdempotencyConflictException()
                    project = await self._project(
                        session, owner_user_id, existing["project_id"]
                    )
                    return {
                        "project": dict(project),
                        "snapshot": decode_json_fields(existing, "metrics_json"),
                    }, True

                record = (
                    await session.execute(
                        text(
                            "SELECT * FROM publish_records_v2 WHERE id=:id "
                            "AND owner_user_id=:owner"
                        ),
                        {"id": publish_record_id, "owner": owner_user_id},
                    )
                ).mappings().first()
                if record is None:
                    raise ValueError(f"publish record not found: {publish_record_id}")
                project = await self._project(session, owner_user_id, record["project_id"])
                if project["version"] != body.expected_project_version:
                    raise VersionConflictException(
                        project["version"], body.expected_project_version
                    )
                if project["status"] not in {"published", "awaiting_review"}:
                    raise ValueError("project is not ready for performance data")
                if not body.confirmed_by_user:
                    raise ValueError("performance snapshot requires user confirmation")

                if body.supersedes_id:
                    superseded = (
                        await session.execute(
                            text(
                                "SELECT id FROM performance_snapshots_v2 WHERE id=:id "
                                "AND owner_user_id=:owner AND publish_record_id=:record"
                            ),
                            {
                                "id": body.supersedes_id,
                                "owner": owner_user_id,
                                "record": publish_record_id,
                            },
                        )
                    ).first()
                    if superseded is None:
                        raise ValueError("superseded snapshot not found")

                snapshot_id = str(uuid.uuid4())
                timestamp = now()
                await session.execute(
                    text(
                        "INSERT INTO performance_snapshots_v2 ("
                        "id,owner_user_id,publish_record_id,project_id,captured_at,source,"
                        "result_availability,unavailable_reason,metrics_json,"
                        "screenshot_material_id,confirmed_by_user,supersedes_id,idempotency_key,"
                        "request_hash,created_at) VALUES ("
                        ":id,:owner,:record,:project,:captured,:source,:availability,:reason,"
                        ":metrics,:material,1,:supersedes,:key,:hash,:now)"
                    ),
                    {
                        "id": snapshot_id,
                        "owner": owner_user_id,
                        "record": publish_record_id,
                        "project": record["project_id"],
                        "captured": body.captured_at,
                        "source": body.source,
                        "availability": body.result_availability,
                        "reason": body.unavailable_reason,
                        "metrics": json.dumps(
                            body.metrics.model_dump(exclude_none=True),
                            ensure_ascii=False,
                        ),
                        "material": body.screenshot_material_id,
                        "supersedes": body.supersedes_id,
                        "key": body.idempotency_key,
                        "hash": digest,
                        "now": timestamp,
                    },
                )
                updated = await session.execute(
                    text(
                        "UPDATE content_projects SET status='awaiting_review',"
                        "last_action='performance_snapshot_added',last_action_at=:now,"
                        "updated_at=:now,version=version+1 WHERE id=:project "
                        "AND owner_user_id=:owner AND version=:expected"
                    ),
                    {
                        "now": timestamp,
                        "project": record["project_id"],
                        "owner": owner_user_id,
                        "expected": body.expected_project_version,
                    },
                )
                if updated.rowcount != 1:
                    raise VersionConflictException(
                        project["version"], body.expected_project_version
                    )
                snapshot = (
                    await session.execute(
                        text("SELECT * FROM performance_snapshots_v2 WHERE id=:id"),
                        {"id": snapshot_id},
                    )
                ).mappings().one()
                updated_project = await self._project(
                    session, owner_user_id, record["project_id"]
                )
                return {
                    "project": dict(updated_project),
                    "snapshot": decode_json_fields(snapshot, "metrics_json"),
                }, False

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
