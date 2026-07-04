"""Publish advisor API endpoints for TopicAI v4.0."""

import logging

from fastapi import APIRouter, Request

from app.models.common import ApiResponse
from app.models.publish import PublishSuggestion, PublishSuggestRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Publish"])


def _ai_meta(result) -> dict:
    """Build AI quality meta from service result (dict or Pydantic model).

    Kept for batch B2 removal. Currently reads confidence / data_source /
    model_version from the service result, falling back to safe defaults.
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
        "caveat": "基于行业基准数据",
    }


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
        meta={"ai_quality": _ai_meta(result)},
    )
