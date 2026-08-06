"""Migration contracts for the first ContentProject calibration slice."""

import json
import shutil
import sqlite3

import pytest

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
    assert any(item.version == "032_source_verification_opportunities" for item in first)
    assert any(item.version == "033_calibration_completeness" for item in first)
    assert any(item.version == "035_intent_lock_action" for item in first)
    assert any(item.version == "041_project_state_events" for item in first)

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
            "publish_hypothesis_amendments",
            "benchmark_samples",
            "benchmark_sample_events",
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
            "project_state_events",
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

        event_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(project_state_events)")
        }
        assert {
            "owner_user_id",
            "project_id",
            "from_status",
            "to_status",
            "reason",
            "actor_type",
            "project_version",
            "idempotency_key",
            "request_hash",
            "created_at",
        } <= event_columns


def test_project_state_event_migration_recovers_after_ddl_before_version_record(
    tmp_path,
):
    db_path = tmp_path / "project-state-event-recovery.db"
    through_040 = tmp_path / "through-040"
    through_040.mkdir()
    for path in DEFAULT_MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"):
        if int(path.name[:3]) <= 40:
            shutil.copy2(path, through_040 / path.name)

    apply(db_path, through_040)
    migration = DEFAULT_MIGRATIONS_DIR / "041_project_state_events.sql"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(migration.read_text(encoding="utf-8"))

    upgraded = apply(db_path, DEFAULT_MIGRATIONS_DIR)
    replay = apply(db_path, DEFAULT_MIGRATIONS_DIR)

    assert [item.version for item in upgraded] == [
        "041_project_state_events",
        "042_growth_onboarding",
        "043_first_party_opportunities",
        "044_repair_opportunity_sources",
        "045_drop_legacy_v1_tables",
    ]
    assert replay == []


def test_capability_trust_migration_recovers_after_ddl_before_version_record(tmp_path):
    db_path = tmp_path / "capability-trust-recovery.db"
    through_036 = tmp_path / "through-036"
    through_036.mkdir()
    for path in DEFAULT_MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"):
        if int(path.name[:3]) <= 36:
            shutil.copy2(path, through_036 / path.name)

    apply(db_path, through_036)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "ALTER TABLE creator_states ADD COLUMN "
            "capability_trust_json TEXT NOT NULL DEFAULT '{}'"
        )

    upgraded = apply(db_path, DEFAULT_MIGRATIONS_DIR)
    replay = apply(db_path, DEFAULT_MIGRATIONS_DIR)

    assert [item.version for item in upgraded] == [
        "037_capability_trust",
        "038_scope_learning_action",
        "039_observation_window_action",
        "040_unavailable_performance_result",
        "041_project_state_events",
        "042_growth_onboarding",
        "043_first_party_opportunities",
        "044_repair_opportunity_sources",
        "045_drop_legacy_v1_tables",
    ]
    assert replay == []


def test_unavailable_result_migration_recovers_after_partial_ddl(tmp_path):
    db_path = tmp_path / "unavailable-result-recovery.db"
    through_039 = tmp_path / "through-039"
    through_039.mkdir()
    for path in DEFAULT_MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"):
        if int(path.name[:3]) <= 39:
            shutil.copy2(path, through_039 / path.name)

    apply(db_path, through_039)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "ALTER TABLE performance_snapshots_v2 ADD COLUMN "
            "result_availability TEXT NOT NULL DEFAULT 'observed' "
            "CHECK (result_availability IN ('observed','unavailable'))"
        )

    upgraded = apply(db_path, DEFAULT_MIGRATIONS_DIR)
    replay = apply(db_path, DEFAULT_MIGRATIONS_DIR)

    assert [item.version for item in upgraded] == [
        "040_unavailable_performance_result",
        "041_project_state_events",
        "042_growth_onboarding",
        "043_first_party_opportunities",
        "044_repair_opportunity_sources",
        "045_drop_legacy_v1_tables",
    ]
    assert replay == []
    with sqlite3.connect(db_path) as conn:
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(performance_snapshots_v2)")
        }
    assert {"result_availability", "unavailable_reason"} <= columns


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
        "030_action_lifecycle",
        "031_trust_boundaries_privacy",
        "032_source_verification_opportunities",
        "033_calibration_completeness",
        "034_intent_model_migration",
        "035_intent_lock_action",
        "036_creator_series_scope",
        "037_capability_trust",
        "038_scope_learning_action",
        "039_observation_window_action",
        "040_unavailable_performance_result",
        "041_project_state_events",
        "042_growth_onboarding",
        "043_first_party_opportunities",
        "044_repair_opportunity_sources",
        "045_drop_legacy_v1_tables",
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
        action_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='next_best_actions'"
        ).fetchone()[0]
        event_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='action_events'"
        ).fetchone()[0]
        assert all(status in action_sql for status in ("'failed'", "'expired'", "'cancelled'"))
        assert all(event in event_sql for event in ("'rejected'", "'failed'", "'expired'", "'cancelled'"))


