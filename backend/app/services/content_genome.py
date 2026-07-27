"""Derived, owner-scoped decision graph for reusable creator knowledge."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from app.services.creator_rule import CreatorRuleService
from app.services.v2_utils import effective_intent_status


class ContentGenomeService:
    """Project active rules and their provenance without duplicating source data."""

    def __init__(self, db: Any):
        self.db = db

    async def for_project(
        self,
        owner_user_id: str,
        project: dict[str, Any] | str,
        *,
        experiment: str | None = None,
    ) -> dict[str, Any]:
        if isinstance(project, str):
            project_row = await self.db.fetch_one(
                "SELECT * FROM content_projects WHERE id=:id AND owner_user_id=:owner "
                "AND deleted_at IS NULL",
                {"id": project, "owner": owner_user_id},
            )
            if project_row is None:
                raise ValueError(f"project not found: {project}")
            project = project_row

        intent_status = effective_intent_status(project)
        content_intent = (
            project.get("retrospective_intent")
            if intent_status == "retrospective"
            else project.get("content_intent")
        )
        return await self.search(
            owner_user_id,
            project_id=project["id"],
            content_intent=(
                None if intent_status == "legacy_unclassified" else content_intent
            ),
            intent_confirmed=intent_status
            in {"working_confirmed", "locked", "retrospective"},
            audience=project.get("target_audience"),
            content_format=project.get("content_format") or project.get("format"),
            experiment=experiment,
        )

    async def search(
        self,
        owner_user_id: str,
        *,
        project_id: str | None = None,
        content_intent: str | None = None,
        intent_confirmed: bool = True,
        audience: str | None = None,
        content_format: str | None = None,
        experiment: str | None = None,
    ) -> dict[str, Any]:
        query = {
            "content_intent": self._normalized_text(content_intent),
            "intent_confirmed": intent_confirmed,
            "audience": self._normalized_text(audience),
            "format": self._normalized_text(content_format),
            "experiment": self._normalized_text(experiment),
        }
        rules = await CreatorRuleService(self.db).list(owner_user_id)
        observations = await self.db.fetch_all(
            "SELECT * FROM observations WHERE owner_user_id=:owner",
            {"owner": owner_user_id},
        )
        observations_by_id = {item["id"]: self._normalize_observation(item) for item in observations}
        state_row = await self.db.fetch_one(
            "SELECT validated_insights_json FROM creator_states WHERE owner_user_id=:owner",
            {"owner": owner_user_id},
        )
        validated_insights = json.loads(
            (state_row or {}).get("validated_insights_json") or "[]"
        )
        all_evidence_rows = await self.db.fetch_all(
            "SELECT * FROM evidence_items WHERE owner_user_id=:owner",
            {"owner": owner_user_id},
        )
        evidence_by_id = {
            item["id"]: self._normalize_evidence(item) for item in all_evidence_rows
        }
        evidence_items = [
            item
            for item in evidence_by_id.values()
            if item["confirmation_status"] == "confirmed"
            and (
                item["project_id"] == project_id
                or (item["reusable"] and item["privacy_level"] != "sensitive")
            )
        ]
        viewpoint_rows = await self.db.fetch_all(
            "SELECT * FROM creator_viewpoints WHERE owner_user_id=:owner "
            "AND status='confirmed'",
            {"owner": owner_user_id},
        )
        viewpoints = [self._normalize_viewpoint(item) for item in viewpoint_rows]
        series_rows = await self.db.fetch_all(
            "SELECT * FROM creator_series WHERE owner_user_id=:owner "
            "AND status='confirmed'",
            {"owner": owner_user_id},
        )
        series_items = [self._normalize_series(item) for item in series_rows]
        publish_rows = await self.db.fetch_all(
            "SELECT DISTINCT project_id FROM publish_records_v2 WHERE owner_user_id=:owner",
            {"owner": owner_user_id},
        )
        published_project_ids = {item["project_id"] for item in publish_rows}
        project_rows = await self.db.fetch_all(
            "SELECT id,title,content_intent,content_format,status,locked_publish_version_id,"
            "archived_at FROM content_projects "
            "WHERE owner_user_id=:owner AND deleted_at IS NULL",
            {"owner": owner_user_id},
        )
        projects_by_id = {item["id"]: dict(item) for item in project_rows}

        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        decision_context: list[dict[str, Any]] = []
        evidence_context: list[dict[str, Any]] = []
        viewpoint_context: list[dict[str, Any]] = []
        series_context: list[dict[str, Any]] = []
        insight_context: list[dict[str, Any]] = []
        included_observations: set[str] = set()
        included_evidence: set[str] = set()
        included_projects: set[str] = set()
        relevant_rule_ids: set[str] = set()
        pending_conflict_edges: list[dict[str, Any]] = []

        for rule in rules:
            active = rule.get("active_version")
            if active is None:
                continue
            applicability = CreatorRuleService._applicability(active.get("scope"))
            if query["content_intent"] and applicability["intent"] != query["content_intent"]:
                continue

            status, reason_codes = self._match_status(query, applicability)
            source_ids = list(active.get("source_observation_ids") or [])
            source_observations = [observations_by_id[item] for item in source_ids if item in observations_by_id]
            invalid_sources = [
                item for item in source_observations
                if item["lifecycle_status"] in {"refuted", "archived"}
            ]
            if len(source_observations) != len(source_ids) or len(source_ids) < CreatorRuleService.MIN_SAMPLES:
                status = "needs_review"
                reason_codes.append("insufficient_or_missing_provenance")
            elif invalid_sources:
                status = "needs_review"
                reason_codes.append("source_observation_no_longer_valid")

            conflicts = rule.get("conflicts") or []
            if any(item["status"] == "open" for item in conflicts):
                status = "conflicted"
                reason_codes.append("unresolved_rule_conflict")
            elif conflicts:
                status = "needs_context"
                reason_codes.append("acknowledged_exception_requires_context")

            node_id = self._rule_node_id(rule["id"], active["version_number"])
            source_project_refs = sorted(
                {
                    project_ref
                    for observation in source_observations
                    for project_ref in observation["support_project_refs"]
                }
            )
            node = {
                "id": node_id,
                "node_type": "creator_rule",
                "rule_id": rule["id"],
                "rule_version_id": active["id"],
                "version_number": active["version_number"],
                "statement": active["statement"],
                "content_intent": rule["content_intent"],
                "applicability": applicability,
                "source_observation_ids": source_ids,
                "source_project_refs": source_project_refs,
                "sample_count": len(source_ids),
                "status": status,
                "reason_codes": sorted(set(reason_codes)),
            }
            nodes.append(node)
            relevant_rule_ids.add(rule["id"])

            for observation in source_observations:
                observation_id = observation["id"]
                edges.append(
                    {
                        "id": f"{node_id}:supported-by:{observation_id}",
                        "edge_type": "supported_by",
                        "from_node_id": node_id,
                        "to_node_id": f"observation:{observation_id}",
                        "status": "active",
                    }
                )
                if observation_id not in included_observations:
                    nodes.append(
                        {
                            "id": f"observation:{observation_id}",
                            "node_type": "observation",
                            "observation_id": observation_id,
                            "statement": observation["statement"],
                            "lifecycle_status": observation["lifecycle_status"],
                            "support_project_refs": observation["support_project_refs"],
                        }
                    )
                    included_observations.add(observation_id)
                for project_ref in observation["support_project_refs"]:
                    self._add_project_node(
                        nodes, projects_by_id, included_projects, project_ref
                    )
                    edges.append(
                        {
                            "id": f"observation:{observation_id}:observed-in:{project_ref}",
                            "edge_type": "observed_in",
                            "from_node_id": f"observation:{observation_id}",
                            "to_node_id": f"content-project:{project_ref}",
                            "status": "active",
                        }
                    )

            for conflict in conflicts:
                left, right = sorted((rule["id"], conflict["rule_id"]))
                pending_conflict_edges.append(
                    {
                        "id": f"creator-rule-conflict:{left}:{right}",
                        "edge_type": "exception_to" if conflict["status"] == "acknowledged" else "conflicts_with",
                        "from_rule_id": left,
                        "to_rule_id": right,
                        "status": conflict["status"],
                        "resolution_ref": (
                            f"creator-rule-resolution:{conflict['resolution']['id']}"
                            if conflict.get("resolution")
                            else None
                        ),
                    }
                )

            if status == "applicable":
                decision_context.append(
                    {
                        "source_ref": f"creator-rule:{rule['id']}:v{active['version_number']}",
                        "statement": active["statement"],
                        "content_intent": rule["content_intent"],
                        "applicability": applicability,
                        "evidence_refs": [f"observation:{item}" for item in source_ids],
                        "source_project_refs": source_project_refs,
                        "sample_count": len(source_ids),
                        "reason": "confirmed_rule_matches_project_context",
                    }
                )

        for evidence in evidence_items:
            source_project = projects_by_id.get(evidence["project_id"])
            is_current_project = evidence["project_id"] == project_id
            if not is_current_project and query["content_intent"]:
                if not source_project or self._normalized_text(
                    source_project.get("content_intent")
                ) != query["content_intent"]:
                    continue
                source_format = self._normalized_text(
                    source_project.get("content_format")
                )
                if query["format"] and source_format and source_format != query["format"]:
                    continue

            evidence_id = evidence["id"]
            node_id = f"evidence:{evidence_id}"
            self._add_evidence_node(
                nodes, included_evidence, evidence, "applicable"
            )
            self._add_project_node(
                nodes, projects_by_id, included_projects, evidence["project_id"]
            )
            edges.append(
                {
                    "id": f"{node_id}:belongs-to:{evidence['project_id']}",
                    "edge_type": "belongs_to",
                    "from_node_id": node_id,
                    "to_node_id": f"content-project:{evidence['project_id']}",
                    "status": "active",
                }
            )
            evidence_context.append(
                {
                    "source_ref": f"evidence:{evidence_id}",
                    "statement": evidence["statement"],
                    "source_type": evidence["source_type"],
                    "privacy_level": evidence["privacy_level"],
                    "project_id": evidence["project_id"],
                    "reusable": evidence["reusable"],
                    "reason": (
                        "current_project_confirmed"
                        if is_current_project
                        else "confirmed_reusable_same_intent"
                    ),
                }
            )

        for viewpoint in viewpoints:
            if query["content_intent"] and self._normalized_text(
                viewpoint["content_intent"]
            ) != query["content_intent"]:
                continue
            if viewpoint["privacy_level"] == "sensitive" and viewpoint["project_id"] != project_id:
                continue
            applicability = CreatorRuleService._applicability(viewpoint["scope"])
            status, reason_codes = self._match_status(query, applicability)
            source_ids = viewpoint["source_evidence_ids"]
            source_items = [evidence_by_id[item] for item in source_ids if item in evidence_by_id]
            if len(source_items) != len(source_ids) or any(
                item["confirmation_status"] != "confirmed" for item in source_items
            ):
                status = "needs_review"
                reason_codes.append("source_evidence_no_longer_valid")

            node_id = f"creator-viewpoint:{viewpoint['id']}"
            nodes.append(
                {
                    "id": node_id,
                    "node_type": "viewpoint",
                    "viewpoint_id": viewpoint["id"],
                    "statement": viewpoint["confirmed_statement"],
                    "rationale": viewpoint["proposed_rationale"],
                    "content_intent": viewpoint["content_intent"],
                    "applicability": applicability,
                    "source_evidence_ids": source_ids,
                    "project_id": viewpoint["project_id"],
                    "privacy_level": viewpoint["privacy_level"],
                    "status": status,
                    "reason_codes": sorted(set(reason_codes)),
                }
            )
            self._add_project_node(
                nodes, projects_by_id, included_projects, viewpoint["project_id"]
            )
            edges.append(
                {
                    "id": f"{node_id}:belongs-to:{viewpoint['project_id']}",
                    "edge_type": "belongs_to",
                    "from_node_id": node_id,
                    "to_node_id": f"content-project:{viewpoint['project_id']}",
                    "status": "active",
                }
            )
            for evidence in source_items:
                self._add_evidence_node(
                    nodes, included_evidence, evidence, "provenance_only"
                )
                edges.append(
                    {
                        "id": f"{node_id}:derived-from:{evidence['id']}",
                        "edge_type": "derived_from",
                        "from_node_id": node_id,
                        "to_node_id": f"evidence:{evidence['id']}",
                        "status": (
                            "active"
                            if evidence["confirmation_status"] == "confirmed"
                            else "invalidated"
                        ),
                    }
                )
            if status == "applicable":
                viewpoint_context.append(
                    {
                        "source_ref": node_id,
                        "statement": viewpoint["confirmed_statement"],
                        "rationale": viewpoint["proposed_rationale"],
                        "content_intent": viewpoint["content_intent"],
                        "applicability": applicability,
                        "evidence_refs": [f"evidence:{item}" for item in source_ids],
                        "project_id": viewpoint["project_id"],
                        "privacy_level": viewpoint["privacy_level"],
                        "reason": "user_confirmed_viewpoint_matches_project_context",
                    }
                )

        for series in series_items:
            if query["content_intent"] and self._normalized_text(
                series["content_intent"]
            ) != query["content_intent"]:
                continue
            if query["format"] and self._normalized_text(
                series["content_format"]
            ) != query["format"]:
                continue
            applicability = CreatorRuleService._applicability(series["scope"])
            status, reason_codes = self._match_status(query, applicability)
            source_ids = series["source_project_ids"]
            source_projects = [
                projects_by_id[item] for item in source_ids if item in projects_by_id
            ]
            if len(source_projects) != len(source_ids) or any(
                item.get("archived_at")
                or item["status"] not in {"published", "awaiting_review", "settled"}
                or not item.get("locked_publish_version_id")
                or item["id"] not in published_project_ids
                for item in source_projects
            ):
                status = "needs_review"
                reason_codes.append("source_project_no_longer_valid")

            node_id = f"creator-series:{series['id']}"
            nodes.append(
                {
                    "id": node_id,
                    "node_type": "series",
                    "series_id": series["id"],
                    "name": series["confirmed_name"],
                    "promise": series["confirmed_promise"],
                    "continuation_prompt": series["confirmed_continuation_prompt"],
                    "rationale": series["proposed_rationale"],
                    "content_intent": series["content_intent"],
                    "content_format": series["content_format"],
                    "applicability": applicability,
                    "source_project_ids": source_ids,
                    "status": status,
                    "reason_codes": sorted(set(reason_codes)),
                }
            )
            for source_project_id in source_ids:
                source_project = projects_by_id.get(source_project_id)
                self._add_project_node(
                    nodes, projects_by_id, included_projects, source_project_id
                )
                edges.append(
                    {
                        "id": f"content-project:{source_project_id}:part-of:{series['id']}",
                        "edge_type": "part_of",
                        "from_node_id": f"content-project:{source_project_id}",
                        "to_node_id": node_id,
                        "status": (
                            "active"
                            if source_project_id in published_project_ids
                            and source_project
                            and not source_project.get("archived_at")
                            and source_project["status"]
                            in {"published", "awaiting_review", "settled"}
                            and source_project.get("locked_publish_version_id")
                            else "invalidated"
                        ),
                    }
                )
            if status == "applicable":
                series_context.append(
                    {
                        "source_ref": node_id,
                        "name": series["confirmed_name"],
                        "promise": series["confirmed_promise"],
                        "continuation_prompt": series["confirmed_continuation_prompt"],
                        "rationale": series["proposed_rationale"],
                        "content_intent": series["content_intent"],
                        "content_format": series["content_format"],
                        "applicability": applicability,
                        "source_project_refs": source_ids,
                        "reason": "user_confirmed_series_matches_project_context",
                    }
                )

        for insight in validated_insights:
            source_ref = str(insight.get("source_ref") or "")
            if not source_ref.startswith("observation:"):
                continue
            observation_id = source_ref.removeprefix("observation:")
            observation = observations_by_id.get(observation_id)
            status = (
                "applicable"
                if observation
                and observation["user_decision"] == "confirmed"
                and observation["lifecycle_status"] not in {"refuted", "archived"}
                and (
                    not query["content_intent"]
                    or self._normalized_text(
                        observation.get("scope", {}).get("content_intent")
                    )
                    in {"", query["content_intent"]}
                )
                else "needs_review"
            )
            node_id = f"validated-insight:{observation_id}"
            nodes.append(
                {
                    "id": node_id,
                    "node_type": "validated_insight",
                    "observation_id": observation_id,
                    "statement": insight.get("statement", ""),
                    "project_id": insight.get("project_id"),
                    "status": status,
                    "reason_codes": (
                        [] if status == "applicable" else ["source_observation_no_longer_valid"]
                    ),
                }
            )
            if observation:
                if not any(item["id"] == f"observation:{observation_id}" for item in nodes):
                    nodes.append(
                        {
                            "id": f"observation:{observation_id}",
                            "node_type": "observation",
                            "statement": observation["statement"],
                            "project_id": observation["project_id"],
                            "status": observation["lifecycle_status"],
                        }
                    )
                edges.append(
                    {
                        "id": f"{node_id}:derived-from:{observation_id}",
                        "edge_type": "derived_from",
                        "from_node_id": node_id,
                        "to_node_id": f"observation:{observation_id}",
                        "status": "active" if status == "applicable" else "invalidated",
                    }
                )
            if status == "applicable":
                insight_context.append(
                    {
                        "source_ref": source_ref,
                        "statement": insight.get("statement", ""),
                        "project_id": insight.get("project_id"),
                        "scope": insight.get("scope", {}),
                        "reason": "user_confirmed_review_insight",
                    }
                )

        seen_edges: set[str] = set()
        for edge in pending_conflict_edges:
            if (
                edge["from_rule_id"] in relevant_rule_ids
                and edge["to_rule_id"] in relevant_rule_ids
                and edge["id"] not in seen_edges
            ):
                edges.append(edge)
                seen_edges.add(edge["id"])

        nodes.sort(key=lambda item: item["id"])
        edges.sort(key=lambda item: item["id"])
        decision_context.sort(key=lambda item: item["source_ref"])
        evidence_context.sort(key=lambda item: item["source_ref"])
        viewpoint_context.sort(key=lambda item: item["source_ref"])
        series_context.sort(key=lambda item: item["source_ref"])
        insight_context.sort(key=lambda item: item["source_ref"])
        fingerprint_payload = [
            {
                "id": item["id"],
                "status": item.get("status"),
                "reason_codes": item.get("reason_codes", []),
            }
            for item in nodes
            if item["node_type"] == "creator_rule"
        ] + [
            {"id": item["id"], "status": item["status"]}
            for item in edges
            if item["edge_type"] in {"conflicts_with", "exception_to"}
        ] + [
            {
                "id": item["id"],
                "status": item.get("status"),
                "project_id": item.get("project_id"),
            }
            for item in nodes
            if item["node_type"] == "evidence"
        ] + [
            {
                "id": item["id"],
                "status": item.get("status"),
                "reason_codes": item.get("reason_codes", []),
            }
            for item in nodes
            if item["node_type"] == "viewpoint"
        ] + [
            {
                "id": item["id"],
                "status": item.get("status"),
                "reason_codes": item.get("reason_codes", []),
            }
            for item in nodes
            if item["node_type"] == "series"
        ] + [
            {
                "id": item["id"],
                "status": item.get("status"),
                "reason_codes": item.get("reason_codes", []),
            }
            for item in nodes
            if item["node_type"] == "validated_insight"
        ]
        fingerprint = hashlib.sha256(
            json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        rule_nodes = [item for item in nodes if item["node_type"] == "creator_rule"]

        return {
            "project_id": project_id,
            "query": query,
            "fingerprint": fingerprint,
            "nodes": nodes,
            "edges": edges,
            "decision_context": decision_context,
            "evidence_context": evidence_context,
            "viewpoint_context": viewpoint_context,
            "series_context": series_context,
            "insight_context": insight_context,
            "summary": {
                "relevant_rule_count": len(rule_nodes),
                "applicable_rule_count": len(decision_context),
                "withheld_rule_count": len(rule_nodes) - len(decision_context),
                "open_conflict_count": sum(
                    1 for item in edges if item["edge_type"] == "conflicts_with"
                ),
                "applicable_evidence_count": len(evidence_context),
                "applicable_viewpoint_count": len(viewpoint_context),
                "applicable_series_count": len(series_context),
                "applicable_insight_count": len(insight_context),
            },
        }

    @classmethod
    def _match_status(
        cls, query: dict[str, Any], applicability: dict[str, str]
    ) -> tuple[str, list[str]]:
        reasons: list[str] = []
        if not query["content_intent"] or not query["intent_confirmed"]:
            reasons.append("unconfirmed_content_intent")
        for field in ("audience", "format"):
            if applicability[field] and not query[field]:
                reasons.append(f"missing_{field}_context")
            elif applicability[field] and applicability[field] != query[field]:
                return "not_applicable", [f"{field}_scope_mismatch"]
        if (
            applicability["experiment"]
            and query["experiment"]
            and applicability["experiment"] != query["experiment"]
        ):
            return "not_applicable", ["experiment_scope_mismatch"]
        return ("needs_context", reasons) if reasons else ("applicable", [])

    @staticmethod
    def _normalized_text(value: Any) -> str:
        return CreatorRuleService._normalized_text(value)

    @staticmethod
    def _normalize_observation(row: dict[str, Any]) -> dict[str, Any]:
        result = dict(row)
        result["support_project_refs"] = json.loads(
            result.pop("support_project_refs_json") or "[]"
        )
        result["counterexample_refs"] = json.loads(
            result.pop("counterexample_refs_json") or "[]"
        )
        result["scope"] = json.loads(result.pop("scope_json") or "{}")
        return result

    @staticmethod
    def _normalize_evidence(row: dict[str, Any]) -> dict[str, Any]:
        result = dict(row)
        result["reusable"] = bool(result["reusable"])
        return result

    @staticmethod
    def _normalize_viewpoint(row: dict[str, Any]) -> dict[str, Any]:
        result = dict(row)
        result["scope"] = json.loads(result.pop("scope_json") or "{}")
        result["source_evidence_ids"] = json.loads(
            result.pop("source_evidence_ids_json") or "[]"
        )
        result["limitations"] = json.loads(result.pop("limitations_json") or "[]")
        return result

    @staticmethod
    def _normalize_series(row: dict[str, Any]) -> dict[str, Any]:
        result = dict(row)
        result["scope"] = json.loads(result.pop("scope_json") or "{}")
        result["source_project_ids"] = json.loads(
            result.pop("source_project_ids_json") or "[]"
        )
        result["limitations"] = json.loads(result.pop("limitations_json") or "[]")
        return result

    @staticmethod
    def _add_evidence_node(
        nodes: list[dict[str, Any]],
        included_evidence: set[str],
        evidence: dict[str, Any],
        status: str,
    ) -> None:
        if evidence["id"] in included_evidence:
            return
        nodes.append(
            {
                "id": f"evidence:{evidence['id']}",
                "node_type": "evidence",
                "evidence_id": evidence["id"],
                "statement": evidence["statement"],
                "source_type": evidence["source_type"],
                "privacy_level": evidence["privacy_level"],
                "project_id": evidence["project_id"],
                "reusable": evidence["reusable"],
                "confirmation_status": evidence["confirmation_status"],
                "status": status,
            }
        )
        included_evidence.add(evidence["id"])

    @staticmethod
    def _add_project_node(
        nodes: list[dict[str, Any]],
        projects_by_id: dict[str, dict[str, Any]],
        included_projects: set[str],
        project_id: str,
    ) -> None:
        if project_id in included_projects or project_id not in projects_by_id:
            return
        project = projects_by_id[project_id]
        nodes.append(
            {
                "id": f"content-project:{project_id}",
                "node_type": "content_project",
                "project_id": project_id,
                "title": project["title"],
                "content_intent": project["content_intent"],
                "content_format": project["content_format"],
                "status": project["status"],
            }
        )
        included_projects.add(project_id)

    @staticmethod
    def _rule_node_id(rule_id: str, version_number: int) -> str:
        return f"creator-rule:{rule_id}:v{version_number}"
