"""Viral analysis API endpoints for TopicAI v4.0."""

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.models.common import ApiResponse, _build_ai_quality
from app.models.viral import ViralAnalysis, ViralAnalyzeRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Viral"])


class _ViralResultStatus(BaseModel):
    """Lightweight status response for /viral/result/{analysis_id}."""

    id: str
    status: str


@router.post("/viral/analyze", response_model=ApiResponse[ViralAnalysis])
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

    return ApiResponse[ViralAnalysis](
        code=200,
        data=result,
        message="爆款拆解完成",
        meta={"ai_quality": _build_ai_quality(result)},
    )


@router.get("/viral/result/{analysis_id}", response_model=ApiResponse[_ViralResultStatus])
async def get_viral_result(request: Request, analysis_id: str):
    """Get a previous viral analysis result."""
    return ApiResponse[_ViralResultStatus](
        code=200,
        data=_ViralResultStatus(id=analysis_id, status="completed"),
        message="success",
        meta={"ai_quality": _build_ai_quality(None)},
    )
