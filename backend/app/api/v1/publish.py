"""Publish advisor API endpoints for TopicAI v4.0."""

import logging

from fastapi import APIRouter, Request

from app.models.common import ApiResponse, _build_ai_quality
from app.models.publish import PublishSuggestion, PublishSuggestRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Publish"])


@router.post("/publish/suggest", response_model=ApiResponse[PublishSuggestion])
async def suggest_publish_time(
    request: Request, data: PublishSuggestRequest
) -> ApiResponse[PublishSuggestion]:
    """Suggest optimal publish times."""
    user_id = getattr(request.state, "user_id", "anonymous")
    platform = data.platform
    content_type = data.content_type

    from app.services.publish_advisor import PublishAdvisorService
    svc = PublishAdvisorService()
    result = svc.suggest(user_id, platform, content_type)

    # Build PublishSuggestion from service result (dict or model)
    if isinstance(result, PublishSuggestion):
        suggestion = result
    elif isinstance(result, dict):
        fields = {k: v for k, v in result.items() if k in PublishSuggestion.model_fields}
        suggestion = PublishSuggestion(**fields)
    else:
        suggestion = PublishSuggestion.model_validate(result)

    return ApiResponse[PublishSuggestion](
        code=200,
        data=suggestion,
        message="发布时间建议生成完成",
        meta={"ai_quality": _build_ai_quality(result)},
    )
