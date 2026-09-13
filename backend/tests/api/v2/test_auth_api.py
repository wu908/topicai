"""HTTP error-path contracts for the auth endpoints.

The register/login/refresh handlers previously had only service-level
coverage; the HTTPException mapping branches (409/401) were uncovered.
"""

from uuid import uuid4

import pytest


def _register_body(suffix: str) -> dict:
    return {
        "email": f"auth-api-{suffix}@example.com",
        "username": f"authapi{suffix}",
        "password": f"Auth-Api-Pw-{suffix}",
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
        "password": _register_body("nobody")["password"],
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_garbage_token_is_unauthorized(client):
    response = await client.post("/api/v2/auth/refresh", json={
        "refresh_token": f"not-a-real-token-{uuid4().hex[:8]}",
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


# ==================== POST /auth/password（改密码） ====================


@pytest.mark.asyncio
async def test_change_password_success_then_login_with_new(client, app):
    from app.api.deps import get_current_user

    register = await client.post(
        "/api/v2/auth/register",
        json={
            "email": f"pwchange-{uuid4().hex[:6]}@example.com",
            "username": "pwchange",
            "password": "Old-Pw-123456",
        },
    )
    assert register.status_code == 201
    registered = register.json()["data"]["user"]
    # 默认桩固定返回种子用户 u1（其 password_hash 是字面量 'hash'）；
    # 改密码必须针对注册出来的真实哈希校验，这里把桩换成注册用户。
    app.dependency_overrides[get_current_user] = lambda: {
        "id": registered["id"],
        "email": registered["email"],
        "username": registered["username"],
    }

    token = register.json()["data"]["access_token"]
    change = await client.post(
        "/api/v2/auth/password",
        json={"current_password": "Old-Pw-123456", "new_password": "New-Pw-654321"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert change.status_code == 200

    relogin_old = await client.post(
        "/api/v2/auth/login",
        json={"email": registered["email"], "password": "Old-Pw-123456"},
    )
    assert relogin_old.status_code == 401

    relogin_new = await client.post(
        "/api/v2/auth/login",
        json={"email": registered["email"], "password": "New-Pw-654321"},
    )
    assert relogin_new.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current_is_unauthorized(client, app):
    from app.api.deps import get_current_user

    register = await client.post(
        "/api/v2/auth/register",
        json={
            "email": f"pwchange-bad-{uuid4().hex[:6]}@example.com",
            "username": "pwchangebad",
            "password": "Old-Pw-123456",
        },
    )
    registered = register.json()["data"]["user"]
    app.dependency_overrides[get_current_user] = lambda: {
        "id": registered["id"],
        "email": registered["email"],
        "username": registered["username"],
    }
    change = await client.post(
        "/api/v2/auth/password",
        json={"current_password": "Wrong-Pw-000000", "new_password": "New-Pw-654321"},
        headers={"Authorization": f"Bearer {register.json()['data']['access_token']}"},
    )
    assert change.status_code == 401
    assert "当前密码不正确" in change.json()["detail"]


@pytest.mark.asyncio
async def test_change_password_requires_auth(client, app):
    from fastapi import HTTPException

    from app.api.deps import get_current_user

    async def _unauthenticated():
        raise HTTPException(status_code=401, detail="请先登录")

    app.dependency_overrides[get_current_user] = _unauthenticated
    change = await client.post(
        "/api/v2/auth/password",
        json={"current_password": "Old-Pw-123456", "new_password": "New-Pw-654321"},
    )
    assert change.status_code == 401
    assert "请先登录" in change.json()["detail"]


@pytest.mark.asyncio
async def test_change_password_rejects_same_password(client, app):
    from app.api.deps import get_current_user

    register = await client.post(
        "/api/v2/auth/register",
        json={
            "email": f"pwchange-same-{uuid4().hex[:6]}@example.com",
            "username": "pwchangesame",
            "password": "Same-Pw-123456",
        },
    )
    registered = register.json()["data"]["user"]
    app.dependency_overrides[get_current_user] = lambda: {
        "id": registered["id"],
        "email": registered["email"],
        "username": registered["username"],
    }
    change = await client.post(
        "/api/v2/auth/password",
        json={"current_password": "Same-Pw-123456", "new_password": "Same-Pw-123456"},
        headers={"Authorization": f"Bearer {register.json()['data']['access_token']}"},
    )
    assert change.status_code == 422
    assert "新密码不能与当前密码相同" in change.json()["detail"]
