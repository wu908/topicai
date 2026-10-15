"""HTTP adapters for cross-project creator rules."""

from fastapi import APIRouter, Depends, Response

from app.api.deps import get_current_user, get_db
from app.core.database import Database
from app.models.common import ApiResponse
from app.models.v2.creator_rule import (
    RuleCandidateCreate,
    RuleCandidateDecision,
    RuleConflictResolutionCreate,
    RuleRollback,
)
from app.services.creator_rule import CreatorRuleService

router = APIRouter(tags=["Creator rules v2"])


def _response(response: Response, result, replayed: bool):
    response.status_code = 200 if replayed else 201
    return ApiResponse(code=response.status_code, data=result, meta={"idempotency_replayed": replayed})


@router.get("/creator-rules")
async def list_creator_rules(user=Depends(get_current_user), db: Database = Depends(get_db)):
    return ApiResponse(data={"items": await CreatorRuleService(db).list(user["id"])})


@router.post("/observations/{observation_id}/rule-candidates", status_code=201)
async def propose_rule_candidate(
    observation_id: str,
    body: RuleCandidateCreate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await CreatorRuleService(db).propose(user["id"], observation_id, body)
    return _response(response, result, replayed)


@router.post("/creator-rule-versions/{version_id}:decide", status_code=201)
async def decide_rule_candidate(
    version_id: str,
    body: RuleCandidateDecision,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await CreatorRuleService(db).decide(user["id"], version_id, body)
    return _response(response, result, replayed)


@router.post("/creator-rules/{rule_id}:rollback", status_code=201)
async def rollback_creator_rule(
    rule_id: str,
    body: RuleRollback,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await CreatorRuleService(db).rollback(user["id"], rule_id, body)
    return _response(response, result, replayed)


@router.post("/creator-rules/{rule_id}/conflicts/{conflict_rule_id}:resolve", status_code=201)
async def resolve_creator_rule_conflict(
    rule_id: str,
    conflict_rule_id: str,
    body: RuleConflictResolutionCreate,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await CreatorRuleService(db).resolve_conflict(
        user["id"], rule_id, conflict_rule_id, body
    )
    return _response(response, result, replayed)


@router.get("/creator-rules/{rule_id}/replay")
async def replay_creator_rule(
    rule_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """规则变更回放对比（P4-B2）：按版本时间线给出「哪里变了」。

    只回放历史，不改规则、不预测效果。
    """
    rules = await CreatorRuleService(db).list(user["id"])
    target = next((r for r in rules if r.get("id") == rule_id), None)
    if target is None:
        raise ValueError("creator rule not found")
    versions = list(target.get("versions") or [])
    # 时间线：旧 → 新
    timeline = list(reversed(versions))
    steps = []
    prev = None
    for v in timeline:
        step = {
            "version_id": v.get("id"),
            "version_number": v.get("version_number"),
            "statement": v.get("statement", ""),
            "scope": v.get("scope") or {},
            "status": v.get("status", ""),
            "created_at": v.get("created_at", ""),
            "changed_fields": [],
        }
        if prev is not None:
            if (prev.get("statement") or "") != (v.get("statement") or ""):
                step["changed_fields"].append("statement")
            if (prev.get("scope") or {}) != (v.get("scope") or {}):
                step["changed_fields"].append("scope")
            if (prev.get("status") or "") != (v.get("status") or ""):
                step["changed_fields"].append("status")
        steps.append(step)
        prev = v
    return ApiResponse(
        data={
            "rule_id": rule_id,
            "steps": steps,
            "active_version_id": (target.get("active_version") or {}).get("id"),
        }
    )
