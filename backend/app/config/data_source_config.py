"""Per-tier data source configuration (Spec-007 T009, FR-004).

Each data source tier (TianAPI, Bilibili, LLM, Preloaded) gets a
``TierConfig`` dataclass that pins:

* ``timeout_seconds`` — single request budget
* ``max_retries`` — retries on transient failure
* ``circuit_breaker_threshold`` — consecutive failures before
  the tier is treated as unavailable
* ``circuit_breaker_cooldown_seconds`` — half-open window before
  retrying the tier

Per Constitution Principle VIII, every tier MUST have these settings
explicitly set; no implicit defaults at call sites.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TierConfig:
    """Per-tier configuration for the data source cascade."""

    name: str
    timeout_seconds: float
    max_retries: int
    circuit_breaker_threshold: int
    circuit_breaker_cooldown_seconds: float

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError(f"{self.name}: timeout_seconds must be > 0")
        if self.max_retries < 0:
            raise ValueError(f"{self.name}: max_retries must be >= 0")
        if self.circuit_breaker_threshold < 1:
            raise ValueError(f"{self.name}: circuit_breaker_threshold must be >= 1")
        if self.circuit_breaker_cooldown_seconds <= 0:
            raise ValueError(f"{self.name}: circuit_breaker_cooldown_seconds must be > 0")


# Default per-tier configs (Spec-007 T009: timeout=3s, retry=1,
# circuit_breaker=3 fails / 30s half-open).
TIER_CONFIGS: dict[str, TierConfig] = {
    "tianapi": TierConfig(
        name="tianapi",
        timeout_seconds=3.0,
        max_retries=1,
        circuit_breaker_threshold=3,
        circuit_breaker_cooldown_seconds=30.0,
    ),
    "bilibili": TierConfig(
        name="bilibili",
        timeout_seconds=3.0,
        max_retries=1,
        circuit_breaker_threshold=3,
        circuit_breaker_cooldown_seconds=30.0,
    ),
    "llm_simulation": TierConfig(
        name="llm_simulation",
        timeout_seconds=10.0,  # LLM calls get more headroom than HTTP
        max_retries=1,
        circuit_breaker_threshold=3,
        circuit_breaker_cooldown_seconds=30.0,
    ),
    "preloaded": TierConfig(
        name="preloaded",
        timeout_seconds=0.1,  # in-memory; should be effectively instant
        max_retries=0,
        circuit_breaker_threshold=10,  # if preloaded fails, something is very wrong
        circuit_breaker_cooldown_seconds=60.0,
    ),
}


def get_tier_config(name: str) -> TierConfig:
    """Return the TierConfig for ``name``; raises KeyError on unknown."""
    return TIER_CONFIGS[name]


__all__ = ["TIER_CONFIGS", "TierConfig", "get_tier_config"]