def test_action_lifecycle_migration_rebuilds_phase_15_constraints(tmp_path):
    db_path = tmp_path / "phase-15.db"
    phase_15_dir = tmp_path / "through-029"
    phase_15_dir.mkdir()
    for path in DEFAULT_MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"):
        if int(path.name[:3]) <= 29:
            target = phase_15_dir / path.name
            shutil.copy2(path, target)
            if path.name.startswith("020_"):
                sql = target.read_text(encoding="utf-8")
                sql = sql.replace(
                    "'proposed','accepted','deferred','completed','superseded',\n"
                    "            'failed','expired','cancelled'",
                    "'proposed','accepted','deferred','completed','superseded'",
                ).replace(
                    "'gate_confirmed','gate_rejected','fallback_used',\n"
                    "        'rejected','failed','expired','cancelled'",
                    "'gate_confirmed','gate_rejected','fallback_used'",
                )
                target.write_text(sql, encoding="utf-8")

    apply(db_path, phase_15_dir)
    upgraded = apply(db_path, DEFAULT_MIGRATIONS_DIR)
    assert [item.version for item in upgraded] == [
        "030_action_lifecycle",
        "031_trust_boundaries_privacy",
        "032_source_verification_opportunities",
        "033_calibration_completeness",
        "034_intent_model_migration",
        "035_intent_lock_action",
        "036_creator_series_scope",
        "037_capability_trust",
        "038_scope_learning_action",
        "039_observation_window_action",
        "040_unavailable_performance_result",
        "041_project_state_events",
        "042_growth_onboarding",
        "043_first_party_opportunities",
        "044_repair_opportunity_sources",
        "045_drop_legacy_v1_tables",
    ]
    with sqlite3.connect(db_path) as conn:
        action_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='next_best_actions'"
        ).fetchone()[0]
        event_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='action_events'"
        ).fetchone()[0]
        assert "'failed','expired','cancelled'" in action_sql
        assert "'rejected','failed','expired','cancelled'" in event_sql
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_source_verification_migration_preserves_series_opportunities(tmp_path):
    db_path = tmp_path / "source-opportunity-upgrade.db"
    through_031 = tmp_path / "through-031"
    through_031.mkdir()
    for path in DEFAULT_MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"):
        if int(path.name[:3]) <= 31:
            shutil.copy2(path, through_031 / path.name)

    apply(db_path, through_031)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute(
            "INSERT INTO users (id,email,username,password_hash,ai_calls_reset_at,created_at) "
            "VALUES ('u1','u1@example.com','u1','hash','2026-07-24T00:00:00Z',"
            "'2026-07-23T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO ai_traces_v2 (id,owner_user_id,task_type,input_refs_json,"
            "policy_version,capability,visibility_boundary_json,contamination_check_json,"
            "calibration_state,output_ref,generated_at) VALUES "
            "('trace-1','u1','series_extension','[]','v1','structured_proposal','{}','{}',"
            "'insufficient','content-opportunity:op-1','2026-07-23T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO content_opportunities (id,owner_user_id,opportunity_type,source_ref,"
            "content_intent,content_format,proposed_title,proposed_audience_change,"
            "proposed_rationale,proposed_material_requirements_json,evidence_refs_json,"
            "unknown_refs_json,status,proposal_source,ai_trace_id,limitations_json,version,"
            "idempotency_key,request_hash,created_at,updated_at) VALUES "
            "('op-1','u1','series_extension','creator-series:s1','share','graphic_note',"
            "'Next note','Reader change','Series continuation','[]','[]','[]','proposed',"
            "'deterministic_fallback','trace-1','[]',1,'op-key','op-hash',"
            "'2026-07-23T00:00:00Z','2026-07-23T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO content_opportunity_events (id,owner_user_id,opportunity_id,"
            "event_type,to_status,opportunity_version,idempotency_key,request_hash,created_at) "
            "VALUES ('event-1','u1','op-1','proposed','proposed',1,'event-key','event-hash',"
            "'2026-07-23T00:00:00Z')"
        )
        conn.commit()

    upgraded = apply(db_path, DEFAULT_MIGRATIONS_DIR)
    assert [item.version for item in upgraded] == [
        "032_source_verification_opportunities",
        "033_calibration_completeness",
        "034_intent_model_migration",
        "035_intent_lock_action",
        "036_creator_series_scope",
        "037_capability_trust",
        "038_scope_learning_action",
        "039_observation_window_action",
        "040_unavailable_performance_result",
        "041_project_state_events",
        "042_growth_onboarding",
        "043_first_party_opportunities",
        "044_repair_opportunity_sources",
        "045_drop_legacy_v1_tables",
    ]
    with sqlite3.connect(db_path) as conn:
        opportunity = conn.execute(
            "SELECT opportunity_type,verification_status,source_refs_json,dimensions_json "
            "FROM content_opportunities "
            "WHERE id='op-1'"
        ).fetchone()
        event_count = conn.execute(
            "SELECT COUNT(*) FROM content_opportunity_events WHERE opportunity_id='op-1'"
        ).fetchone()[0]
        table_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='content_opportunities'"
        ).fetchone()[0]
        assert opportunity[:2] == ("series_extension", "verified")
        source_refs = json.loads(opportunity[2])
        assert source_refs[0]["ref_type"] == "creator_series"
        assert source_refs[0]["entity_id"] == "s1"
        assert set(json.loads(opportunity[3])) == {
            "audience_fit",
            "creator_fit",
            "material_readiness",
            "growth_role",
            "series_potential",
            "timeliness",
            "similarity_risk",
            "safety_risk",
        }
        assert event_count == 1
        assert "'user_source'" in table_sql
        assert "'pending_verification'" in table_sql
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

        conn.execute(
            "UPDATE content_opportunities SET dimensions_json="
            "'{\"audience_fit\":\"strong\"}',source_trigger='official_inspiration',"
            "expires_at='2026-08-07T00:00:00Z',source_refs_json="
            "'[{\"ref_type\":\"creator_series\"}]' WHERE id='op-1'"
        )
        conn.execute(
            "DELETE FROM schema_migrations WHERE version='043_first_party_opportunities'"
        )
        conn.commit()

    repaired = apply(db_path, DEFAULT_MIGRATIONS_DIR)
    assert [item.version for item in repaired] == ["043_first_party_opportunities"]
    with sqlite3.connect(db_path) as conn:
        preserved = conn.execute(
            "SELECT dimensions_json,source_trigger,expires_at,source_refs_json "
            "FROM content_opportunities WHERE id='op-1'"
        ).fetchone()
        assert preserved == (
            '{"audience_fit":"strong"}',
            "official_inspiration",
            "2026-08-07T00:00:00Z",
            '[{"ref_type":"creator_series"}]',
        )
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


