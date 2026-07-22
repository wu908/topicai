"""Service contracts for the bounded starter experiment."""

import pytest
from sqlalchemy import text

from app.models.v2.starter import (
    DirectionGenerate,
    DirectionSelect,
    StarterAssessmentCreate,
    StarterSprintReview,
)
from app.services.direction_candidate import DirectionCandidateService
from app.services.intent_orchestrator import IntentOrchestratorService
from app.services.starter_assessment import StarterAssessmentService
from app.services.starter_sprint import StarterSprintService


async def insert_user(db, user_id: str = "starter-user") -> None:
    await db.execute(
        "INSERT INTO users (id,email,username,password_hash,ai_calls_today,"
        "ai_calls_reset_at,created_at) VALUES "
        "(:id,:email,'Starter','hash',0,'','2026-07-22T00:00:00Z')",
        {"id": user_id, "email": f"{user_id}@example.com"},
    )


def assessment(**overrides) -> StarterAssessmentCreate:
    values = {
        "motivation": "curious",
        "available_hours_per_week": 3,
        "publish_commitment": True,
        "accept_experiment": True,
        "experience_assets": ["从零学习手冲咖啡的三个月"],
        "interest_assets": ["家庭咖啡"],
        "skill_assets": ["把复杂步骤整理成清单"],
        "privacy_limits": [],
        "idempotency_key": "assessment-1",
    }
    values.update(overrides)
    return StarterAssessmentCreate(**values)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"available_hours_per_week": 0}, "paused"),
        ({"publish_commitment": False}, "paused"),
        ({"accept_experiment": False}, "paused"),
        (
            {
                "experience_assets": [],
                "interest_assets": [],
                "skill_assets": [],
            },
            "not_ready",
        ),
        ({}, "ready"),
    ],
)
async def test_readiness_is_bounded_by_action_and_real_assets(test_db, overrides, expected):
    await insert_user(test_db)
    saved, _ = await StarterAssessmentService(test_db).submit(
        "starter-user", assessment(**overrides)
    )
    assert saved["readiness"] == expected


@pytest.mark.asyncio
async def test_privacy_limits_remove_assets_from_readiness_and_directions(test_db):
    await insert_user(test_db)
    saved, _ = await StarterAssessmentService(test_db).submit(
        "starter-user",
        assessment(
            experience_assets=["离职恢复过程"],
            interest_assets=[],
            skill_assets=[],
            privacy_limits=["离职"],
        ),
    )
    assert saved["readiness"] == "not_ready"
    with pytest.raises(ValueError, match="not ready"):
        await DirectionCandidateService(test_db).generate(
            "starter-user",
            DirectionGenerate(
                expected_assessment_version=saved["version"],
                idempotency_key="directions-private",
            ),
        )


@pytest.mark.asyncio
async def test_directions_are_grounded_bounded_and_do_not_make_growth_claims(test_db):
    await insert_user(test_db)
    saved, _ = await StarterAssessmentService(test_db).submit(
        "starter-user", assessment()
    )
    candidates, replayed = await DirectionCandidateService(test_db).generate(
        "starter-user",
        DirectionGenerate(
            expected_assessment_version=saved["version"],
            idempotency_key="directions-1",
        ),
    )
    assert replayed is False
    assert 1 <= len(candidates) <= 3
    assert all(len(item["first_three_topics"]) == 3 for item in candidates)
    assert all(item["evidence_refs"] for item in candidates)
    serialized = str(candidates)
    for prohibited in ("爆款", "保证", "永久定位", "涨粉", "变现", "流量密码"):
        assert prohibited not in serialized

    replay, was_replayed = await DirectionCandidateService(test_db).generate(
        "starter-user",
        DirectionGenerate(
            expected_assessment_version=saved["version"],
            idempotency_key="directions-1",
        ),
    )
    assert was_replayed is True
    assert [item["id"] for item in replay] == [item["id"] for item in candidates]


