"""Owner settings and safe AI capability status contracts."""

from typing import Any

from pydantic import Field

from app.models.v2.intent_actions import StrictModel


class UserSettingsUpdate(StrictModel):
    weekly_publish_goal: int | None = Field(default=None, ge=1, le=7)
    content_strategy: str | None = Field(default=None, min_length=1, max_length=2000)
    xiaohongshu_account_reference: str | None = Field(default=None, max_length=200)
    consent: dict[str, Any] | None = None
    expected_version: int = Field(ge=1)


class AICapabilityStatus(StrictModel):
    enabled: bool
    configured: bool
    model_identifier: str | None
    capabilities: list[str]
    vision_enabled: bool


class UserSettingsView(StrictModel):
    weekly_publish_goal: int = Field(ge=1, le=7)
    timezone: str
    content_strategy: str
    xiaohongshu_account_reference: str | None
    consent: dict[str, Any]
    version: int = Field(ge=1)
    ai: AICapabilityStatus
