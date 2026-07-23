"""Owner-controlled export and deletion endpoints."""

from fastapi import APIRouter, Depends, Response

from app.api.v1.deps import get_current_user, get_db
from app.core.database import Database
from app.models.common import ApiResponse
from app.models.v2.intent_actions import AccountGateRequest, HumanGateType
from app.services.account_data import AccountDataService
from app.services.intent_actions import HumanGateService


router = APIRouter(prefix="/account", tags=["Account data v2"])


@router.post("/data-export:request", status_code=201)
async def request_data_export(
    body: AccountGateRequest,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    gate, replayed = await HumanGateService(db).ensure_for_account(
        user["id"], HumanGateType.PRIVACY, body.idempotency_key
    )
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data=gate,
        meta={"idempotency_replayed": replayed},
    )


@router.get("/data-export")
async def export_account_data(
    gate_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    return ApiResponse(data=await AccountDataService(db).export(user["id"], gate_id))


@router.post("/deletion:request", status_code=201)
async def request_account_deletion(
    body: AccountGateRequest,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    gate, replayed = await HumanGateService(db).ensure_for_account(
        user["id"], HumanGateType.DELETION, body.idempotency_key
    )
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data=gate,
        meta={"idempotency_replayed": replayed},
    )


@router.delete("", status_code=204)
async def delete_account(
    gate_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    await AccountDataService(db).delete_account(user["id"], gate_id)
    return Response(status_code=204)
