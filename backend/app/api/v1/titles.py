"""Titles API endpoints for TopicAI v4.0."""

import logging

from fastapi import APIRouter, HTTPException, Request

from app.models.common import ApiResponse, _build_ai_quality
from app.models.title import TitleOptimization, TitleOptimizeRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Titles"])


@router.post("/titles/optimize", response_model=ApiResponse[TitleOptimization])
async def optimize_title(request: Request, data: TitleOptimizeRequest):
    """Generate optimized title variations."""
    user_id = getattr(request.state, "user_id", "anonymous")
    title = data.title
    summary = data.summary or ""

    if not title:
        raise HTTPException(status_code=422, detail="标题不能为空")

    from app.services.title_optimizer import TitleOptimizerService
    svc = TitleOptimizerService()
    result = svc.optimize(user_id, title, summary)

    return ApiResponse[TitleOptimization](
        code=200,
        data=result,
        message="标题优化完成",
        meta={"ai_quality": _build_ai_quality(result)},
    )
