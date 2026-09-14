"""冷启动锚点：参考样本（别人的内容）的存储与隔离（R7）。

这里守的核心是一条不变式：**参考样本可以影响"你想做成什么样"，但绝不能进入
"你是谁"**。用户贴进来的是他仰慕的账号，不是他自己的作品；把两者混在一起，
系统就会拿别人的定位说"你的定位是……"，而这恰恰是冷启动阶段用户最无法反驳的谎言。
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.core.exceptions import IdempotencyConflictException
from app.models.v2.onboarding import (
    CreatorProfileUpdate,
    HistoryImportCreate,
    ReferenceNoteInput,
)
from app.services.content_opportunity import ContentOpportunityService
from app.services.creator_profile_v2 import CreatorProfileV2Service
from app.services.history_import import HistoryImportService

_HANDLE = "@想成为的样子"
_REFERENCE_NOTE = {
    "external_key": "ref-1",
    "title": "租房第一年，我把 12 平住成了两室",
    "body_excerpt": "先拆掉一件家具，再按动线重排。",
    "published_at": "2026-01-10T00:00:00Z",
    "tags": ["租房", "收纳"],
    "audience_questions": ["预算有限时应该先整理哪里？"],
}


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


def _body(item: dict, key: str) -> HistoryImportCreate:
    return HistoryImportCreate.model_validate(
        {"method": "manual", "items": [item], "idempotency_key": key}
    )


async def _import_reference(db, item: dict | None = None, key: str = "ref-import-1"):
    return await HistoryImportService(db).import_items(
        "u1",
        _body({**_REFERENCE_NOTE, **(item or {})}, key),
        origin="reference",
        item_model=ReferenceNoteInput,
    )


async def _rows(db, origin: str) -> list[dict]:
    return [
        dict(row)
        for row in await db.fetch_all(
            "SELECT * FROM imported_notes WHERE owner_user_id='u1' AND origin=:origin "
            "ORDER BY rowid",
            {"origin": origin},
        )
    ]


@pytest.mark.asyncio
async def test_reference_import_records_the_source_and_a_long_retention(test_db):
    await _insert_user(test_db)

    imported, replayed = await _import_reference(test_db, {"source_handle": _HANDLE})

    assert replayed is False
    assert imported["success_count"] == 1
    (row,) = await _rows(test_db, "reference")
    assert row["origin"] == "reference"
    assert row["source_handle"] == _HANDLE
    # 参考样本不随自有历史的 90 天隐私窗口过期：静默消失会让锚点凭空不见。
    assert row["retention_expires_at"] > (
        datetime.now(UTC) + timedelta(days=3000)
    ).isoformat().replace("+00:00", "Z")


@pytest.mark.asyncio
async def test_own_history_is_unchanged_by_the_new_dimension(test_db):
    """自有历史的语义、保留期、来源列都不变——这是向后兼容的那一半。"""
    await _insert_user(test_db)

    await HistoryImportService(test_db).import_items(
        "u1", _body({"title": "我自己的笔记", "tags": ["租房"]}, "self-import-1")
    )

    (row,) = await _rows(test_db, "self")
    assert row["source_handle"] is None
    assert row["retention_expires_at"] <= (
        datetime.now(UTC) + timedelta(days=91)
    ).isoformat().replace("+00:00", "Z")


@pytest.mark.asyncio
async def test_a_reference_row_without_a_source_is_rejected_on_its_own(test_db):
    """来源是参考样本的必填项：说不出"这是谁"，这条证据就无从追溯。"""
    await _insert_user(test_db)

    imported, _ = await HistoryImportService(test_db).import_items(
        "u1",
        _body(
            {"title": "没有来源的一条", "tags": ["租房"]},
            "ref-missing-source",
        ),
        origin="reference",
        item_model=ReferenceNoteInput,
    )

    assert imported["status"] == "failed"
    assert [item["status"] for item in imported["item_results"]] == ["failed"]
    assert await _rows(test_db, "reference") == []


@pytest.mark.asyncio
async def test_reference_samples_never_reach_the_creator_profile(test_db):
    """只有参考样本时，"你是谁"仍然是空的——不是别人的样子。"""
    await _insert_user(test_db)
    await _import_reference(test_db, {"source_handle": _HANDLE})

    profile = await CreatorProfileV2Service(test_db).get_or_build("u1")

    assert profile["attributes"]["content_pillars"] == []
    assert profile["attributes"]["niche"]["value"] == ""
    assert profile["attributes"]["target_audience"]["value"] == ""


@pytest.mark.asyncio
async def test_reference_samples_never_become_first_party_opportunities(test_db):
    """对照实验：同样的文本，作为参考样本不产生"历史衍生"机会，作为自有历史才会。"""
    await _insert_user(test_db)
    await _import_reference(test_db, {"source_handle": _HANDLE})
    profile_service = CreatorProfileV2Service(test_db)
    proposed = await profile_service.get_or_build("u1")
    await profile_service.update(
        "u1",
        CreatorProfileUpdate(
            niche="小空间居住",
            target_audience="第一次租房的人",
            growth_goal="stable_publish",
            content_pillars=["租房"],
            confirm=True,
            expected_version=proposed["version"],
        ),
    )
    service = ContentOpportunityService(test_db)

    from_references = await service.generate("u1")
    assert [item for item in from_references if item["source_ref"].startswith("imported-note:")] == []

    # 同一篇内容作为"我发过的"进来时，它就该出现——证明上面那条不是因为其它原因而空。
    await HistoryImportService(test_db).import_items(
        "u1", _body({**_REFERENCE_NOTE, "external_key": "mine-1"}, "self-import-2")
    )
    from_own_history = await service.generate("u1")

    assert [item for item in from_own_history if item["source_ref"].startswith("imported-note:")]


@pytest.mark.asyncio
async def test_the_same_text_may_be_both_mine_and_a_reference(test_db):
    """去重按来源区分：同一篇内容既是"我发过的"又是"我想做成这样"，是两条事实。"""
    await _insert_user(test_db)

    await HistoryImportService(test_db).import_items(
        "u1", _body({**_REFERENCE_NOTE, "source_handle": None}, "self-import-3")
    )
    await _import_reference(test_db, {"source_handle": _HANDLE}, key="ref-import-2")

    self_rows = await _rows(test_db, "self")
    reference_rows = await _rows(test_db, "reference")
    # 两条并存。文本完全相同，靠的是"来源参与内容身份"：imported_notes 的唯一键是
    # (owner_user_id, source_hash)，若来源不并入哈希，这次插入会被数据库拒绝。
    assert len(self_rows) == 1
    assert len(reference_rows) == 1
    assert self_rows[0]["source_hash"] != reference_rows[0]["source_hash"]


@pytest.mark.asyncio
async def test_reusing_an_idempotency_key_across_origins_conflicts(test_db):
    """同一个幂等键被用在两种来源上时明确报冲突，而不是把旧结果当成新操作回放。"""
    await _insert_user(test_db)

    await HistoryImportService(test_db).import_items(
        "u1", _body({"title": _REFERENCE_NOTE["title"]}, "shared-key")
    )

    with pytest.raises(IdempotencyConflictException):
        await _import_reference(test_db, key="shared-key")
