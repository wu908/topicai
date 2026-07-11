"""Ideas API endpoints for TopicAI v4.0.

Spec-007 A1: ``POST /ideas/boost`` declares
``response_model=ApiResponse[IdeaBoosterResult]`` so FastAPI emits a
typed OpenAPI schema instead of an untyped ``Any`` blob (Constitution
VII — schema-validated contracts).
"""

import logging

from fastapi import APIRouter, HTTPException, Request

from app.models.common import ApiResponse, _build_ai_quality
from app.models.idea import IdeaBoosterResult, IdeaBoostRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Ideas"])


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
        meta={"ai_quality": _build_ai_quality(result)},
    )
