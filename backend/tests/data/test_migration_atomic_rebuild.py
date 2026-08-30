"""Release-audit batch 3: migration atomicity + 049 hypothesis trigger guard.

Audit session be776634 findings covered here:

* ``033_calibration_completeness`` creates an immutability trigger on
  ``publish_hypotheses`` with no lock-state guard, so it aborts *every*
  UPDATE touching the guarded columns — including edits of rows that are
  still ``draft``. Migration 049 rebuilds the trigger gated on
  ``OLD.status = 'locked'``.
* The runner post-steps that rebuild tables (030, 034, 035/038/039 via
  ``_expand_intent_action_types``, 036) are not atomic and not
  retry-safe: a crash mid-rebuild leaves a leftover ``*_new`` table that
  makes the next startup die with "table already exists", and a failure
  leaves the implicit transaction open so the ``finally`` pragma restore
  is a silent no-op. Only ``_post_step_048_release_audit_fixes`` used
  the correct pattern (explicit BEGIN, DROP-IF-EXISTS pre-clean,
  rollback on error).
"""

from __future__ import annotations

import re
import shutil
import sqlite3
from pathlib import Path

import pytest

from app.data.migrations.runner import DEFAULT_MIGRATIONS_DIR, apply


def _through(tmp_path: Path, last_number: int) -> Path:
    """Copy every migration whose NNN prefix is <= ``last_number``."""
    target = tmp_path / f"through-{last_number:03d}"
    target.mkdir(exist_ok=True)
    for path in DEFAULT_MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"):
        if int(path.name[:3]) <= last_number:
            shutil.copy2(path, target / path.name)
    return target


def _table_names(conn: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }


def _seed_parents(conn: sqlite3.Connection) -> None:
    """Seed the FK parents publish_hypotheses needs.

    The runner post-steps end with ``PRAGMA foreign_key_check`` over the
    WHOLE database, so hypothesis rows with dangling owner/project/version
    references would fail a rebuild even with FK enforcement off.
    """
    conn.execute(
        "INSERT INTO users (id, email, username, password_hash, "
        "ai_calls_reset_at, created_at) "
        "VALUES ('owner-1','a@b.com','alice','h','2026-01-01','2026-01-01')"
    )
    conn.execute(
        "INSERT INTO content_projects ("
        "id,owner_user_id,title,status,primary_goal,target_audience,"
        "last_action_at,created_at,updated_at"
        ") VALUES ('project-1','owner-1','t','inbox','stable_publish',"
        "'aud','2026-08-08T00:00:00Z','2026-08-08T00:00:00Z',"
        "'2026-08-08T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO content_versions ("
        "id,owner_user_id,project_id,version_number,title,body_text,"
        "content_hash,idempotency_key,request_hash,created_at"
        ") VALUES ('version-1','owner-1','project-1',1,'t','b','h',"
        "'vk1','vh1','2026-08-08T00:00:00Z')"
    )
    conn.commit()


def _insert_hypothesis(conn: sqlite3.Connection, hypothesis_id: str, status: str) -> None:
    conn.execute(
        "INSERT INTO publish_hypotheses ("
        "id,owner_user_id,project_id,content_version_id,audience_problem,"
        "reader_promise,expected_behaviors_json,status,idempotency_key,"
        "request_hash,locked_at,locked_by,created_at"
        ") VALUES (?,?,?,?,?,?,'[]',?,?,?,?,?,?)",
        (
            hypothesis_id,
            "owner-1",
            "project-1",
            "version-1",
            "original problem",
            "promise",
            status,
            f"key-{hypothesis_id}",
            f"hash-{hypothesis_id}",
            "2026-08-08T00:00:00Z",
            "owner-1",
            "2026-08-08T00:00:00Z",
        ),
    )
    conn.commit()


