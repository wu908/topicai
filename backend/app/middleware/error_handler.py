"""Global error handler middleware for TopicAI v4.0.

Catches unhandled exceptions and returns user-friendly JSON responses.
"""

import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.exceptions import AppException
from app.core.utils import utc_now

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware that catches exceptions and returns structured JSON errors.

    Ensures all API errors follow the unified response format:
    {code, data, message, meta}
    """

    async def dispatch(self, request: Request, call_next):
        """Process the request through the middleware.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware/handler in the chain.

        Returns:
            HTTP response (normal or error).
        """
        start_time = time.time()

        try:
            response = await call_next(request)

            # Add processing time header
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(round(process_time, 4))

            return response

        except AppException as exc:
            # Known application exception — return structured error
            process_time = time.time() - start_time
            logger.warning(
                f"AppException: {exc.error_code} — {exc.message}",
                extra={
                    "error_code": exc.error_code,
                    "status_code": exc.status_code,
                    "path": str(request.url),
                    "method": request.method,
                },
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "code": exc.status_code,
                    "data": None,
                    "message": exc.message,
                    "meta": {
                        "error_code": exc.error_code,
                        "timestamp": utc_now(),
                        "duration_ms": round(process_time * 1000),
                    },
                },
                headers={"X-Process-Time": str(round(process_time, 4))},
            )

        except Exception as exc:
            # Unhandled exception — log and return generic error
            process_time = time.time() - start_time
            logger.exception(
                f"Unhandled exception: {type(exc).__name__}: {exc}",
                extra={
                    "path": str(request.url),
                    "method": request.method,
                },
            )
            return JSONResponse(
                status_code=500,
                content={
                    "code": 500,
                    "data": None,
                    "message": "服务器内部错误，请稍后重试",
                    "meta": {
                        "error_code": "INTERNAL_ERROR",
                        "timestamp": utc_now(),
                        "duration_ms": round(process_time * 1000),
                    },
                },
                headers={"X-Process-Time": str(round(process_time, 4))},
            )
