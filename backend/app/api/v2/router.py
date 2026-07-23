"""Root router for the ContentProject API."""

from fastapi import APIRouter

from app.models.common import ApiResponse
from app.api.v2.calibration import router as calibration_router
from app.api.v2.projects import router as projects_router
from app.api.v2.intent_actions import router as intent_actions_router
from app.api.v2.candidate_review import router as candidate_review_router
from app.api.v2.creator_rules import router as creator_rules_router
from app.api.v2.content_genome import router as content_genome_router
from app.api.v2.creator_viewpoints import router as creator_viewpoints_router
from app.api.v2.creator_series import router as creator_series_router
from app.api.v2.content_opportunities import router as content_opportunities_router
from app.api.v2.experiment_metrics import router as experiment_metrics_router
from app.api.v2.starter import router as starter_router
from app.api.v2.account_data import router as account_data_router

api_v2_router = APIRouter()
api_v2_router.include_router(projects_router)
api_v2_router.include_router(calibration_router)
api_v2_router.include_router(intent_actions_router)
api_v2_router.include_router(candidate_review_router)
api_v2_router.include_router(creator_rules_router)
api_v2_router.include_router(content_genome_router)
api_v2_router.include_router(creator_viewpoints_router)
api_v2_router.include_router(creator_series_router)
api_v2_router.include_router(content_opportunities_router)
api_v2_router.include_router(experiment_metrics_router)
api_v2_router.include_router(starter_router)
api_v2_router.include_router(account_data_router)


@api_v2_router.get("/health", response_model=ApiResponse[dict])
async def health() -> ApiResponse[dict]:
    """Report availability of the provider-neutral v2 API shell."""
    return ApiResponse(
        data={
            "status": "ok",
            "api_version": "v2",
            "product": "content_project",
        }
    )
