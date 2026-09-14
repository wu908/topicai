"""Thin HTTP adapters for the first ContentProject vertical slice."""

from fastapi import APIRouter, Depends, Response

from app.api.deps import get_current_user, get_db
from app.core.database import Database
from app.models.common import ApiResponse
from app.models.v2.content_project import (
    ContentProjectCreate,
    ContentVersionCreate,
    ProjectTransition,
)
from app.models.v2.project_start import ProjectStartRequest
from app.models.v2.publish_hypothesis import PublishHypothesisLock
from app.services.calibration_workspace import CalibrationWorkspaceService
from app.services.content_project import ContentProjectService
from app.services.content_version import ContentVersionService
from app.services.project_start import ProjectStartService
from app.services.project_state import ProjectStateService
from app.services.publish_hypothesis import PublishHypothesisService

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


@router.post("/start", status_code=201)
async def start_project(
    body: ProjectStartRequest,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """「开始一条内容」：一句话或一条已有素材 → AI 推断意图 → 建项目。

    与 POST /projects 的区别：用户不需要先给标题、选意图、写读者变化；
    推断结果回给前端呈现，用户只在不对时一句话纠正。
    """
    result = await ProjectStartService(db).start(user["id"], body)
    return ApiResponse(data=result.model_dump(mode="json"))


@router.post("/{project_id}:dismiss-inference", status_code=200)
async def dismiss_start_inference(
    project_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """用户说「不对，我自己选」：清掉 AI 的推断，回到既有的意图确认步骤。

    这也是推断的唯一回退路径——推断不是用户确认，所以必须能被一句话撤销。
    """
    await ContentProjectService(db).dismiss_start_inference(user["id"], project_id)
    return ApiResponse(data={"project_id": project_id})


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    project = await ContentProjectService(db).get(user["id"], project_id)
    return ApiResponse(data=project)


@router.post("/{project_id}/transitions", status_code=201)
async def transition_project(
    project_id: str,
    body: ProjectTransition,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await ProjectStateService(db).transition(
        user["id"], project_id, body
    )
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data=result,
        meta={"idempotency_replayed": replayed},
    )


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    await ContentProjectService(db).delete(user["id"], project_id)
    return Response(status_code=204)


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
