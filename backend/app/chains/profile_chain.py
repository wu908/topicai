"""Profile evolution chain for TopicAI v4.0.

Updates rubric_weights based on user feedback patterns.
Implements the cheat-on-content dynamic evolution mechanism.
"""

import logging

logger = logging.getLogger(__name__)


class ProfileChain:
    """Chain for evolving creator profile based on feedback.

    Analyzes feedback patterns and adjusts rubric_weights to better
    match what the user actually engages with.
    """

    def __init__(self, llm_client=None):
        """Initialize profile chain.

        Args:
            llm_client: LLMClient instance.
        """
        self.llm = llm_client

    def evolve_weights(
        self,
        current_weights: dict[str, float],
        feedback_records: list[dict],
    ) -> dict[str, float]:
        """Evolve rubric weights based on feedback.

        Args:
            current_weights: Current rubric weight mapping.
            feedback_records: Recent feedback records (👍👎).

        Returns:
            Updated rubric weights.
        """
        if not feedback_records:
            return current_weights

        new_weights = dict(current_weights)

        # Count feedback by type
        thumbs_up = sum(1 for f in feedback_records if f.get("feedback_type") == "thumb_up")
        thumbs_down = sum(1 for f in feedback_records if f.get("feedback_type") == "thumb_down")
        total = thumbs_up + thumbs_down

        if total == 0:
            return current_weights

        up_ratio = thumbs_up / total

        # Adjust weights: if mostly positive, slightly reinforce current weights
        # If mostly negative, broaden the weights
        if up_ratio >= 0.7:
            # User is happy — reinforce current distribution
            pass
        elif up_ratio <= 0.3:
            # User is unhappy — flatten weights slightly
            flat = 1.0 / len(new_weights)
            for key in new_weights:
                new_weights[key] = round(new_weights[key] * 0.7 + flat * 0.3, 4)

        # Normalize
        total_w = sum(new_weights.values())
        if total_w > 0:
            for key in new_weights:
                new_weights[key] = round(new_weights[key] / total_w, 4)

        return new_weights
