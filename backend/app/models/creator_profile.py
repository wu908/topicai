"""CreatorProfile Pydantic schema for TopicAI v4.0.

Represents a user's creator profile including track, content formats,
production preferences, and recommendation mode.
"""

from pydantic import BaseModel, Field


class CreatorProfile(BaseModel):
    """Creator profile schema.

    Stores user's content creation preferences, track selection,
    and recommendation mode. Used by the recommendation engine
    to personalize AI outputs.

    Attributes:
        id: Unique profile ID (UUID).
        user_id: Associated user ID (FK to users table).
        track: Primary content track/category (e.g., '科技', '美妆').
        content_formats: List of content formats (e.g., ['短视频', '图文']).
        production_complexity: Production complexity level.
        content_depth: Content depth preference.
        hotspot_preference: Hotspot chasing preference.
        recommendation_mode: 'hotspot_fusion' or 'evergreen_deep'.
        rubric_weights: Multi-dimensional rubric weights for scoring.
        created_at: Profile creation timestamp.
        updated_at: Last update timestamp.
    """

    id: str = Field(..., description="Profile ID (UUID)")
    user_id: str = Field(..., description="Associated user ID")
    track: str = Field(..., min_length=1, description="Primary content track")
    content_formats: list[str] = Field(
        ..., min_length=1, description="Content formats"
    )
    production_complexity: str = Field(
        ..., description="Production complexity level"
    )
    content_depth: str = Field(
        ..., description="Content depth preference"
    )
    hotspot_preference: str = Field(
        ..., description="Hotspot chasing preference"
    )
    recommendation_mode: str = Field(
        ...,
        pattern=r"^(hotspot_fusion|evergreen_deep)$",
        description="Recommendation mode",
    )
    rubric_weights: dict[str, float] = Field(
        default_factory=dict,
        description="Multi-dimensional rubric weights",
    )
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Last update timestamp (ISO 8601)")


class OnboardingRequest(BaseModel):
    """Schema for onboarding submission.

    Attributes:
        track: Selected content track.
        content_formats: Preferred content formats.
        production_complexity: Production complexity level.
        content_depth: Content depth preference.
        hotspot_preference: Hotspot preference.
    """

    track: str = Field(..., min_length=1, description="Content track")
    content_formats: list[str] = Field(
        ..., min_length=1, description="Content formats"
    )
    production_complexity: str = Field(
        ..., description="Production complexity"
    )
    content_depth: str = Field(
        ..., description="Content depth preference"
    )
    hotspot_preference: str = Field(
        ..., description="Hotspot preference"
    )


class ProfileUpdateRequest(BaseModel):
    """Schema for updating a creator profile (all fields optional)."""

    track: str | None = Field(default=None, description="Content track")
    content_formats: list[str] | None = Field(default=None, description="Content formats")
    production_complexity: str | None = Field(default=None, description="Production complexity")
    content_depth: str | None = Field(default=None, description="Content depth")
    hotspot_preference: str | None = Field(default=None, description="Hotspot preference")
    recommendation_mode: str | None = Field(default=None, description="Recommendation mode")
