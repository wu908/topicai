"""Public API surface after the v1 removal."""

import pytest


@pytest.mark.asyncio
async def test_openapi_exposes_only_v2_application_routes(client):
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v2/health" in paths
    assert "/api/v2/auth/login" in paths
    assert not any(path.startswith("/api/v1") for path in paths)


@pytest.mark.asyncio
async def test_v1_health_is_gone(client):
    response = await client.get("/api/v1/health")

    assert response.status_code == 404
