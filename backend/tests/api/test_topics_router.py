"""End-to-end tests for /topics router (Spec-007 US2 + Foundation C1).

Foundation batch C1 contract:
- GET /api/v1/topics/history delegates to TopicHistoryService (NOT directly
  to DataManager), returns ApiResponse[TopicHistoryResponse] with
  meta.data_source='recent_cache' / model_version='history-v1'.
- The route handler must not import DataManager (Constitution I) —
  asserted via AST scan of the source file.
"""
import ast
from pathlib import Path

import pytest

# ========== C1: routes do not import DataManager directly ==========

def test_topics_router_does_not_import_data_manager():
    """Constitution I: topics.py route layer must not import DataManager.

    The history endpoint delegates to TopicHistoryService. Importing
    DataManager from the route is a layer-boundary violation.
    """
    src_path = (
        Path(__file__).resolve().parents[2]
        / "app" / "api" / "v1" / "topics.py"
    )
    assert src_path.exists(), f"topics.py not found at {src_path}"
    tree = ast.parse(src_path.read_text(encoding="utf-8"))

    dm_imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and "data_manager" in node.module:
                for alias in node.names:
                    dm_imports.append(f"{node.module}.{alias.name}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if "data_manager" in (alias.name or ""):
                    dm_imports.append(alias.name)

    assert not dm_imports, (
        "topics.py imports DataManager directly — route must delegate to "
        f"TopicHistoryService instead. Found: {dm_imports}"
    )


# ========== C1: /topics/history returns typed envelope ==========

@pytest.mark.asyncio
async def test_topics_history_returns_typed_envelope_when_empty(client):
    """GET /topics/history on a fresh db returns ApiResponse envelope
    with an empty TopicHistoryResponse and recent_cache provenance."""
    r = await client.get("/api/v1/topics/history")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    assert body["message"] == "success"

    data = body["data"]
    assert set(data.keys()) >= {"topics", "count"}
    assert data["topics"] == []
    assert data["count"] == 0

    meta = body["meta"]
    assert meta["data_source"] == "recent_cache"
    assert meta["model_version"] == "history-v1"


@pytest.mark.asyncio
async def test_topics_history_returns_cached_topics_when_service_seeded(app):
    """When TopicHistoryService's DataManager holds cached topics, the
    endpoint surfaces them in the typed envelope.

    We inject a seeded service instance directly so the test does not
    depend on cross-request cache persistence (DataManager._recent_cache
    is per-instance today) — we assert the service→endpoint delegation
    contract, not the (separately tracked) cache-persistence behavior.
    """
    from httpx import ASGITransport, AsyncClient

    from app.data_sources.data_manager import DataManager
    from app.services.topic_history import TopicHistoryService

    dm = DataManager()
    dm.cache_recent_topics([
        {"title": "缓存选题-1", "track_match_score": 0.7},
        {"title": "缓存选题-2", "track_match_score": 0.6},
    ])
    seeded_service = TopicHistoryService(data_manager=dm)

    # Override the get_db yield unchanged; we monkeypatch the endpoint's
    # import target instead — TopicHistoryService. The endpoint builds
    # `TopicHistoryService()` lazily, so we patch the module-level symbol
    # the endpoint resolves at call time.
    import app.services.topic_history as th_module
    original = th_module.TopicHistoryService
    th_module.TopicHistoryService = lambda *a, **kw: seeded_service
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as c:
            r = await c.get("/api/v1/topics/history")
    finally:
        th_module.TopicHistoryService = original

    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    data = body["data"]
    assert data["count"] == 2
    assert len(data["topics"]) == data["count"]
    titles = [t["title"] for t in data["topics"]]
    assert "缓存选题-1" in titles
    assert "缓存选题-2" in titles


@pytest.mark.asyncio
async def test_topics_history_limit_passes_through(app):
    """The `limit` query param caps the returned rows."""
    from httpx import ASGITransport, AsyncClient

    from app.data_sources.data_manager import DataManager
    from app.services.topic_history import TopicHistoryService

    dm = DataManager()
    dm.cache_recent_topics([
        {"title": f"缓存选题-{i}", "track_match_score": 0.5} for i in range(5)
    ])
    seeded_service = TopicHistoryService(data_manager=dm)

    import app.services.topic_history as th_module
    original = th_module.TopicHistoryService
    th_module.TopicHistoryService = lambda *a, **kw: seeded_service
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as c:
            r = await c.get("/api/v1/topics/history?limit=2")
    finally:
        th_module.TopicHistoryService = original

    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data["topics"]) <= 2


@pytest.mark.asyncio
async def test_topics_history_invalid_limit_rejected(client):
    """limit < 1 or > 100 is rejected by Query validation → 422."""
    r0 = await client.get("/api/v1/topics/history?limit=0")
    assert r0.status_code == 422
    r1 = await client.get("/api/v1/topics/history?limit=101")
    assert r1.status_code == 422
