"""Integration test fixtures (Spec-007 Phase 10 T093).

Re-exports the app + client fixtures from `tests/api/conftest.py` so
they're visible to tests under `tests/integration/`. Without this, the
per-test autouse ``_insert_test_users`` + ``app`` + ``client`` trio
defined in `tests/api/conftest.py` isn't auto-discovered.
"""
from __future__ import annotations

import pytest_asyncio
from sqlalchemy import text


@pytest_asyncio.fixture(autouse=True)
async def _insert_test_users(test_db):
    """Insert u1/u2 so cross-user ownership tests can run."""
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
    """FastAPI app with auth + DB overrides pointed at the test_db."""
    from app.api.v1.deps import get_current_user, get_db
    from main import create_app

    app = create_app()
    app.dependency_overrides[get_db] = lambda: test_db

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
async def client(app):
    """HTTPX AsyncClient bound to the FastAPI app, auth as user u1."""
    from httpx import ASGITransport, AsyncClient
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as c:
        yield c
