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
from pydantic import BaseModel, Field

from app.api.v1.deps import get_current_user, get_db
from app.models.common import ApiResponse, _build_ai_quality
from app.models.effect_review import (
    EffectAttributeRequest,
    EffectPredictRequest,
    EffectReview,
    LearningsPayload,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Reviews"])


class ReviewListResponse(BaseModel):
    """List response envelope for GET /api/v1/reviews/list (Spec-007 T066).

    Wraps the paginated review rows so the endpoint can carry a
    ``response_model=ApiResponse[ReviewListResponse]`` and emit a typed
    OpenAPI schema instead of an untyped ``dict`` blob.
    """

    items: list[EffectReview] = Field(
        default_factory=list, description="Review rows, newest first"
    )
    total: int = Field(..., ge=0, description="Total items returned")
    limit: int = Field(..., ge=1, le=100, description="Requested page size")
    status: str | None = Field(
        default=None, description="Status filter echo (if any)"
    )


@router.post(
    "/reviews/predict",
    status_code=201,
    response_model=ApiResponse[EffectReview],
)
async def predict_effect(
    request: Request,
    data: EffectPredictRequest,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> ApiResponse[EffectReview]:
    """Create a blind prediction for content performance before publishing.

    Spec-007 US4 (T062): delegates to ``EffectReviewService.create_prediction``
    which calls ``EffectReviewChain.predict`` and INSERTs into
    ``effect_reviews`` (status='awaiting_actuals').

    Returns 201 Created per the spec-007 contract. The ``data`` payload
    is a Pydantic ``EffectReview`` instance (not a raw dict) so the
    ``response_model`` emits a typed OpenAPI schema.
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

    return ApiResponse[EffectReview](
        code=201,
        data=EffectReview(**result),
        message="效果预测完成",
        meta={"ai_quality": _build_ai_quality(result)},
    )


@router.post(
    "/reviews/attribute",
    status_code=201,
    response_model=ApiResponse[EffectReview],
)
async def attribute_effect(
    request: Request,
    data: EffectAttributeRequest,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> ApiResponse[EffectReview]:
    """Analyze the attribution of content performance after publishing.

    Spec-007 US4 (T063): delegates to ``EffectReviewService.attribute``
    which calls ``EffectReviewChain.attribute`` and UPDATEs the
    ``effect_reviews`` row with actual_result / attribution / learnings
    (status='attributed').

    Returns 201 Created. The service returns ``attribution`` as a
    dict (the ``AttributionPayload`` shape), but ``EffectReview.attribution``
    is typed as ``str | None`` — so we pass the service dict through
    directly. ``ApiResponse.data`` is ``T | Any | None`` so the ``Any``
    fallback accepts the dict while the ``response_model`` still
    advertises ``EffectReview`` in the OpenAPI schema.
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

    return ApiResponse[EffectReview](
        code=201,
        data=result,
        message="归因分析完成",
        meta={"ai_quality": _build_ai_quality(result)},
    )


@router.get(
    "/reviews/learnings",
    response_model=ApiResponse[LearningsPayload],
)
async def reviews_learnings(
    window_days: int = Query(30, ge=1, le=365, description="Rolling window size"),
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> ApiResponse[LearningsPayload]:
    """Aggregate the user's recent learnings (Spec-007 T066 + US4 T060).

    Scans the user's ``effect_reviews`` within ``window_days`` and
    surfaces the top recurring strengths and weaknesses. The
    ``LearningsPayload`` is constructed at the boundary so the
    ``response_model`` validates the contract.
    """
    from app.services.effect_review import EffectReviewService

    svc = EffectReviewService(db)
    payload = await svc.derive_learnings(
        user_id=user["id"], window_days=window_days
    )

    # Pydantic validation at the boundary (Constitution VII).
    parsed = LearningsPayload(**payload)

    return ApiResponse[LearningsPayload](
        code=200,
        data=parsed,
        message="success",
        meta={
            "data_source": "effect_reviews_table",
            "model_version": "learnings-v1",
            "note": "Spec-007 T066: aggregated learnings over rolling window",
        },
    )


@router.get(
    "/reviews/list",
    response_model=ApiResponse[ReviewListResponse],
)
async def reviews_list(
    status: str | None = Query(
        None,
        pattern=r"^(awaiting_actuals|predicted|attributed)$",
        description="Optional status filter",
    ),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> ApiResponse[ReviewListResponse]:
    """List effect reviews for the current user (Spec-007 T066).

    Returns persisted reviews from the ``effect_reviews`` table,
    newest first. Each row is validated against the Pydantic
    ``EffectReview`` model and wrapped in ``ReviewListResponse`` so
    the ``response_model`` emits a typed OpenAPI schema.
    """
    from app.services.effect_review import EffectReviewService

    svc = EffectReviewService(db)
    rows = await svc.list_by_user(
        user_id=user["id"], status=status, limit=limit
    )

    # Pydantic-validate every row.
    items = [EffectReview(**r) for r in rows]

    return ApiResponse[ReviewListResponse](
        code=200,
        data=ReviewListResponse(
            items=items,
            total=len(items),
            limit=limit,
            status=status,
        ),
        message="success",
        meta={
            "data_source": "effect_reviews_table",
            "model_version": "list-v1",
            "note": "Spec-007 T066: persisted review list endpoint",
        },
    )
