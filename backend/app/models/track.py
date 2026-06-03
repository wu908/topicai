"""Track diagnosis Pydantic schemas for TopicAI v4.0.

Defines SubTrack and TrackDiagnosis schemas for
赛道诊断 (track diagnosis) results.
"""

from pydantic import BaseModel, Field


class SubTrack(BaseModel):
    """A sub-track within a content track.

    Attributes:
        name: Sub-track name.
        potential_score: Potential/opportunity score (0-1).
        reason: Why this sub-track is recommended.
    """

    name: str = Field(..., min_length=1, description="Sub-track name")
    potential_score: float = Field(
        ..., ge=0.0, le=1.0, description="Potential score (0-1)"
    )
    reason: str = Field(..., description="Recommendation reason")


class TrackDiagnosis(BaseModel):
    """Complete track diagnosis result.

    Attributes:
        id: Diagnosis ID (UUID).
        user_id: User who requested diagnosis.
        track_keyword: The track keyword being diagnosed.
        health_score: Overall track health (0-1).
        competitiveness_score: Competition level (0-1, higher = more competitive).
        direction_advice: Directional advice for content strategy.
        sub_tracks: 3 recommended sub-tracks.
        confidence: AI confidence (0-1).
        data_source: Data source used.
        created_at: Creation timestamp.
    """

    id: str = Field(..., description="Diagnosis ID (UUID)")
    user_id: str = Field(..., description="User ID")
    track_keyword: str = Field(..., description="Track keyword")
    health_score: float = Field(
        ..., ge=0.0, le=1.0, description="Track health score (0-1)"
    )
    competitiveness_score: float = Field(
        ..., ge=0.0, le=1.0, description="Competitiveness score (0-1)"
    )
    direction_advice: str = Field(
        ..., description="Directional advice"
    )
    sub_tracks: list[SubTrack] = Field(
        ..., min_length=1, description="Recommended sub-tracks"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="AI confidence (0-1)"
    )
    data_source: str = Field(..., description="Data source used")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")


class TrackDiagnoseRequest(BaseModel):
    """Schema for track diagnosis request.

    Attributes:
        track_keyword: The track keyword to diagnose.
    """

    track_keyword: str = Field(
        ..., min_length=1, max_length=100, description="Track keyword"
    )
