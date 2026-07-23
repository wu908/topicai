"""Typed contracts for manual publication and judgment calibration."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PublishRecordCreate(StrictModel):
    content_version_id: str = Field(min_length=1)
    publication_gate_id: str = Field(min_length=1)
    note_url: str | None = Field(default=None, max_length=2000)
    published_at: str = Field(min_length=1)
    expected_project_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class PerformanceMetrics(StrictModel):
    views: int | None = Field(default=None, ge=0)
    likes: int | None = Field(default=None, ge=0)
    favorites: int | None = Field(default=None, ge=0)
    comments: int | None = Field(default=None, ge=0)
    shares: int | None = Field(default=None, ge=0)
    follows_gained: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def require_observed_metric(self):
        if not any(value is not None for value in self.model_dump().values()):
            raise ValueError("at least one observed metric is required")
        return self


class PerformanceSnapshotCreate(StrictModel):
    captured_at: str = Field(min_length=1)
    source: Literal["manual", "screenshot"]
    metrics: PerformanceMetrics
    screenshot_material_id: str | None = None
    confirmed_by_user: bool
    supersedes_id: str | None = None
    expected_project_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class BlindReviewCreate(StrictModel):
    result_snapshot_ids: list[str] = Field(min_length=1)
    expected_project_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class ObservationCreate(StrictModel):
    statement: str = Field(min_length=1, max_length=2000)
    scope: dict = Field(default_factory=dict)
    next_test: str = Field(min_length=1, max_length=2000)
    expected_project_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


ObservationStatus = Literal[
    "observing", "pending_validation", "absorbed", "refuted", "archived"
]


class ObservationTransition(StrictModel):
    to_status: ObservationStatus
    reason: str = Field(min_length=1, max_length=2000)
    expected_observation_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)
