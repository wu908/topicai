"""Migration runner for TopicAI v4.0 (Spec-007 T003 + T004).

Provides an idempotent :func:`apply` that scans ``app/data/migrations/``
for ``NNN_*.sql`` files, applies any whose version is not already
recorded in ``schema_migrations``, and writes back the version + checksum.

The runner is wired into the FastAPI ``lifespan`` startup hook in
``main.py`` so that the database schema is always in sync with the code
on first boot of a fresh deployment.

Design choices:

* Idempotent — running :func:`apply` twice is a no-op on the second call.
* Deterministic ordering — files are sorted by ``NNN`` prefix.
* Self-verifying — each migration's SHA-256 is recorded so tampering
  with an applied file is detectable (logged, not yet enforced).
* Bounded — applies in one short transaction per migration; a failure
  rolls back that single migration and aborts the rest of the run.

Post-step registry (Bug 3 fix)
------------------------------
SQLite has no ``ALTER TABLE ADD COLUMN IF NOT EXISTS`` and a plain
``CREATE TABLE IF NOT EXISTS`` is a *no-op* on an existing table, so a
migration that only adds columns is silently skipped on a database that
predates the column addition (this caused Bug 3: ``/reviews/list`` 500
"no such column"). Pure SQL cannot conditionally add a column, so the
runner pairs each ``NNN_*.sql`` with an optional Python *post-step* — a
callable registered in :data:`MIGRATION_POST_STEPS` keyed by the
migration's stem (``version = path.stem``, e.g. ``"003_effect_reviews"``).

The post-step runs *after* the ``.sql`` script and is responsible for:

* :func:`_ensure_columns` — back-fill any additive columns on an
  existing table (guarded by ``PRAGMA table_info`` so it is a no-op on a
  fresh DB that already has them, and a no-op when the table itself does
  not yet exist — the ``.sql`` ``CREATE TABLE`` builds it in that case).
* Any index ``CREATE INDEX IF NOT EXISTS`` that references a back-filled
  column (the ``.sql`` cannot create such an index up-front because the
  column does not exist yet on an old DB; moving the index into the
  post-step keeps the ``.sql`` ``CREATE TABLE IF NOT EXISTS`` intact as
  the fresh-DB fast path).

The registry is intentionally tiny and explicit — one entry per
migration that needs Python-driven back-fill.
"""

from __future__ import annotations

import hashlib
import logging
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_MIGRATIONS_DIR = Path(__file__).resolve().parent

#: A post-step callable receives the live connection and runs after the
#: matching ``.sql`` script. Keyed by migration stem (``path.stem``).
PostStep = Callable[[sqlite3.Connection], None]


@dataclass(frozen=True)
class AppliedMigration:
    """A migration that was applied during this run."""

    version: str
    applied_at: str
    checksum: str


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _list_migration_files(migrations_dir: Path) -> list[Path]:
    """Return ``NNN_*.sql`` files in deterministic order.

    Files without a 3-digit numeric prefix are ignored (guards against
    ad-hoc notes living in the same directory).
    """
    if not migrations_dir.exists():
        return []
    return sorted(p for p in migrations_dir.glob("[0-9][0-9][0-9]_*.sql"))


