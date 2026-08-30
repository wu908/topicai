"""Typed contracts for the async creation loop (Spec-013 Phase 1)."""

from typing import Any, Literal

from pydantic import Field

from app.models.v2.intent_actions import StrictModel

InboxKind = Literal["text", "image", "voice", "link", "idea"]
InboxConsent = Literal["publishable", "private"]


class InboxItemCreate(StrictModel):
    kind: InboxKind
    title: str = Field(default="", max_length=120)
    content: str = Field(min_length=1, max_length=4000)
    consent: InboxConsent = "publishable"
    idempotency_key: str = Field(min_length=1, max_length=200)


class InboxItemView(StrictModel):
    id: str
    kind: InboxKind
    title: str
    content: str
    consent: InboxConsent
    status: Literal["intake", "digested", "failed"]
    version: int
    created_at: str
    updated_at: str


class DeliverableView(StrictModel):
    id: str
    thread_id: str
    title: str
    body_text: str
    outline: list[Any]
    facts: list[Any]
    judgment: dict[str, Any]
    content_intent: Literal["solve", "share", "record"] | None
    proposed_publish_at: str | None
    is_exploration: bool
    status: Literal[
        "queued", "producing", "ready", "failed", "expired", "picked", "discarded"
    ]
    attribution: str | None
    expire_at: str | None
    precheck: dict[str, Any] = Field(default_factory=dict)
    version: int
    created_at: str
    updated_at: str


class PickupRequest(StrictModel):
    content_intent: Literal["solve", "share", "record"]
    audience_change: str = Field(min_length=1, max_length=1000)
    primary_response: Literal["save", "comment", "profile_visit", "follow"] = "save"
    window_days: int = Field(default=7, ge=1, le=365)
    schedule_at: str | None = Field(default=None, max_length=40)
    idempotency_key: str = Field(min_length=1, max_length=200)


class DiscardRequest(StrictModel):
    reason: str = Field(min_length=1, max_length=60)
    idempotency_key: str = Field(min_length=1, max_length=200)


class MetricsRecord(StrictModel):
    metric: Literal[
        "pickup_seconds", "weekly_minutes", "published_count", "discard_attribution"
    ]
    value: float
    meta: dict[str, Any] = Field(default_factory=dict)
