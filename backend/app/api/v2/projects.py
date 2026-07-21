"""Thin HTTP adapters for the first ContentProject vertical slice."""

from fastapi import APIRouter, Depends, Response

from app.api.v1.deps import get_current_user, get_db
from app.core.database import Database
from app.models.common import ApiResponse
from app.models.v2.content_project import ContentProjectCreate, ContentVersionCreate
from app.models.v2.publish_hypothesis import PublishHypothesisLock
from app.services.content_project import ContentProjectService
from app.services.content_version import ContentVersionService
from app.services.publish_hypothesis import PublishHypothesisService
from app.services.calibration_workspace import CalibrationWorkspaceService

router = APIRouter(prefix="/projects", tags=["ContentProject v2"])


@router.get("")
async def list_projects(
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result = await CalibrationWorkspaceService(db).list_projects(user["id"])
    return ApiResponse(data=result)


@router.post("", status_code=201)
async def create_project(
    body: ContentProjectCreate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    project, replayed = await ContentProjectService(db).create(user["id"], body)
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data=project,
        meta={"idempotency_replayed": replayed},
    )


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    project = await ContentProjectService(db).get(user["id"], project_id)
    return ApiResponse(data=project)


@router.post("/{project_id}/versions", status_code=201)
async def create_version(
    project_id: str,
    body: ContentVersionCreate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    version, replayed = await ContentVersionService(db).create(
        user["id"], project_id, body
    )
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data=version,
        meta={"idempotency_replayed": replayed},
    )


@router.post("/{project_id}/publish-hypothesis:lock", status_code=201)
async def lock_publish_hypothesis(
    project_id: str,
    body: PublishHypothesisLock,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await PublishHypothesisService(db).lock(
        user["id"], project_id, body
    )
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data=result,
        meta={"idempotency_replayed": replayed},
    )
