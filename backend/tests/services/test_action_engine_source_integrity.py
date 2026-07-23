"""Regression guard for the action engine's source boundary."""

import ast
from pathlib import Path


ACTION_ENGINE_MODULES = (
    "ai_trace.py",
    "content_genome.py",
    "content_opportunity.py",
    "creator_series.py",
    "creator_state.py",
    "creator_viewpoint.py",
    "direction_candidate.py",
    "evidence.py",
    "intent_actions.py",
    "intent_orchestrator.py",
)
FORBIDDEN_MODULE_PREFIXES = (
    "app.data_sources",
    "app.config.data_source_config",
    "app.services.topic_recommend",
)
FORBIDDEN_SYMBOLS = {
    "DataManager",
    "LLMDataSource",
    "TianAPISource",
    "BilibiliSource",
    "PreloadedDataSource",
}


def test_action_engine_does_not_import_or_reference_legacy_hotspot_sources():
    services = Path(__file__).resolve().parents[2] / "app" / "services"
    violations: list[str] = []

    for filename in ACTION_ENGINE_MODULES:
        path = services / filename
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(FORBIDDEN_MODULE_PREFIXES):
                        violations.append(f"{filename}:{node.lineno}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith(FORBIDDEN_MODULE_PREFIXES):
                    violations.append(f"{filename}:{node.lineno}: from {module}")
                for alias in node.names:
                    if alias.name in FORBIDDEN_SYMBOLS:
                        violations.append(f"{filename}:{node.lineno}: import {alias.name}")
            elif isinstance(node, ast.Name) and node.id in FORBIDDEN_SYMBOLS:
                violations.append(f"{filename}:{node.lineno}: reference {node.id}")

    assert violations == []
