"""Single OpenAI-compatible LLM boundary used by the v2 product."""

import json
import logging
from typing import Any, TypeVar

from openai import OpenAI

from config.llm_config import DEFAULT_LLM_PARAMS, get_compatible_llm_config
from config.settings import get_settings

logger = logging.getLogger(__name__)
T = TypeVar("T")


class LLMClient:
    def __init__(self):
        self.settings = get_settings()
        config = get_compatible_llm_config(self.settings)
        self.model = config["model"]
        self.capabilities = config["capabilities"]
        self.timeout = config["timeout"]
        self.client = (
            OpenAI(
                api_key=config["api_key"],
                base_url=config["base_url"],
                timeout=config["timeout"],
            )
            if config["configured"]
            else None
        )
        self._max_retries = 2

    def get_capabilities(self) -> set[str]:
        return set(self.capabilities)

    def is_available(self, capability: str = "text") -> bool:
        if capability == "vision" and not self.settings.vision_enabled:
            return False
        return bool(
            self.settings.ai_enabled
            and self.client is not None
            and capability in self.capabilities
        )

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        from app.core.exceptions import LLMException, LLMTimeoutException

        if not self.is_available("text"):
            raise LLMException("LLM is not configured", provider="openai_compatible")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        params = {
            "model": model or self.model,
            "messages": messages,
            **DEFAULT_LLM_PARAMS,
            **kwargs,
        }
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens

        try:
            response = self.client.chat.completions.create(**params)
            return response.choices[0].message.content or ""
        except Exception as exc:
            if "timeout" in str(exc).lower():
                raise LLMTimeoutException(
                    provider="openai_compatible", timeout_seconds=self.timeout
                ) from exc
            raise LLMException(
                f"LLM generation failed: {exc}",
                provider="openai_compatible",
                model_version=model or self.model,
            ) from exc

    def generate_structured(
        self,
        prompt: str,
        schema: type[T],
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> T:
        from app.core.exceptions import LLMStructuredOutputException

        instruction = "Respond only with valid JSON matching the requested schema."
        system = f"{system_prompt}\n\n{instruction}" if system_prompt else instruction
        for attempt in range(self._max_retries + 1):
            try:
                data = json.loads(_clean_json_response(self.generate(prompt, system, **kwargs)))
                return schema.model_validate(data)
            except (json.JSONDecodeError, ValueError) as exc:
                if attempt == self._max_retries:
                    raise LLMStructuredOutputException(
                        f"Invalid structured output after {attempt + 1} attempts: {exc}",
                        provider="openai_compatible",
                        retries=attempt + 1,
                    ) from exc
                logger.warning("Invalid structured LLM output; retrying")
        raise AssertionError("unreachable")

    def vision_generate(self, image_url: str, prompt: str) -> str:
        from app.core.exceptions import LLMException

        if not self.is_available("vision"):
            raise LLMException("Vision is not enabled", provider="openai_compatible")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }
                ],
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise LLMException(
                f"Vision generation failed: {exc}",
                provider="openai_compatible",
                model_version=self.model,
            ) from exc


def _clean_json_response(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw[raw.find("\n") + 1 :]
        if raw.endswith("```"):
            raw = raw[:-3]
    start, end = raw.find("{"), raw.rfind("}")
    return raw[start : end + 1] if 0 <= start < end else raw.strip()


def wrap_user_input(text: str | None) -> str:
    """Delimit untrusted text without allowing it to close the wrapper."""
    safe = (text or "").replace("</user_input>", "&lt;/user_input&gt;")
    safe = safe.replace("<user_input>", "&lt;user_input&gt;")
    return f"<user_input>{safe}</user_input>"
