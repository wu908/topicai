"""Deterministic builders for a fully published content project."""

from datetime import UTC, datetime, timedelta

from app.models.v2.calibration import PublishRecordCreate
from app.models.v2.content_project import ContentProjectCreate, ContentVersionCreate
from app.models.v2.intent_actions import HumanGateDecision
from app.models.v2.publish_hypothesis import PublishHypothesisLock
from app.services.content_project import ContentProjectService
from app.services.content_version import ContentVersionService
from app.services.intent_actions import HumanGateService
from app.services.intent_orchestrator import IntentOrchestratorService
from app.services.publication import PublicationService
from app.services.publish_hypothesis import PublishHypothesisService


async def insert_user(db, user_id: str = "loop-user") -> None:
    await db.execute(
        "INSERT INTO users (id,email,username,password_hash,ai_calls_today,"
        "ai_calls_reset_at,created_at) VALUES "
        "(:id,:email,:uname,'hash',0,'','2026-08-30T00:00:00Z')",
        {"id": user_id, "email": f"{user_id}@example.com", "uname": f"U{user_id}"},
    )


async def published_project(test_db, suffix: str, owner: str = "u1") -> dict:
    """Create -> version -> working intent -> hypothesis lock -> publish.

    published_at is dynamic (an hour ago) so date-window logic in consumers
    stays inside any reasonable observation window without hardcoding.
    """
    project, _ = await ContentProjectService(test_db).create(
        owner,
        ContentProjectCreate(
            title=f"系列 API 项目 {suffix}",
            target_audience="小红书知识创作者",
            content_intent="share",
            audience_change="读者持续看到创作者建立更新节奏",
            idempotency_key=f"api-series-project-{suffix}",
        ),
    )
    version, _ = await ContentVersionService(test_db).create(
        owner,
        project["id"],
        ContentVersionCreate(
            title=f"系列内容 {suffix}",
            body_text="一段已经发布的真实创作经历，包含过程、变化和结果。",
            expected_project_version=project["version"],
            idempotency_key=f"api-series-version-{suffix}",
        ),
    )
    await test_db.execute(
        "UPDATE content_projects SET intent_status='working_confirmed' WHERE id=:id",
        {"id": project["id"]},
    )
    project = await ContentProjectService(test_db).get(owner, project["id"])
    await PublishHypothesisService(test_db).lock(
        owner,
        project["id"],
        PublishHypothesisLock(
            content_version_id=version["id"],
            content_intent="share",
            audience_change="读者持续看到创作者建立更新节奏",
            primary_response="follow",
            supporting_responses=[],
            basis_refs=[f"content-version:{version['id']}"],
            uncertainties=["读者是否期待下一篇"],
            observation_window_days=7,
            viewpoint_anchor="稳定更新来自真实过程而非临时决定",
            expected_project_version=project["version"],
            idempotency_key=f"api-series-hypothesis-{suffix}",
        ),
    )
    project = await ContentProjectService(test_db).get(owner, project["id"])
    action = await IntentOrchestratorService(test_db).ensure_project_action(owner, project["id"])
    gate = await HumanGateService(test_db).ensure_for_action(owner, action["id"])
    await HumanGateService(test_db).decide(
        owner,
        gate["id"],
        HumanGateDecision(
            decision="confirm",
            decision_payload={"public_scope": "public"},
            expected_gate_version=gate["version"],
            idempotency_key=f"api-series-scope-{suffix}",
        ),
    )
    published_at = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    await PublicationService(test_db).record(
        owner,
        project["id"],
        PublishRecordCreate(
            content_version_id=version["id"],
            publication_gate_id=gate["id"],
            note_url=f"https://www.xiaohongshu.com/explore/api-series-{suffix}",
            published_at=published_at,
            expected_project_version=project["version"],
            idempotency_key=f"api-series-publication-{suffix}",
        ),
    )
    return await ContentProjectService(test_db).get(owner, project["id"])
