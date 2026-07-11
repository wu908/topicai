"""Rate limit middleware for AI call throttling.

Enforces three independent budgets:

* Daily AI call limit (default 20/day for free users) keyed by ``user_id``.
* Per-minute auth endpoint limit (default 5/min/IP) keyed by client IP for
  ``/api/v1/auth/{login,register,refresh}`` to blunt credential-stuffing
  and registration flooding.
* Per-hour anonymous AI-call limit (default 20/hour/IP, D4) keyed by client
  IP for AI endpoints when no authenticated ``user_id`` is present, so an
  unauthenticated client cannot brute-force the LLM.

Returns 429 Too Many Requests when a limit is exceeded. The three paths emit
distinct messages and ``error_code`` so clients can distinguish them.
"""

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.exceptions import RateLimitException
from app.core.rate_limiter import MinuteRateLimiter, RateLimiter

logger = logging.getLogger(__name__)

# Rate-limited API paths (AI call endpoints). Every route whose handler may
# invoke the LLM AND which is reachable anonymously (no ``Depends(get_current_user)``)
# MUST be listed here — otherwise the anonymous AI rate limiter (D4) is
# bypassed via ``if path not in _RATE_LIMITED_PATHS: return`` short-circuit.
# Routes guarded by ``Depends(get_current_user)`` 401 unauthenticated callers
# before the middleware's user_id branch, so they need NOT be listed for the
# anonymous path (they are still safe; the daily per-user limiter covers
# authenticated callers via the user_id branch).
_RATE_LIMITED_PATHS: set[str] = {
    "/api/v1/topics/recommend",
    "/api/v1/topics/refresh",  # D4 M1: reachable anonymously, calls LLM via DataManager cascade
    "/api/v1/viral/analyze",
    "/api/v1/ideas/boost",
    "/api/v1/titles/optimize",
    "/api/v1/tracks/diagnose",
    "/api/v1/publish/suggest",  # D4 M1: reachable anonymously, calls publish_advisor._analyze_with_llm
    "/api/v1/profiles/onboarding",
    "/api/v1/profiles/me",  # PUT only
    "/api/v1/reviews/predict",
}

# Auth endpoints governed by the per-IP minute limiter. These are evaluated
# *before* the AI-call branch so they are rate-limited even when the request
# is anonymous (login/register have no user_id yet).
_AUTH_RATE_LIMITED_PATHS: set[str] = {
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
}


