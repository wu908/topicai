"""LLM Client abstraction layer for TopicAI v4.0.

Provides a unified interface for multiple LLM providers with:
- Provider strategy pattern (DeepSeek V4 Flash/Pro, Qwen Plus, GLM-5V-Turbo)
- Automatic retry logic (max 2 retries)
- Streaming response support
- Function tier degradation strategy
- Model version enforcement (no 'latest' aliases)
- Structured output with Pydantic validation
- AIQualityMeta on every output
"""

import json
import logging
from collections.abc import Generator
from datetime import UTC
from typing import Any, TypeVar

from openai import OpenAI

from config.llm_config import (
    DEEP_THINKING_PARAMS,
    DEFAULT_LLM_PARAMS,
    LLM_PROVIDERS,
    get_compatible_llm_config,
    get_fallback_action,
)
from config.settings import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class LLMClient:
    """Unified LLM client with multi-provider support and degradation.

    All LLM calls go through this class. It handles:
    - Provider routing (DeepSeek 鈫?Qwen hot standby)
    - Retry logic (up to 2 retries for structured output)
    - Streaming responses
    - Function tier degradation
    - Model version enforcement
    - AIQualityMeta generation
    """

    def __init__(self):
        """Initialize LLMClient with configured providers."""
        self.settings = get_settings()
        self.compatible_config = get_compatible_llm_config(self.settings)
        self.default_provider = (
            "compatible" if self.compatible_config["configured"] else "deepseek"
        )
        self.active_provider = self.default_provider
        self.providers = self._init_providers()
        self._retry_count = 0
        self._max_retries = 2

    def _init_providers(self) -> dict[str, dict[str, Any]]:
        """Initialize provider configurations with API clients.

        Returns:
            Dict mapping provider names to their configs and clients.
        """
        providers = {}

        # DeepSeek (default)
        ds_config = LLM_PROVIDERS["deepseek"]
        providers["deepseek"] = {
            "name": "deepseek",
            "model": ds_config["default_model"],
            "pro_model": ds_config["pro_model"],
            "client": OpenAI(
                api_key=self.settings.deepseek_api_key,
                base_url=ds_config["base_url"],
            ),
            "base_url": ds_config["base_url"],
            "timeout": ds_config["timeout_seconds"],
            "configured": bool(self.settings.deepseek_api_key),
        }

        # Qwen (hot standby)
        qw_config = LLM_PROVIDERS["qwen"]
        providers["qwen"] = {
            "name": "qwen",
            "model": qw_config["default_model"],
            "client": OpenAI(
                api_key=self.settings.dashscope_api_key,
                base_url=qw_config["base_url"],
            ),
            "base_url": qw_config["base_url"],
            "timeout": qw_config["timeout_seconds"],
            "configured": bool(self.settings.dashscope_api_key),
        }

        # GLM-5V-Turbo (vision)
        glm_config = LLM_PROVIDERS["glm"]
        providers["glm"] = {
            "name": "glm",
            "model": glm_config["default_model"],
            "base_url": glm_config["base_url"],
            "timeout": glm_config["timeout_seconds"],
            "configured": bool(self.settings.zhipu_api_key),
            "capabilities": {"vision"},
        }

        if self.compatible_config["configured"]:
            providers["compatible"] = {
                "name": "openai_compatible",
                "model": self.compatible_config["model"],
                "client": OpenAI(
                    api_key=self.compatible_config["api_key"],
                    base_url=self.compatible_config["base_url"],
                ),
                "base_url": self.compatible_config["base_url"],
                "timeout": self.compatible_config["timeout"],
                "capabilities": self.compatible_config["capabilities"],
                "configured": True,
            }

        return providers

    # ==================== Provider Management ====================

    def switch_provider(self, provider_name: str) -> None:
        """Switch the active LLM provider.

        Args:
            provider_name: 'deepseek', 'qwen', or 'glm'.

        Raises:
            ValueError: If provider_name is not recognized.
        """
        if provider_name not in self.providers:
            raise ValueError(
                f"Unknown provider '{provider_name}'. "
                f"Available: {list(self.providers.keys())}"
            )
        self.active_provider = provider_name
        logger.info(f"Switched LLM provider to {provider_name}")

    def get_active_provider(self) -> str:
        """Get the currently active provider name."""
        return self.active_provider

    def get_capabilities(self) -> set[str]:
        """Return capabilities declared by the active runtime endpoint."""
        return set(self.providers.get(self.active_provider, {}).get("capabilities", {"text"}))

    def is_available(self, capability: str = "text") -> bool:
        """Return whether AI is enabled, configured, and supports a capability."""
        provider = self.providers.get(self.active_provider, {})
        return bool(
            getattr(self.settings, "ai_enabled", True)
            and provider.get("configured", False)
            and provider.get("client") is not None
            and capability in self.get_capabilities()
        )

    # ==================== Core Generation ====================

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        thinking: bool = False,
        **kwargs: Any,
    ) -> str:
        """Generate a text response from the LLM.

        Args:
            prompt: The user prompt text.
            system_prompt: Optional system prompt.
            model: Override model (e.g., 'deepseek-v4-pro').
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum output tokens.
            thinking: Enable deep thinking mode (DeepSeek Pro).
            **kwargs: Additional API parameters.

        Returns:
            Generated text string.

        Raises:
            LLMException: On API errors after retries.
        """
        from app.core.exceptions import LLMException, LLMTimeoutException

        provider_config = self.providers[self.active_provider]
        client = provider_config.get("client")
        if client is None:
            raise LLMException(
                f"No client available for provider '{self.active_provider}'",
                provider=self.active_provider,
            )

        model_name = model or provider_config["model"]

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Build parameters
        params: dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            **DEFAULT_LLM_PARAMS,
        }

        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens

        if thinking:
            params.update(DEEP_THINKING_PARAMS)

        params.update(kwargs)

        try:
            response = client.chat.completions.create(**params)
            content = response.choices[0].message.content or ""
            return content
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower():
                raise LLMTimeoutException(
                    provider=self.active_provider,
                    timeout_seconds=provider_config["timeout"],
                ) from e
            if self._is_rate_limit_error(getattr(e, "status_code", 0)):
                raise LLMException(
                    "LLM rate limit exceeded", provider=self.active_provider
                ) from e
            raise LLMException(
                f"LLM generation failed: {error_msg}",
                provider=self.active_provider,
                model_version=model_name,
            ) from e

    def generate_structured(
        self,
        prompt: str,
        schema: type[T],
        system_prompt: str | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> T:
        """Generate a structured response validated against a Pydantic schema.

        Retries up to 2 times on JSON parse/Pydantic validation failure.

        Args:
            prompt: The user prompt text.
            schema: Pydantic model class for output validation.
            system_prompt: Optional system prompt.
            model: Override model.
            **kwargs: Additional API parameters.

        Returns:
            Validated Pydantic model instance.

        Raises:
            LLMStructuredOutputException: If all retries fail.
        """
        from app.core.exceptions import LLMStructuredOutputException

        # Enhance system prompt to enforce JSON output
        json_system = (
            f"{system_prompt}\n\n"
            f"IMPORTANT: Respond ONLY with valid JSON matching this schema. "
            f"No markdown, no explanation, just the JSON object."
            if system_prompt
            else "Respond ONLY with valid JSON. No markdown, no explanation."
        )

        for attempt in range(self._max_retries + 1):
            try:
                raw = self.generate(
                    prompt=prompt,
                    system_prompt=json_system,
                    model=model,
                    **kwargs,
                )

                # Clean up potential markdown code fences
                cleaned = _clean_json_response(raw)

                # Parse JSON
                data = json.loads(cleaned)

                # Validate with Pydantic
                result = schema.model_validate(data)
                return result

            except (json.JSONDecodeError, ValueError) as e:
                if attempt >= self._max_retries:
                    raise LLMStructuredOutputException(
                        f"Failed to produce valid structured output after "
                        f"{self._max_retries} retries: {str(e)}",
                        provider=self.active_provider,
                        retries=attempt + 1,
                    ) from e
                logger.warning(
                    f"Structured output attempt {attempt + 1} failed: {e}. Retrying..."
                )

        # Should not reach here
        raise LLMStructuredOutputException(
            "Unexpected: max retries exceeded without exception",
            provider=self.active_provider,
        )

    def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Generate a streaming text response.

        Args:
            prompt: The user prompt text.
            system_prompt: Optional system prompt.
            model: Override model.
            **kwargs: Additional API parameters.

        Yields:
            Text chunks as they arrive from the API.
        """
        provider_config = self.providers[self.active_provider]
        client = provider_config.get("client")
        if client is None:
            yield ""
            return

        model_name = model or provider_config["model"]

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        params: dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "stream": True,
            **DEFAULT_LLM_PARAMS,
        }
        params.update(kwargs)

        try:
            stream = client.chat.completions.create(**params)
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield ""

    def generate_with_meta(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate text with AIQualityMeta attached.

        Args:
            prompt: The user prompt text.
            system_prompt: Optional system prompt.
            model: Override model.
            **kwargs: Additional API parameters.

        Returns:
            Dict with 'content' (str) and 'ai_quality' (AIQualityMeta).
        """
        from datetime import datetime

        from app.models.common import AIQualityMeta

        provider_config = self.providers[self.active_provider]
        model_name = model or provider_config["model"]

        content = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model_name,
            **kwargs,
        )

        meta = AIQualityMeta(
            confidence=0.85,
            data_source=model_name,
            model_version=model_name,
            generated_at=datetime.now(UTC)
            .isoformat()
            .replace("+00:00", "Z"),
        )

        return {"content": content, "ai_quality": meta.model_dump()}

    # ==================== Vision (GLM-5V-Turbo) ====================

    def vision_generate(
        self,
        image_url: str | None = None,
        video_url: str | None = None,
        file_url: str | None = None,
        prompt: str = "鎻忚堪杩欏紶鍥剧墖",
        **kwargs: Any,
    ) -> str:
        """Generate text from image/video using GLM-5V-Turbo.

        IMPORTANT: Only one non-text modality per request.
        Cannot combine image + video in one call.

        Args:
            image_url: URL or base64 of the image.
            video_url: URL of the video.
            file_url: URL of the file.
            prompt: Text prompt for the vision model.
            **kwargs: Additional API parameters.

        Returns:
            Text description/analysis of the visual content.

        Raises:
            ModalityLimitException: If more than one non-text modality provided.
        """
        from app.core.exceptions import LLMException, ModalityLimitException

        # Enforce modality limit
        modalities = [
            m
            for m in [image_url, video_url, file_url]
            if m is not None
        ]
        if len(modalities) > 1:
            raise ModalityLimitException(
                "Only one non-text modality (image/video/file) allowed per "
                "GLM-5V-Turbo request."
            )

        glm_config = self.providers["glm"]
        model_name = glm_config["model"]

        # Build message content
        content_parts: list[dict[str, Any]] = []

        if image_url:
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": image_url},
            })
        elif video_url:
            content_parts.append({
                "type": "video_url",
                "video_url": {"url": video_url},
            })
        elif file_url:
            content_parts.append({
                "type": "file_url",
                "file_url": {"url": file_url},
            })

        content_parts.append({"type": "text", "text": prompt})

        try:
            # Use ZhipuAI SDK for GLM
            from zhipuai import ZhipuAI

            client = ZhipuAI(api_key=self.settings.zhipu_api_key)
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": content_parts}],
                **kwargs,
            )
            return response.choices[0].message.content or ""
        except ImportError:
            logger.error("zhipuai SDK not installed for GLM vision")
            raise LLMException(
                "GLM Vision SDK not available",
                provider="glm",
                model_version=model_name,
            ) from None
        except Exception as e:
            raise LLMException(
                f"GLM vision generation failed: {str(e)}",
                provider="glm",
                model_version=model_name,
            ) from e

    # ==================== Degradation & Health ====================

    def get_function_tier_info(self, function_name: str) -> dict[str, Any]:
        """Get the degradation tier info for a function.

        Args:
            function_name: Name of the function/service.

        Returns:
            Dict with tier, fallback, action, and message keys.
        """
        return get_fallback_action(function_name)

    def health_check(self) -> dict[str, Any]:
        """Check the health status of all LLM providers.

        Returns:
            Dict mapping provider names to their availability status.
        """
        status = {"active_provider": self.active_provider}

        for name, config in self.providers.items():
            api_key_available = False
            if name == "deepseek":
                api_key_available = bool(self.settings.deepseek_api_key)
            elif name == "qwen":
                api_key_available = bool(self.settings.dashscope_api_key)
            elif name == "glm":
                api_key_available = bool(self.settings.zhipu_api_key)

            status[name] = {
                "available": api_key_available,
                "model": config["model"],
            }

        return status

    @staticmethod
    def _is_rate_limit_error(status_code: int) -> bool:
        """Check if an HTTP status code indicates rate limiting.

        Args:
            status_code: HTTP status code.

        Returns:
            True if status is 429 (Too Many Requests).
        """
        return status_code == 429


