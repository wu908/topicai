"""Unit tests for the in-process fixed-window auth rate limiter.

Covers the reject branch, window rollover, per-key isolation, and the
bounded-memory prune path — the limiter body had no direct tests before
(middleware tests mock it entirely).
"""

import pytest

from app.core.exceptions import RateLimitException
from app.core.rate_limiter import MinuteRateLimiter


class FakeTime:
    """Controllable monotonic clock (no real sleeps)."""

    def __init__(self):
        self.now = 1_000.0

    def monotonic(self) -> float:
        return self.now


@pytest.fixture
def fake_time(monkeypatch):
    ft = FakeTime()
    import app.core.rate_limiter as module

    monkeypatch.setattr(module, "time", ft)
    return ft


def test_allows_up_to_max_calls_then_rejects(fake_time):
    limiter = MinuteRateLimiter(max_calls=3)
    for _ in range(3):
        limiter.check_and_increment("ip:path")  # 不抛即通过
    with pytest.raises(RateLimitException) as exc:
        limiter.check_and_increment("ip:path")
    assert exc.value.error_code == "AUTH_RATE_LIMIT_EXCEEDED"


def test_window_rollover_resets_count(fake_time):
    limiter = MinuteRateLimiter(max_calls=1)
    limiter.check_and_increment("ip:path")
    with pytest.raises(RateLimitException):
        limiter.check_and_increment("ip:path")
    fake_time.now += 61  # 窗口滚动
    limiter.check_and_increment("ip:path")  # 不抛：新窗口重新计数


def test_keys_are_isolated(fake_time):
    limiter = MinuteRateLimiter(max_calls=1)
    limiter.check_and_increment("ip-a:login")
    with pytest.raises(RateLimitException):
        limiter.check_and_increment("ip-a:login")
    limiter.check_and_increment("ip-b:login")  # 不同 key 不受影响


def test_prune_drops_expired_windows_at_threshold(fake_time):
    limiter = MinuteRateLimiter(max_calls=1)
    limiter._prune_threshold = 4
    # 直接预置 4 个已过期的窗口：下一次插入触达阈值，触发清扫
    limiter._counts = {f"old-{i}": (1, fake_time.now - 120) for i in range(4)}
    limiter.check_and_increment("ip-new:login")
    assert limiter._counts.keys() == {"ip-new:login"}


def test_prune_keeps_live_windows(fake_time):
    limiter = MinuteRateLimiter(max_calls=1)
    limiter._prune_threshold = 2
    limiter._counts = {
        "old:login": (1, fake_time.now - 120),   # 已过期 → 应被清
        "live:login": (1, fake_time.now - 30),   # 仍存活 → 不得被清
    }
    limiter.check_and_increment("ip-new:login")
    assert "live:login" in limiter._counts
    assert "old:login" not in limiter._counts
    assert "ip-new:login" in limiter._counts
