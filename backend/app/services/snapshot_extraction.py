"""Vision-assisted metric proposals that remain unconfirmed until snapshot creation."""

import base64
import json
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import AICapabilityMissingException, IdempotencyConflictException
from app.core.llm import LLMClient, _clean_json_response
from app.core.storage import LocalObjectStorage
from app.models.v2.action_domain import AITraceCreate
from app.models.v2.snapshot_extraction import (
    SnapshotExtractionCreate,
    SnapshotExtractionView,
    SnapshotMetricsProposal,
)
from app.services.ai_trace import AITraceService
from app.services.v2_utils import decode_json_fields, now, request_hash


class SnapshotExtractionService:
    POLICY_VERSION = "snapshot-extract-v1"

    def __init__(
        self,
        db: Any,
        *,
        llm: LLMClient | None = None,
        storage: LocalObjectStorage | None = None,
    ):
        self.db = db
        self.llm = llm or LLMClient()
        self.storage = storage or LocalObjectStorage()

    async def extract(
        self, owner: str, body: SnapshotExtractionCreate
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash(body)
        existing = await self.db.fetch_one(
            "SELECT id,request_hash FROM snapshot_extractions_v2 "
            "WHERE owner_user_id=:owner AND idempotency_key=:key",
            {"owner": owner, "key": body.idempotency_key},
        )
        if existing:
            if existing["request_hash"] != digest:
                raise IdempotencyConflictException()
            return await self.get(owner, existing["id"]), True
        if not self.llm.is_available("vision"):
            raise AICapabilityMissingException("vision")

        material = await self.db.fetch_one(
            "SELECT * FROM materials WHERE id=:id AND owner_user_id=:owner",
            {"id": body.material_id, "owner": owner},
        )
        if material is None:
            raise ValueError("material not found")
        if material["kind"] != "image":
            raise ValueError("snapshot extraction requires an image material")
        image_url = material["source_url"]
        if material.get("storage_path"):
            payload = await self.storage.get(material["storage_path"])
            if payload is None:
                raise ValueError("material file not found")
            image_url = (
                f"data:{material['mime_type']};base64,"
                + base64.b64encode(payload).decode("ascii")
            )
        raw = self.llm.vision_generate(
            image_url,
            "Extract only visible Xiaohongshu performance values. Return JSON with nullable "
            "integer fields: views, likes, favorites, comments, shares, follows_gained. "
            "Use null when a value is absent or unclear. Do not infer or calculate values.",
        )
        try:
            metrics = SnapshotMetricsProposal.model_validate(
                json.loads(_clean_json_response(raw))
            )
        except (json.JSONDecodeError, ValueError) as exc:
            from app.core.exceptions import LLMStructuredOutputException

            raise LLMStructuredOutputException(
                f"Invalid screenshot metric output: {exc}",
                provider="openai_compatible",
                retries=1,
            ) from exc

        extraction_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        timestamp = now()
        trace = AITraceCreate(
            id=trace_id,
            task_type="snapshot_metric_extraction",
            input_refs=[f"material:{body.material_id}"],
            evidence_refs=[f"material:{body.material_id}"],
            policy_version=self.POLICY_VERSION,
            model_identifier=self.llm.model,
            capability="vision",
            visibility_boundary={"allowed": ["selected_metric_screenshot"]},
            contamination_check={"status": "clean"},
            calibration_state="insufficient",
            limitations=[
                "Values are unconfirmed proposals until the user reviews and submits them.",
                "Missing or unclear values remain null.",
            ],
            output_ref=f"snapshot-extraction:{extraction_id}",
            generated_at=timestamp,
            confidence_label="low",
            outcome="success",
        )
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                await AITraceService.create(session, owner, trace)
                await session.execute(
                    text(
                        "INSERT INTO snapshot_extractions_v2 (id,owner_user_id,material_id,"
                        "metrics_json,ai_trace_id,idempotency_key,request_hash,created_at) VALUES "
                        "(:id,:owner,:material,:metrics,:trace,:key,:hash,:now)"
                    ),
                    {
                        "id": extraction_id,
                        "owner": owner,
                        "material": body.material_id,
                        "metrics": json.dumps(
                            metrics.model_dump(exclude_none=False), ensure_ascii=False
                        ),
                        "trace": trace_id,
                        "key": body.idempotency_key,
                        "hash": digest,
                        "now": timestamp,
                    },
                )
        return await self.get(owner, extraction_id), False

    async def get(self, owner: str, extraction_id: str) -> dict[str, Any]:
        row = await self.db.fetch_one(
            "SELECT se.*,at.task_type,at.policy_version,at.model_identifier,at.capability,"
            "at.input_refs_json,at.evidence_refs_json,at.visibility_boundary_json,"
            "at.source_snapshot_ids_json,at.contamination_check_json,at.calibration_state,"
            "at.limitations_json,at.output_ref,at.generated_at,at.confidence_label,at.outcome "
            "FROM snapshot_extractions_v2 se "
            "JOIN ai_traces_v2 at ON at.id=se.ai_trace_id AND at.owner_user_id=se.owner_user_id "
            "WHERE se.id=:id AND se.owner_user_id=:owner",
            {"id": extraction_id, "owner": owner},
        )
        if row is None:
            raise ValueError("snapshot extraction not found")
        result = decode_json_fields(row, "metrics_json", "limitations_json")
        return SnapshotExtractionView.model_validate(
            {
                "id": result["id"],
                "material_id": result["material_id"],
                "metrics": result["metrics"],
                "confirmed_by_user": result["user_decision"]
                in {"confirmed", "edited"},
                "user_decision": result["user_decision"],
                "decided_at": result["decided_at"],
                "snapshot_id": result["snapshot_id"],
                "ai_trace": {
                    "capability": result["capability"],
                    "confidence_label": result["confidence_label"],
                    "limitations": result["limitations"],
                    "outcome": result["outcome"],
                },
            }
        ).model_dump(mode="json")
