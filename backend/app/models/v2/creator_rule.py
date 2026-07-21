"""Contracts for cross-project creator rule validation and rollback."""

from typing import Any, Literal

from pydantic import Field

from app.models.v2.intent_actions import StrictModel


class RuleCandidateCreate(StrictModel):
    expected_creator_state_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class RuleCandidateDecision(StrictModel):
    decision: Literal["confirm", "reject"]
    expected_candidate_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class RuleRollback(StrictModel):
    target_version_id: str = Field(min_length=1, max_length=100)
    expected_rule_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class RuleConflictResolutionCreate(StrictModel):
    resolution_type: Literal["narrow_scope", "keep_exception", "deactivate"]
    scope: dict[str, Any] | None = None
    expected_rule_version: int = Field(ge=1)
    expected_conflict_rule_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)
