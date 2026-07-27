"""Evidence lifecycle and reuse guardrails.

Evidence is deliberately separate from CreatorState. A user answer is only
proposed evidence until the user confirms that TopicAI may use it.
"""

import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.models.v2.evidence import (
    EvidenceCreate,
    EvidenceDecision,
    EvidenceRevocation,
)
from app.services.v2_utils import now, request_hash


class EvidenceService:
    def __init__(self, db: Any):
        self.db = db

    async def create_proposed(
        self, owner_user_id: str, body: EvidenceCreate
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                existing = (
                    await session.execute(
                        text(
                            "SELECT * FROM evidence_items WHERE owner_user_id=:owner "
                            "AND idempotency_key=:key"
                        ),
                        {"owner": owner_user_id, "key": body.idempotency_key},
                    )
                ).mappings().first()
                if existing:
                    if existing["request_hash"] != digest:
                        raise IdempotencyConflictException()
                    return self._normalize(existing), True

                project = (
                    await session.execute(
                        text(
                            "SELECT id FROM content_projects WHERE id=:project "
                            "AND owner_user_id=:owner AND deleted_at IS NULL"
                        ),
                        {"project": body.project_id, "owner": owner_user_id},
                    )
                ).mappings().first()
                if project is None:
                    raise ValueError("project not found")
                timestamp = now()
                evidence_id = str(uuid.uuid4())
                await session.execute(
                    text(
                        "INSERT INTO evidence_items (id,owner_user_id,project_id,"
                        "source_type,statement,source_ref,content_ref,privacy_level,"
                        "confirmation_status,reusable,version,idempotency_key,request_hash,"
                        "created_at,updated_at) VALUES (:id,:owner,:project,:source_type,"
                        ":statement,:source_ref,:content_ref,:privacy,'proposed',:reusable,"
                        "1,:key,:hash,:now,:now)"
                    ),
                    {
                        "id": evidence_id,
                        "owner": owner_user_id,
                        "project": body.project_id,
                        "source_type": body.source_type.value,
                        "statement": body.statement.strip(),
                        "source_ref": body.source_ref,
                        "content_ref": body.content_ref,
                        "privacy": body.privacy_level.value,
                        "reusable": int(body.reusable),
                        "key": body.idempotency_key,
                        "hash": digest,
                        "now": timestamp,
                    },
                )
                created = (
                    await session.execute(
                        text("SELECT * FROM evidence_items WHERE id=:id"),
                        {"id": evidence_id},
                    )
                ).mappings().one()
                return self._normalize(created), False

    async def list_project(self, owner_user_id: str, project_id: str) -> list[dict[str, Any]]:
        rows = await self.db.fetch_all(
            "SELECT * FROM evidence_items WHERE owner_user_id=:owner AND project_id=:project "
            "ORDER BY created_at ASC",
            {"owner": owner_user_id, "project": project_id},
        )
        return [self._normalize(row) for row in rows]

    async def get(self, owner_user_id: str, evidence_id: str) -> dict[str, Any]:
        row = await self.db.fetch_one(
            "SELECT * FROM evidence_items WHERE id=:id AND owner_user_id=:owner",
            {"id": evidence_id, "owner": owner_user_id},
        )
        if row is None:
            raise ValueError("evidence not found")
        return self._normalize(row)

    async def confirm(
        self, owner_user_id: str, evidence_id: str, body: EvidenceDecision
    ) -> tuple[dict[str, Any], bool]:
        return await self._decide(owner_user_id, evidence_id, body, "confirmed", True)

    async def reject(
        self, owner_user_id: str, evidence_id: str, body: EvidenceDecision
    ) -> tuple[dict[str, Any], bool]:
        return await self._decide(owner_user_id, evidence_id, body, "rejected", False)

    async def revoke(
        self, owner_user_id: str, evidence_id: str, body: EvidenceRevocation
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        evidence = await self.get(owner_user_id, evidence_id)
        impact = await self._invalidation_impact(
            owner_user_id, evidence["project_id"], evidence_id
        )
        if evidence["decision_idempotency_key"] == body.idempotency_key:
            if evidence["decision_request_hash"] != digest:
                raise IdempotencyConflictException()
            return {**evidence, "invalidation": impact}, True
        if evidence["version"] != body.expected_evidence_version:
            raise VersionConflictException(evidence["version"], body.expected_evidence_version)
        if evidence["confirmation_status"] != "confirmed":
            raise ValueError("only confirmed evidence can be revoked")

        timestamp = now()
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                updated = await session.execute(
                    text(
                        "UPDATE evidence_items SET confirmation_status='revoked',"
                        "reusable=0,revoked_at=:now,updated_at=:now,version=version+1,"
                        "decision_idempotency_key=:key,decision_request_hash=:hash "
                        "WHERE id=:id AND owner_user_id=:owner AND version=:expected "
                        "AND confirmation_status='confirmed'"
                    ),
                    {
                        "now": timestamp,
                        "key": body.idempotency_key,
                        "hash": digest,
                        "id": evidence_id,
                        "owner": owner_user_id,
                        "expected": body.expected_evidence_version,
                    },
                )
                if updated.rowcount != 1:
                    raise VersionConflictException(
                        evidence["version"] + 1, body.expected_evidence_version
                    )
                await self._invalidate_unpublished_candidates(
                    session,
                    owner_user_id,
                    evidence["project_id"],
                    impact["content_version_ids"],
                    timestamp,
                )
        revoked = await self.get(owner_user_id, evidence_id)
        return {**revoked, "invalidation": impact}, False

    async def assert_reusable(self, owner_user_id: str, evidence_id: str) -> dict[str, Any]:
        evidence = await self.get(owner_user_id, evidence_id)
        if evidence["confirmation_status"] != "confirmed" or not evidence["reusable"]:
            raise ValueError("evidence is not confirmed or has been revoked")
        return evidence

    async def _decide(
        self,
        owner_user_id: str,
        evidence_id: str,
        body: EvidenceDecision,
        status: str,
        reusable: bool,
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        evidence = await self.get(owner_user_id, evidence_id)
        if evidence["decision_idempotency_key"] == body.idempotency_key:
            if evidence["decision_request_hash"] != digest:
                raise IdempotencyConflictException()
            return evidence, True
        if evidence["version"] != body.expected_evidence_version:
            raise VersionConflictException(evidence["version"], body.expected_evidence_version)
        if evidence["confirmation_status"] != "proposed":
            if status == "confirmed" and evidence["confirmation_status"] == "confirmed":
                return evidence, True
            raise ValueError("evidence is no longer proposed")

        session = await self.db.get_session()
        async with session:
            async with session.begin():
                updated = await session.execute(
                    text(
                        "UPDATE evidence_items SET confirmation_status=:status,"
                        "reusable=:reusable,updated_at=:now,version=version+1,"
                        "decision_idempotency_key=:key,decision_request_hash=:hash "
                        "WHERE id=:id AND owner_user_id=:owner AND version=:expected "
                        "AND confirmation_status='proposed'"
                    ),
                    {
                        "status": status,
                        "reusable": int(reusable),
                        "now": now(),
                        "key": body.idempotency_key,
                        "hash": digest,
                        "id": evidence_id,
                        "owner": owner_user_id,
                        "expected": body.expected_evidence_version,
                    },
                )
                if updated.rowcount != 1:
                    raise VersionConflictException(
                        evidence["version"] + 1, body.expected_evidence_version
                    )
        return await self.get(owner_user_id, evidence_id), False

    @staticmethod
    async def _invalidate_unpublished_candidates(
        session: Any,
        owner_user_id: str,
        project_id: str,
        version_ids: list[str],
        timestamp: str,
    ) -> None:
        if not version_ids:
            return
        placeholders = ",".join(f":version_{i}" for i in range(len(version_ids)))
        params = {f"version_{i}": value for i, value in enumerate(version_ids)}
        params.update({"owner": owner_user_id, "project": project_id, "now": timestamp})
        await session.execute(
            text(
                "UPDATE publish_hypotheses SET status='superseded' "
                f"WHERE owner_user_id=:owner AND project_id=:project "
                f"AND content_version_id IN ({placeholders}) AND status='locked'"
            ),
            params,
        )
        await session.execute(
            text(
                "UPDATE blind_reviews SET calibration_state='calibration_invalid',"
                "eligible_for_rule_upgrade=0,eligibility_reason_code='revoked_evidence' "
                "WHERE owner_user_id=:owner AND publish_hypothesis_id IN ("
                "SELECT id FROM publish_hypotheses WHERE owner_user_id=:owner "
                f"AND project_id=:project AND content_version_id IN ({placeholders}))"
            ),
            params,
        )
        await session.execute(
            text(
                "UPDATE content_projects SET locked_publish_version_id=NULL,"
                "publish_hypothesis_id=NULL,calibration_state='insufficient',"
                "status=CASE WHEN status='ready_to_publish' THEN 'creating' ELSE status END,"
                "last_action='evidence_revoked',last_action_at=:now,updated_at=:now,"
                "version=version+1 WHERE id=:project AND owner_user_id=:owner "
                "AND locked_publish_version_id IN (" + placeholders + ")"
            ),
            params,
        )

    async def _invalidation_impact(
        self, owner_user_id: str, project_id: str, evidence_id: str
    ) -> dict[str, Any]:
        versions = await self.db.fetch_all(
            "SELECT id FROM content_versions WHERE owner_user_id=:owner "
            "AND project_id=:project AND evidence_snapshot_json LIKE :needle",
            {
                "owner": owner_user_id,
                "project": project_id,
                "needle": f"%{evidence_id}%",
            },
        )
        version_ids = [row["id"] for row in versions]
        segments = await self.db.fetch_all(
            "SELECT cs.id,cs.segment_key,cs.content_version_id FROM content_segments cs "
            "JOIN content_versions cv ON cv.id=cs.content_version_id "
            "WHERE cs.owner_user_id=:owner AND cs.project_id=:project "
            "AND cv.evidence_snapshot_json LIKE :needle ORDER BY cs.ordinal",
            {
                "owner": owner_user_id,
                "project": project_id,
                "needle": f"%{evidence_id}%",
            },
        )
        return {
            "content_version_ids": version_ids,
            "affected_segments": [dict(row) for row in segments],
            "publication_lock_blocked": bool(version_ids),
            "required_action": "replace_evidence_or_answer_key_question",
        }

    @staticmethod
    def _normalize(row: Any) -> dict[str, Any]:
        result = dict(row)
        result["reusable"] = bool(result["reusable"])
        return result
