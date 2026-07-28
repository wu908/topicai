"""Persist a small starter assessment and derive action readiness."""

import json
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException
from app.models.v2.starter import StarterAssessmentCreate
from app.services.v2_utils import now, request_hash

ASSET_FIELDS = ("experience_assets", "skill_assets", "interest_assets")


class StarterAssessmentService:
    def __init__(self, db: Any):
        self.db = db

    async def submit(
        self, owner_user_id: str, body: StarterAssessmentCreate
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                existing = (
                    await session.execute(
                        text(
                            "SELECT * FROM starter_assessments WHERE owner_user_id=:owner"
                        ),
                        {"owner": owner_user_id},
                    )
                ).mappings().first()
                if existing and existing["idempotency_key"] == body.idempotency_key:
                    if existing["request_hash"] != digest:
                        raise IdempotencyConflictException()
                    return self._normalize(existing), True

                if existing:
                    sprint = (
                        await session.execute(
                            text(
                                "SELECT id FROM starter_sprints WHERE owner_user_id=:owner "
                                "AND assessment_id=:assessment"
                            ),
                            {"owner": owner_user_id, "assessment": existing["id"]},
                        )
                    ).first()
                    if sprint:
                        raise ValueError("starter assessment cannot change after sprint starts")

                payload = body.model_dump(mode="json")
                readiness = self.readiness(payload)
                timestamp = now()
                values = {
                    "id": existing["id"] if existing else str(uuid.uuid4()),
                    "owner": owner_user_id,
                    "motivation": body.motivation,
                    "hours": body.available_hours_per_week,
                    "publish": int(body.publish_commitment),
                    "experiment": int(body.accept_experiment),
                    "experience": json.dumps(body.experience_assets, ensure_ascii=False),
                    "interest": json.dumps(body.interest_assets, ensure_ascii=False),
                    "skills": json.dumps(body.skill_assets, ensure_ascii=False),
                    "privacy": json.dumps(body.privacy_limits, ensure_ascii=False),
                    "readiness": readiness,
                    "key": body.idempotency_key,
                    "hash": digest,
                    "now": timestamp,
                }
                if existing:
                    trace_rows = (
                        await session.execute(
                            text(
                                "SELECT DISTINCT ai_trace_id FROM starter_direction_candidates "
                                "WHERE assessment_id=:assessment AND ai_trace_id IS NOT NULL"
                            ),
                            {"assessment": existing["id"]},
                        )
                    ).fetchall()
                    await session.execute(
                        text(
                            "DELETE FROM starter_direction_candidates "
                            "WHERE assessment_id=:assessment AND owner_user_id=:owner"
                        ),
                        {"assessment": existing["id"], "owner": owner_user_id},
                    )
                    for trace_row in trace_rows:
                        await session.execute(
                            text(
                                "DELETE FROM ai_traces_v2 WHERE id=:id "
                                "AND owner_user_id=:owner"
                            ),
                            {"id": trace_row[0], "owner": owner_user_id},
                        )
                    await session.execute(
                        text(
                            "UPDATE starter_assessments SET motivation=:motivation,"
                            "available_hours_per_week=:hours,publish_commitment=:publish,"
                            "accept_experiment=:experiment,experience_assets_json=:experience,"
                            "interest_assets_json=:interest,skill_assets_json=:skills,"
                            "privacy_limits_json=:privacy,readiness=:readiness,version=version+1,"
                            "idempotency_key=:key,request_hash=:hash,updated_at=:now "
                            "WHERE id=:id AND owner_user_id=:owner"
                        ),
                        values,
                    )
                else:
                    await session.execute(
                        text(
                            "INSERT INTO starter_assessments (id,owner_user_id,motivation,"
                            "available_hours_per_week,publish_commitment,accept_experiment,"
                            "experience_assets_json,interest_assets_json,skill_assets_json,"
                            "privacy_limits_json,readiness,version,idempotency_key,request_hash,"
                            "created_at,updated_at) VALUES (:id,:owner,:motivation,:hours,:publish,"
                            ":experiment,:experience,:interest,:skills,:privacy,:readiness,1,"
                            ":key,:hash,:now,:now)"
                        ),
                        values,
                    )
                saved = (
                    await session.execute(
                        text("SELECT * FROM starter_assessments WHERE id=:id"),
                        {"id": values["id"]},
                    )
                ).mappings().one()
                return self._normalize(saved), False

    async def get(self, owner_user_id: str) -> dict[str, Any] | None:
        row = await self.db.fetch_one(
            "SELECT * FROM starter_assessments WHERE owner_user_id=:owner",
            {"owner": owner_user_id},
        )
        return self._normalize(row) if row else None

    @classmethod
    def readiness(cls, payload: dict[str, Any]) -> str:
        if (
            payload["available_hours_per_week"] <= 0
            or not payload["publish_commitment"]
            or not payload["accept_experiment"]
        ):
            return "paused"
        return "ready" if cls.usable_assets(payload) else "not_ready"

    @staticmethod
    def usable_assets(payload: dict[str, Any]) -> list[tuple[str, int, str]]:
        limits = [item.casefold() for item in payload.get("privacy_limits", []) if item]
        assets: list[tuple[str, int, str]] = []
        for field in ASSET_FIELDS:
            for index, value in enumerate(payload.get(field, [])):
                normalized = value.casefold()
                if any(limit in normalized or normalized in limit for limit in limits):
                    continue
                assets.append((field, index, value))
        return assets

    @staticmethod
    def _normalize(row: Any) -> dict[str, Any]:
        result = dict(row)
        for field in (
            "experience_assets_json",
            "interest_assets_json",
            "skill_assets_json",
            "privacy_limits_json",
        ):
            result[field.removesuffix("_json")] = json.loads(result.pop(field))
        result["publish_commitment"] = bool(result["publish_commitment"])
        result["accept_experiment"] = bool(result["accept_experiment"])
        return result
