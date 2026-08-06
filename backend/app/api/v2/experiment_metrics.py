"""Internal, owner-scoped experiment assignment and validation export APIs."""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import get_current_user, get_db
from app.core.database import Database
from app.models.common import ApiResponse
from app.models.v2.experiment_metrics import (
    ActionMetricsExport,
    ExperimentAssignmentUpsert,
    ExperimentAssignmentView,
    ExperimentId,
)
from app.services.experiment_metrics import ExperimentAssignmentService, ExperimentMetricsService

router = APIRouter(prefix="/internal/validation", tags=["Internal MVP validation"])


@router.put(
    "/experiments/{experiment_id}/assignment",
    status_code=201,
    response_model=ApiResponse[ExperimentAssignmentView],
)
async def assign_experiment(
    experiment_id: ExperimentId,
    body: ExperimentAssignmentUpsert,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await ExperimentAssignmentService(db).upsert(
        user["id"], experiment_id, body
    )
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data=ExperimentAssignmentView.model_validate(result),
        meta={"idempotency_replayed": replayed},
    )


@router.get("/action-metrics", response_model=ApiResponse[ActionMetricsExport])
async def export_action_metrics(
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    experiment_id: ExperimentId | None = Query(default=None),
    cohort: Literal["control", "variant", "observational", "excluded"] | None = Query(
        default=None
    ),
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    data = await ExperimentMetricsService(db).export(
        user["id"],
        start_at=start_at,
        end_at=end_at,
        experiment_id=experiment_id,
        cohort=cohort,
    )
    return ApiResponse(data=ActionMetricsExport.model_validate(data))
