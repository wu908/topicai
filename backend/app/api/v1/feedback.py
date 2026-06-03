"""Feedback API endpoints for TopicAI v4.0."""

import logging

from fastapi import APIRouter, HTTPException, Request

from app.models.feedback import FeedbackSubmitRequest

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
