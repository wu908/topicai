"""Small in-process fixed-window limiter for authentication endpoints."""

import threading
import time

from config.settings import get_settings


class MinuteRateLimiter:
    def __init__(self, max_calls: int | None = None):
        self.max_calls = max_calls or get_settings().auth_rate_limit_per_minute
        self._lock = threading.Lock()
        self._counts: dict[str, tuple[int, float]] = {}

    def check_and_increment(self, key: str) -> None:
        from app.core.exceptions import RateLimitException

        with self._lock:
            count, started = self._counts.get(key, (0, time.monotonic()))
            if time.monotonic() - started >= 60:
                count, started = 0, time.monotonic()
            if count >= self.max_calls:
                raise RateLimitException(
                    message="请求过于频繁，请稍后再试",
                    error_code="AUTH_RATE_LIMIT_EXCEEDED",
                )
            self._counts[key] = (count + 1, started)
