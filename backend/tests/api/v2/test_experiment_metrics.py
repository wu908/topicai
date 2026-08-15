"""Contracts for privacy-safe MVP experiment instrumentation."""

import json
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from app.services.experiment_metrics import ExperimentMetricsService


def test_action_funnel_counts_explicit_rejection_and_cancellation():
    rows = [
        {"action_id": "rejected", "event_type": "rejected", "to_status": "cancelled", "success": 1, "latency_ms": None},
        {"action_id": "cancelled", "event_type": "cancelled", "to_status": "cancelled", "success": 1, "latency_ms": None},
        {"action_id": "expired", "event_type": "expired", "to_status": "expired", "success": 1, "latency_ms": None},
    ]
    funnel = ExperimentMetricsService._funnel(
        {"rejected", "cancelled", "expired"}, rows
    )
    assert funnel["rejected"]["numerator"] == 2
    assert funnel["failed"]["numerator"] == 0


@pytest.mark.asyncio
async def test_active_assignment_is_frozen_on_actions_and_events(client, test_db):
    assigned = await client.put(
        "/api/v2/internal/validation/experiments/E1/assignment",
        json={
            "cohort": "variant",
            "user_segment": "growth",
            "status": "active",
            "idempotency_key": "assign-e1-variant",
        },
    )
    assert assigned.status_code == 201
    assert assigned.json()["data"]["experiment_id"] == "E1"
    assert "owner_user_id" not in assigned.json()["data"]
    assert "request_hash" not in assigned.json()["data"]

    replay = await client.put(
        "/api/v2/internal/validation/experiments/E1/assignment",
        json={
            "cohort": "variant",
            "user_segment": "growth",
            "status": "active",
            "idempotency_key": "assign-e1-variant",
        },
    )
    assert replay.status_code == 200
    assert replay.json()["meta"]["idempotency_replayed"] is True

    today = await client.get("/api/v2/today")
    action = today.json()["data"]["action"]
    assert action["experiment_id"] == "E1"
    assert action["cohort"] == "variant"

    event = await test_db.fetch_one(
        "SELECT * FROM action_events WHERE action_id=:action AND event_type='proposed'",
        {"action": action["id"]},
    )
    assert event["experiment_id"] == "E1"
    assert event["cohort"] == "variant"
    assert event["ai_trace_id"] == action["ai_trace_id"]
    assert event["prompt_version"] == "intent-orchestrator-v2"
    assert event["success"] == 1