@pytest.mark.asyncio
async def test_first_party_migration_keeps_legacy_manual_url_verifiable(tmp_path):
    from app.core.database import Database
    from app.models.v2.content_opportunity import OpportunitySourceVerification
    from app.services.content_opportunity import ContentOpportunityService

    db_path = tmp_path / "legacy-manual-opportunity.db"
    through_042 = tmp_path / "through-042"
    through_042.mkdir()
    for path in DEFAULT_MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"):
        if int(path.name[:3]) <= 42:
            shutil.copy2(path, through_042 / path.name)

    apply(db_path, through_042)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute(
            "INSERT INTO users (id,email,username,password_hash,ai_calls_reset_at,created_at) "
            "VALUES ('u1','u1@example.com','u1','hash','2026-07-24T00:00:00Z',"
            "'2026-07-23T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO ai_traces_v2 (id,owner_user_id,task_type,input_refs_json,"
            "policy_version,capability,visibility_boundary_json,contamination_check_json,"
            "calibration_state,output_ref,generated_at) VALUES "
            "('trace-manual','u1','manual_opportunity','[]','v1','manual_intake','{}','{}',"
            "'insufficient','content-opportunity:manual-1','2026-07-23T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO content_opportunities (id,owner_user_id,opportunity_type,source_ref,"
            "source_excerpt,source_url,source_published_at,source_authority,verification_status,"
            "content_intent,content_format,proposed_title,proposed_audience_change,"
            "proposed_rationale,proposed_material_requirements_json,evidence_refs_json,"
            "unknown_refs_json,status,proposal_source,ai_trace_id,limitations_json,version,"
            "idempotency_key,request_hash,created_at,updated_at) VALUES "
            "('manual-1','u1','user_source','user-source:manual-1','Official update',"
            "'https://example.com/source','2026-07-23T00:00:00Z','Example','pending_verification',"
            "'share','graphic_note','Official update','Explain the update','Needs verification',"
            "'[]','[]','[]','proposed','deterministic_fallback','trace-manual','[]',1,"
            "'manual-key','manual-hash','2026-07-23T00:00:00Z','2026-07-23T00:00:00Z')"
        )
        conn.commit()

    apply(db_path, DEFAULT_MIGRATIONS_DIR)
    db = Database(f"sqlite+aiosqlite:///{db_path.as_posix()}")
    await db.init_db()
    try:
        verified, _ = await ContentOpportunityService(db).verify_source(
            "u1",
            "manual-1",
            OpportunitySourceVerification(
                verification_status="verified",
                original_url="https://example.com/source",
                published_at="2026-07-23T00:00:00Z",
                authoritative_source="Example",
                timeliness="current",
                confirmed_by_user=True,
                expected_opportunity_version=1,
                idempotency_key="verify-legacy-manual",
            ),
        )
    finally:
        await db.close()

    assert verified["source_refs"][0]["ref_type"] == "user_url"


