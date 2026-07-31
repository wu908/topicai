"""Behavior tests for evidence-backed, user-correctable creator profiles."""

import pytest

from app.models.v2.onboarding import (
    CreatorProfileUpdate,
    HistoryImportCreate,
)
from app.services.creator_profile_v2 import CreatorProfileV2Service
from app.services.history_import import HistoryImportService


async def _insert_user(db, user_id: str = "u1") -> None:
    await db.insert(
        "users",
        {
            "id": user_id,
            "email": f"{user_id}@test.com",
            "username": user_id,
            "password_hash": "hash",
            "ai_calls_today": 0,
            "ai_calls_reset_at": "",
            "created_at": "2026-07-31T00:00:00Z",
        },
    )


@pytest.mark.asyncio
async def test_profile_inference_exposes_evidence_and_preserves_rejections(test_db):
    await _insert_user(test_db)
    notes = [
        {
            "external_key": f"note-{index}",
            "title": f"第 {index} 篇小空间预算记录",
            "body_excerpt": "真实记录租房、小空间和预算调整。",
            "tags": ["租房", "预算" if index < 7 else "收纳"],
        }
        for index in range(10)
    ]
    await HistoryImportService(test_db).import_items(
        "u1",
        HistoryImportCreate(method="json", items=notes, idempotency_key="profile-history"),
    )

    service = CreatorProfileV2Service(test_db)
    proposed = await service.get_or_build("u1")

    assert proposed["confirmation_state"] == "needs_review"
    assert proposed["attributes"]["niche"]["value"] == "租房"
    assert len(proposed["attributes"]["niche"]["evidence_refs"]) == 10
    assert proposed["attributes"]["content_pillars"][0]["status"] == "provisional"

    confirmed = await service.update(
        "u1",
        CreatorProfileUpdate(
            niche="小空间生活",
            target_audience="第一次独立租房的年轻人",
            growth_goal="stable_publish",
            content_pillars=["租房预算", "小空间收纳"],
            voice_traits=["具体", "克制"],
            avoid_traits=["夸大效果"],
            rejected=[{"field": "niche", "value": "租房"}],
            confirm=True,
            expected_version=proposed["version"],
        ),
    )

    assert confirmed["confirmation_state"] == "confirmed"
    assert confirmed["attributes"]["niche"]["value"] == "小空间生活"
    assert confirmed["attributes"]["niche"]["status"] == "confirmed"
    assert {item["value"] for item in confirmed["rejected_attributes"]} >= {"租房"}
    assert "租房" not in [item["value"] for item in confirmed["attributes"]["content_pillars"]]


@pytest.mark.asyncio
async def test_profile_with_insufficient_history_stays_provisional(test_db):
    await _insert_user(test_db)
    await HistoryImportService(test_db).import_items(
        "u1",
        HistoryImportCreate(
            method="manual",
            items=[{"title": "唯一一篇", "tags": ["写作"]}],
            idempotency_key="short-history",
        ),
    )

    profile = await CreatorProfileV2Service(test_db).get_or_build("u1")

    assert profile["confirmation_state"] == "provisional"
    assert profile["attributes"]["niche"]["status"] == "provisional"


@pytest.mark.asyncio
async def test_profile_refreshes_after_history_is_imported_after_first_read(test_db):
    await _insert_user(test_db)
    service = CreatorProfileV2Service(test_db)

    initial = await service.get_or_build("u1")
    assert initial["attributes"]["niche"]["value"] == ""

    await HistoryImportService(test_db).import_items(
        "u1",
        HistoryImportCreate(
            method="manual",
            items=[{"title": "budget note", "tags": ["budget"]}],
            idempotency_key="after-first-read",
        ),
    )

    refreshed = await service.get_or_build("u1")
    assert refreshed["attributes"]["niche"]["value"] == "budget"
    assert refreshed["attributes"]["niche"]["evidence_refs"]


@pytest.mark.asyncio
async def test_profile_actions_do_not_change_selected_product_mode(test_db):
    await _insert_user(test_db)
    await test_db.execute(
        "UPDATE users SET product_mode='starter' WHERE id=:owner", {"owner": "u1"}
    )

    service = CreatorProfileV2Service(test_db)
    profile = await service.get_or_build("u1")
    await service.update(
        "u1",
        CreatorProfileUpdate(
            niche="writing",
            target_audience="beginners",
            growth_goal="stable_publish",
            content_pillars=["practice"],
            confirm=True,
            expected_version=profile["version"],
        ),
    )

    user = await test_db.fetch_one(
        "SELECT product_mode FROM users WHERE id=:owner", {"owner": "u1"}
    )
    assert user["product_mode"] == "starter"


@pytest.mark.asyncio
async def test_rejected_pillar_is_removed_from_active_profile(test_db):
    await _insert_user(test_db)
    await HistoryImportService(test_db).import_items(
        "u1",
        HistoryImportCreate(
            method="manual",
            items=[{"title": "budget", "tags": ["budget", "storage"]}],
            idempotency_key="rejected-pillar",
        ),
    )
    service = CreatorProfileV2Service(test_db)
    proposed = await service.get_or_build("u1")

    confirmed = await service.update(
        "u1",
        CreatorProfileUpdate(
            niche="home",
            target_audience="renters",
            growth_goal="stable_publish",
            content_pillars=["budget", "storage"],
            rejected=[{"field": "content_pillar", "value": "budget"}],
            confirm=True,
            expected_version=proposed["version"],
        ),
    )

    assert [item["value"] for item in confirmed["attributes"]["content_pillars"]] == ["storage"]
    assert {item["value"] for item in confirmed["rejected_attributes"]} == {"budget"}
