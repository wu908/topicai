"""Optional tracing seam kept for legacy callers."""

import logging
import uuid
from typing import Any

from config.settings import get_settings

logger = logging.getLogger(__name__)


class ObservabilityService:
    def __init__(self):
        settings = get_settings()
        self.enabled = bool(settings.langfuse_public_key and settings.langfuse_secret_key)

    def trace(self, name: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.enabled:
            return {"trace_id": "", "enabled": False}
        return {"trace_id": str(uuid.uuid4()), "name": name, "metadata": metadata or {}, "enabled": True}

    def generation(self, trace_id: str, model: str, prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        if self.enabled and trace_id:
            logger.debug("LLM generation: model=%s prompt_tokens=%s completion_tokens=%s", model, prompt_tokens, completion_tokens)
