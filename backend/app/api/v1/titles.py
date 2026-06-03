"""Titles API endpoints for TopicAI v4.0."""

import logging

from fastapi import APIRouter, HTTPException, Request

from app.models.title import TitleOptimizeRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Titles"])


def _ai_meta() -> dict:
    return {"confidence": 0.75, "data_source": "deepseek-v4-flash", "model_version": "deepseek-v4-flash", "caveat": "基于AI生成"}


@router.post("/titles/optimize")
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

    return {"code": 200, "data": result, "message": "标题优化完成", "meta": {"ai_quality": _ai_meta()}}
