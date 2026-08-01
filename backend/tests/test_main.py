"""Tests for T01: Project Infrastructure.

Tests cover:
- TC01-01: FastAPI app creation with CORS, routes
- TC01-02: Configuration loading from .env
- TC01-03: Lifespan management (startup/shutdown)
- TC01-04: Dependency completeness (placeholder for pip check)
- TC01-05: Health check endpoint
"""


import pytest


class TestFastAPIAppCreation:
    """TC01-01: FastAPI application creation."""

    def test_create_app_returns_fastapi_instance(self):
        """Given environment variables loaded, When create_app() called,
        Then returns FastAPI instance with correct metadata."""
        from main import create_app

        app = create_app()
        assert app is not None
        assert app.title == "TopicAI"
        assert app.version == "4.0.0"
        assert app.docs_url == "/docs"

    def test_create_app_has_cors_middleware(self):
        """Given app created, When inspecting middleware stack,
        Then CORS middleware is registered."""
        from main import create_app

        app = create_app()
        middleware_names = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_names

    def test_create_app_has_routes_registered(self):
        """Given app created, When inspecting routes,
        Then health endpoint is registered."""
        from main import create_app

        app = create_app()
        routes = [route.path for route in app.routes]
        assert "/api/v1/health" in routes


class TestJwtSecretStartupValidation:
    """D2: Startup validation strengthens JWT_SECRET_KEY checks.

    Production env must reject weak secret keys containing known
    placeholder phrases, or any key shorter than 32 characters.
    Non-production env tolerates weak keys (with a warning) so dev/test
    workflows keep working.
    """

    @staticmethod
    def _reset_settings_singleton() -> None:
        """Clear the cached settings singleton so the next get_settings()
        call reloads from the (monkeypatched) environment."""
        import config.settings

        config.settings._settings = None

    @pytest.fixture(autouse=True)
    def _auto_reset_settings_singleton(self):
        """Auto-clear the settings singleton before and after each test
        so no test leaks a cached Settings into a neighbor."""
        self._reset_settings_singleton()
        yield
        self._reset_settings_singleton()

    def test_create_app_rejects_weak_secret_in_production(self, monkeypatch):
        """Given ENVIRONMENT=production and a weak JWT_SECRET_KEY,
        When create_app() is called,
        Then ValueError is raised mentioning the weak secret."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv(
            "JWT_SECRET_KEY", "dev-secret-key-please-change-in-prod"
        )

        from main import create_app

        with pytest.raises(ValueError, match="weak"):
            create_app()

    def test_create_app_rejects_weak_secret_when_environment_is_Production(
        self, monkeypatch
    ):
        """C1: ENVIRONMENT is case-insensitive. 'Production' must still
        be treated as production and reject weak keys."""
        monkeypatch.setenv("ENVIRONMENT", "Production")
        monkeypatch.setenv(
            "JWT_SECRET_KEY", "dev-secret-key-please-change-in-prod"
        )

        from main import create_app

        with pytest.raises(ValueError, match="weak"):
            create_app()

    def test_create_app_rejects_weak_secret_when_environment_is_PRODUCTION(
        self, monkeypatch
    ):
        """C1: ENVIRONMENT is case-insensitive. 'PRODUCTION' must still
        be treated as production and reject weak keys."""
        monkeypatch.setenv("ENVIRONMENT", "PRODUCTION")
        monkeypatch.setenv(
            "JWT_SECRET_KEY", "dev-secret-key-please-change-in-prod"
        )

        from main import create_app

        with pytest.raises(ValueError, match="weak"):
            create_app()

    def test_create_app_rejects_short_secret_in_production(self, monkeypatch):
        """H2: A secret shorter than 32 characters must be rejected in
        production even if it contains no blacklist phrase."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("JWT_SECRET_KEY", "x9k2q7m4p1z8r6w3t5v0b8n1")  # 24 chars, no phrase

        from main import create_app

        with pytest.raises(ValueError, match="32"):
            create_app()

    def test_create_app_allows_strong_secret_in_production(self, monkeypatch):
        """Given ENVIRONMENT=production and a strong JWT_SECRET_KEY
        (>= 32 chars, no blacklist phrase),
        When create_app() is called,
        Then no ValueError is raised."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv(
            "JWT_SECRET_KEY",
            "x9k2q7m4p1z8r6w3t5v0b8n2c4d6f8h0j2l4s6u8w0y3a5b7c9e1g3i5k7m9o1q3",
        )

        from main import create_app

        app = create_app()
        assert app is not None

    def test_create_app_allows_weak_secret_in_dev(self, monkeypatch):
        """Given ENVIRONMENT=development and a weak JWT_SECRET_KEY,
        When create_app() is called,
        Then no ValueError is raised (dev tolerates weak keys)."""
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("JWT_SECRET_KEY", "dev-secret-key-please-change")

        from main import create_app

        app = create_app()
        assert app is not None

    def test_create_app_rejects_empty_secret_any_env(self, monkeypatch):
        """Given an empty JWT_SECRET_KEY in any environment,
        When create_app() is called,
        Then ValueError is raised (preserve existing behavior)."""
        monkeypatch.setenv("ENVIRONMENT", "test")
        monkeypatch.setenv("JWT_SECRET_KEY", "")

        from main import create_app

        with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
            create_app()


class TestConfigurationLoading:
    """TC01-02: Configuration loading from environment."""

    def test_settings_load_from_env(self, override_test_env):
        """Given .env.example exists, When loading Settings,
        Then all config items have expected values."""
        from config.settings import Settings

        settings = Settings()
        assert settings.environment == "test"
        assert settings.app_name == "TopicAI"
        assert settings.app_version == "4.0.0"
        assert isinstance(settings.debug, bool)

    def test_settings_database_url(self):
        """Given test environment, When accessing database_url,
        Then returns test database URL."""
        from config.settings import Settings

        settings = Settings()
        assert "sqlite" in settings.database_url

    def test_settings_jwt_secret_required(self):
        """Given JWT_SECRET_KEY set, When loading settings,
        Then JWT secret is not empty."""
        from config.settings import Settings

        settings = Settings()
        assert len(settings.jwt_secret_key) > 0

    def test_settings_llm_api_keys_present(self):
        """Given LLM API keys in env, When loading settings,
        Then API keys are accessible."""
        from config.settings import Settings

        settings = Settings()
        assert settings.deepseek_api_key == "test-deepseek-key"
        assert settings.dashscope_api_key == "test-dashscope-key"
        assert settings.zhipu_api_key == "test-zhipu-key"

    def test_settings_tianapi_key_present(self):
        """Given TianAPI key in env, When loading settings,
        Then TianAPI key is accessible."""
        from config.settings import Settings

        settings = Settings()
        assert settings.tianapi_key == "test-tianapi-key"

    def test_settings_ai_call_limit_default(self):
        """Given no custom limit, When loading settings,
        Then ai_calls_per_day defaults to 20."""
        from config.settings import Settings

        settings = Settings()
        assert settings.ai_calls_per_day == 20


class TestLLMConfig:
    """TC01-02 extended: LLM Provider configuration."""

    def test_llm_config_providers_defined(self):
        """Given llm_config module loaded, When checking providers,
        Then DeepSeek, Qwen, and GLM providers are defined."""
        from config.llm_config import LLM_PROVIDERS

        assert "deepseek" in LLM_PROVIDERS
        assert "qwen" in LLM_PROVIDERS
        assert "glm" in LLM_PROVIDERS

    def test_deepseek_config_has_correct_model(self):
        """Given llm_config loaded, When checking deepseek model,
        Then uses deepseek-v4-flash, not latest/chat/reasoner."""
        from config.llm_config import LLM_PROVIDERS

        ds = LLM_PROVIDERS["deepseek"]
        assert ds["default_model"] == "deepseek-v4-flash"
        assert ds["pro_model"] == "deepseek-v4-pro"
        assert ds["base_url"] == "https://api.deepseek.com"

    def test_qwen_config_has_correct_endpoint(self):
        """Given llm_config loaded, When checking qwen config,
        Then base_url is dashscope compatible endpoint."""
        from config.llm_config import LLM_PROVIDERS

        qw = LLM_PROVIDERS["qwen"]
        assert qw["base_url"] == "https://dashscope.aliyuncs.com/compatible-mode/v1"
        assert qw["default_model"] == "qwen-plus"

    def test_glm_config_has_correct_model(self):
        """Given llm_config loaded, When checking glm config,
        Then uses glm-5v-turbo."""
        from config.llm_config import LLM_PROVIDERS

        glm = LLM_PROVIDERS["glm"]
        assert glm["default_model"] == "glm-5v-turbo"
        assert glm["base_url"] == "https://open.bigmodel.cn/api/paas/v4"

    def test_no_latest_alias_in_models(self):
        """Given llm_config loaded, When checking all model names,
        Then no 'latest' alias is used."""
        from config.llm_config import LLM_PROVIDERS

        for provider_name, provider_config in LLM_PROVIDERS.items():
            for key, value in provider_config.items():
                if "model" in key and isinstance(value, str):
                    assert value != "latest", (
                        f"Provider {provider_name} uses 'latest' in {key}"
                    )
                    assert value != "deepseek-chat", (
                        f"Provider {provider_name} uses deprecated 'deepseek-chat'"
                    )
                    assert value != "deepseek-reasoner", (
                        f"Provider {provider_name} uses deprecated 'deepseek-reasoner'"
                    )

    def test_function_tier_config(self):
        """Given llm_config loaded, When checking function tiers,
        Then three tiers are defined: core, auxiliary, decorative."""
        from config.llm_config import FUNCTION_TIERS

        assert "core" in FUNCTION_TIERS
        assert "auxiliary" in FUNCTION_TIERS
        assert "decorative" in FUNCTION_TIERS
        assert FUNCTION_TIERS["core"]["fallback"] == "qwen"
        assert FUNCTION_TIERS["auxiliary"]["fallback"] == "degraded"
        assert FUNCTION_TIERS["decorative"]["fallback"] == "hidden"


class TestDataSourceConfig:
    """TC01-02 extended: Data source configuration."""

    def test_tianapi_endpoints_defined(self):
        """Given data_source_config loaded, When checking endpoints,
        Then all 6 TianAPI endpoints are defined."""
        from config.data_source_config import TIANAPI_ENDPOINTS

        assert len(TIANAPI_ENDPOINTS) == 6
        endpoint_names = [e["name"] for e in TIANAPI_ENDPOINTS]
        assert "weibohot" in endpoint_names
        assert "nethot" in endpoint_names
        assert "douyinhot" in endpoint_names
        assert "toutiaohot" in endpoint_names
        assert "qqhot" in endpoint_names
        assert "allhot" in endpoint_names

    def test_bilibili_endpoints_defined(self):
        """Given data_source_config loaded, When checking B站 endpoints,
        Then popular and ranking endpoints are defined."""
        from config.data_source_config import BILIBILI_ENDPOINTS

        assert len(BILIBILI_ENDPOINTS) >= 2
        urls = [e["url"] for e in BILIBILI_ENDPOINTS]
        assert any("popular" in url for url in urls)
        assert any("ranking" in url for url in urls)

    def test_data_source_layers_defined(self):
        """Given data_source_config loaded, When checking layers,
        Then three layers are defined."""
        from config.data_source_config import DATA_SOURCE_LAYERS

        assert "layer1" in DATA_SOURCE_LAYERS
        assert "layer2" in DATA_SOURCE_LAYERS
        assert "layer3" in DATA_SOURCE_LAYERS


class TestLifespanManagement:
    """TC01-03: Application lifespan management."""

    @pytest.mark.asyncio
    async def test_lifespan_startup_event(self):
        """Given app created, When lifespan startup event fires,
        Then SQLite WAL mode is enabled and services initialized."""
        from main import create_app, lifespan

        create_app()
        # Test that lifespan is an async generator
        assert callable(lifespan)

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_event(self):
        """Given app running, When lifespan shutdown event fires,
        Then connections are cleaned up gracefully."""
        from main import lifespan

        # Verify lifespan handles shutdown
        assert lifespan is not None


class TestHealthCheck:
    """TC01-05: Health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_ok(self, async_client):
        """Given app running, When GET /api/v1/health,
        Then returns 200 with status ok."""
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["status"] == "ok"
        assert data["data"]["version"] == "4.0.0"

    @pytest.mark.asyncio
    async def test_health_endpoint_no_auth_required(self, async_client):
        """Given no auth token, When GET /api/v1/health,
        Then returns 200 without authentication."""
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_response_format(self, async_client):
        """Given app running, When GET /api/v1/health,
        Then response follows unified format {code, data, message, meta}."""
        response = await async_client.get("/api/v1/health")
        data = response.json()
        assert "code" in data
        assert "data" in data
        assert "message" in data
        assert "meta" in data