# ==================== Helper Functions ====================


def _clean_json_response(raw: str) -> str:
    """Clean LLM response to extract valid JSON.

    Handles markdown code fences, leading/trailing whitespace,
    and common LLM output artifacts.

    Args:
        raw: Raw LLM response text.

    Returns:
        Cleaned JSON string.
    """
    raw = raw.strip()

    # Remove markdown code fences
    if raw.startswith("```"):
        # Find the end of the opening fence
        newline_idx = raw.find("\n")
        if newline_idx != -1:
            raw = raw[newline_idx + 1:]
        # Remove closing fence
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    # Remove any leading/trailing non-JSON text
    # Try to find the first { and last }
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw = raw[start:end + 1]

    return raw


def wrap_user_input(text: str | None) -> str:
    """Wrap untrusted user input in XML delimiters for prompt-injection defense.

    Pairs of ``<user_input>...</user_input>`` tags let the LLM distinguish
    the system-prompt scaffold from caller-supplied content (D6 of the
    foundation plan, Constitution Principle XIII). Both the opening and
    closing delimiter literals are HTML-escaped inside the payload, so a
    malicious caller cannot nest a fake ``<user_input>`` block or close
    the real one early to inject instructions into the surrounding
    template context.

    Args:
        text: Untrusted caller content (None treated as empty string).

    Returns:
        The input wrapped in a single closed ``<user_input>...</user_input>``
        pair with inner delimiter tags escaped.
    """
    safe = (text or "").replace("</user_input>", "&lt;/user_input&gt;")
    safe = safe.replace("<user_input>", "&lt;user_input&gt;")
    return f"<user_input>{safe}</user_input>"