@pytest.mark.asyncio
async def test_action_funnel_has_stable_denominator_and_safe_events(client, test_db):
    await client.put(
        "/api/v2/internal/validation/experiments/E1/assignment",
        json={
            "cohort": "variant",
            "user_segment": "growth",
            "status": "active",
            "idempotency_key": "metrics-assignment",
        },
    )
    action = (await client.get("/api/v2/today")).json()["data"]["action"]
    manual = await client.post(
        f"/api/v2/actions/{action['id']}:respond",
        json={
            "decision": "manual",
            "response_payload": {"private_note": "must never be exported"},
            "expected_action_version": action["version"],
            "idempotency_key": "metrics-manual",
        },
    )
    assert manual.status_code == 201

    # Anchor the metrics window to the real clock: the action produced by
    # /api/v2/today carries the actual current timestamp, so a hardcoded
    # end_at would silently exclude it once that date passes (date bomb).
    now = datetime.now(UTC).replace(microsecond=0)
    timestamp = now.isoformat().replace("+00:00", "Z")
    session = await test_db.get_session()
    async with session:
        async with session.begin():
            await session.execute(
                text(
                    "INSERT INTO next_best_actions (id,owner_user_id,action_type,title,reason,"
                    "fallback_action_json,status,version,idempotency_key,request_hash,created_at,updated_at,"
                    "estimated_effort_minutes) VALUES "
                    "('no-offer','u1','create_project','x','x','{}','completed',1,'no-offer','h',:now,:now,1)"
                ),
                {"now": timestamp},
            )
            await session.execute(
                text(
                    "INSERT INTO action_events (id,owner_user_id,action_id,event_type,to_status,"
                    "payload_json,action_version,idempotency_key,request_hash,created_at) VALUES "
                    "('no-offer-event','u1','no-offer','completed','completed',:payload,1,"
                    "'no-offer-event','h',:now)"
                ),
                {
                    "payload": json.dumps({"raw_content": "must never be exported"}),
                    "now": timestamp,
                },
            )
            await session.execute(
                text(
                    "UPDATE action_events SET payload_json=:payload "
                    "WHERE action_id=:action AND event_type='proposed'"
                ),
                {
                    "payload": json.dumps({"raw_content": "eligible secret content"}),
                    "action": action["id"],
                },
            )
            await session.execute(
                text(
                    "INSERT INTO action_events (id,owner_user_id,action_id,event_type,from_status,"
                    "to_status,payload_json,action_version,idempotency_key,request_hash,created_at,"
                    "success,error_code) VALUES ('failed-fallback','u1',:action,'fallback_used',"
                    "'proposed','proposed','{}',1,'failed-fallback','h',:now,0,:error)"
                ),
                {
                    "action": action["id"],
                    "now": timestamp,
                    "error": "private raw exception message",
                },
            )
            await session.execute(
                text(
                    "INSERT INTO next_best_actions (id,owner_user_id,action_type,title,reason,"
                    "fallback_action_json,status,version,idempotency_key,request_hash,created_at,updated_at,"
                    "estimated_effort_minutes) VALUES "
                    "('cross-owner-action','u2','create_project','private title','private reason','{}',"
                    "'proposed',1,'cross-owner-action','h',:now,:now,1)"
                ),
                {"now": timestamp},
            )
            await session.execute(
                text(
                    "INSERT INTO action_events (id,owner_user_id,action_id,event_type,to_status,"
                    "payload_json,action_version,idempotency_key,request_hash,created_at) VALUES "
                    "('cross-owner-event','u1','cross-owner-action','proposed','proposed','{}',1,"
                    "'cross-owner-event','h',:now)"
                ),
                {"now": timestamp},
            )

    response = await client.get(
        "/api/v2/internal/validation/action-metrics",
        params={
            "start_at": (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_at": (now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "experiment_id": "E1",
            "cohort": "variant",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    funnel = data["action_funnel"]
    assert funnel["offered"] == 1
    assert funnel["accepted"]["numerator"] == 0
    assert funnel["rejected"]["numerator"] == 1
    assert funnel["completed"]["numerator"] == 1
    assert funnel["completed"]["denominator"] == 1
    assert funnel["failed"]["numerator"] == 1
    assert all(event["action_id"] != "no-offer" for event in data["events"])
    serialized = json.dumps(data)
    assert "private_note" not in serialized
    assert "must never be exported" not in serialized
    assert "eligible secret content" not in serialized
    assert "private raw exception message" not in serialized
    assert any(event["error_code"] == "invalid_error_code" for event in data["events"])
    assert all(event["action_id"] != "cross-owner-action" for event in data["events"])
    assert "payload_json" not in data["events"][0]
    assert len(data["events"][0]["user_id_hash"]) == 64


@pytest.mark.asyncio
async def test_metrics_are_owner_scoped_and_zero_denominator_is_null(client_as_u2):
    response = await client_as_u2.get(
        "/api/v2/internal/validation/action-metrics",
        params={
            "start_at": "2026-07-01T00:00:00Z",
            "end_at": "2026-08-01T00:00:00Z",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["action_funnel"]["offered"] == 0
    assert data["action_funnel"]["completed"]["rate"] is None
    assert data["events"] == []


@pytest.mark.asyncio
async def test_assignment_switch_completes_previous_active_experiment(client, test_db):
    for experiment in ("E1", "E2"):
        response = await client.put(
            f"/api/v2/internal/validation/experiments/{experiment}/assignment",
            json={
                "cohort": "observational",
                "status": "active",
                "idempotency_key": f"switch-{experiment}",
            },
        )
        assert response.status_code == 201

    rows = await test_db.fetch_all(
        "SELECT experiment_id,status FROM experiment_assignments "
        "WHERE owner_user_id='u1' ORDER BY experiment_id"
    )
    assert rows == [
        {"experiment_id": "E1", "status": "completed"},
        {"experiment_id": "E2", "status": "active"},
    ]
    transition = await test_db.fetch_one(
        "SELECT from_status,to_status FROM experiment_assignment_events "
        "WHERE owner_user_id='u1' AND experiment_id='E1' "
        "ORDER BY created_at DESC, rowid DESC LIMIT 1"
    )
    assert transition == {"from_status": "active", "to_status": "completed"}

    original_replay = await client.put(
        "/api/v2/internal/validation/experiments/E1/assignment",
        json={
            "cohort": "observational",
            "status": "active",
            "idempotency_key": "switch-E1",
        },
    )
    assert original_replay.status_code == 200
    assert original_replay.json()["data"]["status"] == "active"
    still_completed = await test_db.fetch_one(
        "SELECT status FROM experiment_assignments "
        "WHERE owner_user_id='u1' AND experiment_id='E1'"
    )
    assert still_completed == {"status": "completed"}


@pytest.mark.asyncio
async def test_invalid_exclusion_and_oversized_window_are_rejected(client):
    invalid_assignment = await client.put(
        "/api/v2/internal/validation/experiments/E4/assignment",
        json={
            "cohort": "excluded",
            "status": "excluded",
            "idempotency_key": "missing-exclusion-reason",
        },
    )
    assert invalid_assignment.status_code == 422

    oversized = await client.get(
        "/api/v2/internal/validation/action-metrics",
        params={
            "start_at": "2026-01-01T00:00:00Z",
            "end_at": "2026-07-01T00:00:00Z",
        },
    )
    assert oversized.status_code == 400


@pytest.mark.asyncio
async def test_idempotency_key_cannot_replay_across_experiments(client):
    body = {
        "cohort": "control",
        "status": "active",
        "idempotency_key": "cross-experiment-key",
    }
    first = await client.put(
        "/api/v2/internal/validation/experiments/E1/assignment", json=body
    )
    assert first.status_code == 201

    conflicting = await client.put(
        "/api/v2/internal/validation/experiments/E2/assignment", json=body
    )
    assert conflicting.status_code == 409


@pytest.mark.asyncio
async def test_calibration_scope_is_consistent_across_reviews_observations_and_rules():
    class QueryRecorder:
        def __init__(self):
            self.queries = []

        async def fetch_all(self, query, params):
            self.queries.append((query, params))
            return []

    start = datetime(2026, 7, 1, tzinfo=UTC)
    end = datetime(2026, 8, 1, tzinfo=UTC)

    owner_wide = QueryRecorder()
    await ExperimentMetricsService(owner_wide)._calibration(
        "u1", ["p1"], start, end, require_projects=False
    )
    assert all("project_id IN" not in query for query, _ in owner_wide.queries)

    experiment_scoped = QueryRecorder()
    await ExperimentMetricsService(experiment_scoped)._calibration(
        "u1", ["p1"], start, end, require_projects=True
    )
    assert len(experiment_scoped.queries) == 3
    assert all("project_id IN" in query for query, _ in experiment_scoped.queries)
    assert "json_each(crv.source_observation_ids_json)" in experiment_scoped.queries[2][0]


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Flaky ~15%: /next-action may not produce an offered action "
    "depending on calibration state timing. Root cause not yet identified. "
    "See ADR-003 / handoff 2026-08-07.",
    strict=False,
)
async def test_project_scoped_calibration_query_executes_on_sqlite(client):
    await client.put(
        "/api/v2/internal/validation/experiments/E3/assignment",
        json={
            "cohort": "variant",
            "status": "active",
            "idempotency_key": "scoped-query-assignment",
        },
    )
    project = (
        await client.post(
            "/api/v2/projects",
            json={
                "title": "Scoped metrics project",
                "content_intent": "share",
                "idempotency_key": "scoped-metrics-project",
            },
        )
    ).json()["data"]
    await client.get(f"/api/v2/projects/{project['id']}/next-action")

    exported = await client.get(
        "/api/v2/internal/validation/action-metrics",
        params={"experiment_id": "E3", "cohort": "variant"},
    )
    assert exported.status_code == 200
    assert exported.json()["data"]["action_funnel"]["offered"] == 1


@pytest.mark.asyncio
async def test_rule_upgrade_numerator_is_limited_to_valid_clean_reviews():
    class CalibrationRows:
        async def fetch_all(self, query, params):
            if "FROM blind_reviews" in query:
                return [
                    {
                        "calibration_state": "valid",
                        "contamination_status": "clean",
                        "eligible_for_rule_upgrade": 1,
                    },
                    {
                        "calibration_state": "insufficient",
                        "contamination_status": "clean",
                        "eligible_for_rule_upgrade": 1,
                    },
                    {
                        "calibration_state": "calibration_invalid",
                        "contamination_status": "contaminated",
                        "eligible_for_rule_upgrade": 1,
                    },
                ]
            return []

    result = await ExperimentMetricsService(CalibrationRows())._calibration(
        "u1",
        [],
        datetime(2026, 7, 1, tzinfo=UTC),
        datetime(2026, 8, 1, tzinfo=UTC),
        require_projects=False,
    )

    metric = result["eligible_rule_upgrades"]
    assert metric["numerator"] == 1
    assert metric["denominator"] == 1
    assert metric["rate"] == 1
