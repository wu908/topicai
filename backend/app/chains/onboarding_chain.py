"""Onboarding Chain for TopicAI v4.0.

LangChain-based chain for multi-round conversational onboarding.
Collects user preferences and outputs a structured CreatorProfile.
"""

import logging

logger = logging.getLogger(__name__)


class OnboardingChain:
    """Chain for onboarding conversation and profile generation.

    Uses LLM to parse user answers and generate a structured CreatorProfile
    with appropriate recommendation mode and rubric weights.
    """

    def __init__(self, llm_client=None):
        """Initialize onboarding chain.

        Args:
            llm_client: LLMClient instance.
        """
        self.llm = llm_client

    def run(self, answers: dict) -> dict:
        """Run the onboarding analysis and generate profile data.

        Args:
            answers: Dict with onboarding answers.

        Returns:
            Dict with profile fields including recommendation_mode
            and rubric_weights.
        """
        track = answers.get("track", "")
        hotspot_pref = answers.get("hotspot_preference", "追热点")
        content_depth = answers.get("content_depth", "medium")
        formats = answers.get("content_formats", [])

        # Determine recommendation mode
        if hotspot_pref == "追热点":
            recommendation_mode = "hotspot_fusion"
        else:
            recommendation_mode = "evergreen_deep"

        # Generate rubric weights based on preferences
        rubric_weights = self._compute_rubric_weights(
            hotspot_pref, content_depth, formats
        )

        return {
            "track": track,
            "recommendation_mode": recommendation_mode,
            "rubric_weights": rubric_weights,
        }

    def _compute_rubric_weights(
        self,
        hotspot_preference: str,
        content_depth: str,
        formats: list[str],
    ) -> dict[str, float]:
        """Compute initial rubric weights based on user preferences.

        Args:
            hotspot_preference: Hotspot preference.
            content_depth: Content depth level.
            formats: Content format list.

        Returns:
            Dict of 7-dimension rubric weights summing to 1.0.
        """
        weights = {
            "track_match": 0.30,
            "format_match": 0.20,
            "data_quality": 0.15,
            "hotspot_relevance": 0.15,
            "content_depth_match": 0.10,
            "production_complexity_match": 0.05,
            "timeliness": 0.05,
        }

        # Adjust for hotspot preference
        if hotspot_preference == "追热点":
            weights["hotspot_relevance"] = 0.25
            weights["timeliness"] = 0.10
            weights["track_match"] = 0.25
            weights["content_depth_match"] = 0.05
        else:
            weights["content_depth_match"] = 0.20
            weights["hotspot_relevance"] = 0.05
            weights["timeliness"] = 0.03

        # Adjust for content depth
        if content_depth == "deep":
            weights["content_depth_match"] += 0.05
            weights["hotspot_relevance"] = max(0.0, weights["hotspot_relevance"] - 0.05)

        # Normalize to sum to 1.0
        total = sum(weights.values())
        for key in weights:
            weights[key] = round(weights[key] / total, 4)

        return weights
