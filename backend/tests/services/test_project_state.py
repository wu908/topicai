import pytest
import pytest_asyncio

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.models.v2.content_project import ContentProjectCreate, ProjectTransition
from app.services.content_project import ContentProjectService
from app.services.project_state import ProjectStateService


@pytest_asyncio.fixture
async def project_db(test_db):
    await test_db.execute(
        "INSERT INTO users (id,email,username,password_hash,ai_calls_today,"
        "ai_calls_reset_at,created_at) VALUES "
        "('u1','u1@test.com','u1','hash',0,'','2026-07-31T00:00:00Z')"
    )
    return test_db


@pytest.mark.asyncio
async def test_transition_appends_one_event_and_replays(project_db):
    project, _ = await ContentProjectService(project_db).create(
        "u1",
        ContentProjectCreate(
            title="Audit this project",
            target_audience="Creators",
            idempotency_key="project-state-project",
        ),
    )
    command = ProjectTransition(
        to_status="creating",
        reason="brief_baseline_saved",
        expected_version=project["version"],
        idempotency_key="project-state-transition",
    )

    result, replayed = await ProjectStateService(project_db).transition(
        "u1", project["id"], command
    )
    replay, replayed_again = await ProjectStateService(project_db).transition(
        "u1", project["id"], command
    )

    assert replayed is False
    assert replayed_again is True
    assert result == replay
    assert result["project"]["status"] == "creating"
    assert result["project"]["version"] == 2
    assert result["event"]["from_status"] == "preparing"
    assert result["event"]["to_status"] == "creating"
    assert result["event"]["reason"] == "brief_baseline_saved"
    assert result["event"]["actor_type"] == "user"
    assert result["event"]["project_version"] == 2
    assert await project_db.fetch_one(
        "SELECT COUNT(*) AS count FROM project_state_events WHERE project_id=:project",
        {"project": project["id"]},
    ) == {"count": 1}


@pytest.mark.asyncio
async def test_transition_enforces_owner_version_and_canonical_graph(project_db):
    project, _ = await ContentProjectService(project_db).create(
        "u1",
        ContentProjectCreate(
            title="Guard this project",
            target_audience="Creators",
            idempotency_key="project-state-guards",
        ),
    )

    with pytest.raises(ValueError, match="project not found"):
        await ProjectStateService(project_db).transition(
            "u2",
            project["id"],
            ProjectTransition(
                to_status="ready_to_publish",
                reason="publish_hypothesis_locked",
                expected_version=project["version"],
                idempotency_key="wrong-owner",
            ),
        )
    with pytest.raises(VersionConflictException):
        await ProjectStateService(project_db).transition(
            "u1",
            project["id"],
            ProjectTransition(
                to_status="ready_to_publish",
                reason="publish_hypothesis_locked",
                expected_version=project["version"] + 1,
                idempotency_key="stale-version",
            ),
        )
    with pytest.raises(ValueError, match="owning workflow"):
        await ProjectStateService(project_db).transition(
            "u1",
            project["id"],
            ProjectTransition(
                to_status="ready_to_publish",
                reason="bypass_publish_hypothesis",
                expected_version=project["version"],
                idempotency_key="invalid-edge",
            ),
        )

    await project_db.execute(
        "UPDATE content_projects SET status='published' WHERE id=:id",
        {"id": project["id"]},
    )
    published = await ContentProjectService(project_db).get("u1", project["id"])
    with pytest.raises(ValueError, match="owning workflow"):
        await ProjectStateService(project_db).transition(
            "u1",
            project["id"],
            ProjectTransition(
                to_status="creating",
                reason="forbidden_post_publication_rollback",
                expected_version=published["version"],
                idempotency_key="post-publication-rollback",
            ),
        )


@pytest.mark.asyncio
async def test_transition_rejects_idempotency_key_reuse_with_new_payload(project_db):
    project, _ = await ContentProjectService(project_db).create(
        "u1",
        ContentProjectCreate(
            title="Protect transition replay",
            target_audience="Creators",
            idempotency_key="project-state-conflict",
        ),
    )
    service = ProjectStateService(project_db)
    await service.transition(
        "u1",
        project["id"],
        ProjectTransition(
            to_status="creating",
            reason="brief_baseline_saved",
            expected_version=project["version"],
            idempotency_key="reused-transition-key",
        ),
    )

    with pytest.raises(IdempotencyConflictException):
        await service.transition(
            "u1",
            project["id"],
            ProjectTransition(
                to_status="creating",
                reason="different_reason",
                expected_version=project["version"],
                idempotency_key="reused-transition-key",
            ),
        )
