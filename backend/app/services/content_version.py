"""Immutable content-version persistence."""

import json
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.models.v2.content_project import ContentVersionCreate
from app.services.v2_utils import content_hash, now, request_hash


class ContentVersionService:
    def __init__(self, db: Any):
        self.db = db

    async def create(
        self,
        owner_user_id: str,
        project_id: str,
        body: ContentVersionCreate,
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                existing = (
                    await session.execute(
                        text(
                            "SELECT * FROM content_versions WHERE project_id=:project "
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
                    return dict(existing), True

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

                if body.parent_version_id:
                    parent = (
                        await session.execute(
                            text(
                                "SELECT id FROM content_versions WHERE id=:id "
                                "AND project_id=:project AND owner_user_id=:owner"
                            ),
                            {
                                "id": body.parent_version_id,
                                "project": project_id,
                                "owner": owner_user_id,
                            },
                        )
                    ).first()
                    if parent is None:
                        raise ValueError("parent version not found")

                next_number = (
                    await session.execute(
                        text(
                            "SELECT COALESCE(MAX(version_number),0)+1 "
                            "FROM content_versions WHERE project_id=:project"
                        ),
                        {"project": project_id},
                    )
                ).scalar_one()
                version_id = str(uuid.uuid4())
                timestamp = now()
                values = {
                    "id": version_id,
                    "owner": owner_user_id,
                    "project": project_id,
                    "parent": body.parent_version_id,
                    "number": next_number,
                    "title": body.title.strip(),
                    "body": body.body_text,
                    "cover": body.cover_plan,
                    "images": json.dumps(body.image_plan, ensure_ascii=False),
                    "origin": body.change_origin,
                    "summary": body.change_summary,
                    "evidence": json.dumps(body.evidence_snapshot, ensure_ascii=False),
                    "content_hash": content_hash(
                        body.title, body.body_text, body.cover_plan, body.image_plan
                    ),
                    "key": body.idempotency_key,
                    "request_hash": digest,
                    "now": timestamp,
                }
                await session.execute(
                    text(
                        "INSERT INTO content_versions ("
                        "id,owner_user_id,project_id,parent_version_id,version_number,"
                        "title,body_text,cover_plan,image_plan_json,change_origin,"
                        "change_summary,evidence_snapshot_json,content_hash,idempotency_key,"
                        "request_hash,created_at) VALUES ("
                        ":id,:owner,:project,:parent,:number,:title,:body,:cover,:images,"
                        ":origin,:summary,:evidence,:content_hash,:key,:request_hash,:now)"
                    ),
                    values,
                )
                update = await session.execute(
                    text(
                        "UPDATE content_projects SET current_version_id=:version_id,"
                        "last_action='version_created',last_action_at=:now,updated_at=:now,"
                        "version=version+1 WHERE id=:project AND owner_user_id=:owner "
                        "AND version=:expected"
                    ),
                    {
                        "version_id": version_id,
                        "now": timestamp,
                        "project": project_id,
                        "owner": owner_user_id,
                        "expected": body.expected_project_version,
                    },
                )
                if update.rowcount != 1:
                    raise VersionConflictException(
                        project["version"], body.expected_project_version
                    )
                created = (
                    await session.execute(
                        text("SELECT * FROM content_versions WHERE id=:id"),
                        {"id": version_id},
                    )
                ).mappings().one()
                return dict(created), False
