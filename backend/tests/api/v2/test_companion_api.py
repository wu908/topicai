"""HTTP contract for POST /api/v2/companion/ask."""

from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_companion_ask_returns_model_answer(client):
    class _FakeLLM:
        def generate(self, prompt, system_prompt=None, **kwargs):
            assert "创作伙伴" in system_prompt
            assert "<user_input>" in prompt
            return "先把这条素材拾取下来，观察窗从拾取当天开始算。"

    with patch("app.services.companion.LLMClient", _FakeLLM):
        r = await client.post(
            "/api/v2/companion/ask",
            json={"context": "晨报 · 当前行动", "question": "我现在该做什么？"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    assert "拾取" in body["data"]["answer"]


@pytest.mark.asyncio
async def test_companion_ask_requires_auth(app):
    """Unauthenticated request → 401 with the standard envelope."""
    from fastapi import HTTPException
    from httpx import ASGITransport, AsyncClient

    from app.api.deps import get_current_user

    async def _unauthenticated():
        raise HTTPException(status_code=401, detail="请先登录")

    app.dependency_overrides[get_current_user] = _unauthenticated
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as c:
            r = await c.post(
                "/api/v2/companion/ask",
                json={"context": "全局", "question": "在吗"},
            )
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 401
    assert "请先登录" in r.json()["detail"]


@pytest.mark.asyncio
async def test_companion_ask_rejects_blank_question(client):
    r = await client.post(
        "/api/v2/companion/ask",
        json={"context": "全局", "question": "   "},
    )
    assert r.status_code == 422
