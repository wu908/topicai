"""Content risk API endpoints for TopicAI v4.0.

Spec-007 US7 (T074): exposes ``POST /api/v1/risk/check`` for the
pre-publish content risk guard. Delegates to ``ContentRiskService``
(Constitution I) and validates the response against the
``ContentRiskReport`` Pydantic model (Constitution VII).
"""

import logging

from fastapi import APIRouter, Depends

from app.api.v1.deps import get_current_user
from app.models.risk import ContentRiskReport, RiskCheckRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Risk"])


@router.post("/risk/check")
async def risk_check(
    data: RiskCheckRequest,
    user: dict = Depends(get_current_user),
):
    """Check content for compliance risks (Spec-007 T074).

    Delegates to ``ContentRiskService.check`` and validates the result
    with the ``ContentRiskReport`` Pydantic model. The response
    ``meta.ai_quality`` carries the required AI transparency fields
    (``confidence`` / ``data_source`` / ``model_version``) per
    Constitution Principle III.
    """
    from app.services.content_risk import ContentRiskService

    svc = ContentRiskService()
    report = await svc.check(user["id"], data.content)

    # Pydantic validation at the boundary. The service may include
    # extra keys (e.g. ``confidence``) — only the declared fields are
    # preserved in the response payload.
    parsed = ContentRiskReport(**report)

    confidence = float(report.get("confidence", 0.5))
    data_source = str(report.get("data_source", "keyword_only"))
    model_version = str(report.get("model_version", "keyword-v1"))

    return {
        "code": 200,
        "data": parsed.model_dump(),
        "message": "success",
        "meta": {
            "ai_quality": {
                "confidence": confidence,
                "data_source": data_source,
                "model_version": model_version,
                "caveat": "基于关键词扫描（必要时LLM增强），发布前请人工复核",
            },
            "note": "Spec-007 T074: pre-publish content risk guard",
        },
    }