class TestHypothesisLockGuardMigration049:
    """The 033 trigger must only protect rows that are actually locked."""

    def test_draft_hypothesis_editable_after_migration_049(self, tmp_path):
        db = tmp_path / "hypothesis.db"
        apply(db, _through(tmp_path, 33))

        with sqlite3.connect(db) as conn:
            _seed_parents(conn)
            _insert_hypothesis(conn, "h-draft", "draft")
            # Reproduce the 033 bug: the unguarded trigger aborts a
            # legitimate edit of a row that is still a draft.
            with pytest.raises(sqlite3.DatabaseError):
                conn.execute(
                    "UPDATE publish_hypotheses SET audience_problem='refined' "
                    "WHERE id='h-draft'"
                )
            conn.rollback()

        # Migration 049 repairs the trigger in place.
        applied = apply(db, DEFAULT_MIGRATIONS_DIR)
        assert any(item.version == "050_async_creation_loop" for item in applied)

        with sqlite3.connect(db) as conn:
            conn.execute(
                "UPDATE publish_hypotheses SET audience_problem='refined' "
                "WHERE id='h-draft'"
            )
            conn.commit()
            (problem,) = conn.execute(
                "SELECT audience_problem FROM publish_hypotheses WHERE id='h-draft'"
            ).fetchone()
        assert problem == "refined"

    def test_locked_hypothesis_stays_immutable_after_migration_049(self, tmp_path):
        db = tmp_path / "hypothesis-locked.db"
        apply(db, DEFAULT_MIGRATIONS_DIR)

        with sqlite3.connect(db) as conn:
            _seed_parents(conn)
            _insert_hypothesis(conn, "h-locked", "locked")
            with pytest.raises(sqlite3.DatabaseError):
                conn.execute(
                    "UPDATE publish_hypotheses SET reader_promise='changed' "
                    "WHERE id='h-locked'"
                )
            conn.rollback()

            # The status transition itself (e.g. supersede) is not guarded.
            conn.execute(
                "UPDATE publish_hypotheses SET status='superseded' "
                "WHERE id='h-locked'"
            )
            conn.commit()
            (status,) = conn.execute(
                "SELECT status FROM publish_hypotheses WHERE id='h-locked'"
            ).fetchone()
        assert status == "superseded"

    def test_migration_049_recorded_on_fresh_db(self, tmp_path):
        db = tmp_path / "fresh.db"
        applied = apply(db, DEFAULT_MIGRATIONS_DIR)
        assert any(item.version == "050_async_creation_loop" for item in applied)
        assert apply(db, DEFAULT_MIGRATIONS_DIR) == []


class _FaultyConnection:
    """Delegating connection wrapper that raises on a matched statement."""

    def __init__(self, conn: sqlite3.Connection, fail_on: str):
        self._conn = conn
        self._fail_on = fail_on

    def execute(self, sql, *args):
        if self._fail_on in sql:
            raise RuntimeError("injected mid-rebuild failure")
        return self._conn.execute(sql, *args)

    def __getattr__(self, name):
        return getattr(self._conn, name)


