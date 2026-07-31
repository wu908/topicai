"""HTTP journey for Growth onboarding, history import, and profile review."""

import pytest


@pytest.mark.asyncio
async def test_growth_onboarding_imports_partial_history_and_confirms_profile(client):
    context = await client.get("/api/v2/onboarding")
    assert context.json()["data"] == {
        "mode": "growth",
        "state": "not_started",
        "version": 1,
    }
    selected = await client.put(
        "/api/v2/onboarding/mode",
        json={"mode": "growth", "expected_version": 1},
    )
    assert selected.status_code == 200
    assert selected.json()["data"] == {
        "mode": "growth",
        "state": "in_progress",
        "version": 2,
    }

    imported = await client.post(
        "/api/v2/history-imports",
        json={
            "method": "manual",
            "items": [
                {"title": "租房预算复盘", "tags": ["租房", "预算"]},
                {"title": "   ", "tags": ["无效"]},
            ],
            "idempotency_key": "growth-api-import",
        },
    )
    assert imported.status_code == 201
    assert imported.json()["data"]["success_count"] == 1
    assert imported.json()["data"]["failure_count"] == 1

    proposed = await client.get("/api/v2/creator-profile")
    assert proposed.status_code == 200
    profile = proposed.json()["data"]
    assert profile["confirmation_state"] == "provisional"
    assert profile["attributes"]["niche"]["evidence_refs"]

    confirmed = await client.put(
        "/api/v2/creator-profile",
        json={
            "niche": "小空间生活",
            "target_audience": "第一次独立租房的年轻人",
            "growth_goal": "stable_publish",
            "content_pillars": ["租房预算", "小空间收纳"],
            "voice_traits": ["具体"],
            "avoid_traits": ["夸大效果"],
            "rejected": [{"field": "niche", "value": "租房"}],
            "confirm": True,
            "expected_version": profile["version"],
        },
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["data"]["confirmation_state"] == "confirmed"


@pytest.mark.asyncio
async def test_growth_profile_and_history_are_owner_scoped(client, client_as_u2):
    await client.post(
        "/api/v2/history-imports",
        json={
            "method": "json",
            "items": [{"title": "只属于 u1", "tags": ["私有主题"]}],
            "idempotency_key": "owner-history",
        },
    )

    owner_profile = (await client.get("/api/v2/creator-profile")).json()["data"]
    other_profile = (await client_as_u2.get("/api/v2/creator-profile")).json()["data"]

    assert owner_profile["attributes"]["niche"]["value"] == "私有主题"
    assert other_profile["attributes"]["niche"]["value"] == ""
