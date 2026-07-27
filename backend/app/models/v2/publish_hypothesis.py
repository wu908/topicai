"""Pre-publication judgment contracts without performance prediction."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.v2.intent_actions import ContentIntent


class StrictModel(BaseModel):
    """Base model with extra='forbid' to reject unexpected fields."""
    model_config = ConfigDict(extra="forbid")


ExpectedBehavior = Literal["save", "comment", "profile_visit", "follow", "other"]
HypothesisAmendmentType = Literal[
    "clarification", "correction", "context", "evidence_update"
]


class PublishHypothesisLock(StrictModel):
    """Lock Content Intent and Complete Publish Judgment before publication.

    Shared skeleton (all intents): audience_change, primary_response,
    supporting_responses, basis_refs, uncertainties, observation_window_days.

    Intent-specific required fields:
    - solve: audience_problem + reader_promise
    - share: viewpoint_anchor
    - record: continuation_promise
    """
    content_version_id: str = Field(min_length=1)
    content_intent: ContentIntent

    # Shared skeleton (all intents required)
    audience_change: str = Field(min_length=1, max_length=1000)
    primary_response: ExpectedBehavior
    supporting_responses: list[ExpectedBehavior] = Field(
        default_factory=list, max_length=2
    )
    basis_refs: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    observation_window_days: int = Field(ge=1, le=365)

    # solve-specific (required only when content_intent == "solve")
    audience_problem: str | None = Field(default=None, max_length=1000)
    reader_promise: str | None = Field(default=None, max_length=1000)

    # share-specific (required only when content_intent == "share")
    viewpoint_anchor: str | None = Field(default=None, max_length=1000)

    # record-specific (required only when content_intent == "record")
    continuation_promise: str | None = Field(default=None, max_length=1000)

    expected_project_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def require_intent_specific_fields(self):
        """Enforce intent-specific required fields and cross-intent exclusion."""
        if self.content_intent == ContentIntent.SOLVE:
            if not self.audience_problem or not self.reader_promise:
                raise ValueError(
                    "solve intent requires audience_problem and reader_promise"
                )
            if self.viewpoint_anchor or self.continuation_promise:
                raise ValueError(
                    "solve intent cannot include share/record-specific fields"
                )
        elif self.content_intent == ContentIntent.SHARE:
            if not self.viewpoint_anchor:
                raise ValueError("share intent requires viewpoint_anchor")
            if (
                self.audience_problem
                or self.reader_promise
                or self.continuation_promise
            ):
                raise ValueError(
                    "share intent cannot include solve/record-specific fields"
                )
        elif self.content_intent == ContentIntent.RECORD:
            if not self.continuation_promise:
                raise ValueError("record intent requires continuation_promise")
            if (
                self.audience_problem
                or self.reader_promise
                or self.viewpoint_anchor
            ):
                raise ValueError(
                    "record intent cannot include solve/share-specific fields"
                )
        return self


class PublishHypothesisAmendmentCreate(BaseModel):
    amendment_type: HypothesisAmendmentType
    statement: str = Field(min_length=1, max_length=2000)
    reason: str = Field(min_length=1, max_length=2000)
    idempotency_key: str = Field(min_length=1, max_length=200)


class RetrospectiveIntentClassification(StrictModel):
    """User-confirmed post-publication intent classification for historical content.

    Does NOT modify content_intent (remains NULL for unclassified historical
    content). Writes to the separate retrospective_intent column only.
    The retrospective classification scopes future comparison and learning
    without changing the Publication Intent.
    """
    retrospective_intent: ContentIntent
    classification_basis: str = Field(min_length=1, max_length=2000)
    expected_project_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)
