"""Version-bound pre-publication check contracts."""

from typing import Literal

from pydantic import Field

from app.models.v2.intent_actions import StrictModel


class PublishCheckCreate(StrictModel):
    content_version_id: str = Field(min_length=1, max_length=100)
    idempotency_key: str = Field(min_length=1, max_length=200)


class PublishCheckResolution(StrictModel):
    findings: dict[str, Literal["acknowledged", "resolved"]] = Field(min_length=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class AIPublishFinding(StrictModel):
    field: Literal["title", "body_text", "cover_plan"]
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    reason: str = Field(min_length=1, max_length=1000)
    severity: Literal["low", "medium", "high"]


class AIPublishCheckOutput(StrictModel):
    findings: list[AIPublishFinding] = Field(default_factory=list, max_length=20)


class PublishCheckFindingView(AIPublishFinding):
    id: str
    excerpt: str
    rule_source: str
    rule_updated_at: str
    status: Literal["open", "acknowledged", "resolved"]


class PublishCheckResolutionView(StrictModel):
    id: str
    findings: dict[str, Literal["acknowledged", "resolved"]]
    created_at: str


class PublishCheckView(StrictModel):
    id: str
    project_id: str
    content_version_id: str
    status: Literal["clear", "needs_attention", "stale"]
    stale: bool
    findings: list[PublishCheckFindingView]
    limitations: list[str]
    resolutions: list[PublishCheckResolutionView]
    ai_trace_id: str | None
    rule_version: str
    rule_updated_at: str
    checked_at: str
