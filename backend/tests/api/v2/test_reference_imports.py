"""参考样本导入的 HTTP 契约（冷启动锚点 R7）。

服务层的隔离由 tests/services/test_reference_samples.py 守；这里确认用户实际
碰到的那一层：贴进来的参考内容不会长成"你是谁"的画像。
"""

import pytest

# u1 由 tests/api/conftest.py 的 autouse 夹具建好，这里不再重复插入。


def _body(items: list[dict], key: str) -> dict:
    return {"method": "manual", "items": items, "idempotency_key": key}


@pytest.mark.asyncio
async def test_reference_import_requires_a_source_for_every_item(client):
    response = await client.post(
        "/api/v2/reference-imports",
        json=_body(
            [
                {"title": "我知道这是谁", "tags": ["租房"], "source_handle": "@某人"},
                {"title": "我不知道这是谁", "tags": ["租房"]},
            ],
            "ref-http-1",
        ),
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["success_count"] == 1
    assert [item["status"] for item in payload["item_results"]] == [
        "imported",
        "failed",
    ]


@pytest.mark.asyncio
async def test_reference_content_does_not_become_the_creator_profile(client):
    """对照：同一段文本走 /reference-imports 不影响画像，走 /history-imports 才影响。"""
    item = {"title": "租房第一年，我把 12 平住成了两室", "tags": ["租房"], "source_handle": "@某人"}

    imported = await client.post("/api/v2/reference-imports", json=_body([item], "ref-http-2"))
    assert imported.status_code == 201
    assert imported.json()["data"]["success_count"] == 1

    after_reference = (await client.get("/api/v2/creator-profile")).json()["data"]
    assert after_reference["attributes"]["content_pillars"] == []
    assert after_reference["attributes"]["niche"]["value"] == ""

    mine = {key: value for key, value in item.items() if key != "source_handle"}
    as_history = await client.post("/api/v2/history-imports", json=_body([mine], "self-http-1"))
    assert as_history.status_code == 201

    after_history = (await client.get("/api/v2/creator-profile")).json()["data"]
    assert [pillar["value"] for pillar in after_history["attributes"]["content_pillars"]] == [
        "租房"
    ]
