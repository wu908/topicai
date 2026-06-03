"""Abstract base class for content analyzers.

Defines the uniform interface that all content analyzers must implement.
"""

from abc import ABC, abstractmethod
from typing import Any


class ContentAnalyzer(ABC):
    """Abstract base for all content analyzers.

    Each analyzer handles a specific input type (text, image, etc.)
    and returns a unified AnalysisResult dict.
    """

    @abstractmethod
    def analyze(self, content: Any) -> dict[str, Any]:
        """Analyze content and return structured results.

        Args:
            content: Raw content (text string, image bytes, etc.).

        Returns:
            Dict with extracted_text, metadata, and optional error info.
        """
        ...

    @property
    @abstractmethod
    def supported_input_type(self) -> str:
        """Return the input type this analyzer supports (e.g., 'text', 'image')."""
        ...


class ContentAnalyzerFactory:
    """Factory for creating content analyzers by input type."""

    _registry: dict[str, type[ContentAnalyzer]] = {}

    @classmethod
    def register(cls, input_type: str, analyzer_cls: type[ContentAnalyzer]) -> None:
        """Register an analyzer class for an input type.

        Args:
            input_type: Input type string.
            analyzer_cls: ContentAnalyzer subclass.
        """
        cls._registry[input_type] = analyzer_cls

    @classmethod
    def create(cls, input_type: str) -> ContentAnalyzer:
        """Create an analyzer instance for the given input type.

        Args:
            input_type: Input type string.

        Returns:
            ContentAnalyzer instance.

        Raises:
            ValueError: If no analyzer registered for the input type.
        """
        if input_type not in cls._registry:
            from app.content_analyzers.image_analyzer import ImageAnalyzer
            from app.content_analyzers.text_analyzer import TextAnalyzer
            cls._registry["text"] = TextAnalyzer
            cls._registry["image"] = ImageAnalyzer

        analyzer_cls = cls._registry.get(input_type)
        if not analyzer_cls:
            raise ValueError(f"No analyzer registered for input type: {input_type}")
        return analyzer_cls()
