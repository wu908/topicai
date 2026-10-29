"""Owner-scoped first-party analytics endpoints.

Status precedence for ``POST /analytics/events`` is fixed by the contract and
must not be reordered or moved into middleware:

1. 401 — ``get_current_user`` (dependency phase, before the body is read)
2. 503 — ingest switch off (handler, before the body is read)
3. 413 — body larger than 48 KB (Content-Length or a bounded stream read)
4. 422 — structure/type/owner-field errors
5. 200 — valid items stored; per-item failures returned as ``rejected[]``
6. 429 — daily quota exceeded (whole batch rejected, no writes)
"""

import json
import logging
import re
import time
from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from pydantic import ValidationError

from app.api.deps import get_current_user, get_db
from app.core.database import Database
from app.core.exceptions import AppException
from app.models.common import ApiResponse
from app.models.v2.analytics import (
    AnalyticsEventIn,
    AnalyticsEventsRequest,
    AnalyticsIngestResult,
    AnalyticsSummary,
)
from app.services.analytics import (
    EVENT_NAMES,
    MAX_BODY_BYTES,
    MAX_SUMMARY_DAYS,
    AnalyticsService,
)
from config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics v2"])

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _error(message: str, status_code: int, error_code: str) -> AppException:
    return AppException(message, status_code, error_code)


def _payload_too_large() -> AppException:
    return _error("请求体过大", 413, "PAYLOAD_TOO_LARGE")


def _validation_error(message: str) -> AppException:
    return _error(message, 422, "VALIDATION_ERROR")


def _contains_owner_field(value: object) -> bool:
    """True when any JSON object key in the body starts with ``owner``."""
    if isinstance(value, dict):
        if any(str(key).lower().startswith("owner") for key in value):
            return True
        return any(_contains_owner_field(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_owner_field(item) for item in value)
    return False


async def _read_body_within_limit(request: Request) -> bytes:
    """Read the body with a hard 48 KB ceiling.

    The declared Content-Length is checked first (handler-side, after the
    503 switch check), then the stream is read chunk-by-chunk so a missing or
    lying header can never turn into an unbounded read.
    """
    declared = request.headers.get("content-length")
    if declared is not None:
        try:
            declared_length = int(declared)
        except ValueError:
            raise _validation_error("Content-Length 非法") from None
        if declared_length > MAX_BODY_BYTES:
            raise _payload_too_large()
    body = bytearray()
    async for chunk in request.stream():
        if not chunk:
            continue
        body.extend(chunk)
        if len(body) > MAX_BODY_BYTES:
            raise _payload_too_large()
    return bytes(body)


def _parse_events(raw: bytes) -> list[AnalyticsEventIn]:
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise _validation_error("请求体必须是合法 JSON") from None
    if not isinstance(document, dict):
        raise _validation_error("请求体必须是 JSON 对象")
    if _contains_owner_field(document):
        raise _error("请求体不得包含 owner* 字段", 422, "OWNER_NOT_ALLOWED")
    try:
        parsed = AnalyticsEventsRequest.model_validate(document)
    except ValidationError:
        raise _validation_error(
            "events 必须为 1–32 条且字段类型正确"
        ) from None
    return parsed.events


@router.post("/events", response_model=ApiResponse[AnalyticsIngestResult])
async def ingest_events(
    request: Request,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    started = time.perf_counter()
    if not get_settings().analytics_ingest_enabled:
        raise _error("Analytics ingest is disabled", 503, "ANALYTICS_DISABLED")

    raw = await _read_body_within_limit(request)
    events = _parse_events(raw)
    result = await AnalyticsService(db).ingest(user["id"], events)
    logger.info(
        "analytics_ingest accepted=%d duplicates=%d rejected=%d duration_ms=%.1f",
        result["accepted"],
        result["duplicates"],
        len(result["rejected"]),
        (time.perf_counter() - started) * 1000,
    )
    return ApiResponse(data=AnalyticsIngestResult.model_validate(result))


def _parse_day(value: str, field: str) -> date:
    if not isinstance(value, str) or not _DATE_PATTERN.match(value):
        raise _validation_error(f"{field} 必须是 YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise _validation_error(f"{field} 必须是 YYYY-MM-DD") from None


@router.get("/summary", response_model=ApiResponse[AnalyticsSummary])
async def analytics_summary(
    from_: str = Query(alias="from"),
    to: str = Query(),
    event: str | None = Query(default=None),
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    start = _parse_day(from_, "from")
    end = _parse_day(to, "to")
    if start > end:
        raise _validation_error("from 不得晚于 to")
    if (end - start).days + 1 > MAX_SUMMARY_DAYS:
        raise _validation_error("summary 窗口不得超过 90 天")
    if event is not None and event not in EVENT_NAMES:
        raise _validation_error("event 不在允许的事件集合内")

    items = await AnalyticsService(db).summary(
        user["id"], start.isoformat(), end.isoformat(), event
    )
    return ApiResponse(data=AnalyticsSummary.model_validate({"items": items}))
