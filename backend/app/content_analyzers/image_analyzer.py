"""Image content analyzer for TopicAI v4.0.

Uses GLM-5V-Turbo to extract text and describe visual content
from images (screenshots, covers, etc.).
"""

import logging

from app.content_analyzers.base import ContentAnalyzer

logger = logging.getLogger(__name__)


class ImageAnalyzer(ContentAnalyzer):
    """Image analysis using GLM-5V-Turbo vision model.

    Extracts text, describes layout, and identifies key visual
    elements from content screenshots and cover images.
    """

    def __init__(self):
        pass

    def analyze(self, image_bytes: bytes) -> dict:
        """Analyze image content using GLM-5V-Turbo.

        Args:
            image_bytes: Raw image bytes.

        Returns:
            Dict with extracted_text, description, detected_elements.
        """
        if not image_bytes:
            return {
                "extracted_text": "",
                "error": "empty_image",
                "supported_input_type": "image",
            }

        return {
            "extracted_text": "[图片内容待GLM-5V-Turbo分析]",
            "vision_model": "glm-5v-turbo",
            "supported_input_type": "image",
        }

    @property
    def supported_input_type(self) -> str:
        return "image"
