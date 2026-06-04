"""Unit tests for AccountService."""
import pytest
from sqlalchemy import text


@pytest.fixture
def svc(test_db):
    from app.services.account_service import AccountService
    return AccountService(test_db)


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
async def test_create_account(svc):
    r = await svc.create('u1', 'wechat_mp', 'TestAccount')
    assert r.id is not None
    assert r.platform == 'wechat_mp'
    assert r.status == 'disconnected'


@pytest.mark.asyncio
async def test_list_accounts(svc):
    await svc.create('u1', 'wechat_mp', 'A')
    await svc.create('u1', 'xhs', 'B')
    accounts = await svc.list('u1')
    assert len(accounts) == 2


@pytest.mark.asyncio
async def test_get_account(svc):
    r = await svc.create('u1', 'wechat_mp', 'X')
    a = await svc.get('u1', r.id)
    assert a.display_name == 'X'


@pytest.mark.asyncio
async def test_get_wrong_owner(svc):
    r = await svc.create('u1', 'wechat_mp', 'X')
    with pytest.raises(ValueError, match='not found'):
        await svc.get('u2', r.id)


@pytest.mark.asyncio
async def test_set_primary(svc):
    r = await svc.create('u1', 'wechat_mp', 'X')
    await svc.set_primary('u1', r.id)
    a = await svc.get('u1', r.id)
    assert a.is_primary is True


@pytest.mark.asyncio
async def test_disconnect(svc):
    r = await svc.create('u1', 'wechat_mp', 'X')
    await svc.disconnect('u1', r.id)
    a = await svc.get('u1', r.id)
    assert a.status == 'disconnected'


@pytest.mark.asyncio
async def test_disconnect_wrong_owner(svc):
    """Non-owner must not be able to disconnect an account they don't own."""
    r = await svc.create('u1', 'wechat_mp', 'X')
    with pytest.raises(ValueError, match='not found'):
        await svc.disconnect('u2', r.id)
    # Original owner's account must remain untouched.
    a = await svc.get('u1', r.id)
    assert a.status == 'disconnected'  # default from create()


@pytest.mark.asyncio
async def test_trigger_sync(svc):
    r = await svc.create('u1', 'wechat_mp', 'X')
    ts = await svc.trigger_sync('u1', r.id)
    assert ts is not None


@pytest.mark.asyncio
async def test_trigger_sync_wrong_owner(svc):
    """Non-owner must not be able to trigger sync — must raise, not silently
    return a timestamp without updating any row."""
    r = await svc.create('u1', 'wechat_mp', 'X')
    with pytest.raises(ValueError, match='not found'):
        await svc.trigger_sync('u2', r.id)
    # Original account must remain untouched.
    a = await svc.get('u1', r.id)
    assert a.last_sync_at is None


@pytest.mark.asyncio
async def test_set_primary_wrong_owner(svc):
    """Non-owner must not be able to mark an account as primary."""
    r = await svc.create('u1', 'wechat_mp', 'X')
    with pytest.raises(ValueError, match='not found'):
        await svc.set_primary('u2', r.id)
