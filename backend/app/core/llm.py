"""Single OpenAI-compatible LLM boundary used by the v2 product."""

import json
import logging
import re
from typing import Any, TypeVar

from openai import OpenAI
from pydantic import BaseModel

from config.llm_config import DEFAULT_LLM_PARAMS, get_compatible_llm_config
from config.settings import get_settings

logger = logging.getLogger(__name__)
T = TypeVar("T")

# Wrapper-tag variants that untrusted text must not be able to emit. Tolerate
# case differences and internal whitespace so ``</USER_INPUT>`` / ``</user_input >``
# are neutralized just like the canonical lowercase form.
_CLOSING_USER_INPUT_TAG = re.compile(r"<\s*/\s*user_input\s*>", re.IGNORECASE)
_OPENING_USER_INPUT_TAG = re.compile(r"<\s*user_input\s*>", re.IGNORECASE)


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
        from app.core.exceptions import (
            AICapabilityMissingException,
            AINotConfiguredException,
            LLMException,
            LLMTimeoutException,
        )

        if not self.settings.ai_enabled or self.client is None:
            raise AINotConfiguredException()
        if "text" not in self.capabilities:
            raise AICapabilityMissingException("text")

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

        instruction = (
            "Respond only with valid JSON matching the requested schema.\n"
            # 只写"匹配 schema"是不够的：schema 从未发给模型，模型只能猜字段名与
            # 结构——实测线上观点提炼连续 4 次解析失败后降级。这里把模型的字段
            # 骨架（名字 + 类型 + 字面量取值）明写进系统提示，所有调用方一起受益。
            "Use exactly these fields and types:\n"
            f"{_schema_skeleton(schema)}"
        )
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
        from app.core.exceptions import (
            AICapabilityMissingException,
            AINotConfiguredException,
            LLMException,
        )

        if not self.settings.ai_enabled or self.client is None:
            raise AINotConfiguredException()
        if not self.settings.vision_enabled or "vision" not in self.capabilities:
            raise AICapabilityMissingException("vision")
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




def _schema_skeleton(model: type[Any], _depth: int = 0) -> str:
    """把 pydantic 模型摊成一个可直接照抄的 JSON 骨架示例。

    只用于提示词：给出字段名、类型与字面量取值，避免模型靠猜。
    """
    if _depth > 3:  # 防御自引用模型
        return "{...}"

    def sample(annotation: Any) -> Any:
        import typing

        origin = typing.get_origin(annotation)
        args = typing.get_args(annotation)
        if origin is typing.Union or str(origin) == "types.UnionType":
            # Optional[X] → 用 X 的骨架（null 由模型按语义决定）
            concrete = [a for a in args if a is not type(None)]
            return sample(concrete[0]) if concrete else None
        if origin is typing.Literal:
            return args[0] if args else ""
        if origin in (list, tuple, set):
            return [sample(args[0])] if args else []
        if origin is dict:
            return {}
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            fields = {
                name: sample(field.annotation)
                for name, field in annotation.model_fields.items()
            }
            return fields
        if annotation is bool:
            return False
        if annotation is int:
            return 0
        if annotation is float:
            return 0.0
        return ""

    import json as _json

    fields = {
        name: sample(field.annotation)
        for name, field in model.model_fields.items()
    }
    return _json.dumps(fields, ensure_ascii=False, indent=2)


def _clean_json_response(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw[raw.find("\n") + 1 :]
        if raw.endswith("```"):
            raw = raw[:-3]
    start, end = raw.find("{"), raw.rfind("}")
    return raw[start : end + 1] if 0 <= start < end else raw.strip()


def wrap_user_input(text: str | None) -> str:
    """Delimit untrusted text without allowing it to close the wrapper.

    Matching is case-insensitive and tolerates internal whitespace, so
    variants such as ``</USER_INPUT>`` or ``</user_input >`` cannot emit a
    closing-tag-like sequence and break out of the delimiter.
    """
    safe = _CLOSING_USER_INPUT_TAG.sub("&lt;/user_input&gt;", text or "")
    safe = _OPENING_USER_INPUT_TAG.sub("&lt;user_input&gt;", safe)
    return f"<user_input>{safe}</user_input>"
