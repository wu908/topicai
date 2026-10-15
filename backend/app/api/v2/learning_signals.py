"""learning_signals 采集（P4-B1）—— 决策/diff/对账/跳过，append-only。"""

import json
from datetime import UTC

from fastapi import APIRouter, Depends
from pydantic import Field
from sqlalchemy import text

from app.api.deps import get_current_user, get_db
from app.core.database import Database
from app.models.common import ApiResponse
from app.models.v2.intent_actions import StrictModel

_KEY = "learning_signals"
#: 单用户信号上限，防 consent JSON 无限膨胀
_MAX_SIGNALS = 200

SIGNAL_KINDS = ("decision", "diff", "retro", "skip")


class LearningSignalCreate(StrictModel):
    kind: str = Field(pattern="^(decision|diff|retro|skip)$")
    ref: str = Field(default="", max_length=200)
    summary: str = Field(min_length=1, max_length=300)
    payload: dict = Field(default_factory=dict)


class LearningSignalView(StrictModel):
    id: str
    kind: str
    ref: str = ""
    summary: str
    created_at: str


def _to_view(s: dict) -> dict:
    return {
        "id": s.get("id", ""),
        "kind": s.get("kind", ""),
        "ref": s.get("ref", ""),
        "summary": s.get("summary", ""),
        "created_at": s.get("created_at", ""),
    }


class LearningSignalList(StrictModel):
    items: list[LearningSignalView] = []
    total: int = 0


router = APIRouter(prefix="/learning-signals", tags=["Learning signals v2"])


async def _load(db: Database, owner: str) -> list[dict]:
    row = await db.fetch_one(
        "SELECT consent_json FROM users WHERE id=:owner",
        {"owner": owner},
    )
    if row is None:
        raise ValueError("owner not found")
    consent = json.loads(row["consent_json"] or "{}")
    return list(consent.get(_KEY) or [])


async def _append(db: Database, owner: str, signal: dict) -> list[dict]:
    row = await db.fetch_one(
        "SELECT consent_json, settings_version FROM users WHERE id=:owner",
        {"owner": owner},
    )
    consent = json.loads(row["consent_json"] or "{}")
    signals = list(consent.get(_KEY) or [])
    signals.append(signal)
    # 只保留最近 N 条
    if len(signals) > _MAX_SIGNALS:
        signals = signals[-_MAX_SIGNALS:]
    consent[_KEY] = signals
    session = await db.get_session()
    async with session:
        async with session.begin():
            await session.execute(
                text(
                    "UPDATE users SET consent_json=:consent,"
                    "settings_version=settings_version+1 WHERE id=:owner"
                ),
                {"consent": json.dumps(consent, ensure_ascii=False), "owner": owner},
            )
    return signals


@router.get("", response_model=ApiResponse[LearningSignalList])
async def list_signals(
    kind: str | None = None,
    limit: int = 50,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    signals = await _load(db, user["id"])
    if kind:
        signals = [s for s in signals if s.get("kind") == kind]
    signals = list(reversed(signals))[-limit:]
    return ApiResponse(
        data={"items": [_to_view(s) for s in signals], "total": len(signals)},
    )


@router.post("", status_code=201, response_model=ApiResponse[LearningSignalList])
async def create_signal(
    body: LearningSignalCreate,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """记录一条学习信号。append-only，不改历史。"""
    from datetime import datetime

    signal = {
        "id": f"ls-{int(datetime.now(UTC).timestamp() * 1000)}",
        "kind": body.kind,
        "ref": body.ref,
        "summary": body.summary,
        "payload": body.payload,
        "created_at": datetime.now(UTC).isoformat(),
    }
    signals = await _append(db, user["id"], signal)
    return ApiResponse(
        code=201,
        data={
            "items": [_to_view(s) for s in list(reversed(signals))[-50:]],
            "total": len(signals),
        },
    )
