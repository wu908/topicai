"""Owner-scoped experiment assignment and privacy-safe validation exports."""

import hashlib
import re
import statistics
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException
from app.models.v2.experiment_metrics import ExperimentAssignmentUpsert, ExperimentId
from app.services.v2_utils import now, request_hash


class ExperimentAssignmentService:
    def __init__(self, db: Any):
        self.db = db

    async def upsert(
        self,
        owner_user_id: str,
        experiment_id: ExperimentId,
        body: ExperimentAssignmentUpsert,
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                replay = (
                    await session.execute(
                        text(
                            "SELECT * FROM experiment_assignment_events "
                            "WHERE owner_user_id=:owner AND idempotency_key=:key"
                        ),
                        {"owner": owner_user_id, "key": body.idempotency_key},
                    )
                ).mappings().first()
                if replay:
                    if replay["request_hash"] != digest:
                        raise IdempotencyConflictException()
                    return self._assignment_event_view(replay), True

                timestamp = now()
                existing = (
                    await session.execute(
                        text(
                            "SELECT * FROM experiment_assignments "
                            "WHERE owner_user_id=:owner AND experiment_id=:experiment"
                        ),
                        {"owner": owner_user_id, "experiment": experiment_id.value},
                    )
                ).mappings().first()
                if body.status == "active":
                    previous_active = (
                        await session.execute(
                            text(
                                "SELECT * FROM experiment_assignments WHERE owner_user_id=:owner "
                                "AND status='active' AND experiment_id<>:experiment"
                            ),
                            {"owner": owner_user_id, "experiment": experiment_id.value},
                        )
                    ).mappings().all()
                    await session.execute(
                        text(
                            "UPDATE experiment_assignments SET status='completed',"
                            "completed_at=:now WHERE owner_user_id=:owner AND status='active' "
                            "AND experiment_id<>:experiment"
                        ),
                        {
                            "owner": owner_user_id,
                            "experiment": experiment_id.value,
                            "now": timestamp,
                        },
                    )
                    for previous in previous_active:
                        await session.execute(
                            text(
                                "INSERT INTO experiment_assignment_events "
                                "(id,owner_user_id,assignment_id,experiment_id,from_status,to_status,"
                                "cohort,user_segment,assignment_source,exclusion_reason_code,"
                                "idempotency_key,request_hash,created_at) VALUES "
                                "(:id,:owner,:assignment,:experiment,'active','completed',:cohort,"
                                ":segment,:source,NULL,:key,:hash,:now)"
                            ),
                            {
                                "id": str(uuid.uuid4()),
                                "owner": owner_user_id,
                                "assignment": previous["id"],
                                "experiment": previous["experiment_id"],
                                "cohort": previous["cohort"],
                                "segment": previous["user_segment"],
                                "source": previous["assignment_source"],
                                "key": (
                                    f"{body.idempotency_key}:complete:{previous['experiment_id']}"
                                ),
                                "hash": digest,
                                "now": timestamp,
                            },
                        )

                assignment_id = existing["id"] if existing else str(uuid.uuid4())
                values = {
                    "id": assignment_id,
                    "owner": owner_user_id,
                    "experiment": experiment_id.value,
                    "cohort": body.cohort,
                    "segment": body.user_segment,
                    "source": body.assignment_source,
                    "status": body.status,
                    "reason": body.exclusion_reason_code,
                    "key": body.idempotency_key,
                    "hash": digest,
                    "now": timestamp,
                    "activated": timestamp if body.status == "active" else None,
                    "completed": timestamp if body.status in ("completed", "excluded") else None,
                }
                if existing:
                    await session.execute(
                        text(
                            "UPDATE experiment_assignments SET cohort=:cohort,user_segment=:segment,"
                            "assignment_source=:source,status=:status,exclusion_reason_code=:reason,"
                            "idempotency_key=:key,request_hash=:hash,assigned_at=:now,"
                            "activated_at=:activated,completed_at=:completed WHERE id=:id"
                        ),
                        values,
                    )
                else:
                    await session.execute(
                        text(
                            "INSERT INTO experiment_assignments "
                            "(id,owner_user_id,experiment_id,cohort,user_segment,assignment_source,"
                            "status,exclusion_reason_code,idempotency_key,request_hash,assigned_at,"
                            "activated_at,completed_at) VALUES "
                            "(:id,:owner,:experiment,:cohort,:segment,:source,:status,:reason,:key,"
                            ":hash,:now,:activated,:completed)"
                        ),
                        values,
                    )
                await session.execute(
                    text(
                        "INSERT INTO experiment_assignment_events "
                        "(id,owner_user_id,assignment_id,experiment_id,from_status,to_status,cohort,"
                        "user_segment,assignment_source,exclusion_reason_code,idempotency_key,"
                        "request_hash,created_at) VALUES "
                        "(:event_id,:owner,:id,:experiment,:from_status,:status,:cohort,:segment,"
                        ":source,:reason,:key,:hash,:now)"
                    ),
                    {**values, "event_id": str(uuid.uuid4()), "from_status": existing["status"] if existing else None},
                )
                row = (
                    await session.execute(
                        text("SELECT * FROM experiment_assignments WHERE id=:id"),
                        {"id": assignment_id},
                    )
                ).mappings().one()
        return self._assignment_row_view(row), False

    @staticmethod
    def _assignment_row_view(row: Any) -> dict[str, Any]:
        return {
            "experiment_id": row["experiment_id"],
            "cohort": row["cohort"],
            "user_segment": row["user_segment"],
            "status": row["status"],
            "assignment_source": row["assignment_source"],
            "assigned_at": row["assigned_at"],
            "activated_at": row["activated_at"],
            "completed_at": row["completed_at"],
            "exclusion_reason_code": row["exclusion_reason_code"],
        }

    @staticmethod
    def _assignment_event_view(event: Any) -> dict[str, Any]:
        status = event["to_status"]
        timestamp = event["created_at"]
        return {
            "experiment_id": event["experiment_id"],
            "cohort": event["cohort"],
            "user_segment": event["user_segment"],
            "status": status,
            "assignment_source": event["assignment_source"],
            "assigned_at": timestamp,
            "activated_at": timestamp if status == "active" else None,
            "completed_at": timestamp if status in ("completed", "excluded") else None,
            "exclusion_reason_code": event["exclusion_reason_code"],
        }


class ExperimentMetricsService:
    """Build metrics from immutable events without exporting content payloads."""

    MAX_WINDOW_DAYS = 90

    def __init__(self, db: Any):
        self.db = db

    async def export(
        self,
        owner_user_id: str,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        experiment_id: ExperimentId | None = None,
        cohort: str | None = None,
    ) -> dict[str, Any]:
        end = self._utc(end_at or datetime.now(UTC))
        start = self._utc(start_at or (end - timedelta(days=28)))
        if start >= end:
            raise ValueError("start_at must be earlier than end_at")
        if end - start > timedelta(days=self.MAX_WINDOW_DAYS):
            raise ValueError(f"metrics window cannot exceed {self.MAX_WINDOW_DAYS} days")

        filters = ["ae.owner_user_id=:owner", "ae.created_at>=:start", "ae.created_at<:end"]
        params: dict[str, Any] = {
            "owner": owner_user_id,
            "start": self._timestamp(start),
            "end": self._timestamp(end),
        }
        if experiment_id:
            filters.append("ae.experiment_id=:experiment")
            params["experiment"] = experiment_id.value
        if cohort:
            filters.append("ae.cohort=:cohort")
            params["cohort"] = cohort
        where = " AND ".join(filters)
        rows = await self.db.fetch_all(
            "SELECT ae.id,ae.action_id,ae.project_id,ae.event_type,ae.from_status,"
            "ae.to_status,ae.experiment_id,ae.cohort,ae.ai_trace_id,ae.latency_ms,"
            "ae.success,ae.error_code,ae.model_version,ae.prompt_version,ae.created_at,"
            "nba.action_type FROM action_events ae JOIN next_best_actions nba "
            f"ON nba.id=ae.action_id WHERE {where} ORDER BY ae.created_at,ae.id",
            params,
        )
        offered_ids = {row["action_id"] for row in rows if row["event_type"] == "proposed"}
        eligible = [row for row in rows if row["action_id"] in offered_ids]
        funnel = self._funnel(offered_ids, eligible)
        project_ids = sorted({row["project_id"] for row in eligible if row["project_id"]})
        calibration = await self._calibration(
            owner_user_id,
            project_ids,
            start,
            end,
            require_projects=experiment_id is not None or cohort is not None,
        )
        assignment_filters = ["owner_user_id=:owner"]
        assignment_params: dict[str, Any] = {"owner": owner_user_id}
        if experiment_id:
            assignment_filters.append("experiment_id=:experiment")
            assignment_params["experiment"] = experiment_id.value
        if cohort:
            assignment_filters.append("cohort=:cohort")
            assignment_params["cohort"] = cohort
        assignment = await self.db.fetch_one(
            "SELECT experiment_id,cohort,user_segment,status,assignment_source,assigned_at,"
            "activated_at,completed_at,exclusion_reason_code FROM experiment_assignments "
            f"WHERE {' AND '.join(assignment_filters)} ORDER BY assigned_at DESC LIMIT 1",
            assignment_params,
        )
        return {
            "schema_version": "action-metrics-v1",
            "scope": "owner_only_internal_validation",
            "window": {
                "start_at": start.isoformat(),
                "end_at": end.isoformat(),
                "timezone": "UTC",
                "end_exclusive": True,
            },
            "filters": {
                "experiment_id": experiment_id.value if experiment_id else None,
                "cohort": cohort,
            },
            "assignment": assignment,
            "action_funnel": funnel,
            "calibration_quality": calibration,
            "events": [self._safe_event(owner_user_id, row) for row in eligible],
            "privacy": {
                "excluded_fields": [
                    "payload_json",
                    "raw_content",
                    "material_content",
                    "email",
                    "credentials",
                    "api_keys",
                    "platform_tokens",
                ],
                "user_identifier": "domain-separated SHA-256 pseudonym",
            },
        }

    @staticmethod
    def _utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @staticmethod
    def _timestamp(value: datetime) -> str:
        return value.isoformat().replace("+00:00", "Z")

    @classmethod
    def _funnel(cls, offered_ids: set[str], rows: list[dict[str, Any]]) -> dict[str, Any]:
        denominator = len(offered_ids)
        accepted = {
            row["action_id"]
            for row in rows
            if row["event_type"] in ("accepted", "gate_confirmed")
        }
        rejected = {
            row["action_id"]
            for row in rows
            if row["event_type"] in ("deferred", "manual_selected", "gate_rejected")
        }
        completed = {row["action_id"] for row in rows if row["to_status"] == "completed"}
        failed = {row["action_id"] for row in rows if not row["success"]}
        latencies = [row["latency_ms"] for row in rows if row["latency_ms"] is not None]

        def metric(count: int, numerator: str) -> dict[str, Any]:
            return {
                "numerator": count,
                "denominator": denominator,
                "rate": count / denominator if denominator else None,
                "numerator_definition": numerator,
                "denominator_definition": (
                    "distinct actions with a proposed event inside the selected half-open UTC window"
                ),
                "missing_data_handling": (
                    "actions without a proposed event in the window are excluded; zero denominator returns null"
                ),
            }

        return {
            "offered": denominator,
            "accepted": metric(len(accepted), "offered actions with accepted or gate_confirmed event"),
            "rejected": metric(
                len(rejected),
                "offered actions with deferred, manual_selected, or gate_rejected event",
            ),
            "completed": metric(len(completed), "offered actions that reached completed status"),
            "failed": metric(len(failed), "offered actions with success=false"),
            "missing_latency_events": sum(row["latency_ms"] is None for row in rows),
            "median_latency_ms": statistics.median(latencies) if latencies else None,
        }

    async def _calibration(
        self,
        owner: str,
        project_ids: list[str],
        start: datetime,
        end: datetime,
        *,
        require_projects: bool,
    ) -> dict[str, Any]:
        if require_projects and not project_ids:
            return self._empty_calibration()
        params: dict[str, Any] = {
            "owner": owner,
            "start": self._timestamp(start),
            "end": self._timestamp(end),
        }
        project_filter = ""
        if project_ids:
            placeholders = []
            for index, project_id in enumerate(project_ids):
                key = f"project_{index}"
                params[key] = project_id
                placeholders.append(f":{key}")
            project_filter = f" AND project_id IN ({','.join(placeholders)})"
        reviews = await self.db.fetch_all(
            "SELECT calibration_state,contamination_status,eligible_for_rule_upgrade "
            "FROM blind_reviews WHERE owner_user_id=:owner AND created_at>=:start "
            f"AND created_at<:end{project_filter}",
            params,
        )
        observations = await self.db.fetch_all(
            "SELECT lifecycle_status,COUNT(*) AS count FROM observations "
            "WHERE owner_user_id=:owner AND created_at>=:start AND created_at<:end"
            f"{project_filter} GROUP BY lifecycle_status",
            params,
        )
        rules = await self.db.fetch_all(
            "SELECT status,COUNT(*) AS count FROM creator_rule_versions "
            "WHERE owner_user_id=:owner AND created_at>=:start AND created_at<:end "
            "GROUP BY status",
            {"owner": owner, "start": self._timestamp(start), "end": self._timestamp(end)},
        )
        total = len(reviews)
        valid_clean = sum(
            row["calibration_state"] == "valid" and row["contamination_status"] == "clean"
            for row in reviews
        )
        contaminated = sum(row["contamination_status"] != "clean" for row in reviews)
        eligible = sum(bool(row["eligible_for_rule_upgrade"]) for row in reviews)

        def rate(
            numerator: int,
            denominator: int,
            numerator_definition: str,
            denominator_definition: str,
        ) -> dict[str, Any]:
            return {
                "numerator": numerator,
                "denominator": denominator,
                "rate": numerator / denominator if denominator else None,
                "numerator_definition": numerator_definition,
                "denominator_definition": denominator_definition,
                "missing_data_handling": "zero denominator returns null; no result is imputed",
            }

        return {
            "total_reviews": total,
            "valid_clean_reviews": rate(
                valid_clean,
                total,
                "reviews marked valid with clean contamination status",
                "all owner-scoped reviews created inside the selected window",
            ),
            "contaminated_reviews": rate(
                contaminated,
                total,
                "reviews marked suspected or contaminated",
                "all owner-scoped reviews created inside the selected window",
            ),
            "eligible_rule_upgrades": rate(
                eligible,
                valid_clean,
                "reviews explicitly eligible for rule upgrade",
                "valid and clean reviews inside the selected window",
            ),
            "observations_by_status": {
                row["lifecycle_status"]: row["count"] for row in observations
            },
            "rule_versions_by_status": {row["status"]: row["count"] for row in rules},
        }

    @staticmethod
    def _empty_calibration() -> dict[str, Any]:
        def empty_metric(numerator_definition: str, denominator_definition: str):
            return {
                "numerator": 0,
                "denominator": 0,
                "rate": None,
                "numerator_definition": numerator_definition,
                "denominator_definition": denominator_definition,
                "missing_data_handling": "zero denominator returns null; no result is imputed",
            }

        review_denominator = "all owner-scoped reviews created inside the selected window"
        return {
            "total_reviews": 0,
            "valid_clean_reviews": empty_metric(
                "reviews marked valid with clean contamination status", review_denominator
            ),
            "contaminated_reviews": empty_metric(
                "reviews marked suspected or contaminated", review_denominator
            ),
            "eligible_rule_upgrades": empty_metric(
                "reviews explicitly eligible for rule upgrade",
                "valid and clean reviews inside the selected window",
            ),
            "observations_by_status": {},
            "rule_versions_by_status": {},
        }

    @staticmethod
    def _safe_event(owner: str, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "event_id": row["id"],
            "user_id_hash": hashlib.sha256(
                f"topicai-action-metrics-v1:{owner}".encode("utf-8")
            ).hexdigest(),
            "action_id": row["action_id"],
            "action_type": row["action_type"],
            "project_id": row["project_id"],
            "event_type": row["event_type"],
            "state_before": row["from_status"],
            "state_after": row["to_status"],
            "experiment_id": row["experiment_id"],
            "cohort": row["cohort"],
            "ai_trace_id": row["ai_trace_id"],
            "latency_ms": row["latency_ms"],
            "success": bool(row["success"]),
            "error_code": ExperimentMetricsService._safe_error_code(row["error_code"]),
            "model_version": row["model_version"],
            "prompt_version": row["prompt_version"],
            "occurred_at": row["created_at"],
        }

    @staticmethod
    def _safe_error_code(value: str | None) -> str | None:
        if value is None:
            return None
        return value if re.fullmatch(r"[A-Za-z0-9_.:-]{1,100}", value) else "invalid_error_code"
