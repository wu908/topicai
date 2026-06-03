"""Title optimization Pydantic schemas for TopicAI v4.0.

Defines OptimizedTitle and TitleOptimization schemas for
标题优化 (title optimization) results.
"""


from pydantic import BaseModel, Field


class OptimizedTitle(BaseModel):
    """A single optimized title suggestion.

    Attributes:
        title: The optimized title text.
        ctr_estimate: Estimated click-through rate (0-1).
        technique_used: The title technique used (e.g., '数字+悬念').
        technique_reason: Why this technique is effective.
    """

    title: str = Field(..., min_length=1, description="Optimized title")
    ctr_estimate: float = Field(
        ..., ge=0.0, le=1.0, description="Estimated CTR (0-1)"
    )
    technique_used: str = Field(
        ..., description="Title technique used"
    )
    technique_reason: str = Field(
        ..., description="Why this technique works"
    )


class TitleOptimization(BaseModel):
    """Complete title optimization result.

    Attributes:
        id: Optimization ID (UUID).
        user_id: User who requested optimization.
        original_title: The original title to optimize.
        content_summary: Optional summary of the content.
        optimized_titles: 3-5 optimized title suggestions.
        created_at: Creation timestamp.
    """

    id: str = Field(..., description="Optimization ID (UUID)")
    user_id: str = Field(..., description="User ID")
    original_title: str = Field(..., description="Original title")
    content_summary: str | None = Field(
        default=None, description="Content summary"
    )
    optimized_titles: list[OptimizedTitle] = Field(
        ..., min_length=1, max_length=5, description="Optimized titles"
    )
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")


class TitleOptimizeRequest(BaseModel):
    """Schema for title optimization request.

    Attributes:
        title: The original title to optimize.
        content_summary: Optional summary of the content.
    """

    title: str = Field(..., min_length=1, description="Original title")
    summary: str | None = Field(
        default=None, description="Content summary"
    )
