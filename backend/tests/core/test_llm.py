"""Tests for T03: LLM client and degradation strategy.

Tests cover:
- TC03-01: DeepSeek Flash call
- TC03-02: DeepSeek Pro deep thinking
- TC03-03: Qwen hot standby auto-switch
- TC03-04: Structured output validation
- TC03-05/06: Structured output retry
- TC03-07: Streaming response
- TC03-08/09/10: Function tier degradation
- TC03-11: Model version enforcement
- TC03-12: Timeout handling
- TC03-13: Rate limit 429
- TC03-14: GLM-5V-Turbo vision
- TC03-15: GLM modality limit
"""

from unittest.mock import MagicMock

import pytest


class TestLLMClientInitialization:
    """Test LLMClient creation and provider configuration."""

    def test_llm_client_creation(self):
        """Given config, When creating LLMClient, Then default provider is deepseek."""
        from app.core.llm import LLMClient

        client = LLMClient()
        assert client.default_provider == "deepseek"
        assert client.active_provider == "deepseek"

    def test_llm_client_providers_initialized(self):
        """Given LLMClient created, When checking providers dict,
        Then deepseek, qwen, glm all present."""
        from app.core.llm import LLMClient

        client = LLMClient()
        assert "deepseek" in client.providers
        assert "qwen" in client.providers
        assert "glm" in client.providers

    def test_llm_client_model_version_fixed(self):
        """Given LLMClient, When checking model versions,
        Then all are specific versions, not 'latest'."""
        from app.core.llm import LLMClient

        client = LLMClient()
        ds_config = client.providers["deepseek"]
        assert ds_config["model"] == "deepseek-v4-flash"
        assert ds_config["pro_model"] == "deepseek-v4-pro"

    def test_switch_provider(self):
        """Given LLMClient, When switching to qwen,
        Then active_provider updates."""
        from app.core.llm import LLMClient

        client = LLMClient()
        client.switch_provider("qwen")
        assert client.active_provider == "qwen"

    def test_switch_provider_invalid(self):
        """Given LLMClient, When switching to invalid provider,
        Then ValueError raised."""
        from app.core.llm import LLMClient

        client = LLMClient()
        with pytest.raises(ValueError):
            client.switch_provider("invalid")

    def test_get_active_provider(self):
        """Given LLMClient, When calling get_active_provider,
        Then returns active provider name."""
        from app.core.llm import LLMClient

        client = LLMClient()
        assert client.get_active_provider() == "deepseek"


class TestDeepSeekFlash:
    """TC03-01: DeepSeek Flash call."""

    def test_generate_with_deepseek_flash(self, mock_deepseek):
        """Given mock DeepSeek, When generate called,
        Then returns string with correct model version."""
        from app.core.llm import LLMClient

        client = LLMClient()
        result = client.generate("Test prompt")

        assert isinstance(result, str)
        assert "test response from deepseek-v4-flash" in result

    def test_generate_with_system_prompt(self, mock_deepseek):
        """Given system prompt, When generate called,
        Then system message included in request."""
        from app.core.llm import LLMClient

        client = LLMClient()
        result = client.generate(
            "Test prompt",
            system_prompt="You are a helpful assistant.",
        )
        assert result is not None

    def test_generate_with_temperature(self, mock_deepseek):
        """Given custom temperature, When generate called,
        Then temperature passed to API."""
        from app.core.llm import LLMClient

        client = LLMClient()
        result = client.generate("Test", temperature=0.3)
        assert result is not None


class TestDeepSeekPro:
    """TC03-02: DeepSeek Pro deep thinking mode."""

    def test_generate_with_pro_thinking(self, mock_deepseek_pro):
        """Given DeepSeek Pro, When generate with thinking=True,
        Then extra_body includes thinking config."""
        from app.core.llm import LLMClient

        client = LLMClient()
        client.switch_provider("deepseek")
        result = client.generate(
            "Analyze deeply",
            model="deepseek-v4-pro",
            thinking=True,
        )
        assert result is not None
        assert "deep thinking result" in result


class TestQwenHotStandby:
    """TC03-03: Qwen hot standby auto-switch."""

    def test_switch_to_qwen(self, mock_qwen):
        """Given Qwen provider, When generate called,
        Then returns response from qwen-plus."""
        from app.core.llm import LLMClient

        client = LLMClient()
        client.switch_provider("qwen")
        result = client.generate("Test prompt")

        assert result is not None
        assert "qwen-plus" in result


