"""Initial calibration comparison with a code-enforced visibility boundary."""

import json
import uuid
from typing import Any

from sqlalchemy import text

from app.core.exceptions import IdempotencyConflictException, VersionConflictException
from app.models.v2.calibration import BlindReviewCreate
from app.services.v2_utils import decode_json_fields, now, request_hash


class BlindReviewService:
    ALLOWED_INPUT_CLASSES = frozenset(
        {"publish_hypothesis", "content_version", "performance_snapshot"}
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
            self.ALLOWED_INPUT_CLASSES if input_classes is None else input_classes
        )
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

                unexpected = sorted(actual_inputs - self.ALLOWED_INPUT_CLASSES)
                missing = sorted(self.ALLOWED_INPUT_CLASSES - actual_inputs)
                contamination_status = "contaminated" if unexpected else "clean"
                comparison, has_comparable_metric = self._compare(hypothesis, snapshots)
                comparison["intent_review"] = self._intent_review_plan(
                    project,
                    comparison["expected_behavior_comparisons"],
                    len(snapshots),
                )
                if contamination_status == "contaminated":
                    calibration_state = "calibration_invalid"
                elif (
                    missing
                    or hypothesis["status"] != "locked"
                    or not has_comparable_metric
                ):
                    calibration_state = "insufficient"
                else:
                    calibration_state = "valid"
                eligible_for_rule_upgrade = int(calibration_state == "valid")

                visibility_boundary = {
                    "allowed": sorted(self.ALLOWED_INPUT_CLASSES),
                    "forbidden": sorted(self.FORBIDDEN_INPUT_CLASSES),
                    "actual": sorted(actual_inputs),
                }
                contamination_check = {
                    "status": contamination_status,
                    "unexpected_classes": unexpected,
                    "missing_classes": missing,
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
                await session.execute(
                    text(
                        "INSERT INTO ai_traces_v2 ("
                        "id,owner_user_id,task_type,input_refs_json,evidence_refs_json,"
                        "policy_version,model_identifier,capability,visibility_boundary_json,"
                        "source_snapshot_ids_json,contamination_check_json,calibration_state,"
                        "limitations_json,output_ref,generated_at) VALUES ("
                        ":id,:owner,'blind_review_initial_comparison',:inputs,:evidence,"
                        "'blind-review-v1',NULL,'deterministic',:boundary,:snapshots,"
                        ":contamination,:state,:limitations,:output,:now)"
                    ),
                    {
                        "id": trace_id,
                        "owner": owner_user_id,
                        "inputs": json.dumps(
                            [
                                f"publish_hypothesis:{hypothesis['id']}",
                                f"content_version:{hypothesis['content_version_id']}",
                                *[
                                    f"performance_snapshot:{item['id']}"
                                    for item in snapshots
                                ],
                            ]
                        ),
                        "evidence": hypothesis["basis_refs_json"],
                        "boundary": json.dumps(visibility_boundary),
                        "snapshots": json.dumps(body.result_snapshot_ids),
                        "contamination": json.dumps(contamination_check),
                        "state": calibration_state,
                        "limitations": json.dumps(limitations),
                        "output": f"blind_review:{review_id}",
                        "now": timestamp,
                    },
                )
                await session.execute(
                    text(
                        "INSERT INTO blind_reviews ("
                        "id,owner_user_id,project_id,publish_hypothesis_id,"
                        "hypothesis_snapshot_json,result_snapshot_ids_json,comparison_json,"
                        "visibility_boundary_json,contamination_status,calibration_state,"
                        "eligible_for_rule_upgrade,ai_trace_id,idempotency_key,request_hash,"
                        "reviewed_at,created_at) VALUES ("
                        ":id,:owner,:project,:hypothesis,:hypothesis_snapshot,:snapshots,"
                        ":comparison,:boundary,:contamination,:state,:eligible,:trace,:key,:hash,"
                        ":now,:now)"
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
    def _compare(cls, hypothesis, snapshots):
        behaviors = json.loads(hypothesis["expected_behaviors_json"])
        comparisons = []
        has_comparable_metric = False
        for behavior in behaviors:
            metric = cls.BEHAVIOR_METRICS.get(behavior)
            values = [
                snapshot["metrics"].get(metric)
                for snapshot in snapshots
                if metric and snapshot["metrics"].get(metric) is not None
            ]
            if values:
                has_comparable_metric = True
            comparisons.append(
                {
                    "claim": behavior,
                    "metric": metric,
                    "observed_values": values,
                    "assessment": "unknown",
                    "reason": (
                        "Observed without a pre-registered threshold."
                        if values
                        else "No comparable observed metric is available."
                    ),
                }
            )
        return {"expected_behavior_comparisons": comparisons}, has_comparable_metric

    @staticmethod
    def _intent_review_plan(project, comparisons, sample_count: int) -> dict[str, Any]:
        """Turn observed metrics into bounded, intent-specific next actions.

        This deliberately does not infer causes from one result. The plan is
        stored with the review so the later learning gate confirms the exact
        evidence and wording the user saw.
        """
        intent = project.get("content_intent") or "solve"
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
        return {
            "intent": intent,
            "intent_label": labels[intent],
            "sample_count": sample_count,
            "observed_facts": observed_facts,
            "possible_causes": possible_causes,
            **actions,
            "confirmation_required": True,
            "long_term_write_allowed": False,
        }

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
