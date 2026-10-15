"""路径画像 API：GET/PUT 与版本乐观锁。"""


async def test_path_profile_roundtrip(client):
    got = await client.get("/api/v2/path-profile")
    assert got.status_code == 200
    data = got.json()["data"]
    version = data["version"]

    put = await client.put(
        "/api/v2/path-profile",
        json={
            "statement": "把生活里的小实验讲清楚",
            "publish_focus": "可复现的小方法",
            "avoid": "焦虑贩卖",
            "cadence": "每周 1–2 条",
            "tone": "短句不端着",
            "expected_version": version,
        },
    )
    assert put.status_code == 200
    body = put.json()["data"]
    assert body["statement"] == "把生活里的小实验讲清楚"
    assert body["avoid"] == "焦虑贩卖"

    again = await client.get("/api/v2/path-profile")
    assert again.json()["data"]["statement"] == "把生活里的小实验讲清楚"

"""P3-B1：路径画像 AI 修订提案 —— 只提议，写入仍走 PUT。"""

from unittest.mock import patch


async def test_propose_revision_returns_field_proposals(client):
    class _FakeLLM:
        def generate(self, prompt, system_prompt=None, **kwargs):
            assert "不得编造" in system_prompt or "不编造" in system_prompt or "提案" in system_prompt
            return (
                '{"statement":"把生活里的小实验讲清楚的效率博主",'
                '"publish_focus":"可复现的小方法 · 踩坑复盘",'
                '"reason":"更具体，便于选题"}'
            )

        def is_available(self, capability: str = "text") -> bool:
            return True

    with patch("app.api.v2.path_profile.LLMClient", _FakeLLM):
        r = await client.post("/api/v2/path-profile:propose-revision", json={})
    assert r.status_code == 200
    data = r.json()["data"]
    assert "proposals" in data
    props = data["proposals"]
    assert isinstance(props, list) and len(props) >= 1
    fields = {p["field"] for p in props}
    assert fields & {"statement", "publish_focus", "avoid", "cadence", "tone"}
    # 只提议，不落库
    got = await client.get("/api/v2/path-profile")
    assert got.json()["data"]["statement"] == ""


async def test_propose_revision_does_not_mutate_when_llm_down(client):
    class _Down:
        def generate(self, *a, **k):
            raise RuntimeError("no model")

        def is_available(self, capability: str = "text") -> bool:
            return True

    with patch("app.api.v2.path_profile.LLMClient", _Down):
        r = await client.post("/api/v2/path-profile:propose-revision", json={})
    # 无模型 → 空提案，不报 500
    assert r.status_code == 200
    assert r.json()["data"]["proposals"] == []
