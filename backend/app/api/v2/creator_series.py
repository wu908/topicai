"""HTTP adapters for explicit creator series confirmation."""

from fastapi import APIRouter, Depends, Response

from app.api.v1.deps import get_current_user, get_db
from app.core.database import Database
from app.core.llm import LLMClient
from app.models.common import ApiResponse
from app.models.v2.creator_series import (
    SeriesCandidateCreate,
    SeriesDecision,
    SeriesRevocation,
)
from app.services.creator_series import CreatorSeriesService

router = APIRouter(tags=["Creator series v2"])


def _proposal_service(db: Database) -> CreatorSeriesService:
    llm = None
    try:
        from config.settings import get_settings

        if get_settings().environment != "test":
            llm = LLMClient()
    except Exception:
        llm = None
    return CreatorSeriesService(db, llm=llm)


def _response(response: Response, result, replayed: bool):
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data=result,
        meta={"idempotency_replayed": replayed},
    )


@router.get("/creator-series")
async def list_creator_series(
    user=Depends(get_current_user), db: Database = Depends(get_db)
):
    return ApiResponse(data={"items": await CreatorSeriesService(db).list(user["id"])})


@router.post("/creator-series-candidates", status_code=201)
async def propose_series_candidate(
    body: SeriesCandidateCreate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await _proposal_service(db).propose(user["id"], body)
    return _response(response, result, replayed)


@router.post("/creator-series/{series_id}:decide", status_code=201)
async def decide_series_candidate(
    series_id: str,
    body: SeriesDecision,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await CreatorSeriesService(db).decide(user["id"], series_id, body)
    return _response(response, result, replayed)


@router.post("/creator-series/{series_id}:revoke", status_code=201)
async def revoke_creator_series(
    series_id: str,
    body: SeriesRevocation,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await CreatorSeriesService(db).revoke(user["id"], series_id, body)
    return _response(response, result, replayed)
