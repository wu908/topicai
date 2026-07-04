"""Ideas API endpoints for TopicAI v4.0.

Spec-007 A1: ``POST /ideas/boost`` declares
``response_model=ApiResponse[IdeaBoosterResult]`` so FastAPI emits a
typed OpenAPI schema instead of an untyped ``Any`` blob (Constitution
VII — schema-validated contracts).
"""

import logging

from fastapi import APIRouter, HTTPException, Request

from app.models.common import ApiResponse
from app.models.idea import IdeaBoosterResult, IdeaBoostRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Ideas"])


def _ai_meta(result) -> dict:
    """Build the ``meta.ai_quality`` payload from the booster result.

    Provisional: the service currently returns a plain ``dict`` without
    ``data_source`` / ``model_version`` fields, so ``getattr`` falls
    back to ``"llm_simulation"``. Batch B2 (provenance) will replace
    this helper with direct reads from a typed result.
    """
    return {
        "confidence": getattr(result, "confidence", 0.75) if not isinstance(result, dict) else result.get("confidence", 0.75),
        "data_source": (result.get("data_source", "llm_simulation") if isinstance(result, dict) else getattr(result, "data_source", "llm_simulation")),
        "model_version": (result.get("model_version", "llm_simulation") if isinstance(result, dict) else getattr(result, "model_version", "llm_simulation")),
        "caveat": "基于AI推断",
    }


@router.post("/ideas/boost", response_model=ApiResponse[IdeaBoosterResult])
async def boost_idea(request: Request, data: IdeaBoostRequest):
    """Boost a fuzzy idea into a structured content plan."""
    user_id = getattr(request.state, "user_id", "anonymous")
    idea_text = data.idea_text

    from app.services.idea_booster import IdeaBoosterService

    svc = IdeaBoosterService()
    try:
        result = svc.boost(user_id, idea_text)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return ApiResponse(
        code=200,
        data=result,
        message="想法推进完成",
        meta={"ai_quality": _ai_meta(result)},
    )