def test_privacy_migration_preserves_existing_project_gate(tmp_path):
    db_path = tmp_path / "gate-upgrade.db"
    through_030 = tmp_path / "through-030"
    through_030.mkdir()
    for path in DEFAULT_MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"):
        if int(path.name[:3]) <= 30:
            shutil.copy2(path, through_030 / path.name)

    apply(db_path, through_030)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute(
            "INSERT INTO users (id,email,username,password_hash,ai_calls_reset_at,created_at) "
            "VALUES ('u1','u1@example.com','u1','hash','2026-07-24T00:00:00Z','2026-07-23T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO content_projects (id,owner_user_id,title,status,primary_goal,"
            "target_audience,last_action_at,created_at,updated_at) VALUES "
            "('p1','u1','Existing project','ready_to_publish','stable_publish',"
            "'Creators','2026-07-23T00:00:00Z','2026-07-23T00:00:00Z','2026-07-23T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO next_best_actions (id,owner_user_id,project_id,action_type,title,reason,"
            "estimated_effort_minutes,human_gate_type,fallback_action_json,status,version,"
            "idempotency_key,request_hash,created_at,updated_at) VALUES "
            "('a1','u1','p1','record_publication','Record','Manual',2,'publication','{}',"
            "'proposed',1,'action-key','action-hash','2026-07-23T00:00:00Z','2026-07-23T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO human_gates (id,owner_user_id,project_id,action_id,gate_type,prompt,"
            "payload_json,status,decision_payload_json,version,idempotency_key,request_hash,"
            "decided_at,created_at,updated_at) VALUES "
            "('g1','u1','p1','a1','publication','Confirm','{\"legacy\":true}','confirmed',"
            "'{\"confirmed\":true}',2,'gate-key','gate-hash','2026-07-23T00:00:00Z',"
            "'2026-07-23T00:00:00Z','2026-07-23T00:00:00Z')"
        )
        conn.commit()

    apply(db_path, DEFAULT_MIGRATIONS_DIR)
    with sqlite3.connect(db_path) as conn:
        gate = conn.execute(
            "SELECT project_id,action_id,gate_type,payload_json,status,"
            "decision_payload_json,version,idempotency_key,request_hash,decided_at "
            "FROM human_gates WHERE id='g1'"
        ).fetchone()
    assert gate == (
        "p1", "a1", "publication", '{"legacy":true}', "confirmed",
        '{"confirmed":true}', 2, "gate-key", "gate-hash", "2026-07-23T00:00:00Z"
    )


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
        "publish_hypothesis_amendments": "uq_hypothesis_amendments_owner_idempotency",
        "benchmark_samples": "uq_benchmark_samples_owner_idempotency",
        "benchmark_sample_events": "uq_benchmark_sample_events_owner_idempotency",
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


