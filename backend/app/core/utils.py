"""Shared utility functions for TopicAI v4.0.

Centralizes commonly repeated helper functions across the application.
"""

from datetime import UTC, datetime


def utc_now() -> str:
    """Return current UTC time as ISO 8601 string with 'Z' suffix.

    Returns:
        ISO 8601 formatted UTC timestamp string (e.g. "2026-05-26T12:00:00Z").
    """
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
