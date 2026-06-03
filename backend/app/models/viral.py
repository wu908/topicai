"""Viral analysis Pydantic schemas for TopicAI v4.0.

Defines AttributionConclusion and ViralAnalysis schemas for
爆款拆解 (viral content deconstruction) results.
"""


from pydantic import BaseModel, Field


class AttributionConclusion(BaseModel):
    """A single attribution conclusion from viral analysis.

    Attributes:
        dimension: Analysis dimension (e.g., '标题', '节奏', '情绪').
        conclusion: The conclusion drawn.
        relevance: Relevance score (0-1).
        evidence: Supporting evidence.
    """

    dimension: str = Field(..., description="Analysis dimension")
    conclusion: str = Field(..., description="Attribution conclusion")
    relevance: float = Field(
        ..., ge=0.0, le=1.0, description="Relevance score (0-1)"
    )
    evidence: str = Field(..., description="Supporting evidence")


class ViralAnalysis(BaseModel):
    """Complete viral content analysis result.

    Contains structural analysis, attributions, transferable templates,
    rewrite suggestions, and risk warnings.

    Attributes:
        id: Analysis ID (UUID).
        user_id: User who submitted the analysis.
        input_type: 'text' or 'image'.
        input_text: Original input text (90-day expiry).
        input_text_expires_at: Text expiry timestamp (optional).
        viral_score: Overall viral potential score (0-1).
        structural_analysis: Five-dimension structural breakdown.
        attributions: 3-5 attribution conclusions.
        transferable_template: Reusable content template.
        rewrite_suggestions: Suggestions for rewriting.
        risk_warnings: List of risk warnings.
        confidence: AI confidence score (0-1).
        data_source: Data source/model used.
        created_at: Analysis timestamp.
    """

    id: str = Field(..., description="Analysis ID (UUID)")
    user_id: str = Field(..., description="User ID")
    input_type: str = Field(
        default="text",
        pattern=r"^(text|image)$",
        description="Input type",
    )
    input_text: str = Field(..., description="Original input text")
    input_text_expires_at: str | None = Field(
        default=None, description="Text expiry timestamp"
    )
    viral_score: float = Field(
        ..., ge=0.0, le=1.0, description="Viral potential score (0-1)"
    )
    structural_analysis: dict = Field(
        ..., description="Five-dimension structural breakdown"
    )
    attributions: list[AttributionConclusion] = Field(
        ..., min_length=1, max_length=5, description="Attribution conclusions"
    )
    transferable_template: str = Field(
        ..., description="Reusable content template"
    )
    rewrite_suggestions: str = Field(
        ..., description="Rewrite suggestions"
    )
    risk_warnings: list[str] = Field(
        default_factory=list, description="Risk warnings"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="AI confidence (0-1)"
    )
    data_source: str = Field(..., description="Data source/model used")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")


class ViralAnalyzeRequest(BaseModel):
    """Schema for viral analysis request.

    Attributes:
        input_type: 'text' or 'image'.
        content: Text content or image URL/base64.
    """

    input_type: str = Field(
        default="text",
        pattern=r"^(text|image)$",
        description="Input type: text or image",
    )
    content: str = Field(..., min_length=1, description="Content to analyze")
