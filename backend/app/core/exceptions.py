"""Custom exception hierarchy for TopicAI v4.0.

Provides typed exceptions for different error categories to enable
appropriate error handling and user-facing messages.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.utils import utc_now

if TYPE_CHECKING:
    from fastapi import FastAPI


class AppException(Exception):
    """Base application exception.

    All application-specific exceptions should inherit from this class.

    Attributes:
        message: Human-readable error message.
        status_code: HTTP status code for API responses.
        error_code: Machine-readable error code.
    """

    def __init__(
        self,
        message: str = "An application error occurred",
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)

# ==================== LLM Exceptions ====================

class LLMException(AppException):
    """Base exception for LLM-related errors.

    User-facing message: "AI思考中，请稍后重试"
    """

    def __init__(
        self,
        message: str = "LLM service error",
        status_code: int = 503,
        error_code: str = "LLM_ERROR",
        provider: str | None = None,
        model_version: str | None = None,
    ):
        super().__init__(message, status_code, error_code)
        self.provider = provider
        self.model_version = model_version

class LLMTimeoutException(LLMException):
    """LLM request timed out."""

    def __init__(
        self,
        message: str = "LLM request timed out",
        provider: str | None = None,
        timeout_seconds: float | None = None,
    ):
        super().__init__(
            message=message,
            status_code=504,
            error_code="LLM_TIMEOUT",
            provider=provider,
        )
        self.timeout_seconds = timeout_seconds

class LLMStructuredOutputException(LLMException):
    """LLM failed to produce valid structured output after retries."""

    def __init__(
        self,
        message: str = "LLM failed to produce valid structured output",
        provider: str | None = None,
        retries: int = 0,
    ):
        super().__init__(
            message=message,
            status_code=502,
            error_code="LLM_STRUCTURED_OUTPUT_FAILURE",
            provider=provider,
        )
        self.retries = retries

class ModalityLimitException(LLMException):
    """GLM-5V-Turbo modality limit violation.

    Only one non-text modality (image/video/file) per request is allowed.
    """

    def __init__(
        self,
        message: str = "Only one non-text modality allowed per request",
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code="MODALITY_LIMIT_EXCEEDED",
            provider="glm",
        )

# ==================== Data Source Exceptions ====================

class DataSourceException(AppException):
    """Base exception for data source errors."""

    def __init__(
        self,
        message: str = "Data source error",
        status_code: int = 502,
        error_code: str = "DATA_SOURCE_ERROR",
        source: str | None = None,
    ):
        super().__init__(message, status_code, error_code)
        self.source = source

class TianAPIError(DataSourceException):
    """TianAPI returned an error response."""

    def __init__(
        self,
        message: str = "TianAPI error",
        api_code: int | None = None,
    ):
        super().__init__(
            message=message,
            status_code=502,
            error_code="TIANAPI_ERROR",
            source="tianapi",
        )
        self.api_code = api_code

class DataSourceUnavailableException(DataSourceException):
    """Data source is completely unavailable."""

    def __init__(
        self,
        message: str = "Data source unavailable",
        source: str | None = None,
    ):
        super().__init__(
            message=message,
            status_code=503,
            error_code="DATA_SOURCE_UNAVAILABLE",
            source=source,
        )

class ImageProcessException(AppException):
    """Image preprocessing or analysis failed."""

    def __init__(
        self,
        message: str = "Image processing failed",
        status_code: int = 400,
        error_code: str = "IMAGE_PROCESS_ERROR",
    ):
        super().__init__(message, status_code, error_code)

# ==================== Authentication Exceptions ====================

class AuthenticationException(AppException):
    """Authentication failed (wrong credentials, etc.)."""

    def __init__(
        self,
        message: str = "Authentication failed",
        status_code: int = 401,
        error_code: str = "AUTHENTICATION_FAILED",
    ):
        super().__init__(message, status_code, error_code)

class UserAlreadyExistsException(AppException):
    """User with the given email or username already exists."""

    def __init__(
        self,
        message: str = "User already exists",
        status_code: int = 409,
        error_code: str = "USER_ALREADY_EXISTS",
    ):
        super().__init__(message, status_code, error_code)

class TokenExpiredException(AppException):
    """JWT token has expired."""

    def __init__(
        self,
        message: str = "Token has expired",
        status_code: int = 401,
        error_code: str = "TOKEN_EXPIRED",
    ):
        super().__init__(message, status_code, error_code)

class InvalidTokenException(AppException):
    """JWT token is invalid (malformed, wrong signature, etc.)."""

    def __init__(
        self,
        message: str = "Invalid token",
        status_code: int = 401,
        error_code: str = "INVALID_TOKEN",
    ):
        super().__init__(message, status_code, error_code)

# ==================== Rate Limit Exceptions ====================

class RateLimitException(AppException):
    """AI call rate limit exceeded."""

    def __init__(
        self,
        message: str = "今日AI调用次数已用完，请明天再试",
        status_code: int = 429,
        error_code: str = "RATE_LIMIT_EXCEEDED",
        reset_at: str | None = None,
    ):
        super().__init__(message, status_code, error_code)
        self.reset_at = reset_at

# ==================== Not Found Exceptions ====================

class NotFoundException(AppException):
    """Resource not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        status_code: int = 404,
        error_code: str = "NOT_FOUND",
        resource_type: str | None = None,
        resource_id: str | None = None,
    ):
        super().__init__(message, status_code, error_code)
        self.resource_type = resource_type
        self.resource_id = resource_id

