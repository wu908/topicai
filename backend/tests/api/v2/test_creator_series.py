"""HTTP contracts for creator series candidates and decisions."""

import pytest

from tests.helpers.publish import published_project as _published_project


@pytest.mark.asyncio
async def test_series_candidate_confirm_list_workspace_and_revoke(
    client, client_as_u2, test_db
):
    first = await _published_project(test_db, "one")
    second = await _published_project(test_db, "two")
    candidate_body = {
        "source_project_ids": [first["id"], second["id"]],
        "expected_project_versions": {
            first["id"]: first["version"],
            second["id"]: second["version"],
        },
        "idempotency_key": "api-series-propose",
    }
    proposed = await client.post("/api/v2/creator-series-candidates", json=candidate_body)
    replay = await client.post("/api/v2/creator-series-candidates", json=candidate_body)

    assert proposed.status_code == 201
    assert replay.status_code == 200
    assert replay.json()["meta"]["idempotency_replayed"] is True
    candidate = proposed.json()["data"]
    assert candidate["status"] == "proposed"

    listed = await client.get("/api/v2/creator-series")
    assert listed.status_code == 200
    assert listed.json()["data"]["items"][0]["id"] == candidate["id"]

    confirmed = await client.post(
        f"/api/v2/creator-series/{candidate['id']}:decide",
        json={
            "decision": "confirm",
            "confirmed_name": "稳定更新实验室",
            "confirmed_promise": "持续展示一套更新机制如何建立和修正",
            "confirmed_continuation_prompt": "下一篇记录第一次失效时如何调整",
            "expected_series_version": candidate["version"],
            "idempotency_key": "api-series-confirm",
        },
    )
    assert confirmed.status_code == 201
    confirmed_data = confirmed.json()["data"]
    assert confirmed_data["status"] == "confirmed"

    workspace = await client.get(f"/api/v2/projects/{first['id']}/calibration")
    assert workspace.status_code == 200
    workspace_data = workspace.json()["data"]
    assert workspace_data["creator_series"][0]["status"] == "confirmed"
    assert workspace_data["content_genome"]["series_context"][0]["name"] == (
        "稳定更新实验室"
    )

    opportunity = await client.post(
        f"/api/v2/creator-series/{candidate['id']}/extension-opportunities",
        json={
            "expected_series_version": confirmed_data["version"],
            "idempotency_key": "api-series-extension",
        },
    )
    assert opportunity.status_code == 201
    opportunity_data = opportunity.json()["data"]
    assert opportunity_data["status"] == "proposed"
    assert opportunity_data["created_project_id"] is None
    assert opportunity_data["dimensions"] == {
        "audience_fit": "strong",
        "creator_fit": "strong",
        "material_readiness": "partial",
        "growth_role": "series",
        "series_potential": "high",
        "timeliness": "evergreen",
        "similarity_risk": "unknown",
        "safety_risk": "unknown",
    }

    await test_db.execute(
        "UPDATE content_projects SET status='settled' WHERE id IN (:first,:second)",
        {"first": first["id"], "second": second["id"]},
    )
    today = await client.get("/api/v2/today")
    assert today.status_code == 200
    today_action = today.json()["data"]["action"]
    assert today_action["action_type"] == "create_project"
    assert today_action["expected_state_change"] == {
        "action_type": "review_opportunity",
        "source": "series_opportunity",
        "opportunity_id": opportunity_data["id"],
        "opportunity_version": opportunity_data["version"],
    }
    assert today_action["fallback_action"]["path"] == "/opportunities"

    other_owner_today = await client_as_u2.get("/api/v2/today")
    assert other_owner_today.status_code == 200
    other_owner_change = other_owner_today.json()["data"]["action"][
        "expected_state_change"
    ]
    assert other_owner_change["action_type"] == "create_project"
    assert other_owner_change.get("source") != "series_opportunity"
    assert "opportunity_id" not in other_owner_change

    accepted = await client.post(
        f"/api/v2/content-opportunities/{opportunity_data['id']}:decide",
        json={
            "decision": "accept",
            "confirmed_title": "更新机制第一次失效后，我改了什么",
            "confirmed_audience_change": "读者看到机制如何在失败后继续迭代",
            "confirmed_material_requirements": ["失效现场", "调整动作", "调整结果"],
            "expected_opportunity_version": opportunity_data["version"],
            "idempotency_key": "api-series-extension-accept",
        },
    )
    assert accepted.status_code == 201
    accepted_data = accepted.json()["data"]
    assert accepted_data["status"] == "accepted"
    assert accepted_data["project"]["opportunity_id"] == opportunity_data["id"]
    assert accepted_data["project"]["intent_status"] == "working_confirmed"

    refreshed_workspace = await client.get(
        f"/api/v2/projects/{first['id']}/calibration"
    )
    assert refreshed_workspace.json()["data"]["content_opportunities"][0][
        "created_project_id"
    ] == accepted_data["project"]["id"]

    revoked = await client.post(
        f"/api/v2/creator-series/{candidate['id']}:revoke",
        json={
            "reason": "不再继续这个系列",
            "expected_series_version": confirmed_data["version"],
            "idempotency_key": "api-series-revoke",
        },
    )
    assert revoked.status_code == 201
    assert revoked.json()["data"]["status"] == "revoked"


@pytest.mark.asyncio
async def test_series_routes_are_typed_and_owner_scoped(client, client_as_u2):
    invalid = await client.post(
        "/api/v2/creator-series-candidates",
        json={
            "source_project_ids": ["only-one"],
            "expected_project_versions": {"only-one": 1},
            "idempotency_key": "api-series-invalid",
        },
    )
    assert invalid.status_code == 422

    other_owner_list = await client_as_u2.get("/api/v2/creator-series")
    assert other_owner_list.status_code == 200
    assert other_owner_list.json()["data"]["items"] == []

    openapi = (await client.get("/openapi.json")).json()["paths"]
    assert "/api/v2/creator-series-candidates" in openapi
    assert "/api/v2/creator-series/{series_id}:decide" in openapi
    assert "/api/v2/creator-series/{series_id}:revoke" in openapi
    assert "/api/v2/content-opportunities" in openapi
    assert "/api/v2/creator-series/{series_id}/extension-opportunities" in openapi
    assert "/api/v2/content-opportunities/{opportunity_id}:decide" in openapi
