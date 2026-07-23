"""Owner data rights require explicit, owner-scoped HumanGates."""

import asyncio

import pytest

from app.services.account_data import EXPORT_TABLES


async def _decide(client, gate: dict, decision: str, key: str):
    return await client.post(
        f"/api/v2/human-gates/{gate['id']}:decide",
        json={
            "decision": decision,
            "decision_payload": {"owner_confirmed": decision == "confirm"},
            "expected_gate_version": gate["version"],
            "idempotency_key": key,
        },
    )


@pytest.mark.asyncio
async def test_owner_export_requires_privacy_gate_and_excludes_other_owner(
    client, client_as_u2
):
    own_project = (
        await client.post(
            "/api/v2/projects",
            json={
                "title": "Owner export project",
                "target_audience": "Knowledge creators",
                "idempotency_key": "owner-export-project",
            },
        )
    ).json()["data"]
    other_project = (
        await client_as_u2.post(
            "/api/v2/projects",
            json={
                "title": "Other owner project",
                "target_audience": "Other creators",
                "idempotency_key": "other-export-project",
            },
        )
    ).json()["data"]

    requested = await client.post(
        "/api/v2/account/data-export:request",
        json={"idempotency_key": "privacy-export-request"},
    )
    assert requested.status_code == 201
    gate = requested.json()["data"]
    assert gate["gate_type"] == "privacy"
    assert gate["project_id"] is None
    assert gate["action_id"] is None

    blocked = await client.get(
        "/api/v2/account/data-export", params={"gate_id": gate["id"]}
    )
    assert blocked.status_code == 400
    foreign_decision = await _decide(
        client_as_u2, gate, "confirm", "foreign-privacy-decision"
    )
    assert foreign_decision.status_code == 404

    confirmed = await _decide(client, gate, "confirm", "privacy-export-decision")
    assert confirmed.status_code == 201
    exported = await client.get(
        "/api/v2/account/data-export", params={"gate_id": gate["id"]}
    )
    assert exported.status_code == 200
    data = exported.json()["data"]
    assert "password_hash" not in data["owner"]
    assert data["owner"]["ai_calls_today"] == 0
    assert "ai_calls_reset_at" in data["owner"]
    exported_project_ids = {
        item["id"] for item in data["entities"]["content_projects"]
    }
    assert own_project["id"] in exported_project_ids
    assert other_project["id"] not in exported_project_ids
    assert set(data["entities"]) == {table for table, _ in EXPORT_TABLES} | {
        "experiments"
    }
    assert data["content_genomes"][0]["project_id"] == own_project["id"]


@pytest.mark.asyncio
async def test_account_gate_request_is_concurrent_and_idempotent(client):
    responses = await asyncio.gather(
        *(
            client.post(
                "/api/v2/account/data-export:request",
                json={"idempotency_key": "concurrent-privacy-request"},
            )
            for _ in range(4)
        )
    )

    assert {response.status_code for response in responses} == {200, 201}
    gates = [response.json()["data"] for response in responses]
    assert len({gate["id"] for gate in gates}) == 1
    assert all(gate["gate_type"] == "privacy" for gate in gates)

    gate = gates[0]
    decisions = await asyncio.gather(
        *(
            _decide(client, gate, "confirm", "concurrent-privacy-decision")
            for _ in range(4)
        )
    )
    assert {response.status_code for response in decisions} == {200, 201}
    assert all(response.json()["data"]["gate"]["status"] == "confirmed" for response in decisions)


@pytest.mark.asyncio
async def test_account_deletion_requires_confirmed_gate_and_removes_every_owned_entity(
    client, client_as_u2, test_db
):
    own_project = (
        await client.post(
            "/api/v2/projects",
            json={
                "title": "Delete my project",
                "target_audience": "Knowledge creators",
                "idempotency_key": "delete-owner-project",
            },
        )
    ).json()["data"]
    other_project = (
        await client_as_u2.post(
            "/api/v2/projects",
            json={
                "title": "Keep other project",
                "target_audience": "Knowledge creators",
                "idempotency_key": "keep-other-project",
            },
        )
    ).json()["data"]

    rejected_gate = (
        await client.post(
            "/api/v2/account/deletion:request",
            json={"idempotency_key": "delete-request-rejected"},
        )
    ).json()["data"]
    await _decide(client, rejected_gate, "reject", "delete-rejected")
    blocked = await client.delete(
        "/api/v2/account", params={"gate_id": rejected_gate["id"]}
    )
    assert blocked.status_code == 400

    gate = (
        await client.post(
            "/api/v2/account/deletion:request",
            json={"idempotency_key": "delete-request-confirmed"},
        )
    ).json()["data"]
    assert gate["gate_type"] == "deletion"
    confirmed = await _decide(client, gate, "confirm", "delete-confirmed")
    assert confirmed.status_code == 201
    deleted = await client.delete(
        "/api/v2/account", params={"gate_id": gate["id"]}
    )
    assert deleted.status_code == 204

    assert await test_db.fetch_one("SELECT id FROM users WHERE id='u1'") is None
    assert await test_db.fetch_one("SELECT id FROM users WHERE id='u2'") is not None
    assert (
        await test_db.fetch_one(
            "SELECT id FROM content_projects WHERE id=:id", {"id": own_project["id"]}
        )
        is None
    )
    assert (
        await test_db.fetch_one(
            "SELECT id FROM content_projects WHERE id=:id", {"id": other_project["id"]}
        )
        is not None
    )
    for table, owner_column in EXPORT_TABLES:
        row = await test_db.fetch_one(
            f"SELECT COUNT(*) AS count FROM {table} WHERE {owner_column}='u1'"
        )
        assert row["count"] == 0, table