def test_calibration_completeness_enforces_locked_hypothesis_fields(tmp_path):
    db_path = tmp_path / "calibration-completeness.db"
    apply(db_path, DEFAULT_MIGRATIONS_DIR)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO users (id,email,username,password_hash,ai_calls_reset_at,created_at) "
            "VALUES ('u1','u1@example.com','u1','hash','','2026-07-23T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO content_projects (id,owner_user_id,title,status,primary_goal,"
            "target_audience,last_action_at,created_at,updated_at) VALUES "
            "('p1','u1','Project','creating','stable_publish','Creators',"
            "'2026-07-23T00:00:00Z','2026-07-23T00:00:00Z','2026-07-23T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO content_versions (id,owner_user_id,project_id,version_number,title,"
            "body_text,content_hash,idempotency_key,request_hash,created_at) VALUES "
            "('v1','u1','p1',1,'Title','Body','hash','version-key','version-hash',"
            "'2026-07-23T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO publish_hypotheses (id,owner_user_id,project_id,content_version_id,"
            "audience_problem,reader_promise,expected_behaviors_json,status,idempotency_key,"
            "request_hash,locked_at,locked_by,created_at) VALUES "
            "('h1','u1','p1','v1','Problem','Promise','[\"save\"]','locked',"
            "'hypothesis-key','hypothesis-hash','2026-07-23T00:00:00Z','u1',"
            "'2026-07-23T00:00:00Z')"
        )
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            conn.execute(
                "UPDATE publish_hypotheses SET reader_promise='Changed' WHERE id='h1'"
            )
        conn.execute("UPDATE publish_hypotheses SET status='superseded' WHERE id='h1'")
        assert conn.execute(
            "SELECT reader_promise,status FROM publish_hypotheses WHERE id='h1'"
        ).fetchone() == ("Promise", "superseded")


