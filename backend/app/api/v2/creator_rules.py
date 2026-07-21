"""HTTP adapters for cross-project creator rules."""

from fastapi import APIRouter, Depends, Response

from app.api.v1.deps import get_current_user, get_db
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
