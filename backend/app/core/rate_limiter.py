"""In-memory rate limiter for AI call throttling.

Free users get 20 AI calls per day, resetting at UTC 00:00.
Thread-safe implementation using a simple dict with lock.
No Redis dependency — pure Python for MVP simplicity.
"""

import threading
from datetime import UTC, datetime, timedelta

from config.settings import get_settings


class RateLimiter:
    """Thread-safe in-memory rate limiter for AI calls.

    Tracks per-user daily AI call counts. Resets at UTC 00:00 each day.
    """

    def __init__(self, max_calls: int | None = None):
        """Initialize the rate limiter.

        Args:
            max_calls: Maximum AI calls per day. Defaults to settings value.
        """
        settings = get_settings()
        self.max_calls = max_calls or settings.ai_calls_per_day
        self._lock = threading.Lock()
        self._counts: dict[str, dict] = {}  # user_id -> {count, reset_at}

    def check_and_increment(self, user_id: str) -> dict:
        """Check rate limit and increment the counter.

        Args:
            user_id: The user's unique ID.

        Returns:
            Dict with remaining, limit, used, reset_at fields.

        Raises:
            RateLimitError: If the user has exceeded their daily limit.
        """
        from app.core.exceptions import RateLimitException

        with self._lock:
            now = datetime.now(UTC)
            today_reset = now.replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            # Initialize or check reset
            if user_id not in self._counts:
                reset_at = today_reset + timedelta(days=1)
                self._counts[user_id] = {
                    "count": 0,
                    "reset_at": reset_at.isoformat().replace("+00:00", "Z"),
                }
            else:
                user_data = self._counts[user_id]
                reset_at = datetime.fromisoformat(
                    user_data["reset_at"].replace("Z", "+00:00")
                )
                if now >= reset_at:
                    # Reset for new day
                    next_reset = today_reset + timedelta(days=1)
                    self._counts[user_id] = {
                        "count": 0,
                        "reset_at": next_reset.isoformat().replace(
                            "+00:00", "Z"
                        ),
                    }

            user_data = self._counts[user_id]

            # Check limit
            if user_data["count"] >= self.max_calls:
                reset_iso = user_data["reset_at"]
                raise RateLimitException(
                    message=f"今日AI调用次数已用完（{self.max_calls}次/天），请明天再试",
                    reset_at=reset_iso,
                )

            # Increment
            user_data["count"] += 1

            return {
                "remaining": self.max_calls - user_data["count"],
                "limit": self.max_calls,
                "used": user_data["count"],
                "reset_at": user_data["reset_at"],
            }

    def get_remaining(self, user_id: str) -> dict:
        """Get remaining quota without incrementing.

        Args:
            user_id: The user's unique ID.

        Returns:
            Dict with remaining, limit, used, reset_at fields.
        """
        with self._lock:
            if user_id not in self._counts:
                return {
                    "remaining": self.max_calls,
                    "limit": self.max_calls,
                    "used": 0,
                    "reset_at": _next_reset_iso(),
                }
            user_data = self._counts[user_id]
            return {
                "remaining": max(
                    0, self.max_calls - user_data["count"]
                ),
                "limit": self.max_calls,
                "used": user_data["count"],
                "reset_at": user_data["reset_at"],
            }

    def reset_user(self, user_id: str) -> None:
        """Manually reset a user's rate limit counter.

        Args:
            user_id: The user's unique ID.
        """
        with self._lock:
            if user_id in self._counts:
                self._counts[user_id] = {
                    "count": 0,
                    "reset_at": _next_reset_iso(),
                }


def _next_reset_iso() -> str:
    """Get the next UTC midnight as ISO 8601 string."""
    now = datetime.now(UTC)
    today_reset = now.replace(hour=0, minute=0, second=0, microsecond=0)
    next_reset = today_reset + timedelta(days=1)
    return next_reset.isoformat().replace("+00:00", "Z")
