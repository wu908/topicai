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

    # ==================== Spec-007 US6 (T079-T080) ====================

    def derive_rubric_weights(self, request) -> dict:
        """Derive initial 5-dimension rubric_weights via LLM, with fallback.

        Spec-007 US6 (T079-T080): LLM-first pattern mirroring
        US5 ``ContentRiskService`` and US4 ``EffectReviewChain``. Any
        LLM failure (api error, JSON parse, schema mismatch) logs and
        falls back to a deterministic heuristic distribution; the
        response carries AI transparency meta per Constitution III.

        Args:
            request: ``OnboardingRequest`` Pydantic model.

        Returns:
            Dict with keys:
              - ``rubric_weights`` (dict[str, float], 5 dims, sum ≈ 1.0)
              - ``data_source`` ("llm_simulation" | "template_fallback")
              - ``confidence`` (float, [0.0, 1.0])
              - ``model_version`` (str)
        """
        from pydantic import BaseModel, Field

        class _RubricOutput(BaseModel):
            rubric_weights: dict[str, float] = Field(...)
            model_version: str = Field(default="onboarding_rubric.v1")

        from app.core.llm import wrap_user_input

        attributes = wrap_user_input(
            f"track={request.track}, "
            f"content_formats={request.content_formats}, "
            f"production_complexity={request.production_complexity}, "
            f"content_depth={request.content_depth}, "
            f"hotspot_preference={request.hotspot_preference}"
        )
        prompt = (
            "Generate initial 5-dimension rubric_weights for a creator "
            f"with these attributes: {attributes}. "
            "Return JSON with keys: rubric_weights (object with "
            "track_match, format_match, hotspot_relevance, timeliness, "
            "data_quality summing to 1.0) and model_version."
        )

        try:
            llm = self._get_llm()
            output = llm.generate_structured(
                prompt=prompt, schema=_RubricOutput,
            )
            # Normalize to ensure 5 canonical dims + sum=1.0
            weights = self._normalize_5d_weights(output.rubric_weights)
            return {
                "rubric_weights": weights,
                "data_source": "llm_simulation",
                "confidence": 0.75,
                "model_version": output.model_version or "onboarding_rubric.v1",
            }
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "onboarding.derive_rubric_weights.llm_fallback: %s", e,
            )
            return {
                "rubric_weights": self._heuristic_rubric_weights(request),
                "data_source": "template_fallback",
                "confidence": 0.4,
                "model_version": "onboarding_rubric.v1-heuristic",
            }

    @staticmethod
    def _heuristic_rubric_weights(request) -> dict[str, float]:
        """Deterministic 5-dim fallback distribution based on input signals.

        - hotspot_preference in {"追热点", "high"} → boost hotspot_relevance
        - production_complexity in {"high"} → boost data_quality
        - format-rich (≥2 content_formats) → boost format_match
        - otherwise default balanced 5-dim (0.30/0.25/0.20/0.15/0.10)
        """
        if getattr(request, "hotspot_preference", None) in ("追热点", "high"):
            base = {
                "hotspot_relevance": 0.40,
                "track_match": 0.25,
                "format_match": 0.15,
                "data_quality": 0.10,
                "timeliness": 0.10,
            }
        else:
            base = {
                "track_match": 0.30,
                "format_match": 0.25,
                "data_quality": 0.20,
                "hotspot_relevance": 0.15,
                "timeliness": 0.10,
            }
        # If multiple content_formats, nudge format_match up
        formats = getattr(request, "content_formats", None) or []
        if len(formats) >= 2:
            base["format_match"] += 0.05
            base["track_match"] -= 0.05
        return {k: round(v, 4) for k, v in base.items()}

    @staticmethod
    def _normalize_5d_weights(weights: dict[str, float]) -> dict[str, float]:
        """Coerce arbitrary LLM weights to 5 canonical dims, sum=1.0.

        Drops unknown dims, fills missing dims with proportional spread
        of the dropped mass. Falls back to balanced default if input is
        empty/all-zero.
        """
        canonical = ["track_match", "format_match", "hotspot_relevance",
                     "timeliness", "data_quality"]
        cleaned = {k: max(0.0, float(weights.get(k, 0.0))) for k in canonical}
        total = sum(cleaned.values())
        if total <= 0:
            return {k: round(1.0 / 5, 4) for k in canonical}
        return {k: round(v / total, 4) for k, v in cleaned.items()}

