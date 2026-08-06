"""Version-bound deterministic publish guard with optional AI assistance."""

import hashlib
import json
import re
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException
from app.core.llm import LLMClient, wrap_user_input
from app.models.v2.action_domain import AITraceCreate
from app.models.v2.publish_check import (
    AIPublishCheckOutput,
    PublishCheckCreate,
    PublishCheckResolution,
    PublishCheckView,
)
from app.services.ai_trace import AITraceService
from app.services.v2_utils import decode_json_fields, now, request_hash

RULE_SOURCE = "TopicAI deterministic publish rules"
RULE_VERSION = "publish-risk-2026-08-06"
RULE_UPDATED_AT = "2026-08-06T00:00:00Z"
_RISK_RULES = (
    ("guarantee", re.compile(r"100\s*%|保证(?:通过|有效|成功)|必过|稳赚"), "high", "Avoid absolute guarantees or approval promises."),
    ("medical", re.compile(r"治愈|根治|药到病除"), "high", "Health claims need qualified, traceable support."),
    ("financial", re.compile(r"零风险|保本|稳赚不赔"), "high", "Financial guarantees are unsafe and cannot be promised."),
)


class PublishCheckService:
    def __init__(self, db: Any, llm: LLMClient | None = None):
        self.db = db
        self.llm = llm or LLMClient()

    async def run(
        self, owner: str, project_id: str, body: PublishCheckCreate
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash({"project_id": project_id, "body": body.model_dump()})
        existing = await self.db.fetch_one(
            "SELECT id,request_hash FROM publish_checks_v2 "
            "WHERE owner_user_id=:owner AND idempotency_key=:key",
            {"owner": owner, "key": body.idempotency_key},
        )
        if existing:
            if existing["request_hash"] != digest:
                raise IdempotencyConflictException()
            return await self.get(owner, existing["id"]), True

        version = await self.db.fetch_one(
            "SELECT cv.*,cp.current_version_id FROM content_versions cv "
            "JOIN content_projects cp ON cp.id=cv.project_id "
            "WHERE cv.id=:version AND cv.project_id=:project "
            "AND cv.owner_user_id=:owner AND cp.owner_user_id=:owner "
            "AND cp.deleted_at IS NULL",
            {"version": body.content_version_id, "project": project_id, "owner": owner},
        )
        if version is None:
            raise ValueError("content version not found")
        findings = self._deterministic_findings(version)
        limitations = [
            "This check is assistance only and does not guarantee platform approval."
        ]
        trace = None
        if self.llm.is_available("text"):
            try:
                ai_output = self.llm.generate_structured(
                    "Review only the supplied title, body and cover plan for concrete safety or "
                    "privacy risks. Do not invent platform rules or predict approval.\n"
                    + wrap_user_input(
                        json.dumps(
                            {
                                "title": version["title"],
                                "body_text": version["body_text"],
                                "cover_plan": version["cover_plan"],
                            },
                            ensure_ascii=False,
                        )
                    ),
                    AIPublishCheckOutput,
                    system_prompt="You are a bounded pre-publication content risk assistant.",
                )
                findings.extend(self._ai_findings(ai_output, version))
                trace = AITraceCreate(
                    id=str(uuid.uuid4()),
                    task_type="publish_check",
                    input_refs=[f"content-version:{version['id']}"],
                    evidence_refs=[],
                    policy_version=RULE_VERSION,
                    model_identifier=self.llm.model,
                    capability="text",
                    visibility_boundary={"allowed": ["selected_content_version"]},
                    contamination_check={"status": "clean"},
                    calibration_state="valid",
                    limitations=limitations,
                    output_ref="pending:publish-check",
                    generated_at=now(),
                )
            except Exception as exc:
                limitations.append(f"Optional AI assistance was unavailable: {type(exc).__name__}.")
        else:
            limitations.append("Optional AI assistance was not configured; deterministic rules ran.")

        check_id = str(uuid.uuid4())
        timestamp = now()
        if trace:
            trace.output_ref = f"publish-check:{check_id}"
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                if trace:
                    await AITraceService.create(session, owner, trace)
                await session.execute(
                    text(
                        "INSERT INTO publish_checks_v2 (id,owner_user_id,project_id,"
                        "content_version_id,content_hash,findings_json,limitations_json,"
                        "ai_trace_id,rule_version,rule_updated_at,idempotency_key,request_hash,"
                        "checked_at) VALUES (:id,:owner,:project,:version,:content_hash,"
                        ":findings,:limitations,:trace,:rule_version,:rule_updated,:key,:hash,:now)"
                    ),
                    {
                        "id": check_id,
                        "owner": owner,
                        "project": project_id,
                        "version": body.content_version_id,
                        "content_hash": version["content_hash"],
                        "findings": json.dumps(findings, ensure_ascii=False),
                        "limitations": json.dumps(limitations, ensure_ascii=False),
                        "trace": trace.id if trace else None,
                        "rule_version": RULE_VERSION,
                        "rule_updated": RULE_UPDATED_AT,
                        "key": body.idempotency_key,
                        "hash": digest,
                        "now": timestamp,
                    },
                )
        return await self.get(owner, check_id), False

    async def latest(self, owner: str, project_id: str) -> dict[str, Any] | None:
        row = await self.db.fetch_one(
            "SELECT id FROM publish_checks_v2 WHERE owner_user_id=:owner "
            "AND project_id=:project ORDER BY checked_at DESC,id DESC LIMIT 1",
            {"owner": owner, "project": project_id},
        )
        return await self.get(owner, row["id"]) if row else None

    async def get(self, owner: str, check_id: str) -> dict[str, Any]:
        row = await self.db.fetch_one(
            "SELECT pc.*,cp.current_version_id,cv.content_hash AS current_content_hash "
            "FROM publish_checks_v2 pc JOIN content_projects cp ON cp.id=pc.project_id "
            "JOIN content_versions cv ON cv.id=pc.content_version_id "
            "WHERE pc.id=:id AND pc.owner_user_id=:owner AND cp.owner_user_id=:owner",
            {"id": check_id, "owner": owner},
        )
        if row is None:
            raise ValueError("publish check not found")
        result = decode_json_fields(row, "findings_json", "limitations_json")
        resolutions = await self.db.fetch_all(
            "SELECT * FROM publish_check_resolutions_v2 WHERE publish_check_id=:check "
            "AND owner_user_id=:owner ORDER BY created_at,id",
            {"check": check_id, "owner": owner},
        )
        decisions: dict[str, str] = {}
        normalized_resolutions = []
        for resolution in resolutions:
            item = decode_json_fields(resolution, "findings_json")
            decisions.update(item["findings"])
            normalized_resolutions.append(item)
        for finding in result["findings"]:
            finding["status"] = decisions.get(finding["id"], "open")
        result["resolutions"] = normalized_resolutions
        result["stale"] = bool(
            result["current_version_id"] != result["content_version_id"]
            or result["content_hash"] != result["current_content_hash"]
        )
        result["status"] = (
            "stale"
            if result["stale"]
            else "needs_attention"
            if any(item["status"] == "open" for item in result["findings"])
            else "clear"
        )
        return PublishCheckView.model_validate(
            {
                "id": result["id"],
                "project_id": result["project_id"],
                "content_version_id": result["content_version_id"],
                "status": result["status"],
                "stale": result["stale"],
                "findings": result["findings"],
                "limitations": result["limitations"],
                "resolutions": [
                    {
                        "id": item["id"],
                        "findings": item["findings"],
                        "created_at": item["created_at"],
                    }
                    for item in result["resolutions"]
                ],
                "ai_trace_id": result["ai_trace_id"],
                "rule_version": result["rule_version"],
                "rule_updated_at": result["rule_updated_at"],
                "checked_at": result["checked_at"],
            }
        ).model_dump(mode="json")

    async def resolve(
        self, owner: str, check_id: str, body: PublishCheckResolution
    ) -> tuple[dict[str, Any], bool]:
        digest = request_hash({"check_id": check_id, "body": body.model_dump()})
        existing = await self.db.fetch_one(
            "SELECT publish_check_id,request_hash FROM publish_check_resolutions_v2 "
            "WHERE owner_user_id=:owner AND idempotency_key=:key",
            {"owner": owner, "key": body.idempotency_key},
        )
        if existing:
            if existing["request_hash"] != digest or existing["publish_check_id"] != check_id:
                raise IdempotencyConflictException()
            return await self.get(owner, check_id), True
        check = await self.get(owner, check_id)
        finding_ids = {item["id"] for item in check["findings"]}
        if not set(body.findings).issubset(finding_ids):
            raise ValueError("publish check resolution contains an unknown finding")
        await self.db.execute(
            "INSERT INTO publish_check_resolutions_v2 (id,owner_user_id,publish_check_id,"
            "findings_json,idempotency_key,request_hash,created_at) VALUES "
            "(:id,:owner,:check,:findings,:key,:hash,:now)",
            {
                "id": str(uuid.uuid4()),
                "owner": owner,
                "check": check_id,
                "findings": json.dumps(body.findings, ensure_ascii=False),
                "key": body.idempotency_key,
                "hash": digest,
                "now": now(),
            },
        )
        return await self.get(owner, check_id), False

    @staticmethod
    def _deterministic_findings(version: Any) -> list[dict[str, Any]]:
        findings = []
        for field in ("title", "body_text", "cover_plan"):
            value = version[field] or ""
            for rule_id, pattern, severity, reason in _RISK_RULES:
                for match in pattern.finditer(value):
                    finding_id = hashlib.sha256(
                        f"{rule_id}:{field}:{match.start()}:{match.end()}".encode()
                    ).hexdigest()[:16]
                    findings.append(
                        {
                            "id": finding_id,
                            "field": field,
                            "start": match.start(),
                            "end": match.end(),
                            "excerpt": match.group(0),
                            "reason": reason,
                            "severity": severity,
                            "rule_source": RULE_SOURCE,
                            "rule_updated_at": RULE_UPDATED_AT,
                        }
                    )
        return findings

    @staticmethod
    def _ai_findings(output: AIPublishCheckOutput, version: Any) -> list[dict[str, Any]]:
        findings = []
        for index, item in enumerate(output.findings):
            value = version[item.field] or ""
            start = min(item.start, len(value))
            end = min(max(item.end, start), len(value))
            findings.append(
                {
                    "id": hashlib.sha256(
                        f"ai:{index}:{item.field}:{start}:{end}:{item.reason}".encode()
                    ).hexdigest()[:16],
                    "field": item.field,
                    "start": start,
                    "end": end,
                    "excerpt": value[start:end],
                    "reason": item.reason,
                    "severity": item.severity,
                    "rule_source": "Configured model assistance",
                    "rule_updated_at": RULE_UPDATED_AT,
                }
            )
        return findings
