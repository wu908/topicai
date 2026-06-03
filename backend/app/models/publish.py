"""Publish time suggestion Pydantic schemas for TopicAI v4.0.

Defines TimeSlot and PublishSuggestion schemas for
发布时间建议 (publish time suggestions).
"""

from pydantic import BaseModel, Field


class TimeSlot(BaseModel):
    """A suggested time slot for publishing.

    Attributes:
        time_range: Time range string (e.g., '18:00-20:00').
        reason: Why this time slot is recommended.
        benchmark_source: Data source for the benchmark (e.g., '行业基准').
    """

    time_range: str = Field(..., description="Time range (e.g., '18:00-20:00')")
    reason: str = Field(..., description="Recommendation reason")
    benchmark_source: str = Field(
        ..., description="Benchmark data source"
    )


class PublishSuggestion(BaseModel):
    """Publish time suggestion result.

    Attributes:
        id: Suggestion ID (UUID).
        user_id: User who requested the suggestion.
        platform: Target platform (e.g., '小红书', '抖音', 'B站').
        content_type: Content type (e.g., '图文', '短视频').
        suggested_times: 3 suggested time slots.
        created_at: Suggestion timestamp.
    """

    id: str = Field(..., description="Suggestion ID (UUID)")
    user_id: str = Field(..., description="User ID")
    platform: str = Field(..., description="Target platform")
    content_type: str = Field(..., description="Content type")
    suggested_times: list[TimeSlot] = Field(
        ..., min_length=1, description="Suggested time slots"
    )
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")


class PublishSuggestRequest(BaseModel):
    """Schema for publish time suggestion request.

    Attributes:
        platform: Target platform.
        content_type: Content type.
    """

    platform: str = Field(..., min_length=1, description="Target platform")
    content_type: str = Field(..., min_length=1, description="Content type")
