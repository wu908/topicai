"""Initial calibration comparison with a code-enforced visibility boundary."""

import json
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.models.v2.action_domain import AITraceCreate
from app.models.v2.calibration import BlindReviewCreate
from app.services.ai_trace import AITraceService
from app.services.v2_utils import (
    decode_json_fields,
    effective_intent_status,
    now,
    request_hash,
)


class BlindReviewService:
    REQUIRED_INPUT_CLASSES = frozenset(
        {"publish_hypothesis", "content_version", "performance_snapshot"}
    )
    ALLOWED_INPUT_CLASSES = frozenset(
        {*REQUIRED_INPUT_CLASSES, "benchmark_sample"}
    )
    FORBIDDEN_INPUT_CLASSES = frozenset(
        {
            "post_hoc_explanation",
            "review_causes",
            "observation",
            "creator_rule",
            "future_metrics",
        }
    )
    BEHAVIOR_METRICS = {
        "save": "favorites",
        "comment": "comments",
        "follow": "follows_gained",
    }

    def __init__(self, db: Any):
        self.db = db

    async def create(
        self,
        owner_user_id: str,
        project_id: str,
        body: BlindReviewCreate,
        *,
        input_classes: set[str] | None = None,
    ) -> tuple[dict[str, Any], bool]:
        actual_inputs = set(
            self.REQUIRED_INPUT_CLASSES if input_classes is None else input_classes
        )
        if body.benchmark_sample_ids:
            actual_inputs.add("benchmark_sample")
        digest = request_hash(
            {
                "project_id": project_id,
                "body": body.model_dump(mode="json"),
                "input_classes": sorted(actual_inputs),
            }
        )
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                existing = (
                    await session.execute(
                        text(
                            "SELECT * FROM blind_reviews WHERE owner_user_id=:owner "
                            "AND idempotency_key=:key"
                        ),
                        {"owner": owner_user_id, "key": body.idempotency_key},
                    )
                ).mappings().first()
                if existing:
                    if existing["request_hash"] != digest:
                        raise IdempotencyConflictException()
                    project = await self._project(session, owner_user_id, project_id)
                    trace = await self._trace(
                        session, owner_user_id, existing["ai_trace_id"]
                    )
                    return self._result(project, existing, trace), True

                project = await self._project(session, owner_user_id, project_id)
                if project["version"] != body.expected_project_version:
                    raise VersionConflictException(
                        project["version"], body.expected_project_version
                    )
                if project["status"] != "awaiting_review":
                    raise ValueError("project is not awaiting review")
                if len(set(body.result_snapshot_ids)) != len(body.result_snapshot_ids):
                    raise ValueError("result snapshot ids must be unique")
                if len(set(body.benchmark_sample_ids)) != len(body.benchmark_sample_ids):
                    raise ValueError("benchmark sample ids must be unique")

                hypothesis = (
                    await session.execute(
                        text(
                            "SELECT * FROM publish_hypotheses WHERE id=:id "
                            "AND owner_user_id=:owner AND project_id=:project"
                        ),
                        {
                            "id": project["publish_hypothesis_id"],
                            "owner": owner_user_id,
                            "project": project_id,
                        },
                    )
                ).mappings().first()
                if hypothesis is None:
                    raise ValueError("locked publish hypothesis not found")

                snapshots = []
                for snapshot_id in body.result_snapshot_ids:
                    snapshot = (
                        await session.execute(
                            text(
                                "SELECT * FROM performance_snapshots_v2 WHERE id=:id "
                                "AND owner_user_id=:owner AND project_id=:project "
                                "AND confirmed_by_user=1"
                            ),
                            {
                                "id": snapshot_id,
                                "owner": owner_user_id,
                                "project": project_id,
                            },
                        )
                    ).mappings().first()
                    if snapshot is None:
                        raise ValueError(f"result snapshot not found: {snapshot_id}")
                    successor = (
                        await session.execute(
                            text(
                                "SELECT id FROM performance_snapshots_v2 "
                                "WHERE supersedes_id=:id"
                            ),
                            {"id": snapshot_id},
                        )
                    ).first()
                    if successor is not None:
                        raise ValueError(f"result snapshot was superseded: {snapshot_id}")
                    snapshots.append(decode_json_fields(snapshot, "metrics_json"))

                availability_states = {
                    item.get("result_availability", "observed") for item in snapshots
                }
                result_unavailable = availability_states == {"unavailable"}
                if "unavailable" in availability_states and (
                    not result_unavailable or len(snapshots) != 1
                ):
                    raise ValueError(
                        "an unavailable result cannot be combined with other snapshots"
                    )

                benchmark_samples = await self._benchmark_samples(
                    session, owner_user_id, body.benchmark_sample_ids
                )
                included_benchmarks = [
                    item
                    for item in benchmark_samples
                    if item["inclusion_state"] == "included"
                ]

                unexpected = sorted(actual_inputs - self.ALLOWED_INPUT_CLASSES)
                missing = sorted(self.REQUIRED_INPUT_CLASSES - actual_inputs)
                contamination_status = "contaminated" if unexpected else "clean"
                comparison, has_comparable_metric = self._compare(
                    hypothesis, snapshots, included_benchmarks
                )
                comparison["result_availability"] = (
                    "unavailable" if result_unavailable else "observed"
                )
                comparison["benchmark_context"] = {
                    "included_sample_ids": [item["id"] for item in included_benchmarks],
                    "excluded_samples": [
                        {
                            "id": item["id"],
                            "reason_code": item["exclusion_reason_code"],
                        }
                        for item in benchmark_samples
                        if item["inclusion_state"] == "excluded"
                    ],
                    "mode": "relative_observation_only",
                }
                comparison["intent_review"] = self._intent_review_plan(
                    project,
                    comparison["expected_behavior_comparisons"],
                    len(snapshots),
                    result_availability=comparison["result_availability"],
                )
                revoked_evidence_ids = await self._revoked_evidence_ids(
                    session, owner_user_id, hypothesis["content_version_id"]
                )
                intent_status = effective_intent_status(project)
                is_retrospective = intent_status == "retrospective"
                is_legacy = not is_retrospective and (
                    hypothesis["status"] == "legacy_missing"
                    or intent_status == "legacy_unclassified"
                )
                hypothesis_usable = hypothesis["status"] == "locked" or (
                    is_retrospective and hypothesis["status"] == "legacy_missing"
                )
                if contamination_status == "contaminated":
                    calibration_state = "calibration_invalid"
                    eligibility_reason_code = "contaminated_input"
                elif revoked_evidence_ids:
                    calibration_state = "calibration_invalid"
                    eligibility_reason_code = "revoked_evidence"
                elif is_legacy:
                    calibration_state = "insufficient"
                    eligibility_reason_code = "legacy_hypothesis"
                elif result_unavailable:
                    calibration_state = "insufficient"
                    eligibility_reason_code = "insufficient_metrics"
                elif (
                    missing
                    or not hypothesis_usable
                    or not has_comparable_metric
                ):
                    calibration_state = "insufficient"
                    eligibility_reason_code = "insufficient_metrics"
                else:
                    calibration_state = "valid"
                    eligibility_reason_code = "eligible_clean"
                eligible_for_rule_upgrade = int(
                    eligibility_reason_code == "eligible_clean"
                )

                visibility_boundary = {
                    "allowed": sorted(self.ALLOWED_INPUT_CLASSES),
                    "forbidden": sorted(self.FORBIDDEN_INPUT_CLASSES),
                    "actual": sorted(actual_inputs),
                }
                contamination_check = {
                    "status": contamination_status,
                    "unexpected_classes": unexpected,
                    "missing_classes": missing,
                    "revoked_evidence_ids": revoked_evidence_ids,
                }
                hypothesis_snapshot = {
                    "id": hypothesis["id"],
                    "content_version_id": hypothesis["content_version_id"],
                    "audience_problem": hypothesis["audience_problem"],
                    "reader_promise": hypothesis["reader_promise"],
                    "expected_behaviors": json.loads(
                        hypothesis["expected_behaviors_json"]
                    ),
                    "basis_refs": json.loads(hypothesis["basis_refs_json"]),
                    "uncertainties": json.loads(hypothesis["uncertainties_json"]),
                    "locked_at": hypothesis["locked_at"],
                }
                review_id = str(uuid.uuid4())
                trace_id = str(uuid.uuid4())
                timestamp = now()
                limitations = [
                    "Observed metrics do not establish causal attribution.",
                    "Missing metrics remain unknown and are never treated as zero.",
                ]
                if result_unavailable:
                    limitations.append(
                        "An unavailable result can only produce an unknown Intent Outcome."
                    )
                await AITraceService.create(
                    session,
                    owner_user_id,
                    AITraceCreate(
                        id=trace_id,
                        task_type="blind_review_initial_comparison",
                        input_refs=[
                            f"publish_hypothesis:{hypothesis['id']}",
                            f"content_version:{hypothesis['content_version_id']}",
                            *[
                                f"performance_snapshot:{item['id']}"
                                for item in snapshots
                            ],
                            *[
                                f"benchmark_sample:{item['id']}"
                                for item in included_benchmarks
                            ],
                        ],
                        evidence_refs=json.loads(hypothesis["basis_refs_json"]),
                        policy_version="blind-review-v1",
                        capability="deterministic",
                        visibility_boundary=visibility_boundary,
                        source_snapshot_ids=body.result_snapshot_ids,
                        contamination_check=contamination_check,
                        calibration_state=calibration_state,
                        limitations=limitations,
                        output_ref=f"blind_review:{review_id}",
                        generated_at=timestamp,
                    ),
                )
                await session.execute(
                    text(
                        "INSERT INTO blind_reviews ("
                        "id,owner_user_id,project_id,publish_hypothesis_id,"
                        "hypothesis_snapshot_json,result_snapshot_ids_json,comparison_json,"
                        "visibility_boundary_json,contamination_status,calibration_state,"
                        "eligible_for_rule_upgrade,eligibility_reason_code,"
                        "benchmark_sample_ids_json,ai_trace_id,idempotency_key,request_hash,"
                        "reviewed_at,created_at) VALUES ("
                        ":id,:owner,:project,:hypothesis,:hypothesis_snapshot,:snapshots,"
                        ":comparison,:boundary,:contamination,:state,:eligible,:reason,"
                        ":benchmarks,:trace,:key,:hash,:now,:now)"
                    ),
                    {
                        "id": review_id,
                        "owner": owner_user_id,
                        "project": project_id,
                        "hypothesis": hypothesis["id"],
                        "hypothesis_snapshot": json.dumps(hypothesis_snapshot),
                        "snapshots": json.dumps(body.result_snapshot_ids),
                        "comparison": json.dumps(comparison),
                        "boundary": json.dumps(visibility_boundary),
                        "contamination": contamination_status,
                        "state": calibration_state,
                        "eligible": eligible_for_rule_upgrade,
                        "reason": eligibility_reason_code,
                        "benchmarks": json.dumps(
                            [item["id"] for item in included_benchmarks]
                        ),
                        "trace": trace_id,
                        "key": body.idempotency_key,
                        "hash": digest,
                        "now": timestamp,
                    },
                )
                updated = await session.execute(
                    text(
                        "UPDATE content_projects SET calibration_state=:state,"
                        "last_action='blind_review_completed',last_action_at=:now,"
                        "updated_at=:now,version=version+1 WHERE id=:project "
                        "AND owner_user_id=:owner AND version=:expected"
                    ),
                    {
                        "state": calibration_state,
                        "now": timestamp,
                        "project": project_id,
                        "owner": owner_user_id,
                        "expected": body.expected_project_version,
                    },
                )
                if updated.rowcount != 1:
                    raise VersionConflictException(
                        project["version"], body.expected_project_version
                    )
                review = (
                    await session.execute(
                        text("SELECT * FROM blind_reviews WHERE id=:id"),
                        {"id": review_id},
                    )
                ).mappings().one()
                trace = await self._trace(session, owner_user_id, trace_id)
                updated_project = await self._project(
                    session, owner_user_id, project_id
                )
                return self._result(updated_project, review, trace), False

    @classmethod
    def _compare(cls, hypothesis, snapshots, benchmark_samples=()):
        behaviors = json.loads(hypothesis["expected_behaviors_json"])
        comparisons = []
        has_comparable_metric = False
        result_unavailable = any(
            snapshot.get("result_availability") == "unavailable"
            for snapshot in snapshots
        )
        for behavior in behaviors:
            metric = cls.BEHAVIOR_METRICS.get(behavior)
            values = [
                snapshot["metrics"].get(metric)
                for snapshot in snapshots
                if metric and snapshot["metrics"].get(metric) is not None
            ]
            if values:
                has_comparable_metric = True
            benchmark_values = [
                sample["metrics"].get(metric)
                for sample in benchmark_samples
                if metric and sample["metrics"].get(metric) is not None
            ]
            relative_position = "unknown"
            if values and benchmark_values:
                observed = values[-1]
                if observed < min(benchmark_values):
                    relative_position = "below_observed_range"
                elif observed > max(benchmark_values):
                    relative_position = "above_observed_range"
                else:
                    relative_position = "within_observed_range"
            comparisons.append(
                {
                    "claim": behavior,
                    "metric": metric,
                    "observed_values": values,
                    "benchmark_observed_values": benchmark_values,
                    "relative_position": relative_position,
                    "assessment": "unknown",
                    "reason": (
                        "Result was explicitly marked unavailable."
                        if result_unavailable
                        else "Observed without a pre-registered threshold."
                        if values
                        else "No comparable observed metric is available."
                    ),
                }
            )
        return {"expected_behavior_comparisons": comparisons}, has_comparable_metric

    @staticmethod
    async def _benchmark_samples(session, owner_user_id: str, sample_ids: list[str]):
        samples = []
        for sample_id in sample_ids:
            row = (
                await session.execute(
                    text(
                        "SELECT * FROM benchmark_samples WHERE id=:id "
                        "AND owner_user_id=:owner"
                    ),
                    {"id": sample_id, "owner": owner_user_id},
                )
            ).mappings().first()
            if row is None:
                raise ValueError(f"benchmark sample not found: {sample_id}")
            samples.append(
                decode_json_fields(row, "metric_snapshot_ids_json", "metrics_json")
            )
        return samples

    @staticmethod
    async def _revoked_evidence_ids(session, owner_user_id: str, version_id: str):
        version = (
            await session.execute(
                text(
                    "SELECT evidence_snapshot_json FROM content_versions WHERE id=:id "
                    "AND owner_user_id=:owner"
                ),
                {"id": version_id, "owner": owner_user_id},
            )
        ).mappings().first()
        if version is None:
            return []
        evidence_ids = [
            item.get("evidence_id")
            for item in json.loads(version["evidence_snapshot_json"] or "[]")
            if isinstance(item, dict) and item.get("evidence_id")
        ]
        revoked = []
        for evidence_id in evidence_ids:
            row = (
                await session.execute(
                    text(
                        "SELECT confirmation_status FROM evidence_items WHERE id=:id "
                        "AND owner_user_id=:owner"
                    ),
                    {"id": evidence_id, "owner": owner_user_id},
                )
            ).mappings().first()
            if row and row["confirmation_status"] == "revoked":
                revoked.append(evidence_id)
        return revoked

    @staticmethod
    def _intent_review_plan(
        project,
        comparisons,
        sample_count: int,
        *,
        result_availability: str = "observed",
    ) -> dict[str, Any]:
        """Turn observed metrics into bounded, intent-specific next actions.

        This deliberately does not infer causes from one result. The plan is
        stored with the review so the later learning gate confirms the exact
        evidence and wording the user saw.
        """
        intent = (
            project.get("content_intent")
            or project.get("retrospective_intent")
            or "solve"
        )
        labels = {"solve": "解决", "share": "分享", "record": "记录"}
        observed_facts = [
            {
                "claim": item["claim"],
                "metric": item["metric"],
                "observed_values": item["observed_values"],
                "assessment": item["assessment"],
                "status": "observed" if item["observed_values"] else "unknown",
            }
            for item in comparisons
        ]
        possible_causes = {
            "solve": [
                "当前结果只能说明读者是否出现了对应行为，不能单独证明方法本身有效。",
                "问题具体程度、步骤清晰度和案例可信度仍未被单独验证。",
            ],
            "share": [
                "评论和关注变化可能同时受到事件相关性、表达真实度和平台分发影响。",
                "当前数据不能单独证明读者产生了共鸣或理解。",
            ],
            "record": [
                "阅读和关注变化可能同时受到更新节点、系列预期和平台分发影响。",
                "单次快照不能证明读者会持续关注后续过程。",
            ],
        }[intent]
        actions = {
            "solve": {
                "continue_item": "继续测试问题、方法、案例和限制都清楚的解决型内容。",
                "stop_item": "停止把一次收藏或关注结果当成方法已经被验证。",
                "experiment_item": "下一篇保持受众和问题相近，只增加一个具体案例或限制说明，再比较对应行为。",
            },
            "share": {
                "continue_item": "继续分享有具体事件、感受和观点变化的内容。",
                "stop_item": "停止只用评论数量判断是否产生了真实共鸣。",
                "experiment_item": "下一篇保持主题相近，只突出一个转折瞬间，再比较评论的具体回应质量。",
            },
            "record": {
                "continue_item": "继续用起点、过程、转折和结果记录真实变化。",
                "stop_item": "停止用一次阅读或关注结果判断系列内容会持续有效。",
                "experiment_item": "下一篇保持系列主题相近，只增加一个阶段性更新和明确的后续节点，再比较持续关注信号。",
            },
        }[intent]
        plan = {
            "intent": intent,
            "intent_label": labels[intent],
            "sample_count": sample_count,
            "observed_facts": observed_facts,
            "possible_causes": possible_causes,
            **actions,
            "confirmation_required": True,
            "long_term_write_allowed": False,
        }
        if result_availability == "unavailable":
            plan.update(
                {
                    "intent_outcome": "unknown",
                    "result_availability": "unavailable",
                    "possible_causes": [
                        "结果数据不可用，无法判断发布意图获得了支持还是遇到矛盾。"
                    ],
                    "follow_up_options": [
                        {
                            "action": "collect_more_evidence",
                            "label": "收集其他证据",
                            "statement": "本次平台结果不可用，改为收集可追溯的读者反馈。",
                            "next_test": "收集与本次发布意图相关的读者反馈，再决定是否继续测试。",
                        },
                        {
                            "action": "repeat_observation",
                            "label": "重试观察",
                            "statement": "本次平台结果不可用，稍后重新尝试取得同一观察窗口的数据。",
                            "next_test": "在数据可能恢复后重新检查同一篇内容，不把缺失值记为零。",
                        },
                        {
                            "action": "run_bounded_experiment",
                            "label": "做一个有界实验",
                            "statement": "本次结果未知，下一篇只改变一个变量继续验证。",
                            "next_test": actions["experiment_item"],
                        },
                    ],
                }
            )
        return plan

    @staticmethod
    async def _project(session, owner_user_id: str, project_id: str):
        project = (
            await session.execute(
                text(
                    "SELECT * FROM content_projects WHERE id=:id "
                    "AND owner_user_id=:owner AND deleted_at IS NULL"
                ),
                {"id": project_id, "owner": owner_user_id},
            )
        ).mappings().first()
        if project is None:
            raise ValueError(f"project not found: {project_id}")
        return project

    @staticmethod
    async def _trace(session, owner_user_id: str, trace_id: str):
        trace = (
            await session.execute(
                text(
                    "SELECT * FROM ai_traces_v2 WHERE id=:id "
                    "AND owner_user_id=:owner"
                ),
                {"id": trace_id, "owner": owner_user_id},
            )
        ).mappings().first()
        if trace is None:
            raise ValueError(f"AI trace not found: {trace_id}")
        return trace

    @staticmethod
    def _result(project, review, trace):
        review_result = decode_json_fields(
            review,
            "hypothesis_snapshot_json",
            "result_snapshot_ids_json",
            "comparison_json",
            "visibility_boundary_json",
            "benchmark_sample_ids_json",
        )
        review_result["eligible_for_rule_upgrade"] = bool(
            review_result["eligible_for_rule_upgrade"]
        )
        trace_result = decode_json_fields(
            trace,
            "input_refs_json",
            "evidence_refs_json",
            "visibility_boundary_json",
            "source_snapshot_ids_json",
            "contamination_check_json",
            "limitations_json",
        )
        return {
            "project": dict(project),
            "review": review_result,
            "trace": trace_result,
        }
