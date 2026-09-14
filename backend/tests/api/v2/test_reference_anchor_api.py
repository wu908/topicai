"""参考锚点的 HTTP 契约（冷启动锚点 R7）。

服务层的规矩由 tests/services/test_reference_anchor.py 守；这里只确认用户碰到的那一层：
还没贴参考时是一个空读数（不是 404），改锚点需要带上版本号。
"""

import pytest

# u1 由 tests/api/conftest.py 的 autouse 夹具建好。


def _reference(title: str, tags: list[str], handle: str = "@某人") -> dict:
    return {"title": title, "tags": tags, "source_handle": handle}


@pytest.mark.asyncio
async def test_a_fresh_user_gets_an_empty_reading_not_a_404(client):
    """刚注册、还没贴参考是正常状态——前端据此渲染"贴 2–3 个你想做成的样子"。"""
    response = await client.get("/api/v2/reference-anchor")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["reference_count"] == 0
    assert data["topics"] == []
    assert data["audience"] is None


@pytest.mark.asyncio
async def test_the_reading_survives_a_reload_and_can_be_rewritten(client):
    imported = await client.post(
        "/api/v2/reference-imports",
        json={
            "method": "manual",
            "items": [
                _reference("12 平的出租屋，我按动线重排了三次", ["租房", "收纳"]),
                _reference("搬了四次家之后，我只留这些东西", ["租房", "收纳"]),
            ],
            "idempotency_key": "anchor-http-1",
        },
    )
    assert imported.status_code == 201

    # 模型不可用（测试环境 AI 关闭）→ 确定性读数：标签词频 + 表面写法。
    first = (await client.get("/api/v2/reference-anchor")).json()["data"]
    reloaded = (await client.get("/api/v2/reference-anchor")).json()["data"]

    assert first["reference_count"] == 2
    assert reloaded["version"] == first["version"]  # 参考集没变就不重推
    # 两个标签各出现在 2 条参考里，并列时按标签名排——确定性读法必须稳定可复现。
    assert [item["value"] for item in first["topics"]] == ["收纳", "租房"]
    assert [item["sample_count"] for item in first["topics"]] == [2, 2]
    assert first["capability"] == "deterministic_fallback"

    rewritten = await client.put(
        "/api/v2/reference-anchor",
        json={
            "topics": ["我自己定的方向"],
            "audience": "我想写给刚毕业的自己",
            "expected_version": first["version"],
        },
    )

    assert rewritten.status_code == 200
    data = rewritten.json()["data"]
    assert data["capability"] == "user_edited"
    assert [item["value"] for item in data["topics"]] == ["我自己定的方向"]
    assert data["audience"]["value"] == "我想写给刚毕业的自己"

    stale = await client.put(
        "/api/v2/reference-anchor",
        json={"topics": ["再改一次"], "expected_version": first["version"]},
    )

    assert stale.status_code == 409
    assert stale.json()["meta"]["details"]["current_version"] == data["version"]
