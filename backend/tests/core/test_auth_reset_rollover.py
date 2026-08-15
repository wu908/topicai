"""Regression: AI-quota reset must roll over across a month boundary.

``register`` used to derive the next reset instant with
``reset_at.replace(day=reset_at.day + 1)``. On the last day of any month
that produces an out-of-range day number and ``replace`` raises
``ValueError``, so registration failed outright on the 28th/30th/31st
depending on the month. The fix uses ``timedelta(days=1)``.
"""

from datetime import UTC, datetime

import pytest

from app.core.auth import AuthManager


class _FrozenDatetime:
    """Minimal stand-in exposing only the ``now`` used by ``register``."""

    fixed = datetime(2026, 1, 31, 23, 30, tzinfo=UTC)

    @classmethod
    def now(cls, tz=None):
        return cls.fixed if tz is None else cls.fixed.astimezone(tz)


@pytest.mark.parametrize(
    ("frozen", "expected_reset"),
    [
        (datetime(2026, 1, 31, 23, 30, tzinfo=UTC), "2026-02-01T00:00:00Z"),
        (datetime(2026, 2, 28, 12, 0, tzinfo=UTC), "2026-03-01T00:00:00Z"),
        (datetime(2026, 4, 30, 0, 0, tzinfo=UTC), "2026-05-01T00:00:00Z"),
        (datetime(2026, 12, 31, 18, 0, tzinfo=UTC), "2027-01-01T00:00:00Z"),
    ],
    ids=["jan31", "feb28", "apr30", "dec31-year-roll"],
)
async def test_register_rolls_quota_reset_over_month_end(
    test_db, monkeypatch, frozen: datetime, expected_reset: str
):
    """Registering on the last day of a month stores the next month's 1st."""

    class Frozen(_FrozenDatetime):
        fixed = frozen

    monkeypatch.setattr("app.core.auth.datetime", Frozen)

    auth = AuthManager(test_db)
    await auth.register("edge@example.test", "edge-user", "sufficiently-long-pw")

    row = await test_db.fetch_one(
        "SELECT ai_calls_reset_at FROM users WHERE email=:email",
        {"email": "edge@example.test"},
    )
    assert row is not None
    assert row["ai_calls_reset_at"] == expected_reset


async def test_register_on_mid_month_day_is_next_day(test_db, monkeypatch):
    """Sanity check that the ordinary (non-boundary) case is unchanged."""

    class Frozen(_FrozenDatetime):
        fixed = datetime(2026, 6, 10, 9, 15, tzinfo=UTC)

    monkeypatch.setattr("app.core.auth.datetime", Frozen)

    auth = AuthManager(test_db)
    await auth.register("mid@example.test", "mid-user", "sufficiently-long-pw")

    row = await test_db.fetch_one(
        "SELECT ai_calls_reset_at FROM users WHERE email=:email",
        {"email": "mid@example.test"},
    )
    assert row is not None
    assert row["ai_calls_reset_at"] == "2026-06-11T00:00:00Z"
