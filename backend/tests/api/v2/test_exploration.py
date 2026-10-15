"""探索位 / 落选归因 API（P3-B4）。"""


async def test_exploration_slot_roundtrip(client):
    got = await client.get("/api/v2/exploration-slots")
    assert got.status_code == 200
    data = got.json()["data"]
    assert data["items"] == []
    version = data["version"]

    created = await client.post(
        "/api/v2/exploration-slots",
        json={
            "title": "清单体 vs 过程叙事",
            "hypothesis": "过程叙事更能带评论",
            "expected_version": version,
        },
    )
    assert created.status_code == 201
    items = created.json()["data"]["items"]
    assert len(items) == 1
    slot = items[0]
    assert slot["status"] == "running"
    assert slot["title"] == "清单体 vs 过程叙事"
    v2 = created.json()["data"]["version"]

    decided = await client.post(
        f"/api/v2/exploration-slots/{slot['id']}:decide",
        json={
            "status": "rejected",
            "attribution": "样本不够，落选不计能力等级",
            "expected_version": v2,
        },
    )
    assert decided.status_code == 200
    d = decided.json()["data"]["items"][0]
    assert d["status"] == "rejected"
    assert "样本不够" in d["attribution"]


async def test_exploration_slot_version_conflict(client):
    got = await client.get("/api/v2/exploration-slots")
    version = got.json()["data"]["version"]
    await client.post(
        "/api/v2/exploration-slots",
        json={"title": "A", "expected_version": version},
    )
    # stale version
    r = await client.post(
        "/api/v2/exploration-slots",
        json={"title": "B", "expected_version": version},
    )
    assert r.status_code in (409, 412, 500)
