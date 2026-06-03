"""Idea booster Pydantic schemas for TopicAI v4.0.

Defines IdeaBoosterResult schema for 想法推进 (idea crystallization) results.
"""


from pydantic import BaseModel, Field


class IdeaBoosterResult(BaseModel):
    """Result of idea boosting/crystallization.

    Takes a fuzzy idea and produces structured analysis:
    key assumptions, feasibility assessment, title candidates,
    content outline, and publish schedule.

    Attributes:
        id: Result ID (UUID).
        user_id: User who submitted the idea.
        input_idea: Original idea text (90-day expiry).
        input_idea_expires_at: Idea text expiry timestamp.
        key_assumptions: Extracted key assumptions (3-5).
        feasibility_assessment: Feasibility analysis.
        title_candidates: Candidate titles (3-5).
        content_outline: Structured content outline.
        publish_schedule: Suggested publish schedule.
        confidence: AI confidence (0-1).
        created_at: Creation timestamp.
    """

    id: str = Field(..., description="Result ID (UUID)")
    user_id: str = Field(..., description="User ID")
    input_idea: str = Field(..., description="Original idea text")
    input_idea_expires_at: str | None = Field(
        default=None, description="Idea text expiry timestamp"
    )
    key_assumptions: list[str] = Field(
        ..., min_length=1, description="Key assumptions (3-5)"
    )
    feasibility_assessment: str = Field(
        ..., description="Feasibility analysis"
    )
    title_candidates: list[str] = Field(
        ..., min_length=1, description="Candidate titles"
    )
    content_outline: str = Field(
        ..., description="Content outline"
    )
    publish_schedule: str = Field(
        ..., description="Suggested publish schedule"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="AI confidence (0-1)"
    )
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")


class IdeaBoostRequest(BaseModel):
    """Schema for idea boost request.

    Attributes:
        idea: The fuzzy idea text to crystallize.
    """

    idea_text: str = Field(..., min_length=1, max_length=5000, description="Idea text")
