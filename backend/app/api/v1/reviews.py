"""Reviews API endpoints for TopicAI v4.0.

Provides effect blind prediction and attribution analysis endpoints.
Requires JWT authentication.

Spec-007:
- US7 (T066): adds ``GET /api/v1/reviews/learnings`` and
  ``GET /api/v1/reviews/list`` to surface persisted effect_reviews data.
- US4 (T062, T063): rewrites ``POST /api/v1/reviews/predict`` and
  ``POST /api/v1/reviews/attribute`` to use the new async
  ``EffectReviewService`` (DB-persistent, chain-backed) and returns
  201 Created per the US3/T056 contract.
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


def _ai_meta(confidence: float = 0.7, data_source: str = "llm_simulation") -> dict:
    """Generate AI quality metadata for review responses.

    Args:
        confidence: AI confidence score (0-1).
        data_source: One of 'llm_simulation' | 'template_fallback'.

    Returns:
        Dict with AI quality metadata.
    """
    return {
        "confidence": confidence,
        "data_source": data_source,
        "model_version": "deepseek-v4-flash",
        "caveat": "基于AI分析，供参考",
    }


@router.post("/reviews/predict", status_code=201)
async def predict_effect(
    request: Request,
    data: EffectPredictRequest,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Create a blind prediction for content performance before publishing.

    Spec-007 US4 (T062): delegates to ``EffectReviewService.create_prediction``
    which calls ``EffectReviewChain.predict`` and INSERTs into
    ``effect_reviews`` (status='awaiting_actuals').

    Returns 201 Created per the spec-007 contract.
    """
    from app.services.effect_review import EffectReviewService

    user_id = user["id"]
    content_data = {
        "topic_title": data.topic_title,
        "content_outline": data.content_outline,
    }

    svc = EffectReviewService(db)
    try:
        result = await svc.create_prediction(user_id, content_data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return {
        "code": 201,
        "data": result,
        "message": "效果预测完成",
        "meta": {"ai_quality": _ai_meta(confidence=0.7, data_source="llm_simulation")},
    }


@router.post("/reviews/attribute", status_code=201)
async def attribute_effect(
    request: Request,
    data: EffectAttributeRequest,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Analyze the attribution of content performance after publishing.

    Spec-007 US4 (T063): delegates to ``EffectReviewService.attribute``
    which calls ``EffectReviewChain.attribute`` and UPDATEs the
    ``effect_reviews`` row with actual_result / attribution / learnings
    (status='attributed').

    Returns 201 Created.
    """
    from app.services.effect_review import EffectReviewService

    user_id = user["id"]
    svc = EffectReviewService(db)
    try:
        result = await svc.attribute(
            user_id=user_id,
            prediction_id=data.review_id,
            actual_data=data.actual_data,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return {
        "code": 201,
        "data": result,
        "message": "归因分析完成",
        "meta": {"ai_quality": _ai_meta(confidence=0.7, data_source="llm_simulation")},
    }


@router.get("/reviews/learnings")
async def reviews_learnings(
    window_days: int = Query(30, ge=1, le=365, description="Rolling window size"),
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Aggregate the user's recent learnings (Spec-007 T066 + US4 T060).

    Scans the user's ``effect_reviews`` within ``window_days`` and
    surfaces the top recurring strengths and weaknesses. Returns a
    ``LearningsPayload`` shape, validated at the boundary.
    """
    from app.services.effect_review import EffectReviewService

    svc = EffectReviewService(db)
    payload = await svc.derive_learnings(
        user_id=user["id"], window_days=window_days
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

    svc = EffectReviewService(db)
    rows = await svc.list_by_user(
        user_id=user["id"], status=status, limit=limit
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
