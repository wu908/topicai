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
