"""Account + Team Pydantic models - Phase 6/7 backend contract.

Field names and types MUST match
frontend/src/types/contracts/accounts.ts exactly.
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


Platform = Literal[
    "wechat_mp",
    "wechat_video",
    "xhs",
    "bilibili",
    "douyin",
    "zhihu",
]

TeamRole = Literal["admin", "editor", "viewer"]
AccountStatus = Literal["connected", "expired", "disconnected"]


class AccountStats(BaseModel):
    followers: int
    articles: int
    avg_read_count: int


class PlatformAccount(BaseModel):
    id: str
    owner_id: str
    platform: Platform
    display_name: str
    is_primary: bool = False
    status: AccountStatus = "disconnected"
    token_expires_at: Optional[str] = None
    last_sync_at: Optional[str] = None
    stats: Optional[AccountStats] = None
    created_at: str
    updated_at: str


class TeamMember(BaseModel):
    id: str
    email: str
    username: str
    initial: str
    role: TeamRole
    joined_at: str
    last_active_at: Optional[str] = None


class TeamInviteRequest(BaseModel):
    email: str
    role: TeamRole


class RoleChangeRequest(BaseModel):
    role: TeamRole
