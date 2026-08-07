"""Version-bound publish check adapters."""

from fastapi import APIRouter, Depends, Response

from app.api.deps import get_current_user, get_db
from app.core.database import Database
from app.models.common import ApiResponse
from app.models.v2.publish_check import (
    PublishCheckCreate,
    PublishCheckResolution,
    PublishCheckView,
)
from app.services.publish_check import PublishCheckService

router = APIRouter(tags=["Publish checks v2"])


def _created(response: Response, result, replayed: bool):
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data=result,
        meta={"idempotency_replayed": replayed},
    )


@router.post(
    "/projects/{project_id}/publish-checks",
    response_model=ApiResponse[PublishCheckView],
    status_code=201,
)
async def run_publish_check(
    project_id: str,
    body: PublishCheckCreate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await PublishCheckService(db).run(user["id"], project_id, body)
    return _created(response, result, replayed)


@router.get(
    "/projects/{project_id}/publish-checks/latest",
    response_model=ApiResponse[PublishCheckView | None],
)
async def get_latest_publish_check(
    project_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    return ApiResponse(data=await PublishCheckService(db).latest(user["id"], project_id))


@router.put(
    "/publish-checks/{check_id}/resolution",
    response_model=ApiResponse[PublishCheckView],
    status_code=201,
)
async def resolve_publish_check(
    check_id: str,
    body: PublishCheckResolution,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await PublishCheckService(db).resolve(user["id"], check_id, body)
    return _created(response, result, replayed)
