"""Rate limit middleware for AI call throttling.

Enforces the daily AI call limit (default 20/day for free users).
Returns 429 Too Many Requests when limit is exceeded.
"""

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.exceptions import RateLimitException
from app.core.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# Rate-limited API paths (AI call endpoints)
_RATE_LIMITED_PATHS: set[str] = {
    "/api/v1/topics/recommend",
    "/api/v1/viral/analyze",
    "/api/v1/ideas/boost",
    "/api/v1/titles/optimize",
    "/api/v1/tracks/diagnose",
    "/api/v1/profiles/onboarding",
    "/api/v1/profiles/me",  # PUT only
    "/api/v1/reviews/predict",
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware that checks AI call rate limits for protected endpoints.

    Only counts AI-call endpoints. Non-limited paths pass through freely.
    """

    def __init__(self, app, rate_limiter: RateLimiter | None = None):
        """Initialize the rate limit middleware.

        Args:
            app: The FastAPI application.
            rate_limiter: RateLimiter instance. Creates default if None.
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()

    async def dispatch(self, request: Request, call_next):
        """Check rate limit before processing the request.

        Args:
            request: The incoming HTTP request.
            call_next: The next handler in the chain.

        Returns:
            HTTP response or 429 error.
        """
        path = request.url.path

        # Only check rate limits for AI-call endpoints
        if path not in _RATE_LIMITED_PATHS:
            return await call_next(request)

        # Extract user_id from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id is None:
            # If no user context, still pass through (auth middleware will handle)
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