def _client_ip(request: Request) -> str:
    """Extract the client IP from the request.

    Falls back to the literal string ``"unknown"`` when ``request.client`` is
    ``None`` (can happen with some test transports / misconfigured proxies).
    All client-less callers then share one ``"unknown"`` budget bucket — a
    warning is logged so a flooded ``"unknown"`` bucket is observable rather
    than silently denying service to other client-less callers.

    TODO(D4/future): honour ``X-Forwarded-For`` when running behind a trusted
    proxy; MVP uses the direct peer address to avoid spoofing via header.
    """
    client = getattr(request, "client", None)
    if client is None:
        logger.warning(
            "rate_limit: request.client is None; all such requests share the "
            "'unknown' bucket — possible proxy/config issue"
        )
        return "unknown"
    host = getattr(client, "host", None)
    return host or "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware that checks AI call rate limits for protected endpoints.

    Only counts AI-call endpoints. Non-limited paths pass through freely.
    """

    def __init__(
        self,
        app,
        rate_limiter: RateLimiter | None = None,
        auth_rate_limiter: MinuteRateLimiter | None = None,
        auth_max_per_minute: int | None = None,
        anonymous_rate_limiter: MinuteRateLimiter | None = None,
        anonymous_max_per_hour: int | None = None,
    ):
        """Initialize the rate limit middleware.

        Args:
            app: The FastAPI application.
            rate_limiter: ``RateLimiter`` instance for AI calls. Default if None.
            auth_rate_limiter: ``MinuteRateLimiter`` instance for auth endpoints.
                When ``None`` (default) a fresh ``MinuteRateLimiter`` is created,
                using ``auth_max_per_minute`` (or the settings default) as the
                per-minute budget. Pass an explicit instance (e.g. a mock) to
                bypass auto-construction.
            auth_max_per_minute: Optional override for the per-minute budget; only
                applies when ``auth_rate_limiter`` is left to be auto-created.
            anonymous_rate_limiter: ``MinuteRateLimiter`` instance for anonymous
                AI-call endpoints (D4). When ``None`` (default) a fresh
                ``MinuteRateLimiter`` is created with a 3600s window and
                ``anonymous_max_per_hour`` (or the settings default
                ``anonymous_ai_calls_per_hour``) as the per-hour budget.
                Anonymous callers (no ``user_id`` on request.state) hitting
                AI-call endpoints are throttled per-IP instead of passing
                through unbounded.
            anonymous_max_per_hour: Optional override for the per-hour budget;
                only applies when ``anonymous_rate_limiter`` is auto-created.
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
        if auth_rate_limiter is None:
            self.auth_rate_limiter = MinuteRateLimiter(
                max_calls_per_minute=auth_max_per_minute
            )
        else:
            self.auth_rate_limiter = auth_rate_limiter
        if anonymous_rate_limiter is None:
            # Read the settings default explicitly. MinuteRateLimiter's own
            # fallback would otherwise pick ``auth_rate_limit_per_minute``
            # (a *minute* budget of 5) — silently making the anonymous hourly
            # budget 5/h instead of the configured 20/h and leaving the
            # ``anonymous_ai_calls_per_hour`` setting as dead code. (D4 C1)
            from config.settings import get_settings

            anon_budget = (
                anonymous_max_per_hour
                if anonymous_max_per_hour is not None
                else get_settings().anonymous_ai_calls_per_hour
            )
            self.anonymous_rate_limiter = MinuteRateLimiter(
                max_calls_per_minute=anon_budget,
                window_seconds=3600.0,
            )
        else:
            self.anonymous_rate_limiter = anonymous_rate_limiter

    async def dispatch(self, request: Request, call_next):
        """Check rate limit before processing the request.

        Args:
            request: The incoming HTTP request.
            call_next: The next handler in the chain.

        Returns:
            HTTP response or 429 error.
        """
        path = request.url.path
        # Normalise trailing slash so POST /api/v1/auth/login/ (which FastAPI
        # would otherwise 307-redirect to the canonical path, bypassing the
        # middleware) is caught by the same set-membership checks. The root
        # path collapses to "" but neither rate-limited set contains it.
        if len(path) > 1:
            path = path.rstrip("/")

        # Auth endpoints: per-IP minute window, evaluated BEFORE the AI branch
        # so anonymous requests (login/register) are still throttled.
        if path in _AUTH_RATE_LIMITED_PATHS:
            ip = _client_ip(request)
            try:
                self.auth_rate_limiter.check_and_increment(ip)
            except RateLimitException:
                return JSONResponse(
                    status_code=429,
                    content={
                        "code": 429,
                        "data": None,
                        "message": "请求过于频繁，请稍后再试",
                        "meta": {
                            "error_code": "AUTH_RATE_LIMIT_EXCEEDED",
                        },
                    },
                )
            return await call_next(request)

        # Only check rate limits for AI-call endpoints
        if path not in _RATE_LIMITED_PATHS:
            return await call_next(request)

        # Extract user_id from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id is None:
            # Anonymous AI endpoint caller (D4): apply a strict per-IP hourly
            # budget instead of the previous "pass through unbounded" hole.
            # The daily limiter is keyed on user_id so it cannot be used here;
            # the anonymous limiter is an IP-keyed fixed-window instance.
            ip = _client_ip(request)
            try:
                self.anonymous_rate_limiter.check_and_increment(ip)
            except RateLimitException:
                return JSONResponse(
                    status_code=429,
                    content={
                        "code": 429,
                        "data": None,
                        "message": "请求过于频繁，请稍后再试",
                        "meta": {
                            "error_code": "ANONYMOUS_AI_RATE_LIMIT_EXCEEDED",
                        },
                    },
                )
            return await call_next(request)

        # Check rate limit
        try:
            self.rate_limiter.check_and_increment(user_id)
        except RateLimitException:
            # Rate limit exceeded
            reset_info = self.rate_limiter.get_remaining(user_id)
            return JSONResponse(
                status_code=429,
                content={
                    "code": 429,
                    "data": None,
                    "message": "今日AI调用次数已用完，请明天再试",
                    "meta": {
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "reset_at": reset_info.get("reset_at"),
                        "limit": reset_info.get("limit"),
                        "used": reset_info.get("used"),
                        "remaining": 0,
                    },
                },
            )

        return await call_next(request)
