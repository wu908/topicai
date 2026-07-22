"""Contracts for the bounded starter assessment and three-project experiment."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.v2.intent_actions import ContentIntent


class StarterReadiness(StrEnum):
    NOT_READY = "not_ready"
    READY = "ready"
    PAUSED = "paused"


class StarterAssessmentCreate(BaseModel):
    motivation: Literal["curious", "career", "expression", "other"]
    available_hours_per_week: float = Field(ge=0, le=40)
    publish_commitment: bool
    accept_experiment: bool
    experience_assets: list[str] = Field(default_factory=list, max_length=10)
    interest_assets: list[str] = Field(default_factory=list, max_length=10)
    skill_assets: list[str] = Field(default_factory=list, max_length=10)
    privacy_limits: list[str] = Field(default_factory=list, max_length=10)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @field_validator(
        "experience_assets", "interest_assets", "skill_assets", "privacy_limits"
    )
    @classmethod
    def clean_items(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            item = value.strip()
            if item and item not in cleaned:
                cleaned.append(item[:200])
        return cleaned


class DirectionGenerate(BaseModel):
    expected_assessment_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class DirectionSelect(BaseModel):
    expected_direction_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class StarterSprintReview(BaseModel):
    observed_summary: str = Field(min_length=1, max_length=1000)
    blocker_reasons: list[str] = Field(default_factory=list, max_length=3)
    next_topics: list[str] = Field(default_factory=list, max_length=3)
    expected_sprint_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @field_validator("blocker_reasons", "next_topics")
    @classmethod
    def clean_review_items(cls, values: list[str]) -> list[str]:
        return [item.strip()[:200] for item in values if item.strip()]


class StarterTopic(BaseModel):
    title: str
    content_intent: ContentIntent
    audience_change: str
    evidence_refs: list[str]
