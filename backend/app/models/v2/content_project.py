"""ContentProject and immutable content-version contracts."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from app.models.v2.intent_actions import ContentIntent


class ProjectStatus(StrEnum):
    INBOX = "inbox"
    PREPARING = "preparing"
    CREATING = "creating"
    READY_TO_PUBLISH = "ready_to_publish"
    PUBLISHED = "published"
    AWAITING_REVIEW = "awaiting_review"
    SETTLED = "settled"


class ContentProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    primary_goal: Literal["stable_publish", "follower_growth", "experiment"] = "stable_publish"
    target_audience: str = Field(default="", max_length=500)
    content_intent: ContentIntent | None = None
    content_format: Literal["graphic_note", "vlog_plan"] = "graphic_note"
    audience_change: str | None = Field(default=None, max_length=1000)
    status: ProjectStatus = ProjectStatus.PREPARING
    planned_publish_at: str | None = None
    opportunity_id: str | None = None
    starter_sprint_id: str | None = None
    idempotency_key: str = Field(min_length=1, max_length=200)


class ProjectTransition(BaseModel):
    to_status: ProjectStatus
    reason: str = Field(min_length=1, max_length=200)
    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class ContentVersionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body_text: str = Field(min_length=1)
    cover_plan: str = ""
    image_plan: list[dict] = Field(default_factory=list)
    parent_version_id: str | None = None
    change_origin: Literal["user", "ai", "import"] = "user"
    change_summary: str | None = None
    evidence_snapshot: list[dict] = Field(default_factory=list)
    expected_project_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)
