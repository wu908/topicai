"""Canonical ContentProject status transitions with append-only audit."""

import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.models.v2.content_project import ProjectTransition
from app.services.v2_utils import now, request_hash


class ProjectStateService:
    ALLOWED_TRANSITIONS = {
        "inbox": {"preparing"},
        "preparing": {"inbox", "creating", "ready_to_publish"},
        "creating": {"preparing", "ready_to_publish"},
        "ready_to_publish": {"creating", "published"},
        "published": {"awaiting_review"},
        "awaiting_review": {"settled"},
        "settled": set(),
    }
    PUBLIC_TRANSITIONS = {
        ("inbox", "preparing"),
        ("preparing", "inbox"),
        ("preparing", "creating"),
        ("creating", "preparing"),
    }

    def __init__(self, db: Any):
        self.db = db

    async def transition(
        self,
        owner_user_id: str,
        project_id: str,
        body: ProjectTransition,
        *,
        actor_type: str = "user",
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(
            {
                "project_id": project_id,
                "actor_type": actor_type,
                "body": body.model_dump(mode="json"),
            }
        )
        event_key = f"transition:{body.idempotency_key}"
        session = await self.db.get_session()
        async with session, session.begin():
            existing = (
                await session.execute(
                    text(
                        "SELECT * FROM project_state_events "
                        "WHERE owner_user_id=:owner AND idempotency_key=:key"
                    ),
                    {"owner": owner_user_id, "key": event_key},
                )
            ).mappings().first()
            if existing:
                if existing["request_hash"] != digest or existing["project_id"] != project_id:
                    raise IdempotencyConflictException()
                project = await self._project(session, owner_user_id, project_id)
                return {"project": dict(project), "event": dict(existing)}, True

            project = await self._project(session, owner_user_id, project_id)
            if project["version"] != body.expected_version:
                raise VersionConflictException(project["version"], body.expected_version)
            if (project["status"], body.to_status.value) not in self.PUBLIC_TRANSITIONS:
                raise ValueError("project transition must use its owning workflow")
            result = await self.apply(
                session,
                owner_user_id,
                project,
                to_status=body.to_status.value,
                reason=body.reason,
                actor_type=actor_type,
                expected_version=body.expected_version,
                idempotency_key=event_key,
                digest=digest,
                timestamp=now(),
            )
            return result, False

    @classmethod
    async def apply(
        cls,
        session: Any,
        owner_user_id: str,
        project: Any,
        *,
        to_status: str,
        reason: str,
        actor_type: str,
        expected_version: int,
        idempotency_key: str,
        digest: str,
        timestamp: str,
    ) -> dict[str, Any]:
        if project["version"] != expected_version:
            raise VersionConflictException(project["version"], expected_version)
        from_status = project["status"]
        if to_status == from_status:
            raise ValueError("project status is unchanged")
        if to_status not in cls.ALLOWED_TRANSITIONS[from_status]:
            raise ValueError(f"invalid project transition: {from_status} -> {to_status}")
        reason = reason.strip()
        if not reason:
            raise ValueError("project transition reason is required")
        if actor_type not in {"user", "system"}:
            raise ValueError("invalid project transition actor")

        updated = await session.execute(
            text(
                "UPDATE content_projects SET status=:status,last_action=:reason,"
                "last_action_at=:now,updated_at=:now,version=version+1 "
                "WHERE id=:project AND owner_user_id=:owner AND version=:expected"
            ),
            {
                "status": to_status,
                "reason": reason,
                "now": timestamp,
                "project": project["id"],
                "owner": owner_user_id,
                "expected": expected_version,
            },
        )
        if updated.rowcount != 1:
            raise VersionConflictException(project["version"], expected_version)

        event_id = str(uuid.uuid4())
        await session.execute(
            text(
                "INSERT INTO project_state_events ("
                "id,owner_user_id,project_id,from_status,to_status,reason,actor_type,"
                "project_version,idempotency_key,request_hash,created_at) VALUES ("
                ":id,:owner,:project,:from_status,:to_status,:reason,:actor,"
                ":version,:key,:hash,:now)"
            ),
            {
                "id": event_id,
                "owner": owner_user_id,
                "project": project["id"],
                "from_status": from_status,
                "to_status": to_status,
                "reason": reason,
                "actor": actor_type,
                "version": expected_version + 1,
                "key": idempotency_key,
                "hash": digest,
                "now": timestamp,
            },
        )
        updated_project = await cls._project(session, owner_user_id, project["id"])
        event = (
            await session.execute(
                text("SELECT * FROM project_state_events WHERE id=:id"),
                {"id": event_id},
            )
        ).mappings().one()
        return {"project": dict(updated_project), "event": dict(event)}

    @staticmethod
    async def _project(session: Any, owner_user_id: str, project_id: str):
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
