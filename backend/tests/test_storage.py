"""Unit tests for LocalObjectStorage."""
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


def test_verify_rejects_non_hex_token():
    """A token containing non-hex characters must not validate."""
    storage = LocalObjectStorage()
    import time
    future_expires = int(time.time()) + 300
    assert storage.verify('u1/test.txt', 'not-a-hex-token!@#', future_expires) is False


def test_verify_rejects_short_token():
    """A token shorter than the expected HMAC length must not validate."""
    storage = LocalObjectStorage()
    import time
    future_expires = int(time.time()) + 300
    assert storage.verify('u1/test.txt', 'abc', future_expires) is False


def test_verify_rejects_tampered_token():
    """A token of correct length but wrong signature must not validate."""
    storage = LocalObjectStorage()
    import time
    future_expires = int(time.time()) + 300
    # Generate a valid token, then flip one character in the middle.
    url = storage.sign_url('u1/test.txt', ttl_seconds=300)
    import urllib.parse
    q = dict(urllib.parse.parse_qsl(url.split('?')[1]))
    valid_token = q['token']
    # Flip the first character (hex char → different hex char).
    flipped = ('1' if valid_token[0] != '1' else '2') + valid_token[1:]
    assert flipped != valid_token
    assert storage.verify('u1/test.txt', flipped, future_expires) is False
