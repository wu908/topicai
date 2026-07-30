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
import json
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


_INTENT_ACTION_INDEX_TRIGGER_SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS uq_next_best_actions_owner_idempotency
    ON next_best_actions(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_next_best_actions_owner_status
    ON next_best_actions(owner_user_id, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_next_best_actions_project_status
    ON next_best_actions(project_id, status, updated_at DESC);
CREATE TRIGGER IF NOT EXISTS trg_next_best_actions_experiment_context
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
"""

_INTENT_ACTION_EVENT_TRIGGER_SQL = """
CREATE TRIGGER IF NOT EXISTS trg_action_events_experiment_context
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


def _intent_action_table_sql(action_sql: str) -> str:
    return action_sql.replace(
        "CREATE TABLE next_best_actions",
        "CREATE TABLE next_best_actions_intent_new",
        1,
    ).replace(
        'CREATE TABLE "next_best_actions"',
        "CREATE TABLE next_best_actions_intent_new",
        1,
    ).replace(
        "'create_project','confirm_intent','answer_key_question'",
        "'create_project','confirm_intent','lock_intent','answer_key_question'",
        1,
    )


def _scope_learning_table_sql(action_sql: str) -> str:
    """Widen the action_type CHECK for scope_learning, renaming if needed.

    The rename is skipped when the caller already renamed the table (the
    in-memory migration path composes this with _intent_action_table_sql), since
    "CREATE TABLE next_best_actions" is a prefix of the renamed form and would
    otherwise be rewritten twice.
    """
    renamed = (
        action_sql
        if "next_best_actions_intent_new" in action_sql
        else action_sql.replace(
            "CREATE TABLE next_best_actions",
            "CREATE TABLE next_best_actions_intent_new",
            1,
        ).replace(
            'CREATE TABLE "next_best_actions"',
            "CREATE TABLE next_best_actions_intent_new",
            1,
        )
    )
    return renamed.replace(
        "'confirm_learning','manage_learning'",
        "'confirm_learning','manage_learning','scope_learning'",
        1,
    )


def _observation_window_table_sql(action_sql: str) -> str:
    """Widen the action_type CHECK for await_observation_window."""
    renamed = (
        action_sql
        if "next_best_actions_intent_new" in action_sql
        else action_sql.replace(
            "CREATE TABLE next_best_actions",
            "CREATE TABLE next_best_actions_intent_new",
            1,
        ).replace(
            'CREATE TABLE "next_best_actions"',
            "CREATE TABLE next_best_actions_intent_new",
            1,
        )
    )
    return renamed.replace(
        "'scope_learning'",
        "'scope_learning','await_observation_window'",
        1,
    )


def _expand_intent_action_types(
    conn: sqlite3.Connection,
    sentinel: str,
    build_sql: Callable[[str], str],
) -> None:
    """Rebuild next_best_actions so its action_type CHECK accepts one more value.

    SQLite cannot alter a CHECK constraint in place, so the table is recreated
    with the same foreign_keys=OFF pattern as _post_step_030_action_lifecycle.
    """
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='next_best_actions'"
    ).fetchone()
    if not row:
        return
    if sentinel not in row[0]:
        replacement_sql = build_sql(row[0])
        if replacement_sql == row[0]:
            raise sqlite3.IntegrityError("intent action constraint could not be expanded")

        conn.commit()
        conn.execute("PRAGMA foreign_keys=OFF")
        try:
            conn.execute("DROP TRIGGER IF EXISTS trg_next_best_actions_experiment_context")
            conn.execute("DROP TRIGGER IF EXISTS trg_action_events_experiment_context")
            conn.execute(replacement_sql)
            columns = [
                item[1]
                for item in conn.execute("PRAGMA table_info(next_best_actions)").fetchall()
            ]
            column_list = ",".join(columns)
            conn.execute(
                f"INSERT INTO next_best_actions_intent_new ({column_list}) "
                f"SELECT {column_list} FROM next_best_actions"
            )
            conn.execute("DROP TABLE next_best_actions")
            conn.execute(
                "ALTER TABLE next_best_actions_intent_new RENAME TO next_best_actions"
            )
            conn.commit()
        finally:
            conn.execute("PRAGMA foreign_keys=ON")

    conn.executescript(_INTENT_ACTION_INDEX_TRIGGER_SQL)
    conn.executescript(_INTENT_ACTION_EVENT_TRIGGER_SQL)
    conn.commit()
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        raise sqlite3.IntegrityError(
            f"intent action migration broke foreign keys: {violations}"
        )


def _post_step_035_intent_lock_action(conn: sqlite3.Connection) -> None:
    _expand_intent_action_types(conn, "'lock_intent'", _intent_action_table_sql)


def _post_step_038_scope_learning_action(conn: sqlite3.Connection) -> None:
    _expand_intent_action_types(conn, "'scope_learning'", _scope_learning_table_sql)


def _post_step_039_observation_window_action(conn: sqlite3.Connection) -> None:
    _expand_intent_action_types(
        conn,
        "'await_observation_window'",
        _observation_window_table_sql,
    )


_INTENT_MODEL_CONTENT_PROJECTS_SQL = """
    CREATE TABLE content_projects_intent_new (
        id                          TEXT PRIMARY KEY,
        owner_user_id               TEXT NOT NULL,
        title                       TEXT NOT NULL,
        status                      TEXT NOT NULL CHECK (status IN (
                                        'inbox','preparing','creating','ready_to_publish',
                                        'published','awaiting_review','settled'
                                    )),
        platform                    TEXT NOT NULL DEFAULT 'xiaohongshu'
                                        CHECK (platform = 'xiaohongshu'),
        format                      TEXT NOT NULL DEFAULT 'graphic_note'
                                        CHECK (format = 'graphic_note'),
        primary_goal                TEXT NOT NULL CHECK (primary_goal IN (
                                        'stable_publish','follower_growth','experiment'
                                    )),
        target_audience             TEXT NOT NULL,
        opportunity_id              TEXT,
        starter_sprint_id           TEXT,
        planned_publish_at          TEXT,
        current_version_id          TEXT,
        locked_publish_version_id   TEXT,
        publish_hypothesis_id       TEXT,
        calibration_state           TEXT NOT NULL DEFAULT 'not_ready' CHECK (calibration_state IN (
                                        'not_ready','insufficient','valid','calibration_invalid'
                                    )),
        last_action                 TEXT,
        last_action_at              TEXT NOT NULL,
        archived_at                 TEXT,
        version                     INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
        idempotency_key             TEXT,
        request_hash                TEXT,
        created_at                  TEXT NOT NULL,
        updated_at                  TEXT NOT NULL,
        deleted_at                  TEXT,
        content_intent              TEXT DEFAULT 'solve'
                                        CHECK (content_intent IN ('solve','share','record')),
        content_format              TEXT NOT NULL DEFAULT 'graphic_note'
                                        CHECK (content_format IN ('graphic_note','vlog_plan')),
        intent_status               TEXT NOT NULL DEFAULT 'legacy_missing'
                                        CHECK (intent_status IN (
                                            'candidate','confirmed','legacy_missing',
                                            'working_confirmed','locked',
                                            'legacy_unclassified','retrospective'
                                        )),
        audience_change             TEXT,
        material_requirements_json  TEXT NOT NULL DEFAULT '[]',
        expected_responses_json     TEXT NOT NULL DEFAULT '[]',
        success_signals_json        TEXT NOT NULL DEFAULT '[]',
        automation_level            TEXT NOT NULL DEFAULT 'guided'
                                        CHECK (automation_level IN ('guided','autopilot_to_ready')),
        creator_state_version       INTEGER NOT NULL DEFAULT 1 CHECK (creator_state_version >= 1),
        intent_locked_at            TEXT,
        retrospective_intent        TEXT
                                        CHECK (retrospective_intent IN ('solve','share','record')
                                               OR retrospective_intent IS NULL),
        FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """


def _post_step_034_intent_model(conn: sqlite3.Connection) -> None:
    """Rebuild content_projects to expand the intent_status CHECK constraint.

    SQLite forbids ALTER CONSTRAINT, so the table is rebuilt. Dropping a
    parent table with foreign_keys=ON would cascade-delete child rows
    (human_gates, next_best_actions, etc.), so this follows the same
    foreign_keys=OFF rebuild pattern as _post_step_030_action_lifecycle.

    Idempotent: if the new intent_status values are already present in the
    table's CHECK constraint, this is a no-op.
    """
    table_sql_row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='content_projects'"
    ).fetchone()
    if not table_sql_row:
        return
    table_sql = table_sql_row[0]

    # Already migrated? The expanded CHECK contains 'working_confirmed'.
    if "'working_confirmed'" in table_sql and "retrospective_intent" in table_sql:
        return

    conn.commit()
    conn.execute("PRAGMA foreign_keys=OFF")
    try:
        conn.execute(_INTENT_MODEL_CONTENT_PROJECTS_SQL)
        # Copy every existing column verbatim; the two new columns default NULL.
        old_columns = [
            row[1]
            for row in conn.execute("PRAGMA table_info(content_projects)").fetchall()
        ]
        column_list = ",".join(old_columns)
        conn.execute(
            f"INSERT INTO content_projects_intent_new ({column_list}) "
            f"SELECT {column_list} FROM content_projects"
        )
        conn.execute("DROP TABLE content_projects")
        conn.execute(
            "ALTER TABLE content_projects_intent_new RENAME TO content_projects"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_content_projects_owner_status "
            "ON content_projects(owner_user_id, status, updated_at)"
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_content_projects_owner_idempotency "
            "ON content_projects(owner_user_id, idempotency_key) "
            "WHERE idempotency_key IS NOT NULL"
        )
        conn.commit()
    finally:
        conn.execute("PRAGMA foreign_keys=ON")
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        raise sqlite3.IntegrityError(
            f"intent model migration broke foreign keys: {violations}"
        )


