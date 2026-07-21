"""Contracts for AI-proposed, user-confirmed creator viewpoints."""

from typing import Literal

from pydantic import Field, model_validator

from app.models.v2.intent_actions import StrictModel


class ViewpointDraft(StrictModel):
    statement: str = Field(min_length=1, max_length=2000)
    rationale: str = Field(min_length=1, max_length=4000)
    limitations: list[str] = Field(default_factory=list, max_length=20)


class ViewpointCandidateCreate(StrictModel):
    source_evidence_ids: list[str] = Field(min_length=1, max_length=20)
    source_content_version_id: str | None = Field(default=None, max_length=100)
    expected_project_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class ViewpointDecision(StrictModel):
    decision: Literal["confirm", "reject"]
    confirmed_statement: str | None = Field(default=None, max_length=2000)
    reason: str | None = Field(default=None, max_length=2000)
    expected_viewpoint_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def validate_confirmed_statement(self):
        if self.confirmed_statement is not None and not self.confirmed_statement.strip():
            raise ValueError("confirmed_statement cannot be blank")
        return self


class ViewpointRevocation(StrictModel):
    reason: str = Field(min_length=1, max_length=2000)
    expected_viewpoint_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)
