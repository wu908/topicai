"""Behavior tests for idempotent, partial historical-note imports."""

import pytest
from pydantic import ValidationError

from app.core.exceptions import IdempotencyConflictException
from app.models.v2.onboarding import HistoryImportCreate
from app.services.history_import import HistoryImportService


def test_history_import_caps_batches_at_200_items():
    with pytest.raises(ValidationError):
        HistoryImportCreate(
            method="manual",
            items=[{"title": f"note-{index}"} for index in range(201)],
            idempotency_key="too-many",
        )


@pytest.mark.asyncio
async def test_history_import_keeps_valid_items_and_deduplicates_retries(test_db):
    await test_db.insert(
        "users",
        {
            "id": "u1",
            "email": "u1@test.com",
            "username": "UserOne",
            "password_hash": "hash",
            "ai_calls_today": 0,
            "ai_calls_reset_at": "",
            "created_at": "2026-07-31T00:00:00Z",
        },
    )
    body = HistoryImportCreate.model_validate(
        {
            "method": "manual",
            "items": [
                {
                    "external_key": "note-1",
                    "title": "租房第一年，我用表格把生活费降了两成",
                    "body_excerpt": "记录预算方法和实际调整。",
                    "published_at": "2026-01-10T00:00:00Z",
                    "tags": ["租房", "预算"],
                },
                {"external_key": "broken", "title": "   "},
            ],
            "idempotency_key": "history-import-1",
        }
    )

    imported, replayed = await HistoryImportService(test_db).import_items("u1", body)

    assert replayed is False
    assert imported["success_count"] == 1
    assert imported["failure_count"] == 1
    assert [item["status"] for item in imported["item_results"]] == [
        "imported",
        "failed",
    ]

    replay, replayed = await HistoryImportService(test_db).import_items("u1", body)
    assert replayed is True
    assert replay["id"] == imported["id"]

    retried, replayed = await HistoryImportService(test_db).import_items(
        "u1",
        body.model_copy(update={"idempotency_key": "history-import-2"}),
    )
    assert replayed is False
    assert retried["item_results"][0]["status"] == "duplicate"
    assert retried["success_count"] == 1


@pytest.mark.asyncio
async def test_history_import_rejects_idempotency_key_reuse_with_new_payload(test_db):
    await test_db.insert(
        "users",
        {
            "id": "u1",
            "email": "u1@test.com",
            "username": "UserOne",
            "password_hash": "hash",
            "ai_calls_today": 0,
            "ai_calls_reset_at": "",
            "created_at": "2026-07-31T00:00:00Z",
        },
    )
    service = HistoryImportService(test_db)
    original = HistoryImportCreate.model_validate(
        {
            "method": "json",
            "items": [{"title": "第一篇", "body_excerpt": "正文"}],
            "idempotency_key": "same-key",
        }
    )
    await service.import_items("u1", original)

    changed = HistoryImportCreate.model_validate(
        {
            "method": "json",
            "items": [{"title": "另一篇", "body_excerpt": "不同正文"}],
            "idempotency_key": "same-key",
        }
    )
    with pytest.raises(IdempotencyConflictException):
        await service.import_items("u1", changed)


@pytest.mark.asyncio
async def test_history_import_itemizes_schema_validation_failures(test_db):
    await test_db.insert(
        "users",
        {
            "id": "u1",
            "email": "u1@test.com",
            "username": "UserOne",
            "password_hash": "hash",
            "ai_calls_today": 0,
            "ai_calls_reset_at": "",
            "created_at": "2026-07-31T00:00:00Z",
        },
    )
    body = HistoryImportCreate(
        method="json",
        items=[
            {"title": "valid"},
            {},
            {"title": "x" * 201},
        ],
        idempotency_key="schema-errors",
    )

    imported, _ = await HistoryImportService(test_db).import_items("u1", body)

    assert imported["success_count"] == 1
    assert imported["failure_count"] == 2
    assert [item["status"] for item in imported["item_results"]] == [
        "imported",
        "failed",
        "failed",
    ]
