"""Single transactional writer for v2 AI provenance records."""

import json
from typing import Any

from sqlalchemy import text

from app.models.v2.action_domain import AITraceCreate


class AITraceService:
    @staticmethod
    async def create(
        session: Any, owner_user_id: str, trace: AITraceCreate
    ) -> None:
        await session.execute(
            text(
                "INSERT INTO ai_traces_v2 (id,owner_user_id,task_type,input_refs_json,"
                "evidence_refs_json,policy_version,model_identifier,capability,"
                "visibility_boundary_json,source_snapshot_ids_json,contamination_check_json,"
                "calibration_state,limitations_json,output_ref,generated_at,confidence_label,"
                "outcome,user_decision) VALUES "
                "(:id,:owner,:task_type,:inputs,:evidence,:policy,:model,:capability,"
                ":boundary,:snapshots,:contamination,:state,:limitations,:output,:generated,"
                ":confidence,:outcome,:decision)"
            ),
            {
                "id": trace.id,
                "owner": owner_user_id,
                "task_type": trace.task_type,
                "inputs": json.dumps(trace.input_refs, ensure_ascii=False),
                "evidence": json.dumps(trace.evidence_refs, ensure_ascii=False),
                "policy": trace.policy_version,
                "model": trace.model_identifier,
                "capability": trace.capability,
                "boundary": json.dumps(trace.visibility_boundary, ensure_ascii=False),
                "snapshots": json.dumps(trace.source_snapshot_ids, ensure_ascii=False),
                "contamination": json.dumps(trace.contamination_check, ensure_ascii=False),
                "state": trace.calibration_state,
                "limitations": json.dumps(trace.limitations, ensure_ascii=False),
                "output": trace.output_ref,
                "generated": trace.generated_at,
                "confidence": trace.confidence_label,
                "outcome": trace.outcome,
                "decision": trace.user_decision,
            },
        )
