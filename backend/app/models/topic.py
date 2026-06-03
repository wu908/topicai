"""Topic recommendation Pydantic schemas for TopicAI v4.0.

Defines TopicItem (individual recommendation) and TopicRecommendation
(batch recommendation result).
"""


from pydantic import BaseModel, Field


class TopicItem(BaseModel):
    """Individual topic recommendation.

    Each topic has multi-dimensional scores used for ranking.
    The composite_score is the weighted aggregate used for sorting.

    Attributes:
        title: Topic title/suggestion.
        reason: Why this topic is recommended.
        estimated_heat: Estimated current heat/popularity (0-1).
        content_angle: Suggested content angle/approach.
        track_match_score: How well it matches the user's track (0-1).
        format_match_score: How well it matches the user's format (0-1).
        data_quality_score: Quality/reliability of the underlying data (0-1).
        composite_score: Weighted aggregate score (0-1).
        confidence: AI confidence in this recommendation (0-1).
        data_source: Source of the recommendation data.
        caveat: Optional caveat about the recommendation.
    """

    title: str = Field(..., min_length=1, description="Topic title")
    reason: str = Field(..., description="Recommendation reason")
    estimated_heat: float = Field(
        ..., ge=0.0, le=1.0, description="Estimated heat (0-1)"
    )
    content_angle: str = Field(..., description="Suggested content angle")
    track_match_score: float = Field(
        ..., ge=0.0, le=1.0, description="Track match score (0-1)"
    )
    format_match_score: float = Field(
        ..., ge=0.0, le=1.0, description="Format match score (0-1)"
    )
    data_quality_score: float = Field(
        ..., ge=0.0, le=1.0, description="Data quality score (0-1)"
    )
    composite_score: float = Field(
        ..., ge=0.0, le=1.0, description="Composite score (0-1)"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="AI confidence (0-1)"
    )
    data_source: str = Field(..., description="Data source identifier")
    caveat: str | None = Field(
        default=None, description="Optional caveat"
    )


class TopicRecommendation(BaseModel):
    """Batch topic recommendation result.

    Attributes:
        id: Recommendation ID (UUID).
        user_id: User who received the recommendation.
        topics: List of recommended topics (5-10 items).
        recommendation_mode: 'hotspot_fusion' or 'evergreen_deep'.
        data_source_used: Which data source tier was used.
        created_at: Recommendation timestamp.
    """

    id: str = Field(..., description="Recommendation ID (UUID)")
    user_id: str = Field(..., description="User ID")
    topics: list[TopicItem] = Field(
        ..., min_length=1, max_length=10, description="Recommended topics"
    )
    recommendation_mode: str = Field(
        ..., description="Recommendation mode"
    )
    data_source_used: str = Field(
        ..., description="Data source tier used"
    )
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")


class TopicRecommendRequest(BaseModel):
    """Schema for topic recommendation request.

    Attributes:
        mode: Recommendation mode ('hotspot_fusion' or 'evergreen_deep').
        track: Optional track override (defaults to user profile track).
    """

    mode: str = Field(
        default="hotspot_fusion",
        pattern=r"^(hotspot_fusion|evergreen_deep)$",
        description="Recommendation mode",
    )
    track: str | None = Field(
        default=None, description="Track override"
    )
