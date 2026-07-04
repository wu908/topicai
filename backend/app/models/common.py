"""Common/shared Pydantic models for TopicAI v4.0.

Includes AIQualityMeta (AI output quality metadata), ApiResponse wrapper,
and PaginatedResponse for list endpoints.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from app.core.utils import utc_now


class AIQualityMeta(BaseModel):
    """AI output quality metadata.

    Every AI-generated output MUST include this metadata to enable
    transparency, quality tracking, and hallucination detection.

    Attributes:
        confidence: Confidence score (0.0 to 1.0).
        data_source: Data source identifier (e.g., 'tianapi', 'ai_inference').
        model_version: Specific model version used (e.g., 'deepseek-v4-flash').
        caveat: Optional caveat/warning about the data quality.
        generated_at: ISO 8601 UTC timestamp of generation.
    """

    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score (0-1)"
    )
    data_source: str = Field(
        ..., description="Data source identifier"
    )
    model_version: str = Field(
        ..., description="Model version used (no 'latest' aliases)"
    )
    caveat: str | None = Field(
        default=None,
        description="Optional caveat or warning about data quality",
    )
    generated_at: str = Field(
        default_factory=utc_now,
        description="ISO 8601 UTC generation timestamp",
    )

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper for list endpoints.

    Attributes:
        items: List of items for the current page.
        total: Total number of items across all pages.
        page: Current page number (1-indexed).
        page_size: Number of items per page.
    """

    items: list[T] = Field(default_factory=list, description="Page items")
    total: int = Field(..., ge=0, description="Total items across all pages")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")

class ApiResponse(BaseModel, Generic[T]):
    """Unified API response format.

    All TopicAI API responses use this format:
    {code, data, message, meta}

    Generic over the data payload type T. Use ``response_model=ApiResponse[Foo]``
    on endpoints so FastAPI emits a typed OpenAPI schema instead of an untyped
    Any blob. ``data: Any | None`` is kept as the runtime fallback for endpoints
    that have not yet been migrated to a concrete T.

    Attributes:
        code: HTTP status code.
        data: Response payload (can be None for errors).
        message: Human-readable message.
        meta: Additional metadata (AI quality, pagination, etc.).
    """

    code: int = Field(default=200, description="HTTP status code")
    data: T | Any | None = Field(default=None, description="Response payload")
    message: str = Field(default="success", description="Human-readable message")
    meta: dict = Field(default_factory=dict, description="Additional metadata")
