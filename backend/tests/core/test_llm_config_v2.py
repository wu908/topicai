"""Spec-008 tests for the provider-neutral OpenAI-compatible LLM boundary."""

from unittest.mock import MagicMock, patch

import pytest

from config.llm_config import get_compatible_llm_config
from config.settings import Settings


def _reset_settings() -> None:
    import config.settings as settings_module

    settings_module._settings = None


@pytest.fixture(autouse=True)
def reset_settings_after_test():
    yield
    _reset_settings()


def test_settings_load_provider_neutral_fields(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.example.test/v1")
    monkeypatch.setenv("LLM_API_KEY", "compatible-test-key")
    monkeypatch.setenv("LLM_MODEL", "writer-model")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "17")
    monkeypatch.setenv("LLM_CAPABILITIES", "text, vision")

    settings = Settings()

    assert settings.llm_base_url == "https://llm.example.test/v1"
    assert settings.llm_api_key == "compatible-test-key"
    assert settings.llm_model == "writer-model"
    assert settings.llm_timeout_seconds == 17
    assert settings.llm_capabilities == "text, vision"


def test_compatible_config_is_not_configured_without_endpoint_or_key(monkeypatch):
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    config = get_compatible_llm_config(Settings())

    assert config["configured"] is False
    assert config["capabilities"] == {"text"}


def test_llm_client_uses_compatible_endpoint_when_configured(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.example.test/v1")
    monkeypatch.setenv("LLM_API_KEY", "compatible-test-key")
    monkeypatch.setenv("LLM_MODEL", "writer-model")
    monkeypatch.setenv("LLM_CAPABILITIES", "text,vision")
    _reset_settings()

    mock_client = MagicMock()
    with patch("app.core.llm.OpenAI", return_value=mock_client) as openai_factory:
        from app.core.llm import LLMClient

        client = LLMClient()

    assert client.default_provider == "compatible"
    assert client.active_provider == "compatible"
    assert client.providers["compatible"]["model"] == "writer-model"
    assert client.get_capabilities() == {"text", "vision"}
    assert client.is_available("text") is True
    assert client.is_available("vision") is True
    assert openai_factory.call_args_list[-1].kwargs["base_url"] == "https://llm.example.test/v1"


def test_llm_client_reports_unavailable_when_no_model_is_configured(monkeypatch):
    for key in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL", "DEEPSEEK_API_KEY", "DASHSCOPE_API_KEY", "ZHIPU_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    _reset_settings()

    with patch("app.core.llm.OpenAI", return_value=MagicMock()):
        from app.core.llm import LLMClient

        client = LLMClient()

    assert client.active_provider == "deepseek"
    assert client.is_available("text") is False
    assert client.is_available("vision") is False


def test_llm_client_reports_missing_vision_capability(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.example.test/v1")
    monkeypatch.setenv("LLM_API_KEY", "compatible-test-key")
    monkeypatch.setenv("LLM_MODEL", "text-only-model")
    monkeypatch.setenv("LLM_CAPABILITIES", "text")
    _reset_settings()

    with patch("app.core.llm.OpenAI", return_value=MagicMock()):
        from app.core.llm import LLMClient

        client = LLMClient()

    assert client.is_available("text") is True
    assert client.is_available("vision") is False
