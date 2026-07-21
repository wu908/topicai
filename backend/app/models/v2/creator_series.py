"""Contracts for AI-proposed, user-confirmed content series relationships."""

from typing import Literal

from pydantic import Field, model_validator

from app.models.v2.intent_actions import StrictModel


class SeriesDraft(StrictModel):
    name: str = Field(min_length=1, max_length=200)
    promise: str = Field(min_length=1, max_length=2000)
    rationale: str = Field(min_length=1, max_length=4000)
    continuation_prompt: str = Field(min_length=1, max_length=2000)
    limitations: list[str] = Field(default_factory=list, max_length=20)


class SeriesCandidateCreate(StrictModel):
    source_project_ids: list[str] = Field(min_length=2, max_length=20)
    expected_project_versions: dict[str, int] = Field(min_length=2, max_length=20)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def validate_sources(self):
        if len(set(self.source_project_ids)) != len(self.source_project_ids):
            raise ValueError("source_project_ids must be unique")
        if set(self.expected_project_versions) != set(self.source_project_ids):
            raise ValueError("expected_project_versions must match source_project_ids")
        if any(version < 1 for version in self.expected_project_versions.values()):
            raise ValueError("expected project versions must be positive")
        return self


class SeriesDecision(StrictModel):
    decision: Literal["confirm", "reject"]
    confirmed_name: str | None = Field(default=None, max_length=200)
    confirmed_promise: str | None = Field(default=None, max_length=2000)
    confirmed_continuation_prompt: str | None = Field(default=None, max_length=2000)
    reason: str | None = Field(default=None, max_length=2000)
    expected_series_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def validate_confirmed_values(self):
        for value in (
            self.confirmed_name,
            self.confirmed_promise,
            self.confirmed_continuation_prompt,
        ):
            if value is not None and not value.strip():
                raise ValueError("confirmed series values cannot be blank")
        return self


class SeriesRevocation(StrictModel):
    reason: str = Field(min_length=1, max_length=2000)
    expected_series_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)