_CREATOR_SERIES_SCOPE_SQL = """
    CREATE TABLE creator_series_scope_new (
        id TEXT PRIMARY KEY,
        owner_user_id TEXT NOT NULL,
        content_intent TEXT CHECK (content_intent IN ('solve','share','record')
                                   OR content_intent IS NULL),
        content_format TEXT CHECK (content_format IN ('graphic_note','vlog_plan')
                                   OR content_format IS NULL),
        proposed_name TEXT NOT NULL,
        proposed_promise TEXT NOT NULL,
        proposed_rationale TEXT NOT NULL,
        proposed_continuation_prompt TEXT NOT NULL,
        confirmed_name TEXT,
        confirmed_promise TEXT,
        confirmed_continuation_prompt TEXT,
        scope_json TEXT NOT NULL DEFAULT '{}',
        source_project_ids_json TEXT NOT NULL DEFAULT '[]',
        status TEXT NOT NULL CHECK (status IN ('proposed','confirmed','rejected','revoked')),
        proposal_source TEXT NOT NULL CHECK (proposal_source IN ('ai','deterministic_fallback')),
        ai_trace_id TEXT NOT NULL,
        limitations_json TEXT NOT NULL DEFAULT '[]',
        version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
        idempotency_key TEXT NOT NULL,
        request_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        confirmed_at TEXT,
        revoked_at TEXT,
        FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (ai_trace_id) REFERENCES ai_traces_v2(id)
    )
    """