def test_intent_model_migration_adds_intent_status_values_and_columns(tmp_path):
    """Verify migration 034 expands intent_status CHECK and adds new columns."""
    db_path = tmp_path / "intent-model.db"
    through_033 = tmp_path / "through-033"
    through_033.mkdir()
    for path in DEFAULT_MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"):
        if int(path.name[:3]) <= 33:
            shutil.copy2(path, through_033 / path.name)

    apply(db_path, through_033)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute(
            "INSERT INTO users (id,email,username,password_hash,ai_calls_reset_at,created_at) "
            "VALUES ('u1','u1@example.com','u1','hash','2026-07-24T00:00:00Z','2026-07-23T00:00:00Z')"
        )
        # Old intent_status='confirmed' works before migration
        conn.execute(
            "INSERT INTO content_projects (id,owner_user_id,title,status,primary_goal,"
            "target_audience,last_action_at,created_at,updated_at,intent_status) VALUES "
            "('p1','u1','Legacy confirmed project','inbox','stable_publish','all',"
            "'2026-07-23T00:00:00Z','2026-07-23T00:00:00Z','2026-07-23T00:00:00Z','confirmed')"
        )
        conn.execute(
            "INSERT INTO next_best_actions (id,owner_user_id,project_id,action_type,title,reason,"
            "estimated_effort_minutes,fallback_action_json,status,version,idempotency_key,"
            "request_hash,created_at,updated_at) VALUES "
            "('a1','u1','p1','confirm_intent','Confirm','Legacy action',2,'{}','proposed',1,"
            "'action-key','action-hash','2026-07-23T00:00:00Z','2026-07-23T00:00:00Z')"
        )
        conn.commit()

    # Apply 034 and its follow-up for databases that may already have recorded 034.
    upgraded = apply(db_path, DEFAULT_MIGRATIONS_DIR)
    replay = apply(db_path, DEFAULT_MIGRATIONS_DIR)
    assert any(item.version == "034_intent_model_migration" for item in upgraded)
    assert any(item.version == "035_intent_lock_action" for item in upgraded)
    assert replay == []

    with sqlite3.connect(db_path) as conn:
        # Verify new columns exist
        project_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(content_projects)")
        }
        assert "intent_locked_at" in project_columns
        assert "retrospective_intent" in project_columns

        hypothesis_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(publish_hypotheses)")
        }
        assert "content_intent" in hypothesis_columns
        assert "audience_change" in hypothesis_columns
        assert "primary_response" in hypothesis_columns
        assert "supporting_responses_json" in hypothesis_columns
        assert "observation_window_days" in hypothesis_columns
        assert "viewpoint_anchor" in hypothesis_columns
        assert "continuation_promise" in hypothesis_columns

        # Verify old status value persists
        old_status = conn.execute(
            "SELECT intent_status FROM content_projects WHERE id='p1'"
        ).fetchone()[0]
        assert old_status == "confirmed"
        conn.execute(
            "UPDATE next_best_actions SET action_type='lock_intent' WHERE id='a1'"
        )
        assert conn.execute(
            "SELECT action_type FROM next_best_actions WHERE id='a1'"
        ).fetchone()[0] == "lock_intent"

        # Test new intent_status values can be written
        conn.execute(
            "INSERT INTO content_projects (id,owner_user_id,title,status,primary_goal,"
            "target_audience,last_action_at,created_at,updated_at,intent_status) VALUES "
            "('p2','u1','Working confirmed project','inbox','stable_publish','all',"
            "'2026-07-23T00:00:00Z','2026-07-23T00:00:00Z','2026-07-23T00:00:00Z',"
            "'working_confirmed')"
        )
        conn.execute(
            "INSERT INTO content_projects (id,owner_user_id,title,status,primary_goal,"
            "target_audience,last_action_at,created_at,updated_at,intent_status,"
            "intent_locked_at) VALUES "
            "('p3','u1','Locked project','ready_to_publish','stable_publish','all',"
            "'2026-07-23T00:00:00Z','2026-07-23T00:00:00Z','2026-07-23T00:00:00Z',"
            "'locked','2026-07-23T12:00:00Z')"
        )
        conn.execute(
            "INSERT INTO content_projects (id,owner_user_id,title,status,primary_goal,"
            "target_audience,last_action_at,created_at,updated_at,intent_status) VALUES "
            "('p4','u1','Legacy unclassified','published','stable_publish','all',"
            "'2026-07-23T00:00:00Z','2026-07-23T00:00:00Z','2026-07-23T00:00:00Z',"
            "'legacy_unclassified')"
        )
        conn.execute(
            "INSERT INTO content_projects (id,owner_user_id,title,status,primary_goal,"
            "target_audience,last_action_at,created_at,updated_at,intent_status,"
            "retrospective_intent,content_intent) VALUES "
            "('p5','u1','Retrospective project','settled','stable_publish','all',"
            "'2026-07-23T00:00:00Z','2026-07-23T00:00:00Z','2026-07-23T00:00:00Z',"
            "'retrospective','share',NULL)"
        )
        assert conn.execute(
            "SELECT content_intent FROM content_projects WHERE id='p5'"
        ).fetchone()[0] is None

        # Verify invalid retrospective_intent is rejected
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "UPDATE content_projects SET retrospective_intent='invalid' WHERE id='p1'"
            )

        # Test new publish_hypotheses columns can be written
        conn.execute(
            "INSERT INTO content_versions (id,owner_user_id,project_id,version_number,title,"
            "body_text,content_hash,idempotency_key,request_hash,created_at) VALUES "
            "('v1','u1','p3',1,'Title','Body','hash','v-key','v-hash','2026-07-23T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO publish_hypotheses (id,owner_user_id,project_id,content_version_id,"
            "audience_problem,reader_promise,expected_behaviors_json,status,idempotency_key,"
            "request_hash,locked_at,locked_by,created_at,content_intent,audience_change,"
            "primary_response,observation_window_days) VALUES "
            "('h1','u1','p3','v1','Problem','Promise','[\"save\"]','locked','h-key','h-hash',"
            "'2026-07-23T00:00:00Z','u1','2026-07-23T00:00:00Z','solve','Understand X',"
            "'save',30)"
        )
        hypothesis = conn.execute(
            "SELECT content_intent,audience_change,primary_response,observation_window_days "
            "FROM publish_hypotheses WHERE id='h1'"
        ).fetchone()
        assert hypothesis == ("solve", "Understand X", "save", 30)


