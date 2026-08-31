"""HTTP error-path contracts for the auth endpoints.

The register/login/refresh handlers previously had only service-level
coverage; the HTTPException mapping branches (409/401) were uncovered.
"""

import pytest


def _register_body(suffix: str) -> dict:
    return {
        "email": f"auth-api-{suffix}@example.com",
        "username": f"authapi{suffix}",
        "password": "Auth-Api-Pw-123",
    }


@pytest.mark.asyncio
async def test_register_success_and_duplicate_conflict(client):
    first = await client.post("/api/v2/auth/register", json=_register_body("dup"))
    assert first.status_code == 201
    assert first.json()["data"]["access_token"]

    duplicate = await client.post("/api/v2/auth/register", json=_register_body("dup"))
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password_rejected(client):
    weak = _register_body("weak")
    weak["password"] = "short"
    response = await client.post("/api/v2/auth/register", json=weak)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_wrong_password_is_unauthorized(client):
    await client.post("/api/v2/auth/register", json=_register_body("login"))
    wrong = _register_body("login")
    wrong["password"] = "Definitely-Not-The-Password"
    response = await client.post("/api/v2/auth/login", json={
        "email": wrong["email"], "password": wrong["password"],
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email_is_unauthorized(client):
    response = await client.post("/api/v2/auth/login", json={
        "email": "nobody-auth-api@example.com",
        "password": "Whatever-Pw-123",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_garbage_token_is_unauthorized(client):
    response = await client.post("/api/v2/auth/refresh", json={
        "refresh_token": "not-a-real-token",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_roundtrip_with_registered_user(client):
    registered = (
        await client.post("/api/v2/auth/register", json=_register_body("refresh"))
    ).json()["data"]
    response = await client.post("/api/v2/auth/refresh", json={
        "refresh_token": registered["refresh_token"],
    })
    assert response.status_code == 200
    assert response.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_me_returns_authenticated_user(client):
    response = await client.get("/api/v2/auth/me")
    assert response.status_code == 200
    assert response.json()["data"]["user"]["id"] == "u1"
