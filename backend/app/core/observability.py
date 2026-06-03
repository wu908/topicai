"""Observability service for TopicAI v4.0.

LangFuse LLM tracing encapsulation.
Disabled by default (test environment / no API key).
"""

import logging
from typing import Any

from config.settings import get_settings

logger = logging.getLogger(__name__)


class ObservabilityService:
    """LangFuse-based LLM observability.

    Provides tracing hooks for LLM calls including trace_id,
    generation metadata, and cost tracking.
    """

    def __init__(self):
        settings = get_settings()
        self._public_key = settings.langfuse_public_key
        self._secret_key = settings.langfuse_secret_key
        self.enabled: bool = bool(self._public_key and self._secret_key)

    def trace(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new trace.

        Args:
            name: Trace name.
            metadata: Optional metadata.

        Returns:
            Trace context dict with trace_id.
        """
        if not self.enabled:
            return {"trace_id": "", "enabled": False}

        import uuid
        trace_id = str(uuid.uuid4())
        logger.debug(f"LangFuse trace created: {name} [{trace_id}]")
        return {"trace_id": trace_id, "name": name, "metadata": metadata or {}, "enabled": True}

    def generation(
        self,
        trace_id: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> None:
        """Log a generation event.

        Args:
            trace_id: Parent trace ID.
            model: Model name.
            prompt_tokens: Input token count.
            completion_tokens: Output token count.
        """
        if not self.enabled or not trace_id:
            return
        logger.debug(
            f"LangFuse generation: model={model}, "
            f"prompt_tokens={prompt_tokens}, completion_tokens={completion_tokens}"
        )
