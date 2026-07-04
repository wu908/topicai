"""Feedback API endpoints for TopicAI v4.0.

Spec-007:
- US7 (T057): adds ``GET /api/v1/feedback/history`` for the personalization
  loop audit endpoint.
- US3 (T053, T056): POST /api/v1/feedback now persists to ``user_feedback``
  and triggers the cold-start + bounded-shift adaptation pipeline.
  Returns 202 (Accepted) per the async persistence contract. The legacy
  GET /api/v1/feedback/analysis endpoint no longer calls
  ``analyze_feedback(user_id, [])`` (T056) and is now a deprecation shim
  pointing clients at /feedback/history.

A8 (foundation): all three endpoints declare ``response_model=ApiResponse[T]``
so FastAPI emits typed OpenAPI schemas and Pydantic validates the boundary
on every response (Constitution VII). The inline ``_DeprecationNotice``
and ``FeedbackHistoryResponse`` schemas are endpoint-scoped payloads that
are NOT part of the cross-service contract — they live in this file to
keep the audit-trail shim and the history view local.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from app.api.v1.deps import get_current_user, get_db
from app.models.common import ApiResponse
from app.models.feedback import FeedbackRecord, FeedbackSubmitRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Feedback"])


class _DeprecationNotice(BaseModel):
    """Payload for the legacy ``GET /feedback/analysis`` deprecation shim.

    Spec-007 T056 removed the ``analyze_feedback(user_id, [])`` call and
    turned the endpoint into a typed pointer at the history endpoint.
    """

    deprecated: bool
    replacement: str
    message: str


class FeedbackHistoryResponse(BaseModel):
    """Payload for ``GET /feedback/history``.

    Attributes:
        items: Pydantic-validated ``FeedbackRecord`` rows, newest first.
        total: Number of rows in ``items`` (post-filter, pre-pagination).
        limit: ``limit`` query param echoed back to the caller.
        source_type: ``source_type`` filter echoed back (None if absent).
        since: ``since`` lower-bound echoed back (None if absent).
    """

    items: list[FeedbackRecord]
    total: int
    limit: int
    source_type: str | None
    since: str | None


@router.post(
    "/feedback",
    response_model=ApiResponse[FeedbackRecord],
    status_code=202,
)
async def submit_feedback(
    request: Request,
    data: FeedbackSubmitRequest,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    user_id = user["id"]

    from app.services.feedback import FeedbackService
    svc = FeedbackService()
    record = await svc.submit(
        db,
        user_id,
        data.target_type,
        data.target_id,
        data.feedback_type,
        reason=data.reason or "",
    )

    return ApiResponse[FeedbackRecord](
        code=202,
        data=FeedbackRecord(**record),
        message="反馈已提交",
        meta={},
    )


@router.get(
    "/feedback/analysis",
    response_model=ApiResponse[_DeprecationNotice],
)
async def get_feedback_analysis(request: Request, user: dict = Depends(get_current_user)):
    user_id = user.get("id") or getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录")

    # Spec-007 T056: the legacy analyze_feedback(user_id, []) call is
    # removed. The endpoint is now a deprecation shim pointing at the
    # /api/v1/feedback/history audit endpoint, which reads the persisted
    # user_feedback rows directly.
    return ApiResponse[_DeprecationNotice](
        code=200,
        data=_DeprecationNotice(
            deprecated=True,
            replacement="/api/v1/feedback/history",
            message="分析接口已废弃；请通过 /feedback/history 查看历史记录",
        ),
        message="success",
        meta={},
    )


@router.get(
    "/feedback/history",
    response_model=ApiResponse[FeedbackHistoryResponse],
)
async def feedback_history(
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    source_type: str | None = Query(
        None,
        pattern=r"^(topic|title|idea|viral|track|publish|effect_review)$",
        description="Optional SourceType filter",
    ),
    since: str | None = Query(
        None, description="Optional ISO-8601 lower bound on created_at"
    ),
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Return persisted feedback records for the current user (Spec-007 T057).

    Read-only view of ``user_feedback`` for personalization audits and
    the on-device feedback history. The Pydantic ``FeedbackRecord``
    model validates each row at the router boundary.
    """
    from app.services.feedback import FeedbackService

    svc = FeedbackService()
    rows = await svc.list_by_user(
        db,
        user_id=user["id"],
        limit=limit,
        source_type=source_type,
        since=since,
    )

    # Pydantic-validate every row so the contract is enforced at the
    # boundary (Constitution VII).
    items = [FeedbackRecord(**r) for r in rows]

    return ApiResponse[FeedbackHistoryResponse](
        code=200,
        data=FeedbackHistoryResponse(
            items=items,
            total=len(items),
            limit=limit,
            source_type=source_type,
            since=since,
        ),
        message="success",
        meta={
            "data_source": "user_feedback_table",
            "model_version": "history-v1",
            "note": "Spec-007 T057: persisted feedback history endpoint",
        },
    )
