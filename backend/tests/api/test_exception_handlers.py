"""Tests for global exception handlers.

Two suites:

1. ValueError boundary translation (router-boundary):
   - "not found" → 404
   - "last admin" / "already exists" / "not owned" → 422
   - other → 400

2. RequestValidationError sanitization (D5):
   - In production, the handler must NOT echo Pydantic's internal
     `errors()` (field paths `loc`, `type`, `ctx`, `input`) back to the
     client — that leaks internal schema structure. Only `error_code`
     plus a generic message is returned.
   - In development, the `errors` array is kept so devs can debug.
"""
import pytest


def _reset_settings_singleton() -> None:
    """Clear the cached settings singleton so the next get_settings()
    call reloads from the (monkeypatched) environment."""
    import config.settings

    config.settings._settings = None


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


# ==================== D5: RequestValidationError sanitization ====================


def _build_validation_app():
    """Build a minimal FastAPI app with the global exception handlers and a
    route that has strict Pydantic validation so we can trigger a
    RequestValidationError on a bad request body."""
    from fastapi import FastAPI
    from pydantic import BaseModel

    from app.core.exceptions import setup_exception_handlers

    app = FastAPI()
    setup_exception_handlers(app)

    class Body(BaseModel):
        name: str
        age: int

    @app.post("/validate")
    async def validate(body: Body):
        return {"name": body.name, "age": body.age}

    return app


@pytest.mark.asyncio
async def test_validation_error_in_production_does_not_leak_internal_errors(
    monkeypatch, client
):
    """D5: In production, RequestValidationError must NOT echo Pydantic's
    internal `errors()` (loc / type / ctx / input) — that leaks the internal
    schema structure to the client. Only `error_code` + generic message."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    _reset_settings_singleton()
    try:
        app = _build_validation_app()
        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as c:
            # Missing required field "name" and wrong type for "age".
            r = await c.post("/validate", json={"age": "not-an-int"})
    finally:
        _reset_settings_singleton()

    assert r.status_code == 422
    body = r.json()
    assert body["code"] == 422
    assert body["message"] == "请求参数校验失败"
    meta = body["meta"]
    assert meta.get("error_code") == "VALIDATION_ERROR"
    # Production MUST NOT leak internal Pydantic error details.
    assert "errors" not in meta or meta["errors"] in (None, [], ""), (
        f"production meta leaked internal errors: {meta.get('errors')!r}"
    )


@pytest.mark.asyncio
async def test_validation_error_in_dev_keeps_errors_for_debug(monkeypatch, client):
    """D5: In development, RequestValidationError still surfaces the full
    Pydantic `errors()` array so developers can debug schema mismatches."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    _reset_settings_singleton()
    try:
        app = _build_validation_app()
        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as c:
            r = await c.post("/validate", json={"age": "not-an-int"})
    finally:
        _reset_settings_singleton()

    assert r.status_code == 422
    body = r.json()
    assert body["code"] == 422
    assert body["message"] == "请求参数校验失败"
    meta = body["meta"]
    assert meta.get("error_code") == "VALIDATION_ERROR"
    # Dev keeps the detailed Pydantic error list.
    errors = meta.get("errors")
    assert isinstance(errors, list) and len(errors) > 0, (
        f"dev meta missing detailed errors: {meta!r}"
    )
