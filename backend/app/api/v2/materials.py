"""Thin material CRUD and reuse adapters."""

from fastapi import APIRouter, Depends, Response

from app.api.deps import get_current_user, get_db
from app.core.database import Database
from app.models.common import ApiResponse
from app.models.v2.material import (
    MaterialCreate,
    MaterialListResult,
    MaterialUpdate,
    MaterialUsageCreate,
    MaterialView,
)
from app.services.material import MaterialService

router = APIRouter(prefix="/materials", tags=["Materials v2"])


@router.get("", response_model=ApiResponse[MaterialListResult])
async def list_materials(
    kind: str | None = None,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    items = await MaterialService(db).list(user["id"], kind=kind)
    return ApiResponse(data={"items": items, "total": len(items)})


@router.post("", response_model=ApiResponse[MaterialView], status_code=201)
async def create_material(
    body: MaterialCreate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await MaterialService(db).create(user["id"], body)
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data=result,
        meta={"idempotency_replayed": replayed},
    )


@router.get("/{material_id}", response_model=ApiResponse[MaterialView])
async def get_material(
    material_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    return ApiResponse(data=await MaterialService(db).get(user["id"], material_id))


@router.get("/{material_id}/content")
async def get_material_content(
    material_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    content, mime_type = await MaterialService(db).content_bytes(
        user["id"], material_id
    )
    return Response(
        content=content,
        media_type=mime_type,
        headers={
            "Content-Disposition": "attachment",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.patch("/{material_id}", response_model=ApiResponse[MaterialView])
async def update_material(
    material_id: str,
    body: MaterialUpdate,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    return ApiResponse(
        data=await MaterialService(db).update(user["id"], material_id, body)
    )


@router.post(
    "/{material_id}/usages",
    response_model=ApiResponse[MaterialView],
    status_code=201,
)
async def add_material_usage(
    material_id: str,
    body: MaterialUsageCreate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await MaterialService(db).add_usage(
        user["id"], material_id, body
    )
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data=result,
        meta={"idempotency_replayed": replayed},
    )


@router.delete("/{material_id}", status_code=204)
async def delete_material(
    material_id: str,
    confirmed: bool = False,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    await MaterialService(db).delete(user["id"], material_id, confirmed=confirmed)
    return Response(status_code=204)
