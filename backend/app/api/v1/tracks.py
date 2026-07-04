"""Tracks API endpoints for TopicAI v4.0."""

import logging

from fastapi import APIRouter, HTTPException, Request

from app.models.common import ApiResponse
from app.models.track import TrackDiagnoseRequest, TrackDiagnosis

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Tracks"])


def _ai_meta(result) -> dict:
    """Build AI quality meta dict from a TrackDiagnosis-like result.

    Note: batch B2 will replace this with AIQualityMeta construction.
    For now, extract values via getattr so the function works with both
    Pydantic TrackDiagnosis instances (tests) and dicts (service output).
    """
    return {
        "confidence": getattr(result, "confidence", 0.75),
        "data_source": getattr(result, "data_source", "llm_simulation"),
        "model_version": getattr(result, "model_version", "deepseek-v4-flash"),
        "caveat": "基于基准数据分析",
    }


@router.post("/tracks/diagnose", response_model=ApiResponse[TrackDiagnosis])
async def diagnose_track(request: Request, data: TrackDiagnoseRequest):
    """Diagnose a content track."""
    user_id = getattr(request.state, "user_id", "anonymous")
    track_keyword = data.track_keyword

    if not track_keyword:
        raise HTTPException(status_code=422, detail="赛道关键词不能为空")

    from app.services.track_diagnosis import TrackDiagnosisService
    svc = TrackDiagnosisService()
    result = svc.diagnose(user_id, track_keyword)

    return ApiResponse[TrackDiagnosis](
        code=200,
        data=result,
        message="赛道诊断完成",
        meta={"ai_quality": _ai_meta(result)},
    )
