"""Tenant scoping for benchmark successor lookups.

Covers an ocr scan finding (session be776634): the successor query in
``BenchmarkSampleService._historical_metrics`` was the only lookup in the
file without an owner predicate, so a snapshot written by another tenant
with ``supersedes_id`` pointing at this owner's snapshot would deny a
legitimate benchmark operation.
"""

import json

import pytest
from sqlalchemy import text

from app.models.v2.content_project import ContentProjectCreate
from app.services.benchmark_sample import BenchmarkSampleService
from app.services.content_project import ContentProjectService


@pytest.mark.asyncio
async def test_cross_tenant_successor_does_not_block_benchmark_metrics(test_db):
    session = await test_db.get_session()
    async with session:
        await session.execute(
            text(
                "INSERT INTO users (id,email,username,password_hash,ai_calls_today,"
                "ai_calls_reset_at,created_at) VALUES "
                "('u1','u1@bench.test','u1-bench','hash',0,'','2026-08-01T00:00:00Z'),"
                "('u2','u2@bench.test','u2-bench','hash',0,'','2026-08-01T00:00:00Z')"
            )
        )
        await session.commit()

    project, _ = await ContentProjectService(test_db).create(
        "u1",
        ContentProjectCreate(title="基准项目", idempotency_key="bench-project-1"),
    )
    project_id = project["id"]

    session = await test_db.get_session()
    async with session:
        # Seed calibration rows directly; the FK chain (publish records,
        # versions, hypotheses) is not what this test exercises.
        await session.execute(text("PRAGMA foreign_keys=OFF"))
        await session.execute(
            text(
                "INSERT INTO publish_records_v2 (id,owner_user_id,project_id,"
                "locked_version_id,publish_hypothesis_id,platform,published_at,"
                "recorded_at,idempotency_key,request_hash,created_at) VALUES "
                "('rec-a','u1',:project,'ver-x','hyp-x','xiaohongshu',"
                "'2026-08-01T00:00:00Z','2026-08-01T00:00:00Z','rec-key','rec-hash',"
                "'2026-08-01T00:00:00Z')"
            ),
            {"project": project_id},
        )
        snapshot_sql = (
            "INSERT INTO performance_snapshots_v2 (id,owner_user_id,"
            "publish_record_id,project_id,captured_at,source,metrics_json,"
            "confirmed_by_user,supersedes_id,idempotency_key,request_hash,"
            "created_at) VALUES "
            "(:id,:owner,'rec-a',:project,:captured,'manual',:metrics,1,"
            ":supersedes,:key,:hash,:captured)"
        )
        await session.execute(
            text(snapshot_sql),
            {
                "id": "snap-a",
                "owner": "u1",
                "project": project_id,
                "captured": "2026-08-02T00:00:00Z",
                "metrics": json.dumps({"views": 10}),
                "supersedes": None,
                "key": "snap-a-key",
                "hash": "snap-a-hash",
            },
        )
        # Another tenant claims to supersede u1's snapshot.
        await session.execute(
            text(snapshot_sql),
            {
                "id": "snap-b",
                "owner": "u2",
                "project": project_id,
                "captured": "2026-08-03T00:00:00Z",
                "metrics": json.dumps({"views": 99}),
                "supersedes": "snap-a",
                "key": "snap-b-key",
                "hash": "snap-b-hash",
            },
        )
        await session.execute(text("PRAGMA foreign_keys=ON"))
        await session.commit()

        metrics, record_id = await BenchmarkSampleService._historical_metrics(
            session, "u1", project_id, ["snap-a"]
        )

    assert record_id == "rec-a"
    assert metrics == {"views": 10}


@pytest.mark.asyncio
async def test_same_tenant_successor_still_blocks_benchmark_metrics(test_db):
    session = await test_db.get_session()
    async with session:
        await session.execute(
            text(
                "INSERT INTO users (id,email,username,password_hash,ai_calls_today,"
                "ai_calls_reset_at,created_at) VALUES "
                "('u1','u1@bench.test','u1-bench','hash',0,'','2026-08-01T00:00:00Z')"
            )
        )
        await session.commit()

    project, _ = await ContentProjectService(test_db).create(
        "u1",
        ContentProjectCreate(title="基准项目", idempotency_key="bench-project-2"),
    )
    project_id = project["id"]

    session = await test_db.get_session()
    async with session:
        await session.execute(text("PRAGMA foreign_keys=OFF"))
        await session.execute(
            text(
                "INSERT INTO publish_records_v2 (id,owner_user_id,project_id,"
                "locked_version_id,publish_hypothesis_id,platform,published_at,"
                "recorded_at,idempotency_key,request_hash,created_at) VALUES "
                "('rec-a','u1',:project,'ver-x','hyp-x','xiaohongshu',"
                "'2026-08-01T00:00:00Z','2026-08-01T00:00:00Z','rec-key','rec-hash',"
                "'2026-08-01T00:00:00Z')"
            ),
            {"project": project_id},
        )
        snapshot_sql = (
            "INSERT INTO performance_snapshots_v2 (id,owner_user_id,"
            "publish_record_id,project_id,captured_at,source,metrics_json,"
            "confirmed_by_user,supersedes_id,idempotency_key,request_hash,"
            "created_at) VALUES "
            "(:id,:owner,'rec-a',:project,:captured,'manual',:metrics,1,"
            ":supersedes,:key,:hash,:captured)"
        )
        await session.execute(
            text(snapshot_sql),
            {
                "id": "snap-a",
                "owner": "u1",
                "project": project_id,
                "captured": "2026-08-02T00:00:00Z",
                "metrics": json.dumps({"views": 10}),
                "supersedes": None,
                "key": "snap-a-key",
                "hash": "snap-a-hash",
            },
        )
        await session.execute(
            text(snapshot_sql),
            {
                "id": "snap-b",
                "owner": "u1",
                "project": project_id,
                "captured": "2026-08-03T00:00:00Z",
                "metrics": json.dumps({"views": 99}),
                "supersedes": "snap-a",
                "key": "snap-b-key",
                "hash": "snap-b-hash",
            },
        )
        await session.execute(text("PRAGMA foreign_keys=ON"))
        await session.commit()

        with pytest.raises(ValueError, match="was superseded"):
            await BenchmarkSampleService._historical_metrics(
                session, "u1", project_id, ["snap-a"]
            )
