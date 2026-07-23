"""HTTP adapters for explainable content opportunities."""

from fastapi import APIRouter, Depends, Response

from app.api.v1.deps import get_current_user, get_db
from app.core.database import Database
from app.core.llm import LLMClient
from app.models.common import ApiResponse
from app.models.v2.content_opportunity import (
    OpportunityDecision,
    SeriesExtensionCreate,
    UserSourceOpportunityCreate,
)
from app.services.content_opportunity import ContentOpportunityService

router = APIRouter(tags=["Content opportunities v2"])


def _proposal_service(db: Database) -> ContentOpportunityService:
    llm = None
    try:
        from config.settings import get_settings

        if get_settings().environment != "test":
            llm = LLMClient()
    except Exception:
        llm = None
    return ContentOpportunityService(db, llm=llm)


def _response(response: Response, result, replayed: bool):
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data=result,
        meta={"idempotency_replayed": replayed},
    )


@router.get("/content-opportunities")
async def list_content_opportunities(
    user=Depends(get_current_user), db: Database = Depends(get_db)
):
    return ApiResponse(
        data={"items": await ContentOpportunityService(db).list(user["id"])}
    )


@router.post("/creator-series/{series_id}/extension-opportunities", status_code=201)
async def propose_series_extension(
    series_id: str,
    body: SeriesExtensionCreate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await _proposal_service(db).propose_series_extension(
        user["id"], series_id, body
    )
    return _response(response, result, replayed)


@router.post("/content-opportunities/source-verification", status_code=201)
async def create_source_verification_opportunity(
    body: UserSourceOpportunityCreate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await ContentOpportunityService(db).create_user_source(
        user["id"], body
    )
    return _response(response, result, replayed)


@router.post("/content-opportunities/{opportunity_id}:decide", status_code=201)
async def decide_content_opportunity(
    opportunity_id: str,
    body: OpportunityDecision,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await ContentOpportunityService(db).decide(
        user["id"], opportunity_id, body
    )
    return _response(response, result, replayed)
