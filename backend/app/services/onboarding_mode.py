"""Owner-scoped product-mode selection for onboarding."""

from typing import Any

from app.core.exceptions import VersionConflictException
from app.models.v2.onboarding import OnboardingContext, ProductModeUpdate


class OnboardingModeService:
    def __init__(self, db: Any):
        self.db = db

    async def get(self, owner_user_id: str) -> OnboardingContext:
        current = await self.db.fetch_one(
            "SELECT product_mode,onboarding_state,onboarding_version " "FROM users WHERE id=:owner",
            {"owner": owner_user_id},
        )
        if current is None:
            raise ValueError("user not found")
        return OnboardingContext(
            mode=current["product_mode"],
            state=current["onboarding_state"],
            version=current["onboarding_version"],
        )

    async def select(self, owner_user_id: str, body: ProductModeUpdate) -> OnboardingContext:
        current = await self.get(owner_user_id)
        if current.version != body.expected_version:
            raise VersionConflictException(current.version, body.expected_version)
        result = await self.db.execute(
            "UPDATE users SET product_mode=:mode,onboarding_state='in_progress',"
            "onboarding_version=onboarding_version+1 WHERE id=:owner "
            "AND onboarding_version=:expected",
            {
                "mode": body.mode,
                "owner": owner_user_id,
                "expected": body.expected_version,
            },
        )
        if getattr(result, "rowcount", 1) == 0:
            latest = await self.get(owner_user_id)
            raise VersionConflictException(latest.version, body.expected_version)
        return await self.get(owner_user_id)
