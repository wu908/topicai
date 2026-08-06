"""Application exceptions and FastAPI error envelopes."""

from typing import TYPE_CHECKING

from app.core.utils import utc_now

if TYPE_CHECKING:
    from fastapi import FastAPI


class AppException(Exception):
    def __init__(
        self,
        message: str = "An application error occurred",
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class LLMException(AppException):
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
    def __init__(self, provider: str | None = None, timeout_seconds: float | None = None):
        super().__init__("LLM request timed out", 504, "LLM_TIMEOUT", provider)
        self.timeout_seconds = timeout_seconds


class LLMStructuredOutputException(LLMException):
    def __init__(
        self,
        message: str = "LLM failed to produce valid structured output",
        provider: str | None = None,
        retries: int = 0,
    ):
        super().__init__(message, 502, "LLM_STRUCTURED_OUTPUT_FAILURE", provider)
        self.retries = retries


class AINotConfiguredException(LLMException):
    def __init__(self):
        super().__init__(
            "AI is not configured; continue with the manual path",
            503,
            "AI_NOT_CONFIGURED",
            "openai_compatible",
        )


class AICapabilityMissingException(LLMException):
    def __init__(self, capability: str):
        super().__init__(
            f"AI capability is not available: {capability}",
            422,
            "AI_CAPABILITY_MISSING",
            "openai_compatible",
        )
        self.capability = capability


class AuthenticationException(AppException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401, "AUTHENTICATION_FAILED")


class UserAlreadyExistsException(AppException):
    def __init__(self, message: str = "User already exists"):
        super().__init__(message, 409, "USER_ALREADY_EXISTS")


class TokenExpiredException(AppException):
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, 401, "TOKEN_EXPIRED")


class InvalidTokenException(AppException):
    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, 401, "INVALID_TOKEN")


class RateLimitException(AppException):
    def __init__(
        self,
        message: str = "请求过于频繁，请稍后再试",
        error_code: str = "RATE_LIMIT_EXCEEDED",
        reset_at: str | None = None,
    ):
        super().__init__(message, 429, error_code)
        self.reset_at = reset_at


class SourceExpiredException(AppException):
    def __init__(self):
        super().__init__(
            "expired source requires explicit confirmation before accepting this opportunity",
            400,
            "SOURCE_EXPIRED",
        )


class VersionConflictException(AppException):
    def __init__(self, current_version: int, expected_version: int):
        super().__init__("Project changed since you opened it", 409, "VERSION_CONFLICT")
        self.current_version = current_version
        self.expected_version = expected_version


class IdempotencyConflictException(AppException):
    def __init__(self):
        super().__init__(
            "Idempotency key was already used for a different request",
            409,
            "IDEMPOTENCY_CONFLICT",
        )


class MaterialInUseException(AppException):
    def __init__(self, details: dict):
        super().__init__(
            "Material is referenced by one or more projects",
            409,
            "MATERIAL_IN_USE",
        )
        self.details = details


class PublishCheckBlockedException(AppException):
    def __init__(self, check: dict):
        stale = bool(check.get("stale"))
        super().__init__(
            "Publish check is stale" if stale else "Publish check findings require a decision",
            409,
            "PUBLISH_CHECK_STALE" if stale else "PUBLISH_CHECK_UNRESOLVED",
        )
        self.details = {
            "publish_check_id": check.get("id"),
            "status": check.get("status"),
            "open_finding_ids": [
                item["id"]
                for item in check.get("findings", [])
                if item.get("status") == "open"
            ],
        }


def setup_exception_handlers(app: "FastAPI") -> None:
    from fastapi import Request
    from fastapi.encoders import jsonable_encoder
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        from config.settings import get_settings

        meta = {"error_code": "VALIDATION_ERROR", "timestamp": utc_now()}
        if not get_settings().is_production:
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
    async def application_handler(request: Request, exc: AppException):
        meta = {"error_code": exc.error_code, "timestamp": utc_now()}
        if isinstance(exc, VersionConflictException):
            meta["details"] = {
                "current_version": exc.current_version,
                "expected_version": exc.expected_version,
            }
        elif hasattr(exc, "details"):
            meta["details"] = exc.details
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
        message = str(exc)
        lowered = message.lower()
        if "not found" in lowered:
            status = 404
        elif any(value in lowered for value in ("already exists", "not owned", "last admin")):
            status = 422
        else:
            status = 400
        return JSONResponse(
            status_code=status,
            content={
                "code": status,
                "data": None,
                "message": message,
                "meta": {"timestamp": utc_now()},
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        from config.settings import get_settings

        message = (
            "服务器内部错误，请稍后重试"
            if get_settings().is_production
            else f"Internal error: {exc}"
        )
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "data": None,
                "message": message,
                "meta": {"error_code": "INTERNAL_ERROR", "timestamp": utc_now()},
            },
        )
