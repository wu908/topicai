"""HTTP adapters for Growth onboarding and correctable creator profiles."""

from fastapi import APIRouter, Depends, Response

from app.api.deps import get_current_user, get_db
from app.core.database import Database
from app.models.common import ApiResponse
from app.models.v2.onboarding import (
    CreatorProfileResult,
    CreatorProfileUpdate,
    HistoryImportCreate,
    HistoryImportResult,
    OnboardingContext,
    ProductModeUpdate,
)
from app.services.creator_profile_v2 import CreatorProfileV2Service
from app.services.history_import import HistoryImportService
from app.services.onboarding_mode import OnboardingModeService

router = APIRouter(tags=["Growth onboarding v2"])


@router.get("/onboarding", response_model=ApiResponse[OnboardingContext])
async def get_onboarding_context(user=Depends(get_current_user), db: Database = Depends(get_db)):
    return ApiResponse[OnboardingContext](data=await OnboardingModeService(db).get(user["id"]))


@router.put("/onboarding/mode", response_model=ApiResponse[OnboardingContext])
async def select_mode(
    body: ProductModeUpdate,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    return ApiResponse[OnboardingContext](
        data=await OnboardingModeService(db).select(user["id"], body)
    )


@router.post(
    "/history-imports",
    status_code=201,
    response_model=ApiResponse[HistoryImportResult],
)
async def import_history(
    body: HistoryImportCreate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await HistoryImportService(db).import_items(user["id"], body)
    response.status_code = 200 if replayed else 201
    return ApiResponse[HistoryImportResult](
        code=response.status_code,
        data=result,
        meta={"idempotency_replayed": replayed},
    )


@router.get("/creator-profile", response_model=ApiResponse[CreatorProfileResult])
async def get_creator_profile(user=Depends(get_current_user), db: Database = Depends(get_db)):
    return ApiResponse[CreatorProfileResult](
        data=await CreatorProfileV2Service(db).get_or_build(user["id"])
    )


@router.put("/creator-profile", response_model=ApiResponse[CreatorProfileResult])
async def update_creator_profile(
    body: CreatorProfileUpdate,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    return ApiResponse[CreatorProfileResult](
        data=await CreatorProfileV2Service(db).update(user["id"], body)
    )