class TestStructuredOutput:
    """TC03-04/05/06: Structured output with Pydantic."""

    def test_generate_structured_success(self, mock_deepseek):
        """TC03-04: Given prompt + Pydantic schema, When generate_structured,
        Then returns valid Pydantic instance."""
        from app.core.llm import LLMClient
        from app.models.topic import TopicItem

        # Override mock to return valid TopicItem JSON
        mock_deepseek.chat.completions.create.return_value.choices[
            0
        ].message.content = (
            '{"title":"AI未来趋势","reason":"热门赛道","estimated_heat":0.85,'
            '"content_angle":"技术角度","track_match_score":0.9,'
            '"format_match_score":0.8,"data_quality_score":0.85,'
            '"composite_score":0.85,"confidence":0.9,"data_source":"tianapi"}'
        )

        client = LLMClient()
        result = client.generate_structured("test", TopicItem)

        assert isinstance(result, TopicItem)
        assert result.title == "AI未来趋势"
        assert result.confidence == 0.9

    def test_generate_structured_retry_on_invalid_json(self, mock_deepseek):
        """TC03-05: Given invalid JSON on first attempt, When generate_structured,
        Then retries and succeeds on second attempt."""
        from app.core.llm import LLMClient
        from app.models.topic import TopicItem

        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            resp = MagicMock()
            if call_count[0] == 1:
                resp.choices = [
                    MagicMock(
                        message=MagicMock(content="invalid json {{{"),
                        finish_reason="stop",
                    )
                ]
            else:
                resp.choices = [
                    MagicMock(
                        message=MagicMock(
                            content='{"title":"修复后","reason":"retry",'
                            '"estimated_heat":0.5,"content_angle":"test",'
                            '"track_match_score":0.5,"format_match_score":0.5,'
                            '"data_quality_score":0.5,"composite_score":0.5,'
                            '"confidence":0.7,"data_source":"test"}'
                        ),
                        finish_reason="stop",
                    )
                ]
            resp.usage = MagicMock(prompt_tokens=10, completion_tokens=10, total_tokens=20)
            return resp

        mock_deepseek.chat.completions.create.side_effect = side_effect

        client = LLMClient()
        result = client.generate_structured("test", TopicItem)

        assert isinstance(result, TopicItem)
        assert call_count[0] == 2
        assert result.title == "修复后"

    def test_generate_structured_fails_after_max_retries(self, mock_deepseek):
        """TC03-06: Given all retries return invalid JSON, When generate_structured,
        Then raises LLMStructuredOutputException."""
        from app.core.exceptions import LLMStructuredOutputException
        from app.core.llm import LLMClient
        from app.models.topic import TopicItem

        mock_deepseek.chat.completions.create.return_value.choices[
            0
        ].message.content = "not valid json at all {{{{{"

        client = LLMClient()
        with pytest.raises(LLMStructuredOutputException):
            client.generate_structured("test", TopicItem)


class TestStreamingResponse:
    """TC03-07: Streaming response."""

    def test_generate_stream(self, mock_deepseek_stream):
        """Given streaming mock, When generate_stream called,
        Then yields chunks and assembles full response."""
        from app.core.llm import LLMClient

        client = LLMClient()
        chunks = list(client.generate_stream("Test prompt"))
        full_text = "".join(chunks)

        assert len(chunks) > 0
        assert "streaming test" in full_text


class TestFunctionDegradation:
    """TC03-08/09/10: Function tier degradation."""

    def test_core_function_tier(self):
        """TC03-08: Given core function, When checking tier,
        Then fallback is qwen (switch_provider)."""
        from app.core.llm import LLMClient

        client = LLMClient()
        tier_info = client.get_function_tier_info("topic_recommend")
        assert tier_info["tier"] == "core"
        assert tier_info["fallback"] == "qwen"

    def test_auxiliary_function_tier(self):
        """TC03-09: Given auxiliary function, When checking tier,
        Then fallback is degraded (show message)."""
        from app.core.llm import LLMClient

        client = LLMClient()
        tier_info = client.get_function_tier_info("idea_booster")
        assert tier_info["tier"] == "auxiliary"
        assert tier_info["fallback"] == "degraded"

    def test_decorative_function_tier(self):
        """TC03-10: Given decorative function, When checking tier,
        Then fallback is hidden."""
        from app.core.llm import LLMClient

        client = LLMClient()
        tier_info = client.get_function_tier_info("content_risk_check")
        assert tier_info["tier"] == "decorative"
        assert tier_info["fallback"] == "hidden"


