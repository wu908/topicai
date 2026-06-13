"""Unit tests for ErrorHandlerMiddleware."""

import pytest

from app.core.exceptions import AppException
from app.middleware.error_handler import ErrorHandlerMiddleware


class _FakeRequest:
    """Minimal request stub exposing what ErrorHandlerMiddleware uses."""

    def __init__(self, path: str = "/x", method: str = "GET") -> None:
        self.url = type("U", (), {"__str__": lambda self: path})()
        self.method = method


class _FakeResponse:
    def __init__(self) -> None:
        self.headers: dict[str, str] = {}


@pytest.mark.asyncio
async def test_dispatch_passes_through_on_success() -> None:
    """Successful response gets X-Process-Time header and is returned unchanged."""
    mw = ErrorHandlerMiddleware(app=None)  # type: ignore[arg-type]
    response = _FakeResponse()

    async def _call_next(_request):
        return response

    out = await mw.dispatch(_FakeRequest(), _call_next)
    assert out is response
    assert "X-Process-Time" in out.headers


@pytest.mark.asyncio
async def test_dispatch_handles_known_app_exception() -> None:
    """AppException → structured JSON 4xx with error_code in meta."""
    mw = ErrorHandlerMiddleware(app=None)  # type: ignore[arg-type]

    async def _call_next(_request):
        raise AppException(error_code="NOT_FOUND", message="missing", status_code=404)

    response = await mw.dispatch(_FakeRequest(path="/foo", method="POST"), _call_next)
    assert response.status_code == 404
    import json
    body = json.loads(response.body)
    assert body["code"] == 404
    assert body["message"] == "missing"
    assert body["meta"]["error_code"] == "NOT_FOUND"
    assert "X-Process-Time" in response.headers


@pytest.mark.asyncio
async def test_dispatch_handles_unhandled_exception() -> None:
    """Unhandled Exception → 500 with generic Chinese message; no leak of internals."""
    mw = ErrorHandlerMiddleware(app=None)  # type: ignore[arg-type]

    async def _call_next(_request):
        raise RuntimeError("secret stack trace")

    response = await mw.dispatch(_FakeRequest(), _call_next)
    assert response.status_code == 500
    body = response.body
    assert b"INTERNAL_ERROR" in body
    assert b"secret stack trace" not in body  # do not leak
    assert "X-Process-Time" in response.headers
