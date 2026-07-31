"""HTTP journey for first-party explainable opportunities."""

import pytest


@pytest.mark.asyncio
async def test_opportunity_write_endpoints_publish_typed_response_schema(client):
    document = (await client.get("/openapi.json")).json()

    for path in (
        "/api/v2/creator-series/{series_id}/extension-opportunities",
        "/api/v2/content-opportunities/source-verification",
        "/api/v2/content-opportunities/{opportunity_id}:decide",
        "/api/v2/content-opportunities/{opportunity_id}:verify-source",
    ):
        schema = document["paths"][path]["post"]["responses"]["201"]["content"][
            "application/json"
        ]["schema"]
        assert schema.get("$ref", "").endswith("ApiResponse_ContentOpportunityView_")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("original_url", " "),
        ("published_at", "not-a-date"),
        ("authoritative_source", " "),
    ],
)
@pytest.mark.asyncio
async def test_source_verification_rejects_invalid_metadata(client, field, value):
    body = {
        "verification_status": "verified",
        "original_url": "https://example.com/source",
        "published_at": "2026-07-31T00:00:00Z",
        "authoritative_source": "官方发布方",
        "timeliness": "current",
        "confirmed_by_user": True,
        "expected_opportunity_version": 1,
        "idempotency_key": f"invalid-source-{field}",
    }
    body[field] = value

    response = await client.post(
        "/api/v2/content-opportunities/missing:verify-source", json=body
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("trigger", "metadata"),
    [
        ("user_keyword", {}),
        ("user_url", {"original_url": "https://example.com/source"}),
        ("official_inspiration", {"authoritative_source": "小红书官方"}),
    ],
)
@pytest.mark.asyncio
async def test_manual_opportunity_records_trigger_and_expiry(client, trigger, metadata):
    response = await client.post(
        "/api/v2/content-opportunities/source-verification",
        json={
            "trigger": trigger,
            "pasted_text": "用户手动提交的创作灵感",
            "expires_at": "2026-08-07T00:00:00Z",
            "idempotency_key": f"manual-{trigger}",
            **metadata,
        },
    )

    assert response.status_code == 201
    opportunity = response.json()["data"]
    assert opportunity["source_trigger"] == trigger
    assert opportunity["expires_at"] == "2026-08-07T00:00:00Z"
    assert opportunity["verification_status"] == "pending_verification"


@pytest.mark.asyncio
async def test_expired_manual_source_requires_explicit_reverification_before_adoption(
    client, test_db
):
    profile = (await client.get("/api/v2/creator-profile")).json()["data"]
    await client.put(
        "/api/v2/creator-profile",
        json={
            "niche": "small-space living",
            "target_audience": "first-time renters",
            "growth_goal": "stable_publish",
            "content_pillars": ["storage"],
            "confirm": True,
            "expected_version": profile["version"],
        },
    )
    created = await client.post(
        "/api/v2/content-opportunities/source-verification",
        json={
            "trigger": "user_url",
            "pasted_text": "An old official update",
            "original_url": "https://example.com/old-update",
            "expires_at": "2020-01-02T00:00:00Z",
            "idempotency_key": "expired-source",
        },
    )
    opportunity = created.json()["data"]
    verified = await client.post(
        f"/api/v2/content-opportunities/{opportunity['id']}:verify-source",
        json={
            "verification_status": "verified",
            "original_url": "https://example.com/old-update",
            "published_at": "2020-01-01T00:00:00Z",
            "authoritative_source": "Example",
            "timeliness": "current",
            "confirmed_by_user": True,
            "expected_opportunity_version": opportunity["version"],
            "idempotency_key": "verify-expired-as-current",
        },
    )
    verified_data = verified.json()["data"]

    blocked = await client.post(
        f"/api/v2/content-opportunities/{opportunity['id']}:decide",
        json={
            "decision": "accept",
            "expected_opportunity_version": verified_data["version"],
            "idempotency_key": "adopt-stale-source",
        },
    )

    assert blocked.status_code == 400
    assert await test_db.fetch_one(
        "SELECT COUNT(*) AS count FROM content_projects WHERE opportunity_id=:id",
        {"id": opportunity["id"]},
    ) == {"count": 0}

    reconfirmed = await client.post(
        f"/api/v2/content-opportunities/{opportunity['id']}:verify-source",
        json={
            "verification_status": "verified",
            "original_url": "https://example.com/old-update",
            "published_at": "2020-01-01T00:00:00Z",
            "authoritative_source": "Example",
            "timeliness": "expired",
            "confirmed_by_user": True,
            "expected_opportunity_version": verified_data["version"],
            "idempotency_key": "confirm-expired-source",
        },
    )
    reconfirmed_data = reconfirmed.json()["data"]
    adopted = await client.post(
        f"/api/v2/content-opportunities/{opportunity['id']}:decide",
        json={
            "decision": "accept",
            "expected_opportunity_version": reconfirmed_data["version"],
            "idempotency_key": "adopt-confirmed-expired-source",
        },
    )
    assert adopted.status_code == 201
    assert adopted.json()["data"]["created_project_id"] is not None


