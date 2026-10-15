"""HTTP contract for POST /api/v2/projects/{id}/humanize（P2-B1）。"""

from unittest.mock import patch

import pytest


async def _create_project(client) -> str:
    r = await client.post(
        "/api/v2/projects/start",
        json={"raw_input": "人话化测试条目", "idempotency_key": "hum-1"},
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]["project_id"]


@pytest.mark.asyncio
async def test_humanize_rewrites_body(client):
    class _FakeLLM:
        def generate(self, prompt, system_prompt=None, **kwargs):
            assert "不得编造" in system_prompt or "不编造" in system_prompt
            return "番茄钟挪到第二天早上，反而更容易坚持。"

        def is_available(self, capability: str = "text") -> bool:
            return True

    pid = await _create_project(client)
    with patch("app.services.humanize.LLMClient", _FakeLLM):
        r = await client.post(
            f"/api/v2/projects/{pid}/humanize",
            json={"body_text": "基于数据分析，番茄钟优化方案可提升效率。"},
        )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["changed"] is True
    assert "番茄钟挪到第二天" in data["body_text"]


@pytest.mark.asyncio
async def test_humanize_keeps_original_when_llm_down(client):
    class _Down:
        def generate(self, *a, **k):
            raise RuntimeError("no model")

        def is_available(self, capability: str = "text") -> bool:
            return True

    pid = await _create_project(client)
    src = "原文。"
    with patch("app.services.humanize.LLMClient", _Down):
        r = await client.post(
            f"/api/v2/projects/{pid}/humanize",
            json={"body_text": src},
        )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["body_text"] == src
    assert data["changed"] is False


@pytest.mark.asyncio
async def test_humanize_requires_existing_project(client):
    r = await client.post(
        "/api/v2/projects/no-such-id/humanize",
        json={"body_text": "x"},
    )
    assert r.status_code in (404, 500)
