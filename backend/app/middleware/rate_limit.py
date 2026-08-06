"""Per-IP rate limiting for public authentication endpoints."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.exceptions import RateLimitException
from app.core.rate_limiter import MinuteRateLimiter

_AUTH_PATHS = {
    "/api/v2/auth/login",
    "/api/v2/auth/register",
    "/api/v2/auth/refresh",
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limiter: MinuteRateLimiter | None = None):
        super().__init__(app)
        self.limiter = limiter or MinuteRateLimiter()

    async def dispatch(self, request: Request, call_next):
        path = request.url.path.rstrip("/") or "/"
        if path not in _AUTH_PATHS:
            return await call_next(request)

        host = request.client.host if request.client else "unknown"
        try:
            self.limiter.check_and_increment(f"{host}:{path}")
        except RateLimitException:
            return JSONResponse(
                status_code=429,
                content={
                    "code": 429,
                    "data": None,
                    "message": "请求过于频繁，请稍后再试",
                    "meta": {"error_code": "AUTH_RATE_LIMIT_EXCEEDED"},
                },
            )
        return await call_next(request)
