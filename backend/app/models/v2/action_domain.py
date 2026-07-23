"""Read contracts for the AI-native action domain."""

from typing import Any, Literal

from pydantic import Field

from app.models.v2.evidence import (
    EvidenceConfirmationStatus,
    EvidencePrivacyLevel,
    EvidenceSourceType,
)
from app.models.v2.experiment_metrics import ExperimentId
from app.models.v2.intent_actions import (
    ActionType,
    AutomationLevel,
    ContentIntent,
    HumanGateType,
    StrictModel,
)


ActionStatus = Literal[
    "proposed",
    "accepted",
    "deferred",
    "completed",
    "superseded",
    "failed",
    "expired",
    "cancelled",
]
ActionEventType = Literal[
    "proposed",
    "accepted",
    "deferred",
    "manual_selected",
    "completed",
    "superseded",
    "gate_confirmed",
    "gate_rejected",
    "fallback_used",
    "rejected",
    "failed",
    "expired",
    "cancelled",
]
Cohort = Literal["control", "variant", "observational", "excluded"]


class CreatorState(StrictModel):
    id: str
    owner_user_id: str
    facts: list[dict[str, Any]]
    inferences: list[dict[str, Any]]
    validated_insights: list[dict[str, Any]]
    unknowns: list[dict[str, Any]]
    contradictions: list[dict[str, Any]]
    intent_preferences: dict[str, Any]
    current_goal: str
    available_minutes: int | None = Field(default=None, ge=0)
    automation_trust_level: Literal["guided", "eligible", "autopilot_to_ready"]
    completed_project_count: int = Field(ge=0)
    candidate_acceptance_rate: float = Field(ge=0, le=1)
    unresolved_correction_count: int = Field(ge=0)
    autopilot_consent: bool
    source_refs: list[Any]
    version: int = Field(ge=1)
    created_at: str
    updated_at: str
    autopilot_eligible: bool


class ContentGenome(StrictModel):
    project_id: str
    query: dict[str, Any]
    fingerprint: str = Field(min_length=64, max_length=64)
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    decision_context: list[dict[str, Any]]
    evidence_context: list[dict[str, Any]]
    viewpoint_context: list[dict[str, Any]]
    series_context: list[dict[str, Any]]
    insight_context: list[dict[str, Any]]
    summary: dict[str, int]


class Evidence(StrictModel):
    id: str
    owner_user_id: str
    project_id: str
    source_type: EvidenceSourceType
    statement: str
    source_ref: str
    content_ref: str | None = None
    privacy_level: EvidencePrivacyLevel
    confirmation_status: EvidenceConfirmationStatus
    reusable: bool
    version: int = Field(ge=1)
    idempotency_key: str
    request_hash: str
    decision_idempotency_key: str | None = None
    decision_request_hash: str | None = None
    revoked_at: str | None = None
    created_at: str
    updated_at: str


class HumanGate(StrictModel):
    id: str
    owner_user_id: str
    project_id: str | None = None
    action_id: str | None = None
    gate_type: HumanGateType
    prompt: str
    payload: dict[str, Any]
    status: Literal["pending", "confirmed", "rejected"]
    decision_payload: dict[str, Any] | None = None
    version: int = Field(ge=1)
    idempotency_key: str
    request_hash: str
    decision_idempotency_key: str | None = None
    decision_request_hash: str | None = None
    decided_at: str | None = None
    created_at: str
    updated_at: str


class ActionEvent(StrictModel):
    id: str
    owner_user_id: str
    action_id: str
    project_id: str | None = None
    event_type: ActionEventType
    from_status: str | None = None
    to_status: str
    payload: dict[str, Any]
    action_version: int = Field(ge=1)
    idempotency_key: str
    request_hash: str
    created_at: str
    experiment_id: ExperimentId | None = None
    cohort: Cohort | None = None
    ai_trace_id: str | None = None
    latency_ms: int | None = Field(default=None, ge=0)
    success: bool
    error_code: str | None = None
    model_version: str | None = None
    prompt_version: str | None = None


class NextBestAction(StrictModel):
    id: str
    owner_user_id: str
    project_id: str | None = None
    action_type: ActionType
    content_intent: ContentIntent | None = None
    title: str
    reason: str
    evidence_refs: list[str]
    unknown_refs: list[str]
    expected_state_change: dict[str, Any]
    estimated_effort_minutes: int = Field(ge=0)
    automation_level: AutomationLevel
    human_gate_type: HumanGateType | None = None
    fallback_action: dict[str, Any]
    status: ActionStatus
    ai_trace_id: str | None = None
    expires_at: str | None = None
    version: int = Field(ge=1)
    idempotency_key: str
    request_hash: str
    created_at: str
    updated_at: str
    experiment_id: ExperimentId | None = None
    cohort: Cohort | None = None
    human_gate: HumanGate | None = None
    last_event: dict[str, Any] | None = None


class AITraceCreate(StrictModel):
    id: str
    task_type: str
    input_refs: list[str]
    evidence_refs: list[str] = Field(default_factory=list)
    policy_version: str
    model_identifier: str | None = None
    capability: str
    visibility_boundary: dict[str, Any]
    source_snapshot_ids: list[str] = Field(default_factory=list)
    contamination_check: dict[str, Any]
    calibration_state: Literal["valid", "insufficient", "calibration_invalid"]
    limitations: list[str] = Field(default_factory=list)
    output_ref: str
    generated_at: str


class AITrace(AITraceCreate):
    owner_user_id: str


class Experiment(StrictModel):
    id: ExperimentId
    name: str
    hypothesis: str
    metric_definitions: dict[str, list[str]]
    default_window_days: int = Field(ge=1, le=365)
    status: Literal["planned", "running", "completed", "stopped"]
    created_at: str
    updated_at: str
