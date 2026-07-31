"""Foundation contract for the ContentProject v2 API."""

import pytest


@pytest.mark.asyncio
async def test_v2_health_is_registered_and_provider_neutral(client):
    response = await client.get("/api/v2/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 200
    assert payload["data"]["status"] == "ok"
    assert payload["data"]["api_version"] == "v2"
    assert payload["data"]["product"] == "content_project"
    assert "provider" not in payload["data"]


@pytest.mark.asyncio
async def test_v2_health_appears_in_openapi(client):
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v2/health" in response.json()["paths"]


@pytest.mark.asyncio
async def test_project_transition_returns_project_and_state_event(client):
    created = await client.post(
        "/api/v2/projects",
        json={
            "title": "Transition through the public seam",
            "target_audience": "Creators",
            "idempotency_key": "api-state-project",
        },
    )
    project = created.json()["data"]

    response = await client.post(
        f"/api/v2/projects/{project['id']}/transitions",
        json={
            "to_status": "creating",
            "reason": "brief_baseline_saved",
            "expected_version": project["version"],
            "idempotency_key": "api-state-transition",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["data"]["project"]["status"] == "creating"
    assert payload["data"]["event"]["actor_type"] == "user"
    assert payload["meta"]["idempotency_replayed"] is False
