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

    config = get_compatible_llm_config(Settings(_env_file=None))

    assert config["configured"] is False
    assert config["capabilities"] == {"text"}


def test_llm_client_uses_compatible_endpoint_when_configured(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.example.test/v1")
    monkeypatch.setenv("LLM_API_KEY", "compatible-test-key")
    monkeypatch.setenv("LLM_MODEL", "writer-model")
    monkeypatch.setenv("LLM_CAPABILITIES", "text,vision")
    monkeypatch.setenv("VISION_ENABLED", "true")
    _reset_settings()

    mock_client = MagicMock()
    with patch("app.core.llm.OpenAI", return_value=mock_client) as openai_factory:
        from app.core.llm import LLMClient

        client = LLMClient()

    assert client.model == "writer-model"
    assert client.get_capabilities() == {"text", "vision"}
    assert client.is_available("text") is True
    assert client.is_available("vision") is True
    assert openai_factory.call_args.kwargs["base_url"] == "https://llm.example.test/v1"


def test_llm_client_reports_unavailable_when_no_model_is_configured(monkeypatch):
    for key in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("LLM_BASE_URL", "")
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("LLM_MODEL", "")
    _reset_settings()

    with patch("app.core.llm.OpenAI", return_value=MagicMock()):
        from app.core.llm import LLMClient

        client = LLMClient()

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


def test_vision_requires_operator_switch_and_declared_capability(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.example.test/v1")
    monkeypatch.setenv("LLM_API_KEY", "compatible-test-key")
    monkeypatch.setenv("LLM_MODEL", "vision-model")
    monkeypatch.setenv("LLM_CAPABILITIES", "text,vision")
    monkeypatch.setenv("VISION_ENABLED", "false")
    _reset_settings()

    with patch("app.core.llm.OpenAI", return_value=MagicMock()):
        from app.core.llm import LLMClient

        client = LLMClient()

    assert client.is_available("text") is True
    assert client.is_available("vision") is False

    monkeypatch.setenv("VISION_ENABLED", "true")
    _reset_settings()
    with patch("app.core.llm.OpenAI", return_value=MagicMock()):
        client = LLMClient()

    assert client.is_available("vision") is True


def test_generate_structured_tells_the_model_the_field_names():
    """结构化调用必须把字段骨架写进系统提示。

    背景：`generate_structured` 只说"返回符合 schema 的 JSON"，而 schema 本身
    从未发给模型——模型只能猜字段名。线上实测：观点提炼连续 4 次解析失败后
    降级为 deterministic_fallback；同类的提示词还有机会、系列、规则、发布前检查。
    """
    from pydantic import BaseModel

    from app.core.llm import LLMClient

    class Draft(BaseModel):
        statement: str
        limitations: list[str]

    seen: dict[str, str] = {}
    client = LLMClient.__new__(LLMClient)  # 跳过 __init__ 对配置/网络的依赖
    client._max_retries = 0

    def fake_generate(prompt, system=None, **kwargs):  # type: ignore[no-untyped-def]
        seen["system"] = system or ""
        return '{"statement": "一句话", "limitations": []}'

    client.generate = fake_generate  # type: ignore[method-assign]

    out = client.generate_structured("素材", Draft, "你是观点提炼助手")

    assert '"statement"' in seen["system"]
    assert '"limitations"' in seen["system"]
    assert "你是观点提炼助手" in seen["system"]
    assert out.statement == "一句话"