@pytest.mark.asyncio
async def test_selection_creates_exactly_three_existing_action_projects_idempotently(test_db):
    await insert_user(test_db)
    saved, _ = await StarterAssessmentService(test_db).submit(
        "starter-user", assessment()
    )
    candidates, _ = await DirectionCandidateService(test_db).generate(
        "starter-user",
        DirectionGenerate(
            expected_assessment_version=saved["version"],
            idempotency_key="directions-1",
        ),
    )
    command = DirectionSelect(
        expected_direction_version=candidates[0]["version"],
        idempotency_key="sprint-1",
    )
    workspace, replayed = await StarterSprintService(test_db).select_direction(
        "starter-user", candidates[0]["id"], command
    )
    assert replayed is False
    assert len(workspace["projects"]) == 3
    assert {item["starter_sprint_id"] for item in workspace["projects"]} == {
        workspace["sprint"]["id"]
    }
    assert all(item["primary_goal"] == "experiment" for item in workspace["projects"])

    action_types = []
    for project in workspace["projects"]:
        action = await IntentOrchestratorService(test_db).ensure_project_action(
            "starter-user", project["id"]
        )
        action_types.append(action["action_type"])
    assert action_types == ["confirm_intent", "confirm_intent", "confirm_intent"]

    replay, was_replayed = await StarterSprintService(test_db).select_direction(
        "starter-user", candidates[0]["id"], command
    )
    assert was_replayed is True
    assert [item["id"] for item in replay["projects"]] == [
        item["id"] for item in workspace["projects"]
    ]


@pytest.mark.asyncio
async def test_long_asset_still_creates_projects_with_valid_titles(test_db):
    await insert_user(test_db)
    saved, _ = await StarterAssessmentService(test_db).submit(
        "starter-user",
        assessment(
            experience_assets=["一" * 200],
            interest_assets=[],
            skill_assets=[],
        ),
    )
    candidates, _ = await DirectionCandidateService(test_db).generate(
        "starter-user",
        DirectionGenerate(
            expected_assessment_version=saved["version"],
            idempotency_key="directions-long-title",
        ),
    )
    workspace, _ = await StarterSprintService(test_db).select_direction(
        "starter-user",
        candidates[0]["id"],
        DirectionSelect(
            expected_direction_version=candidates[0]["version"],
            idempotency_key="sprint-long-title",
        ),
    )
    assert all(len(project["title"]) <= 200 for project in workspace["projects"])


@pytest.mark.asyncio
async def test_review_requires_a_real_publication_and_stays_experimental(test_db):
    await insert_user(test_db)
    assessment_row, _ = await StarterAssessmentService(test_db).submit(
        "starter-user", assessment()
    )
    candidates, _ = await DirectionCandidateService(test_db).generate(
        "starter-user",
        DirectionGenerate(
            expected_assessment_version=assessment_row["version"],
            idempotency_key="directions-1",
        ),
    )
    workspace, _ = await StarterSprintService(test_db).select_direction(
        "starter-user",
        candidates[0]["id"],
        DirectionSelect(
            expected_direction_version=candidates[0]["version"],
            idempotency_key="sprint-1",
        ),
    )
    sprint = workspace["sprint"]
    review = StarterSprintReview(
        observed_summary="第一篇已发布，继续观察哪类表达更容易完成。",
        blocker_reasons=["封面制作耗时"],
        next_topics=["继续测试过程记录"],
        expected_sprint_version=sprint["version"],
        idempotency_key="review-1",
    )
    with pytest.raises(ValueError, match="publication"):
        await StarterSprintService(test_db).review("starter-user", sprint["id"], review)

    await test_db.execute(
        "UPDATE content_projects SET status='published' WHERE id=:id",
        {"id": workspace["projects"][0]["id"]},
    )
    reviewed, replayed = await StarterSprintService(test_db).review(
        "starter-user", sprint["id"], review
    )
    assert replayed is False
    assert reviewed["sprint"]["graduation_state"] == "graduated"
    assert reviewed["sprint"]["published_count"] == 1
    assert "永久" not in reviewed["sprint"]["review_summary"]
