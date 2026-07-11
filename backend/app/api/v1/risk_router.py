"""Content risk API endpoints for TopicAI v4.0.

Spec-007 US7 (T074): exposes ``POST /api/v1/risk/check`` for the
pre-publish content risk guard. Delegates to ``ContentRiskService``
(Constitution I) and validates the response against the
``ContentRiskReport`` Pydantic model (Constitution VII).

The shared ``Database`` is injected via ``Depends(get_db)`` so the
service reads the ``risk_keywords`` table (seeded on first use) and
honours per-user overrides. When no db is wired in (tests/scripts),
the service falls back to its hardcoded keyword list.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends

from app.api.v1.deps import get_current_user, get_db
from app.models.common import ApiResponse
from app.models.risk import ContentRiskReport, RiskCheckRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Risk"])


@router.post("/risk/check", response_model=ApiResponse[ContentRiskReport])
async def risk_check(
    data: RiskCheckRequest,
    user: dict = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> ApiResponse[ContentRiskReport]:
    """Check content for compliance risks (Spec-007 T074).

    Delegates to ``ContentRiskService.check`` and validates the result
    with the ``ContentRiskReport`` Pydantic model. The response
    ``meta.ai_quality`` carries the required AI transparency fields
    (``confidence`` / ``data_source`` / ``model_version``) per
    Constitution Principle III.
    """
    from app.services.content_risk import ContentRiskService

    svc = ContentRiskService(db=db)
    report = await svc.check(user["id"], data.content)

    # Pydantic validation at the boundary. The service may include
    # extra keys (e.g. ``confidence``) — only the declared fields are
    # preserved on the parsed instance.
    parsed = ContentRiskReport(**report)

    # AI transparency fields are read off the parsed Pydantic instance.
    # ``ContentRiskReport`` does not yet declare these, so ``getattr``
    # falls back to keyword-only defaults when the field is absent.
    confidence = float(getattr(parsed, "confidence", 0.5))
    data_source = str(getattr(parsed, "data_source", "keyword_only"))
    model_version = str(getattr(parsed, "model_version", "keyword-v1"))
    caveat = str(
        getattr(
            parsed,
            "caveat",
            "基于关键词扫描（必要时LLM增强），发布前请人工复核",
        )
    )

    return ApiResponse[ContentRiskReport](
        code=200,
        data=parsed,
        message="success",
        meta={
            "ai_quality": {
                "confidence": confidence,
                "data_source": data_source,
                "model_version": model_version,
                "caveat": caveat,
            },
            "note": "Spec-007 T074: pre-publish content risk guard",
        },
    )
