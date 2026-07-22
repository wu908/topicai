"""Migration contracts for the first ContentProject calibration slice."""

import shutil
import sqlite3

from app.data.migrations.runner import DEFAULT_MIGRATIONS_DIR, apply


def _tables(conn: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }


def test_content_project_calibration_schema_applies_and_replays(tmp_path):
    db_path = tmp_path / "content-project.db"

    first = apply(db_path, DEFAULT_MIGRATIONS_DIR)
    second = apply(db_path, DEFAULT_MIGRATIONS_DIR)

    assert second == []
    assert any(item.version == "012_content_projects" for item in first)
    assert any(item.version == "014_content_versions" for item in first)
    assert any(item.version == "018_publish_hypotheses" for item in first)
    assert any(item.version == "019_calibration_loop" for item in first)
    assert any(item.version == "020_intent_driven_actions" for item in first)
    assert any(item.version == "021_evidence_items" for item in first)
    assert any(item.version == "022_candidate_segment_reviews" for item in first)
    assert any(item.version == "023_creator_rule_versions" for item in first)
    assert any(item.version == "024_creator_rule_resolutions" for item in first)
    assert any(item.version == "025_creator_viewpoints" for item in first)
    assert any(item.version == "026_creator_series" for item in first)
    assert any(item.version == "028_action_experiment_metrics" for item in first)

    with sqlite3.connect(db_path) as conn:
        tables = _tables(conn)
        assert {
            "content_projects",
            "content_versions",
            "publish_hypotheses",
            "publish_records_v2",
            "performance_snapshots_v2",
            "ai_traces_v2",
            "blind_reviews",
            "observations",
            "observation_events",
            "creator_states",
            "next_best_actions",
            "human_gates",
            "action_events",
            "evidence_items",
            "content_segments",
            "content_segment_decisions",
            "creator_rules",
            "creator_rule_versions",
            "creator_rule_events",
            "creator_rule_resolutions",
            "creator_viewpoints",
            "creator_viewpoint_events",
            "creator_series",
            "creator_series_events",
            "experiments",
            "experiment_assignments",
            "experiment_assignment_events",
        } <= tables
        project_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(content_projects)")
        }
        assert {
            "locked_publish_version_id",
            "publish_hypothesis_id",
            "calibration_state",
            "version",
            "content_intent",
            "content_format",
            "intent_status",
            "automation_level",
        } <= project_columns


def test_intent_action_migration_upgrades_from_019_and_replays(tmp_path):
    db_path = tmp_path / "upgrade.db"
    legacy_dir = tmp_path / "through-019"
    legacy_dir.mkdir()
    for path in DEFAULT_MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"):
        if int(path.name[:3]) <= 19:
            shutil.copy2(path, legacy_dir / path.name)

    apply(db_path, legacy_dir)
    upgraded = apply(db_path, DEFAULT_MIGRATIONS_DIR)
    replay = apply(db_path, DEFAULT_MIGRATIONS_DIR)

    assert [item.version for item in upgraded] == [
        "020_intent_driven_actions",
        "021_evidence_items",
        "022_candidate_segment_reviews",
        "023_creator_rule_versions",
        "024_creator_rule_resolutions",
        "025_creator_viewpoints",
        "026_creator_series",
        "027_content_opportunities",
        "028_action_experiment_metrics",
        "029_starter_domain",
    ]
    assert replay == []
    with sqlite3.connect(db_path) as conn:
        assert {"creator_states", "next_best_actions", "human_gates", "action_events", "evidence_items", "content_segments", "content_segment_decisions", "creator_rules", "creator_rule_versions", "creator_rule_events", "creator_rule_resolutions", "creator_viewpoints", "creator_viewpoint_events", "creator_series", "creator_series_events", "content_opportunities", "content_opportunity_events", "experiments", "experiment_assignments", "experiment_assignment_events", "starter_assessments", "starter_direction_candidates", "starter_sprints"} <= _tables(conn)
        legacy_defaults = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='content_projects'"
        ).fetchone()[0]
        assert "content_intent" in legacy_defaults
        event_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(action_events)")
        }
        assert {
            "experiment_id",
            "cohort",
            "ai_trace_id",
            "latency_ms",
            "success",
            "error_code",
            "model_version",
            "prompt_version",
        } <= event_columns


def test_publish_hypothesis_is_unique_per_project_version(tmp_path):
    db_path = tmp_path / "content-project.db"
    apply(db_path, DEFAULT_MIGRATIONS_DIR)

    with sqlite3.connect(db_path) as conn:
        indexes = {
            row[1]
            for row in conn.execute("PRAGMA index_list(publish_hypotheses)")
            if row[2]
        }
    assert "uq_publish_hypotheses_project_version" in indexes


def test_calibration_rows_have_owner_scoped_idempotency(tmp_path):
    db_path = tmp_path / "content-project.db"
    apply(db_path, DEFAULT_MIGRATIONS_DIR)

    expected_indexes = {
        "publish_records_v2": "uq_publish_records_v2_owner_idempotency",
        "performance_snapshots_v2": "uq_performance_snapshots_v2_owner_idempotency",
        "blind_reviews": "uq_blind_reviews_owner_idempotency",
        "observations": "uq_observations_owner_idempotency",
        "observation_events": "uq_observation_events_owner_idempotency",
    }
    with sqlite3.connect(db_path) as conn:
        for table, expected in expected_indexes.items():
            indexes = {
                row[1]
                for row in conn.execute(f"PRAGMA index_list({table})")
                if row[2]
            }
            assert expected in indexes

        segment_indexes = {
            row[1]
            for row in conn.execute("PRAGMA index_list(content_segment_decisions)")
            if row[2]
        }
        assert "uq_content_segment_decisions_owner_idempotency" in segment_indexes

        rule_indexes = {
            row[1]
            for row in conn.execute("PRAGMA index_list(creator_rule_events)")
            if row[2]
        }
        assert "uq_creator_rule_events_owner_idempotency" in rule_indexes
