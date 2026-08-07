"""Screenshot metric extraction contracts."""

from typing import Literal

from pydantic import Field, model_validator

from app.models.v2.calibration import PerformanceMetrics
from app.models.v2.intent_actions import StrictModel


class SnapshotExtractionCreate(StrictModel):
    material_id: str = Field(min_length=1, max_length=100)
    idempotency_key: str = Field(min_length=1, max_length=200)


class SnapshotMetricsProposal(PerformanceMetrics):
    @model_validator(mode="after")
    def require_metric(self):
        if not any(value is not None for value in self.model_dump().values()):
            raise ValueError("screenshot extraction must propose at least one metric")
        return self


class SnapshotExtractionTraceView(StrictModel):
    capability: Literal["vision"]
    confidence_label: Literal["high", "medium", "low", "unavailable"]
    limitations: list[str]
    outcome: Literal["success", "fallback", "failed", "cancelled"]


class SnapshotExtractionView(StrictModel):
    id: str
    material_id: str | None
    metrics: PerformanceMetrics
    confirmed_by_user: bool
    user_decision: Literal["pending", "confirmed", "rejected", "edited"]
    decided_at: str | None
    snapshot_id: str | None
    ai_trace: SnapshotExtractionTraceView
