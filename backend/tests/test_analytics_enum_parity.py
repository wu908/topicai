"""Cross-language enum parity for analytics payload keys.

The backend validates ``action_key`` / ``next_action`` against its own enums,
while the frontend mirrors the same unions in TypeScript. If the frontend adds
a member and the backend is not updated, the event is silently ``rejected``
(data loss without an error). This test fails on drift.
"""

import re
from pathlib import Path

from app.models.v2.analytics import NextAction
from app.models.v2.intent_actions import ActionType

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_FILE = REPO_ROOT / "frontend/src/types/contracts/v2/content.ts"


def parse_union(source: str, type_name: str) -> set[str]:
    """Extract the string members of ``export type <name> = 'a' | 'b';``."""
    pattern = rf"export type {re.escape(type_name)}\s*=\s*(?P<body>.*?);"
    match = re.search(pattern, source, re.S)
    if match is None:
        raise AssertionError(f"union {type_name} not found in contract source")
    return set(re.findall(r"'([a-z_]+)'", match.group("body")))


def test_frontend_contract_file_exists() -> None:
    assert (REPO_ROOT / "backend").is_dir()
    assert CONTRACT_FILE.is_file(), f"missing frontend contract: {CONTRACT_FILE}"


def test_intent_action_type_matches_backend() -> None:
    source = CONTRACT_FILE.read_text(encoding="utf-8")
    frontend = parse_union(source, "IntentActionType")
    backend = {item.value for item in ActionType}
    assert frontend == backend, (
        f"IntentActionType drift: backend-only={backend - frontend}, "
        f"frontend-only={frontend - backend}"
    )


def test_next_action_matches_backend() -> None:
    source = CONTRACT_FILE.read_text(encoding="utf-8")
    frontend = parse_union(source, "NextAction")
    backend = {item.value for item in NextAction}
    assert frontend == backend, (
        f"NextAction drift: backend-only={backend - frontend}, "
        f"frontend-only={frontend - backend}"
    )


def test_parser_detects_missing_member() -> None:
    """Mutation check: the parser is not vacuously true."""
    sample = "export type NextAction =\n  | 'create_version'\n  | 'lock_hypothesis';\n"
    assert parse_union(sample, "NextAction") == {"create_version", "lock_hypothesis"}
    mutated = sample.replace("  | 'lock_hypothesis'", "")
    assert parse_union(mutated, "NextAction") != {
        "create_version",
        "lock_hypothesis",
    }
