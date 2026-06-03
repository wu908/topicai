"""Unit tests for LocalObjectStorage."""
import tempfile, os
import pytest
from app.core.storage import LocalObjectStorage


@pytest.mark.asyncio
async def test_put_and_get():
    storage = LocalObjectStorage()
    path = await storage.put('u1', 'hello.txt', b'hello world')
    assert 'u1' in path
    data = await storage.get(path)
    assert data == b'hello world'


@pytest.mark.asyncio
async def test_delete():
    storage = LocalObjectStorage()
    path = await storage.put('u1', 'tmp.txt', b'x')
    await storage.delete(path)
    data = await storage.get(path)
    assert data is None


@pytest.mark.asyncio
async def test_sign_and_verify():
    storage = LocalObjectStorage()
    url = storage.sign_url('u1/test.txt', ttl_seconds=300)
    assert '?token=' in url
    assert '&expires=' in url
    import urllib.parse
    q = dict(urllib.parse.parse_qsl(url.split('?')[1]))
    assert storage.verify('u1/test.txt', q['token'], int(q['expires'])) is True


@pytest.mark.asyncio
async def test_expired_url():
    storage = LocalObjectStorage()
    url = storage.sign_url('u1/test.txt', ttl_seconds=-60)
    import urllib.parse
    q = dict(urllib.parse.parse_qsl(url.split('?')[1]))
    assert storage.verify('u1/test.txt', q['token'], int(q['expires'])) is False
