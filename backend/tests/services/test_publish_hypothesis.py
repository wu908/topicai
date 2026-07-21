"""Service contracts for project/version/hypothesis persistence."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.models.v2.content_project import ContentProjectCreate, ContentVersionCreate
from app.models.v2.publish_hypothesis import PublishHypothesisLock
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


async def _project_and_version(db):
    project, _ = await ContentProjectService(db).create(
        "u1",
        ContentProjectCreate(
            title="把踩坑经验写成一篇笔记",
            primary_goal="stable_publish",
            target_audience="刚开始做知识型账号的人",
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
    project = await ContentProjectService(db).get("u1", project["id"])
    return project, version


@pytest.mark.asyncio
async def test_lock_hypothesis_and_version_atomically(seeded_db):
    project, version = await _project_and_version(seeded_db)
    request = PublishHypothesisLock(
        content_version_id=version["id"],
        audience_problem="不知道知识型账号第一篇该写什么",
        reader_promise="用三个真实踩坑案例给出可执行起步顺序",
        expected_behaviors=["save", "profile_visit"],
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
    assert result["project"]["locked_publish_version_id"] == version["id"]
    assert result["project"]["publish_hypothesis_id"] == result["hypothesis"]["id"]


@pytest.mark.asyncio
async def test_lock_is_idempotent_but_rejects_payload_reuse(seeded_db):
    project, version = await _project_and_version(seeded_db)
    request = PublishHypothesisLock(
        content_version_id=version["id"],
        audience_problem="不知道第一篇写什么",
        reader_promise="给出真实起步顺序",
        expected_behaviors=["save"],
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

    changed = request.model_copy(update={"reader_promise": "换一个承诺"})
    with pytest.raises(IdempotencyConflictException):
        await service.lock("u1", project["id"], changed)


@pytest.mark.asyncio
async def test_version_conflict_rolls_back_hypothesis(seeded_db):
    project, version = await _project_and_version(seeded_db)
    request = PublishHypothesisLock(
        content_version_id=version["id"],
        audience_problem="不知道第一篇写什么",
        reader_promise="给出真实起步顺序",
        expected_behaviors=["save"],
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
        audience_problem="所有者的判断",
        reader_promise="不向其他用户泄漏",
        expected_behaviors=["save"],
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
