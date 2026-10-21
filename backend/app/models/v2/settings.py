"""Owner settings and safe AI capability status contracts."""

from typing import Any

from pydantic import Field

from app.models.v2.intent_actions import StrictModel


class AgentIdentityPrefs(StrictModel):
    """全局 / 项目助手外观与指令（UI 契约）。"""

    global_name: str | None = Field(default=None, max_length=32)
    global_avatar: str | None = Field(default=None, max_length=200_000)
    project_name: str | None = Field(default=None, max_length=32)
    project_avatar: str | None = Field(default=None, max_length=200_000)
    global_agent_md: str | None = Field(default=None, max_length=8000)
    project_agent_md: str | None = Field(default=None, max_length=8000)


class ProductPrefs(StrictModel):
    """产品创作偏好。"""

    default_content_kind: str | None = Field(default=None, pattern="^(graphic_note|vlog_plan)$")
    retro_reminder_days: int | None = Field(default=None, ge=0, le=30)
    memory_write_mode: str | None = Field(default=None, pattern="^(propose|auto|manual)$")
    default_material_privacy: str | None = Field(default=None, pattern="^(private|public)$")
    publish_check_level: str | None = Field(default=None, pattern="^(standard|strict|soft)$")
    # 人话化（去 AI 味）默认开；显式 False 才关（P2-F3）
    humanize_enabled: bool | None = None
    # 全局 AI 唤起方式：Alt+Space 或只用悬浮球
    inspiration_shortcut: str | None = Field(default=None, pattern="^(alt|ball)$")
    # 项目助手起草语气（只影响项目内成稿，不影响全局 AI）
    draft_tone: str | None = Field(default=None, pattern="^(same|short|long)$")


class UserSettingsUpdate(StrictModel):
    weekly_publish_goal: int | None = Field(default=None, ge=1, le=7)
    content_strategy: str | None = Field(default=None, min_length=1, max_length=2000)
    xiaohongshu_account_reference: str | None = Field(default=None, max_length=200)
    consent: dict[str, Any] | None = None
    # 夜间自动消化（默认关）：用户主动开启后每晚整理可发布素材。
    auto_digest_enabled: bool | None = None
    agent_identity: AgentIdentityPrefs | None = None
    product_prefs: ProductPrefs | None = None
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
    auto_digest_enabled: bool
    version: int = Field(ge=1)
    ai: AICapabilityStatus
    agent_identity: AgentIdentityPrefs
    product_prefs: ProductPrefs
