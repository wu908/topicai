"""Account API endpoints - Phase 6/7 contract.
6 endpoints matching frontend/src/types/contracts/accounts.ts.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.v1.deps import get_current_user, get_db
from app.core.database import Database
from app.models.accounts import Platform
from app.models.common import ApiResponse
from app.services.account_service import AccountService

router = APIRouter(tags=["Accounts"])


class CreateAccountBody(BaseModel):
    platform: Platform
    display_name: str


@router.get("/accounts")
async def list_accounts(
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    svc = AccountService(db)
    result = await svc.list(user["id"])
    return ApiResponse(code=200, data=[r.model_dump() for r in result], message="success")


@router.get("/accounts/{account_id}")
async def get_account(
    account_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    svc = AccountService(db)
    result = await svc.get(user["id"], account_id)
    return ApiResponse(code=200, data=result.model_dump(), message="success")


@router.post("/accounts", status_code=201)
async def create_account(
    body: CreateAccountBody,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    svc = AccountService(db)
    result = await svc.create(user["id"], body.platform, body.display_name)
    return ApiResponse(code=201, data=result.model_dump(), message="Account created")


@router.patch("/accounts/{account_id}")
async def set_primary_account(
    account_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    svc = AccountService(db)
    result = await svc.set_primary(user["id"], account_id)
    return ApiResponse(code=200, data=result.model_dump(), message="Primary set")


@router.delete("/accounts/{account_id}", status_code=204)
async def disconnect_account(
    account_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    svc = AccountService(db)
    await svc.disconnect(user["id"], account_id)
    return ApiResponse(code=204, data={}, message="Disconnected")


@router.post("/accounts/{account_id}/sync", status_code=202)
async def trigger_sync(
    account_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    svc = AccountService(db)
    result = await svc.trigger_sync(user["id"], account_id)
    return ApiResponse(code=202, data={"last_sync_at": result}, message="Sync triggered")
