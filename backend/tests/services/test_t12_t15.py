"""Tests for T12-T15: Content analyzers, prompt registry, tasks, monitoring."""
import pytest


class TestContentAnalyzers:
    """T12: Content analyzer abstraction tests."""

    def test_analyzer_factory_creates_text_analyzer(self):
        from app.content_analyzers.base import ContentAnalyzerFactory
        analyzer = ContentAnalyzerFactory.create("text")
        assert analyzer.supported_input_type == "text"

    def test_analyzer_factory_creates_image_analyzer(self):
        from app.content_analyzers.base import ContentAnalyzerFactory
        analyzer = ContentAnalyzerFactory.create("image")
        assert analyzer.supported_input_type == "image"

    def test_analyzer_factory_raises_for_unknown(self):
        from app.content_analyzers.base import ContentAnalyzerFactory
        with pytest.raises(ValueError):
            ContentAnalyzerFactory.create("video")

    def test_text_analyzer_inherits_base(self):
        from app.content_analyzers.base import ContentAnalyzer
        from app.content_analyzers.text_analyzer import TextAnalyzer
        assert issubclass(TextAnalyzer, ContentAnalyzer)

    def test_image_analyzer_inherits_base(self):
        from app.content_analyzers.base import ContentAnalyzer
        from app.content_analyzers.image_analyzer import ImageAnalyzer
        assert issubclass(ImageAnalyzer, ContentAnalyzer)

    def test_text_analyze_returns_structured_result(self):
        from app.content_analyzers.text_analyzer import TextAnalyzer
        result = TextAnalyzer().analyze("Hello World")
        assert "extracted_text" in result
        assert result["extracted_text"] == "Hello World"

    def test_image_analyze_returns_vision_result(self):
        from app.content_analyzers.image_analyzer import ImageAnalyzer
        result = ImageAnalyzer().analyze(b"fake-image")
        assert "extracted_text" in result
        assert result.get("vision_model") == "glm-5v-turbo"


class TestPromptRegistry:
    """T13: Prompt registry tests."""

    def test_registry_lists_available_modules(self):
        from app.prompts.registry import PromptRegistry
        modules = PromptRegistry.list_modules()
        assert "onboarding" in modules
        assert "topic_recommend" in modules
        assert "viral_analysis" in modules

    def test_registry_gets_latest_version(self):
        from app.prompts.registry import PromptRegistry
        version = PromptRegistry.get_latest_version("onboarding")
        assert version == "v1"

    def test_registry_loads_prompt(self):
        from app.prompts.registry import PromptRegistry
        content = PromptRegistry.get_prompt("onboarding", "v1")
        assert "创作画像" in content or "Prompt" in content
        assert len(content) > 0

    def test_registry_raises_for_missing_module(self):
        from app.prompts.registry import PromptRegistry
        with pytest.raises(FileNotFoundError):
            PromptRegistry.get_prompt("nonexistent_module", "v1")

    def test_registry_raises_for_missing_version(self):
        from app.prompts.registry import PromptRegistry
        with pytest.raises(FileNotFoundError):
            PromptRegistry.get_prompt("onboarding", "v99")


class TestSchedulerTasks:
    """T14: Scheduler tasks tests."""

    def test_backup_service_exists(self):
        from app.tasks.backup import BackupService
        svc = BackupService()
        assert svc is not None

    def test_backup_generates_filename(self):
        from datetime import date

        from app.tasks.backup import BackupService
        svc = BackupService()
        fname = svc._backup_filename()
        assert str(date.today()) in fname
        assert fname.endswith(".db.bak")

    def test_cleanup_service_exists(self):
        from app.tasks.content_cleanup import ContentCleanupService
        svc = ContentCleanupService()
        assert svc is not None

    def test_health_check_service_exists(self):
        from app.tasks.health_check import HealthCheckService
        svc = HealthCheckService()
        assert svc is not None

    def test_health_check_returns_status(self):
        from app.tasks.health_check import HealthCheckService
        svc = HealthCheckService()
        status = svc.check_all()
        assert "deepseek" in status
        assert "tianapi" in status


class TestMonitoring:
    """T15: Monitoring integration tests."""

    def test_observability_service_exists(self):
        from app.core.observability import ObservabilityService
        svc = ObservabilityService()
        assert svc is not None

    def test_observability_disabled_by_default(self):
        from app.core.observability import ObservabilityService
        svc = ObservabilityService()
        assert svc.enabled is False

    def test_observability_enabled_with_key(self, monkeypatch):
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "test-pk")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "test-sk")
        # Reset settings singleton to pick up new env vars
        import config.settings
        config.settings._settings = None
        from app.core.observability import ObservabilityService
        svc = ObservabilityService()
        assert svc.enabled is True

    def test_setup_monitoring_returns_none_when_disabled(self, monkeypatch):
        monkeypatch.delenv("SENTRY_DSN", raising=False)
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("POSTHOG_API_KEY", raising=False)
        from app.middleware.monitoring import setup_monitoring
        result = setup_monitoring(None)
        assert result is None
