"""Topic recommendation chain for TopicAI v4.0."""

import logging

logger = logging.getLogger(__name__)


class TopicChain:
    """LLM chain for topic recommendation generation."""

    def __init__(self, llm_client=None):
        self.llm = llm_client

    def run(self, trends: list[dict], profile: dict) -> dict:
        return {"topics": trends[:5] if trends else []}
