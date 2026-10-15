"""Path profile（路径画像）— 存 consent JSON，additive、无迁移。

P3-B1：AI 修订提案走 `:propose-revision`，只提议；写入仍由用户 PUT 确认。
"""

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import Field
from sqlalchemy import text

from app.api.deps import get_current_user, get_db
from app.core.database import Database
from app.core.exceptions import VersionConflictException
from app.core.llm import LLMClient, wrap_user_input
from app.models.common import ApiResponse
from app.models.v2.intent_actions import StrictModel

logger = logging.getLogger(__name__)

_PROPOSAL_SYSTEM_PROMPT = (
    "你是路径画像修订顾问。根据用户现有画像，给出更具体的修订提案。\n"
    "硬规则：\n"
    "1. 不得编造用户的经历、身份、数据；只能基于现有画像字段改写或细化。\n"
    "2. 只输出 JSON，不要解释。JSON 形如：\n"
    '{"statement": "...", "publish_focus": "...", "avoid": "...", "cadence": "...", "tone": "...", "reason": "..."}\n'
    "3. 只给有改进的字段；没把握的字段留空字符串。\n"
    "4. reason 用一句话说明为什么这样改。\n"
)


class PathProfilePayload(StrictModel):
    statement: str | None = Field(default=None, max_length=500)
    publish_focus: str | None = Field(default=None, max_length=500)
    avoid: str | None = Field(default=None, max_length=500)
    cadence: str | None = Field(default=None, max_length=120)
    tone: str | None = Field(default=None, max_length=200)
    expected_version: int = Field(ge=1)


class PathProfileView(StrictModel):
    statement: str = ""
    publish_focus: str = ""
    avoid: str = ""
    cadence: str = ""
    tone: str = ""
    version: int = Field(ge=1)


class PathRevisionProposal(StrictModel):
    field: str
    current: str = ""
    proposed: str
    reason: str = ""


class PathRevisionView(StrictModel):
    proposals: list[PathRevisionProposal] = []
    reason: str = ""


_FIELDS = ("statement", "publish_focus", "avoid", "cadence", "tone")


def _parse_proposals(raw: str, profile: dict[str, Any]) -> tuple[list[dict], str]:
    """把 LLM JSON 解析成提案列表；解析失败返回空。"""
    text_out = (raw or "").strip()
    if not text_out:
        return [], ""
    # 剥掉可能的 ```json 壳
    if text_out.startswith("```"):
        text_out = text_out.strip("`")
        if text_out.lower().startswith("json"):
            text_out = text_out[4:]
    try:
        data = json.loads(text_out)
    except json.JSONDecodeError:
        logger.warning("path-profile proposal parse failed")
        return [], ""
    if not isinstance(data, dict):
        return [], ""
    reason = str(data.get("reason") or "")
    proposals: list[dict] = []
    for key in _FIELDS:
        proposed = (data.get(key) or "").strip()
        if not proposed:
            continue
        current = (profile.get(key) or "").strip()
        if proposed == current:
            continue
        proposals.append(
            {"field": key, "current": current, "proposed": proposed, "reason": reason}
        )
    return proposals, reason


router = APIRouter(prefix="/path-profile", tags=["Path profile v2"])

_PATH_KEY = "path_profile"


async def _load(db: Database, owner: str) -> tuple[dict, int]:
    row = await db.fetch_one(
        "SELECT consent_json, settings_version FROM users WHERE id=:owner",
        {"owner": owner},
    )
    if row is None:
        raise ValueError("owner not found")
    consent = json.loads(row["consent_json"] or "{}")
    return consent, int(row["settings_version"])


def _view(consent: dict, version: int) -> dict:
    profile = consent.get(_PATH_KEY) or {}
    return PathProfileView.model_validate(
        {
            "statement": profile.get("statement") or "",
            "publish_focus": profile.get("publish_focus") or "",
            "avoid": profile.get("avoid") or "",
            "cadence": profile.get("cadence") or "",
            "tone": profile.get("tone") or "",
            "version": version,
        }
    ).model_dump(mode="json")


@router.get("", response_model=ApiResponse[PathProfileView])
async def get_path_profile(user=Depends(get_current_user), db: Database = Depends(get_db)):
    consent, version = await _load(db, user["id"])
    return ApiResponse(data=_view(consent, version))


@router.put("", response_model=ApiResponse[PathProfileView])
async def update_path_profile(
    body: PathProfilePayload,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    consent, version = await _load(db, user["id"])
    if version != body.expected_version:
        raise VersionConflictException(version, body.expected_version)
    profile = dict(consent.get(_PATH_KEY) or {})
    for key in ("statement", "publish_focus", "avoid", "cadence", "tone"):
        value = getattr(body, key)
        if value is not None:
            profile[key] = value
    consent[_PATH_KEY] = profile
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
                    "owner": user["id"],
                    "expected": body.expected_version,
                },
            )
            if result.rowcount != 1:
                _, fresh = await _load(db, user["id"])
                raise VersionConflictException(fresh, body.expected_version)
    consent2, version2 = await _load(db, user["id"])
    return ApiResponse(data=_view(consent2, version2))


@router.post(
    ":propose-revision",
    response_model=ApiResponse[PathRevisionView],
)
async def propose_revision(
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """AI 修订提案（P3-B1）。只提议不落库；写入仍由用户 PUT。无模型/失败 → 空提案。"""
    consent, _version = await _load(db, user["id"])
    profile = dict(consent.get(_PATH_KEY) or {})
    current_text = json.dumps(
        {k: (profile.get(k) or "") for k in _FIELDS},
        ensure_ascii=False,
    )
    llm = LLMClient()
    if not getattr(llm, "is_available", lambda _c="text": True)("text"):
        return ApiResponse(data={"proposals": [], "reason": ""})
    try:
        raw = llm.generate(
            wrap_user_input(current_text),
            system_prompt=_PROPOSAL_SYSTEM_PROMPT,
            temperature=0.4,
            max_tokens=500,
        )
    except Exception:  # noqa: BLE001
        logger.warning("path-profile propose-revision failed", exc_info=True)
        return ApiResponse(data={"proposals": [], "reason": ""})
    proposals, reason = _parse_proposals(raw or "", profile)
    return ApiResponse(data={"proposals": proposals, "reason": reason})
