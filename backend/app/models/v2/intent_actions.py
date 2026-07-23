"""Typed contracts for intent-driven content orchestration."""

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ContentIntent(StrEnum):
    SOLVE = "solve"
    SHARE = "share"
    RECORD = "record"


class IntentStatus(StrEnum):
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"
    LEGACY_MISSING = "legacy_missing"


class AutomationLevel(StrEnum):
    GUIDED = "guided"
    AUTOPILOT_TO_READY = "autopilot_to_ready"


class HumanGateType(StrEnum):
    INTENT = "intent"
    USER_FACT = "user_fact"
    CONTENT_VERSION = "content_version"
    PUBLIC_SCOPE = "public_scope"
    PUBLICATION = "publication"
    LONG_TERM_LEARNING = "long_term_learning"
    PRIVACY = "privacy"
    DELETION = "deletion"


class ActionType(StrEnum):
    CREATE_PROJECT = "create_project"
    CONFIRM_INTENT = "confirm_intent"
    ANSWER_KEY_QUESTION = "answer_key_question"
    REVIEW_CANDIDATE = "review_candidate"
    CONFIRM_PUBLISH_SCOPE = "confirm_publish_scope"
    RECORD_PUBLICATION = "record_publication"
    ADD_PERFORMANCE = "add_performance"
    REVIEW_RESULT = "review_result"
    CONFIRM_LEARNING = "confirm_learning"
    MANAGE_LEARNING = "manage_learning"


class IntentConfirmation(StrictModel):
    content_intent: ContentIntent
    audience_change: str = Field(min_length=1, max_length=1000)
    material_requirements: list[str] = Field(default_factory=list, max_length=20)
    expected_responses: list[str] = Field(default_factory=list, max_length=20)
    success_signals: list[str] = Field(default_factory=list, max_length=20)
    expected_project_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


ActionDecision = Literal["accept", "defer", "reject", "manual"]


class ActionResponse(StrictModel):
    decision: ActionDecision
    response_payload: dict[str, Any] = Field(default_factory=dict)
    expected_action_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def require_rejection_reason(self):
        if self.decision == "reject" and not str(
            self.response_payload.get("reason", "")
        ).strip():
            raise ValueError("rejection reason is required")
        if "available_minutes" in self.response_payload:
            value = self.response_payload["available_minutes"]
            if self.decision != "reject":
                raise ValueError("available_minutes is only accepted with a rejection")
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError("available_minutes must be a non-negative integer")
        return self


class ActionLifecycleCommand(StrictModel):
    operation: Literal["fail", "expire", "cancel"]
    reason: str = Field(min_length=1, max_length=500)
    error_code: str | None = Field(default=None, max_length=100)
    expected_action_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class HumanGateDecision(StrictModel):
    decision: Literal["confirm", "reject"]
    decision_payload: dict[str, Any] = Field(default_factory=dict)
    expected_gate_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class AccountGateRequest(StrictModel):
    idempotency_key: str = Field(min_length=1, max_length=200)


class OrchestratorCandidate(StrictModel):
    action_type: ActionType
    title: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2000)
    evidence_refs: list[str] = Field(default_factory=list)
    unknown_refs: list[str] = Field(default_factory=list)
    expected_state_change: dict[str, Any] = Field(default_factory=dict)
    estimated_effort_minutes: int = Field(ge=0, le=240)
    human_gate: HumanGateType | None = None
    fallback_action: dict[str, Any]


class CandidateDraft(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    body_text: str = Field(min_length=1)
    cover_plan: str = Field(default="", max_length=1000)
    evidence_refs: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class AutomationPreference(StrictModel):
    automation_level: AutomationLevel
    explicit_consent: bool
    expected_creator_state_version: int = Field(ge=1)
    expected_project_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def require_consent_for_autopilot(self):
        if self.automation_level == AutomationLevel.AUTOPILOT_TO_READY and not self.explicit_consent:
            raise ValueError("explicit consent is required for automatic preparation")
        return self
