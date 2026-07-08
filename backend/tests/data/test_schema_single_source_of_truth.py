"""Schema single-source-of-truth lock-down tests (Spec-007 dual-schema debt).

These tests pin the migration runner as the ONLY schema authority. They were
written RED-first against the dual-source world (SQL_SCHEMA big-string +
migrations + conftest inline SQL) and go GREEN as the consolidation lands
(T101-T107).

* T101 — ``000_initial_schema.sql`` lets the runner alone bootstrap the
  full app schema on a fresh DB, and the runner records the 000 version.
* T105 — ``creator_profiles.recommendation_mode`` CHECK constraint is
  enforced on a fresh DB (proves the migration 005 authoritative definition
  won, not the CHECK-less SQL_SCHEMA version).
* T107 — drift regressions: SQL_SCHEMA must be empty/retired and every
  table name the service layer references must have a migration that
  creates it.
"""

from __future__ import annotations

import asyncio
import re
import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import text

from app.data.migrations.runner import DEFAULT_MIGRATIONS_DIR, apply

# The complete set of tables the application expects after the runner
# bootstraps a fresh DB. Sourced from the union of SQL_SCHEMA (the 19
# originals) + the 002/003/004/005/006 additive migrations. Sorted for
# stable diff output.
_EXPECTED_TABLES: frozenset[str] = frozenset(
    {
        # 000_initial originals (19 business tables + schema_migrations)
        "schema_migrations",
        "users",
        "creator_profiles",
        "topic_recommendations",
        "viral_analyses",
        "idea_boosters",
        "title_optimizations",
        "track_diagnoses",
        "feedback_records",
        "feedback_analyses",
        "effect_reviews",
        "content_risks",
        "publish_suggestions",
        "user_events",
        "llm_call_logs",
        "upgrade_signals",
        "assets",
        "asset_tags",
        "asset_tag_links",
        "asset_usages",
        "platform_accounts",
        "team_members",
        # migration-only additions (002/004/006)
        "user_feedback",
        "risk_keywords",
        "platform_tokens",
    }
)


def _tables_in(conn: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }


# ==================== T101 ====================


class TestBootstrapFullSchema:
    """T101: the migration runner alone bootstraps every app table on a
    fresh DB — no SQL_SCHEMA, no conftest inline SQL needed."""

    def test_migration_runner_bootstraps_full_schema_on_fresh_db(self, tmp_path):
        db = tmp_path / "fresh.db"
        apply(db, DEFAULT_MIGRATIONS_DIR)

        with sqlite3.connect(db) as conn:
            tables = _tables_in(conn)

        missing = _EXPECTED_TABLES - tables
        extra = tables - _EXPECTED_TABLES
        assert not missing, f"runner did not create: {sorted(missing)}"
        assert not extra, f"runner created unexpected tables: {sorted(extra)}"

    def test_schema_migrations_records_000_initial(self, tmp_path):
        db = tmp_path / "fresh.db"
        apply(db, DEFAULT_MIGRATIONS_DIR)

        with sqlite3.connect(db) as conn:
            rows = {
                row[0]: row[1]
                for row in conn.execute(
                    "SELECT version, checksum FROM schema_migrations"
                )
            }

        assert "000_initial_schema" in rows, (
            "000_initial_schema not recorded in schema_migrations; "
            f"recorded versions: {sorted(rows)}"
        )
        assert len(rows["000_initial_schema"]) == 64  # SHA-256 hex

    def test_creator_profiles_has_authoritative_check(self, tmp_path):
        """T101 (supporting T105): the 000/migration definition of
        creator_profiles carries the recommendation_mode CHECK that the
        SQL_SCHEMA version lacked. Verified by inspecting the fresh DB's
        table SQL (sqlite_master) — the CHECK clause must be present."""
        db = tmp_path / "fresh.db"
        apply(db, DEFAULT_MIGRATIONS_DIR)

        with sqlite3.connect(db) as conn:
            (sql,) = conn.execute(
                "SELECT sql FROM sqlite_master WHERE name='creator_profiles'"
            ).fetchone()

        assert "recommendation_mode" in sql
        assert "CHECK" in sql.upper(), (
            "creator_profiles missing the recommendation_mode CHECK — "
            "the SQL_SCHEMA (CHECK-less) version won instead of the "
            "migration-authoritative definition.\nSQL:\n" + str(sql)
        )


# ==================== T105 ====================


class TestCreatorProfilesCheckEnforced:
    """T105: a row violating recommendation_mode's CHECK is rejected at
    the SQLite layer on a fresh DB (proves the constraint is real, not
    just textual)."""

    def test_creator_profiles_check_enforced_on_fresh_db(self, tmp_path):
        db = tmp_path / "fresh.db"
        apply(db, DEFAULT_MIGRATIONS_DIR)

        # users row first (creator_profiles.user_id FKs to it).
        with sqlite3.connect(db) as conn:
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute(
                "INSERT INTO users (id, email, username, password_hash, "
                "ai_calls_reset_at, created_at) "
                "VALUES ('u1','a@b.com','alice','h','2026-01-01','2026-01-01')"
            )
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO creator_profiles "
                    "(id, user_id, track, content_formats, "
                    "production_complexity, content_depth, hotspot_preference, "
                    "recommendation_mode, rubric_weights, created_at, updated_at) "
                    "VALUES ('p1','u1','t','[]','low','shallow','hot',"
                    "'bogus_mode_not_in_check','{}','2026-01-01','2026-01-01')"
                )


# ==================== T107 (drift lock-down) ====================


