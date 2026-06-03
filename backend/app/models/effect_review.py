"""Effect review Pydantic schemas for TopicAI v4.0.

Defines EffectReview schema for 效果复盘 (effect review / cheat-on-content).
Supports blind prediction → actual comparison → attribution → learning loop.
"""

from typing import Any

from pydantic import BaseModel, Field


class EffectReview(BaseModel):
    """Effect review record (cheat-on-content integration).

    Supports the blind prediction → publish → attribute → learn cycle.

    Attributes:
        id: Review ID (UUID).
        user_id: User who created the review.
        topic_title: The topic/title being reviewed.
        prediction: Blind prediction data (immutable once saved).
        actual_result: Actual performance data (filled after publishing).
        attribution: Attribution analysis (prediction vs actual comparison).
        learnings: Key learnings and takeaways.
        created_at: Review creation timestamp.
    """

    id: str = Field(..., description="Review ID (UUID)")
    user_id: str = Field(..., description="User ID")
    topic_title: str = Field(..., description="Topic/title being reviewed")
    prediction: dict[str, Any] = Field(
        ..., description="Blind prediction data (immutable)"
    )
    actual_result: dict[str, Any] | None = Field(
        default=None, description="Actual performance data"
    )
    attribution: str | None = Field(
        default=None, description="Attribution analysis"
    )
    learnings: dict[str, Any] | None = Field(
        default=None, description="Key learnings"
    )
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")


class EffectPredictRequest(BaseModel):
    """Schema for blind prediction request.

    Attributes:
        topic_title: The topic/title to predict performance for.
        content_outline: Optional content outline for context.
    """

    topic_title: str = Field(
        ..., min_length=1, description="Topic/title to predict"
    )
    content_outline: str | None = Field(
        default=None, description="Content outline for context"
    )


class EffectAttributeRequest(BaseModel):
    """Schema for attribution request (post-publish).

    Attributes:
        review_id: The EffectReview ID from the prediction step.
        actual_data: Actual performance metrics.
    """

    review_id: str = Field(..., description="EffectReview ID")
    actual_data: dict[str, Any] = Field(
        ..., description="Actual performance metrics"
    )