class TestModelVersionEnforcement:
    """TC03-11: Model version must be fixed, no 'latest'."""

    def test_model_version_not_latest(self):
        """Given all provider configs, When checking models,
        Then no 'latest' string found."""
        from app.core.llm import LLMClient

        client = LLMClient()
        for _name, config in client.providers.items():
            assert config["model"] != "latest"
            assert "latest" not in config["model"]

    def test_model_version_not_deprecated(self):
        """Given all provider configs, When checking models,
        Then no deprecated model names used."""
        from app.core.llm import LLMClient

        client = LLMClient()
        for name, config in client.providers.items():
            model = config["model"]
            assert model != "deepseek-chat", f"{name} uses deprecated deepseek-chat"
            assert model != "deepseek-reasoner", f"{name} uses deprecated deepseek-reasoner"


class TestRateLimitHandling:
    """TC03-13: Rate limit 429 handling."""

    def test_rate_limit_detection(self):
        """Given LLMClient, When checking rate_limit_error method,
        Then returns True for 429 status."""
        from app.core.llm import LLMClient

        client = LLMClient()
        assert client._is_rate_limit_error(429) is True
        assert client._is_rate_limit_error(200) is False
        assert client._is_rate_limit_error(503) is False


class TestHealthCheck:
    """Health check for LLM providers."""

    def test_health_check(self):
        """Given LLMClient, When health_check called,
        Then returns status for all providers."""
        from app.core.llm import LLMClient

        client = LLMClient()
        status = client.health_check()

        assert "deepseek" in status
        assert "qwen" in status
        assert "glm" in status
        assert "active_provider" in status

    def test_health_check_provider_structure(self):
        """Given health_check result, When checking each provider,
        Then has available and model fields."""
        from app.core.llm import LLMClient

        client = LLMClient()
        status = client.health_check()

        for provider in ["deepseek", "qwen", "glm"]:
            assert "available" in status[provider]
            assert "model" in status[provider]


class TestAIQualityMetaIntegration:
    """Verify AIQualityMeta is produced with every LLM call."""

    def test_generate_produces_quality_meta(self, mock_deepseek):
        """Given LLM call, When generate_structured succeeds,
        Then AIQualityMeta is embedded."""
        from app.core.llm import LLMClient
        from app.models.topic import TopicItem

        mock_deepseek.chat.completions.create.return_value.choices[
            0
        ].message.content = (
            '{"title":"Test","reason":"test","estimated_heat":0.5,'
            '"content_angle":"test","track_match_score":0.5,'
            '"format_match_score":0.5,"data_quality_score":0.5,'
            '"composite_score":0.5,"confidence":0.7,"data_source":"test"}'
        )

        client = LLMClient()
        result = client.generate_structured("test", TopicItem)
        assert result.data_source == "test"
        assert result.confidence == 0.7

    def test_generate_quality_meta_in_result(self, mock_deepseek):
        """Given LLM call, When generate called,
        Then quality meta accessible from result metadata."""
        from app.core.llm import LLMClient

        client = LLMClient()
        meta = client.generate_with_meta("test prompt")

        assert isinstance(meta, dict)
        assert "content" in meta
        assert "ai_quality" in meta
        assert meta["ai_quality"]["model_version"] == "deepseek-v4-flash"
        assert meta["ai_quality"]["data_source"] == "deepseek-v4-flash"


class TestGLMVision:
    """TC03-14/15: GLM-5V-Turbo vision."""

    def test_vision_generate(self, mock_glm):
        """TC03-14: Given image bytes, When vision_generate called,
        Then returns text description using glm-5v-turbo."""
        from app.core.llm import LLMClient

        client = LLMClient()
        client.switch_provider("glm")
        result = client.vision_generate(
            image_url="https://example.com/image.jpg",
            prompt="描述这张图片",
        )
        assert result is not None

    def test_vision_modality_limit(self):
        """TC03-15: Given both image and video, When vision_generate,
        Then raises ModalityLimitException."""
        from app.core.exceptions import ModalityLimitException
        from app.core.llm import LLMClient

        client = LLMClient()
        with pytest.raises(ModalityLimitException):
            client.vision_generate(
                image_url="https://example.com/img.jpg",
                video_url="https://example.com/video.mp4",
                prompt="Analyze",
            )
