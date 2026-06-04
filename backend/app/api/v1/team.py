"""Team API endpoints - Phase 6/7 contract.
4 endpoints matching frontend/src/types/contracts/accounts.ts team section.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.v1.deps import get_current_user, get_db
from app.core.database import Database
from app.models.accounts import TeamRole
from app.models.common import ApiResponse
from app.services.team_service import TeamService

router = APIRouter(tags=["Team"])


class InviteBody(BaseModel):
    email: str
    role: TeamRole
    username: str


class ChangeRoleBody(BaseModel):
    role: TeamRole


@router.get("/team/members")
async def list_members(
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    svc = TeamService(db)
    result = await svc.list(user["id"])
    return ApiResponse(code=200, data=[r.model_dump() for r in result], message="success")


@router.post("/team/members", status_code=201)
async def invite_member(
    body: InviteBody,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    svc = TeamService(db)
    result = await svc.invite(user["id"], body.email, body.username, body.role)
    # REST convention: 201 created responses should advertise the
    # canonical location of the new resource.
    return JSONResponse(
        status_code=201,
        content=ApiResponse(code=201, data=result.model_dump(), message="Member invited").model_dump(),
        headers={"Location": f"/api/v1/team/members/{result.id}"},
    )


@router.patch("/team/members/{member_id}")
async def change_role(
    member_id: str,
    body: ChangeRoleBody,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    svc = TeamService(db)
    result = await svc.change_role(user["id"], member_id, body.role)
    return ApiResponse(code=200, data=result.model_dump(), message="Role changed")


@router.delete("/team/members/{member_id}", status_code=204)
async def remove_member(
    member_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    svc = TeamService(db)
    await svc.remove(user["id"], member_id)
    return ApiResponse(code=204, data={}, message="Member removed")
