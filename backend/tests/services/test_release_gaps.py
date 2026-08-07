"""Contracts for the remaining Spec-008 release-critical services."""

import base64

import pytest
import pytest_asyncio

from app.models.v2.calibration import PublishRecordCreate
from app.models.v2.content_project import ContentProjectCreate, ContentVersionCreate
from app.models.v2.material import MaterialCreate, MaterialUpdate, MaterialUsageCreate
from app.models.v2.publish_check import PublishCheckCreate, PublishCheckResolution
from app.models.v2.settings import UserSettingsUpdate
from app.models.v2.snapshot_extraction import SnapshotExtractionCreate
from app.services.content_project import ContentProjectService
from app.services.content_version import ContentVersionService
from app.services.material import MaterialService
from app.services.publication import PublicationService
from app.services.publish_check import PublishCheckService
from app.services.settings import UserSettingsService
from app.services.snapshot_extraction import SnapshotExtractionService


@pytest_asyncio.fixture(autouse=True)
async def _seed_owner(test_db):
    await test_db.execute(
        "INSERT INTO users (id,email,username,password_hash,ai_calls_today,"
        "ai_calls_reset_at,created_at) VALUES ('u1','u1@test.com','u1','hash',0,'',"
        "'2026-08-06T00:00:00Z')"
    )


async def _project_with_version(db, suffix: str, body_text: str = "A first-party note."):
    project, _ = await ContentProjectService(db).create(
        "u1",
        ContentProjectCreate(
            title=f"Release gap {suffix}",
            target_audience="Knowledge creators",
            idempotency_key=f"project-{suffix}",
        ),
    )
    version, _ = await ContentVersionService(db).create(
        "u1",
        project["id"],
        ContentVersionCreate(
            title="A concrete title",
            body_text=body_text,
            cover_plan="Use a real process image.",
            image_plan=[
                {"order": 1, "description": "Step one"},
                {"order": 2, "description": "Step two"},
            ],
            expected_project_version=project["version"],
            idempotency_key=f"version-{suffix}",
        ),
    )
    return await ContentProjectService(db).get("u1", project["id"]), version


@pytest.mark.asyncio
async def test_material_crud_usage_and_locked_reference_snapshot(test_db):
    project, version = await _project_with_version(test_db, "material")
    service = MaterialService(test_db)
    material, replayed = await service.create(
        "u1",
        MaterialCreate(
            kind="text",
            title="Failed launch notes",
            content="What failed, what changed, and the observed result.",
            privacy_level="private",
            project_id=project["id"],
            idempotency_key="material-create",
        ),
    )
    assert replayed is False
    assert material["content"] == "What failed, what changed, and the observed result."
    assert material["usages"][0]["project_id"] == project["id"]
    assert set(material) == {
        "id",
        "title",
        "kind",
        "mime_type",
        "size",
        "content",
        "privacy_level",
        "version",
        "usages",
        "created_at",
        "updated_at",
    }

    replay, replayed = await service.create(
        "u1",
        MaterialCreate(
            kind="text",
            title="Failed launch notes",
            content="What failed, what changed, and the observed result.",
            privacy_level="private",
            project_id=project["id"],
            idempotency_key="material-create",
        ),
    )
    assert replayed is True
    assert replay["id"] == material["id"]

    updated = await service.update(
        "u1",
        material["id"],
        MaterialUpdate(
            title="Launch notes",
            privacy_level="sensitive",
            expected_version=material["version"],
        ),
    )
    assert updated["privacy_level"] == "sensitive"

    other_project, _ = await _project_with_version(test_db, "material-reuse")
    linked, replayed = await service.add_usage(
        "u1",
        material["id"],
        MaterialUsageCreate(
            project_id=other_project["id"],
            idempotency_key="material-reuse",
        ),
    )
    assert replayed is False
    assert {item["project_id"] for item in linked["usages"]} == {
        project["id"],
        other_project["id"],
    }

    await test_db.execute(
        "UPDATE content_projects SET locked_publish_version_id=:version WHERE id=:project",
        {"version": version["id"], "project": project["id"]},
    )
    stored_before = await test_db.fetch_one(
        "SELECT evidence_snapshot_json FROM content_versions WHERE id=:id",
        {"id": version["id"]},
    )
    impact = await service.deletion_impact("u1", material["id"])
    assert impact["locked_version_ids"] == [version["id"]]
    await service.delete("u1", material["id"], confirmed=True)
    stored = await test_db.fetch_one(
        "SELECT evidence_snapshot_json FROM content_versions WHERE id=:id",
        {"id": version["id"]},
    )
    assert stored["evidence_snapshot_json"] == stored_before["evidence_snapshot_json"]
    assert await test_db.fetch_one(
        "SELECT id FROM materials WHERE id=:id", {"id": material["id"]}
    ) is None


