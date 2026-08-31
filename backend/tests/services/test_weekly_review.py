"""Weekly review aggregation contracts (Spec-013 Phase 1 tail)."""

from datetime import UTC, datetime, timedelta

import pytest

from app.models.v2.calibration import (
    BlindReviewCreate,
    PerformanceMetrics,
    PerformanceSnapshotCreate,
)
from app.services.blind_review import BlindReviewService
from app.services.content_project import ContentProjectService
from app.services.performance_snapshot import PerformanceSnapshotService
from app.services.weekly_review import WeeklyReviewService
from tests.helpers.publish import insert_user
from tests.helpers.publish import published_project as _published_project

OTHER = "weekly-other"



async def _append_snapshot(test_db, project, publish_id, suffix):
    project = await ContentProjectService(test_db).get("u1", project["id"])
    result, _ = await PerformanceSnapshotService(test_db).append(
        "u1",
        publish_id,
        PerformanceSnapshotCreate(
            captured_at=(datetime.now(UTC) - timedelta(hours=1)).isoformat(),
            source="manual",
            metrics=PerformanceMetrics(favorites=41, comments=6),
            confirmed_by_user=True,
            expected_project_version=project["version"],
            idempotency_key=f"weekly-snap-{suffix}",
        ),
    )
    return result["snapshot"]


@pytest.mark.asyncio
async def test_no_publications_means_no_rows(test_db):
    await insert_user(test_db, "u1")
    assert await WeeklyReviewService(test_db).rows("u1") == []


@pytest.mark.asyncio
async def test_published_project_starts_at_needs_snapshot(test_db):
    await insert_user(test_db, "u1")
    project = await _published_project(test_db, "w1")
    rows = await WeeklyReviewService(test_db).rows("u1")
    assert len(rows) == 1 and rows[0]["project_id"] == project["id"]
    assert rows[0]["stage"] == "needs_snapshot"
    assert rows[0]["judgment"]["audience_change"] == "读者持续看到创作者建立更新节奏"
    assert rows[0]["actual"]["captured_at"] is None


@pytest.mark.asyncio
async def test_snapshot_advances_stage_to_needs_review(test_db):
    await insert_user(test_db, "u1")
    project = await _published_project(test_db, "w2")
    record = await test_db.fetch_one(
        "SELECT id FROM publish_records_v2 WHERE project_id=:p",
        {"p": project["id"]},
    )
    await _append_snapshot(test_db, project, record["id"], "w2")
    row = (await WeeklyReviewService(test_db).rows("u1"))[0]
    assert row["stage"] == "needs_review"
    assert row["actual"]["metrics"]["favorites"] == 41


@pytest.mark.asyncio
async def test_blind_review_insufficient_flags_stage(test_db):
    await insert_user(test_db, "u1")
    project = await _published_project(test_db, "w3")
    record = await test_db.fetch_one(
        "SELECT id FROM publish_records_v2 WHERE project_id=:p",
        {"p": project["id"]},
    )
    snapshot = await _append_snapshot(test_db, project, record["id"], "w3")
    await BlindReviewService(test_db).create(
        "u1",
        project["id"],
        BlindReviewCreate(
            result_snapshot_ids=[snapshot["id"]],
            expected_project_version=project["version"] + 1,
            idempotency_key="weekly-review-w3",
        ),
    )
    row = (await WeeklyReviewService(test_db).rows("u1"))[0]
    assert row["stage"] in ("review_insufficient", "ready_to_confirm")
    assert row["review"] is not None
    assert row["observation"] is None


@pytest.mark.asyncio
async def test_owner_isolation(test_db):
    await insert_user(test_db, "u1")
    await insert_user(test_db, OTHER)
    await _published_project(test_db, "w4")
    assert await WeeklyReviewService(test_db).rows(OTHER) == []
