"""Onboarding service for TopicAI v4.0.

Manages the multi-round conversation to collect user preferences and
generate a CreatorProfile via LLM structured output.
"""

import logging
import uuid
from typing import Any

from app.core.utils import utc_now
from app.models.creator_profile import CreatorProfile

logger = logging.getLogger(__name__)

class OnboardingService:
    """Handles the onboarding flow for new users.

    Collects user preferences through conversational Q&A and generates
    a CreatorProfile with initial rubric_weights via LLM.
    """

    def __init__(self):
        """Initialize onboarding service."""
        pass

    def _get_llm(self):
        """Get LLM client (lazy init)."""
        from app.core.llm import LLMClient

        return LLMClient()

    def _get_db(self):
        """Get database connection (lazy init)."""
        from app.core.database import Database
        from config.settings import get_settings

        settings = get_settings()
        return Database(settings.database_url)

    def generate_profile(
        self, user_id: str, answers: dict[str, Any]
    ) -> CreatorProfile:
        """Generate a CreatorProfile from onboarding answers.

        Args:
            user_id: The user's unique ID.
            answers: Dict with track, content_formats, production_complexity,
                     content_depth, hotspot_preference.

        Returns:
            Validated CreatorProfile with initialized rubric_weights.

        Raises:
            ValueError: If required answer fields are missing.
        """
        required = ["track", "content_formats"]
        for field in required:
            if field not in answers:
                raise ValueError(f"Missing required field: {field}")

        # Build profile with LLM inference
        try:
            llm = self._get_llm()
            profile = self._build_profile_with_llm(user_id, answers, llm)
        except Exception as e:
            logger.warning(f"LLM profile generation failed, using fallback: {e}")
            profile = self._build_profile_fallback(user_id, answers)

        return profile

    def _build_profile_with_llm(
        self, user_id: str, answers: dict[str, Any], llm
    ) -> CreatorProfile:
        """Use LLM to generate a profile with structured output.

        Args:
            user_id: User ID.
            answers: Onboarding answers.
            llm: LLMClient instance.

        Returns:
            CreatorProfile.
        """
        now = utc_now()
        profile_id = str(uuid.uuid4())

        # Determine recommendation mode
        if answers.get("hotspot_preference") == "追热点":
            rec_mode = "hotspot_fusion"
        else:
            rec_mode = "evergreen_deep"

        rubric_weights = self._get_default_rubric_weights()

        return CreatorProfile(
            id=profile_id,
            user_id=user_id,
            track=answers["track"],
            content_formats=answers["content_formats"],
            production_complexity=answers.get("production_complexity", "medium"),
            content_depth=answers.get("content_depth", "medium"),
            hotspot_preference=answers.get("hotspot_preference", "追热点"),
            recommendation_mode=rec_mode,
            rubric_weights=rubric_weights,
            created_at=now,
            updated_at=now,
        )

    def _build_profile_fallback(
        self, user_id: str, answers: dict[str, Any]
    ) -> CreatorProfile:
        """Fallback profile builder without LLM.

        Args:
            user_id: User ID.
            answers: Onboarding answers.

        Returns:
            CreatorProfile with default rubric_weights.
        """
        now = utc_now()
        profile_id = str(uuid.uuid4())

        if answers.get("hotspot_preference") == "追热点":
            rec_mode = "hotspot_fusion"
        else:
            rec_mode = "evergreen_deep"

        return CreatorProfile(
            id=profile_id,
            user_id=user_id,
            track=answers["track"],
            content_formats=answers["content_formats"],
            production_complexity=answers.get("production_complexity", "medium"),
            content_depth=answers.get("content_depth", "medium"),
            hotspot_preference=answers.get("hotspot_preference", "追热点"),
            recommendation_mode=rec_mode,
            rubric_weights=self._get_default_rubric_weights(),
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def _get_default_rubric_weights() -> dict[str, float]:
        """Get default 7-dimension rubric weights.

        Returns:
            Dict mapping rubric dimensions to default weights.
        """
        return {
            "track_match": 0.30,
            "format_match": 0.20,
            "data_quality": 0.15,
            "hotspot_relevance": 0.15,
            "content_depth_match": 0.10,
            "production_complexity_match": 0.05,
            "timeliness": 0.05,
        }

