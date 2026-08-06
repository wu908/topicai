"""HTTP adapters for explainable content opportunities."""

from typing import Literal

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import get_current_user, get_db
from app.core.database import Database
from app.core.llm import LLMClient
from app.models.common import ApiResponse
from app.models.v2.content_opportunity import (
    ContentOpportunityView,
    OpportunityDecision,
    OpportunityGenerateRequest,
    OpportunityListResult,
    OpportunitySourceVerification,
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


def _response(
    response: Response, result, replayed: bool
) -> ApiResponse[ContentOpportunityView]:
    response.status_code = 200 if replayed else 201
    return ApiResponse[ContentOpportunityView](
        code=response.status_code,
        data=result,
        meta={"idempotency_replayed": replayed},
    )


@router.get(
    "/content-opportunities",
    response_model=ApiResponse[OpportunityListResult],
)
async def list_content_opportunities(
    opportunity_type: Literal[
        "series_extension",
        "user_source",
        "history_derivative",
        "user_question",
        "material_derivative",
        "insight_derivative",
        "evergreen",
    ]
    | None = Query(default=None, alias="type"),
    decision: Literal["adopt", "save", "reject"] | None = None,
    timeliness: Literal[
        "evergreen", "current", "expiring", "expired", "unknown"
    ]
    | None = None,
    user=Depends(get_current_user), db: Database = Depends(get_db)
):
    return ApiResponse[OpportunityListResult](
        data=OpportunityListResult(
            items=await ContentOpportunityService(db).list(
                user["id"], opportunity_type, decision, timeliness
            )
        )
    )


@router.post(
    "/content-opportunities:generate",
    response_model=ApiResponse[OpportunityListResult],
)
async def generate_content_opportunities(
    body: OpportunityGenerateRequest,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    return ApiResponse[OpportunityListResult](
        data=OpportunityListResult(
            items=await ContentOpportunityService(db).generate(
                user["id"], body.desired_count
            )
        )
    )


@router.post(
    "/creator-series/{series_id}/extension-opportunities",
    status_code=201,
    response_model=ApiResponse[ContentOpportunityView],
)
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


@router.post(
    "/content-opportunities/source-verification",
    status_code=201,
    response_model=ApiResponse[ContentOpportunityView],
)
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


@router.post(
    "/content-opportunities/{opportunity_id}:decide",
    status_code=201,
    response_model=ApiResponse[ContentOpportunityView],
)
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


@router.post(
    "/content-opportunities/{opportunity_id}:verify-source",
    status_code=201,
    response_model=ApiResponse[ContentOpportunityView],
)
async def verify_content_opportunity_source(
    opportunity_id: str,
    body: OpportunitySourceVerification,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await ContentOpportunityService(db).verify_source(
        user["id"], opportunity_id, body
    )
    return _response(response, result, replayed)
