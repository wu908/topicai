"""Viral analysis API endpoints for TopicAI v4.0."""

import logging

from fastapi import APIRouter, HTTPException, Request

from app.models.viral import ViralAnalyzeRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Viral"])


def _ai_meta(confidence: float = 0.75) -> dict:
    return {"confidence": confidence, "data_source": "deepseek-v4-flash", "model_version": "deepseek-v4-flash", "caveat": "基于AI分析，供参考"}


@router.post("/viral/analyze")
async def analyze_viral_content(request: Request, data: ViralAnalyzeRequest):
    """Analyze viral/爆款 content (text or image)."""
    user_id = getattr(request.state, "user_id", "anonymous")
    content = data.content
    input_type = data.input_type

    from app.services.viral_analysis import ViralAnalysisService
    svc = ViralAnalysisService()

    try:
        result = svc.analyze(user_id, content, input_type)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return {"code": 200, "data": result, "message": "爆款拆解完成", "meta": {"ai_quality": _ai_meta(result.get("confidence", 0.75))}}


@router.get("/viral/result/{analysis_id}")
async def get_viral_result(request: Request, analysis_id: str):
    """Get a previous viral analysis result."""
    return {"code": 200, "data": {"id": analysis_id, "status": "completed"}, "message": "success", "meta": {"ai_quality": _ai_meta()}}
