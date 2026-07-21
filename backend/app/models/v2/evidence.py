"""Contracts for source-aware evidence used by intent orchestration."""

from enum import StrEnum
from typing import Literal

from pydantic import Field

from app.models.v2.intent_actions import StrictModel


class EvidenceSourceType(StrEnum):
    USER_FACT = "user_fact"
    EXTERNAL_FACT = "external_fact"
    AI_INFERENCE = "ai_inference"
    VALIDATED_INSIGHT = "validated_insight"


class EvidenceConfirmationStatus(StrEnum):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    REVOKED = "revoked"


class EvidencePrivacyLevel(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"
    SENSITIVE = "sensitive"


class EvidenceCreate(StrictModel):
    project_id: str = Field(min_length=1, max_length=100)
    statement: str = Field(min_length=1, max_length=10000)
    source_type: EvidenceSourceType = EvidenceSourceType.USER_FACT
    source_ref: str = Field(min_length=1, max_length=500)
    content_ref: str | None = Field(default=None, max_length=500)
    privacy_level: EvidencePrivacyLevel = EvidencePrivacyLevel.PRIVATE
    reusable: bool = False
    idempotency_key: str = Field(min_length=1, max_length=200)


class EvidenceDecision(StrictModel):
    decision: Literal["confirm", "reject"]
    expected_evidence_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class EvidenceRevocation(StrictModel):
    expected_evidence_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)
