"""Unit tests for BilibiliSource and TianAPISource.

Focus on routing/JSON parsing; HTTP transport is mocked via monkeypatch.
"""

import pytest

from app.data_sources.bilibili_source import BilibiliSource
from app.data_sources.tianapi_source import TianAPISource


class _FakeResp:
    """Minimal httpx.Response stand-in exposing .json() and .raise_for_status()."""

    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        return None


# ─── BilibiliSource ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_bilibili_fetch_popular_delegates_to_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """fetch_popular delegates to _fetch_endpoint('popular') and returns its list."""
    src = BilibiliSource()

    async def _fake_fetch(endpoint: str):
        return [{"title": "ep1"}, {"title": "ep2"}]

    monkeypatch.setattr(src, "_fetch_endpoint", _fake_fetch)
    out = await src.fetch_popular()
    assert out == [{"title": "ep1"}, {"title": "ep2"}]


@pytest.mark.asyncio
async def test_bilibili_fetch_ranking_returns_list_on_code_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    """fetch_ranking returns the data.list payload when response code is 0."""
    src = BilibiliSource()

    class _FakeClient:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def get(self, url, timeout=None):
            return _FakeResp({"code": 0, "data": {"list": [{"a": 1}, {"b": 2}]}})

    import app.data_sources.bilibili_source as mod
    monkeypatch.setattr(mod.httpx, "AsyncClient", lambda *a, **k: _FakeClient())
    out = await src.fetch_ranking(rid=1)
    assert out == [{"a": 1}, {"b": 2}]


@pytest.mark.asyncio
async def test_bilibili_fetch_ranking_returns_empty_on_nonzero_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """fetch_ranking returns [] on non-zero code."""
    src = BilibiliSource()

    class _FakeClient:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def get(self, url, timeout=None):
            return _FakeResp({"code": -101, "message": "not logged in"})

    import app.data_sources.bilibili_source as mod
    monkeypatch.setattr(mod.httpx, "AsyncClient", lambda *a, **k: _FakeClient())
    assert await src.fetch_ranking() == []


@pytest.mark.asyncio
async def test_bilibili_fetch_ranking_handles_non_list_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    """fetch_ranking returns [] when data.list is not a list (defensive guard)."""
    src = BilibiliSource()

    class _FakeClient:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def get(self, url, timeout=None):
            return _FakeResp({"code": 0, "data": {"list": "garbage"}})

    import app.data_sources.bilibili_source as mod
    monkeypatch.setattr(mod.httpx, "AsyncClient", lambda *a, **k: _FakeClient())
    assert await src.fetch_ranking() == []


# ─── TianAPISource ───────────────────────────────────────────────────────


def test_tianapi_stores_api_key() -> None:
    """TianAPISource keeps the api_key on self for downstream calls."""
    src = TianAPISource(api_key="secret-xyz")
    assert src.api_key == "secret-xyz"


def test_tianapi_empty_key() -> None:
    """Empty api_key still constructs; downstream calls will return [] via guards."""
    src = TianAPISource(api_key="")
    assert src.api_key == ""


@pytest.mark.asyncio
async def test_tianapi_fetch_weibo_hot_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    """fetch_weibo_hot delegates to _fetch_endpoint('weibohot')."""
    src = TianAPISource(api_key="k")

    async def _fake_fetch(endpoint_name: str):
        assert endpoint_name == "weibohot"
        return [{"hotword": "w1"}]

    monkeypatch.setattr(src, "_fetch_endpoint", _fake_fetch)
    out = await src.fetch_weibo_hot()
    assert out == [{"hotword": "w1"}]


@pytest.mark.asyncio
async def test_tianapi_fetch_baidu_hot_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    """fetch_baidu_hot delegates to _fetch_endpoint('nethot')."""
    src = TianAPISource(api_key="k")

    async def _fake_fetch(endpoint_name: str):
        assert endpoint_name == "nethot"
        return [{"keyword": "k1", "index": 100}]

    monkeypatch.setattr(src, "_fetch_endpoint", _fake_fetch)
    out = await src.fetch_baidu_hot()
    assert out == [{"keyword": "k1", "index": 100}]


@pytest.mark.asyncio
async def test_tianapi_fetch_douyin_hot_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    """fetch_douyin_hot delegates to _fetch_endpoint('douyinhot')."""
    src = TianAPISource(api_key="k")

    async def _fake_fetch(endpoint_name: str):
        assert endpoint_name == "douyinhot"
        return [{"word": "d1"}]

    monkeypatch.setattr(src, "_fetch_endpoint", _fake_fetch)
    out = await src.fetch_douyin_hot()
    assert out == [{"word": "d1"}]


@pytest.mark.asyncio
async def test_tianapi_fetch_all_hot_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    """fetch_all_hot delegates to _fetch_endpoint('allhot')."""
    src = TianAPISource(api_key="k")

    async def _fake_fetch(endpoint_name: str):
        assert endpoint_name == "allhot"
        return [{"from": "weibo"}, {"from": "baidu"}]

    monkeypatch.setattr(src, "_fetch_endpoint", _fake_fetch)
    out = await src.fetch_all_hot()
    assert out == [{"from": "weibo"}, {"from": "baidu"}]


@pytest.mark.asyncio
async def test_tianapi_is_available_false_without_key() -> None:
    """is_available returns False when api_key is empty (no HTTP call)."""
    src = TianAPISource(api_key="")
    assert await src.is_available() is False


@pytest.mark.asyncio
async def test_tianapi_is_available_true_on_code_200(monkeypatch: pytest.MonkeyPatch) -> None:
    """is_available returns True when the API responds with code 200."""
    src = TianAPISource(api_key="k")

    class _FakeClient:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def get(self, url, params=None, timeout=None):
            return _FakeResp({"code": 200, "result": {"newslist": []}})

    import app.data_sources.tianapi_source as mod
    monkeypatch.setattr(mod.httpx, "AsyncClient", lambda *a, **k: _FakeClient())
    assert await src.is_available() is True


@pytest.mark.asyncio
async def test_tianapi_is_available_false_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """is_available returns False when the network raises (caught)."""
    src = TianAPISource(api_key="k")

    class _FakeClient:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def get(self, url, params=None, timeout=None):
            raise RuntimeError("network down")

    import app.data_sources.tianapi_source as mod
    monkeypatch.setattr(mod.httpx, "AsyncClient", lambda *a, **k: _FakeClient())
    assert await src.is_available() is False
