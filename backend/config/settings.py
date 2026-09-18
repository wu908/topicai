"""Global configuration for TopicAI v4.0.

Uses Pydantic BaseSettings for environment variable loading with validation.
All sensitive values read from .env file or environment variables.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

# Canonical environment names, plus the common shorthands that must not be
# allowed to silently fall through to a non-production value.
_ENVIRONMENT_ALIASES = {
    "production": "production",
    "prod": "production",
    "development": "development",
    "dev": "development",
    "local": "development",
    "staging": "staging",
    "stage": "staging",
    "test": "test",
    "testing": "test",
    "ci": "test",
}

# Only symmetric HMAC algorithms are supported: the app signs with a shared
# secret (``jwt_secret_key``), so allowing ``none`` or an asymmetric alg here
# would yield unsigned or incorrectly verified tokens.
_ALLOWED_JWT_ALGORITHMS = {"HS256", "HS384", "HS512"}


class Settings(BaseSettings):
    """Global application settings loaded from environment variables.

    All values have sensible defaults for development. Production values
    should be set via environment variables or .env file.
    """

    # ==================== Application ====================
    app_name: str = Field(default="TopicAI", alias="APP_NAME")
    app_version: str = Field(default="5.0.0", alias="APP_VERSION")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # ==================== Database ====================
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/topicai.db",
        alias="DATABASE_URL",
    )
    # ==================== Provider-neutral LLM ====================
    llm_base_url: str = Field(default="", alias="LLM_BASE_URL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_model: str = Field(default="", alias="LLM_MODEL")
    llm_timeout_seconds: float = Field(default=30.0, alias="LLM_TIMEOUT_SECONDS", gt=0)
    llm_capabilities: str = Field(default="text", alias="LLM_CAPABILITIES")

    # ==================== 全模态（音视频素材识别） ====================
    # 小米 MiMo 开放平台的 omni 模型：音/视频 → 文本。
    # 与主 LLM 分开配置：它按模态与计费都独立，且 base_url 不同（官方 OpenAI
    # 兼容端点 https://api.xiaomimimo.com/v1）。模型 id 是 **mimo-v2.5**
    # （历史上那个 mimo-v2-omni 已于 2026-06-30 下线，写 "v2.5-omni" 会 404）。
    omni_enabled: bool = Field(default=False, alias="OMNI_ENABLED")
    omni_base_url: str = Field(default="https://api.xiaomimimo.com/v1", alias="OMNI_BASE_URL")
    omni_api_key: str = Field(default="", alias="OMNI_API_KEY")
    omni_model: str = Field(default="mimo-v2.5", alias="OMNI_MODEL")
    omni_timeout_seconds: float = Field(default=120.0, alias="OMNI_TIMEOUT_SECONDS", gt=0)
    # 官方限制：base64 字符串 ≤50MB（视频 URL ≤300MB）。留出余量后按原始字节判定。
    omni_max_media_bytes: int = Field(default=45_000_000, alias="OMNI_MAX_MEDIA_BYTES")

    # ==================== Content Project v2 ====================
    ai_enabled: bool = Field(default=True, alias="AI_ENABLED")
    vision_enabled: bool = Field(default=False, alias="VISION_ENABLED")

    # 夜间自动消化的触发时刻（产品时区）。默认 03:00，与设置页文案一致；
    # 做成配置是为了能在不等到凌晨的情况下验证这条链路真的会跑。
    nightly_digest_hour: int = Field(default=3, ge=0, le=23, alias="NIGHTLY_DIGEST_HOUR")
    nightly_digest_minute: int = Field(default=0, ge=0, le=59, alias="NIGHTLY_DIGEST_MINUTE")

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
    auth_rate_limit_per_minute: int = Field(
        default=5, alias="AUTH_RATE_LIMIT_PER_MINUTE", ge=1
    )

    # ==================== Monitoring ====================
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")
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

    @field_validator("environment")
    @classmethod
    def _normalize_environment(cls, value: str) -> str:
        """Normalize ``ENVIRONMENT`` to a canonical name, rejecting typos.

        ``is_production`` gates the JWT-secret strength check in
        ``backend/main.py``. An unrecognized value such as ``producton``
        would make that gate fail *open*, so an invalid environment must
        fail loudly at startup instead of degrading silently.
        """
        normalized = value.strip().lower()
        if normalized not in _ENVIRONMENT_ALIASES:
            allowed = ", ".join(sorted(set(_ENVIRONMENT_ALIASES)))
            raise ValueError(
                f"ENVIRONMENT must be one of: {allowed} (got {value!r})"
            )
        return _ENVIRONMENT_ALIASES[normalized]

    @field_validator("jwt_algorithm")
    @classmethod
    def _validate_jwt_algorithm(cls, value: str) -> str:
        """Reject algorithms this app cannot safely verify (e.g. ``none``)."""
        normalized = value.strip().upper()
        if normalized not in _ALLOWED_JWT_ALGORITHMS:
            allowed = ", ".join(sorted(_ALLOWED_JWT_ALGORITHMS))
            raise ValueError(
                f"JWT_ALGORITHM must be one of: {allowed} (got {value!r})"
            )
        return normalized

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