class TestRebuildAtomicity:
    """Post-step table rebuilds must be atomic and retry-safe (048 pattern)."""

    def test_expand_intent_action_types_rolls_back_on_failure(self, tmp_path):
        from app.data.migrations.runner import (
            _expand_intent_action_types,
            _intent_action_table_sql,
        )

        db = tmp_path / "intent.db"
        apply(db, _through(tmp_path, 34))

        with sqlite3.connect(db) as conn:
            _seed_parents(conn)
            conn.execute(
                "INSERT INTO next_best_actions ("
                "id,owner_user_id,action_type,title,reason,"
                "estimated_effort_minutes,fallback_action_json,status,"
                "idempotency_key,request_hash,created_at,updated_at"
                ") VALUES ('a1','owner-1','create_project','t','r',5,'{}',"
                "'proposed','k1','h1','2026-08-08T00:00:00Z','2026-08-08T00:00:00Z')"
            )
            conn.commit()

            faulty = _FaultyConnection(conn, "DROP TABLE next_best_actions")
            with pytest.raises(RuntimeError):
                _expand_intent_action_types(
                    faulty, "'lock_intent'", _intent_action_table_sql
                )

            # The failure must roll back as one unit: no leftover rebuild
            # table, the original table and its rows intact, no open
            # transaction, and FK enforcement restored.
            assert "next_best_actions_intent_new" not in _table_names(conn)
            (count,) = conn.execute(
                "SELECT COUNT(*) FROM next_best_actions"
            ).fetchone()
            assert count == 1
            assert conn.in_transaction is False
            (fk,) = conn.execute("PRAGMA foreign_keys").fetchone()
            assert fk == 1

            # A retry after the failure completes the rebuild.
            _expand_intent_action_types(
                conn, "'lock_intent'", _intent_action_table_sql
            )
            (sql,) = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' "
                "AND name='next_best_actions'"
            ).fetchone()
        assert "'lock_intent'" in sql

    def test_rebuild_survives_leftover_new_tables(self, tmp_path):
        """A crash between CREATE and DROP of the *_new table on a previous
        startup must not wedge the next run with 'table already exists'."""
        db = tmp_path / "leftover.db"
        # Stop before 034 so the 034/035/036 post-steps still run and each
        # encounters its crashed-run leftover.
        apply(db, _through(tmp_path, 33))

        with sqlite3.connect(db) as conn:
            # Simulate the leftovers a crashed rebuild would leave behind.
            conn.execute("CREATE TABLE next_best_actions_intent_new (id TEXT)")
            conn.execute("CREATE TABLE content_projects_intent_new (id TEXT)")
            conn.execute("CREATE TABLE creator_series_scope_new (id TEXT)")
            conn.commit()

        # 034/035/036 post-steps rebuild content_projects, next_best_actions
        # and creator_series; the full apply must finish cleanly despite the
        # debris.
        apply(db, DEFAULT_MIGRATIONS_DIR)

        with sqlite3.connect(db) as conn:
            tables = _table_names(conn)
        leftovers = {t for t in tables if t.endswith("_new")}
        assert not leftovers, f"leftover rebuild tables: {sorted(leftovers)}"

    def test_action_lifecycle_rebuild_survives_leftover_new_tables(self, tmp_path):
        db = tmp_path / "leftover-030.db"
        apply(db, _through(tmp_path, 29))

        with sqlite3.connect(db) as conn:
            # Fresh 020 tables already ship the expanded CHECKs, so revert
            # them to the pre-phase-16 legacy shape that actually triggers
            # the 030 rebuild (drop + recreate from the stored DDL).
            for table, pattern, legacy in (
                (
                    "next_best_actions",
                    r"'proposed','accepted','deferred','completed','superseded',"
                    r"\s*'failed','expired','cancelled'",
                    "'proposed','accepted','deferred','completed','superseded'",
                ),
                (
                    "action_events",
                    r"'gate_confirmed','gate_rejected','fallback_used',"
                    r"\s*'rejected','failed','expired','cancelled'",
                    "'gate_confirmed','gate_rejected','fallback_used'",
                ),
            ):
                (stored,) = conn.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                    (table,),
                ).fetchone()
                legacy_sql = re.sub(pattern, legacy, stored, count=1)
                assert legacy_sql != stored, f"failed to revert {table} CHECK"
                conn.execute(f"DROP TABLE {table}")
                conn.execute(legacy_sql)
            # Simulate the leftovers a crashed rebuild would leave behind.
            conn.execute("CREATE TABLE next_best_actions_lifecycle_new (id TEXT)")
            conn.execute("CREATE TABLE action_events_lifecycle_new (id TEXT)")
            conn.commit()

        apply(db, DEFAULT_MIGRATIONS_DIR)

        with sqlite3.connect(db) as conn:
            tables = _table_names(conn)
            (action_sql,) = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' "
                "AND name='next_best_actions'"
            ).fetchone()
        leftovers = {t for t in tables if t.endswith("_new")}
        assert not leftovers, f"leftover rebuild tables: {sorted(leftovers)}"
        assert "'failed','expired','cancelled'" in action_sql
