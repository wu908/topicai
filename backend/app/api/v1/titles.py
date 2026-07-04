"""Titles API endpoints for TopicAI v4.0."""

import logging

from fastapi import APIRouter, HTTPException, Request

from app.models.common import ApiResponse
from app.models.title import TitleOptimization, TitleOptimizeRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Titles"])


def _ai_meta(result) -> dict:
    """Build AI quality metadata from service result.

    Accepts either a dict (legacy service return) or a Pydantic model
    (bare TitleOptimization). Falls back to safe defaults when
    provenance fields are absent — full provenance correction is
    tracked in batch B2.
    """
    if isinstance(result, dict):
        confidence = result.get("confidence", 0.75)
        data_source = result.get("data_source", "llm_simulation")
        model_version = result.get("model_version", "llm_simulation")
    else:
        confidence = getattr(result, "confidence", 0.75)
        data_source = getattr(result, "data_source", "llm_simulation")
        model_version = getattr(result, "model_version", "llm_simulation")
    return {
        "confidence": confidence,
        "data_source": data_source,
        "model_version": model_version,
        "caveat": "基于AI生成",
    }


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
        meta={"ai_quality": _ai_meta(result)},
    )
