"""HTTP adapters for the bounded starter experiment."""

from fastapi import APIRouter, Depends, Response

from app.api.v1.deps import get_current_user, get_db
from app.core.database import Database
from app.models.common import ApiResponse
from app.models.v2.starter import (
    DirectionGenerate,
    DirectionSelect,
    StarterAssessmentCreate,
    StarterSprintReview,
)
from app.services.direction_candidate import DirectionCandidateService
from app.services.starter_assessment import StarterAssessmentService
from app.services.starter_sprint import StarterSprintService

router = APIRouter(prefix="/starter", tags=["Starter v2"])


@router.get("")
async def get_starter_workspace(
    user=Depends(get_current_user), db: Database = Depends(get_db)
):
    return ApiResponse(data=await StarterSprintService(db).workspace(user["id"]))


@router.post("/assessment", status_code=201)
async def submit_assessment(
    body: StarterAssessmentCreate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    assessment, replayed = await StarterAssessmentService(db).submit(user["id"], body)
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data={"assessment": assessment, "next_step": "directions" if assessment["readiness"] == "ready" else "assessment"},
        meta={"idempotency_replayed": replayed},
    )


@router.post("/directions:generate", status_code=201)
async def generate_directions(
    body: DirectionGenerate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    candidates, replayed = await DirectionCandidateService(db).generate(user["id"], body)
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data={"candidates": candidates, "next_step": "directions"},
        meta={"idempotency_replayed": replayed},
    )


@router.post("/directions/{direction_id}:select", status_code=201)
async def select_direction(
    direction_id: str,
    body: DirectionSelect,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    workspace, replayed = await StarterSprintService(db).select_direction(
        user["id"], direction_id, body
    )
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data=workspace,
        meta={"idempotency_replayed": replayed},
    )


@router.post("/sprints/{sprint_id}:review")
async def review_sprint(
    sprint_id: str,
    body: StarterSprintReview,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    workspace, replayed = await StarterSprintService(db).review(user["id"], sprint_id, body)
    return ApiResponse(
        data=workspace,
        meta={"idempotency_replayed": replayed},
    )
