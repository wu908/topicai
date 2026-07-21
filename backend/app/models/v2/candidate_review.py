"""Contracts for immutable candidate segment review."""

from typing import Literal

from pydantic import Field, model_validator

from app.models.v2.intent_actions import StrictModel


class SegmentDecisionInput(StrictModel):
    content_version_id: str = Field(min_length=1, max_length=100)
    decision: Literal["accept", "reject", "replace"]
    replacement_text: str | None = Field(default=None, max_length=20000)
    reason: str | None = Field(default=None, max_length=1000)
    expected_segment_version: int = Field(ge=0)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def require_replacement_for_replace(self):
        if self.decision == "replace" and not (self.replacement_text or "").strip():
            raise ValueError("replacement_text is required when replacing a segment")
        return self


class CandidateRevisionInput(StrictModel):
    content_version_id: str = Field(min_length=1, max_length=100)
    expected_project_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class CandidateRestoreInput(StrictModel):
    source_version_id: str = Field(min_length=1, max_length=100)
    expected_project_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)
