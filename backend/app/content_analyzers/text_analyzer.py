"""Text content analyzer for TopicAI v4.0.

Extracts and preprocesses text content for analysis.
"""

import logging

from app.content_analyzers.base import ContentAnalyzer

logger = logging.getLogger(__name__)


class TextAnalyzer(ContentAnalyzer):
    """Text content preprocessor and analyzer.

    Extracts clean text, identifies structure, and prepares
    content for downstream LLM analysis chains.
    """

    def __init__(self):
        pass

    def analyze(self, text: str) -> dict:
        """Analyze text content.

        Args:
            text: Raw text content.

        Returns:
            Dict with extracted_text, word_count, structure hints.
        """
        if not text or not text.strip():
            return {"extracted_text": "", "word_count": 0, "error": "empty"}

        cleaned = text.strip()
        word_count = len(cleaned)

        return {
            "extracted_text": cleaned[:10000],
            "word_count": word_count,
            "supported_input_type": "text",
        }

    @property
    def supported_input_type(self) -> str:
        return "text"
