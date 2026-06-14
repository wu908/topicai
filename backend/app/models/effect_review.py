"""Effect review Pydantic schemas for TopicAI v4.0.

Defines EffectReview schema for 效果复盘 (effect review / cheat-on-content).
Supports blind prediction → actual comparison → attribution → learning loop.

Spec-007 T015 adds the typed payload models used by ``EffectReviewChain``
(US4, FR-007): ``PredictionPayload``, ``DimensionalConclusion``,
``AttributionPayload``, and ``LearningsPayload``. They are the contract
that chain outputs must parse into (Constitution Principle VII) and the
shape that is serialized into the ``effect_reviews`` JSON columns.
"""

from typing import Any

from pydantic import BaseModel, Field


# --- Spec-007 T015: typed payload models (US4, FR-007) -------------------


class PredictionPayload(BaseModel):
    """Blind prediction emitted by ``EffectReviewChain.predict``.

    All four numeric fields are bounded ``>= 0`` so that LLMs returning
    negative estimates (a known failure mode) are rejected at parse time
    and the chain can fall back to template output.
    """

    estimated_views: int = Field(..., ge=0, description="Predicted view count")
    estimated_likes: int = Field(..., ge=0, description="Predicted like count")
    estimated_comments: int = Field(..., ge=0, description="Predicted comment count")
    engagement_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Predicted engagement rate as a 0..1 fraction",
    )
    caveat: str = Field(
        ...,
        min_length=1,
        description="Honest disclaimer of prediction uncertainty",
    )


class DimensionalConclusion(BaseModel):
    """One axis of attribution analysis (3..5 returned per attribution)."""

    dimension: str = Field(..., min_length=1, description="Dimension key, e.g. 'hook_strength'")
    conclusion: str = Field(..., min_length=1, description="Human-readable conclusion")
    relevance: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="0..1 weight of this dimension in the overall verdict",
    )
    evidence: str = Field(..., min_length=1, description="Cited evidence from actuals")


class AttributionPayload(BaseModel):
    """List of dimensional conclusions for a single review."""

    conclusions: list[DimensionalConclusion] = Field(
        ...,
        min_length=3,
        max_length=5,
        description="3..5 dimensional conclusions",
    )


class LearningsPayload(BaseModel):
    """Aggregated learnings over the user's last-30-day window.

    Regenerated lazily by ``EffectReviewService.derive_learnings`` and
    cached on the ``effect_reviews.learnings`` column (US4, T065).
    """

    top_strengths: list[str] = Field(
        default_factory=list,
        description="Recurring strengths across recent reviews",
    )
    top_weaknesses: list[str] = Field(
        default_factory=list,
        description="Recurring weaknesses across recent reviews",
    )
    sample_size: int = Field(
        ...,
        ge=0,
        description="Number of attributed reviews aggregated",
    )
    window_days: int = Field(
        default=30,
        ge=1,
        description="Rolling window size in days",
    )


# --- Existing schemas (unchanged) ---------------------------------------


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
