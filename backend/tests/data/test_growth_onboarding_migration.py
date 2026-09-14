"""Migration coverage for Growth onboarding persistence."""

import shutil
import sqlite3

import pytest

from app.data.migrations.runner import DEFAULT_MIGRATIONS_DIR, apply


def test_growth_onboarding_migration_is_replay_safe(tmp_path):
    db_path = tmp_path / "growth-onboarding.db"

    first = apply(db_path, DEFAULT_MIGRATIONS_DIR)
    second = apply(db_path, DEFAULT_MIGRATIONS_DIR)

    assert first[-1].version == "055_reference_anchor"
    assert second == []
    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert {"history_imports", "imported_notes"} <= tables
        user_columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
        assert {
            "product_mode",
            "onboarding_state",
            "timezone",
            "weekly_publish_goal",
            "consent_json",
        } <= user_columns
        profile_columns = {row[1] for row in conn.execute("PRAGMA table_info(creator_profiles)")}
        assert {
            "niche",
            "target_audience",
            "content_pillars_json",
            "confirmation_state",
            "version",
        } <= profile_columns


def test_growth_onboarding_migration_recovers_after_ddl_before_version_record(tmp_path):
    db_path = tmp_path / "growth-onboarding-recovery.db"
    through_041 = tmp_path / "through-041"
    through_041.mkdir()
    for path in DEFAULT_MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"):
        if int(path.name[:3]) <= 41:
            shutil.copy2(path, through_041 / path.name)

    apply(db_path, through_041)
    migration = DEFAULT_MIGRATIONS_DIR / "042_growth_onboarding.sql"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(migration.read_text(encoding="utf-8"))

    upgraded = apply(db_path, DEFAULT_MIGRATIONS_DIR)
    replay = apply(db_path, DEFAULT_MIGRATIONS_DIR)

    assert [item.version for item in upgraded] == [
        "042_growth_onboarding",
        "043_first_party_opportunities",
        "044_repair_opportunity_sources",
        "045_drop_legacy_v1_tables",
        "046_release_contract_gaps",
        "047_account_data_jobs",
        "048_release_audit_fixes",
        "049_release_audit_batch3", "050_async_creation_loop", "051_deliverable_precheck",
        "052_auto_digest_setting",
        "053_project_start_inference",
        "054_reference_samples",
        "055_reference_anchor",
    ]
    assert replay == []


def test_reference_sample_columns_are_enforced_on_a_fresh_database(tmp_path):
    """全新库：来源列存在、默认 self、CHECK 生效。"""
    db_path = tmp_path / "reference-samples-fresh.db"
    apply(db_path, DEFAULT_MIGRATIONS_DIR)

    with sqlite3.connect(db_path) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(imported_notes)")}
        assert {"origin", "source_handle"} <= columns

        conn.execute(
            "INSERT INTO users (id,email,username,password_hash,ai_calls_reset_at,created_at) "
            "VALUES ('u1','a@b.com','alice','h','2026-01-01','2026-01-01')"
        )
        conn.execute(
            "INSERT INTO history_imports (id,owner_user_id,method,status,input_count,"
            "success_count,failure_count,item_results_json,idempotency_key,request_hash,"
            "started_at,completed_at) VALUES ('h1','u1','manual','completed',1,1,0,'[]',"
            "'k','r','2026-01-01','2026-01-01')"
        )
        # 不写 origin：老的写入路径必须原样可用，并落到 self。
        conn.execute(
            "INSERT INTO imported_notes (id,owner_user_id,history_import_id,title,"
            "body_excerpt,metrics_json,audience_questions_json,tags_json,source_hash,"
            "retention_expires_at,user_confirmed,created_at) VALUES ('n1','u1','h1','旧笔记',"
            "'',:metrics,'[]','[]','hash-1','2026-12-31',0,'2026-01-01')",
            {"metrics": "{}"},
        )
        (origin,) = conn.execute("SELECT origin FROM imported_notes WHERE id='n1'").fetchone()
        assert origin == "self"
        (handle,) = conn.execute(
            "SELECT source_handle FROM imported_notes WHERE id='n1'"
        ).fetchone()
        assert handle is None

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "UPDATE imported_notes SET origin='someone_else' WHERE id='n1'"
            )


def test_existing_imported_notes_become_self_on_upgrade(tmp_path):
    """老库升级：列被补上，**已经存在**的行必须是 self——不能被误当成参考样本。"""
    db_path = tmp_path / "reference-samples-upgrade.db"
    through_041 = tmp_path / "through-041"
    through_041.mkdir()
    for path in DEFAULT_MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"):
        if int(path.name[:3]) <= 41:
            shutil.copy2(path, through_041 / path.name)
    apply(db_path, through_041)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            (DEFAULT_MIGRATIONS_DIR / "042_growth_onboarding.sql").read_text(encoding="utf-8")
        )
        conn.execute(
            "INSERT INTO users (id,email,username,password_hash,ai_calls_reset_at,created_at) "
            "VALUES ('u1','a@b.com','alice','h','2026-01-01','2026-01-01')"
        )
        conn.execute(
            "INSERT INTO history_imports (id,owner_user_id,method,status,input_count,"
            "success_count,failure_count,item_results_json,idempotency_key,request_hash,"
            "started_at,completed_at) VALUES ('h1','u1','manual','completed',1,1,0,'[]',"
            "'k','r','2026-01-01','2026-01-01')"
        )
        conn.execute(
            "INSERT INTO imported_notes (id,owner_user_id,history_import_id,title,"
            "body_excerpt,metrics_json,audience_questions_json,tags_json,source_hash,"
            "retention_expires_at,user_confirmed,created_at) VALUES ('legacy','u1','h1',"
            "'升级前就存在的笔记','','{}','[]','[]','hash-legacy','2026-12-31',0,'2026-01-01')"
        )

    apply(db_path, DEFAULT_MIGRATIONS_DIR)

    with sqlite3.connect(db_path) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(imported_notes)")}
        assert {"origin", "source_handle"} <= columns
        (origin,) = conn.execute(
            "SELECT origin FROM imported_notes WHERE id='legacy'"
        ).fetchone()
        assert origin == "self"
