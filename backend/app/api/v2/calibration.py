"""Thin HTTP adapters for publication and calibration records."""

from fastapi import APIRouter, Depends, Response

from app.api.v1.deps import get_current_user, get_db
from app.core.database import Database
from app.models.common import ApiResponse
from app.models.v2.calibration import (
    BenchmarkSampleCreate,
    BenchmarkSampleInclusionUpdate,
    BlindReviewCreate,
    ObservationCreate,
    ObservationTransition,
    PerformanceSnapshotCreate,
    PublishRecordCreate,
)
from app.models.v2.publish_hypothesis import PublishHypothesisAmendmentCreate
from app.services.benchmark_sample import BenchmarkSampleService
from app.services.blind_review import BlindReviewService
from app.services.calibration_workspace import CalibrationWorkspaceService
from app.services.observation import ObservationService
from app.services.performance_snapshot import PerformanceSnapshotService
from app.services.publication import PublicationService
from app.services.publish_hypothesis import PublishHypothesisService

router = APIRouter(tags=["Calibration v2"])


def _response(response: Response, result, replayed: bool):
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data=result,
        meta={"idempotency_replayed": replayed},
    )


@router.get("/projects/{project_id}/calibration")
async def get_calibration_workspace(
    project_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result = await CalibrationWorkspaceService(db).get(user["id"], project_id)
    return ApiResponse(data=result)


@router.get("/publish-hypotheses/{hypothesis_id}/amendments")
async def list_hypothesis_amendments(
    hypothesis_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result = await PublishHypothesisService(db).list_amendments(
        user["id"], hypothesis_id
    )
    return ApiResponse(data=result)


@router.post("/publish-hypotheses/{hypothesis_id}/amendments", status_code=201)
async def amend_publish_hypothesis(
    hypothesis_id: str,
    body: PublishHypothesisAmendmentCreate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await PublishHypothesisService(db).amend(
        user["id"], hypothesis_id, body
    )
    return _response(response, result, replayed)


@router.get("/benchmark-samples")
async def list_benchmark_samples(
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    return ApiResponse(data=await BenchmarkSampleService(db).list(user["id"]))


@router.post("/benchmark-samples", status_code=201)
async def create_benchmark_sample(
    body: BenchmarkSampleCreate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await BenchmarkSampleService(db).create(user["id"], body)
    return _response(response, result, replayed)


@router.post("/benchmark-samples/{sample_id}/inclusion", status_code=201)
async def set_benchmark_sample_inclusion(
    sample_id: str,
    body: BenchmarkSampleInclusionUpdate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await BenchmarkSampleService(db).set_inclusion(
        user["id"], sample_id, body
    )
    return _response(response, result, replayed)


@router.post("/projects/{project_id}/publish-records", status_code=201)
async def record_publication(
    project_id: str,
    body: PublishRecordCreate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await PublicationService(db).record(user["id"], project_id, body)
    return _response(response, result, replayed)


@router.post("/publish-records/{publish_record_id}/snapshots", status_code=201)
async def append_snapshot(
    publish_record_id: str,
    body: PerformanceSnapshotCreate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await PerformanceSnapshotService(db).append(
        user["id"], publish_record_id, body
    )
    return _response(response, result, replayed)


@router.post("/projects/{project_id}/blind-reviews", status_code=201)
async def create_blind_review(
    project_id: str,
    body: BlindReviewCreate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await BlindReviewService(db).create(
        user["id"], project_id, body
    )
    return _response(response, result, replayed)


@router.post("/blind-reviews/{blind_review_id}/observations", status_code=201)
async def create_observation(
    blind_review_id: str,
    body: ObservationCreate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await ObservationService(db).create(
        user["id"], blind_review_id, body
    )
    return _response(response, result, replayed)


@router.post("/observations/{observation_id}/transitions", status_code=201)
async def transition_observation(
    observation_id: str,
    body: ObservationTransition,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await ObservationService(db).transition(
        user["id"], observation_id, body
    )
    return _response(response, result, replayed)
