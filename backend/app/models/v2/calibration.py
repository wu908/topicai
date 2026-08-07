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


class PerformanceSnapshotCreate(StrictModel):
    captured_at: str = Field(min_length=1)
    source: Literal["manual", "screenshot"]
    result_availability: Literal["observed", "unavailable"] = "observed"
    unavailable_reason: str | None = Field(default=None, max_length=500)
    metrics: PerformanceMetrics = Field(default_factory=PerformanceMetrics)
    screenshot_material_id: str | None = None
    snapshot_extraction_id: str | None = None
    confirmed_by_user: bool
    supersedes_id: str | None = None
    expected_project_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def validate_result_availability(self):
        has_metric = any(value is not None for value in self.metrics.model_dump().values())
        if self.result_availability == "observed":
            if not has_metric:
                raise ValueError("at least one observed metric is required")
            if self.unavailable_reason is not None:
                raise ValueError("observed results cannot have an unavailable reason")
        else:
            if has_metric:
                raise ValueError("unavailable results cannot contain metrics")
            if not self.unavailable_reason or not self.unavailable_reason.strip():
                raise ValueError("unavailable results require a reason")
            self.unavailable_reason = self.unavailable_reason.strip()
        if self.snapshot_extraction_id and (
            self.source != "screenshot" or not self.screenshot_material_id
        ):
            raise ValueError(
                "snapshot extraction confirmation requires its screenshot material"
            )
        return self


class BlindReviewCreate(StrictModel):
    result_snapshot_ids: list[str] = Field(min_length=1)
    benchmark_sample_ids: list[str] = Field(default_factory=list)
    expected_project_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class BenchmarkMetrics(StrictModel):
    views: int | None = Field(default=None, ge=0)
    likes: int | None = Field(default=None, ge=0)
    favorites: int | None = Field(default=None, ge=0)
    comments: int | None = Field(default=None, ge=0)
    shares: int | None = Field(default=None, ge=0)
    follows_gained: int | None = Field(default=None, ge=0)


class BenchmarkSampleCreate(StrictModel):
    source_type: Literal["historical_project", "imported_post"]
    source_ref: str = Field(min_length=1, max_length=2000)
    project_id: str | None = None
    metric_snapshot_ids: list[str] = Field(default_factory=list)
    metrics: BenchmarkMetrics = Field(default_factory=BenchmarkMetrics)
    quality_state: Literal["verified", "partial", "legacy"]
    inclusion_state: Literal["included", "excluded"] = "excluded"
    exclusion_reason_code: str | None = Field(default=None, max_length=100)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def validate_source_and_inclusion(self):
        if self.source_type == "historical_project":
            if not self.project_id or not self.metric_snapshot_ids:
                raise ValueError(
                    "historical_project requires project_id and metric_snapshot_ids"
                )
        elif self.project_id is not None or self.metric_snapshot_ids:
            raise ValueError(
                "imported_post cannot reference internal projects or metric snapshots"
            )
        if self.inclusion_state == "excluded" and not self.exclusion_reason_code:
            raise ValueError("excluded samples require exclusion_reason_code")
        if self.inclusion_state == "included":
            if self.exclusion_reason_code:
                raise ValueError("included samples cannot have an exclusion reason")
            if self.quality_state == "legacy":
                raise ValueError("legacy samples cannot be included")
            if self.source_type == "imported_post" and not any(
                value is not None for value in self.metrics.model_dump().values()
            ):
                raise ValueError("included imported samples require an observed metric")
        return self


class BenchmarkSampleInclusionUpdate(StrictModel):
    inclusion_state: Literal["included", "excluded"]
    exclusion_reason_code: str | None = Field(default=None, max_length=100)
    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def validate_exclusion(self):
        if self.inclusion_state == "excluded" and not self.exclusion_reason_code:
            raise ValueError("excluded samples require exclusion_reason_code")
        if self.inclusion_state == "included" and self.exclusion_reason_code:
            raise ValueError("included samples cannot have an exclusion reason")
        return self


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