def _backfill_creator_series_scope(conn: sqlite3.Connection) -> None:
    """Record member intent/format sets in scope_json for pre-036 rows.

    Existing rows were built under the same-intent/same-format constraint,
    so each one's single scalar value *is* its complete member set.
    Idempotent: rows that already carry ``member_intents`` are left alone.
    """
    rows = conn.execute(
        "SELECT id, content_intent, content_format, scope_json FROM creator_series"
    ).fetchall()
    for series_id, intent, content_format, scope_json in rows:
        try:
            scope = json.loads(scope_json or "{}")
        except ValueError:
            scope = {}
        if not isinstance(scope, dict):
            scope = {}
        if "member_intents" in scope and "member_formats" in scope:
            continue
        scope["member_intents"] = [intent] if intent else []
        scope["member_formats"] = [content_format] if content_format else []
        conn.execute(
            "UPDATE creator_series SET scope_json=:scope WHERE id=:id",
            {"scope": json.dumps(scope, ensure_ascii=False), "id": series_id},
        )
    conn.commit()


def _post_step_036_creator_series_scope(conn: sqlite3.Connection) -> None:
    """Drop the NOT NULL on creator_series intent/format and back-fill scope.

    Spec-011: a Creator Series is connected by an ongoing audience promise,
    so its members may differ in intent and format. The two scalar columns
    stay for backward compatibility but become nullable — NULL means
    "members disagree, no single value is authoritative".

    SQLite forbids dropping NOT NULL, so the table is rebuilt with the same
    foreign_keys=OFF pattern as _post_step_034_intent_model (creator_series
    is a parent of creator_series_events).

    Idempotent: the rebuild is skipped once the columns are already nullable.
    """
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='creator_series'"
    ).fetchone()
    if not row:
        return
    if "content_intent IS NULL" in row[0]:
        _backfill_creator_series_scope(conn)
        return

    conn.commit()
    conn.execute("PRAGMA foreign_keys=OFF")
    try:
        conn.execute(_CREATOR_SERIES_SCOPE_SQL)
        columns = [
            item[1]
            for item in conn.execute("PRAGMA table_info(creator_series)").fetchall()
        ]
        column_list = ",".join(columns)
        conn.execute(
            f"INSERT INTO creator_series_scope_new ({column_list}) "
            f"SELECT {column_list} FROM creator_series"
        )
        conn.execute("DROP TABLE creator_series")
        conn.execute("ALTER TABLE creator_series_scope_new RENAME TO creator_series")
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_creator_series_owner_idempotency "
            "ON creator_series(owner_user_id, idempotency_key)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_creator_series_owner_status "
            "ON creator_series(owner_user_id, status, updated_at DESC)"
        )
        conn.commit()
    finally:
        conn.execute("PRAGMA foreign_keys=ON")
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        raise sqlite3.IntegrityError(
            f"creator series scope migration broke foreign keys: {violations}"
        )
    _backfill_creator_series_scope(conn)


#: Migration stem -> post-step callable. Add an entry only when a
#: migration needs Python-driven back-fill that pure SQL cannot express.
MIGRATION_POST_STEPS: dict[str, PostStep] = {
    "003_effect_reviews": _post_step_003_effect_reviews,
    "030_action_lifecycle": _post_step_030_action_lifecycle,
    "034_intent_model_migration": _post_step_034_intent_model,
    "035_intent_lock_action": _post_step_035_intent_lock_action,
    "036_creator_series_scope": _post_step_036_creator_series_scope,
    "038_scope_learning_action": _post_step_038_scope_learning_action,
    "039_observation_window_action": _post_step_039_observation_window_action,
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
            if version == "037_capability_trust":
                _ensure_columns(
                    conn,
                    "creator_states",
                    [("capability_trust_json", "TEXT NOT NULL DEFAULT '{}'")],
                )
            else:
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
