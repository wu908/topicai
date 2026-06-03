"""Ideas API endpoints for TopicAI v4.0."""

import logging

from fastapi import APIRouter, HTTPException, Request

from app.models.idea import IdeaBoostRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Ideas"])


def _ai_meta() -> dict:
    return {"confidence": 0.75, "data_source": "deepseek-v4-flash", "model_version": "deepseek-v4-flash", "caveat": "基于AI推断"}


@router.post("/ideas/boost")
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

    return {"code": 200, "data": result, "message": "想法推进完成", "meta": {"ai_quality": _ai_meta()}}