def test_intent_lock_action_migration_upgrades_database_with_034_recorded(tmp_path):
    db_path = tmp_path / "intent-lock-action.db"
    through_034 = tmp_path / "through-034"
    through_034.mkdir()
    for path in DEFAULT_MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"):
        if int(path.name[:3]) <= 34:
            shutil.copy2(path, through_034 / path.name)

    apply(db_path, through_034)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys=OFF")
        action_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='next_best_actions'"
        ).fetchone()[0]
        dependent_sql = [
            row[0]
            for row in conn.execute(
                "SELECT sql FROM sqlite_master WHERE tbl_name='next_best_actions' "
                "AND type IN ('index','trigger') AND sql IS NOT NULL"
            )
        ]
        event_trigger_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='trigger' "
            "AND name='trg_action_events_experiment_context'"
        ).fetchone()[0]
        legacy_sql = action_sql.replace(
            "next_best_actions", "next_best_actions_pre_035", 1
        ).replace(",'lock_intent'", "", 1)
        columns = [
            row[1] for row in conn.execute("PRAGMA table_info(next_best_actions)")
        ]
        column_list = ",".join(columns)
        conn.execute(legacy_sql)
        conn.execute(
            f"INSERT INTO next_best_actions_pre_035 ({column_list}) "
            f"SELECT {column_list} FROM next_best_actions"
        )
        conn.execute("DROP TRIGGER trg_action_events_experiment_context")
        conn.execute("DROP TABLE next_best_actions")
        conn.execute(
            "ALTER TABLE next_best_actions_pre_035 RENAME TO next_best_actions"
        )
        for sql in dependent_sql:
            conn.execute(sql)
        conn.execute(event_trigger_sql)
        conn.commit()

    upgraded = apply(db_path, DEFAULT_MIGRATIONS_DIR)

    assert [item.version for item in upgraded] == [
        "035_intent_lock_action",
        "036_creator_series_scope",
        "037_capability_trust",
        "038_scope_learning_action",
        "039_observation_window_action",
        "040_unavailable_performance_result",
        "041_project_state_events",
        "042_growth_onboarding",
        "043_first_party_opportunities",
        "044_repair_opportunity_sources",
        "045_drop_legacy_v1_tables",
    ]
    with sqlite3.connect(db_path) as conn:
        action_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='next_best_actions'"
        ).fetchone()[0]
        assert "'lock_intent'" in action_sql
        # 038 expands the same constraint again without dropping 035's value.
        assert "'scope_learning'" in action_sql


