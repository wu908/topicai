"""Versioned owner settings with credential-free AI status."""

import json
from typing import Any

from sqlalchemy import text

from app.core.exceptions import VersionConflictException
from app.models.v2.settings import UserSettingsUpdate, UserSettingsView
from app.services.creator_state import CreatorStateService
from app.services.v2_utils import now
from config.settings import get_settings


_AGENT_KEY = "agent_identity"
_PRODUCT_KEY = "product_prefs"


def _prefs_from_consent(consent: dict) -> tuple[dict, dict]:
    agent = consent.get(_AGENT_KEY) or {}
    product = consent.get(_PRODUCT_KEY) or {}
    return agent, product


def _merge_prefs(consent: dict, agent: dict | None, product: dict | None) -> dict:
    next_consent = dict(consent or {})
    if agent is not None:
        merged = dict(next_consent.get(_AGENT_KEY) or {})
        merged.update({k: v for k, v in agent.items() if v is not None})
        next_consent[_AGENT_KEY] = merged
    if product is not None:
        merged = dict(next_consent.get(_PRODUCT_KEY) or {})
        merged.update({k: v for k, v in product.items() if v is not None})
        next_consent[_PRODUCT_KEY] = merged
    return next_consent


class UserSettingsService:
    def __init__(self, db: Any):
        self.db = db

    async def get(self, owner: str) -> dict[str, Any]:
        user = await self.db.fetch_one(
            "SELECT weekly_publish_goal,timezone,consent_json,"
            "xiaohongshu_account_reference,settings_version,auto_digest_enabled "
            "FROM users WHERE id=:owner",
            {"owner": owner},
        )
        if user is None:
            raise ValueError("owner not found")
        state = await CreatorStateService(self.db).get(owner)
        config = get_settings()
        capabilities = {
            value.strip()
            for value in config.llm_capabilities.split(",")
            if value.strip()
        }
        consent = json.loads(user["consent_json"] or "{}")
        agent_prefs, product_prefs = _prefs_from_consent(consent)
        return UserSettingsView.model_validate({
            "weekly_publish_goal": user["weekly_publish_goal"],
            "timezone": user["timezone"],
            "content_strategy": state["current_goal"],
            "xiaohongshu_account_reference": user[
                "xiaohongshu_account_reference"
            ],
            "consent": consent,
            "agent_identity": agent_prefs,
            "product_prefs": product_prefs,
            "auto_digest_enabled": bool(user["auto_digest_enabled"]),
            "version": user["settings_version"],
            "ai": {
                "enabled": config.ai_enabled,
                "configured": bool(
                    config.ai_enabled
                    and config.llm_base_url
                    and config.llm_api_key
                    and config.llm_model
                ),
                "model_identifier": config.llm_model or None,
                "capabilities": sorted(capabilities),
                "vision_enabled": bool(
                    config.vision_enabled and "vision" in capabilities
                ),
            },
        }).model_dump(mode="json")

    async def update(self, owner: str, body: UserSettingsUpdate) -> dict[str, Any]:
        current = await self.get(owner)
        if current["version"] != body.expected_version:
            raise VersionConflictException(current["version"], body.expected_version)
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                updated = await session.execute(
                    text(
                        "UPDATE users SET weekly_publish_goal=:goal,consent_json=:consent,"
                        "xiaohongshu_account_reference=:account,"
                        "auto_digest_enabled=:auto_digest,"
                        "settings_version=settings_version+1 "
                        "WHERE id=:owner AND settings_version=:expected"
                    ),
                    {
                        "goal": body.weekly_publish_goal
                        if body.weekly_publish_goal is not None
                        else current["weekly_publish_goal"],
                        "consent": json.dumps(
                            _merge_prefs(
                                body.consent
                                if body.consent is not None
                                else current["consent"],
                                body.agent_identity.model_dump(exclude_none=True)
                                if body.agent_identity is not None
                                else None,
                                body.product_prefs.model_dump(exclude_none=True)
                                if body.product_prefs is not None
                                else None,
                            ),
                            ensure_ascii=False,
                        ),
                        "account": body.xiaohongshu_account_reference
                        if body.xiaohongshu_account_reference is not None
                        else current["xiaohongshu_account_reference"],
                        "auto_digest": int(
                            body.auto_digest_enabled
                            if body.auto_digest_enabled is not None
                            else current["auto_digest_enabled"]
                        ),
                        "owner": owner,
                        "expected": body.expected_version,
                    },
                )
                if updated.rowcount != 1:
                    fresh = await self.db.fetch_one(
                        "SELECT settings_version FROM users WHERE id=:owner",
                        {"owner": owner},
                    )
                    raise VersionConflictException(
                        fresh["settings_version"], body.expected_version
                    )
                if body.content_strategy is not None:
                    await session.execute(
                        text(
                            "UPDATE creator_states SET current_goal=:goal,updated_at=:now,"
                            "version=version+1 WHERE owner_user_id=:owner"
                        ),
                        {
                            "goal": body.content_strategy.strip(),
                            "now": now(),
                            "owner": owner,
                        },
                    )
        return await self.get(owner)
