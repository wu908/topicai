"""Publish advisor chain for TopicAI v4.0."""

import logging

logger = logging.getLogger(__name__)


class PublishChain:
    def __init__(self, llm_client=None):
        self.llm = llm_client

    def run(self, platform: str, content_type: str) -> list:
        return []
