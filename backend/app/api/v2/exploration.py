"""探索位 / 落选归因（P3-B4）—— 诚实记录实验，不预测结果。"""

import json

from fastapi import APIRouter, Depends
from pydantic import Field
from sqlalchemy import text

from app.api.deps import get_current_user, get_db
from app.core.database import Database
from app.core.exceptions import VersionConflictException
from app.models.common import ApiResponse
from app.models.v2.intent_actions import StrictModel

_KEY = "exploration_slots"


class ExplorationSlotCreate(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    hypothesis: str = Field(default="", max_length=500)
    expected_version: int = Field(ge=1)


class ExplorationSlotDecide(StrictModel):
    status: str = Field(pattern="^(adopted|rejected|running)$")
    attribution: str = Field(default="", max_length=500)
    expected_version: int = Field(ge=1)


class ExplorationSlotView(StrictModel):
    id: str
    title: str
    hypothesis: str = ""
    status: str = "running"
    attribution: str = ""


class ExplorationListView(StrictModel):
    items: list[ExplorationSlotView] = []
    version: int = Field(ge=1)


router = APIRouter(prefix="/exploration-slots", tags=["Exploration slot v2"])


async def _load(db: Database, owner: str) -> tuple[list[dict], int]:
    row = await db.fetch_one(
        "SELECT consent_json, settings_version FROM users WHERE id=:owner",
        {"owner": owner},
    )
    if row is None:
        raise ValueError("owner not found")
    consent = json.loads(row["consent_json"] or "{}")
    return list(consent.get(_KEY) or []), int(row["settings_version"])


async def _save(db: Database, owner: str, slots: list[dict], expected: int) -> int:
    row = await db.fetch_one(
        "SELECT consent_json FROM users WHERE id=:owner",
        {"owner": owner},
    )
    consent = json.loads(row["consent_json"] or "{}")
    consent[_KEY] = slots
    session = await db.get_session()
    async with session:
        async with session.begin():
            result = await session.execute(
                text(
                    "UPDATE users SET consent_json=:consent,"
                    "settings_version=settings_version+1 "
                    "WHERE id=:owner AND settings_version=:expected"
                ),
                {
                    "consent": json.dumps(consent, ensure_ascii=False),
                    "owner": owner,
                    "expected": expected,
                },
            )
            if result.rowcount != 1:
                _, fresh = await _load(db, owner)
                raise VersionConflictException(fresh, expected)
    _, version = await _load(db, owner)
    return version


@router.get("", response_model=ApiResponse[ExplorationListView])
async def list_slots(user=Depends(get_current_user), db: Database = Depends(get_db)):
    slots, version = await _load(db, user["id"])
    return ApiResponse(data={"items": slots, "version": version})


@router.post("", status_code=201, response_model=ApiResponse[ExplorationListView])
async def create_slot(
    body: ExplorationSlotCreate,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    slots, version = await _load(db, user["id"])
    if version != body.expected_version:
        raise VersionConflictException(version, body.expected_version)
    slot = {
        "id": f"exp-{len(slots) + 1}-{body.expected_version}",
        "title": body.title,
        "hypothesis": body.hypothesis,
        "status": "running",
        "attribution": "",
    }
    slots.append(slot)
    new_version = await _save(db, user["id"], slots, body.expected_version)
    return ApiResponse(data={"items": slots, "version": new_version})


@router.post("/{slot_id}:decide", response_model=ApiResponse[ExplorationListView])
async def decide_slot(
    slot_id: str,
    body: ExplorationSlotDecide,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    slots, version = await _load(db, user["id"])
    if version != body.expected_version:
        raise VersionConflictException(version, body.expected_version)
    found = False
    for s in slots:
        if s.get("id") == slot_id:
            s["status"] = body.status
            s["attribution"] = body.attribution
            found = True
            break
    if not found:
        raise ValueError("exploration slot not found")
    new_version = await _save(db, user["id"], slots, body.expected_version)
    return ApiResponse(data={"items": slots, "version": new_version})
