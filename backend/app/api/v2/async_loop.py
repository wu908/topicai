"""Thin adapters for the async creation loop (Spec-013 Phase 1)."""

from fastapi import APIRouter, Depends, Response

from app.api.deps import get_current_user, get_db
from app.core.database import Database
from app.models.common import ApiResponse
from app.models.v2.async_loop import (
    DeliverableView,
    DiscardRequest,
    InboxItemCreate,
    InboxItemView,
    MetricsRecord,
    PickupRequest,
)
from app.services.async_loop import (
    InboxService,
    LoopMetricsService,
    PickupService,
    ProductionService,
)
from app.services.weekly_review import WeeklyReviewService

router = APIRouter(prefix="/loop", tags=["AsyncLoop v2"])


@router.post("/inbox", response_model=ApiResponse[InboxItemView], status_code=201)
async def add_inbox_item(
    body: InboxItemCreate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    item, replayed = await InboxService(db).add(user["id"], body)
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data=item,
        meta={"idempotency_replayed": replayed},
    )


@router.get("/inbox", response_model=ApiResponse[dict])
async def list_inbox(
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    items = await InboxService(db).list(user["id"])
    return ApiResponse(data={"items": items, "total": len(items)})


@router.post("/inbox/digest", response_model=ApiResponse[dict])
async def digest_inbox(
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result = await ProductionService(db).digest(user["id"])
    return ApiResponse(data=result)


@router.get("/deliverables", response_model=ApiResponse[dict])
async def list_deliverables(
    status: str = "ready",
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    items = await ProductionService(db).list_deliverables(user["id"], status=status)
    return ApiResponse(data={"items": items, "total": len(items)})


@router.post(
    "/deliverables/{deliverable_id}:pickup",
    response_model=ApiResponse[dict],
)
async def pickup_deliverable(
    deliverable_id: str,
    body: PickupRequest,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await PickupService(db).pickup(user["id"], deliverable_id, body)
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data=result,
        meta={"idempotency_replayed": replayed},
    )


@router.post(
    "/deliverables/{deliverable_id}:discard",
    response_model=ApiResponse[DeliverableView],
)
async def discard_deliverable(
    deliverable_id: str,
    body: DiscardRequest,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    return ApiResponse(data=await PickupService(db).discard(
        user["id"], deliverable_id, body
    ))


@router.get("/weekly", response_model=ApiResponse[dict])
async def weekly_rows(
    days: int = 7,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    rows = await WeeklyReviewService(db).rows(user["id"], days=days)
    return ApiResponse(data={"items": rows, "total": len(rows)})


@router.post("/metrics", response_model=ApiResponse[dict], status_code=201)
async def record_metric(
    body: MetricsRecord,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    return ApiResponse(data=await LoopMetricsService(db).record(user["id"], body))


@router.get("/metrics", response_model=ApiResponse[dict])
async def list_metrics(
    metric: str | None = None,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    rows = await LoopMetricsService(db).list(user["id"], metric=metric)
    return ApiResponse(data={"items": rows, "total": len(rows)})
