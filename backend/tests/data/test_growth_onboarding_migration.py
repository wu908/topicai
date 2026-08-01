"""Migration coverage for Growth onboarding persistence."""

import shutil
import sqlite3

from app.data.migrations.runner import DEFAULT_MIGRATIONS_DIR, apply


def test_growth_onboarding_migration_is_replay_safe(tmp_path):
    db_path = tmp_path / "growth-onboarding.db"

    first = apply(db_path, DEFAULT_MIGRATIONS_DIR)
    second = apply(db_path, DEFAULT_MIGRATIONS_DIR)

    assert first[-1].version == "044_repair_opportunity_sources"
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
    ]
    assert replay == []
