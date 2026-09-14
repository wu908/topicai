"""Contracts for Growth onboarding and historical-note evidence."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class HistoryNoteInput(BaseModel):
    external_key: str | None = Field(default=None, max_length=200)
    title: str = Field(max_length=200)
    body_excerpt: str = Field(default="", max_length=5000)
    published_at: str | None = None
    note_url: str | None = Field(default=None, max_length=2000)
    metrics: dict[str, Any] = Field(default_factory=dict)
    audience_questions: list[str] = Field(default_factory=list, max_length=20)
    tags: list[str] = Field(default_factory=list, max_length=20)


class HistoryImportCreate(BaseModel):
    method: Literal["manual", "csv", "json"]
    # Items are validated independently by HistoryImportService so one malformed
    # record does not reject the rest of the batch at the HTTP boundary.
    items: list[object] = Field(min_length=1, max_length=200)
    idempotency_key: str = Field(min_length=1, max_length=200)


class ReferenceNoteInput(HistoryNoteInput):
    """一条**别人**的内容——用户想做成的那种样子。

    与 HistoryNoteInput 的唯一区别是必须说明来源：用户说不出自己是谁，
    但能指出"我想做成这样"，而"这样"是谁的必须记下来，否则这条证据无从追溯，
    也无从让用户判断系统有没有看错人。

    metrics 不参与任何推断：别人笔记的点赞数不是你的基线，也不构成选题依据
    （见 reference_anchor 的 visibility_boundary）。
    """

    source_handle: str = Field(min_length=1, max_length=200)


class ProductModeUpdate(BaseModel):
    mode: Literal["starter", "growth"]
    expected_version: int = Field(ge=1)


class ProfileAttributeRejection(BaseModel):
    field: Literal["niche", "target_audience", "growth_goal", "content_pillar", "voice_trait"]
    value: str = Field(min_length=1, max_length=200)


class CreatorProfileUpdate(BaseModel):
    niche: str = Field(min_length=1, max_length=200)
    target_audience: str = Field(min_length=1, max_length=500)
    growth_goal: Literal["stable_publish", "follower_growth", "both"]
    content_pillars: list[str] = Field(min_length=1, max_length=5)
    voice_traits: list[str] = Field(default_factory=list, max_length=5)
    avoid_traits: list[str] = Field(default_factory=list, max_length=10)
    rejected: list[ProfileAttributeRejection] = Field(default_factory=list, max_length=20)
    confirm: bool = False
    expected_version: int = Field(ge=1)

    @field_validator("niche", "target_audience")
    @classmethod
    def clean_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value cannot be blank")
        return cleaned

    @field_validator("content_pillars")
    @classmethod
    def clean_required_values(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            item = value.strip()
            if item and item not in cleaned:
                cleaned.append(item[:200])
        if not cleaned:
            raise ValueError("at least one non-blank value is required")
        return cleaned

    @field_validator("voice_traits", "avoid_traits")
    @classmethod
    def clean_optional_values(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            item = value.strip()
            if item and item not in cleaned:
                cleaned.append(item[:200])
        return cleaned


class OnboardingContext(BaseModel):
    mode: Literal["starter", "growth"]
    state: Literal["not_started", "in_progress", "completed"]
    version: int = Field(ge=1)


class HistoryImportItemResult(BaseModel):
    index: int = Field(ge=0)
    status: Literal["imported", "duplicate", "failed"]
    note_id: str | None = None
    error: str | None = None


class HistoryImportResult(BaseModel):
    id: str
    method: Literal["manual", "csv", "json"]
    status: Literal["completed", "partial", "failed"]
    input_count: int = Field(ge=1, le=200)
    success_count: int = Field(ge=0)
    failure_count: int = Field(ge=0)
    item_results: list[HistoryImportItemResult]
    started_at: str
    completed_at: str


class ProfileAttribute(BaseModel):
    value: str
    status: Literal["provisional", "confirmed", "rejected"]
    origin: Literal["inferred", "user"]
    evidence_refs: list[str]
    confidence: Literal["low", "medium", "high"]
    limitations: list[str]


class ProfileAttributes(BaseModel):
    niche: ProfileAttribute
    target_audience: ProfileAttribute
    growth_goal: ProfileAttribute
    content_pillars: list[ProfileAttribute]
    voice_traits: list[ProfileAttribute]
    avoid_traits: list[ProfileAttribute]


class RejectedProfileAttribute(ProfileAttribute):
    field: str


class CreatorProfileResult(BaseModel):
    id: str
    confirmation_state: Literal["provisional", "confirmed", "needs_review"]
    version: int = Field(ge=1)
    attributes: ProfileAttributes
    rejected_attributes: list[RejectedProfileAttribute]
