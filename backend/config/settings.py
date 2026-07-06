"""Global configuration for TopicAI v4.0.

Uses Pydantic BaseSettings for environment variable loading with validation.
All sensitive values read from .env file or environment variables.
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global application settings loaded from environment variables.

    All values have sensible defaults for development. Production values
    should be set via environment variables or .env file.
    """

    # ==================== Application ====================
    app_name: str = Field(default="TopicAI", alias="APP_NAME")
    app_version: str = Field(default="4.0.0", alias="APP_VERSION")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # ==================== Database ====================
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/topicai.db",
        alias="DATABASE_URL",
    )
    chroma_persist_dir: str = Field(
        default="./data/chroma",
        alias="CHROMA_PERSIST_DIR",
    )

    # ==================== LLM Providers ====================
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    dashscope_api_key: str = Field(default="", alias="DASHSCOPE_API_KEY")
    zhipu_api_key: str = Field(default="", alias="ZHIPU_API_KEY")

    # ==================== Data Sources ====================
    tianapi_key: str = Field(default="", alias="TIANAPI_KEY")

    # ==================== Authentication ====================
    jwt_secret_key: str = Field(
        default="",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS"
    )
    jwt_iss: str = Field(default="topica", alias="JWT_ISS", min_length=1)
    jwt_aud: str = Field(default="topica", alias="JWT_AUD", min_length=1)

    # ==================== Rate Limiting ====================
    ai_calls_per_day: int = Field(default=20, alias="AI_CALLS_PER_DAY")

    # ==================== Monitoring ====================
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")
    langfuse_public_key: str = Field(default="", alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", alias="LANGFUSE_SECRET_KEY")
    posthog_api_key: str = Field(default="", alias="POSTHOG_API_KEY")
    posthog_host: str = Field(
        default="https://app.posthog.com", alias="POSTHOG_HOST"
    )

    # ==================== Backup ====================
    backup_dir: str = Field(default="./backups", alias="BACKUP_DIR")
    backup_retention_count: int = Field(
        default=30, alias="BACKUP_RETENTION_COUNT"
    )
    backup_schedule_hour: int = Field(default=3, alias="BACKUP_SCHEDULE_HOUR")
    backup_schedule_minute: int = Field(
        default=0, alias="BACKUP_SCHEDULE_MINUTE"
    )

    # ==================== Content Cleanup ====================
    content_retention_days: int = Field(
        default=90, alias="CONTENT_RETENTION_DAYS"
    )

    # ==================== CORS ====================
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
        ],
        alias="CORS_ORIGINS",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

    @property
    def is_production(self) -> bool:
        """Check if running in production environment.

        Comparison is case-insensitive and whitespace-trimmed so that
        ``ENVIRONMENT=Production`` / ``PRODUCTION`` / `` production `` are
        all treated as production. Without this normalization a case
        typo would silently flip the JWT-secret strength gate to
        fail-open in production.
        """
        return self.environment.strip().lower() == "production"

    @property
    def is_test(self) -> bool:
        """Check if running in test environment (case-insensitive)."""
        return self.environment.strip().lower() == "test"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment (case-insensitive)."""
        return self.environment.strip().lower() == "development"


# Singleton settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance (lazy-loaded singleton).

    Returns:
        Settings: The global application settings.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
