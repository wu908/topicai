"""Global pytest fixtures for TopicAI v4.0 test suite.

Provides shared fixtures for database, HTTP client, mock LLM providers,
mock data sources, and test user authentication.
"""

import os
import sys
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore

# Ensure backend is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ==================== Environment Overrides ====================


@pytest.fixture(autouse=True)
def override_test_env(monkeypatch):
    """Override environment variables for testing."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("CHROMA_PERSIST_DIR", "./test_chroma/")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek-key")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-dashscope-key")
    monkeypatch.setenv("ZHIPU_API_KEY", "test-zhipu-key")
    monkeypatch.setenv("TIANAPI_KEY", "test-tianapi-key")
    monkeypatch.setenv("SENTRY_DSN", "")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "")
    monkeypatch.setenv("POSTHOG_API_KEY", "")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
    monkeypatch.setenv("ENVIRONMENT", "test")
    yield


# ==================== Database ====================


@pytest_asyncio.fixture
async def test_db():
    """SQLite :memory: mode database, isolated per test.

    Initializes the bootstrap schema, then applies the Phase-2 additive
    migrations (``002_user_feedback``, ``003_effect_reviews`` extended
    columns, ``004_risk_keywords``) so test data matches production
    reality for the Spec-007 US7 endpoints.
    """
    from sqlalchemy import text

    from app.core.database import Database

    db = Database("sqlite+aiosqlite:///:memory:")
    await db.init_db()

    async with db.engine.begin() as conn:  # type: ignore[attr-defined]
        # 002_user_feedback — Spec-007 T011 (US3 / US7 T057)
        await conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS user_feedback (
                id              CHAR(36) PRIMARY KEY,
                user_id         CHAR(36) NOT NULL,
                source_type     TEXT     NOT NULL,
                source_id       CHAR(36) NOT NULL,
                feedback_type   TEXT     NOT NULL,
                feedback_value  TEXT,
                reason          TEXT,
                created_at      TEXT     NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_user_feedback_user_id_created_at "
            "ON user_feedback (user_id, created_at DESC)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_user_feedback_source "
            "ON user_feedback (source_type, source_id)"
        ))

        # 003_effect_reviews — Spec-007 T012: extended columns not in
        # the bootstrap SQL_SCHEMA. Idempotent: skip if already present.
        for stmt in [
            "ALTER TABLE effect_reviews ADD COLUMN content_outline TEXT",
            "ALTER TABLE effect_reviews ADD COLUMN status TEXT NOT NULL DEFAULT 'awaiting_actuals'",
            "ALTER TABLE effect_reviews ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''",
        ]:
            try:
                await conn.execute(text(stmt))
            except Exception:
                # Column already exists (SQLite raises on duplicate).
                pass

        # 004_risk_keywords — Spec-007 T013 (US5 / US7 T074)
        await conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS risk_keywords (
                id          CHAR(36) PRIMARY KEY,
                user_id     CHAR(36),
                keyword     TEXT     NOT NULL,
                severity    TEXT     NOT NULL,
                category    TEXT     NOT NULL,
                created_at  TEXT     NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        ))

    yield db
    await db.close()


# ==================== HTTP Client ====================


@pytest_asyncio.fixture
async def async_client():
    """FastAPI TestClient using httpx AsyncClient."""
    from httpx import ASGITransport, AsyncClient

    from main import create_app

    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# ==================== Mock LLM Providers ====================


@pytest.fixture
def mock_deepseek():
    """Mock DeepSeek API response."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='{"result": "test response from deepseek-v4-flash"}',
                role="assistant",
            ),
            finish_reason="stop",
        )
    ]
    mock_response.usage = MagicMock(
        prompt_tokens=50, completion_tokens=30, total_tokens=80
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create = MagicMock(return_value=mock_response)

    with patch("app.core.llm.OpenAI", return_value=mock_client):
        yield mock_client


@pytest.fixture
def mock_deepseek_pro():
    """Mock DeepSeek V4 Pro with reasoning_content."""
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message = MagicMock(
        content='{"analysis": "deep thinking result", "conclusion": "test"}',
        role="assistant",
    )
    mock_choice.finish_reason = "stop"
    mock_response.choices = [mock_choice]
    mock_response.usage = MagicMock(
        prompt_tokens=100, completion_tokens=200, total_tokens=300
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create = MagicMock(return_value=mock_response)

    with patch("app.core.llm.OpenAI", return_value=mock_client):
        yield mock_client


@pytest.fixture
def mock_qwen():
    """Mock Qwen API response."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='{"result": "test response from qwen-plus"}',
                role="assistant",
            ),
            finish_reason="stop",
        )
    ]
    mock_response.usage = MagicMock(
        prompt_tokens=40, completion_tokens=25, total_tokens=65
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create = MagicMock(return_value=mock_response)

    with patch("app.core.llm.OpenAI", return_value=mock_client):
        yield mock_client


@pytest.fixture
def mock_glm():
    """Mock GLM-5V-Turbo API response."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="图片分析结果：这是一张内容创作相关的截图...",
                role="assistant",
            ),
            finish_reason="stop",
        )
    ]
    mock_response.usage = MagicMock(
        prompt_tokens=200, completion_tokens=80, total_tokens=280
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create = MagicMock(return_value=mock_response)

    try:
        # Mock at the source: zhipuai package
        with patch("zhipuai.ZhipuAI", return_value=mock_client):
            yield mock_client
    except (ImportError, ModuleNotFoundError, AttributeError):
        yield mock_client


# ==================== Mock Data Sources ====================


@pytest.fixture
def mock_tianapi():
    """Mock TianAPI response for all 6 hot search endpoints."""
    mock_response = MagicMock()
    mock_response.json = MagicMock(
        return_value={
            "code": 200,
            "msg": "success",
            "result": [
                {"hotword": "AI创作工具", "hotwordnum": 8234567, "hottag": "科技"},
                {"hotword": "小红书运营", "hotwordnum": 5678901, "hottag": "职场"},
                {"hotword": "DeepSeek教程", "hotwordnum": 4567890, "hottag": "科技"},
                {"hotword": "内容创作者", "hotwordnum": 3456789, "hottag": "职场"},
                {"hotword": "短视频爆款", "hotwordnum": 2345678, "hottag": "娱乐"},
            ],
        }
    )
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", return_value=mock_response) as mock_get:
        yield mock_get


@pytest.fixture
def mock_tianapi_unavailable():
    """Mock TianAPI as unavailable (returning error)."""
    mock_response = MagicMock()
    mock_response.json = MagicMock(
        return_value={"code": 500, "msg": "Internal Server Error"}
    )
    mock_response.status_code = 500

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        yield


@pytest.fixture
def mock_bilibili():
    """Mock Bilibili API response."""
    mock_response = MagicMock()
    mock_response.json = MagicMock(
        return_value={
            "code": 0,
            "data": {
                "list": [
                    {
                        "aid": 123456,
                        "title": "2026年AI工具大盘点",
                        "play": 500000,
                        "video_review": 12000,
                        "danmaku": 3000,
                    },
                    {
                        "aid": 123457,
                        "title": "如何打造爆款内容",
                        "play": 350000,
                        "video_review": 8000,
                        "danmaku": 2000,
                    },
                ]
            },
        }
    )
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        yield


# ==================== Mock Embedding ====================


@pytest.fixture
def mock_embedding():
    """Mock BGE embedding returning fixed 1024-dim vectors."""
    mock_model = MagicMock()
    mock_model.encode = MagicMock(return_value=np.ones((1, 1024), dtype=np.float32) if np else [[0.0] * 1024])

    try:
        with patch(
            "sentence_transformers.SentenceTransformer", return_value=mock_model
        ):
            yield mock_model
    except (ImportError, ModuleNotFoundError):
        yield mock_model


# ==================== Disable Monitoring ====================


@pytest.fixture(autouse=True)
def disable_monitoring():
    """Disable Sentry/LangFuse/PostHog in tests.

    Gracefully handles missing optional monitoring modules.
    """
    patches = []
    for module_path in ("sentry_sdk.init", "langfuse.Langfuse", "posthog.Posthog"):
        try:
            p = patch(module_path)
            p.start()
            patches.append(p)
        except (ImportError, ModuleNotFoundError):
            # Monitoring module not installed — harmless to skip
            pass

    yield

    for p in reversed(patches):
        p.stop()


# ==================== Mock Streaming ====================


@pytest.fixture
def mock_deepseek_stream():
    """Mock DeepSeek streaming response."""
    mock_chunks = [
        MagicMock(
            choices=[MagicMock(delta=MagicMock(content='{"result":'), finish_reason=None)]
        ),
        MagicMock(
            choices=[
                MagicMock(delta=MagicMock(content='"streaming test"'), finish_reason=None)
            ]
        ),
        MagicMock(
            choices=[MagicMock(delta=MagicMock(content="}"), finish_reason="stop")]
        ),
    ]

    mock_stream = MagicMock()
    mock_stream.__iter__ = MagicMock(return_value=iter(mock_chunks))
    mock_stream.__aiter__ = MagicMock(return_value=iter(mock_chunks))

    mock_client = MagicMock()
    mock_client.chat.completions.create = MagicMock(return_value=mock_stream)

    with patch("app.core.llm.OpenAI", return_value=mock_client):
        yield mock_client


# ==================== Test Helpers ====================


def generate_test_id() -> str:
    """Generate a unique test ID."""
    return str(uuid.uuid4())


def utc_now_iso() -> str:
    """Get current UTC time as ISO 8601 string."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def future_iso(days: int = 1) -> str:
    """Get future UTC time as ISO 8601 string."""
    return (datetime.now(UTC) + timedelta(days=days)).isoformat().replace(
        "+00:00", "Z"
    )