def test_old_043_database_gets_backfilled_by_044(tmp_path):
    """Regression: databases that ran old-043 (which hardcoded source_trigger='system',
    source_refs_json='[]', dimensions_json='{}') must be repaired by migration 044.

    The original 043 INSERT SELECT used hard-coded placeholders; the runner-marker
    fix in 08f289c changed the *file*, but the runner skips any migration version
    already recorded in schema_migrations.  A 044 repair migration is the only way
    to reach those rows.
    """
    db_path = tmp_path / "old-043-repair.db"
    through_043 = tmp_path / "through-043"
    through_043.mkdir()
    for path in DEFAULT_MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"):
        if int(path.name[:3]) <= 43:
            shutil.copy2(path, through_043 / path.name)

    # Bring the schema up to 043 only (records it in schema_migrations but not 044).
    apply(db_path, through_043)

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute(
            "INSERT INTO users (id,email,username,password_hash,ai_calls_reset_at,created_at) "
            "VALUES ('u1','u1@example.com','u1','hash','2026-07-24T00:00:00Z','2026-07-23T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO ai_traces_v2 (id,owner_user_id,task_type,input_refs_json,"
            "policy_version,capability,visibility_boundary_json,contamination_check_json,"
            "calibration_state,output_ref,generated_at) VALUES "
            "('trace-1','u1','manual_opportunity','[]','v1','manual_intake','{}','{}',"
            "'valid','content-opportunity:op-1','2026-07-23T00:00:00Z')"
        )
        # Simulate what old-043 hardcoded: a user_source row with placeholder defaults.
        conn.execute(
            "INSERT INTO content_opportunities ("
            "id,owner_user_id,opportunity_type,source_trigger,source_ref,"
            "source_refs_json,verification_status,content_intent,content_format,"
            "proposed_title,proposed_audience_change,proposed_rationale,"
            "evidence_refs_json,unknown_refs_json,dimensions_json,"
            "status,proposal_source,ai_trace_id,limitations_json,"
            "version,idempotency_key,request_hash,created_at,updated_at"
            ") VALUES ("
            "'op-1','u1','user_source','system','keyword:python',"
            "'[]','verified','share','graphic_note',"
            "'Python basics','Developers','Beginner-friendly Python guide',"
            "'[]','[]','{}',"
            "'proposed','ai','trace-1','[]',"
            "1,'op-key','op-hash','2026-07-23T00:00:00Z','2026-07-23T00:00:00Z'"
            ")"
        )
        conn.commit()

    # Pre-condition: row carries the bad placeholder values old-043 would have left.
    with sqlite3.connect(db_path) as conn:
        pre = conn.execute(
            "SELECT source_refs_json, dimensions_json, source_trigger "
            "FROM content_opportunities WHERE id='op-1'"
        ).fetchone()
    assert pre == ("[]", "{}", "system")

    # 043 is already recorded → runner skips it; 044 must apply and fix the row.
    upgraded = apply(db_path, DEFAULT_MIGRATIONS_DIR)
    assert any(item.version == "044_repair_opportunity_sources" for item in upgraded)

    with sqlite3.connect(db_path) as conn:
        post = conn.execute(
            "SELECT source_refs_json, dimensions_json, source_trigger "
            "FROM content_opportunities WHERE id='op-1'"
        ).fetchone()

    source_refs = json.loads(post[0])
    dimensions = json.loads(post[1])
    assert len(source_refs) >= 1, "source_refs_json must be backfilled with at least one entry"
    assert set(dimensions.keys()) == {
        "audience_fit",
        "creator_fit",
        "material_readiness",
        "growth_role",
        "series_potential",
        "timeliness",
        "similarity_risk",
        "safety_risk",
    }, "dimensions_json must be backfilled with all dimension keys"
    # user_source with no URL and no authority → user_keyword
    assert post[2] == "user_keyword", "source_trigger must be backfilled for user_source"

    # Idempotency: a second apply must be a no-op.
    assert apply(db_path, DEFAULT_MIGRATIONS_DIR) == []


def test_intent_lock_action_migration_repairs_interrupted_artifacts(tmp_path):
    db_path = tmp_path / "intent-lock-action-recovery.db"
    apply(db_path, DEFAULT_MIGRATIONS_DIR)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "DELETE FROM schema_migrations WHERE version='035_intent_lock_action'"
        )
        conn.execute("DROP INDEX uq_next_best_actions_owner_idempotency")
        conn.execute("DROP INDEX idx_next_best_actions_owner_status")
        conn.execute("DROP INDEX idx_next_best_actions_project_status")
        conn.execute("DROP TRIGGER trg_next_best_actions_experiment_context")
        conn.execute("DROP TRIGGER trg_action_events_experiment_context")
        conn.commit()

    repaired = apply(db_path, DEFAULT_MIGRATIONS_DIR)

    assert [item.version for item in repaired] == ["035_intent_lock_action"]
    with sqlite3.connect(db_path) as conn:
        artifacts = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('index','trigger')"
            )
        }
    assert {
        "uq_next_best_actions_owner_idempotency",
        "idx_next_best_actions_owner_status",
        "idx_next_best_actions_project_status",
        "trg_next_best_actions_experiment_context",
        "trg_action_events_experiment_context",
    } <= artifacts
