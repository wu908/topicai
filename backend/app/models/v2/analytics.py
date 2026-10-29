"""Pydantic contracts for first-party analytics ingest and summary.

The request body is parsed by hand in ``app/api/v2/analytics.py`` (the
endpoint deliberately does NOT declare a Pydantic body, so auth/switch/size
checks keep their contract precedence); these models are the typed shape the
handler validates against after those checks.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NextAction(StrEnum):
    """Stable next-action keys mirrored from the v2 content contract.

    ``action_key`` for ``content_list_action_click`` stores one of these
    keys (or ``view`` / ``handle`` / ``orchestrated:<ActionType>``) so a UX
    copy change can never break historical comparability.
    """

    CREATE_VERSION = "create_version"
    LOCK_HYPOTHESIS = "lock_hypothesis"
    RECORD_PUBLICATION = "record_publication"
    AWAIT_OBSERVATION_WINDOW = "await_observation_window"
    ADD_SNAPSHOT = "add_snapshot"
    RUN_BLIND_REVIEW = "run_blind_review"
    CREATE_OBSERVATION = "create_observation"
    MANAGE_OBSERVATIONS = "manage_observations"
    ADD_COMPARABLE_SNAPSHOT = "add_comparable_snapshot"
    REVIEW_CALIBRATION_ISSUE = "review_calibration_issue"


class AnalyticsEventIn(BaseModel):
    """One raw event from the batch. Item-level semantics are validated in
    the service so a bad item returns 200 + ``rejected[]`` instead of
    failing the whole batch."""

    model_config = ConfigDict(extra="forbid")

    event: str
    payload: dict[str, Any] = Field(default_factory=dict)
    client_ts: str
    idem_key: str


class AnalyticsEventsRequest(BaseModel):
    """Batch envelope: 1–32 events per request."""

    model_config = ConfigDict(extra="forbid")

    events: list[AnalyticsEventIn] = Field(min_length=1, max_length=32)


class RejectedEvent(BaseModel):
    index: int
    reason: str


class AnalyticsIngestResult(BaseModel):
    """200 ``data`` for POST /analytics/events.

    ``accepted`` and ``duplicates`` are mutually exclusive per event; the
    quota path (429) never returns this payload.
    """

    accepted: int = 0
    duplicates: int = 0
    rejected: list[RejectedEvent] = Field(default_factory=list)


class AnalyticsSummaryItem(BaseModel):
    event: str
    date: str
    count: int


class AnalyticsSummary(BaseModel):
    items: list[AnalyticsSummaryItem] = Field(default_factory=list)
