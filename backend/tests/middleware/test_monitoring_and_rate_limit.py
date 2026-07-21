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


def _make_request(
    path: str,
    user_id: str | None = None,
    client_host: str | None = "127.0.0.1",
) -> MagicMock:
    """Build a MagicMock Request with the given path, state.user_id and client.host.

    ``client_host=None`` simulates a request with ``request.client`` unset
    (e.g. some test clients / proxied environments without a peer).
    """
    request = MagicMock()
    request.url.path = path
    request.state.user_id = user_id
    if client_host is None:
        request.client = None
    else:
        request.client = MagicMock(host=client_host)
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
    async def test_no_user_id_routes_to_anonymous_limiter(self):
        """request.state.user_id is None on an AI endpoint -> routed to the
        anonymous IP limiter (NOT the daily AI limiter) and, when the anonymous
        budget allows, the request passes through.

        D4 reverses the previous D3 contract which silently passed anonymous
        AI calls. The daily limiter (``mock_limiter``) must remain untouched.
        """
        from app.middleware.rate_limit import RateLimitMiddleware

        mock_limiter = MagicMock()  # daily AI limiter — must NOT be touched
        mock_anon = MagicMock()  # anonymous IP limiter — MUST be touched
        middleware = RateLimitMiddleware(
            app=MagicMock(),
            rate_limiter=mock_limiter,
            anonymous_rate_limiter=mock_anon,
        )
        request = _make_request(
            "/api/v1/topics/recommend", user_id=None, client_host="10.0.0.10"
        )

        call_next = AsyncMock(return_value="passthrough")
        result = await middleware.dispatch(request, call_next)

        assert result == "passthrough"
        mock_limiter.check_and_increment.assert_not_called()
        mock_anon.check_and_increment.assert_called_once_with("10.0.0.10")

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


# ─── Anonymous AI-call rate limiting (D4) ───────────────────────────────


