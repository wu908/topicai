"""Reviews API endpoints for TopicAI v4.0.

Provides effect blind prediction and attribution analysis endpoints.
Requires JWT authentication.

Spec-007 US7 (T066): adds ``GET /api/v1/reviews/learnings`` and
``GET /api/v1/reviews/list`` to surface persisted effect_reviews data.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.v1.deps import get_current_user, get_db
from app.models.effect_review import (
    EffectAttributeRequest,
    EffectPredictRequest,
    EffectReview,
    LearningsPayload,
)

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


@router.get("/reviews/learnings")
async def reviews_learnings(
    window_days: int = Query(30, ge=1, le=365, description="Rolling window size"),
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Aggregate the user's recent learnings (Spec-007 T066).

    Scans the user's ``effect_reviews`` within ``window_days`` and
    surfaces the top recurring strengths and weaknesses. Returns a
    ``LearningsPayload`` shape, validated at the boundary.
    """
    from app.services.effect_review import EffectReviewService

    svc = EffectReviewService()
    payload = await svc.derive_learnings(
        db, user_id=user["id"], window_days=window_days
    )

    # Pydantic validation at the boundary (Constitution VII).
    parsed = LearningsPayload(**payload)

    return {
        "code": 200,
        "data": parsed.model_dump(),
        "message": "success",
        "meta": {
            "data_source": "effect_reviews_table",
            "model_version": "learnings-v1",
            "note": "Spec-007 T066: aggregated learnings over rolling window",
        },
    }


@router.get("/reviews/list")
async def reviews_list(
    status: str | None = Query(
        None,
        pattern=r"^(awaiting_actuals|predicted|attributed)$",
        description="Optional status filter",
    ),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """List effect reviews for the current user (Spec-007 T066).

    Returns persisted reviews from the ``effect_reviews`` table,
    newest first. The Pydantic ``EffectReview`` model validates each
    row at the boundary.
    """
    from app.services.effect_review import EffectReviewService

    svc = EffectReviewService()
    rows = await svc.list_by_user(
        db, user_id=user["id"], status=status, limit=limit
    )

    # Pydantic-validate every row.
    items = [EffectReview(**r) for r in rows]

    return {
        "code": 200,
        "data": {
            "items": [item.model_dump() for item in items],
            "total": len(items),
            "limit": limit,
            "status": status,
        },
        "message": "success",
        "meta": {
            "data_source": "effect_reviews_table",
            "model_version": "list-v1",
            "note": "Spec-007 T066: persisted review list endpoint",
        },
    }
