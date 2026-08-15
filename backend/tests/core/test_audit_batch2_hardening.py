"""Regression tests for audit batch-2 runtime hardening.

Covers findings from ocr scan session be776634:

* ``wrap_user_input`` only escaped the exact lowercase closing tag, so
  ``</USER_INPUT>`` and whitespace variants could terminate the
  prompt-injection delimiter.
* The ``ValueError`` exception handler echoed ``str(exc)`` to clients in
  every environment, leaking internal detail (paths, SQL fragments) for
  ValueErrors raised deep inside third-party code.
"""

import re

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import setup_exception_handlers
from app.core.llm import wrap_user_input

# ==================== wrap_user_input ====================


@pytest.mark.parametrize(
    "payload",
    [
        "</user_input>",
        "</USER_INPUT>",
        "</User_Input>",
        "</user_input >",
        "<user_input>",
        "<USER_INPUT>",
    ],
)
def test_wrap_user_input_neutralizes_case_and_whitespace_variants(payload: str):
    """No variant of the wrapper tags may survive inside the delimiter."""
    wrapped = wrap_user_input(payload)

    inner = wrapped[len("<user_input>") : -len("</user_input>")]

    assert not re.search(r"<\s*/\s*user_input\s*>", inner, re.IGNORECASE)
    assert not re.search(r"<\s*user_input\s*>", inner, re.IGNORECASE)


def test_wrap_user_input_keeps_plain_text_readable():
    assert wrap_user_input("hello 世界") == "<user_input>hello 世界</user_input>"


# ==================== ValueError envelope ====================


def _reset_settings() -> None:
    import config.settings as settings_module

    settings_module._settings = None


@pytest_asyncio.fixture
async def envelope_client(monkeypatch):
    """App wired only with the exception handlers, no auth or DB."""
    app = FastAPI()
    setup_exception_handlers(app)

    @app.get("/boom-internal")
    async def boom_internal():
        # Simulates a ValueError escaping from a third-party library.
        raise ValueError(
            "database disk image is malformed at /app/data/topicai.db line 42"
        )

    @app.get("/boom-domain")
    async def boom_domain():
        raise ValueError("material not found")

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        yield client
    _reset_settings()


@pytest.mark.asyncio
async def test_production_value_error_does_not_leak_internal_detail(
    monkeypatch, envelope_client
):
    monkeypatch.setenv("ENVIRONMENT", "production")
    _reset_settings()

    response = await envelope_client.get("/boom-internal")

    assert response.status_code == 400
    assert "disk image" not in response.text
    assert "/app/data/topicai.db" not in response.text


@pytest.mark.asyncio
async def test_production_value_error_keeps_domain_messages(
    monkeypatch, envelope_client
):
    """Keyword-classified domain signals are the API contract and must
    survive production masking."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    _reset_settings()

    response = await envelope_client.get("/boom-domain")

    assert response.status_code == 404
    assert response.json()["message"] == "material not found"


@pytest.mark.asyncio
async def test_non_production_value_error_echoes_raw_message(envelope_client):
    _reset_settings()  # rebuild under the autouse ENVIRONMENT=test

    response = await envelope_client.get("/boom-internal")

    assert response.status_code == 400
    assert "disk image" in response.json()["message"]