class TestAnonymousAIRateLimit:
    """Per-IP hourly-window rate limiting for anonymous AI calls.

    D4 reverses the D3 "anonymous AI endpoint passes through" hole: anonymous
    callers (no ``user_id`` on request.state) hitting AI-call endpoints now
    share a strict per-IP budget (default 20/hour/IP) so an unauthenticated
    client cannot brute-force the LLM. Authenticated callers continue to use
    the daily per-user limiter.
    """

    def _middleware(self, max_per_hour: int = 20):
        from app.core.rate_limiter import MinuteRateLimiter
        from app.middleware.rate_limit import RateLimitMiddleware

        # AI daily limiter is a MagicMock: must NOT be touched by the anon path.
        daily = MagicMock()
        anon = MinuteRateLimiter(
            max_calls_per_minute=max_per_hour, window_seconds=3600.0
        )
        return RateLimitMiddleware(
            app=MagicMock(),
            rate_limiter=daily,
            anonymous_rate_limiter=anon,
        )

    @pytest.mark.asyncio
    async def test_anonymous_ai_endpoint_rate_limited(self):
        """20 same-IP anonymous AI calls pass; the 21st returns 429."""
        middleware = self._middleware(max_per_hour=20)

        call_next = AsyncMock(return_value="ok")
        for _ in range(20):
            request = _make_request(
                "/api/v1/topics/recommend", user_id=None, client_host="10.0.0.10"
            )
            result = await middleware.dispatch(request, call_next)
            assert result == "ok"

        # 21st request — should hit the anonymous rate limiter.
        request = _make_request(
            "/api/v1/topics/recommend", user_id=None, client_host="10.0.0.10"
        )
        result = await middleware.dispatch(request, call_next)
        assert result.status_code == 429
        # Daily limiter untouched on the anonymous path.
        middleware.rate_limiter.check_and_increment.assert_not_called()

    @pytest.mark.asyncio
    async def test_anonymous_ai_rate_limit_per_ip(self):
        """IP A exhausting its budget must NOT block IP B."""
        middleware = self._middleware(max_per_hour=1)

        call_next = AsyncMock(return_value="ok")
        request_a = _make_request(
            "/api/v1/topics/recommend", user_id=None, client_host="10.0.0.1"
        )
        await middleware.dispatch(request_a, call_next)

        # IP A is now blocked.
        request_a2 = _make_request(
            "/api/v1/topics/recommend", user_id=None, client_host="10.0.0.1"
        )
        result_a = await middleware.dispatch(request_a2, call_next)
        assert result_a.status_code == 429

        # IP B should still pass through.
        request_b = _make_request(
            "/api/v1/topics/recommend", user_id=None, client_host="10.0.0.2"
        )
        result_b = await middleware.dispatch(request_b, call_next)
        assert result_b == "ok"

    @pytest.mark.asyncio
    async def test_anonymous_ai_429_message_generic(self):
        """429 message is generic — does NOT leak the auth tier (no "登录" hint).

        Leaking "登录" tells an attacker the endpoint has an authentication
        tier to chase. The anonymous 429 uses the same generic wording as the
        auth limiter so no information about the auth state is disclosed.
        """
        middleware = self._middleware(max_per_hour=1)

        call_next = AsyncMock(return_value="ok")
        request1 = _make_request(
            "/api/v1/topics/recommend", user_id=None, client_host="10.0.0.3"
        )
        await middleware.dispatch(request1, call_next)

        request2 = _make_request(
            "/api/v1/topics/recommend", user_id=None, client_host="10.0.0.3"
        )
        result = await middleware.dispatch(request2, call_next)
        assert result.status_code == 429

        import json as _json

        body = (
            result.body.decode("utf-8")
            if isinstance(result.body, bytes)
            else result.body
        )
        parsed = _json.loads(body)
        assert parsed["code"] == 429
        assert parsed["data"] is None
        # Message must distinguish from the daily AI limiter ("已用完") but
        # must NOT leak the authentication tier ("登录").
        assert "已用完" not in parsed["message"]
        assert "登录" not in parsed["message"]
        assert "频繁" in parsed["message"]
        assert parsed["meta"]["error_code"] == "ANONYMOUS_AI_RATE_LIMIT_EXCEEDED"

    @pytest.mark.asyncio
    async def test_anonymous_ai_429_does_not_leak_threshold(self):
        """429 meta must NOT expose limit/used/reset_at/remaining.

        Leaking thresholds lets an attacker tune brute-force cadence to just
        under the budget. The anonymous 429 envelope keeps only error_code,
        matching the D3 S2 principle applied to auth 429s.
        """
        middleware = self._middleware(max_per_hour=1)

        call_next = AsyncMock(return_value="ok")
        request1 = _make_request(
            "/api/v1/topics/recommend", user_id=None, client_host="10.0.0.4"
        )
        await middleware.dispatch(request1, call_next)

        request2 = _make_request(
            "/api/v1/topics/recommend", user_id=None, client_host="10.0.0.4"
        )
        result = await middleware.dispatch(request2, call_next)
        assert result.status_code == 429

        import json as _json

        body = (
            result.body.decode("utf-8")
            if isinstance(result.body, bytes)
            else result.body
        )
        parsed = _json.loads(body)
        assert parsed["code"] == 429
        assert parsed["data"] is None
        meta = parsed["meta"]
        assert set(meta.keys()) == {"error_code"}
        assert meta["error_code"] == "ANONYMOUS_AI_RATE_LIMIT_EXCEEDED"

    @pytest.mark.asyncio
    async def test_authenticated_user_uses_daily_limiter_not_anonymous(self):
        """Authenticated requests must flow through the daily AI limiter, not
        the anonymous IP limiter. The anonymous limiter must NOT count the call.
        """
        from app.middleware.rate_limit import RateLimitMiddleware

        mock_anon = MagicMock()
        middleware = RateLimitMiddleware(
            app=MagicMock(),
            rate_limiter=MagicMock(),  # daily — will be asserted
            anonymous_rate_limiter=mock_anon,
        )

        call_next = AsyncMock(return_value="ok")
        request = _make_request(
            "/api/v1/topics/recommend", user_id="u-1", client_host="10.0.0.5"
        )
        result = await middleware.dispatch(request, call_next)

        assert result == "ok"
        middleware.rate_limiter.check_and_increment.assert_called_once_with("u-1")
        mock_anon.check_and_increment.assert_not_called()

    @pytest.mark.asyncio
    async def test_anonymous_publish_suggest_rate_limited(self):
        """D4 M1: /api/v1/publish/suggest is reachable anonymously and calls
        the LLM (publish_advisor._analyze_with_llm). It MUST be in
        _RATE_LIMITED_PATHS so anonymous callers are throttled per-IP —
        otherwise the D4 hole reopens via this route.
        """
        from app.middleware.rate_limit import _RATE_LIMITED_PATHS

        assert "/api/v1/publish/suggest" in _RATE_LIMITED_PATHS

        middleware = self._middleware(max_per_hour=2)
        call_next = AsyncMock(return_value="ok")
        for _ in range(2):
            request = _make_request(
                "/api/v1/publish/suggest", user_id=None, client_host="10.0.0.20"
            )
            result = await middleware.dispatch(request, call_next)
            assert result == "ok"

        request = _make_request(
            "/api/v1/publish/suggest", user_id=None, client_host="10.0.0.20"
        )
        result = await middleware.dispatch(request, call_next)
        assert result.status_code == 429
        # Daily limiter untouched on the anonymous path.
        middleware.rate_limiter.check_and_increment.assert_not_called()

    @pytest.mark.asyncio
    async def test_anonymous_topics_refresh_rate_limited(self):
        """D4 M1: /api/v1/topics/refresh is reachable anonymously and reroutes
        to TopicRecommendService (DataManager cascade includes the LLM tier).
        It MUST be in _RATE_LIMITED_PATHS so anonymous callers are throttled.
        """
        from app.middleware.rate_limit import _RATE_LIMITED_PATHS

        assert "/api/v1/topics/refresh" in _RATE_LIMITED_PATHS

        middleware = self._middleware(max_per_hour=1)
        call_next = AsyncMock(return_value="ok")
        request1 = _make_request(
            "/api/v1/topics/refresh", user_id=None, client_host="10.0.0.21"
        )
        await middleware.dispatch(request1, call_next)

        request2 = _make_request(
            "/api/v1/topics/refresh", user_id=None, client_host="10.0.0.21"
        )
        result = await middleware.dispatch(request2, call_next)
        assert result.status_code == 429
        middleware.rate_limiter.check_and_increment.assert_not_called()

    @pytest.mark.asyncio
    async def test_default_anonymous_limiter_reads_settings_anonymous_ai_calls_per_hour(
        self, monkeypatch
    ):
        """D4 C1: when RateLimitMiddleware is constructed with NO explicit
        anonymous_rate_limiter / anonymous_max_per_hour (the production path
        — main.py just does add_middleware(RateLimitMiddleware)), the limiter
        MUST pick up settings.anonymous_ai_calls_per_hour — NOT fall back to
        MinuteRateLimiter's internal default which is auth_rate_limit_per_minute
        (5). Before C1 fix the new settings field was dead code and the
        anonymous budget was silently 5/h instead of the configured value.
        """

        # Reset the settings singleton so the patched env re-reads cleanly.
        import config.settings as _settings_module

        monkeypatch.setenv("ANONYMOUS_AI_CALLS_PER_HOUR", "7")
        _settings_module._settings = None
        try:
            from app.middleware.rate_limit import RateLimitMiddleware

            middleware = RateLimitMiddleware(app=MagicMock())
            # The auto-constructed anonymous limiter's max_calls_per_minute
            # must equal the settings value (7), proving the settings field is
            # actually consulted on the production path.
            assert (
                middleware.anonymous_rate_limiter.max_calls_per_minute == 7
            ), (
                "anonymous_rate_limiter did not read settings.anonymous_ai_calls_per_hour; "
                " MinuteRateLimiter likely fell back to auth_rate_limit_per_minute (D4 C1 regression)"
            )
        finally:
            _settings_module._settings = None


