"""Pre-publication judgment contracts without performance prediction."""

from typing import Literal

from pydantic import BaseModel, Field


ExpectedBehavior = Literal["save", "comment", "profile_visit", "follow", "other"]
HypothesisAmendmentType = Literal[
    "clarification", "correction", "context", "evidence_update"
]


class PublishHypothesisLock(BaseModel):
    content_version_id: str = Field(min_length=1)
    audience_problem: str = Field(min_length=1, max_length=1000)
    reader_promise: str = Field(min_length=1, max_length=1000)
    expected_behaviors: list[ExpectedBehavior] = Field(min_length=1)
    basis_refs: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    expected_project_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class PublishHypothesisAmendmentCreate(BaseModel):
    amendment_type: HypothesisAmendmentType
    statement: str = Field(min_length=1, max_length=2000)
    reason: str = Field(min_length=1, max_length=2000)
    idempotency_key: str = Field(min_length=1, max_length=200)
