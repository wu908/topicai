"""HTTP adapters for the derived ContentGenome read model."""

from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_db
from app.core.database import Database
from app.models.common import ApiResponse
from app.services.content_genome import ContentGenomeService

router = APIRouter(tags=["ContentGenome v2"])


@router.get("/content-genome")
async def search_content_genome(
    content_intent: Literal["solve", "share", "record"] | None = None,
    audience: str | None = Query(default=None, max_length=500),
    content_format: Literal["graphic_note", "vlog_plan"] | None = None,
    experiment: str | None = Query(default=None, max_length=1000),
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result = await ContentGenomeService(db).search(
        user["id"],
        content_intent=content_intent,
        audience=audience,
        content_format=content_format,
        experiment=experiment,
    )
    return ApiResponse(data=result)


@router.get("/projects/{project_id}/content-genome")
async def get_project_content_genome(
    project_id: str,
    experiment: str | None = Query(default=None, max_length=1000),
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result = await ContentGenomeService(db).for_project(
        user["id"], project_id, experiment=experiment
    )
    return ApiResponse(data=result)
