"""HTTP adapters for the intent-driven action loop."""

from fastapi import APIRouter, Depends, Response

from app.api.v1.deps import get_current_user, get_db
from app.core.database import Database
from app.core.llm import LLMClient
from app.models.common import ApiResponse
from app.models.v2.evidence import EvidenceDecision, EvidenceRevocation
from app.models.v2.intent_actions import (
    ActionLifecycleCommand,
    ActionResponse,
    AutomationPreference,
    HumanGateDecision,
    IntentConfirmation,
)
from app.models.v2.publish_hypothesis import RetrospectiveIntentClassification
from app.services.creator_state import CreatorStateService
from app.services.evidence import EvidenceService
from app.services.intent_actions import (
    ActionResponseService,
    AutomationPreferenceService,
    HumanGateService,
    IntentConfirmationService,
)
from app.services.intent_orchestrator import IntentOrchestratorService

router = APIRouter(tags=["Intent orchestration v2"])


def _created_or_replayed(response: Response, result, replayed: bool):
    response.status_code = 200 if replayed else 201
    return ApiResponse(
        code=response.status_code,
        data=result,
        meta={"idempotency_replayed": replayed},
    )


def _optional_llm() -> LLMClient | None:
    try:
        from config.settings import get_settings

        if get_settings().environment != "test":
            return LLMClient()
    except Exception:
        pass
    return None


@router.get("/today")
async def get_today_action(
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    return ApiResponse(data=await IntentOrchestratorService(db).today(user["id"]))


@router.get("/creator-state")
async def get_creator_state(
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    return ApiResponse(data=await CreatorStateService(db).refresh_trust(user["id"]))


@router.get("/projects/{project_id}/evidence")
async def list_project_evidence(
    project_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    return ApiResponse(data=await EvidenceService(db).list_project(user["id"], project_id))


@router.post("/evidence/{evidence_id}:decide", status_code=201)
async def decide_evidence(
    evidence_id: str,
    body: EvidenceDecision,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    service = EvidenceService(db)
    result, replayed = (
        await service.confirm(user["id"], evidence_id, body)
        if body.decision == "confirm"
        else await service.reject(user["id"], evidence_id, body)
    )
    return _created_or_replayed(response, result, replayed)


@router.post("/evidence/{evidence_id}:revoke", status_code=201)
async def revoke_evidence(
    evidence_id: str,
    body: EvidenceRevocation,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await EvidenceService(db).revoke(user["id"], evidence_id, body)
    return _created_or_replayed(response, result, replayed)


@router.get("/projects/{project_id}/next-action")
async def get_project_next_action(
    project_id: str,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result = await IntentOrchestratorService(db).ensure_project_action(user["id"], project_id)
    return ApiResponse(data=result)


@router.post("/projects/{project_id}/intent:confirm", status_code=201)
async def confirm_project_intent(
    project_id: str,
    body: IntentConfirmation,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await IntentConfirmationService(db).confirm(
        user["id"], project_id, body
    )
    return _created_or_replayed(response, result, replayed)


@router.post(
    "/projects/{project_id}/intent:classify-retrospective", status_code=201
)
async def classify_retrospective_intent(
    project_id: str,
    body: RetrospectiveIntentClassification,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await IntentConfirmationService(db).classify_retrospective(
        user["id"], project_id, body
    )
    return _created_or_replayed(response, result, replayed)


@router.post("/actions/{action_id}:respond", status_code=201)
async def respond_to_action(
    action_id: str,
    body: ActionResponse,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await ActionResponseService(db, llm=_optional_llm()).respond(
        user["id"], action_id, body
    )
    return _created_or_replayed(response, result, replayed)


@router.post("/actions/{action_id}:transition", status_code=201)
async def transition_action(
    action_id: str,
    body: ActionLifecycleCommand,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await ActionResponseService(db).transition(
        user["id"], action_id, body
    )
    return _created_or_replayed(response, result, replayed)


@router.post("/projects/{project_id}/automation", status_code=201)
async def set_project_automation(
    project_id: str,
    body: AutomationPreference,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await AutomationPreferenceService(db).set_project_level(
        user["id"], project_id, body
    )
    return _created_or_replayed(response, result, replayed)


@router.post("/actions/{action_id}/human-gate", status_code=201)
async def open_human_gate(
    action_id: str,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result = await HumanGateService(db).ensure_for_action(user["id"], action_id)
    response.status_code = 200 if result["status"] != "pending" else 201
    return ApiResponse(code=response.status_code, data=result)


@router.post("/human-gates/{gate_id}:decide", status_code=201)
async def decide_human_gate(
    gate_id: str,
    body: HumanGateDecision,
    response: Response,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    result, replayed = await HumanGateService(db, llm=_optional_llm()).decide(
        user["id"], gate_id, body
    )
    return _created_or_replayed(response, result, replayed)
