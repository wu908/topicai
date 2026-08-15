"""ContentProject and immutable content-version contracts."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.v2.intent_actions import ContentIntent


class ProjectStatus(StrEnum):
    INBOX = "inbox"
    PREPARING = "preparing"
    CREATING = "creating"
    READY_TO_PUBLISH = "ready_to_publish"
    PUBLISHED = "published"
    AWAITING_REVIEW = "awaiting_review"
    SETTLED = "settled"


# States a project may be created in. Every other movement must go through
# ``ProjectTransition`` with its reason + expected-version checks.
_ENTRY_STATES = frozenset({ProjectStatus.INBOX, ProjectStatus.PREPARING})


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

    @field_validator("status")
    @classmethod
    def _restrict_to_entry_states(cls, value: ProjectStatus) -> ProjectStatus:
        """Reject non-entry states so creation cannot bypass the
        ``ProjectTransition`` state machine (e.g. creating a project that
        is already ``published``/``settled``)."""
        if value not in _ENTRY_STATES:
            allowed = ", ".join(sorted(state.value for state in _ENTRY_STATES))
            raise ValueError(f"projects can only be created in an entry state ({allowed})")
        return value


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
