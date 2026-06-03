"""Unit tests for AssetService."""
import pytest
import pytest_asyncio
from sqlalchemy import text


@pytest_asyncio.fixture(autouse=True)
async def _insert_test_user(test_db):
    s = await test_db.get_session()
    try:
        await s.execute(text("INSERT OR IGNORE INTO users (id, email, username, password_hash, ai_calls_today, ai_calls_reset_at, created_at) VALUES ('u1', 'test@t.com', 'tester', 'hash', 0, '', '2026-06-03T00:00:00Z')"))
        await s.commit()
    finally:
        await s.close()


@pytest.fixture
def svc(test_db):
    from app.services.asset_service import AssetService
    return AssetService(test_db)


async def _rm(svc, oid, aid):
    try:
        await svc.delete(oid, aid)
    except ValueError:
        pass


async def run_upload(svc, owner_id):
    from app.models.assets import AssetUploadRequest
    body = AssetUploadRequest(filename='test.png', mime_type='image/png', type='image')
    return await svc.create_upload(owner_id, body)


@pytest.mark.asyncio
async def test_create_upload(svc):
    r = await run_upload(svc, 'u1')
    assert r.asset_id is not None
    assert '/assets/' in r.upload_url
    await _rm(svc, 'u1', r.asset_id)


@pytest.mark.asyncio
async def test_list_assets(svc):
    r1 = await run_upload(svc, 'u1')
    r2 = await run_upload(svc, 'u1')
    from app.models.assets import AssetListQuery
    q = AssetListQuery()
    result = await svc.list('u1', q)
    assert result.total == 2
    assert len(result.items) == 2
    await _rm(svc, 'u1', r1.asset_id)
    await _rm(svc, 'u1', r2.asset_id)


@pytest.mark.asyncio
async def test_list_filter_by_type(svc):
    from app.models.assets import AssetUploadRequest
    r1 = await svc.create_upload('u1', AssetUploadRequest(filename='doc.pdf', mime_type='application/pdf', type='document'))
    r2 = await svc.create_upload('u1', AssetUploadRequest(filename='img.png', mime_type='image/png', type='image'))
    from app.models.assets import AssetListQuery
    result = await svc.list('u1', AssetListQuery(type='image'))
    assert result.total == 1
    await _rm(svc, 'u1', r1.asset_id)
    await _rm(svc, 'u1', r2.asset_id)


@pytest.mark.asyncio
async def test_get_asset(svc):
    r = await run_upload(svc, 'u1')
    a = await svc.get('u1', r.asset_id)
    assert a.filename == 'test.png'
    await _rm(svc, 'u1', r.asset_id)


@pytest.mark.asyncio
async def test_get_asset_wrong_owner(svc):
    r = await run_upload(svc, 'u1')
    with pytest.raises(ValueError, match='not found'):
        await svc.get('u2', r.asset_id)
    await _rm(svc, 'u1', r.asset_id)


@pytest.mark.asyncio
async def test_storage_stats(svc):
    await run_upload(svc, 'u1')
    stats = await svc.storage_stats('u1')
    assert stats.total_bytes == 10_000_000_000


@pytest.mark.asyncio
async def test_delete_asset(svc):
    r = await run_upload(svc, 'u1')
    await svc.delete('u1', r.asset_id)
    with pytest.raises(ValueError, match='not found'):
        await svc.get('u1', r.asset_id)


@pytest.mark.asyncio
async def test_delete_wrong_owner(svc):
    r = await run_upload(svc, 'u1')
    with pytest.raises(ValueError, match='not found'):
        await svc.delete('u2', r.asset_id)
    await _rm(svc, 'u1', r.asset_id)


@pytest.mark.asyncio
async def test_set_tags(svc):
    r = await run_upload(svc, 'u1')
    s = await svc.db.get_session()
    try:
        await s.execute(text("INSERT INTO asset_tags (id, owner_id, name, color, created_at) VALUES ('t1','u1','product','green','2026')"))
        await s.execute(text("INSERT INTO asset_tags (id, owner_id, name, color, created_at) VALUES ('t2','u1','team','amber','2026')"))
        await s.commit()
    finally:
        await s.close()
    a = await svc.set_tags('u1', r.asset_id, ['t1', 't2'])
    assert len(a.tags) == 2
    assert 'product' in [t.name for t in a.tags]
    await _rm(svc, 'u1', r.asset_id)
