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


@pytest.mark.asyncio
async def test_set_tags_wrong_owner(svc):
    # P1: a caller who does not own the asset must not be able to mutate its tags,
    # and the DELETE must not run before the ownership check fails.
    r = await run_upload(svc, 'u1')
    s = await svc.db.get_session()
    try:
        await s.execute(text("INSERT OR IGNORE INTO users (id, email, username, password_hash, ai_calls_today, ai_calls_reset_at, created_at) VALUES ('u2', 'u2@t.com', 'u2', 'hash', 0, '', '2026-06-03T00:00:00Z')"))
        await s.execute(text("INSERT INTO asset_tags (id, owner_id, name, color, created_at) VALUES ('t1','u1','product','green','2026')"))
        # u2's tag should be rejected even if the caller tries to attach it to u1's asset
        await s.execute(text("INSERT INTO asset_tags (id, owner_id, name, color, created_at) VALUES ('t_x','u2','foreign','red','2026')"))
        await s.execute(text("INSERT INTO asset_tag_links (asset_id, tag_id) VALUES (:aid, 't1')"), {"aid": r.asset_id})
        await s.commit()
    finally:
        await s.close()
    with pytest.raises(ValueError, match='not found'):
        await svc.set_tags('u2', r.asset_id, ['t1'])
    # original tag link must still be there — the failed request did not delete it
    s2 = await svc.db.get_session()
    try:
        rows = (await s2.execute(text("SELECT tag_id FROM asset_tag_links WHERE asset_id = :aid"), {"aid": r.asset_id})).fetchall()
        assert {row.tag_id for row in rows} == {'t1'}
    finally:
        await s2.close()
    await _rm(svc, 'u1', r.asset_id)


@pytest.mark.asyncio
async def test_set_tags_rejects_foreign_tag_ids(svc):
    # P1 (defense-in-depth): even when the asset is yours, you cannot attach
    # a tag that belongs to another owner.
    r = await run_upload(svc, 'u1')
    s = await svc.db.get_session()
    try:
        await s.execute(text("INSERT OR IGNORE INTO users (id, email, username, password_hash, ai_calls_today, ai_calls_reset_at, created_at) VALUES ('u2', 'u2@t.com', 'u2', 'hash', 0, '', '2026-06-03T00:00:00Z')"))
        await s.execute(text("INSERT INTO asset_tags (id, owner_id, name, color, created_at) VALUES ('t1','u1','product','green','2026')"))
        await s.execute(text("INSERT INTO asset_tags (id, owner_id, name, color, created_at) VALUES ('t_x','u2','foreign','red','2026')"))
        await s.commit()
    finally:
        await s.close()
    with pytest.raises(ValueError, match='not found or not owned'):
        await svc.set_tags('u1', r.asset_id, ['t1', 't_x'])
    await _rm(svc, 'u1', r.asset_id)


@pytest.mark.asyncio
async def test_get_usage(svc):
    # P1: get_usage requires owner_id; wrong owner gets no rows, right owner sees theirs.
    r = await run_upload(svc, 'u1')
    s = await svc.db.get_session()
    try:
        await s.execute(text(
            "INSERT INTO asset_usages (id, asset_id, article_id, used_at) "
            "VALUES ('us1', :aid, 'art1', '2026-06-01T00:00:00Z')"
        ), {"aid": r.asset_id})
        await s.commit()
    finally:
        await s.close()
    rows = await svc.get_usage('u1', r.asset_id)
    assert len(rows) == 1
    assert rows[0]['asset_id'] == r.asset_id
    assert rows[0]['article_id'] == 'art1'
    assert rows[0]['article_title'] is None  # honest placeholder, not a leaked UUID
    assert rows[0]['used_at'] == '2026-06-01T00:00:00Z'
    foreign = await svc.get_usage('u2', r.asset_id)
    assert foreign == []
    await _rm(svc, 'u1', r.asset_id)
