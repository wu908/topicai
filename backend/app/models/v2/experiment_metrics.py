"""Typed contracts for internal MVP experiment instrumentation."""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from app.models.v2.intent_actions import StrictModel


class ExperimentId(StrEnum):
    E1 = "E1"
    E2 = "E2"
    E3 = "E3"
    E4 = "E4"


class ExperimentAssignmentUpsert(StrictModel):
    cohort: Literal["control", "variant", "observational", "excluded"]
    user_segment: Literal["starter", "growth", "unknown"] = "unknown"
    assignment_source: Literal["manual_internal", "deterministic", "imported"] = (
        "manual_internal"
    )
    status: Literal["planned", "active", "completed", "excluded"] = "active"
    exclusion_reason_code: str | None = Field(default=None, max_length=100)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def validate_exclusion(self):
        if self.status == "excluded" and not self.exclusion_reason_code:
            raise ValueError("exclusion_reason_code is required when status is excluded")
        if self.cohort == "excluded" and self.status != "excluded":
            raise ValueError("excluded cohort requires excluded status")
        return self


class MetricsWindow(StrictModel):
    start_at: datetime
    end_at: datetime
    timezone: str = "UTC"
    end_exclusive: bool = True


class MetricsFilter(StrictModel):
    experiment_id: ExperimentId | None = None
    cohort: Literal["control", "variant", "observational", "excluded"] | None = None


class RateMetric(StrictModel):
    numerator: int = Field(ge=0)
    denominator: int = Field(ge=0)
    rate: float | None = Field(default=None, ge=0, le=1)
    numerator_definition: str
    denominator_definition: str
    missing_data_handling: str


class ActionFunnel(StrictModel):
    offered: int = Field(ge=0)
    accepted: RateMetric
    rejected: RateMetric
    completed: RateMetric
    failed: RateMetric
    missing_latency_events: int = Field(ge=0)
    median_latency_ms: float | None = Field(default=None, ge=0)


class CalibrationQuality(StrictModel):
    total_reviews: int = Field(ge=0)
    valid_clean_reviews: RateMetric
    contaminated_reviews: RateMetric
    eligible_rule_upgrades: RateMetric
    observations_by_status: dict[str, int]
    rule_versions_by_status: dict[str, int]


class ExperimentAssignmentView(StrictModel):
    experiment_id: ExperimentId
    cohort: Literal["control", "variant", "observational", "excluded"]
    user_segment: Literal["starter", "growth", "unknown"]
    status: Literal["planned", "active", "completed", "excluded"]
    assignment_source: Literal["manual_internal", "deterministic", "imported"]
    assigned_at: str
    activated_at: str | None = None
    completed_at: str | None = None
    exclusion_reason_code: str | None = None


class SafeActionEvent(StrictModel):
    event_id: str
    user_id_hash: str = Field(min_length=64, max_length=64)
    action_id: str
    action_type: str
    project_id: str | None = None
    event_type: str
    state_before: str | None = None
    state_after: str
    experiment_id: ExperimentId | None = None
    cohort: Literal["control", "variant", "observational", "excluded"] | None = None
    ai_trace_id: str | None = None
    latency_ms: int | None = Field(default=None, ge=0)
    success: bool
    error_code: str | None = Field(default=None, max_length=100)
    model_version: str | None = None
    prompt_version: str | None = None
    occurred_at: str


class PrivacyBoundary(StrictModel):
    excluded_fields: list[str]
    user_identifier: str


class ActionMetricsExport(StrictModel):
    schema_version: Literal["action-metrics-v1"]
    scope: Literal["owner_only_internal_validation"]
    window: MetricsWindow
    filters: MetricsFilter
    assignment: ExperimentAssignmentView | None = None
    action_funnel: ActionFunnel
    calibration_quality: CalibrationQuality
    events: list[SafeActionEvent]
    privacy: PrivacyBoundary
