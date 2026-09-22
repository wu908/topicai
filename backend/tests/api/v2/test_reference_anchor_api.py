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


@pytest.mark.asyncio
async def test_tagless_references_still_return_a_reading_not_a_400(client):
    """F25 回归（用户验收测试 2026-09-19）。

    真实前端的 parseReferences 给每条参考都写 ``tags: []``——上面那些用例都带标签，
    所以这条真实路径从未被测过。修复前它会返回 400，且 message 是一段英文 pydantic
    原文（`1 validation error for _AnchorDraft topics ...`），用户完全无法理解。
    """
    imported = await client.post(
        "/api/v2/reference-imports",
        json={
            "method": "manual",
            "items": [
                {"title": "12 平的出租屋，我按动线重排了三次", "tags": [], "source_handle": "@甲"},
                {"title": "搬了四次家之后，我只留这些东西", "tags": [], "source_handle": "@乙"},
            ],
            "idempotency_key": "anchor-http-tagless",
        },
    )
    assert imported.status_code == 201

    response = await client.get("/api/v2/reference-anchor")

    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert data["reference_count"] == 2
    # 没有标签时退到参考标题，仍然给得出可核对的选题。
    assert [item["value"] for item in data["topics"]] == [
        "12 平的出租屋，我按动线重排了三次",
        "搬了四次家之后，我只留这些东西",
    ]
    # 用户可见文案里不得出现 pydantic / 内部模型名。
    assert "pydantic" not in body["message"].lower()
    assert "_AnchorDraft" not in body["message"]
