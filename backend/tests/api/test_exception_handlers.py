"""Tests for global ValueError exception handler.

Locks in the router-boundary translation:
- "not found" → 404
- "last admin" / "already exists" / "not owned" → 422
- other → 400
"""
import pytest


@pytest.mark.asyncio
async def test_value_error_not_found_returns_404(client):
    """A service raising ValueError('X not found') must surface as 404."""
    from fastapi import FastAPI

    from app.api.v1.deps import get_current_user, get_db
    from app.core.exceptions import setup_exception_handlers

    app = FastAPI()
    setup_exception_handlers(app)
    app.dependency_overrides[get_db] = lambda: None
    async def _fake_user():
        return {"id": "u1"}
    app.dependency_overrides[get_current_user] = _fake_user

    @app.get("/raise-not-found")
    async def raise_not_found():
        raise ValueError("Account not found")

    from httpx import ASGITransport, AsyncClient
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as c:
        r = await c.get("/raise-not-found")
    assert r.status_code == 404
    body = r.json()
    assert body["code"] == 404
    assert "Account not found" in body["message"]


@pytest.mark.asyncio
async def test_value_error_last_admin_returns_422(client):
    from fastapi import FastAPI

    from app.api.v1.deps import get_current_user, get_db
    from app.core.exceptions import setup_exception_handlers

    app = FastAPI()
    setup_exception_handlers(app)
    app.dependency_overrides[get_db] = lambda: None
    async def _fake_user():
        return {"id": "u1"}
    app.dependency_overrides[get_current_user] = _fake_user

    @app.get("/raise-last-admin")
    async def raise_last_admin():
        raise ValueError("Cannot demote the last admin")

    from httpx import ASGITransport, AsyncClient
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as c:
        r = await c.get("/raise-last-admin")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_value_error_already_exists_returns_422(client):
    from fastapi import FastAPI

    from app.api.v1.deps import get_current_user, get_db
    from app.core.exceptions import setup_exception_handlers

    app = FastAPI()
    setup_exception_handlers(app)
    app.dependency_overrides[get_db] = lambda: None
    async def _fake_user():
        return {"id": "u1"}
    app.dependency_overrides[get_current_user] = _fake_user

    @app.get("/raise-duplicate")
    async def raise_duplicate():
        raise ValueError("Member with email 'a@b.com' already exists")

    from httpx import ASGITransport, AsyncClient
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as c:
        r = await c.get("/raise-duplicate")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_value_error_other_returns_400(client):
    from fastapi import FastAPI

    from app.api.v1.deps import get_current_user, get_db
    from app.core.exceptions import setup_exception_handlers

    app = FastAPI()
    setup_exception_handlers(app)
    app.dependency_overrides[get_db] = lambda: None
    async def _fake_user():
        return {"id": "u1"}
    app.dependency_overrides[get_current_user] = _fake_user

    @app.get("/raise-other")
    async def raise_other():
        raise ValueError("malformed input abc")

    from httpx import ASGITransport, AsyncClient
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as c:
        r = await c.get("/raise-other")
    assert r.status_code == 400
