"""Service contracts for project/version/hypothesis persistence."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.models.v2.content_project import ContentProjectCreate, ContentVersionCreate
from app.models.v2.publish_hypothesis import (
    PublishHypothesisAmendmentCreate,
    PublishHypothesisLock,
)
from app.services.content_project import ContentProjectService
from app.services.content_version import ContentVersionService
from app.services.publish_hypothesis import PublishHypothesisService


@pytest_asyncio.fixture
async def seeded_db(test_db):
    session = await test_db.get_session()
    async with session:
        await session.execute(
            text(
                "INSERT INTO users (id,email,username,password_hash,ai_calls_today,"
                "ai_calls_reset_at,created_at) VALUES "
                "('u1','u1@test.com','u1','hash',0,'','2026-07-18T00:00:00Z'),"
                "('u2','u2@test.com','u2','hash',0,'','2026-07-18T00:00:00Z')"
            )
        )
        await session.commit()
    return test_db


async def _project_and_version(db, *, content_intent="solve"):
    project, _ = await ContentProjectService(db).create(
        "u1",
        ContentProjectCreate(
            title="把踩坑经验写成一篇笔记",
            primary_goal="stable_publish",
            target_audience="刚开始做知识型账号的人",
            content_intent=content_intent,
            idempotency_key="project-1",
        ),
    )
    version, _ = await ContentVersionService(db).create(
        "u1",
        project["id"],
        ContentVersionCreate(
            title="我做知识型账号踩过的 3 个坑",
            body_text="第一，不要先追热点。第二，先保存真实案例。",
            expected_project_version=project["version"],
            idempotency_key="version-1",
        ),
    )
    await db.execute(
        "UPDATE content_projects SET intent_status='working_confirmed' WHERE id=:id",
        {"id": project["id"]},
    )
    project = await ContentProjectService(db).get("u1", project["id"])
    return project, version


@pytest.mark.asyncio
async def test_lock_hypothesis_and_version_atomically(seeded_db):
    project, version = await _project_and_version(seeded_db)
    request = PublishHypothesisLock(
        content_version_id=version["id"],
        content_intent="solve",
        audience_change="读者能够按真实经验开始第一篇内容",
        primary_response="save",
        supporting_responses=["profile_visit"],
        observation_window_days=7,
        audience_problem="不知道知识型账号第一篇该写什么",
        reader_promise="用三个真实踩坑案例给出可执行起步顺序",
        basis_refs=["user_fact:three-failures"],
        uncertainties=["收藏是否会转化为主页访问"],
        expected_project_version=project["version"],
        idempotency_key="hypothesis-1",
    )

    result, replayed = await PublishHypothesisService(seeded_db).lock(
        "u1", project["id"], request
    )

    assert replayed is False
    assert result["hypothesis"]["status"] == "locked"
    assert result["project"]["status"] == "ready_to_publish"
    assert result["project"]["intent_status"] == "locked"
    assert result["project"]["intent_locked_at"]
    assert result["project"]["locked_publish_version_id"] == version["id"]
    assert result["project"]["publish_hypothesis_id"] == result["hypothesis"]["id"]
    assert result["hypothesis"]["content_intent"] == "solve"
    assert result["hypothesis"]["audience_change"] == "读者能够按真实经验开始第一篇内容"
    assert result["hypothesis"]["primary_response"] == "save"
    assert result["hypothesis"]["supporting_responses_json"] == '["profile_visit"]'
    assert result["hypothesis"]["observation_window_days"] == 7


@pytest.mark.asyncio
async def test_share_lock_persists_viewpoint_without_solve_fields(seeded_db):
    project, version = await _project_and_version(
        seeded_db, content_intent="share"
    )
    result, _ = await PublishHypothesisService(seeded_db).lock(
        "u1",
        project["id"],
        PublishHypothesisLock(
            content_version_id=version["id"],
            content_intent="share",
            audience_change="读者理解一次真实经历带来的观点变化",
            primary_response="comment",
            supporting_responses=["follow"],
            basis_refs=["user_fact:first-post"],
            uncertainties=[],
            observation_window_days=14,
            viewpoint_anchor="这次经历让我停止追逐所有热点",
            expected_project_version=project["version"],
            idempotency_key="share-hypothesis",
        ),
    )

    assert result["hypothesis"]["viewpoint_anchor"] == "这次经历让我停止追逐所有热点"
    assert result["hypothesis"]["audience_problem"] == ""
    assert result["hypothesis"]["reader_promise"] == ""


@pytest.mark.asyncio
async def test_lock_requires_working_intent_confirmation(seeded_db):
    project, version = await _project_and_version(seeded_db)
    await seeded_db.execute(
        "UPDATE content_projects SET intent_status='candidate' WHERE id=:id",
        {"id": project["id"]},
    )
    body = PublishHypothesisLock(
        content_version_id=version["id"],
        content_intent="solve",
        audience_change="读者知道如何开始第一篇内容",
        primary_response="save",
        observation_window_days=7,
        audience_problem="不知道第一篇写什么",
        reader_promise="给出真实起步顺序",
        expected_project_version=project["version"],
        idempotency_key="candidate-lock",
    )

    with pytest.raises(ValueError, match="working confirmed"):
        await PublishHypothesisService(seeded_db).lock("u1", project["id"], body)


@pytest.mark.asyncio
async def test_lock_rejects_legacy_confirmed_row_with_lock_evidence(seeded_db):
    project, version = await _project_and_version(seeded_db)
    await seeded_db.execute(
        "UPDATE content_projects SET intent_status='confirmed',intent_locked_at=:locked "
        "WHERE id=:id",
        {"locked": "2026-07-26T00:00:00Z", "id": project["id"]},
    )
    body = PublishHypothesisLock(
        content_version_id=version["id"],
        content_intent="solve",
        audience_change="读者知道如何开始第一篇内容",
        primary_response="save",
        observation_window_days=7,
        audience_problem="不知道第一篇写什么",
        reader_promise="给出真实起步顺序",
        expected_project_version=project["version"],
        idempotency_key="legacy-locked-row",
    )

    with pytest.raises(ValueError, match="working confirmed"):
        await PublishHypothesisService(seeded_db).lock("u1", project["id"], body)


@pytest.mark.asyncio
async def test_post_lock_amendments_append_without_mutating_hypothesis(seeded_db):
    project, version = await _project_and_version(seeded_db)
    locked, _ = await PublishHypothesisService(seeded_db).lock(
        "u1",
        project["id"],
        PublishHypothesisLock(
            content_version_id=version["id"],
            content_intent="solve",
            audience_change="Original audience change",
            primary_response="save",
            observation_window_days=7,
            audience_problem="Original audience problem",
            reader_promise="Original promise",
            expected_project_version=project["version"],
            idempotency_key="amendment-lock",
        ),
    )
    hypothesis_id = locked["hypothesis"]["id"]
    service = PublishHypothesisService(seeded_db)
    body = PublishHypothesisAmendmentCreate(
        amendment_type="clarification",
        statement="This narrows the intended reader context.",
        reason="New context became available after lock.",
        idempotency_key="amendment-1",
    )

    amendment, replayed = await service.amend("u1", hypothesis_id, body)
    replay, was_replayed = await service.amend("u1", hypothesis_id, body)
    amendments = await service.list_amendments("u1", hypothesis_id)
    hypothesis = await seeded_db.fetch_one(
        "SELECT audience_problem,reader_promise FROM publish_hypotheses WHERE id=:id",
        {"id": hypothesis_id},
    )

    assert replayed is False
    assert was_replayed is True
    assert replay["id"] == amendment["id"]
    assert [item["statement"] for item in amendments] == [body.statement]
    assert hypothesis == {
        "audience_problem": "Original audience problem",
        "reader_promise": "Original promise",
    }
    with pytest.raises(ValueError, match="not found"):
        await service.amend("u2", hypothesis_id, body)


@pytest.mark.asyncio
async def test_lock_is_idempotent_but_rejects_payload_reuse(seeded_db):
    project, version = await _project_and_version(seeded_db)
    request = PublishHypothesisLock(
        content_version_id=version["id"],
        content_intent="solve",
        audience_change="读者知道如何开始第一篇内容",
        primary_response="save",
        observation_window_days=7,
        audience_problem="不知道第一篇写什么",
        reader_promise="给出真实起步顺序",
        basis_refs=["user_fact:first-post"],
        uncertainties=[],
        expected_project_version=project["version"],
        idempotency_key="hypothesis-retry",
    )
    service = PublishHypothesisService(seeded_db)

    first, first_replayed = await service.lock("u1", project["id"], request)
    second, second_replayed = await service.lock("u1", project["id"], request)

    assert first_replayed is False
    assert second_replayed is True
    assert second["hypothesis"]["id"] == first["hypothesis"]["id"]

    changed = request.model_copy(update={"audience_change": "换一个预期变化"})
    with pytest.raises(IdempotencyConflictException):
        await service.lock("u1", project["id"], changed)


@pytest.mark.asyncio
async def test_version_conflict_rolls_back_hypothesis(seeded_db):
    project, version = await _project_and_version(seeded_db)
    request = PublishHypothesisLock(
        content_version_id=version["id"],
        content_intent="solve",
        audience_change="读者知道如何开始第一篇内容",
        primary_response="save",
        observation_window_days=7,
        audience_problem="不知道第一篇写什么",
        reader_promise="给出真实起步顺序",
        basis_refs=[],
        uncertainties=[],
        expected_project_version=project["version"] - 1,
        idempotency_key="stale-hypothesis",
    )

    with pytest.raises(VersionConflictException):
        await PublishHypothesisService(seeded_db).lock("u1", project["id"], request)

    rows = await seeded_db.fetch_all(
        "SELECT id FROM publish_hypotheses WHERE project_id=:project_id",
        {"project_id": project["id"]},
    )
    assert rows == []


@pytest.mark.asyncio
async def test_project_owner_isolation(seeded_db):
    project, _ = await _project_and_version(seeded_db)

    with pytest.raises(ValueError, match="not found"):
        await ContentProjectService(seeded_db).get("u2", project["id"])


@pytest.mark.asyncio
async def test_idempotency_replay_is_owner_scoped(seeded_db):
    project, version = await _project_and_version(seeded_db)
    version_request = ContentVersionCreate(
        title="第二版",
        body_text="只有所有者可以回放这个版本。",
        expected_project_version=project["version"],
        idempotency_key="private-version-key",
    )
    await ContentVersionService(seeded_db).create(
        "u1", project["id"], version_request
    )

    with pytest.raises(ValueError, match="not found"):
        await ContentVersionService(seeded_db).create(
            "u2", project["id"], version_request
        )

    refreshed = await ContentProjectService(seeded_db).get("u1", project["id"])
    lock_request = PublishHypothesisLock(
        content_version_id=version["id"],
        content_intent="solve",
        audience_change="只有所有者能读取判断",
        primary_response="save",
        observation_window_days=7,
        audience_problem="所有者的判断",
        reader_promise="不向其他用户泄漏",
        expected_project_version=refreshed["version"],
        idempotency_key="private-hypothesis-key",
    )
    await PublishHypothesisService(seeded_db).lock(
        "u1", project["id"], lock_request
    )

    with pytest.raises(ValueError, match="not found"):
        await PublishHypothesisService(seeded_db).lock(
            "u2", project["id"], lock_request
        )
