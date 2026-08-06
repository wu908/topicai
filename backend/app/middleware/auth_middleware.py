"""JWT authentication middleware for the v2 API.

Parses the Authorization Bearer token on every request and injects
request.state.user_id if the token is valid. Does NOT reject requests
without a token — individual endpoints should enforce auth via Depends
or by checking request.state.user_id themselves.
"""

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Public paths that never need a token (skip overhead)
_PUBLIC_PATHS = {
    "/api/v2/health",
    "/api/v2/auth/register",
    "/api/v2/auth/login",
    "/api/v2/auth/refresh",
    "/docs",
    "/redoc",
    "/openapi.json",
}


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Middleware that extracts and verifies JWT bearer tokens.

    On every request:
    1. Reads the Authorization header.
    2. If a valid Bearer token is found, decodes it and sets
       request.state.user_id to the subject (user UUID).
    3. If no token or an invalid token is present, request.state.user_id
       remains None (endpoints decide how to handle unauthenticated access).
    """

    async def dispatch(self, request: Request, call_next):
        """Inject user_id from JWT if present and valid."""
        # Default: unauthenticated
        request.state.user_id = None

        # Skip overhead for public paths
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        authorization: str | None = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization[len("Bearer "):]
            try:
                from app.core.auth import AuthManager
                auth = AuthManager(db=request.app.state.db)
                user_id = auth.get_user_id_from_token(token)
                request.state.user_id = user_id
            except Exception as exc:
                # Token invalid/expired — continue as anonymous
                logger.debug(f"JWT parse failed: {type(exc).__name__}: {exc}")

        return await call_next(request)
