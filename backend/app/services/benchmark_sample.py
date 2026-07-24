"""Owner-scoped benchmark samples for relative calibration only."""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.models.v2.calibration import (
    BenchmarkSampleCreate,
    BenchmarkSampleInclusionUpdate,
)
from app.services.v2_utils import decode_json_fields, now, request_hash


class BenchmarkSampleService:
    def __init__(self, db: Any):
        self.db = db

    async def list(self, owner_user_id: str) -> list[dict[str, Any]]:
        rows = await self.db.fetch_all(
            "SELECT * FROM benchmark_samples WHERE owner_user_id=:owner "
            "ORDER BY updated_at DESC,id",
            {"owner": owner_user_id},
        )
        return [self._normalize(row) for row in rows]

    async def create(
        self, owner_user_id: str, body: BenchmarkSampleCreate
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                existing = (
                    await session.execute(
                        text(
                            "SELECT * FROM benchmark_samples WHERE owner_user_id=:owner "
                            "AND idempotency_key=:key"
                        ),
                        {"owner": owner_user_id, "key": body.idempotency_key},
                    )
                ).mappings().first()
                if existing:
                    if existing["request_hash"] != digest:
                        raise IdempotencyConflictException()
                    return self._normalize(existing), True

                metrics = body.metrics.model_dump()
                publish_record_id = None
                if body.source_type == "historical_project":
                    metrics, publish_record_id = await self._historical_metrics(
                        session,
                        owner_user_id,
                        body.project_id,
                        body.metric_snapshot_ids,
                    )
                self._assert_includable(
                    body.inclusion_state, body.quality_state, metrics
                )

                sample_id = str(uuid.uuid4())
                timestamp = now()
                await session.execute(
                    text(
                        "INSERT INTO benchmark_samples ("
                        "id,owner_user_id,source_type,source_ref,project_id,publish_record_id,"
                        "metric_snapshot_ids_json,metrics_json,quality_state,inclusion_state,"
                        "exclusion_reason_code,version,idempotency_key,request_hash,created_at,"
                        "updated_at) VALUES (:id,:owner,:source_type,:source_ref,:project,"
                        ":record,:snapshots,:metrics,:quality,:inclusion,:reason,1,:key,:hash,"
                        ":now,:now)"
                    ),
                    {
                        "id": sample_id,
                        "owner": owner_user_id,
                        "source_type": body.source_type,
                        "source_ref": body.source_ref,
                        "project": body.project_id,
                        "record": publish_record_id,
                        "snapshots": json.dumps(body.metric_snapshot_ids),
                        "metrics": json.dumps(metrics),
                        "quality": body.quality_state,
                        "inclusion": body.inclusion_state,
                        "reason": body.exclusion_reason_code,
                        "key": body.idempotency_key,
                        "hash": digest,
                        "now": timestamp,
                    },
                )
                await self._event(
                    session,
                    owner_user_id,
                    sample_id,
                    None,
                    body.inclusion_state,
                    body.exclusion_reason_code,
                    1,
                    body.idempotency_key,
                    digest,
                    timestamp,
                )
                created = (
                    await session.execute(
                        text("SELECT * FROM benchmark_samples WHERE id=:id"),
                        {"id": sample_id},
                    )
                ).mappings().one()
                return self._normalize(created), False

    async def set_inclusion(
        self,
        owner_user_id: str,
        sample_id: str,
        body: BenchmarkSampleInclusionUpdate,
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(
            {"sample_id": sample_id, "body": body.model_dump(mode="json")}
        )
        replay = await self.db.fetch_one(
            "SELECT * FROM benchmark_sample_events WHERE owner_user_id=:owner "
            "AND idempotency_key=:key",
            {"owner": owner_user_id, "key": body.idempotency_key},
        )
        if replay:
            if replay["request_hash"] != digest:
                raise IdempotencyConflictException()
            return await self.get(owner_user_id, sample_id), True

        sample = await self.get(owner_user_id, sample_id)
        if sample["version"] != body.expected_version:
            raise VersionConflictException(sample["version"], body.expected_version)
        if sample["inclusion_state"] == body.inclusion_state:
            raise ValueError("benchmark sample already has the requested inclusion state")
        self._assert_includable(
            body.inclusion_state, sample["quality_state"], sample["metrics"]
        )

        timestamp = now()
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                updated = await session.execute(
                    text(
                        "UPDATE benchmark_samples SET inclusion_state=:state,"
                        "exclusion_reason_code=:reason,version=version+1,updated_at=:now "
                        "WHERE id=:id AND owner_user_id=:owner AND version=:expected"
                    ),
                    {
                        "state": body.inclusion_state,
                        "reason": body.exclusion_reason_code,
                        "now": timestamp,
                        "id": sample_id,
                        "owner": owner_user_id,
                        "expected": body.expected_version,
                    },
                )
                if updated.rowcount != 1:
                    raise VersionConflictException(
                        sample["version"] + 1, body.expected_version
                    )
                await self._event(
                    session,
                    owner_user_id,
                    sample_id,
                    sample["inclusion_state"],
                    body.inclusion_state,
                    body.exclusion_reason_code,
                    body.expected_version + 1,
                    body.idempotency_key,
                    digest,
                    timestamp,
                )
        return await self.get(owner_user_id, sample_id), False

    async def get(self, owner_user_id: str, sample_id: str) -> dict[str, Any]:
        row = await self.db.fetch_one(
            "SELECT * FROM benchmark_samples WHERE id=:id AND owner_user_id=:owner",
            {"id": sample_id, "owner": owner_user_id},
        )
        if row is None:
            raise ValueError("benchmark sample not found")
        return self._normalize(row)

    @staticmethod
    async def _historical_metrics(
        session: Any,
        owner_user_id: str,
        project_id: str | None,
        snapshot_ids: list[str],
    ) -> tuple[dict[str, int | None], str]:
        project = (
            await session.execute(
                text(
                    "SELECT id FROM content_projects WHERE id=:id "
                    "AND owner_user_id=:owner AND deleted_at IS NULL"
                ),
                {"id": project_id, "owner": owner_user_id},
            )
        ).first()
        if project is None:
            raise ValueError("benchmark source project not found")

        snapshots = []
        for snapshot_id in dict.fromkeys(snapshot_ids):
            snapshot = (
                await session.execute(
                    text(
                        "SELECT * FROM performance_snapshots_v2 WHERE id=:id "
                        "AND owner_user_id=:owner AND project_id=:project "
                        "AND confirmed_by_user=1"
                    ),
                    {
                        "id": snapshot_id,
                        "owner": owner_user_id,
                        "project": project_id,
                    },
                )
            ).mappings().first()
            if snapshot is None:
                raise ValueError(f"benchmark metric snapshot not found: {snapshot_id}")
            successor = (
                await session.execute(
                    text(
                        "SELECT id FROM performance_snapshots_v2 WHERE supersedes_id=:id"
                    ),
                    {"id": snapshot_id},
                )
            ).first()
            if successor:
                raise ValueError(f"benchmark metric snapshot was superseded: {snapshot_id}")
            snapshots.append(snapshot)
        record_ids = {item["publish_record_id"] for item in snapshots}
        if len(record_ids) != 1:
            raise ValueError("benchmark snapshots must belong to one publication")
        latest = max(snapshots, key=lambda item: (item["captured_at"], item["id"]))
        return json.loads(latest["metrics_json"]), latest["publish_record_id"]

    @staticmethod
    def _assert_includable(
        inclusion_state: str, quality_state: str, metrics: dict[str, Any]
    ) -> None:
        if inclusion_state != "included":
            return
        if quality_state == "legacy":
            raise ValueError("legacy benchmark samples cannot be included")
        if not any(value is not None for value in metrics.values()):
            raise ValueError("included benchmark samples require an observed metric")

    @staticmethod
    async def _event(
        session: Any,
        owner: str,
        sample_id: str,
        from_state: str | None,
        to_state: str,
        reason: str | None,
        version: int,
        key: str,
        digest: str,
        timestamp: str,
    ) -> None:
        await session.execute(
            text(
                "INSERT INTO benchmark_sample_events ("
                "id,owner_user_id,benchmark_sample_id,from_state,to_state,reason_code,"
                "sample_version,idempotency_key,request_hash,created_at) VALUES ("
                ":id,:owner,:sample,:from_state,:to_state,:reason,:version,:key,:hash,:now)"
            ),
            {
                "id": str(uuid.uuid4()),
                "owner": owner,
                "sample": sample_id,
                "from_state": from_state,
                "to_state": to_state,
                "reason": reason,
                "version": version,
                "key": key,
                "hash": digest,
                "now": timestamp,
            },
        )

    @staticmethod
    def _normalize(row: Any) -> dict[str, Any]:
        return decode_json_fields(row, "metric_snapshot_ids_json", "metrics_json")
