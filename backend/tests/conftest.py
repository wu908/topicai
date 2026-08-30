"""Shared fixtures for the v2-only backend test suite."""

import os
import sys

import pytest
import pytest_asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def override_test_env(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("LLM_BASE_URL", "")
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("LLM_MODEL", "")
    monkeypatch.setenv("LLM_CAPABILITIES", "text")
    monkeypatch.setenv("VISION_ENABLED", "false")
    monkeypatch.setenv("SENTRY_DSN", "")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("OBJECT_STORAGE_ROOT", str(tmp_path / "objects"))
    # Settings 进程级单例可能已被本地 .env 污染（如真实凭据）；每个测试强制重读。
    import config.settings as _settings_module

    _settings_module._settings = None
    yield
    _settings_module._settings = None


@pytest_asyncio.fixture
async def test_db():
    from app.core.database import Database

    db = Database("sqlite+aiosqlite:///:memory:")
    await db.init_db()
    yield db
    await db.close()
