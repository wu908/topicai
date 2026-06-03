"""Content risk Pydantic schemas for TopicAI v4.0.

Defines RiskItem and ContentRiskReport schemas for
内容风险检测 (content risk detection).
"""

from pydantic import BaseModel, Field


class RiskItem(BaseModel):
    """A single risk item detected in content.

    Attributes:
        category: Risk category (e.g., '违规词', '敏感话题').
        description: Detailed description of the risk.
        severity: 'low', 'medium', or 'high'.
        suggestion: Recommended action to mitigate the risk.
    """

    category: str = Field(..., description="Risk category")
    description: str = Field(..., description="Risk description")
    severity: str = Field(
        ...,
        pattern=r"^(low|medium|high)$",
        description="Risk severity level",
    )
    suggestion: str = Field(..., description="Mitigation suggestion")


class ContentRiskReport(BaseModel):
    """Complete content risk detection report.

    Attributes:
        id: Report ID (UUID).
        user_id: User who submitted the content.
        content_text: The content text to analyze (90-day expiry).
        content_text_expires_at: Content text expiry timestamp.
        risks: List of detected risk items.
        overall_risk_score: Overall risk score (0-1, higher = riskier).
        created_at: Report timestamp.
    """

    id: str = Field(..., description="Report ID (UUID)")
    user_id: str = Field(..., description="User ID")
    content_text: str = Field(..., description="Content text to analyze")
    content_text_expires_at: str | None = Field(
        default=None, description="Content text expiry timestamp"
    )
    risks: list[RiskItem] = Field(
        default_factory=list, description="Detected risk items"
    )
    overall_risk_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall risk score (0-1)"
    )
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")


class RiskCheckRequest(BaseModel):
    """Schema for content risk check request.

    Attributes:
        content: The content text to check for risks.
    """

    content: str = Field(
        ..., min_length=1, max_length=10000, description="Content to check"
    )
