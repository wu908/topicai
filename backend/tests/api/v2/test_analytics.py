"""Owner-scoped first-party analytics API contract (T-API-1..14)."""

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.utils import utc_now
from app.services import analytics as analytics_service
from app.services.account_data import EXPORT_TABLES
from app.services.analytics import EVENT_ACTION_CLICK, EVENT_OPEN, EVENT_VIEW
from config.settings import Settings, get_settings

EVENTS_URL = "/api/v2/analytics/events"
SUMMARY_URL = "/api/v2/analytics/summary"


@pytest.fixture
def analytics_on(monkeypatch):
    """Enable the ingest switch for the duration of one test (default is off)."""
    settings = get_settings()
    monkeypatch.setattr(settings, "analytics_ingest_enabled", True)
    return settings


def _key(prefix: str = "idem") -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _item(
    event: str = EVENT_VIEW,
    payload: dict | None = None,
    client_ts: str | None = None,
    idem_key: str | None = None,
    **overrides,
) -> dict:
    item = {
        "event": event,
        "payload": payload
        if payload is not None
        else {"group": "all", "count": 1},
        "client_ts": client_ts or utc_now(),
        "idem_key": idem_key or _key(),
    }
    item.update(overrides)
    return item


def _body(events: list[dict]) -> dict:
    return {"events": events}


async def _post_events(client, events: list[dict]):
    return await client.post(EVENTS_URL, json=_body(events))


async def _summary(client, params: dict) -> list[dict]:
    response = await client.get(SUMMARY_URL, params=params)
    assert response.status_code == 200, response.text
    return response.json()["data"]["items"]