# ==================== Validation Exception ====================

class ValidationException(AppException):
    """Input validation failed."""

    def __init__(
        self,
        message: str = "Validation failed",
        status_code: int = 422,
        error_code: str = "VALIDATION_ERROR",
        details: dict | None = None,
    ):
        super().__init__(message, status_code, error_code)
        self.details = details or {}


class VersionConflictException(AppException):
    """Optimistic concurrency token no longer matches the aggregate."""

    def __init__(self, current_version: int, expected_version: int):
        super().__init__(
            message="Project changed since you opened it",
            status_code=409,
            error_code="VERSION_CONFLICT",
        )
        self.current_version = current_version
        self.expected_version = expected_version


class IdempotencyConflictException(AppException):
    """An idempotency key was reused for a different request payload."""

    def __init__(self):
        super().__init__(
            message="Idempotency key was already used for a different request",
            status_code=409,
            error_code="IDEMPOTENCY_CONFLICT",
        )

# ==================== Exception Handler Setup ====================

def setup_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI application.

    Args:
        app: The FastAPI application instance.
    """
    from fastapi import Request
    from fastapi.encoders import jsonable_encoder
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request, exc: RequestValidationError
    ):
        """Surface real Pydantic / body-parse errors instead of the generic
        400 'There was an error parsing the body' returned by FastAPI's
        default routing layer.

        Environment-aware sanitization (D5):
        - In production, Pydantic's internal ``errors()`` (field paths
          ``loc``, ``type``, ``ctx``, ``input``) is NOT echoed back to
          the client — that leaks internal schema structure which an
          attacker could use to infer field constraints and types. Only
          ``error_code`` + a generic message are returned.
        - In development, the detailed ``errors`` array is kept so devs
          can debug schema mismatches.
        """
        from config.settings import get_settings

        settings = get_settings()

        meta: dict = {
            "error_code": "VALIDATION_ERROR",
            "timestamp": utc_now(),
        }
        if not settings.is_production:
            meta["errors"] = jsonable_encoder(exc.errors())

        return JSONResponse(
            status_code=422,
            content={
                "code": 422,
                "data": None,
                "message": "请求参数校验失败",
                "meta": meta,
            },
        )

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """Handle all AppException subclasses with appropriate HTTP responses."""
        meta = {
            "error_code": exc.error_code,
            "timestamp": utc_now(),
        }
        if isinstance(exc, VersionConflictException):
            meta["details"] = {
                "current_version": exc.current_version,
                "expected_version": exc.expected_version,
            }

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code,
                "data": None,
                "message": exc.message,
                "meta": meta,
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Service-layer ValueError → HTTP boundary.

        Services raise ValueError with messages like:
          - "Account not found", "Member not found", "Asset not found"
          - "Cannot demote the last admin", "Cannot remove the last admin"
          - "Tags not found or not owned: [...]"
          - "already exists" (duplicate email)

        Translate to 404 for "not found", 422 for business-rule violations
        and duplicates, 400 for malformed input. The message is surfaced
        verbatim so the frontend can display it.
        """
        msg = str(exc)
        msg_l = msg.lower()
        if "not found" in msg_l:
            status_code = 404
        elif "last admin" in msg_l or "already exists" in msg_l or "not owned" in msg_l:
            status_code = 422
        else:
            status_code = 400
        return JSONResponse(
            status_code=status_code,
            content={
                "code": status_code,
                "data": None,
                "message": msg,
                "meta": {"timestamp": utc_now()},
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        """Catch-all for unhandled exceptions.

        In production, returns a generic message. In development,
        includes traceback info.
        """

        from config.settings import get_settings

        settings = get_settings()

        if settings.is_production:
            message = "服务器内部错误，请稍后重试"
        else:
            message = f"Internal error: {str(exc)}"

        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "data": None,
                "message": message,
                "meta": {
                    "error_code": "INTERNAL_ERROR",
                    "timestamp": utc_now(),
                },
            },
        )
