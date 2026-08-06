"""Owner settings adapters."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_db
from app.core.database import Database
from app.models.common import ApiResponse
from app.models.v2.settings import UserSettingsUpdate, UserSettingsView
from app.services.settings import UserSettingsService

router = APIRouter(prefix="/settings", tags=["Settings v2"])


@router.get("", response_model=ApiResponse[UserSettingsView])
async def get_settings(
    user=Depends(get_current_user), db: Database = Depends(get_db)
):
    return ApiResponse(data=await UserSettingsService(db).get(user["id"]))


@router.put("", response_model=ApiResponse[UserSettingsView])
async def update_settings(
    body: UserSettingsUpdate,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    return ApiResponse(data=await UserSettingsService(db).update(user["id"], body))
