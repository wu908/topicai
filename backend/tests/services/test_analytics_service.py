"""Service-level contracts for first-party analytics (PILOT-12).

Covers the helpers that were previously only exercised indirectly through the
API tests, plus the T8 retention purge contract (dry-run by default).
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.services.analytics import (
    AnalyticsService,
    _is_stable_action_key,
    _iso,
    _parse_client_ts,
    _payload_bytes,
)

USER_ID = "analytics-service-user"
EVENT = "content_list_view"


async def _insert_user(db, user_id: str = USER_ID) -> None:
    await db.execute(
        "INSERT INTO users (id,email,username,password_hash,ai_calls_today,"
        "ai_calls_reset_at,created_at) VALUES "
        "(:id,:email,:uname,'hash',0,'','2026-08-30T00:00:00Z')",
        {"id": user_id, "email": f"{user_id}@example.com", "uname": f"U{user_id}"},
    )


async def _insert_event(
    db,
    *,
    idem_key: str,
    retention_expires_at: datetime,
    owner: str = USER_ID,
) -> None:
    moment = _iso(datetime(2026, 10, 1, tzinfo=UTC))
    await db.execute(
        "INSERT INTO analytics_events (id,owner_user_id,event_name,payload_json,"
        "client_ts,server_ts,retention_expires_at,idem_key,created_at) VALUES "
        "(:id,:owner,:event,'{\"group\":\"all\"}',:client_ts,:server_ts,"
        ":retention,:idem,:created_at)",
        {
            "id": f"evt-{idem_key}",
            "owner": owner,
            "event": EVENT,
            "client_ts": moment,
            "server_ts": moment,
            "retention": _iso(retention_expires_at),
            "idem": idem_key,
            "created_at": moment,
        },
    )


async def _idem_keys(db) -> list[str]:
    rows = await db.fetch_all(
        "SELECT idem_key FROM analytics_events ORDER BY idem_key"
    )
    return [row["idem_key"] for row in rows]


# ==================== Helpers ====================


def test_payload_bytes_counts_utf8_bytes() -> None:
    # {"k":"..."} adds 8 ASCII bytes around the value.
    assert _payload_bytes({"k": "x" * 1016}) == 1024
    assert _payload_bytes({"k": "x" * 1017}) == 1025
    # CJK characters are three UTF-8 bytes each.
    assert _payload_bytes({"k": "中" * 338}) == 1022
    assert _payload_bytes({"k": "中" * 339}) == 1025


def test_parse_client_ts_variants() -> None:
    expected = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)
    assert _parse_client_ts("2026-10-30T12:00:00Z") == expected
    assert _parse_client_ts("2026-10-30T12:00:00+00:00") == expected
    assert _parse_client_ts("2026-10-30T20:00:00+08:00") == expected
    # Naive timestamps are treated as UTC (documented in the service).
    assert _parse_client_ts("2026-10-30T12:00:00") == expected
    assert _parse_client_ts("") is None
    assert _parse_client_ts("not-a-timestamp") is None
    assert _parse_client_ts(None) is None  # type: ignore[arg-type]


def test_is_stable_action_key_allows_contract_keys() -> None:
    assert _is_stable_action_key("view")
    assert _is_stable_action_key("handle")
    assert _is_stable_action_key("create_version")  # NextAction value
    assert _is_stable_action_key("orchestrated:create_project")  # ActionType
    # Anything else must be rejected (a frontend drift would land here).
    assert not _is_stable_action_key("orchestrated:not_an_action")
    assert not _is_stable_action_key("create_project")  # ActionType needs prefix
    assert not _is_stable_action_key("继续")
    assert not _is_stable_action_key("")


# ==================== Retention purge (T8) ====================


async def test_purge_expired_dry_run_counts_without_deleting(test_db) -> None:
    await _insert_user(test_db)
    now = datetime(2026, 10, 31, 12, 0, tzinfo=UTC)
    await _insert_event(
        test_db, idem_key="expired-1", retention_expires_at=now - timedelta(days=1)
    )
    await _insert_event(
        test_db, idem_key="future-1", retention_expires_at=now + timedelta(days=1)
    )
    service = AnalyticsService(test_db)

    assert await service.purge_expired(now=now) == 1
    assert await _idem_keys(test_db) == ["expired-1", "future-1"]


async def test_purge_expired_is_inclusive_and_idempotent(test_db) -> None:
    await _insert_user(test_db)
    now = datetime(2026, 10, 31, 12, 0, tzinfo=UTC)
    await _insert_event(
        test_db, idem_key="boundary", retention_expires_at=now
    )
    await _insert_event(
        test_db, idem_key="future", retention_expires_at=now + timedelta(seconds=1)
    )
    service = AnalyticsService(test_db)

    assert await service.purge_expired(dry_run=False, now=now) == 1
    assert await _idem_keys(test_db) == ["future"]
    assert await service.purge_expired(dry_run=False, now=now) == 0


async def test_purge_expired_naive_now_is_treated_as_utc(test_db) -> None:
    await _insert_user(test_db)
    naive_now = datetime(2026, 10, 31, 12, 0)
    await _insert_event(
        test_db,
        idem_key="expired",
        retention_expires_at=datetime(2026, 10, 31, 11, 0, tzinfo=UTC),
    )
    await _insert_event(
        test_db,
        idem_key="future",
        retention_expires_at=datetime(2026, 10, 31, 13, 0, tzinfo=UTC),
    )
    service = AnalyticsService(test_db)

    assert await service.purge_expired(now=naive_now) == 1


@pytest.mark.parametrize("dry_run", [True, False])
async def test_purge_expired_empty_table_returns_zero(test_db, dry_run: bool) -> None:
    await _insert_user(test_db)
    service = AnalyticsService(test_db)
    assert await service.purge_expired(dry_run=dry_run) == 0
