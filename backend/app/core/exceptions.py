"""Application exceptions and FastAPI error envelopes."""

import logging
from typing import TYPE_CHECKING

from app.core.utils import utc_now

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RequestValidationError → user-facing message mapping.
#
# Audit 2026-09-13: production used to return a bare "请求参数校验失败" with
# no field guidance — e.g. a reserved-domain email was indistinguishable
# from every other 422. The mapped message is built ONLY from code-defined
# field names (loc tail) and pydantic's error-type enum; never from
# `msg`/`input`/`ctx`, so no user data or library internals can leak into
# the client-facing text. Unknown fields keep the generic message.
# ---------------------------------------------------------------------------

_VALIDATION_FIELD_LABELS = {
    "email": "邮箱",
    "username": "姓名",
    "password": "密码",
    "refresh_token": "登录凭证",
}

_VALIDATION_GENERIC_MESSAGE = "请求参数校验失败"


def _validation_user_message(errors: list[dict]) -> str:
    for err in errors:
        loc = err.get("loc") or []
        field = str(loc[-1]) if loc else ""
        etype = str(err.get("type", ""))
        label = _VALIDATION_FIELD_LABELS.get(field, "")
        if field == "email" and etype.startswith("value_error"):
            return "邮箱格式不正确，请检查后重试"
        if etype == "missing" and label:
            return f"缺少必填项：{label}"
        if etype == "string_too_short" and label:
            return f"{label}长度不足，请检查后重试"
        if label:
            return f"{label}格式不正确，请检查后重试"
    return _VALIDATION_GENERIC_MESSAGE


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


class UserActionRequiredException(AppException):
    """A domain refusal the user is expected to act on.

    Bare ValueErrors from services are deliberately replaced with a generic
    message in production (they can carry SQL/paths). Refusals that tell the
    creator *what to do next* must therefore be typed, so their message
    survives the production filter and reaches the client.
    """

    def __init__(self, message: str):
        super().__init__(message, 400, "USER_ACTION_REQUIRED")


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

        errors = jsonable_encoder(exc.errors())
        meta = {"error_code": "VALIDATION_ERROR", "timestamp": utc_now()}
        if not get_settings().is_production:
            meta["errors"] = errors
        # Field-level guidance is derived from code-defined field names and
        # pydantic's type enum only — safe to expose in production (the
        # unsanitized errors array stays dev-only, per D5).
        message = _validation_user_message(errors)
        return JSONResponse(
            status_code=422,
            content={
                "code": 422,
                "data": None,
                "message": message,
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
        from pydantic import ValidationError

        from config.settings import get_settings

        # F25a: ValidationError subclasses ValueError and str(exc) is an
        # English field dump (paths, input values, pydantic URLs). Handle it
        # before the keyword classifier so that dump never becomes the
        # client message — in any environment.
        if isinstance(exc, ValidationError):
            logger.warning("Pydantic ValidationError surfaced to client", exc_info=exc)
            meta: dict = {"error_code": "VALIDATION_ERROR", "timestamp": utc_now()}
            if not get_settings().is_production:
                meta["errors"] = str(exc)
            return JSONResponse(
                status_code=422,
                content={
                    "code": 422,
                    "data": None,
                    "message": "提交的内容没有通过校验，请检查后重试",
                    "meta": meta,
                },
            )

        message = str(exc)
        lowered = message.lower()
        if "not found" in lowered:
            status = 404
        elif any(value in lowered for value in ("already exists", "not owned", "last admin")):
            status = 422
        else:
            status = 400
        # Keyword-classified messages are deliberate domain signals and part
        # of the API contract; anything else may originate deep inside a
        # third-party library (paths, SQL fragments, field values) and must
        # not be echoed to clients — in any environment (F25a defense-in-depth).
        meta = {"timestamp": utc_now()}
        if status == 400:
            logger.warning("Unhandled ValueError surfaced to client", exc_info=exc)
            if not get_settings().is_production:
                meta["errors"] = message
            message = "请求参数无效"
        return JSONResponse(
            status_code=status,
            content={
                "code": status,
                "data": None,
                "message": message,
                "meta": meta,
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
