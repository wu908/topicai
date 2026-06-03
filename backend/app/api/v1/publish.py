"""Publish advisor API endpoints for TopicAI v4.0."""

import logging

from fastapi import APIRouter, Request

from app.models.publish import PublishSuggestRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Publish"])


def _ai_meta() -> dict:
    return {"confidence": 0.75, "data_source": "benchmark", "model_version": "deepseek-v4-flash", "caveat": "基于行业基准数据"}


@router.post("/publish/suggest")
async def suggest_publish_time(request: Request, data: PublishSuggestRequest):
    """Suggest optimal publish times."""
    user_id = getattr(request.state, "user_id", "anonymous")
    platform = data.platform
    content_type = data.content_type

    from app.services.publish_advisor import PublishAdvisorService
    svc = PublishAdvisorService()
    result = svc.suggest(user_id, platform, content_type)

    return {"code": 200, "data": result, "message": "发布时间建议生成完成", "meta": {"ai_quality": _ai_meta()}}