@pytest.mark.asyncio
async def test_generate_and_list_first_party_opportunities(client, test_db):
    await client.post(
        "/api/v2/history-imports",
        json={
            "method": "manual",
            "items": [
                {
                    "title": "一次真实的小空间调整",
                    "tags": ["storage"],
                    "audience_questions": ["小空间应该先整理哪里？"],
                }
            ],
            "idempotency_key": "api-opportunity-history",
        },
    )
    profile = (await client.get("/api/v2/creator-profile")).json()["data"]
    await client.put(
        "/api/v2/creator-profile",
        json={
            "niche": "small-space living",
            "target_audience": "first-time renters",
            "growth_goal": "stable_publish",
            "content_pillars": ["storage"],
            "confirm": True,
            "expected_version": profile["version"],
        },
    )

    generated = await client.post(
        "/api/v2/content-opportunities:generate",
        json={"desired_count": 3},
    )

    assert generated.status_code == 200
    item = generated.json()["data"]["items"][0]
    assert item["opportunity_type"] == "history_derivative"
    assert item["dimensions"]["creator_fit"] == "strong"
    assert item["dimensions"]["growth_role"] == "trust"
    listed = await client.get("/api/v2/content-opportunities")
    assert {row["id"] for row in listed.json()["data"]["items"]} == {
        row["id"] for row in generated.json()["data"]["items"]
    }
    by_type = await client.get(
        "/api/v2/content-opportunities", params={"type": "evergreen"}
    )
    assert [row["opportunity_type"] for row in by_type.json()["data"]["items"]] == [
        "evergreen"
    ]
    by_timeliness = await client.get(
        "/api/v2/content-opportunities", params={"timeliness": "evergreen"}
    )
    assert [row["id"] for row in by_timeliness.json()["data"]["items"]] == [
        by_type.json()["data"]["items"][0]["id"]
    ]

    accept_body = {
        "decision": "accept",
        "expected_opportunity_version": item["version"],
        "idempotency_key": "first-party-adoption",
    }
    accepted = await client.post(
        f"/api/v2/content-opportunities/{item['id']}:decide",
        json=accept_body,
    )
    assert accepted.status_code == 201
    accepted_data = accepted.json()["data"]
    assert accepted_data["status"] == "accepted"
    assert accepted_data["project"]["opportunity_id"] == item["id"]
    assert accepted_data["project"]["target_audience"] == "first-time renters"

    replay = await client.post(
        f"/api/v2/content-opportunities/{item['id']}:decide",
        json=accept_body,
    )
    assert replay.status_code == 200
    assert replay.json()["meta"]["idempotency_replayed"] is True
    projects = await test_db.fetch_all(
        "SELECT id FROM content_projects WHERE opportunity_id=:opportunity",
        {"opportunity": item["id"]},
    )
    assert len(projects) == 1

    evergreen = generated.json()["data"]["items"][1]
    saved = await client.post(
        f"/api/v2/content-opportunities/{evergreen['id']}:decide",
        json={
            "decision": "save",
            "reason": "稍后补充素材",
            "expected_opportunity_version": evergreen["version"],
            "idempotency_key": "first-party-save",
        },
    )
    assert saved.status_code == 201
    saved_data = saved.json()["data"]
    assert saved_data["status"] == "saved"
    assert saved_data["created_project_id"] is None
    by_decision = await client.get(
        "/api/v2/content-opportunities", params={"decision": "save"}
    )
    assert [row["id"] for row in by_decision.json()["data"]["items"]] == [
        evergreen["id"]
    ]

    adopted_saved = await client.post(
        f"/api/v2/content-opportunities/{evergreen['id']}:decide",
        json={
            "decision": "accept",
            "expected_opportunity_version": saved_data["version"],
            "idempotency_key": "first-party-adopt-saved",
        },
    )
    assert adopted_saved.status_code == 201
    assert adopted_saved.json()["data"]["status"] == "accepted"
    assert adopted_saved.json()["data"]["created_project_id"] is not None

    profile = (await client.get("/api/v2/creator-profile")).json()["data"]
    await client.put(
        "/api/v2/creator-profile",
        json={
            "niche": "small-space living",
            "target_audience": "first-time renters",
            "growth_goal": "stable_publish",
            "content_pillars": ["storage"],
            "confirm": True,
            "expected_version": profile["version"],
        },
    )
    regenerated = await client.post(
        "/api/v2/content-opportunities:generate",
        json={"desired_count": 1},
    )
    rejected_item = regenerated.json()["data"]["items"][0]
    rejected = await client.post(
        f"/api/v2/content-opportunities/{rejected_item['id']}:decide",
        json={
            "decision": "reject",
            "reason": "与本周计划不符",
            "expected_opportunity_version": rejected_item["version"],
            "idempotency_key": "first-party-reject",
        },
    )
    assert rejected.status_code == 201
    assert rejected.json()["data"]["status"] == "rejected"
    event = await test_db.fetch_one(
        "SELECT payload_json FROM content_opportunity_events "
        "WHERE opportunity_id=:opportunity AND event_type='rejected'",
        {"opportunity": rejected_item["id"]},
    )
    assert "与本周计划不符" in event["payload_json"]
    feedback = await test_db.fetch_all(
        "SELECT source_id,feedback_type,reason FROM user_feedback "
        "WHERE user_id=:owner AND source_type='opportunity'",
        {"owner": "u1"},
    )
    assert {
        (row["source_id"], row["feedback_type"], row["reason"]) for row in feedback
    } == {
        (item["id"], "adopt", None),
        (evergreen["id"], "save", "稍后补充素材"),
        (evergreen["id"], "adopt", None),
        (rejected_item["id"], "reject", "与本周计划不符"),
    }
