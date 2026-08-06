"""HTTP adapters for immutable candidate content review."""

from fastapi import APIRouter, Depends, Response

from app.api.deps import get_current_user, get_db
from app.core.database import Database
from app.models.common import ApiResponse
from app.models.v2.candidate_review import (
    CandidateRestoreInput,
    CandidateRevisionInput,
    SegmentDecisionInput,
)
from app.services.candidate_review import CandidateReviewService

router = APIRouter(tags=["Candidate review v2"])


def _response(response: Response, result, replayed: bool):
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data=result,
        meta={"idempotency_replayed": replayed},
    )


@router.get("/projects/{project_id}/candidate-review")
async def get_candidate_review(
    project_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    return ApiResponse(data=await CandidateReviewService(db).get(user["id"], project_id))


@router.post("/projects/{project_id}/candidate-review/segments/{segment_id}:decide", status_code=201)
async def decide_candidate_segment(
    project_id: str,
    segment_id: str,
    body: SegmentDecisionInput,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await CandidateReviewService(db).decide_segment(
        user["id"], project_id, segment_id, body
    )
    return _response(response, result, replayed)


@router.post("/projects/{project_id}/candidate-review:revise", status_code=201)
async def revise_candidate(
    project_id: str,
    body: CandidateRevisionInput,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await CandidateReviewService(db).revise(user["id"], project_id, body)
    return _response(response, result, replayed)


@router.post("/projects/{project_id}/candidate-review:restore", status_code=201)
async def restore_candidate(
    project_id: str,
    body: CandidateRestoreInput,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await CandidateReviewService(db).restore(user["id"], project_id, body)
    return _response(response, result, replayed)
