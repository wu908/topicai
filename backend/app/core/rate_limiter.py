"""In-memory rate limiters.

Two distinct limiters coexist:

* ``RateLimiter`` — daily AI call quota per user (UTC midnight reset).
* ``MinuteRateLimiter`` — per-IP minute fixed-window limiter used by the
  auth endpoints (login / register / refresh) to mitigate credential
  stuffing and registration flooding.

Both are thread-safe and keep state in-process (no Redis). ``MinuteRateLimiter``
is deliberately separate from ``RateLimiter`` to avoid coupling the AI daily
quota with the auth per-minute budget — they have different windows, different
keys (user_id vs IP) and different error semantics.
"""

import threading
import time
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


class MinuteRateLimiter:
    """Thread-safe per-IP fixed-window rate limiter.

    Designed for auth endpoints (login/register/refresh) where the budget is
    small (default 5/min/IP) and the key is the client IP rather than a
    user_id (because the user is not yet authenticated). Also reused — with a
    3600s window — as the anonymous AI-call limiter (D4): anonymous callers
    share a strict per-IP hourly budget so an unauthenticated client cannot
    brute-force the LLM.

    A fixed window is sufficient for MVP: a window_start timestamp is kept
    per IP, and once ``window_seconds`` elapse the counter resets. Edge
    bursts at window boundaries are an accepted trade-off for simplicity.

    The constructor parameter ``max_calls_per_minute`` is retained for
    backward compatibility with D3 even though the window is now
    configurable; conceptually it is "max calls per window".
    """

    WINDOW_SECONDS: float = 60.0

    def __init__(
        self,
        max_calls_per_minute: int | None = None,
        window_seconds: float | None = None,
    ):
        """Initialize the minute rate limiter.

        Args:
            max_calls_per_minute: Maximum calls per IP within one window.
                Defaults to ``settings.auth_rate_limit_per_minute``. Despite
                the historical name this is "max calls per window" — the
                window length is controlled by ``window_seconds``.
            window_seconds: Window length in seconds. Defaults to
                ``60.0`` (one minute) for auth-endpoint use. Pass
                ``3600.0`` to use the limiter as an hourly anonymous AI
                limiter (D4).
        """
        settings = get_settings()
        self.max_calls_per_minute = (
            max_calls_per_minute
            if max_calls_per_minute is not None
            else settings.auth_rate_limit_per_minute
        )
        self.window_seconds = (
            window_seconds if window_seconds is not None else self.WINDOW_SECONDS
        )
        self._lock = threading.Lock()
        # ip -> {count, window_start}
        self._counts: dict[str, dict[str, float | int]] = {}

    def check_and_increment(self, ip: str) -> dict:
        """Check rate limit and increment the counter for the given IP.

        Args:
            ip: The client IP (use ``"unknown"`` when IP is unavailable).

        Returns:
            Dict with remaining, limit, used, reset_at (ISO 8601) fields.

        Raises:
            RateLimitException: If the per-minute budget for the IP is used up.
        """
        from app.core.exceptions import RateLimitException

        with self._lock:
            now = time.monotonic()
            entry = self._counts.get(ip)
            if entry is None or (now - float(entry["window_start"])) >= self.window_seconds:
                # Start a new window.
                entry = {"count": 0, "window_start": now}
                self._counts[ip] = entry

            if entry["count"] >= int(self.max_calls_per_minute):
                reset_at_iso = self._reset_at_iso(entry)
                raise RateLimitException(
                    message="请求过于频繁，请稍后再试",
                    error_code="AUTH_RATE_LIMIT_EXCEEDED",
                    reset_at=reset_at_iso,
                )

            entry["count"] = int(entry["count"]) + 1
            return {
                "remaining": int(self.max_calls_per_minute) - int(entry["count"]),
                "limit": int(self.max_calls_per_minute),
                "used": int(entry["count"]),
                "reset_at": self._reset_at_iso(entry),
            }

    def get_remaining(self, ip: str) -> dict:
        """Get remaining quota for an IP without incrementing."""
        with self._lock:
            entry = self._counts.get(ip)
            now = time.monotonic()
            if entry is None or (now - float(entry["window_start"])) >= self.window_seconds:
                return {
                    "remaining": int(self.max_calls_per_minute),
                    "limit": int(self.max_calls_per_minute),
                    "used": 0,
                    "reset_at": self._iso_now_plus(self.window_seconds),
                }
            return {
                "remaining": max(
                    0, int(self.max_calls_per_minute) - int(entry["count"])
                ),
                "limit": int(self.max_calls_per_minute),
                "used": int(entry["count"]),
                "reset_at": self._reset_at_iso(entry),
            }

    def reset_ip(self, ip: str) -> None:
        """Manually reset the counter for an IP."""
        with self._lock:
            if ip in self._counts:
                self._counts[ip] = {
                    "count": 0,
                    "window_start": time.monotonic(),
                }

    def _reset_at_iso(self, entry: dict[str, float | int]) -> str:
        """Return ISO 8601 wall-clock time at which the current window resets."""
        remaining = self.window_seconds - (time.monotonic() - float(entry["window_start"]))
        if remaining < 0:
            remaining = 0.0
        reset_dt = datetime.now(UTC) + timedelta(seconds=remaining)
        return reset_dt.isoformat().replace("+00:00", "Z")

    @staticmethod
    def _iso_now_plus(seconds: float) -> str:
        reset_dt = datetime.now(UTC) + timedelta(seconds=seconds)
        return reset_dt.isoformat().replace("+00:00", "Z")
