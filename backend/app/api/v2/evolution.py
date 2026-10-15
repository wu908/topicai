"""P4：进化可见区 —— 「哪里变了」汇总（学习信号 / 规则变更 / 能力信任）。"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_db
from app.core.database import Database
from app.models.common import ApiResponse
from app.models.v2.intent_actions import StrictModel
from app.services.creator_rule import CreatorRuleService
from app.services.creator_state import CreatorStateService


class EvolutionChange(StrictModel):
    kind: str
    summary: str
    at: str = ""


class EvolutionSummary(StrictModel):
    changes: list[EvolutionChange] = []
    capability_trust: dict[str, int] = {}
    recent_signals: list[dict] = []


router = APIRouter(prefix="/evolution", tags=["Evolution v2"])


@router.get("/summary", response_model=ApiResponse[EvolutionSummary])
async def evolution_summary(
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """进化可见区（P4-F1）：最近「哪里变了」。只读，不预测。"""
    import json

    # 学习信号
    row = await db.fetch_one(
        "SELECT consent_json FROM users WHERE id=:owner",
        {"owner": user["id"]},
    )
    consent = json.loads(row["consent_json"] or "{}") if row else {}
    signals = list(consent.get("learning_signals") or [])[-10:]
    changes: list[dict] = []
    for s in reversed(signals):
        changes.append(
            {
                "kind": s.get("kind", "signal"),
                "summary": s.get("summary", ""),
                "at": s.get("created_at", ""),
            }
        )

    # 规则变更（最近版本）
    try:
        rules = await CreatorRuleService(db).list(user["id"])
        for rule in rules[:5]:
            versions = rule.get("versions") or []
            if not versions:
                continue
            latest = versions[0]
            changes.append(
                {
                    "kind": "rule",
                    "summary": f"规则变更：{latest.get('statement', '')[:60]}",
                    "at": latest.get("created_at", ""),
                }
            )
    except Exception:  # noqa: BLE001
        pass

    # 能力信任
    try:
        state = await CreatorStateService(db).get(user["id"])
        trust = state.get("capability_trust") or {}
    except Exception:  # noqa: BLE001
        trust = {}

    # 按时间粗排：有 at 的在前
    changes.sort(key=lambda c: c.get("at") or "", reverse=True)
    return ApiResponse(
        data={
            "changes": changes[:20],
            "capability_trust": trust,
            "recent_signals": signals,
        }
    )
