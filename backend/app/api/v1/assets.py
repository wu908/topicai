"""Asset API endpoints - Phase 6/7 contract.
8 endpoints matching frontend/src/types/contracts/assets.ts.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.api.v1.deps import get_current_user, get_db
from app.core.database import Database
from app.models.assets import (
    AssetListQuery, AssetUploadRequest, AssetTagUpdateRequest,
)
from app.models.common import ApiResponse
from app.services.asset_service import AssetService

router = APIRouter(tags=["Assets"])


@router.get("/assets")
async def list_assets(
    request: Request,
    type: str | None = None,
    tag_id: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    query = AssetListQuery(type=type, tag_id=tag_id, q=q, page=page, page_size=page_size)
    svc = AssetService(db)
    result = await svc.list(user["id"], query)
    return ApiResponse(code=200, data=result.model_dump(), message="success")


@router.get("/assets/storage")
async def get_storage(
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    svc = AssetService(db)
    result = await svc.storage_stats(user["id"])
    return ApiResponse(code=200, data=result.model_dump(), message="success")


@router.get("/assets/{asset_id}")
async def get_asset(
    asset_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    svc = AssetService(db)
    result = await svc.get(user["id"], asset_id)
    return ApiResponse(code=200, data=result.model_dump(), message="success")


@router.get("/assets/{asset_id}/usage")
async def get_asset_usage(
    asset_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    svc = AssetService(db)
    result = await svc.get_usage(asset_id)
    return ApiResponse(code=200, data=result, message="success")


@router.post("/assets/upload-url", status_code=201)
async def create_upload(
    body: AssetUploadRequest,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    svc = AssetService(db)
    result = await svc.create_upload(user["id"], body)
    return ApiResponse(code=201, data=result.model_dump(), message="Upload URL created")


@router.patch("/assets/{asset_id}/tags")
async def update_asset_tags(
    asset_id: str,
    body: AssetTagUpdateRequest,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    svc = AssetService(db)
    result = await svc.set_tags(user["id"], asset_id, body.tag_ids)
    return ApiResponse(code=200, data=result.model_dump(), message="Tags updated")


@router.delete("/assets/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    svc = AssetService(db)
    await svc.delete(user["id"], asset_id)
    return ApiResponse(code=204, data={}, message="Deleted")