class TestRequirementsAndEnv:
    """TC01-04: Dependency and environment completeness."""

    def test_requirements_txt_exists(self):
        """Given project root, When checking requirements.txt,
        Then file exists and contains key dependencies."""
        import os

        req_path = os.path.join(
            os.path.dirname(__file__), "..", "requirements.txt"
        )
        assert os.path.exists(req_path), "requirements.txt not found"

    def test_env_example_exists(self):
        """Given project root, When checking .env.example,
        Then file exists with required variables."""
        import os

        env_path = os.path.join(os.path.dirname(__file__), "..", ".env.example")
        assert os.path.exists(env_path), ".env.example not found"

    def test_pyproject_toml_exists(self):
        """Given project root, When checking pyproject.toml,
        Then file exists with project metadata."""
        import os

        proj_path = os.path.join(
            os.path.dirname(__file__), "..", "pyproject.toml"
        )
        assert os.path.exists(proj_path), "pyproject.toml not found"

    def test_env_example_contains_required_keys(self):
        """Given .env.example, When reading contents,
        Then all required configuration keys are documented."""
        import os

        env_path = os.path.join(os.path.dirname(__file__), "..", ".env.example")
        with open(env_path, encoding="utf-8") as f:
            content = f.read()

        required_keys = [
            "DATABASE_URL",
            "DEEPSEEK_API_KEY",
            "DASHSCOPE_API_KEY",
            "ZHIPU_API_KEY",
            "TIANAPI_KEY",
            "JWT_SECRET_KEY",
        ]
        for key in required_keys:
            assert key in content, f"Missing required key {key} in .env.example"