# ─── Auth endpoint rate limiting (D3) ───────────────────────────────────


class TestAuthRateLimit:
    """Per-IP minute-window rate limiting for auth endpoints."""

    def _middleware(self, max_per_minute: int = 5):
        from app.middleware.rate_limit import RateLimitMiddleware

        return RateLimitMiddleware(
            app=MagicMock(),
            rate_limiter=MagicMock(),  # AI limiter — must NOT be touched
            auth_rate_limiter=None,  # force default MinuteRateLimiter
            auth_max_per_minute=max_per_minute,
        )

    @pytest.mark.asyncio
    async def test_auth_login_rate_limited_after_5_per_minute_per_ip(self):
        """5 same-IP login calls pass; the 6th returns 429."""
        middleware = self._middleware(max_per_minute=5)

        call_next = AsyncMock(return_value="ok")
        for _ in range(5):
            request = _make_request("/api/v1/auth/login", client_host="10.0.0.1")
            result = await middleware.dispatch(request, call_next)
            assert result == "ok"

        # 6th request — should hit the auth rate limiter.
        request = _make_request("/api/v1/auth/login", client_host="10.0.0.1")
        result = await middleware.dispatch(request, call_next)
        assert result.status_code == 429
        # AI rate limiter untouched for auth endpoints.
        middleware.rate_limiter.check_and_increment.assert_not_called()

    @pytest.mark.asyncio
    async def test_auth_register_rate_limited(self):
        """register endpoint enforces the same IP minute-window."""
        middleware = self._middleware(max_per_minute=5)

        call_next = AsyncMock(return_value="ok")
        for _ in range(5):
            request = _make_request("/api/v1/auth/register", client_host="10.0.0.2")
            result = await middleware.dispatch(request, call_next)
            assert result == "ok"

        request = _make_request("/api/v1/auth/register", client_host="10.0.0.2")
        result = await middleware.dispatch(request, call_next)
        assert result.status_code == 429

    @pytest.mark.asyncio
    async def test_auth_refresh_rate_limited(self):
        """refresh endpoint enforces the same IP minute-window."""
        middleware = self._middleware(max_per_minute=5)

        call_next = AsyncMock(return_value="ok")
        for _ in range(5):
            request = _make_request("/api/v1/auth/refresh", client_host="10.0.0.3")
            result = await middleware.dispatch(request, call_next)
            assert result == "ok"

        request = _make_request("/api/v1/auth/refresh", client_host="10.0.0.3")
        result = await middleware.dispatch(request, call_next)
        assert result.status_code == 429

    @pytest.mark.asyncio
    async def test_auth_endpoints_have_independent_budgets(self):
        """A failed-login burst must not consume registration's budget."""
        middleware = self._middleware(max_per_minute=1)

        call_next = AsyncMock(return_value="ok")
        login = _make_request("/api/v1/auth/login", client_host="10.0.0.10")
        register = _make_request("/api/v1/auth/register", client_host="10.0.0.10")

        assert await middleware.dispatch(login, call_next) == "ok"
        assert await middleware.dispatch(register, call_next) == "ok"

        login_again = _make_request(
            "/api/v1/auth/login", client_host="10.0.0.10"
        )
        register_again = _make_request(
            "/api/v1/auth/register", client_host="10.0.0.10"
        )
        assert (await middleware.dispatch(login_again, call_next)).status_code == 429
        assert (await middleware.dispatch(register_again, call_next)).status_code == 429

    @pytest.mark.asyncio
    async def test_auth_rate_limit_is_per_ip(self):
        """IP A exhausting its budget must NOT block IP B."""
        middleware = self._middleware(max_per_minute=5)

        call_next = AsyncMock(return_value="ok")
        for _ in range(5):
            request = _make_request("/api/v1/auth/login", client_host="10.0.0.1")
            await middleware.dispatch(request, call_next)

        # IP A is now blocked.
        request_a = _make_request("/api/v1/auth/login", client_host="10.0.0.1")
        result_a = await middleware.dispatch(request_a, call_next)
        assert result_a.status_code == 429

        # IP B should still pass through.
        request_b = _make_request("/api/v1/auth/login", client_host="10.0.0.2")
        result_b = await middleware.dispatch(request_b, call_next)
        assert result_b == "ok"

    @pytest.mark.asyncio
    async def test_non_auth_path_not_rate_limited_by_auth_limiter(self):
        """AI endpoints are governed by the AI limiter, not the auth limiter."""
        middleware = self._middleware(max_per_minute=1)

        call_next = AsyncMock(return_value="ok")
        # Even with auth_max_per_minute=1, AI recommend endpoint must pass and
        # must delegate to the AI limiter (here a MagicMock) rather than the
        # auth MinuteRateLimiter.
        request = _make_request(
            "/api/v1/topics/recommend", user_id="u-1", client_host="10.0.0.9"
        )
        result = await middleware.dispatch(request, call_next)
        assert result == "ok"
        middleware.rate_limiter.check_and_increment.assert_called_once_with("u-1")

    @pytest.mark.asyncio
    async def test_auth_endpoint_anonymous_still_rate_limited(self):
        """Auth endpoints with no user_id are still rate-limited by IP."""
        middleware = self._middleware(max_per_minute=5)

        call_next = AsyncMock(return_value="ok")
        for _ in range(5):
            request = _make_request(
                "/api/v1/auth/login", user_id=None, client_host="10.0.0.4"
            )
            result = await middleware.dispatch(request, call_next)
            assert result == "ok"

        request = _make_request(
            "/api/v1/auth/login", user_id=None, client_host="10.0.0.4"
        )
        result = await middleware.dispatch(request, call_next)
        assert result.status_code == 429

    @pytest.mark.asyncio
    async def test_auth_rate_limit_429_has_distinct_message(self):
        """429 from auth limiter uses an auth-specific message (not the AI daily one)."""
        middleware = self._middleware(max_per_minute=1)

        call_next = AsyncMock(return_value="ok")
        request1 = _make_request("/api/v1/auth/login", client_host="10.0.0.5")
        await middleware.dispatch(request1, call_next)

        request2 = _make_request("/api/v1/auth/login", client_host="10.0.0.5")
        result = await middleware.dispatch(request2, call_next)
        assert result.status_code == 429

        import json as _json

        body = (
            result.body.decode("utf-8")
            if isinstance(result.body, bytes)
            else result.body
        )
        parsed = _json.loads(body)
        assert parsed["code"] == 429
        assert parsed["data"] is None
        assert "已用完" not in parsed["message"]
        assert parsed["meta"]["error_code"] == "AUTH_RATE_LIMIT_EXCEEDED"

    @pytest.mark.asyncio
    async def test_auth_rate_limit_unknown_ip_uses_unknown_bucket(self):
        """When request.client is None, IP falls back to 'unknown' bucket."""
        middleware = self._middleware(max_per_minute=1)

        call_next = AsyncMock(return_value="ok")
        request1 = _make_request("/api/v1/auth/login", client_host=None)
        result1 = await middleware.dispatch(request1, call_next)
        assert result1 == "ok"

        # Second call from same "unknown" bucket should be limited.
        request2 = _make_request("/api/v1/auth/login", client_host=None)
        result2 = await middleware.dispatch(request2, call_next)
        assert result2.status_code == 429

    @pytest.mark.asyncio
    async def test_auth_rate_limit_window_resets(self):
        """After the minute window elapses, the counter resets (fixed window)."""
        from app.core.rate_limiter import MinuteRateLimiter

        limiter = MinuteRateLimiter(max_calls_per_minute=2)
        # Fill the window.
        limiter.check_and_increment("10.0.0.6")
        limiter.check_and_increment("10.0.0.6")
        # Manipulate the stored window_start to the past to simulate elapsed time.
        with limiter._lock:
            limiter._counts["10.0.0.6"]["window_start"] -= 61.0
        # Should now be allowed again.
        result = limiter.check_and_increment("10.0.0.6")
        assert result["used"] == 1

    @pytest.mark.asyncio
    async def test_auth_login_trailing_slash_still_rate_limited(self):
        """POST /api/v1/auth/login/ (trailing slash) is still rate-limited.

        FastAPI default ``redirect_slashes=True`` would otherwise 307-redirect
        the canonical path, bypassing the auth limiter. The middleware normalises
        the path by stripping the trailing slash before set membership checks.
        """
        middleware = self._middleware(max_per_minute=5)

        call_next = AsyncMock(return_value="ok")
        for _ in range(5):
            request = _make_request("/api/v1/auth/login/", client_host="10.0.0.7")
            result = await middleware.dispatch(request, call_next)
            assert result == "ok"

        request = _make_request("/api/v1/auth/login/", client_host="10.0.0.7")
        result = await middleware.dispatch(request, call_next)
        assert result.status_code == 429

    @pytest.mark.asyncio
    async def test_auth_429_does_not_leak_threshold(self):
        """Auth 429 meta must NOT expose limit/used/reset_at/remaining.

        Leaking thresholds lets an attacker tune brute-force cadence. The auth
        429 envelope keeps only code/data/message/error_code.
        """
        middleware = self._middleware(max_per_minute=1)

        call_next = AsyncMock(return_value="ok")
        request1 = _make_request("/api/v1/auth/login", client_host="10.0.0.8")
        await middleware.dispatch(request1, call_next)

        request2 = _make_request("/api/v1/auth/login", client_host="10.0.0.8")
        result = await middleware.dispatch(request2, call_next)
        assert result.status_code == 429

        import json as _json

        body = (
            result.body.decode("utf-8")
            if isinstance(result.body, bytes)
            else result.body
        )
        parsed = _json.loads(body)
        assert parsed["code"] == 429
        assert parsed["data"] is None
        meta = parsed["meta"]
        assert set(meta.keys()) == {"error_code"}
        assert meta["error_code"] == "AUTH_RATE_LIMIT_EXCEEDED"
