"""Quota atomicity (PILOT-15): BEGIN IMMEDIATE makes COUNT+INSERT atomic.

These tests use a *file* database and a second connection holding a write lock;
``:memory:`` with a single connection cannot expose the check-then-act race.
"""

import asyncio
from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import OperationalError

from app.core.database import Database
from app.core.exceptions import AppException
from app.models.v2.analytics import AnalyticsEventIn
from app.services import analytics as analytics_module
from app.services.analytics import EVENT_VIEW, AnalyticsService, _iso

USER_ID = "quota-atomic-user"


def _item(n: int) -> AnalyticsEventIn:
    return AnalyticsEventIn(
        event=EVENT_VIEW,
        payload={"group": "all", "count": 1},
        client_ts=_iso(datetime.now(UTC)),
        idem_key=f"quota-idem-{n:04d}",
    )


async def _open_db(tmp_path) -> Database:
    db = Database(f"sqlite+aiosqlite:///{tmp_path.as_posix()}/quota.db")
    await db.init_db()
    await db.execute(
        "INSERT INTO users (id,email,username,password_hash,ai_calls_today,"
        "ai_calls_reset_at,created_at) VALUES "
        "(:id,:email,:uname,'hash',0,'','2026-08-30T00:00:00Z')",
        {"id": USER_ID, "email": "q@example.com", "uname": "Q"},
    )
    return db


async def _count(db: Database) -> int:
    row = await db.fetch_one("SELECT COUNT(*) AS count FROM analytics_events")
    return int(row["count"]) if row else 0


async def _insert_uncommitted_row(conn) -> None:
    now = _iso(datetime.now(UTC))
    await conn.exec_driver_sql(
        "INSERT INTO analytics_events (id,owner_user_id,event_name,payload_json,"
        "client_ts,server_ts,retention_expires_at,idem_key,created_at) VALUES "
        "(?,?,?,?,?,?,?,?,?)",
        (
            "held-row",
            USER_ID,
            EVENT_VIEW,
            '{"group":"all"}',
            now,
            now,
            now,
            "held-idem",
            now,
        ),
    )


async def test_quota_boundary_and_no_write_on_exceed(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(analytics_module, "DAILY_EVENT_QUOTA", 2)
    db = await _open_db(tmp_path)
    try:
        service = AnalyticsService(db)
        ok = await service.ingest(USER_ID, [_item(1), _item(2)])
        assert ok["accepted"] == 2
        with pytest.raises(AppException) as exc:
            await service.ingest(USER_ID, [_item(3)])
        assert exc.value.status_code == 429
        assert await _count(db) == 2
    finally:
        await db.close()


@pytest.mark.parametrize("_run", range(10))
async def test_quota_check_is_atomic_under_held_write_lock(
    tmp_path, monkeypatch, _run: int
) -> None:
    """Old code: B's SELECT sees 0 uncommitted rows -> both insert (final=2).

    New code: B blocks on BEGIN IMMEDIATE; after A commits it sees 1 row and
    rejects with 429 (final=1).
    """
    monkeypatch.setattr(analytics_module, "DAILY_EVENT_QUOTA", 1)
    db = await _open_db(tmp_path)
    conn = None
    try:
        conn = await db.engine.connect()
        await conn.exec_driver_sql("BEGIN IMMEDIATE")
        await _insert_uncommitted_row(conn)

        task = asyncio.create_task(AnalyticsService(db).ingest(USER_ID, [_item(1)]))
        await asyncio.sleep(0.2)  # let B reach BEGIN IMMEDIATE (blocked)
        assert not task.done()
        await conn.commit()  # A commits; B must now see the row

        with pytest.raises(AppException) as exc:
            await task
        assert exc.value.status_code == 429
        assert await _count(db) == 1
    finally:
        if conn is not None:
            await conn.close()
        await db.close()


@pytest.mark.slow
async def test_lock_timeout_surfaces_operational_error(tmp_path) -> None:
    """Lock held past busy_timeout: service raises OperationalError (-> 500)."""
    db = await _open_db(tmp_path)
    conn = None
    try:
        conn = await db.engine.connect()
        await conn.exec_driver_sql("BEGIN IMMEDIATE")
        await _insert_uncommitted_row(conn)
        with pytest.raises(OperationalError, match="database is locked"):
            await AnalyticsService(db).ingest(USER_ID, [_item(2)])
    finally:
        if conn is not None:
            await conn.rollback()
            await conn.close()
        await db.close()
