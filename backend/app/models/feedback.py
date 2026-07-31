"""Feedback Pydantic schemas for TopicAI v4.0.

Defines FeedbackRecord and FeedbackAnalysis schemas for
效果反馈 (effect feedback) collection and analysis.

Spec-007 T016: ``source_type`` enum expanded to match the seven ``SourceType``
values declared in ``frontend/src/types/enums.ts`` (US3, FR-005):
``topic | title | idea | viral | track | publish | effect_review``.
The narrower ``topic|viral|title|idea`` set is retained as a forward-compat
shim on the request side via ``SUBMITTABLE_SOURCE_TYPE_PATTERN`` so the
existing ``POST /api/v1/feedback`` endpoint keeps working unchanged.
"""

from typing import Any

from pydantic import BaseModel, Field

# Mirrors frontend/src/types/enums.ts -> SourceType. Keep in sync.
SOURCE_TYPES: tuple[str, ...] = (
    "topic",
    "title",
    "idea",
    "viral",
    "track",
    "publish",
    "effect_review",
    "opportunity",
)
SOURCE_TYPE_PATTERN = r"^(topic|title|idea|viral|track|publish|effect_review|opportunity)$"

# Subset accepted by the legacy POST /api/v1/feedback submit endpoint.
# Persisted rows may use the wider enum; new submissions go through T056's
# async endpoint which accepts the full set.
SUBMITTABLE_SOURCE_TYPES: tuple[str, ...] = (
    "topic",
    "title",
    "idea",
    "viral",
)
SUBMITTABLE_SOURCE_TYPE_PATTERN = r"^(topic|title|idea|viral)$"


class FeedbackRecord(BaseModel):
    """A single feedback record from a user.

    Captures 👍👎 feedback on AI outputs (topics, titles, viral analyses, etc.).

    Attributes:
        id: Feedback record ID (UUID).
        user_id: User who submitted feedback.
        source_type: Type of AI output (see SOURCE_TYPES for the full enum).
        source_id: ID of the AI output being rated.
        feedback_type: 'thumb_up', 'thumb_down', 'adopted', 'modified', 'ignored'.
        feedback_value: Optional free-text feedback.
        reason: Optional reason for the feedback.
        created_at: Feedback timestamp.
    """

    id: str = Field(..., description="Feedback record ID (UUID)")
    user_id: str = Field(..., description="User ID")
    source_type: str = Field(
        ...,
        pattern=SOURCE_TYPE_PATTERN,
        description="Type of AI output (SourceType enum)",
    )
    source_id: str = Field(..., description="ID of the AI output")
    feedback_type: str = Field(
        ...,
        pattern=r"^(thumb_up|thumb_down|adopted|modified|ignored|adopt|save|reject)$",
        description="Feedback type",
    )
    feedback_value: str | None = Field(
        default=None, description="Optional free-text feedback"
    )
    reason: str | None = Field(
        default=None, description="Optional reason"
    )
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")


class FeedbackSubmitRequest(BaseModel):
    """Schema for submitting feedback.

    Attributes:
        target_type: 'topic', 'viral', 'title', or 'idea'.
        target_id: ID of the AI output.
        feedback_type: 'thumb_up', 'thumb_down', 'adopted', 'modified', 'ignored'.
        reason: Optional reason for the feedback.
    """

    target_type: str = Field(
        ...,
        pattern=SUBMITTABLE_SOURCE_TYPE_PATTERN,
        description="Type of AI output (legacy 4-value set)",
    )
    target_id: str = Field(..., description="ID of the AI output")
    feedback_type: str = Field(
        ...,
        pattern=r"^(thumb_up|thumb_down|adopted|modified|ignored)$",
        description="Feedback type",
    )
    reason: str | None = Field(
        default=None, description="Optional reason"
    )


class FeedbackAnalysis(BaseModel):
    """LLM analysis of accumulated feedback.

    Identifies success/failure patterns and adjusts recommendation weights.

    Attributes:
        id: Analysis ID (UUID).
        user_id: User whose feedback was analyzed.
        feedback_record_id: Associated feedback record.
        success_factors: Identified success factors (JSON).
        failure_factors: Identified failure factors (JSON).
        weight_adjustments: Rubric weight adjustments (JSON).
        excluded_patterns: Patterns to exclude from future recommendations.
        created_at: Analysis timestamp.
    """

    id: str = Field(..., description="Analysis ID (UUID)")
    user_id: str = Field(..., description="User ID")
    feedback_record_id: str = Field(
        ..., description="Associated feedback record ID"
    )
    success_factors: dict[str, Any] | None = Field(
        default=None, description="Identified success factors"
    )
    failure_factors: dict[str, Any] | None = Field(
        default=None, description="Identified failure factors"
    )
    weight_adjustments: dict[str, float] = Field(
        default_factory=dict, description="Rubric weight adjustments"
    )
    excluded_patterns: list[str] = Field(
        default_factory=list, description="Excluded patterns"
    )
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
