"""Behavior tests for first-party explainable opportunity generation."""

import json

import pytest

from app.models.v2.onboarding import CreatorProfileUpdate, HistoryImportCreate
from app.services.content_opportunity import ContentOpportunityService
from app.services.creator_profile_v2 import CreatorProfileV2Service
from app.services.creator_state import CreatorStateService
from app.services.history_import import HistoryImportService


async def _insert_user(db) -> None:
    await db.insert(
        "users",
        {
            "id": "u1",
            "email": "u1@test.com",
            "username": "u1",
            "password_hash": "hash",
            "ai_calls_today": 0,
            "ai_calls_reset_at": "",
            "created_at": "2026-07-31T00:00:00Z",
        },
    )


@pytest.mark.asyncio
async def test_generate_keeps_audience_questions_without_matching_note_tags(test_db):
    await _insert_user(test_db)
    await HistoryImportService(test_db).import_items(
        "u1",
        HistoryImportCreate(
            method="manual",
            items=[
                {
                    "title": "租房后的真实问题",
                    "tags": ["moving"],
                    "audience_questions": ["预算有限时应该先整理哪里？"],
                }
            ],
            idempotency_key="opportunity-question",
        ),
    )
    profile_service = CreatorProfileV2Service(test_db)
    proposed = await profile_service.get_or_build("u1")
    await profile_service.update(
        "u1",
        CreatorProfileUpdate(
            niche="small-space living",
            target_audience="first-time renters",
            growth_goal="stable_publish",
            content_pillars=["storage"],
            confirm=True,
            expected_version=proposed["version"],
        ),
    )

    generated = await ContentOpportunityService(test_db).generate("u1")

    question = next(
        item for item in generated if item["opportunity_type"] == "user_question"
    )
    assert question["proposed_title"] == "预算有限时应该先整理哪里？"
    assert question["source_ref"].startswith("imported-note:")
    trace = await test_db.fetch_one(
        "SELECT visibility_boundary_json FROM ai_traces_v2 WHERE id=:id",
        {"id": question["ai_trace_id"]},
    )
    assert "imported_history" in json.loads(trace["visibility_boundary_json"])[
        "actual"
    ]


@pytest.mark.asyncio
async def test_generate_uses_first_party_history_without_rejected_profile_attributes(test_db):
    await _insert_user(test_db)
    await HistoryImportService(test_db).import_items(
        "u1",
        HistoryImportCreate(
            method="manual",
            items=[
                {
                    "title": "一次真实的小空间调整",
                    "body_excerpt": "记录调整前后的实际过程。",
                    "tags": ["budget", "storage"],
                    "audience_questions": ["小空间应该先整理哪里？"],
                }
            ],
            idempotency_key="opportunity-history",
        ),
    )
    profile_service = CreatorProfileV2Service(test_db)
    proposed = await profile_service.get_or_build("u1")
    await profile_service.update(
        "u1",
        CreatorProfileUpdate(
            niche="small-space living",
            target_audience="first-time renters",
            growth_goal="stable_publish",
            content_pillars=["budget", "storage"],
            rejected=[{"field": "content_pillar", "value": "budget"}],
            confirm=True,
            expected_version=proposed["version"],
        ),
    )

    await test_db.execute(
        "UPDATE imported_notes SET retention_expires_at='2020-01-01T00:00:00Z' "
        "WHERE owner_user_id='u1'"
    )
    service = ContentOpportunityService(test_db)
    expired = await service.generate("u1")
    assert [item["opportunity_type"] for item in expired] == ["evergreen"]

    await test_db.execute(
        "UPDATE imported_notes SET retention_expires_at='2099-01-01T00:00:00Z',"
        "tags_json='[\"budget\"]' "
        "WHERE owner_user_id='u1'"
    )
    misaligned = await service.generate("u1")
    assert [item["opportunity_type"] for item in misaligned] == [
        "user_question",
        "evergreen",
    ]

    await test_db.execute(
        "UPDATE imported_notes SET tags_json='[\"storage\"]' WHERE owner_user_id='u1'"
    )
    await test_db.insert(
        "materials",
        {
            "id": "material-1",
            "owner_user_id": "u1",
            "name": "搬家前后收纳对比.pdf",
            "mime_type": "application/pdf",
            "kind": "document",
            "size": 128,
            "source_url": "/materials",
            "created_at": "2026-07-31T00:00:00Z",
            "updated_at": "2026-07-31T00:00:00Z",
        },
    )
    await CreatorStateService(test_db).append_validated_insight(
        "u1",
        {
            "statement": "先展示失败现场，再解释调整动作，更容易让读者理解",
            "source_ref": "observation:confirmed-1",
            "source_type": "validated_insight",
        },
    )
    generated = await service.generate("u1")

    assert [item["opportunity_type"] for item in generated] == [
        "history_derivative",
        "user_question",
        "material_derivative",
        "insight_derivative",
        "evergreen",
    ]
    assert generated[0]["source_ref"].startswith("imported-note:")
    history_source = generated[0]["source_refs"][0]
    assert history_source["ref_type"] == "imported_note"
    assert history_source["entity_id"]
    assert history_source["excerpt"] == "记录调整前后的实际过程。"
    assert history_source["verification_state"] == "verified"
    assert {
        "ref_type",
        "entity_id",
        "url",
        "publisher",
        "published_at",
        "collected_at",
        "title",
        "excerpt",
        "verification_state",
        "rights_note",
    } == set(history_source)
    assert generated[0]["dimensions"]["creator_fit"] == "strong"
    assert generated[0]["dimensions"]["material_readiness"] == "ready"
    assert generated[2]["source_ref"] == "material:material-1"
    assert generated[2]["dimensions"]["audience_fit"] == "unknown"
    assert generated[2]["dimensions"]["creator_fit"] == "unknown"
    assert generated[2]["dimensions"]["material_readiness"] == "partial"
    assert generated[3]["evidence_refs"] == ["observation:confirmed-1"]
    assert generated[4]["dimensions"]["timeliness"] == "evergreen"
    candidate_text = " ".join(
        str(item[field])
        for item in generated
        for field in ("proposed_title", "proposed_rationale", "dimensions")
    )
    assert "budget" not in candidate_text
