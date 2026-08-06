"""API router test fixtures.

Provides an isolated FastAPI app per test with:
- In-memory SQLite database (test_db fixture inherited from parent conftest)
- Auth override that returns a fake authenticated user
- DB override pointing at the test database
"""
from __future__ import annotations

import pytest_asyncio
from sqlalchemy import text


@pytest_asyncio.fixture(autouse=True)
async def _insert_test_users(test_db):
    """Insert two users so cross-user (ownership) tests can run."""
    s = await test_db.get_session()
    try:
        for uid, email, uname in [
            ("u1", "u1@test.com", "UserOne"),
            ("u2", "u2@test.com", "UserTwo"),
        ]:
            await s.execute(text(
                "INSERT OR IGNORE INTO users (id, email, username, password_hash, "
                "ai_calls_today, ai_calls_reset_at, created_at) "
                "VALUES (:id, :email, :uname, 'hash', 0, '', '2026-06-03T00:00:00Z')"
            ), {"id": uid, "email": email, "uname": uname})
        await s.commit()
    finally:
        await s.close()


@pytest_asyncio.fixture
async def app(test_db):
    """Build a FastAPI app with auth and DB overrides pointed at the test_db.

    We import the real create_app() but override the get_current_user and
    get_db dependencies so the app talks to our :memory: database with a
    fake authenticated user.
    """
    from app.api.deps import get_current_user, get_db
    from main import create_app

    app = create_app()
    app.dependency_overrides[get_db] = lambda: test_db

    # Default: override returns user 'u1'. Per-test fixtures can swap this.
    async def _fake_user_u1():
        return {
            "id": "u1", "email": "u1@test.com", "username": "UserOne",
            "ai_calls_today": 0, "created_at": "2026-06-03T00:00:00Z",
            "last_login": None,
        }
    app.dependency_overrides[get_current_user] = _fake_user_u1
    yield app
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def app_as_u2(test_db):
    """Same as `app` but authenticated as user 'u2' — for cross-user tests."""
    from app.api.deps import get_current_user, get_db
    from main import create_app

    app = create_app()
    app.dependency_overrides[get_db] = lambda: test_db

    async def _fake_user_u2():
        return {
            "id": "u2", "email": "u2@test.com", "username": "UserTwo",
            "ai_calls_today": 0, "created_at": "2026-06-03T00:00:00Z",
            "last_login": None,
        }
    app.dependency_overrides[get_current_user] = _fake_user_u2
    yield app
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app):
    """HTTPX AsyncClient bound to the FastAPI app with auth as user u1.

    raise_app_exceptions=False on the transport so the client returns 5xx
    responses instead of re-raising ValueError, letting ownership tests
    assert the boundary behavior (no mutation) even before routers
    translate ValueError→404.
    """
    from httpx import ASGITransport, AsyncClient
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as c:
        yield c


@pytest_asyncio.fixture
async def client_as_u2(app_as_u2):
    """HTTPX AsyncClient authenticated as user u2 — for cross-user tests."""
    from httpx import ASGITransport, AsyncClient
    async with AsyncClient(
        transport=ASGITransport(app=app_as_u2, raise_app_exceptions=False),
        base_url="http://test",
    ) as c:
        yield c


@pytest_asyncio.fixture
async def client_no_auth(test_db):
    """HTTPX AsyncClient with NO auth override — exercises the real
    get_current_user which will 401 when request.state.user_id is missing."""
    from httpx import ASGITransport, AsyncClient

    from app.api.deps import get_db
    from main import create_app

    app = create_app()
    app.dependency_overrides[get_db] = lambda: test_db
    # Intentionally NO get_current_user override — real one runs and 401s.
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as c:
        yield c
    app.dependency_overrides.clear()
