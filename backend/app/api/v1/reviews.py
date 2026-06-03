"""Reviews API endpoints for TopicAI v4.0.

Provides effect blind prediction and attribution analysis endpoints.
Requires JWT authentication.
"""

import logging

from fastapi import APIRouter, HTTPException, Request

from app.models.effect_review import EffectAttributeRequest, EffectPredictRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Reviews"])


def _ai_meta(confidence: float = 0.7) -> dict:
    """Generate AI quality metadata for review responses.

    Args:
        confidence: AI confidence score (0-1).

    Returns:
        Dict with AI quality metadata.
    """
    return {
        "confidence": confidence,
        "data_source": "deepseek-v4-flash",
        "model_version": "deepseek-v4-flash",
        "caveat": "基于AI分析，供参考",
    }


@router.post("/reviews/predict")
async def predict_effect(request: Request, data: EffectPredictRequest):
    """Create a blind prediction for content performance before publishing.

    Accepts content metadata (title, outline, platform, etc.) and returns
    an estimated performance prediction with confidence score.

    Args:
        request: FastAPI request object.
        data: Prediction request with topic_title and optional content_outline.

    Returns:
        Prediction result with estimated metrics and confidence.
    """
    from app.services.effect_review import EffectReviewService

    user_id = getattr(request.state, "user_id", "anonymous")

    content_data = {
        "topic_title": data.topic_title,
        "content_outline": data.content_outline,
    }

    svc = EffectReviewService()

    try:
        result = svc.create_prediction(user_id, content_data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return {
        "code": 200,
        "data": result,
        "message": "效果预测完成",
        "meta": {"ai_quality": _ai_meta(confidence=result.get("confidence", 0.7))},
    }


@router.post("/reviews/attribute")
async def attribute_effect(request: Request, data: EffectAttributeRequest):
    """Analyze the attribution of content performance after publishing.

    Compares actual performance data against the original prediction
    and provides attribution conclusions about what worked or didn't.

    Args:
        request: FastAPI request object.
        data: Attribution request with review_id and actual_data.

    Returns:
        Attribution analysis with conclusions and learnings.
    """
    from app.services.effect_review import EffectReviewService

    user_id = getattr(request.state, "user_id", "anonymous")

    svc = EffectReviewService()

    try:
        result = svc.create_attribution(
            user_id, data.review_id, data.actual_data
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return {
        "code": 200,
        "data": result,
        "message": "归因分析完成",
        "meta": {"ai_quality": _ai_meta(confidence=0.7)},
    }
