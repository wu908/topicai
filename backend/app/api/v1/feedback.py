"""Feedback API endpoints for TopicAI v4.0.

Spec-007 US7 (T057): adds ``GET /api/v1/feedback/history`` for the
personalization loop audit endpoint. Reads persisted records from
``user_feedback`` ordered by ``created_at DESC`` with optional
``source_type`` and ``since`` filters.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.v1.deps import get_current_user, get_db
from app.models.feedback import FeedbackRecord, FeedbackSubmitRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Feedback"])


@router.post("/feedback", status_code=201)
async def submit_feedback(request: Request, data: FeedbackSubmitRequest):
    user_id = getattr(request.state, "user_id", "anonymous")

    from app.services.feedback import FeedbackService
    svc = FeedbackService()
    record = svc.submit(
        user_id, data.target_type, data.target_id, data.feedback_type,
        reason=data.reason or "",
    )

    return {"code": 201, "data": record, "message": "反馈已提交", "meta": {}}


@router.get("/feedback/analysis")
async def get_feedback_analysis(request: Request):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录")

    from app.services.feedback import FeedbackService
    svc = FeedbackService()
    analysis = svc.analyze_feedback(user_id, [])
    return {"code": 200, "data": analysis, "message": "success", "meta": {}}


@router.get("/feedback/history")
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

    return {
        "code": 200,
        "data": {
            "items": [item.model_dump() for item in items],
            "total": len(items),
            "limit": limit,
            "source_type": source_type,
            "since": since,
        },
        "message": "success",
        "meta": {
            "data_source": "user_feedback_table",
            "model_version": "history-v1",
            "note": "Spec-007 T057: persisted feedback history endpoint",
        },
    }
