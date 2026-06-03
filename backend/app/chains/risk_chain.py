"""Content risk chain for TopicAI v4.0."""

import logging

logger = logging.getLogger(__name__)


class RiskChain:
    def __init__(self, llm_client=None):
        self.llm = llm_client

    def run(self, content: str) -> dict:
        return {"risks": [], "score": 0.0}
