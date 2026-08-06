"""HTTP adapters for explicit creator viewpoint confirmation."""

from fastapi import APIRouter, Depends, Response

from app.api.deps import get_current_user, get_db
from app.core.database import Database
from app.core.llm import LLMClient
from app.models.common import ApiResponse
from app.models.v2.creator_viewpoint import (
    ViewpointCandidateCreate,
    ViewpointDecision,
    ViewpointRevocation,
)
from app.services.creator_viewpoint import CreatorViewpointService

router = APIRouter(tags=["Creator viewpoints v2"])


def _proposal_service(db: Database) -> CreatorViewpointService:
    llm = None
    try:
        from config.settings import get_settings

        if get_settings().environment != "test":
            llm = LLMClient()
    except Exception:
        llm = None
    return CreatorViewpointService(db, llm=llm)


def _response(response: Response, result, replayed: bool):
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data=result,
        meta={"idempotency_replayed": replayed},
    )


@router.get("/creator-viewpoints")
async def list_creator_viewpoints(
    user=Depends(get_current_user), db: Database = Depends(get_db)
):
    return ApiResponse(data={"items": await CreatorViewpointService(db).list(user["id"])})


@router.post("/projects/{project_id}/viewpoint-candidates", status_code=201)
async def propose_viewpoint_candidate(
    project_id: str,
    body: ViewpointCandidateCreate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await _proposal_service(db).propose(
        user["id"], project_id, body
    )
    return _response(response, result, replayed)


@router.post("/creator-viewpoints/{viewpoint_id}:decide", status_code=201)
async def decide_viewpoint_candidate(
    viewpoint_id: str,
    body: ViewpointDecision,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await CreatorViewpointService(db).decide(
        user["id"], viewpoint_id, body
    )
    return _response(response, result, replayed)


@router.post("/creator-viewpoints/{viewpoint_id}:revoke", status_code=201)
async def revoke_creator_viewpoint(
    viewpoint_id: str,
    body: ViewpointRevocation,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await CreatorViewpointService(db).revoke(
        user["id"], viewpoint_id, body
    )
    return _response(response, result, replayed)