def _ensure_schema_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version    TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL,
            checksum   TEXT NOT NULL
        )
        """
    )


def _already_applied(conn: sqlite3.Connection) -> dict[str, str]:
    return {
        row[0]: row[1]
        for row in conn.execute("SELECT version, checksum FROM schema_migrations").fetchall()
    }


def _existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    """Return the column names of ``table`` (empty set if the table does
    not exist — ``PRAGMA table_info`` returns no rows for missing tables)."""
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _ensure_columns(
    conn: sqlite3.Connection,
    table: str,
    columns: list[tuple[str, str]],
) -> None:
    """Back-fill ``columns`` on ``table`` if missing.

    Each entry is ``(name, ddl_type_fragment)`` where ``ddl_type_fragment``
    is everything that follows ``ADD COLUMN`` — e.g. ``"TEXT NOT NULL
    DEFAULT ''"``. SQLite has no ``ADD COLUMN IF NOT EXISTS``, so we guard
    with ``PRAGMA table_info``. If ``table`` does not exist the call is a
    no-op (the ``.sql`` ``CREATE TABLE`` is expected to build it on a
    fresh DB). Safe to call repeatedly — already-present columns are
    skipped.
    """
    present = _existing_columns(conn, table)
    if not present:
        # Table does not exist yet — the .sql CREATE TABLE handles fresh
        # DBs; nothing to back-fill here.
        return
    for name, ddl_type in columns:
        if name in present:
            continue
        logger.info("Back-filling column %s on %s", name, table)
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl_type}")
        present.add(name)


def _post_step_003_effect_reviews(conn: sqlite3.Connection) -> None:
    """Post-step for ``003_effect_reviews``.

    On an existing DB whose ``effect_reviews`` predates the additive
    columns, back-fill them (Bug 3). On a fresh DB the ``.sql``
    ``CREATE TABLE`` already produced the full schema and this is a
    no-op. The two ``CREATE INDEX`` statements that reference the
    back-filled ``status`` column live here (not in the ``.sql``) so
    they cannot fire before the column exists.
    """
    _ensure_columns(
        conn,
        "effect_reviews",
        [
            ("content_outline", "TEXT NOT NULL DEFAULT ''"),
            ("actual_result", "TEXT"),
            ("attribution", "TEXT"),
            ("learnings", "TEXT"),
            ("status", "TEXT NOT NULL DEFAULT 'awaiting_actuals'"),
            ("updated_at", "TEXT NOT NULL DEFAULT ''"),
        ],
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_effect_reviews_user_id_created_at "
        "ON effect_reviews (user_id, created_at DESC)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_effect_reviews_status "
        "ON effect_reviews (status)"
    )


def _post_step_030_action_lifecycle(conn: sqlite3.Connection) -> None:
    """Expand action status constraints for databases created before phase 16."""
    action_sql_row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='next_best_actions'"
    ).fetchone()
    event_sql_row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='action_events'"
    ).fetchone()
    if not action_sql_row or not event_sql_row:
        return
    action_sql = action_sql_row[0]
    event_sql = event_sql_row[0]
    if "'failed','expired','cancelled'" in action_sql and "'rejected','failed'" in event_sql:
        return

    action_new = action_sql.replace(
        "CREATE TABLE next_best_actions",
        "CREATE TABLE next_best_actions_lifecycle_new",
        1,
    ).replace(
        "'proposed','accepted','deferred','completed','superseded'",
        "'proposed','accepted','deferred','completed','superseded','failed','expired','cancelled'",
        1,
    )
    event_new = event_sql.replace(
        "CREATE TABLE action_events",
        "CREATE TABLE action_events_lifecycle_new",
        1,
    ).replace(
        "'gate_confirmed','gate_rejected','fallback_used'",
        "'gate_confirmed','gate_rejected','fallback_used','rejected','failed','expired','cancelled'",
        1,
    )
    if action_new == action_sql or event_new == event_sql:
        raise sqlite3.IntegrityError("action lifecycle constraints could not be expanded")

    conn.commit()
    conn.execute("PRAGMA foreign_keys=OFF")
    try:
        conn.execute("DROP TRIGGER IF EXISTS trg_next_best_actions_experiment_context")
        conn.execute("DROP TRIGGER IF EXISTS trg_action_events_experiment_context")
        for table, replacement_sql in (
            ("next_best_actions", action_new),
            ("action_events", event_new),
        ):
            new_table = f"{table}_lifecycle_new"
            conn.execute(replacement_sql)
            columns = [
                row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
            ]
            column_list = ",".join(columns)
            conn.execute(
                f"INSERT INTO {new_table} ({column_list}) "
                f"SELECT {column_list} FROM {table}"
            )
            conn.execute(f"DROP TABLE {table}")
            conn.execute(f"ALTER TABLE {new_table} RENAME TO {table}")

        conn.executescript(
            """
            CREATE UNIQUE INDEX uq_next_best_actions_owner_idempotency
                ON next_best_actions(owner_user_id, idempotency_key);
            CREATE INDEX idx_next_best_actions_owner_status
                ON next_best_actions(owner_user_id, status, updated_at DESC);
            CREATE INDEX idx_next_best_actions_project_status
                ON next_best_actions(project_id, status, updated_at DESC);
            CREATE UNIQUE INDEX uq_action_events_owner_idempotency
                ON action_events(owner_user_id, idempotency_key);
            CREATE INDEX idx_action_events_action_created
                ON action_events(action_id, created_at);
            CREATE INDEX idx_action_events_metrics_window
                ON action_events(owner_user_id, created_at, experiment_id, cohort, event_type);
            CREATE TRIGGER trg_next_best_actions_experiment_context
            AFTER INSERT ON next_best_actions
            WHEN NEW.experiment_id IS NULL
            BEGIN
                UPDATE next_best_actions
                SET experiment_id = (
                        SELECT experiment_id FROM experiment_assignments
                        WHERE owner_user_id=NEW.owner_user_id AND status='active'
                        ORDER BY activated_at DESC, assigned_at DESC LIMIT 1
                    ),
                    cohort = (
                        SELECT cohort FROM experiment_assignments
                        WHERE owner_user_id=NEW.owner_user_id AND status='active'
                        ORDER BY activated_at DESC, assigned_at DESC LIMIT 1
                    )
                WHERE id=NEW.id;
            END;
            CREATE TRIGGER trg_action_events_experiment_context
            AFTER INSERT ON action_events
            BEGIN
                UPDATE action_events
                SET experiment_id = COALESCE(
                        NEW.experiment_id,
                        (SELECT experiment_id FROM next_best_actions WHERE id=NEW.action_id),
                        (SELECT experiment_id FROM experiment_assignments
                         WHERE owner_user_id=NEW.owner_user_id AND status='active'
                         ORDER BY activated_at DESC, assigned_at DESC LIMIT 1)
                    ),
                    cohort = COALESCE(
                        NEW.cohort,
                        (SELECT cohort FROM next_best_actions WHERE id=NEW.action_id),
                        (SELECT cohort FROM experiment_assignments
                         WHERE owner_user_id=NEW.owner_user_id AND status='active'
                         ORDER BY activated_at DESC, assigned_at DESC LIMIT 1)
                    ),
                    ai_trace_id = COALESCE(
                        NEW.ai_trace_id,
                        (SELECT ai_trace_id FROM next_best_actions WHERE id=NEW.action_id)
                    ),
                    model_version = COALESCE(
                        NEW.model_version,
                        (SELECT model_identifier FROM ai_traces_v2 WHERE id=(
                            SELECT ai_trace_id FROM next_best_actions WHERE id=NEW.action_id
                        ))
                    ),
                    prompt_version = COALESCE(
                        NEW.prompt_version,
                        (SELECT policy_version FROM ai_traces_v2 WHERE id=(
                            SELECT ai_trace_id FROM next_best_actions WHERE id=NEW.action_id
                        ))
                    )
                WHERE id=NEW.id;
            END;
            """
        )
        conn.commit()
    finally:
        conn.execute("PRAGMA foreign_keys=ON")
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        raise sqlite3.IntegrityError(f"action lifecycle migration broke foreign keys: {violations}")


#: Migration stem -> post-step callable. Add an entry only when a
#: migration needs Python-driven back-fill that pure SQL cannot express.
MIGRATION_POST_STEPS: dict[str, PostStep] = {
    "003_effect_reviews": _post_step_003_effect_reviews,
    "030_action_lifecycle": _post_step_030_action_lifecycle,
}


def apply(
    db_path: str | Path,
    migrations_dir: str | Path = DEFAULT_MIGRATIONS_DIR,
) -> list[AppliedMigration]:
    """Apply all pending migrations to the SQLite database at ``db_path``.

    Args:
        db_path: Path to the SQLite file. Use ``":memory:"`` for tests.
        migrations_dir: Directory containing ``NNN_*.sql`` files.

    Returns:
        The list of migrations applied during this call (empty when
        the database is already up to date).
    """
    migrations_dir = Path(migrations_dir)
    files = _list_migration_files(migrations_dir)
    if not files:
        logger.info("No migration files found in %s", migrations_dir)
        return []

    applied: list[AppliedMigration] = []
    with sqlite3.connect(db_path) as conn:
        # Align this connection's pragmas with the async engine (init_db sets
        # the same pair on aiosqlite). foreign_keys=ON so the migration's
        # FK-bearing CREATE/ALTER respects constraints; busy_timeout=5000 so
        # a concurrent async-engine write doesn't immediately error the
        # runner's sync connection with "database is locked".
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        _ensure_schema_migrations_table(conn)
        known = _already_applied(conn)

        for path in files:
            version = path.stem  # e.g. "001_bootstrap"
            sql = path.read_text(encoding="utf-8")
            checksum = _sha256(sql)

            if version in known:
                if known[version] != checksum:
                    logger.warning(
                        "Migration %s checksum drift (recorded=%s current=%s)",
                        version,
                        known[version],
                        checksum,
                    )
                continue

            logger.info("Applying migration %s", version)
            conn.executescript(sql)
            post_step = MIGRATION_POST_STEPS.get(version)
            if post_step is not None:
                logger.info("Running post-step for %s", version)
                post_step(conn)
            conn.execute(
                "INSERT INTO schema_migrations(version, applied_at, checksum) "
                "VALUES (?, datetime('now'), ?)",
                (version, checksum),
            )
            conn.commit()
            applied.append(
                AppliedMigration(
                    version=version,
                    applied_at=conn.execute("SELECT datetime('now')").fetchone()[0],
                    checksum=checksum,
                )
            )

    logger.info("Migration run complete: %d applied", len(applied))
    return applied


def status(
    db_path: str | Path,
    migrations_dir: str | Path = DEFAULT_MIGRATIONS_DIR,
) -> tuple[list[str], list[str]]:
    """Return ``(pending_versions, applied_versions)`` for diagnostics."""
    migrations_dir = Path(migrations_dir)
    files = _list_migration_files(migrations_dir)
    versions: list[str] = [p.stem for p in files]

    with sqlite3.connect(db_path) as conn:
        _ensure_schema_migrations_table(conn)
        applied = sorted(_already_applied(conn).keys())

    pending = [v for v in versions if v not in applied]
    return pending, applied


__all__ = [
    "AppliedMigration",
    "MIGRATION_POST_STEPS",
    "apply",
    "status",
]
