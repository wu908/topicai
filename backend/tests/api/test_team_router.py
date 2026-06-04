"""End-to-end tests for /team/members router.

Covers all 4 endpoints + 401 (no auth) + ownership (cross-user) rejection.
"""
import pytest


# ========== Happy path (user u1) ==========

@pytest.mark.asyncio
async def test_list_members_empty(client):
    r = await client.get("/api/v1/team/members")
    assert r.status_code == 200
    assert r.json()["data"] == []


@pytest.mark.asyncio
async def test_invite_member(client):
    r = await client.post(
        "/api/v1/team/members",
        json={"email": "a@b.com", "username": "Alice", "role": "editor"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["data"]["email"] == "a@b.com"
    assert body["data"]["role"] == "editor"
    assert body["data"]["id"] is not None


@pytest.mark.asyncio
async def test_change_role(client):
    create_r = await client.post(
        "/api/v1/team/members",
        json={"email": "a@b.com", "username": "Alice", "role": "editor"},
    )
    mid = create_r.json()["data"]["id"]

    r = await client.patch(
        f"/api/v1/team/members/{mid}",
        json={"role": "admin"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["role"] == "admin"


@pytest.mark.asyncio
async def test_remove_member(client):
    create_r = await client.post(
        "/api/v1/team/members",
        json={"email": "a@b.com", "username": "Alice", "role": "viewer"},
    )
    mid = create_r.json()["data"]["id"]

    r = await client.delete(f"/api/v1/team/members/{mid}")
    assert r.status_code == 204

    # Confirm gone.
    list_r = await client.get("/api/v1/team/members")
    assert list_r.json()["data"] == []


# ========== 401 (no auth) ==========

@pytest.mark.asyncio
async def test_list_members_no_auth_401(client_no_auth):
    r = await client_no_auth.get("/api/v1/team/members")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_invite_member_no_auth_401(client_no_auth):
    r = await client_no_auth.post(
        "/api/v1/team/members",
        json={"email": "a@b.com", "username": "A", "role": "editor"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_change_role_no_auth_401(client_no_auth):
    r = await client_no_auth.patch(
        "/api/v1/team/members/anything",
        json={"role": "admin"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_remove_member_no_auth_401(client_no_auth):
    r = await client_no_auth.delete("/api/v1/team/members/anything")
    assert r.status_code == 401


# ========== Ownership (cross-user rejection) ==========
# Service raises ValueError on non-owner; router lets it bubble.
# Tests assert no data mutation occurred (security guarantee).

@pytest.mark.asyncio
async def test_change_role_other_owner_no_mutation(client, client_as_u2):
    create_r = await client.post(
        "/api/v1/team/members",
        json={"email": "a@b.com", "username": "Alice", "role": "editor"},
    )
    mid = create_r.json()["data"]["id"]

    r = await client_as_u2.patch(
        f"/api/v1/team/members/{mid}",
        json={"role": "admin"},
    )
    assert r.status_code >= 400
    # u1's member still has original role.
    list_r = await client.get("/api/v1/team/members")
    assert list_r.json()["data"][0]["role"] == "editor"


@pytest.mark.asyncio
async def test_remove_member_other_owner_no_mutation(client, client_as_u2):
    create_r = await client.post(
        "/api/v1/team/members",
        json={"email": "a@b.com", "username": "Alice", "role": "viewer"},
    )
    mid = create_r.json()["data"]["id"]

    r = await client_as_u2.delete(f"/api/v1/team/members/{mid}")
    assert r.status_code >= 400
    # u1 still has the member.
    list_r = await client.get("/api/v1/team/members")
    assert len(list_r.json()["data"]) == 1
