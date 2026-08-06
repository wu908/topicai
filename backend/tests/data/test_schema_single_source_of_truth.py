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
import shutil
import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import text

from app.data.migrations.runner import DEFAULT_MIGRATIONS_DIR, apply

# The complete set of tables the application expects after the runner
# bootstraps a fresh DB. Sourced from the union of SQL_SCHEMA (the 19
# originals) + all additive migrations. Sorted for
# stable diff output.
_EXPECTED_TABLES: frozenset[str] = frozenset(
    {
        # v2-only final schema
        "schema_migrations",
        "users",
        "creator_profiles",
        "materials",
        "material_usages",
        # v2 content-project foundation and intent orchestration (012-033)
        "content_projects",
        "content_versions",
        "publish_hypotheses",
        "publish_hypothesis_amendments",
        "publish_records_v2",
        "performance_snapshots_v2",
        "ai_traces_v2",
        "blind_reviews",
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
        "content_opportunities",
        "content_opportunity_events",
        "experiments",
        "experiment_assignments",
        "experiment_assignment_events",
        "project_state_events",
        "history_imports",
        "imported_notes",
        # bounded starter entry flow (029); content execution remains in projects
        "starter_assessments",
        "starter_direction_candidates",
        "starter_sprints",
        # release contract gaps (046)
        "publish_checks_v2",
        "publish_check_resolutions_v2",
        "snapshot_extractions_v2",
        # auditable owner-data operations (047)
        "account_data_jobs",
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

    def test_creator_profiles_has_v2_checks(self, tmp_path):
        db = tmp_path / "fresh.db"
        apply(db, DEFAULT_MIGRATIONS_DIR)

        with sqlite3.connect(db) as conn:
            (sql,) = conn.execute(
                "SELECT sql FROM sqlite_master WHERE name='creator_profiles'"
            ).fetchone()

        assert "growth_goal" in sql
        assert "confirmation_state" in sql
        assert "recommendation_mode" not in sql
        assert "CHECK" in sql.upper()


# ==================== T105 ====================


class TestCreatorProfilesCheckEnforced:
    """The final v2 profile enum constraints are enforced by SQLite."""

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
                    "(id,user_id,growth_goal,confirmation_state,created_at,updated_at) "
                    "VALUES ('p1','u1','bogus_goal','provisional','2026-01-01','2026-01-01')"
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
        _ignore = {"sqlite_master", "schema_migrations", "dual", "json_each"}
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
    async def test_database_init_db_applies_migrations_on_memory(self):
        from app.core.database import Database

        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()
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


# ==================== T103 (lifespan + conftest routed through bridge) ========


class TestConftestFixtureRoutedThroughBridge:
    """The test fixture receives the final v2 schema from the migration runner."""

    @pytest.mark.asyncio
    async def test_conftest_fixture_has_all_production_tables(self, test_db):
        async with test_db.engine.begin() as conn:
            rows = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = {r[0] for r in rows.fetchall()}

        migration_only = {"content_projects", "creator_states", "materials"}
        missing = migration_only - tables
        assert not missing, (
            f"test_db fixture missing migration-only tables {sorted(missing)} "
            "— the fixture is not routed through Database.apply_migrations()"
        )


# ==================== T104 (retire SQL_SCHEMA) ====================


class TestInitDbRetiresSqlSchema:
    """T104: ``init_db`` must no longer execute ``SQL_SCHEMA`` — the
    migration runner (called via :meth:`apply_migrations`) is the sole
    schema authority. Two facets:

    * ``SQL_SCHEMA`` as a module attribute is empty / removed.
    * ``init_db`` creates ZERO tables when migrations are suppressed.

    Both go RED in the dual-source world (SQL_SCHEMA still defines and
    runs ~20 tables) and GREEN once T104 deletes the SQL_SCHEMA body from
    ``init_db``.
    """

    def test_sql_schema_constant_is_empty_or_absent(self):
        from app.core import database as database_module

        schema = getattr(database_module, "SQL_SCHEMA", "") or ""
        tables = _collect_table_names_in_sql(schema)
        assert not tables, (
            "SQL_SCHEMA still defines tables; it must be retired. Found: "
            f"{sorted(tables)}"
        )

    @pytest.mark.asyncio
    async def test_init_db_creates_no_tables_when_migrations_suppressed(
        self, monkeypatch
    ):
        from app.core.database import Database

        # Suppress the bridge so init_db's only schema source is whatever
        # init_db itself runs. If SQL_SCHEMA is retired, init_db creates
        # zero tables (only pragmas + session factory).
        async def _no_op(self):  # noqa: ANN001
            return None

        monkeypatch.setattr(Database, "apply_migrations", _no_op)

        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()
        try:
            async with db.engine.begin() as conn:  # type: ignore[union-attr]
                rows = await conn.execute(
                    text(
                        "SELECT name FROM sqlite_master "
                        "WHERE type='table' AND name != 'sqlite_sequence'"
                    )
                )
                tables = {r[0] for r in rows.fetchall()}
        finally:
            await db.close()

        assert not tables, (
            f"init_db created {sorted(tables)} without migrations — SQL_SCHEMA "
            "is still the schema authority inside init_db."
        )


# ==================== T301-T305 (008 creator_profiles reconcile) ============


class TestCreatorProfilesReconcile:
    """T301-T305: migration 008 reconciles legacy ``creator_profiles``
    tables that predate the 005 ``CHECK (recommendation_mode IN (...))``
    constraint.

    Background: a prod DB created before migration 005 has
    ``creator_profiles.recommendation_mode`` as a plain ``TEXT NOT NULL``
    with no CHECK — so a buggy write could land any string. The 005
    migration adds the CHECK on fresh DBs only (``CREATE TABLE IF NOT
    EXISTS`` is a no-op on an existing table), so legacy DBs remain
    CHECK-less. Migration 008 rebuilds the table with the CHECK in place
    using the 12-step SQLite pattern (CREATE new, INSERT-SELECT, DROP,
    RENAME, CREATE INDEX).

    Invariants verified here:
      (a) A legacy creator_profiles that accepted a bogus
          ``recommendation_mode`` pre-008 rejects the same bogus value
          post-008 (proves the CHECK landed).
      (b) A pre-existing row's ``rubric_weights`` (and row count) survive
          the rebuild (proves no data loss).
      (c) On a fresh DB the rebuild is a no-op — the CHECK and the
          ``idx_creator_profiles_user_id`` index both still exist.
      (d) Migration 008 is recorded in ``schema_migrations`` with a
          64-char SHA-256 hex checksum.
    """

    _LE_USERS = (
        "id TEXT PRIMARY KEY, "
        "email TEXT UNIQUE NOT NULL, "
        "username TEXT UNIQUE NOT NULL, "
        "password_hash TEXT NOT NULL, "
        "ai_calls_today INTEGER NOT NULL DEFAULT 0, "
        "ai_calls_reset_at TEXT NOT NULL, "
        "created_at TEXT NOT NULL, "
        "last_login TEXT"
    )

    @staticmethod
    def _through_008(tmp_path: Path) -> Path:
        migrations = tmp_path / "through-008"
        migrations.mkdir(exist_ok=True)
        for source in DEFAULT_MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"):
            if source.name <= "008_creator_profiles_reconcile.sql":
                shutil.copy2(source, migrations / source.name)
        return migrations

    def _create_legacy_creator_profiles(self, conn: sqlite3.Connection) -> None:
        """Simulate a pre-005 schema: ``users`` + ``creator_profiles``
        with the 005 column order but NO CHECK on
        ``recommendation_mode``."""
        conn.executescript(
            f"""
            CREATE TABLE users ({self._LE_USERS});
            CREATE TABLE creator_profiles (
                id                    TEXT PRIMARY KEY,
                user_id               TEXT NOT NULL UNIQUE,
                track                 TEXT NOT NULL,
                content_formats       TEXT NOT NULL,
                production_complexity TEXT NOT NULL,
                content_depth         TEXT NOT NULL,
                hotspot_preference    TEXT NOT NULL,
                recommendation_mode   TEXT NOT NULL,
                rubric_weights        TEXT NOT NULL DEFAULT '{{}}',
                created_at            TEXT NOT NULL,
                updated_at            TEXT NOT NULL DEFAULT ''
            );
            """
        )

    def test_legacy_creator_profiles_gets_check_after_migration_008(
        self, tmp_path
    ):
        """T301: bogus ``recommendation_mode`` is accepted on the legacy
        table (proves no CHECK) and rejected after 008 runs (proves the
        CHECK is back)."""
        db = tmp_path / "legacy.db"
        with sqlite3.connect(db) as conn:
            self._create_legacy_creator_profiles(conn)
            conn.execute(
                "INSERT INTO users (id, email, username, password_hash, "
                "ai_calls_reset_at, created_at) "
                "VALUES ('u1','a@b.com','alice','h','2026-01-01','2026-01-01')"
            )
            # (1) bogus insert succeeds — proves legacy has no CHECK.
            conn.execute(
                "INSERT INTO creator_profiles "
                "(id, user_id, track, content_formats, production_complexity, "
                " content_depth, hotspot_preference, recommendation_mode, "
                " rubric_weights, created_at, updated_at) "
                "VALUES ('p0','u1','t','[]','low','shallow','hot',"
                "        'bogus_legacy','{}','2026-01-01','')"
            )
            # Delete the bogus row so 008's INSERT-SELECT can succeed
            # (the new table's CHECK would otherwise reject the copy).
            conn.execute("DELETE FROM creator_profiles")
            # Seed a valid row so the rebuild has data to preserve.
            conn.execute(
                "INSERT INTO creator_profiles "
                "(id, user_id, track, content_formats, production_complexity, "
                " content_depth, hotspot_preference, recommendation_mode, "
                " rubric_weights, created_at, updated_at) "
                "VALUES ('p1','u1','t','[]','low','shallow','hot',"
                "        'hotspot_fusion','{}','2026-01-01','')"
            )
            conn.commit()

        apply(db, self._through_008(tmp_path))

        with sqlite3.connect(db) as conn:
            conn.execute("PRAGMA foreign_keys=ON")
            # (2) bogus insert after 008 must raise IntegrityError. Use a
            # fresh user_id (u2) so the failure is the CHECK, not the
            # UNIQUE(user_id) constraint on creator_profiles.
            conn.execute(
                "INSERT INTO users (id, email, username, password_hash, "
                "ai_calls_reset_at, created_at) "
                "VALUES ('u2','b@b.com','bob','h','2026-01-01','2026-01-01')"
            )
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO creator_profiles "
                    "(id, user_id, track, content_formats, production_complexity, "
                    " content_depth, hotspot_preference, recommendation_mode, "
                    " rubric_weights, created_at, updated_at) "
                    "VALUES ('p2','u2','t','[]','low','shallow','hot',"
                    "        'bogus_post_008','{}','2026-01-01','')"
                )

    def test_data_preserved_through_008_reconcile(self, tmp_path):
        """T302/T303: ``rubric_weights`` and row count survive the 12-step
        rebuild. Bug guard: a future refactor that drops a column from the
        INSERT-SELECT list would silently lose data — this test pins the
        full column set."""
        db = tmp_path / "legacy.db"
        with sqlite3.connect(db) as conn:
            self._create_legacy_creator_profiles(conn)
            conn.execute(
                "INSERT INTO users (id, email, username, password_hash, "
                "ai_calls_reset_at, created_at) "
                "VALUES ('u1','a@b.com','alice','h','2026-01-01','2026-01-01')"
            )
            conn.execute(
                "INSERT INTO creator_profiles "
                "(id, user_id, track, content_formats, production_complexity, "
                " content_depth, hotspot_preference, recommendation_mode, "
                " rubric_weights, created_at, updated_at) "
                "VALUES ('p1','u1','t','[]','low','shallow','hot',"
                "        'hotspot_fusion','{\"x\":0.5}','2026-01-01','')"
            )
            conn.commit()

        apply(db, self._through_008(tmp_path))

        with sqlite3.connect(db) as conn:
            (count,) = conn.execute(
                "SELECT COUNT(*) FROM creator_profiles"
            ).fetchone()
            (rubric,) = conn.execute(
                "SELECT rubric_weights FROM creator_profiles WHERE id='p1'"
            ).fetchone()

        assert count == 1, f"008 lost data: expected 1 row, got {count}"
        assert rubric == '{"x":0.5}', (
            f"rubric_weights not preserved through 008 rebuild: "
            f"expected '{{\"x\":0.5}}', got {rubric!r}"
        )

    def test_fresh_db_creator_profiles_has_check_and_index_after_008(
        self, tmp_path
    ):
        """T304: on a fresh DB (000 already creates ``creator_profiles``
        WITH the CHECK), running migrations through 008 is a no-op
        rebuild — the CHECK and the ``idx_creator_profiles_user_id``
        index both survive."""
        db = tmp_path / "fresh.db"
        apply(db, self._through_008(tmp_path))

        with sqlite3.connect(db) as conn:
            (sql,) = conn.execute(
                "SELECT sql FROM sqlite_master WHERE name='creator_profiles'"
            ).fetchone()
            assert "CHECK" in sql.upper(), (
                "fresh DB creator_profiles missing CHECK after 008: " + str(sql)
            )
            indexes = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' "
                    "AND tbl_name='creator_profiles'"
                )
            }
            assert "idx_creator_profiles_user_id" in indexes, (
                f"fresh DB missing idx_creator_profiles_user_id after 008: "
                f"{sorted(indexes)}"
            )

    def test_migration_008_recorded_with_sha256_checksum(self, tmp_path):
        """T305: migration 008 is recorded in ``schema_migrations`` with a
        64-char SHA-256 hex checksum (mirrors the contract every other
        shipped migration honours)."""
        db = tmp_path / "fresh.db"
        apply(db, self._through_008(tmp_path))

        with sqlite3.connect(db) as conn:
            rows = {
                row[0]: row[1]
                for row in conn.execute(
                    "SELECT version, checksum FROM schema_migrations"
                )
            }

        assert "008_creator_profiles_reconcile" in rows, (
            "008_creator_profiles_reconcile not recorded in schema_migrations; "
            f"recorded versions: {sorted(rows)}"
        )
        assert len(rows["008_creator_profiles_reconcile"]) == 64
