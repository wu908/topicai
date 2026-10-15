"""P4 进化：learning_signals 采集 + 进化可见区（B1 / F1）。"""


async def test_learning_signal_roundtrip(client):
    got = await client.get("/api/v2/learning-signals")
    assert got.status_code == 200
    assert got.json()["data"]["items"] == []

    created = await client.post(
        "/api/v2/learning-signals",
        json={
            "kind": "decision",
            "ref": "human-gate:g1",
            "summary": "确认候选：保留 A 版",
            "payload": {"decision": "confirm"},
        },
    )
    assert created.status_code == 201, created.text
    items = created.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["kind"] == "decision"
    assert "保留 A 版" in items[0]["summary"]

    for kind in ("diff", "retro", "skip"):
        r = await client.post(
            "/api/v2/learning-signals",
            json={"kind": kind, "summary": f"{kind} 信号"},
        )
        assert r.status_code == 201

    listed = await client.get("/api/v2/learning-signals")
    assert listed.json()["data"]["total"] == 4

    only_diff = await client.get("/api/v2/learning-signals?kind=diff")
    assert only_diff.json()["data"]["total"] == 1
    assert only_diff.json()["data"]["items"][0]["kind"] == "diff"


async def test_learning_signal_rejects_unknown_kind(client):
    r = await client.post(
        "/api/v2/learning-signals",
        json={"kind": "gossip", "summary": "x"},
    )
    assert r.status_code == 422


async def test_evolution_summary_includes_signals_and_trust(client):
    await client.post(
        "/api/v2/learning-signals",
        json={"kind": "retro", "summary": "对账：收藏 45 点赞 32"},
    )
    r = await client.get("/api/v2/evolution/summary")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "changes" in data
    assert "capability_trust" in data
    summaries = [c["summary"] for c in data["changes"]]
    assert any("对账" in s for s in summaries)
