"""设置契约：agent_identity / product_prefs 持久化。"""

from app.models.v2.settings import AgentIdentityPrefs, ProductPrefs


async def test_settings_roundtrip_agent_and_product_prefs(client):
    got = await client.get("/api/v2/settings")
    assert got.status_code == 200
    data = got.json()["data"]
    version = data["version"]

    update = await client.put(
        "/api/v2/settings",
        json={
            "expected_version": version,
            "agent_identity": {
                "global_name": "阿洛",
                "project_name": "项目助手",
                "global_agent_md": "称呼我为小K",
            },
            "product_prefs": {
                "default_content_kind": "graphic_note",
                "memory_write_mode": "propose",
                "retro_reminder_days": 3,
            },
        },
    )
    assert update.status_code == 200
    body = update.json()["data"]
    assert body["agent_identity"]["global_name"] == "阿洛"
    assert body["agent_identity"]["project_name"] == "项目助手"
    assert body["agent_identity"]["global_agent_md"] == "称呼我为小K"
    assert body["product_prefs"]["default_content_kind"] == "graphic_note"
    assert body["product_prefs"]["memory_write_mode"] == "propose"
    assert body["product_prefs"]["retro_reminder_days"] == 3

    again = await client.get("/api/v2/settings")
    assert again.status_code == 200
    persisted = again.json()["data"]
    assert persisted["agent_identity"]["global_name"] == "阿洛"
    assert persisted["product_prefs"]["retro_reminder_days"] == 3


def test_agent_identity_model_strips_none():
    prefs = AgentIdentityPrefs(global_name="A", project_name=None)
    assert prefs.model_dump(exclude_none=True) == {"global_name": "A"}
    product = ProductPrefs(memory_write_mode="manual")
    assert product.model_dump(exclude_none=True) == {"memory_write_mode": "manual"}
