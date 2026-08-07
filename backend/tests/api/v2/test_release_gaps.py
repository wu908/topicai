"""HTTP contracts for materials, settings, publish checks, and screenshot fallback."""

import base64

import pytest
from fastapi.routing import APIRoute

from app.models.common import ApiResponse


def test_release_gap_routes_publish_versioned_response_models(app):
    covered = {
        ("GET", "/api/v2/materials"),
        ("POST", "/api/v2/materials"),
        ("GET", "/api/v2/materials/{material_id}"),
        ("PATCH", "/api/v2/materials/{material_id}"),
        ("POST", "/api/v2/materials/{material_id}/usages"),
        ("GET", "/api/v2/settings"),
        ("PUT", "/api/v2/settings"),
        ("POST", "/api/v2/projects/{project_id}/publish-checks"),
        ("GET", "/api/v2/projects/{project_id}/publish-checks/latest"),
        ("PUT", "/api/v2/publish-checks/{check_id}/resolution"),
        ("POST", "/api/v2/snapshots:extract"),
        ("GET", "/api/v2/account/data-export"),
        ("DELETE", "/api/v2/account"),
    }
    routes = {
        (method, route.path): route
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in route.methods
    }

    assert covered <= routes.keys()
    for key in covered:
        model = routes[key].response_model
        assert model is not None, key
        assert model is not ApiResponse, key


async def _project_version(client, suffix: str, body_text: str = "A bounded observation."):
    project = (
        await client.post(
            "/api/v2/projects",
            json={
                "title": f"Release API {suffix}",
                "target_audience": "Knowledge creators",
                "idempotency_key": f"release-api-project-{suffix}",
            },
        )
    ).json()["data"]
    version = (
        await client.post(
            f"/api/v2/projects/{project['id']}/versions",
            json={
                "title": "A concrete title",
                "body_text": body_text,
                "expected_project_version": project["version"],
                "idempotency_key": f"release-api-version-{suffix}",
            },
        )
    ).json()["data"]
    return project, version


@pytest.mark.asyncio
async def test_material_and_settings_contracts_are_owner_scoped(client, client_as_u2):
    project, _ = await _project_version(client, "material")
    created = await client.post(
        "/api/v2/materials",
        json={
            "kind": "text",
            "title": "A reusable fact",
            "content": "A first-party observation.",
            "privacy_level": "private",
            "project_id": project["id"],
            "idempotency_key": "api-material-create",
        },
    )
    assert created.status_code == 201
    material = created.json()["data"]
    assert material["usages"][0]["project_id"] == project["id"]
    assert (await client_as_u2.get(f"/api/v2/materials/{material['id']}")).status_code == 404
    listed = await client.get("/api/v2/materials")
    assert [item["id"] for item in listed.json()["data"]["items"]] == [material["id"]]

    settings = (await client.get("/api/v2/settings")).json()["data"]
    updated = await client.put(
        "/api/v2/settings",
        json={
            "weekly_publish_goal": 3,
            "content_strategy": "One evidence-backed series each week.",
            "xiaohongshu_account_reference": "creator-account",
            "consent": {"history_analysis": True},
            "expected_version": settings["version"],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["weekly_publish_goal"] == 3
    assert "api_key" not in updated.json()["data"]["ai"]


@pytest.mark.asyncio
async def test_material_file_download_cannot_render_active_content_inline(client):
    created = await client.post(
        "/api/v2/materials",
        json={
            "kind": "document",
            "title": "Untrusted HTML",
            "content_base64": base64.b64encode(b"<script>alert(1)</script>").decode(),
            "mime_type": "text/html",
            "privacy_level": "private",
            "idempotency_key": "api-active-document",
        },
    )

    downloaded = await client.get(
        f"/api/v2/materials/{created.json()['data']['id']}/content"
    )

    assert downloaded.status_code == 200
    assert downloaded.headers["content-disposition"] == "attachment"
    assert downloaded.headers["x-content-type-options"] == "nosniff"


@pytest.mark.asyncio
async def test_publish_check_and_screenshot_manual_fallback_contract(client):
    project, version = await _project_version(
        client, "check", "This is 100% guaranteed to pass platform review."
    )
    checked = await client.post(
        f"/api/v2/projects/{project['id']}/publish-checks",
        json={
            "content_version_id": version["id"],
            "idempotency_key": "api-publish-check",
        },
    )
    assert checked.status_code == 201
    check = checked.json()["data"]
    assert check["status"] == "needs_attention"
    finding = check["findings"][0]
    resolved = await client.put(
        f"/api/v2/publish-checks/{check['id']}/resolution",
        json={
            "findings": {finding["id"]: "acknowledged"},
            "idempotency_key": "api-publish-check-resolution",
        },
    )
    assert resolved.status_code == 201
    assert resolved.json()["data"]["status"] == "clear"

    image = await client.post(
        "/api/v2/materials",
        json={
            "kind": "image",
            "title": "Metrics screenshot",
            "content_base64": base64.b64encode(b"fake-png").decode(),
            "mime_type": "image/png",
            "privacy_level": "sensitive",
            "idempotency_key": "api-screenshot-material",
        },
    )
    assert image.status_code == 201
    unavailable = await client.post(
        "/api/v2/snapshots:extract",
        json={
            "material_id": image.json()["data"]["id"],
            "idempotency_key": "api-snapshot-extraction",
        },
    )
    assert unavailable.status_code == 422
    assert unavailable.json()["meta"]["error_code"] == "AI_CAPABILITY_MISSING"
