"""TDD tests for the migration runner (Spec-007 T003).

These tests predate the implementation in ``app/data/migrations/runner.py``;
they MUST be runnable against an in-memory SQLite database.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.data.migrations.runner import DEFAULT_MIGRATIONS_DIR


def _tmp_migrations_dir(tmp_path: Path) -> Path:
    """Create two trivial migration files in a temp dir."""
    (tmp_path / "001_init.sql").write_text(
        "CREATE TABLE widget(id INTEGER PRIMARY KEY, name TEXT);"
    )
    (tmp_path / "002_add_idx.sql").write_text(
        "CREATE INDEX idx_widget_name ON widget(name);"
    )
    return tmp_path


class TestMigrationRunner:
    def test_apply_runs_pending_migrations(self, tmp_path):
        from app.data.migrations.runner import apply

        migrations_dir = _tmp_migrations_dir(tmp_path)
        db = tmp_path / "app.db"
        applied = apply(db, migrations_dir)

        assert [m.version for m in applied] == ["001_init", "002_add_idx"]

        with sqlite3.connect(db) as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
        assert "schema_migrations" in tables
        assert "widget" in tables

    def test_apply_is_idempotent(self, tmp_path):
        from app.data.migrations.runner import apply

        migrations_dir = _tmp_migrations_dir(tmp_path)
        db = tmp_path / "app.db"
        first = apply(db, migrations_dir)
        second = apply(db, migrations_dir)

        assert len(first) == 2
        assert second == []  # no new migrations on second run

    def test_apply_records_checksum(self, tmp_path):
        from app.data.migrations.runner import apply

        migrations_dir = _tmp_migrations_dir(tmp_path)
        db = tmp_path / "app.db"
        apply(db, migrations_dir)

        with sqlite3.connect(db) as conn:
            row = conn.execute(
                "SELECT version, checksum FROM schema_migrations ORDER BY version"
            ).fetchall()
        assert [r[0] for r in row] == ["001_init", "002_add_idx"]
        for _version, checksum in row:
            assert len(checksum) == 64  # SHA-256 hex

    def test_status_returns_pending_and_applied(self, tmp_path):
        from app.data.migrations.runner import apply, status

        migrations_dir = _tmp_migrations_dir(tmp_path)
        db = tmp_path / "app.db"
        pending, applied = status(db, migrations_dir)
        assert pending == ["001_init", "002_add_idx"]
        assert applied == []

        apply(db, migrations_dir)

        pending, applied = status(db, migrations_dir)
        assert pending == []
        assert applied == ["001_init", "002_add_idx"]

    def test_empty_migrations_dir(self, tmp_path):
        from app.data.migrations.runner import apply

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        assert apply(tmp_path / "app.db", empty_dir) == []

    def test_no_duplicate_numeric_prefix_in_default_dir(self):
        """Regression for the 2026-07-03 dual-005 incident.

        Two migrations (005_creator_profiles.sql and 005_platform_tokens.sql)
        once shared the NNN=005 prefix. The runner keys schema_migrations by
        path.stem so they never collided at runtime, but the duplicate prefix
        broke the monotonic version invariant and made status() ambiguous.
        Lock down that no two shipped migrations share the same 3-digit prefix.
        """
        import re

        from app.data.migrations.runner import _list_migration_files

        files = _list_migration_files(DEFAULT_MIGRATIONS_DIR)
        assert files, "expected migrations to be present in the default dir"

        prefixes: list[str] = []
        for path in files:
            match = re.match(r"^(\d{3})_", path.name)
            assert match, f"migration {path.name} lacks a 3-digit NNN prefix"
            prefixes.append(match.group(1))
        assert len(prefixes) == len(set(prefixes)), (
            f"duplicate migration NNN prefixes: {prefixes}"
        )


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


# Columns that the Bug 3 "old" effect_reviews table is missing relative to the
# 003_effect_reviews.sql full schema.
_EFFECT_REVIEWS_FULL_COLUMNS = {
    "id",
    "user_id",
    "topic_title",
    "content_outline",
    "prediction",
    "actual_result",
    "attribution",
    "learnings",
    "status",
    "created_at",
    "updated_at",
}


class TestIdempotentColumnBackfill:
    """Regression tests for Bug 3: an existing DB that predates a column
    addition must have the new columns back-filled by the runner, because
    ``CREATE TABLE IF NOT EXISTS`` is a no-op on an existing table and SQLite
    has no ``ALTER TABLE ADD COLUMN IF NOT EXISTS``.
    """

    def _create_old_effect_reviews(self, conn: sqlite3.Connection) -> None:
        """Recreate the pre-Bug-3 effect_reviews schema (missing the additive
        columns introduced by migration 003)."""
        conn.execute(
            """
            CREATE TABLE effect_reviews (
                id          CHAR(36) PRIMARY KEY,
                user_id     CHAR(36) NOT NULL,
                topic_title TEXT     NOT NULL,
                prediction  TEXT     NOT NULL,
                created_at  TEXT     NOT NULL
            )
            """
        )

    def test_backfills_missing_columns_on_existing_db(self, tmp_path):
        from app.data.migrations.runner import apply

        db = tmp_path / "t.db"
        with sqlite3.connect(db) as conn:
            self._create_old_effect_reviews(conn)

        apply(db, DEFAULT_MIGRATIONS_DIR)

        with sqlite3.connect(db) as conn:
            columns = _table_columns(conn, "effect_reviews")

        missing = _EFFECT_REVIEWS_FULL_COLUMNS - columns
        assert not missing, f"Bug 3 regression: missing columns {missing}"

    def test_fresh_db_unchanged(self, tmp_path):
        from app.data.migrations.runner import apply

        db = tmp_path / "t.db"
        apply(db, DEFAULT_MIGRATIONS_DIR)

        with sqlite3.connect(db) as conn:
            columns = _table_columns(conn, "effect_reviews")

        assert columns == _EFFECT_REVIEWS_FULL_COLUMNS

    def test_idempotent_re_run(self, tmp_path):
        from app.data.migrations.runner import apply

        db = tmp_path / "t.db"
        with sqlite3.connect(db) as conn:
            self._create_old_effect_reviews(conn)

        apply(db, DEFAULT_MIGRATIONS_DIR)
        # Second run on the back-filled DB must apply nothing and not error.
        second = apply(db, DEFAULT_MIGRATIONS_DIR)
        assert second == []

        with sqlite3.connect(db) as conn:
            columns = _table_columns(conn, "effect_reviews")
        assert columns == _EFFECT_REVIEWS_FULL_COLUMNS
