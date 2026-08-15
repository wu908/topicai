"""Small in-process fixed-window limiter for authentication endpoints."""

import threading
import time

from config.settings import get_settings


class MinuteRateLimiter:
    # Once the table reaches this many live windows, sweep expired entries
    # before inserting more. Keeps the common path allocation-free.
    _prune_threshold = 1024

    def __init__(self, max_calls: int | None = None):
        self.max_calls = max_calls or get_settings().auth_rate_limit_per_minute
        self._lock = threading.Lock()
        self._counts: dict[str, tuple[int, float]] = {}

    def _prune_expired(self, now: float) -> None:
        """Drop windows that have already rolled over.

        Keys are derived from the client IP, which is attacker-influenced, so
        without eviction a flood of distinct source addresses would grow
        ``_counts`` without bound for the lifetime of the process.
        """
        expired = [key for key, (_, started) in self._counts.items() if now - started >= 60]
        for key in expired:
            del self._counts[key]

    def check_and_increment(self, key: str) -> None:
        from app.core.exceptions import RateLimitException

        with self._lock:
            now = time.monotonic()
            if len(self._counts) >= self._prune_threshold:
                self._prune_expired(now)

            count, started = self._counts.get(key, (0, now))
            if now - started >= 60:
                count, started = 0, now
            if count >= self.max_calls:
                raise RateLimitException(
                    message="请求过于频繁，请稍后再试",
                    error_code="AUTH_RATE_LIMIT_EXCEEDED",
                )
            self._counts[key] = (count + 1, started)
