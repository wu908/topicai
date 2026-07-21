"""ContentProject aggregate creation and owner-scoped reads."""

import json
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException
from app.models.v2.content_project import ContentProjectCreate
from app.services.v2_utils import now, request_hash, row_dict


class ContentProjectService:
    def __init__(self, db: Any):
        self.db = db

    async def create(
        self, owner_user_id: str, body: ContentProjectCreate
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                existing = (
                    await session.execute(
                        text(
                            "SELECT * FROM content_projects WHERE owner_user_id=:owner "
                            "AND idempotency_key=:key"
                        ),
                        {"owner": owner_user_id, "key": body.idempotency_key},
                    )
                ).mappings().first()
                if existing:
                    if existing["request_hash"] != digest:
                        raise IdempotencyConflictException()
                    return self._normalize(existing), True

                timestamp = now()
                project_id = str(uuid.uuid4())
                candidate_intent = (
                    body.content_intent.value
                    if body.content_intent
                    else self._infer_candidate_intent(body.title)
                )
                values = {
                    "id": project_id,
                    "owner": owner_user_id,
                    "title": body.title.strip(),
                    "status": body.status.value,
                    "goal": body.primary_goal,
                    "audience": body.target_audience.strip(),
                    "intent": candidate_intent,
                    "content_format": body.content_format,
                    "audience_change": body.audience_change.strip() if body.audience_change else None,
                    "opportunity": body.opportunity_id,
                    "sprint": body.starter_sprint_id,
                    "planned": body.planned_publish_at,
                    "key": body.idempotency_key,
                    "hash": digest,
                    "now": timestamp,
                }
                await session.execute(
                    text(
                        "INSERT INTO content_projects ("
                        "id,owner_user_id,title,status,primary_goal,target_audience,"
                        "content_intent,content_format,intent_status,audience_change,"
                        "opportunity_id,starter_sprint_id,planned_publish_at,last_action,"
                        "last_action_at,version,idempotency_key,request_hash,created_at,updated_at"
                        ") VALUES ("
                        ":id,:owner,:title,:status,:goal,:audience,:intent,:content_format,"
                        "'candidate',:audience_change,:opportunity,:sprint,"
                        ":planned,'project_created',:now,1,:key,:hash,:now,:now)"
                    ),
                    values,
                )
                created = (
                    await session.execute(
                        text("SELECT * FROM content_projects WHERE id=:id"),
                        {"id": project_id},
                    )
                ).mappings().one()
                return self._normalize(created), False

    async def get(self, owner_user_id: str, project_id: str) -> dict[str, Any]:
        row = await self.db.fetch_one(
            "SELECT * FROM content_projects WHERE id=:id AND owner_user_id=:owner "
            "AND deleted_at IS NULL",
            {"id": project_id, "owner": owner_user_id},
        )
        result = row_dict(row)
        if result is None:
            raise ValueError(f"project not found: {project_id}")
        return self._normalize(result)

    @staticmethod
    def _normalize(row: Any) -> dict[str, Any]:
        result = dict(row)
        for field in (
            "material_requirements_json",
            "expected_responses_json",
            "success_signals_json",
        ):
            if field in result:
                result[field.removesuffix("_json")] = json.loads(result.pop(field))
        return result

    @staticmethod
    def _infer_candidate_intent(title: str) -> str:
        normalized = title.lower()
        if any(token in normalized for token in ("记录", "过程", "变化", "打卡", "第", "vlog")):
            return "record"
        if any(token in normalized for token in ("分享", "经历", "感受", "观点", "我", "为什么")):
            return "share"
        return "solve"
