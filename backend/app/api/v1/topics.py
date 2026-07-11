"""Topics API endpoints for TopicAI v4.0.

Provides topic recommendation, refresh, and explanation endpoints.
"""

import logging

from fastapi import APIRouter, Query, Request

from app.models.common import ApiResponse
from app.models.topic import TopicHistoryResponse, TopicRecommendRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Topics"])


def _ai_quality_meta(confidence: float = 0.7, data_source: str = "template_fallback") -> dict:
    return {
        "confidence": confidence,
        "data_source": data_source,
        "model_version": "deepseek-v4-flash",
        "caveat": "基于AI推断，建议结合实际情况判断",
    }


@router.get("/topics/recommend")
async def recommend_topics(request: Request):
    """Generate topic recommendations."""
    user_id = getattr(request.state, "user_id", "anonymous")
    track = request.query_params.get("track", "科技")
    mode = request.query_params.get("mode", "hotspot_fusion")

    from app.services.topic_recommend import TopicRecommendService
    svc = TopicRecommendService()
    result = await svc.recommend_async(user_id, track, mode, count=5)

    return {
        "code": 200,
        "data": {"topics": result["topics"]},
        "message": "success",
        "meta": {"ai_quality": _ai_quality_meta(confidence=result["meta"].get("confidence", 0.7))},
    }


@router.post("/topics/refresh")
async def refresh_recommendations(request: Request, data: TopicRecommendRequest):
    """Refresh topic recommendations (get a new batch)."""
    user_id = getattr(request.state, "user_id", "anonymous")
    track = data.track or "科技"
    mode = data.mode

    from app.services.topic_recommend import TopicRecommendService
    svc = TopicRecommendService()
    result = await svc.recommend_async(user_id, track, mode, count=5)

    return {
        "code": 200,
        "data": {"topics": result["topics"]},
        "message": "已刷新选题推荐",
        "meta": {"ai_quality": _ai_quality_meta()},
    }


@router.get("/topics/{topic_id}/explain")
async def explain_recommendation(request: Request, topic_id: str):
    """Explain why a topic was recommended."""
    return {
        "code": 200,
        "data": {
            "topic_id": topic_id,
            "explanation": "该选题与您的赛道'科技'高度匹配，当前热搜趋势上升，推荐指数：高",
            "factors": [
                {"factor": "赛道匹配", "weight": 0.30, "score": 0.90},
                {"factor": "热点趋势", "weight": 0.25, "score": 0.85},
                {"factor": "内容适配", "weight": 0.20, "score": 0.80},
            ],
        },
        "message": "success",
        "meta": {"ai_quality": _ai_quality_meta()},
    }


@router.get(
    "/topics/history",
    response_model=ApiResponse[TopicHistoryResponse],
)
async def topics_history(request: Request, limit: int = Query(20, ge=1, le=100)):
    """Return recently recommended topics (Spec-007 US2 T046).

    Foundation batch C1: route now delegates to ``TopicHistoryService``
    instead of importing ``DataManager`` directly (Constitution I —
    service-layer architecture). The service wraps the recent-cache read
    and returns provenance metadata so downstream AI-transparency audits
    can trace this read path (Constitution III).
    """
    from app.services.topic_history import TopicHistoryService

    svc = TopicHistoryService()
    payload = svc.get_recent(limit=limit)

    return ApiResponse[TopicHistoryResponse](
        code=200,
        data=TopicHistoryResponse(
            topics=payload["topics"],
            count=payload["count"],
        ),
        message="success",
        meta=payload["meta"],
    )
