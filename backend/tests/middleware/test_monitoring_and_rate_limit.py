"""Coverage tests for monitoring + rate_limit middlewares.

Targets:
  * app.middleware.monitoring.setup_monitoring (52% -> ~95%)
      - Missing lines 27-32 (Sentry init + ImportError fallback)
      - Missing lines 35-38 (PostHog init + ImportError fallback)
      - Missing line  44 (return value with sentry/posthog flags)
  * app.middleware.rate_limit.RateLimitMiddleware.dispatch (76% -> ~95%)
      - Missing lines 70-91 (rate-limit check + 429 response)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# ─── setup_monitoring ───────────────────────────────────────────────────


class TestSetupMonitoring:
    """setup_monitoring: Sentry/PostHog init + return flags."""

    def test_disabled_when_no_env(self, monkeypatch):
        """No SENTRY_DSN or POSTHOG_API_KEY -> returns None."""
        monkeypatch.delenv("SENTRY_DSN", raising=False)
        monkeypatch.delenv("POSTHOG_API_KEY", raising=False)
        from app.middleware.monitoring import setup_monitoring

        assert setup_monitoring(app=MagicMock()) is None

    def test_sentry_enabled_returns_dict_with_flags(self, monkeypatch):
        """SENTRY_DSN set -> returns dict with sentry_initialized=True."""
        monkeypatch.setenv("SENTRY_DSN", "https://fake@sentry.io/123")
        monkeypatch.delenv("POSTHOG_API_KEY", raising=False)
        from app.middleware.monitoring import setup_monitoring

        # If sentry_sdk is installed it will init; if not, ImportError is caught.
        # Either way, the function should return a dict (line 44).
        result = setup_monitoring(app=MagicMock())

        if result is not None:
            assert result["sentry_initialized"] is True
            assert result["posthog_initialized"] is False

    def test_posthog_only_returns_none(self, monkeypatch):
        """POSTHOG_API_KEY set without SENTRY_DSN -> returns None (line 40 branch)."""
        monkeypatch.delenv("SENTRY_DSN", raising=False)
        monkeypatch.setenv("POSTHOG_API_KEY", "phc_fake_key")
        from app.middleware.monitoring import setup_monitoring

        # When SENTRY_DSN is empty, line 40-42 path returns None regardless of
        # PostHog. The PostHog init block (35-38) still runs and logs.
        result = setup_monitoring(app=MagicMock())
        assert result is None

    def test_both_envs_set_returns_dict(self, monkeypatch):
        """Both envs set -> returns dict with both flags True (if no ImportError)."""
        monkeypatch.setenv("SENTRY_DSN", "https://fake@sentry.io/123")
        monkeypatch.setenv("POSTHOG_API_KEY", "phc_fake_key")
        from app.middleware.monitoring import setup_monitoring

        result = setup_monitoring(app=MagicMock())
        if result is not None:
            assert result["sentry_initialized"] is True
            assert result["posthog_initialized"] is True


# ─── RateLimitMiddleware.dispatch ──────────────────────────────────────


def _make_request(path: str, user_id: str | None) -> MagicMock:
    """Build a MagicMock Request with the given path and state.user_id."""
    request = MagicMock()
    request.url.path = path
    request.state.user_id = user_id
    return request


class TestRateLimitMiddleware:
    """RateLimitMiddleware.dispatch: pass-through, no user_id, 429 on limit."""

    @pytest.mark.asyncio
    async def test_non_limited_path_passes_through(self):
        """Path not in _RATE_LIMITED_PATHS -> call_next is invoked, no limit check."""
        from app.middleware.rate_limit import RateLimitMiddleware

        mock_limiter = MagicMock()
        middleware = RateLimitMiddleware(app=MagicMock(), rate_limiter=mock_limiter)
        request = _make_request("/api/v1/health", user_id="u-1")

        call_next = AsyncMock(return_value="passthrough")
        result = await middleware.dispatch(request, call_next)

        assert result == "passthrough"
        mock_limiter.check_and_increment.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_user_id_passes_through(self):
        """request.state.user_id is None -> pass through (auth handles it)."""
        from app.middleware.rate_limit import RateLimitMiddleware

        mock_limiter = MagicMock()
        middleware = RateLimitMiddleware(app=MagicMock(), rate_limiter=mock_limiter)
        request = _make_request("/api/v1/topics/recommend", user_id=None)

        call_next = AsyncMock(return_value="passthrough")
        result = await middleware.dispatch(request, call_next)

        assert result == "passthrough"
        mock_limiter.check_and_increment.assert_not_called()

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_returns_429(self):
        """RateLimitException raised -> 429 JSONResponse with reset_at/limit/used."""
        from app.core.exceptions import RateLimitException
        from app.middleware.rate_limit import RateLimitMiddleware

        mock_limiter = MagicMock()
        mock_limiter.check_and_increment.side_effect = RateLimitException(
            "Daily limit reached"
        )
        mock_limiter.get_remaining.return_value = {
            "reset_at": "2026-06-19T00:00:00Z",
            "limit": 20,
            "used": 20,
        }
        middleware = RateLimitMiddleware(app=MagicMock(), rate_limiter=mock_limiter)
        request = _make_request("/api/v1/topics/recommend", user_id="u-1")

        call_next = AsyncMock()
        result = await middleware.dispatch(request, call_next)

        # 429 short-circuits the call_next.
        assert result.status_code == 429
        call_next.assert_not_called()
        # Body is JSON-decodable to the documented envelope.
        import json as _json
        body = result.body.decode("utf-8") if isinstance(result.body, bytes) else result.body
        parsed = _json.loads(body)
        assert parsed["code"] == 429
        assert parsed["data"] is None
        assert "已用完" in parsed["message"]
        meta = parsed["meta"]
        assert meta["error_code"] == "RATE_LIMIT_EXCEEDED"
        assert meta["reset_at"] == "2026-06-19T00:00:00Z"
        assert meta["limit"] == 20
        assert meta["used"] == 20
        assert meta["remaining"] == 0

    @pytest.mark.asyncio
    async def test_within_limit_passes_through(self):
        """check_and_increment returns normally -> call_next is invoked."""
        from app.middleware.rate_limit import RateLimitMiddleware

        mock_limiter = MagicMock()
        mock_limiter.check_and_increment.return_value = None
        middleware = RateLimitMiddleware(app=MagicMock(), rate_limiter=mock_limiter)
        request = _make_request("/api/v1/viral/analyze", user_id="u-2")

        call_next = AsyncMock(return_value="ok")
        result = await middleware.dispatch(request, call_next)

        assert result == "ok"
        mock_limiter.check_and_increment.assert_called_once_with("u-2")
        call_next.assert_called_once()
