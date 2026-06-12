"""TDD tests for TierConfig (Spec-007 T009)."""

from __future__ import annotations

import pytest

from app.config.data_source_config import TIER_CONFIGS, TierConfig, get_tier_config


class TestTierConfigDefaults:
    def test_all_four_tiers_present(self):
        assert set(TIER_CONFIGS) == {"tianapi", "bilibili", "llm_simulation", "preloaded"}

    def test_get_tier_config_returns_known(self):
        cfg = get_tier_config("tianapi")
        assert cfg.name == "tianapi"
        assert cfg.timeout_seconds == 3.0
        assert cfg.max_retries == 1
        assert cfg.circuit_breaker_threshold == 3
        assert cfg.circuit_breaker_cooldown_seconds == 30.0

    def test_get_tier_config_unknown_raises(self):
        with pytest.raises(KeyError):
            get_tier_config("does_not_exist")

    def test_llm_simulation_has_more_headroom_than_http(self):
        llm = get_tier_config("llm_simulation")
        tian = get_tier_config("tianapi")
        assert llm.timeout_seconds >= tian.timeout_seconds

    def test_negative_timeout_rejected(self):
        with pytest.raises(ValueError, match="timeout_seconds"):
            TierConfig("x", timeout_seconds=-1, max_retries=0, circuit_breaker_threshold=1, circuit_breaker_cooldown_seconds=1.0)

    def test_negative_retries_rejected(self):
        with pytest.raises(ValueError, match="max_retries"):
            TierConfig("x", timeout_seconds=1, max_retries=-1, circuit_breaker_threshold=1, circuit_breaker_cooldown_seconds=1.0)

    def test_zero_breaker_threshold_rejected(self):
        with pytest.raises(ValueError, match="circuit_breaker_threshold"):
            TierConfig("x", timeout_seconds=1, max_retries=0, circuit_breaker_threshold=0, circuit_breaker_cooldown_seconds=1.0)

    def test_zero_cooldown_rejected(self):
        with pytest.raises(ValueError, match="circuit_breaker_cooldown_seconds"):
            TierConfig("x", timeout_seconds=1, max_retries=0, circuit_breaker_threshold=1, circuit_breaker_cooldown_seconds=0)
