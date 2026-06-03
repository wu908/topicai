"""Creator Profile service for TopicAI v4.0.

CRUD operations and dynamic profile evolution based on feedback.
Implements the cheat-on-content dynamic evolution mechanism.
"""

import json
import logging
from typing import Any

from app.core.database import Database
from app.core.utils import utc_now

logger = logging.getLogger(__name__)

class CreatorProfileService:
    """Manages creator profile CRUD and dynamic evolution.

    The profile evolves over time as users provide feedback (👍👎),
    updating rubric_weights to better match their content style.
    """

    def __init__(self, db: Database):
        """Initialize with a database connection.

        Args:
            db: Database instance (must be initialized).
        """
        self.db = db

    async def create(self, profile_data: dict[str, Any]) -> None:
        """Create a new creator profile.

        Args:
            profile_data: Dict with all profile fields.
        """
        # Serialize JSON fields
        data = dict(profile_data)
        if isinstance(data.get("content_formats"), list):
            data["content_formats"] = json.dumps(data["content_formats"])
        if isinstance(data.get("rubric_weights"), dict):
            data["rubric_weights"] = json.dumps(data["rubric_weights"])

        await self.db.insert("creator_profiles", data)

    async def get(self, user_id: str) -> dict[str, Any] | None:
        """Get a creator profile by user_id.

        Args:
            user_id: The user's unique ID.

        Returns:
            Profile dict with deserialized JSON fields, or None.
        """
        row = await self.db.fetch_one(
            "SELECT * FROM creator_profiles WHERE user_id = :user_id",
            {"user_id": user_id},
        )
        if not row:
            return None

        return self._deserialize(row)

    async def update(
        self, user_id: str, updates: dict[str, Any]
    ) -> None:
        """Update a creator profile.

        Args:
            user_id: The user's unique ID.
            updates: Fields to update.
        """
        data = dict(updates)
        if "content_formats" in data and isinstance(data["content_formats"], list):
            data["content_formats"] = json.dumps(data["content_formats"])
        if "rubric_weights" in data and isinstance(data["rubric_weights"], dict):
            data["rubric_weights"] = json.dumps(data["rubric_weights"])

        data["updated_at"] = utc_now()

        await self.db.update(
            "creator_profiles",
            data,
            {"user_id": user_id},
        )

    async def update_rubric_weights(
        self, user_id: str, weights: dict[str, float]
    ) -> None:
        """Update only the rubric_weights field.

        Used by the feedback loop to evolve profile weights.

        Args:
            user_id: The user's unique ID.
            weights: New rubric weight mapping.
        """
        await self.db.update(
            "creator_profiles",
            {
                "rubric_weights": json.dumps(weights),
                "updated_at": utc_now(),
            },
            {"user_id": user_id},
        )

    async def delete(self, user_id: str) -> None:
        """Delete a creator profile.

        Args:
            user_id: The user's unique ID.
        """
        await self.db.delete("creator_profiles", {"user_id": user_id})

    async def exists(self, user_id: str) -> bool:
        """Check if a profile exists for the user.

        Args:
            user_id: The user's unique ID.

        Returns:
            True if profile exists.
        """
        row = await self.db.fetch_one(
            "SELECT id FROM creator_profiles WHERE user_id = :user_id",
            {"user_id": user_id},
        )
        return row is not None

    def _deserialize(self, row: dict[str, Any]) -> dict[str, Any]:
        """Deserialize JSON fields from a database row.

        Args:
            row: Raw database row.

        Returns:
            Row with deserialized JSON fields.
        """
        result = dict(row)
        for field in ("content_formats", "rubric_weights"):
            if field in result and isinstance(result[field], str):
                try:
                    result[field] = json.loads(result[field])
                except json.JSONDecodeError:
                    pass
        return result