@pytest.mark.asyncio
async def test_settings_update_is_versioned_and_hides_credentials(test_db, monkeypatch):
    service = UserSettingsService(test_db)
    initial = await service.get("u1")
    assert initial["weekly_publish_goal"] == 2
    assert initial["ai"]["configured"] is False
    assert "api_key" not in initial["ai"]

    updated = await service.update(
        "u1",
        UserSettingsUpdate(
            weekly_publish_goal=3,
            content_strategy="Publish one evidence-backed series each week.",
            xiaohongshu_account_reference="creator-note-account",
            consent={"history_analysis": True},
            expected_version=initial["version"],
        ),
    )
    assert updated["weekly_publish_goal"] == 3
    assert updated["content_strategy"].startswith("Publish one")
    assert updated["xiaohongshu_account_reference"] == "creator-note-account"
    assert updated["consent"] == {"history_analysis": True}


@pytest.mark.asyncio
async def test_publish_check_is_version_bound_and_resolutions_are_append_only(test_db):
    project, version = await _project_with_version(
        test_db,
        "publish-check",
        body_text="This method is 100% guaranteed to pass platform review.",
    )
    service = PublishCheckService(test_db)
    check, replayed = await service.run(
        "u1",
        project["id"],
        PublishCheckCreate(
            content_version_id=version["id"],
            idempotency_key="publish-check-run",
        ),
    )
    assert replayed is False
    assert check["stale"] is False
    assert check["status"] == "needs_attention"
    finding = check["findings"][0]
    assert finding["field"] == "body_text"
    assert finding["start"] < finding["end"]
    assert finding["rule_source"] == "TopicAI deterministic publish rules"
    assert finding["rule_updated_at"]

    resolved, replayed = await service.resolve(
        "u1",
        check["id"],
        PublishCheckResolution(
            findings={finding["id"]: "acknowledged"},
            idempotency_key="publish-check-resolution",
        ),
    )
    assert replayed is False
    assert resolved["status"] == "clear"
    assert resolved["findings"][0]["status"] == "acknowledged"
    assert len(resolved["resolutions"]) == 1

    new_project = await ContentProjectService(test_db).get("u1", project["id"])
    await ContentVersionService(test_db).create(
        "u1",
        project["id"],
        ContentVersionCreate(
            title="A safer revision",
            body_text="A bounded personal observation.",
            expected_project_version=new_project["version"],
            idempotency_key="publish-check-new-version",
        ),
    )
    assert (await service.get("u1", check["id"]))["stale"] is True


@pytest.mark.asyncio
async def test_publication_reuses_the_latest_resolved_version_check(test_db):
    project, version = await _project_with_version(
        test_db,
        "publication-check-reuse",
        body_text="This method is 100% guaranteed to pass platform review.",
    )
    check_service = PublishCheckService(test_db)
    check, _ = await check_service.run(
        "u1",
        project["id"],
        PublishCheckCreate(
            content_version_id=version["id"],
            idempotency_key="publication-reuse-check",
        ),
    )
    await check_service.resolve(
        "u1",
        check["id"],
        PublishCheckResolution(
            findings={item["id"]: "acknowledged" for item in check["findings"]},
            idempotency_key="publication-reuse-resolution",
        ),
    )

    with pytest.raises(ValueError, match="project is not ready to publish"):
        await PublicationService(test_db).record(
            "u1",
            project["id"],
            PublishRecordCreate(
                content_version_id=version["id"],
                publication_gate_id="not-reached",
                published_at="2026-08-06T10:00:00Z",
                expected_project_version=project["version"],
                idempotency_key="publication-reuse",
            ),
        )

    count = await test_db.fetch_one(
        "SELECT COUNT(*) AS count FROM publish_checks_v2 WHERE project_id=:project",
        {"project": project["id"]},
    )
    assert count["count"] == 1


class _VisionLLM:
    model = "vision-test-model"

    def is_available(self, capability="text"):
        return capability == "vision"

    def vision_generate(self, image_url, prompt):
        assert image_url.startswith("data:image/png;base64,")
        assert "views" in prompt
        return '{"views": 1200, "likes": 80, "favorites": 45, "comments": null, "shares": 3, "follows_gained": null}'


@pytest.mark.asyncio
async def test_screenshot_extraction_returns_unconfirmed_idempotent_proposal(test_db):
    material, _ = await MaterialService(test_db).create(
        "u1",
        MaterialCreate(
            kind="image",
            title="72 hour metrics",
            content_base64=base64.b64encode(b"fake-png").decode(),
            mime_type="image/png",
            privacy_level="sensitive",
            idempotency_key="screenshot-material",
        ),
    )
    service = SnapshotExtractionService(test_db, llm=_VisionLLM())
    body = SnapshotExtractionCreate(
        material_id=material["id"], idempotency_key="snapshot-extract"
    )
    proposal, replayed = await service.extract("u1", body)
    assert replayed is False
    assert proposal["confirmed_by_user"] is False
    assert proposal["metrics"]["views"] == 1200
    assert proposal["ai_trace"]["capability"] == "vision"
    assert proposal["ai_trace"]["confidence_label"] == "low"
    assert proposal["ai_trace"]["outcome"] == "success"

    assert await MaterialService(test_db).delete(
        "u1", material["id"], confirmed=False
    )
    retained = await service.get("u1", proposal["id"])
    assert retained["material_id"] is None

    replay, replayed = await service.extract("u1", body)
    assert replayed is True
    assert replay["id"] == proposal["id"]
