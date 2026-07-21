"""TopicAI v4.0 "Air Pro" — FastAPI Application Entry Point.

Creates and configures the FastAPI application with:
- CORS middleware
- JWT authentication
- Rate limiting middleware
- Global exception handler
- API v1 router
- Lifespan management (startup/shutdown)
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.api.v2.router import api_v2_router
from app.core.exceptions import setup_exception_handlers
from app.middleware.auth_middleware import JWTAuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from config.settings import get_settings

logger = logging.getLogger(__name__)

# Module-level weak-secret blacklist. Multi-word placeholder phrases
# (NOT bare short words like "dev"/"test"/"secret") so a long
# high-entropy random key that happens to contain "test" or "dev" as a
# substring is not falsely rejected. The minimum-length gate below is
# the primary defense against short keys regardless of content.
_WEAK_SECRET_SUBSTRINGS: tuple[str, ...] = (
    "change-me",
    "change-in-prod",
    "please-change",
    "changeme",
    "placeholder",
    "your-secret",
    "dev-secret",
    "test-secret",
    "secret-key",
)

# Minimum JWT_SECRET_KEY length enforced in production. 32 characters
# is the baseline for a 192-bit HS256 secret.
_PRODUCTION_SECRET_MIN_LENGTH: int = 32


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup initialization and graceful shutdown.

    Startup:
        - Initialize SQLite WAL mode
        - Start APScheduler (if configured)
        - Initialize ChromaDB connection

    Shutdown:
        - Close database connections
        - Shutdown scheduler
        - Clean up resources
    """
    settings = get_settings()
    logger.info(
        f"Starting {settings.app_name} v{settings.app_version} "
        f"in {settings.environment} mode"
    )

    # ==================== Startup ====================
    try:
        # Initialize database
        from app.core.database import Database

        db = Database(settings.database_url)
        app.state.db = db
        await db.init_db()
        logger.info("Database initialized (SQLite WAL mode)")

        # Apply pending SQL migrations through the Database's own engine
        # (Spec-007 T004 + T103). The bridge routes file DBs to the sync
        # runner via asyncio.to_thread and :memory: to the aiosqlite engine,
        # so migrations always land on the SAME database init_db uses.
        try:
            await db.apply_migrations()
        except Exception as e:
            logger.warning(f"Migration runner skipped: {e}")

        # Initialize ChromaDB (lazy - don't fail startup if unavailable)
        try:
            from app.core.chroma import get_chroma_client

            chroma_client = get_chroma_client(settings.chroma_persist_dir)
            app.state.chroma = chroma_client
            logger.info("ChromaDB client initialized")
        except Exception as e:
            logger.warning(f"ChromaDB initialization skipped: {e}")
            app.state.chroma = None

        # Initialize APScheduler for background tasks
        try:
            from app.tasks.scheduler import init_scheduler

            scheduler = init_scheduler()
            app.state.scheduler = scheduler
            logger.info("APScheduler initialized")
        except Exception as e:
            logger.warning(f"Scheduler initialization skipped: {e}")
            app.state.scheduler = None

        # Initialize Sentry (if DSN configured)
        if settings.sentry_dsn:
            try:
                import sentry_sdk

                sentry_sdk.init(
                    dsn=settings.sentry_dsn,
                    environment=settings.environment,
                    release=settings.app_version,
                    traces_sample_rate=0.1 if settings.is_production else 1.0,
                )
                logger.info("Sentry initialized")
            except Exception as e:
                logger.warning(f"Sentry initialization failed: {e}")

        logger.info(f"{settings.app_name} startup complete")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield  # Application runs here

    # ==================== Shutdown ====================
    logger.info(f"Shutting down {settings.app_name}...")

    # Close database
    if hasattr(app.state, "db") and app.state.db:
        try:
            await app.state.db.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.warning(f"Database close error: {e}")

    # Shutdown scheduler
    if hasattr(app.state, "scheduler") and app.state.scheduler:
        try:
            app.state.scheduler.shutdown(wait=False)
            logger.info("Scheduler shutdown")
        except Exception as e:
            logger.warning(f"Scheduler shutdown error: {e}")

    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance.
    """
    settings = get_settings()

    if not settings.jwt_secret_key or settings.jwt_secret_key == "change-me-to-a-random-secret-key":
        raise ValueError(
            "JWT_SECRET_KEY must be set. Please configure this in your .env file."
        )

    secret_lower = settings.jwt_secret_key.lower()
    looks_weak = any(sub in secret_lower for sub in _WEAK_SECRET_SUBSTRINGS)
    too_short = len(settings.jwt_secret_key) < _PRODUCTION_SECRET_MIN_LENGTH

    if settings.is_production and (looks_weak or too_short):
        # L1: do NOT enumerate the blacklist phrases in the error
        # message; the minimum-length gate is the primary defense and
        # the phrase blacklist is a secondary catcher of placeholders.
        raise ValueError(
            "JWT_SECRET_KEY looks weak in production (known placeholder "
            "or too short). Set a strong random secret of "
            ">= 32 characters."
        )
    if not settings.is_production and looks_weak:
        logger.warning(
            "JWT_SECRET_KEY looks weak (contains placeholder phrase); "
            "acceptable in non-production only."
        )

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="TopicAI — AI驱动的短视频创作选题助手，提供热点选题推荐、病毒性分析、标题优化、"
        "内容风险评估和发布建议等创作全链路智能服务。",
        contact={
            "name": "TopicAI Team",
            "email": "support@topicai.com",
        },
        license_info={
            "name": "Proprietary",
        },
        openapi_tags=[
            {"name": "Health", "description": "健康检查与系统状态"},
            {"name": "Authentication", "description": "用户注册、登录与 Token 管理"},
            {"name": "Profiles", "description": "创作画像创建与管理"},
            {"name": "Topics", "description": "选题推荐、刷新与解释"},
            {"name": "Viral", "description": "内容病毒性分析与拆解"},
            {"name": "Ideas", "description": "创意点子的可行性评估与深化"},
            {"name": "Titles", "description": "标题优化与变体生成"},
            {"name": "Tracks", "description": "赛道健康度诊断"},
            {"name": "Publish", "description": "最佳发布时间建议"},
            {"name": "Feedback", "description": "用户反馈提交与分析"},
        ],
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        debug=settings.debug,
    )

    # ==================== CORS Middleware ====================
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    )

    # ==================== JWT Auth Middleware ====================
    app.add_middleware(JWTAuthMiddleware)

    # ==================== Rate Limit Middleware ====================
    app.add_middleware(RateLimitMiddleware)

    # ==================== Global Exception Handlers ====================
    setup_exception_handlers(app)

    # ==================== API Routes ====================
    app.include_router(api_v1_router, prefix="/api/v1")
    app.include_router(api_v2_router, prefix="/api/v2", tags=["ContentProject v2"])

    return app


# ==================== Direct Run Entry Point ====================
if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:create_app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
        factory=True,
    )
