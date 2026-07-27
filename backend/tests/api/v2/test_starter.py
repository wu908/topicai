"""HTTP journey for starter assessment, directions and shared projects."""

import pytest

ASSESSMENT = {
    "motivation": "expression",
    "available_hours_per_week": 4,
    "publish_commitment": True,
    "accept_experiment": True,
    "experience_assets": ["第一次独自租房和整理小空间"],
    "interest_assets": ["低成本居住改造"],
    "skill_assets": ["用表格控制生活预算"],
    "privacy_limits": ["具体住址"],
    "idempotency_key": "starter-assessment-api",
}


@pytest.mark.asyncio
async def test_starter_api_hands_three_projects_to_existing_action_protocol(client):
    empty = await client.get("/api/v2/starter")
    assert empty.status_code == 200
    assert empty.json()["data"]["next_step"] == "assessment"

    assessed = await client.post("/api/v2/starter/assessment", json=ASSESSMENT)
    assert assessed.status_code == 201
    assessment = assessed.json()["data"]["assessment"]
    assert assessment["readiness"] == "ready"

    generated = await client.post(
        "/api/v2/starter/directions:generate",
        json={
            "expected_assessment_version": assessment["version"],
            "idempotency_key": "starter-directions-api",
        },
    )
    assert generated.status_code == 201
    candidates = generated.json()["data"]["candidates"]
    assert len(candidates) <= 3

    selected = await client.post(
        f"/api/v2/starter/directions/{candidates[0]['id']}:select",
        json={
            "expected_direction_version": candidates[0]["version"],
            "idempotency_key": "starter-sprint-api",
        },
    )
    assert selected.status_code == 201
    workspace = selected.json()["data"]
    assert len(workspace["projects"]) == 3

    for project in workspace["projects"]:
        action = await client.get(f"/api/v2/projects/{project['id']}/next-action")
        assert action.status_code == 200
        assert action.json()["data"]["action_type"] == "confirm_intent"

    replay = await client.post(
        f"/api/v2/starter/directions/{candidates[0]['id']}:select",
        json={
            "expected_direction_version": candidates[0]["version"],
            "idempotency_key": "starter-sprint-api",
        },
    )
    assert replay.status_code == 200
    assert [item["id"] for item in replay.json()["data"]["projects"]] == [
        item["id"] for item in workspace["projects"]
    ]


@pytest.mark.asyncio
async def test_starter_resources_are_owner_scoped(client, client_as_u2):
    assessed = await client.post("/api/v2/starter/assessment", json=ASSESSMENT)
    assessment = assessed.json()["data"]["assessment"]
    generated = await client.post(
        "/api/v2/starter/directions:generate",
        json={
            "expected_assessment_version": assessment["version"],
            "idempotency_key": "starter-directions-owner",
        },
    )
    direction = generated.json()["data"]["candidates"][0]
    foreign = await client_as_u2.post(
        f"/api/v2/starter/directions/{direction['id']}:select",
        json={
            "expected_direction_version": direction["version"],
            "idempotency_key": "foreign-selection",
        },
    )
    assert foreign.status_code == 404