def _collect_table_names_in_sql(text: str) -> set[str]:
    """Return all ``CREATE TABLE`` target names found in a SQL blob."""
    return {
        m.group(1)
        for m in re.finditer(
            r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+([A-Za-z_][A-Za-z0-9_]*)",
            text,
            re.IGNORECASE,
        )
    }


class TestSingleSourceOfTruth:
    """T107: pin that SQL_SCHEMA is retired (no CREATE TABLE in it) and
    that every table the service layer names appears in a migration.

    These go GREEN once T104 retires SQL_SCHEMA; they are RED in the
    dual-source world and serve as the permanent drift guard.
    """

    def test_no_create_table_in_sql_schema(self):
        from app.core import database as database_module

        schema = getattr(database_module, "SQL_SCHEMA", "") or ""
        tables = _collect_table_names_in_sql(schema)
        assert not tables, (
            "SQL_SCHEMA still creates tables — it must be retired so the "
            f"migration runner is the sole schema authority. Found: "
            f"{sorted(tables)}"
        )

    def test_every_service_layer_table_has_a_migration(self):
        """Every table name appearing in service-layer SQL must be created
        by some migration file (so retiring SQL_SCHEMA never drops a
        table the app uses)."""
        backend_root = Path(__file__).resolve().parents[2]
        app_dir = backend_root / "app"

        # Collect every table name referenced in app/services and app/chains.
        # Only match UPPERCASE SQL keywords inside string literals — the
        # service layer writes SQL in upper-case (FROM/INTO/UPDATE/JOIN),
        # while Python imports use lower-case ``from``. This avoids false
        # positives like ``from typing import``.
        referenced: set[str] = set()
        _sql_ref = re.compile(
            r"\b(?:FROM|INTO|UPDATE|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)"
        )
        for sub in ("services", "chains"):
            for path in (app_dir / sub).rglob("*.py"):
                src = path.read_text(encoding="utf-8")
                for m in _sql_ref.finditer(src):
                    # Require the keyword to be uppercase as written (not a
                    # Python ``from`` import), to stay conservative.
                    if m.group(0).split()[0].isupper():
                        referenced.add(m.group(1).lower())

        # Built-in / non-app tables that are legitimately referenced but
        # not owned by the app schema.
        _ignore = {"sqlite_master", "schema_migrations", "dual"}
        referenced -= _ignore

        # Tables the migrations create.
        migrated: set[str] = set()
        for sql_path in DEFAULT_MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"):
            migrated |= _collect_table_names_in_sql(
                sql_path.read_text(encoding="utf-8")
            )

        missing = referenced - migrated
        assert not missing, (
            "service/chains reference tables with no migration creating "
            f"them — retiring SQL_SCHEMA would break these: {sorted(missing)}"
        )


# ==================== T102 (async/sync bridge) ====================


def _async_table_names(db) -> set[str]:
    """Reflect the table names on a Database instance's async engine."""
    async def _collect() -> set[str]:
        async with db.engine.begin() as conn:
            rows = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            return {r[0] for r in rows.fetchall()}

    return asyncio.get_event_loop().run_until_complete(_collect())


class TestDatabaseApplyMigrations:
    """T102: ``Database.apply_migrations()`` runs the migration runner
    through the SAME engine ``init_db`` will use, so a memory test DB and
    a file DB both end up with the full schema — no second, divergent
    sqlite3 :memory: database.

    These go RED before the bridge exists (``apply_migrations`` is not yet
    a method) and GREEN once T102 lands.
    """

    @pytest.mark.asyncio
    async def test_database_apply_migrations_creates_tables_on_memory(self):
        from app.core.database import Database

        db = Database("sqlite+aiosqlite:///:memory:")
        # init_db creates the engine, sets pragmas, and (once T104 lands)
        # calls apply_migrations. During T102 init_db still also runs
        # SQL_SCHEMA, so we exercise the bridge directly here.
        await db.init_db()
        await db.apply_migrations()
        try:
            async with db.engine.begin() as conn:  # type: ignore[union-attr]
                rows = await conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
                tables = {r[0] for r in rows.fetchall()}
        finally:
            await db.close()

        missing = _EXPECTED_TABLES - tables
        assert not missing, f"apply_migrations (memory) missing: {sorted(missing)}"

    @pytest.mark.asyncio
    async def test_database_apply_migrations_applies_to_file_db(self, tmp_path):
        from app.core.database import Database

        file_url = f"sqlite+aiosqlite:///{tmp_path / 'bridge.db'}"
        db = Database(file_url)
        await db.init_db()
        await db.apply_migrations()
        try:
            async with db.engine.begin() as conn:  # type: ignore[union-attr]
                rows = await conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
                tables = {r[0] for r in rows.fetchall()}
        finally:
            await db.close()

        missing = _EXPECTED_TABLES - tables
        assert not missing, f"apply_migrations (file) missing: {sorted(missing)}"

    @pytest.mark.asyncio
    async def test_database_raw_path_memory_returns_none(self):
        """``_raw_path`` returns ``None`` for ``:memory:`` URLs so the
        bridge routes to the aiosqlite executescript branch (the sync
        sqlite3 :memory: would be a different DB)."""
        from app.core.database import Database

        assert Database("sqlite+aiosqlite:///:memory:")._raw_path() is None

    @pytest.mark.asyncio
    async def test_database_raw_path_file_returns_path(self, tmp_path):
        from app.core.database import Database

        file_url = f"sqlite+aiosqlite:///{tmp_path / 'bridge.db'}"
        assert Database(file_url)._raw_path() == str(tmp_path / "bridge.db")
