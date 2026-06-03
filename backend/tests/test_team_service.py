"""Unit tests for TeamService."""
import pytest
from sqlalchemy import text


@pytest.fixture
def svc(test_db):
    from app.services.team_service import TeamService
    return TeamService(test_db)


import pytest_asyncio

@pytest_asyncio.fixture(autouse=True)
async def _insert_test_user(test_db):
    s = await test_db.get_session()
    try:
        await s.execute(text("INSERT OR IGNORE INTO users (id, email, username, password_hash, ai_calls_today, ai_calls_reset_at, created_at) VALUES ('u1', 'test@t.com', 'tester', 'hash', 0, '', '2026-06-03T00:00:00Z')"))
        await s.commit()
    finally:
        await s.close()


@pytest.mark.asyncio
async def test_invite_member(svc):
    r = await svc.invite('u1', 'a@b.com', 'TestUser', 'editor')
    assert r.email == 'a@b.com'
    assert r.role == 'editor'


@pytest.mark.asyncio
async def test_list_members(svc):
    await svc.invite('u1', 'a@b.com', 'A', 'editor')
    await svc.invite('u1', 'c@d.com', 'B', 'viewer')
    members = await svc.list('u1')
    assert len(members) == 2


@pytest.mark.asyncio
async def test_duplicate_email_rejected(svc):
    await svc.invite('u1', 'a@b.com', 'A', 'editor')
    with pytest.raises(ValueError, match='already exists'):
        await svc.invite('u1', 'a@b.com', 'B', 'viewer')


@pytest.mark.asyncio
async def test_change_role(svc):
    r = await svc.invite('u1', 'a@b.com', 'A', 'editor')
    m = await svc.change_role('u1', r.id, 'admin')
    assert m.role == 'admin'


@pytest.mark.asyncio
async def test_cannot_demote_last_admin(svc):
    admin = await svc.invite('u1', 'a@b.com', 'Admin', 'admin')
    with pytest.raises(ValueError, match='last admin'):
        await svc.change_role('u1', admin.id, 'editor')


@pytest.mark.asyncio
async def test_cannot_remove_last_admin(svc):
    admin = await svc.invite('u1', 'a@b.com', 'Admin', 'admin')
    with pytest.raises(ValueError, match='last admin'):
        await svc.remove('u1', admin.id)


@pytest.mark.asyncio
async def test_remove_member(svc):
    r = await svc.invite('u1', 'a@b.com', 'A', 'editor')
    await svc.remove('u1', r.id)
    members = await svc.list('u1')
    assert len(members) == 0


@pytest.mark.asyncio
async def test_remove_nonexistent(svc):
    with pytest.raises(ValueError, match='not found'):
        await svc.remove('u1', 'nonexistent')