async def _create_project(client, key: str = "analytics-project") -> dict:
    response = await client.post(
        "/api/v2/projects",
        json={
            "title": "Analytics project",
            "target_audience": "Knowledge creators",
            "idempotency_key": key,
        },
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["data"]


async def _insert_row(
    db,
    *,
    owner: str = "u1",
    event: str = EVENT_VIEW,
    created_at: str,
    retention: str = "2099-01-01T00:00:00.000000Z",
    payload: dict | None = None,
) -> None:
    await db.execute(
        "INSERT INTO analytics_events "
        "(id,owner_user_id,event_name,payload_json,client_ts,server_ts,"
        "retention_expires_at,idem_key,created_at) "
        "VALUES (:id,:owner,:event,:payload,:client_ts,:server_ts,:retention,"
        ":idem_key,:created_at)",
        {
            "id": str(uuid.uuid4()),
            "owner": owner,
            "event": event,
            "payload": json.dumps(payload or {"group": "all"}),
            "client_ts": created_at,
            "server_ts": created_at,
            "retention": retention,
            "idem_key": _key("row"),
            "created_at": created_at,
        },
    )


def _large_valid_json_body(size: int = 49 * 1024) -> bytes:
    item = _item()
    item["payload"] = {"group": "all", "count": 1, "pad": "x" * size}
    return json.dumps({"events": [item]}).encode("utf-8")


def _large_invalid_json_body(size: int = 49 * 1024) -> bytes:
    return b'{"events":[' + b"x" * size


async def _chunks(payload: bytes, size: int = 8192):
    for start in range(0, len(payload), size):
        yield payload[start : start + size]


# ==================== T-API-1: authentication precedes body parsing ====================


@pytest.mark.asyncio
async def test_t_api_1_unauthenticated_401_even_with_invalid_json(client_no_auth):
    response = await client_no_auth.post(
        EVENTS_URL,
        content=b"definitely-not-json",
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 401
    body = response.json()
    assert "detail" in body
    assert "code" not in body


# ==================== T-API-2: 413 and status precedence ====================


@pytest.mark.asyncio
async def test_t_api_2_oversized_body_is_413(client, analytics_on):
    valid = _large_valid_json_body()
    assert len(valid) > 48 * 1024
    response = await client.post(
        EVENTS_URL, content=valid, headers={"content-type": "application/json"}
    )
    assert response.status_code == 413, response.text
    assert response.json()["meta"]["error_code"] == "PAYLOAD_TOO_LARGE"

    invalid = _large_invalid_json_body()
    response = await client.post(
        EVENTS_URL, content=invalid, headers={"content-type": "application/json"}
    )
    assert response.status_code == 413

    # No Content-Length (chunked) must still stop at the 48 KB ceiling.
    response = await client.post(
        EVENTS_URL,
        content=_chunks(valid),
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 413, response.text


@pytest.mark.asyncio
async def test_t_api_2_oversized_body_loses_to_401_and_503(client, client_no_auth):
    oversized = _large_valid_json_body()

    unauthenticated = await client_no_auth.post(
        EVENTS_URL,
        content=oversized,
        headers={"content-type": "application/json"},
    )
    assert unauthenticated.status_code == 401

    # Same request with the switch off must be 503 (checked before size).
    disabled = await client.post(
        EVENTS_URL,
        content=oversized,
        headers={"content-type": "application/json"},
    )
    assert disabled.status_code == 503
    assert disabled.json()["meta"]["error_code"] == "ANALYTICS_DISABLED"


# ==================== T-API-3: structural errors → 422 ====================


@pytest.mark.asyncio
async def test_t_api_3_structure_count_and_owner_fields_are_422(
    client, analytics_on
):
    empty = await _post_events(client, [])
    assert empty.status_code == 422
    assert empty.json()["meta"]["error_code"] == "VALIDATION_ERROR"

    too_many = await _post_events(
        client, [_item(idem_key=_key()) for _ in range(33)]
    )
    assert too_many.status_code == 422

    owner_in_envelope = await client.post(
        EVENTS_URL, json={"events": [_item()], "owner_user_id": "u2"}
    )
    assert owner_in_envelope.status_code == 422
    assert owner_in_envelope.json()["meta"]["error_code"] == "OWNER_NOT_ALLOWED"

    owner_in_item = await _post_events(
        client, [_item(owner_user_id="u2")]
    )
    assert owner_in_item.status_code == 422
    assert owner_in_item.json()["meta"]["error_code"] == "OWNER_NOT_ALLOWED"

    unknown_item_key = await _post_events(client, [_item(at="now")])
    assert unknown_item_key.status_code == 422
    assert unknown_item_key.json()["meta"]["error_code"] == "VALIDATION_ERROR"


# ==================== T-API-4: per-item failures are rejected, not fatal ====================


@pytest.mark.asyncio
async def test_t_api_4_invalid_items_return_200_with_rejected(client, analytics_on):
    response = await _post_events(
        client,
        [
            _item(event="content_list_unknown"),
            _item(payload={"group": "all", "count": 1, "email": "a@b.co"}),
            _item(payload={"group": "bogus"}),
        ],
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["accepted"] == 0
    assert data["duplicates"] == 0
    assert data["rejected"] == [
        {"index": 0, "reason": "unknown_event"},
        {"index": 1, "reason": "payload_key_not_allowed"},
        {"index": 2, "reason": "payload_value_invalid"},
    ]


@pytest.mark.asyncio
async def test_t_api_4_item_limits_are_rejected(client, analytics_on):
    future = (datetime.now(UTC) + timedelta(minutes=10)).isoformat().replace(
        "+00:00", "Z"
    )
    response = await _post_events(
        client,
        [
            _item(idem_key="short"),
            _item(client_ts=future),
            _item(payload={"group": "all", "count": 1, "pad": "x" * 1500}),
        ],
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert [item["reason"] for item in data["rejected"]] == [
        "idem_key_invalid",
        "client_ts_invalid",
        "payload_too_large",
    ]


# ==================== T-API-5: valid batch ====================


@pytest.mark.asyncio
async def test_t_api_5_valid_batch_accepted(client, analytics_on, test_db):
    project = await _create_project(client)
    response = await _post_events(
        client,
        [
            _item(payload={"group": "all", "count": 12}),
            _item(
                event=EVENT_OPEN,
                payload={"project_id": project["id"], "group": "wanted", "via": "title"},
            ),
            _item(
                event=EVENT_ACTION_CLICK,
                payload={
                    "project_id": project["id"],
                    "group": "wanted",
                    "action_key": "handle",
                    "next_action": None,
                },
            ),
        ],
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data == {"accepted": 3, "duplicates": 0, "rejected": []}
    stored = await test_db.fetch_one(
        "SELECT COUNT(*) AS count FROM analytics_events WHERE owner_user_id='u1'"
    )
    assert stored["count"] == 3


# ==================== T-API-6: summary counts equal inserted rows ====================


@pytest.mark.asyncio
async def test_t_api_6_summary_counts_same_utc_day(client, analytics_on, test_db):
    response = await _post_events(
        client,
        [
            _item(),
            _item(),
        ],
    )
    assert response.status_code == 200, response.text
    stored = await test_db.fetch_one(
        "SELECT substr(created_at,1,10) AS day FROM analytics_events "
        "WHERE owner_user_id='u1' LIMIT 1"
    )
    day = stored["day"]

    items = await _summary(client, {"from": day, "to": day, "event": EVENT_VIEW})
    assert items == [{"event": EVENT_VIEW, "date": day, "count": 2}]


# ==================== T-API-7: UTC day window and owner isolation ====================


@pytest.mark.asyncio
async def test_t_api_7_summary_utc_day_window_and_owner_isolation(
    client, test_db
):
    await _insert_row(test_db, created_at="2026-10-01T10:00:00.000000Z")
    await _insert_row(
        test_db,
        event=EVENT_OPEN,
        created_at="2026-10-01T23:59:59.000000Z",
        payload={"project_id": "p1", "via": "title"},
    )
    await _insert_row(test_db, created_at="2026-10-02T00:00:00.000000Z")
    await _insert_row(
        test_db, owner="u2", created_at="2026-10-01T12:00:00.000000Z"
    )

    day_one = {
        (item["event"], item["date"]): item["count"]
        for item in await _summary(
            client, {"from": "2026-10-01", "to": "2026-10-01"}
        )
    }
    assert day_one == {
        (EVENT_VIEW, "2026-10-01"): 1,
        (EVENT_OPEN, "2026-10-01"): 1,
    }

    both_days = {
        (item["event"], item["date"]): item["count"]
        for item in await _summary(
            client, {"from": "2026-10-01", "to": "2026-10-02"}
        )
    }
    assert both_days[(EVENT_VIEW, "2026-10-01")] == 1  # u2 row is excluded
    assert both_days[(EVENT_VIEW, "2026-10-02")] == 1

    filtered = await _summary(
        client, {"from": "2026-10-01", "to": "2026-10-02", "event": EVENT_OPEN}
    )
    assert filtered == [
        {"event": EVENT_OPEN, "date": "2026-10-01", "count": 1}
    ]

    # 90 inclusive days pass; 91 fail.
    boundary = await client.get(
        SUMMARY_URL, params={"from": "2026-10-01", "to": "2026-12-29"}
    )
    assert boundary.status_code == 200, boundary.text
    over = await client.get(
        SUMMARY_URL, params={"from": "2026-10-01", "to": "2026-12-30"}
    )
    assert over.status_code == 422
    inverted = await client.get(
        SUMMARY_URL, params={"from": "2026-10-02", "to": "2026-10-01"}
    )
    assert inverted.status_code == 422
    bad_event = await client.get(
        SUMMARY_URL,
        params={"from": "2026-10-01", "to": "2026-10-01", "event": "unknown"},
    )
    assert bad_event.status_code == 422


# ==================== T-API-8: expired retention rows are filtered ====================


@pytest.mark.asyncio
async def test_t_api_8_expired_rows_are_not_returned(client, test_db):
    await _insert_row(
        test_db,
        created_at="2026-10-05T10:00:00.000000Z",
        retention="2020-01-01T00:00:00.000000Z",
    )
    await _insert_row(
        test_db,
        created_at="2026-10-05T11:00:00.000000Z",
        retention="2099-01-01T00:00:00.000000Z",
    )

    items = await _summary(client, {"from": "2026-10-05", "to": "2026-10-05"})
    assert items == [{"event": EVENT_VIEW, "date": "2026-10-05", "count": 1}]


# ==================== T-API-9: export covers the new table ====================


@pytest.mark.asyncio
async def test_t_api_9_export_includes_analytics_events(client, analytics_on):
    assert ("analytics_events", "owner_user_id") in EXPORT_TABLES
    response = await _post_events(client, [_item(payload={"group": "all", "count": 3})])
    assert response.status_code == 200, response.text

    requested = (
        await client.post(
            "/api/v2/account/data-export:request",
            json={"idempotency_key": "analytics-export-request"},
        )
    ).json()["data"]
    decided = await client.post(
        f"/api/v2/human-gates/{requested['id']}:decide",
        json={
            "decision": "confirm",
            "decision_payload": {"owner_confirmed": True},
            "expected_gate_version": requested["version"],
            "idempotency_key": "analytics-export-decide",
        },
    )
    assert decided.status_code in (200, 201), decided.text

    exported = await client.get(
        "/api/v2/account/data-export", params={"gate_id": requested["id"]}
    )
    assert exported.status_code == 200, exported.text
    rows = exported.json()["data"]["entities"]["analytics_events"]
    assert len(rows) == 1
    assert rows[0]["owner_user_id"] == "u1"
    assert rows[0]["event_name"] == EVENT_VIEW
    assert rows[0]["payload"] == {"group": "all", "count": 3}


# ==================== T-API-10: switch off → 503, quota → 429 ====================


@pytest.mark.asyncio
async def test_t_api_10_switch_off_503_before_body_parsing(client):
    valid = await _post_events(client, [_item()])
    assert valid.status_code == 503
    assert valid.json()["meta"]["error_code"] == "ANALYTICS_DISABLED"

    invalid = await client.post(
        EVENTS_URL,
        content=b"not-json",
        headers={"content-type": "application/json"},
    )
    assert invalid.status_code == 503

    oversized = await client.post(
        EVENTS_URL,
        content=_large_valid_json_body(),
        headers={"content-type": "application/json"},
    )
    assert oversized.status_code == 503


@pytest.mark.asyncio
async def test_t_api_10_quota_exceeded_is_429_without_rejected(
    client, analytics_on, test_db, monkeypatch
):
    monkeypatch.setattr(analytics_service, "DAILY_EVENT_QUOTA", 2)
    first = await _post_events(client, [_item(), _item()])
    assert first.status_code == 200
    assert first.json()["data"]["accepted"] == 2

    exceeded = await _post_events(client, [_item()])
    assert exceeded.status_code == 429, exceeded.text
    body = exceeded.json()
    assert body["meta"]["error_code"] == "ANALYTICS_QUOTA_EXCEEDED"
    assert body["data"] is None

    stored = await test_db.fetch_one(
        "SELECT COUNT(*) AS count FROM analytics_events WHERE owner_user_id='u1'"
    )
    assert stored["count"] == 2


# ==================== T-API-11: clean environment defaults to disabled ====================


def test_t_api_11_default_switch_is_false(monkeypatch):
    monkeypatch.delenv("ANALYTICS_INGEST_ENABLED", raising=False)
    assert Settings().analytics_ingest_enabled is False
    assert get_settings().analytics_ingest_enabled is False


# ==================== T-API-12: idempotency within and across batches ====================


@pytest.mark.asyncio
async def test_t_api_12_idempotency_same_and_cross_batch(
    client, analytics_on, test_db
):
    key = "same-batch-key-001"
    same_batch = await _post_events(
        client, [_item(idem_key=key), _item(idem_key=key)]
    )
    assert same_batch.status_code == 200, same_batch.text
    assert same_batch.json()["data"] == {
        "accepted": 1,
        "duplicates": 1,
        "rejected": [],
    }

    cross_batch = await _post_events(client, [_item(idem_key=key)])
    assert cross_batch.json()["data"] == {
        "accepted": 0,
        "duplicates": 1,
        "rejected": [],
    }

    fresh = await _post_events(client, [_item(idem_key="fresh-key-0001")])
    assert fresh.json()["data"] == {
        "accepted": 1,
        "duplicates": 0,
        "rejected": [],
    }

    stored = await test_db.fetch_one(
        "SELECT COUNT(*) AS count FROM analytics_events WHERE owner_user_id='u1'"
    )
    assert stored["count"] == 2


# ==================== T-API-13: cross-owner project is not disclosed ====================


@pytest.mark.asyncio
async def test_t_api_13_cross_owner_project_rejected(
    client, client_as_u2, analytics_on, test_db
):
    foreign_response = await client_as_u2.post(
        "/api/v2/projects",
        json={
            "title": "Foreign project",
            "target_audience": "Other creators",
            "idempotency_key": "analytics-foreign-project",
        },
    )
    foreign_project = foreign_response.json()["data"]

    response = await _post_events(
        client,
        [
            _item(
                event=EVENT_OPEN,
                payload={"project_id": foreign_project["id"], "via": "title"},
            ),
            _item(
                event=EVENT_ACTION_CLICK,
                payload={
                    "project_id": foreign_project["id"],
                    "action_key": "handle",
                },
            ),
        ],
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["accepted"] == 0
    assert [item["reason"] for item in data["rejected"]] == [
        "project_not_owned",
        "project_not_owned",
    ]
    stored = await test_db.fetch_one(
        "SELECT COUNT(*) AS count FROM analytics_events WHERE owner_user_id='u1'"
    )
    assert stored["count"] == 0


# ==================== T-API-14: action_key stable forms ====================


@pytest.mark.asyncio
async def test_t_api_14_action_key_stable_forms(client, analytics_on):
    project = await _create_project(client, key="analytics-action-key-project")
    valid_keys = [
        "view",
        "handle",
        "orchestrated:create_project",
        "run_blind_review",
    ]
    accepted = await _post_events(
        client,
        [
            _item(
                event=EVENT_ACTION_CLICK,
                payload={
                    "project_id": project["id"],
                    "group": "all",
                    "action_key": key,
                },
            )
            for key in valid_keys
        ],
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["data"] == {
        "accepted": 4,
        "duplicates": 0,
        "rejected": [],
    }

    invalid_keys = [
        "view ",
        "handle_click",
        "orchestrated:not_a_real_action",
        "run_blind_review_v2",
        "继续",
    ]
    rejected = await _post_events(
        client,
        [
            _item(
                event=EVENT_ACTION_CLICK,
                payload={
                    "project_id": project["id"],
                    "action_key": key,
                },
            )
            for key in invalid_keys
        ],
    )
    assert rejected.status_code == 200, rejected.text
    data = rejected.json()["data"]
    assert data["accepted"] == 0
    assert [item["reason"] for item in data["rejected"]] == [
        "payload_value_invalid"
    ] * len(invalid_keys)
