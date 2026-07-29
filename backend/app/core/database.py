"""SQLite database module for TopicAI v4.0.

Provides WAL mode SQLite connection via aiosqlite with SQLAlchemy async engine.
All database operations go through this module — no raw SQL elsewhere.
"""

import asyncio
import logging
import sqlite3
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)

# ==================== Schema (retired in T104) ====================
# The SQL_SCHEMA big-string that lived here has been removed: schema
# creation is now the migration runner's sole responsibility, invoked
# via Database.apply_migrations() from init_db. Keeping the CREATE
# TABLEs here was the other half of the dual source-of-truth debt
# (the NNN_*.sql migrations were the other) and caused Bug 3. See
# tests/data/test_schema_single_source_of_truth.py for the lock-down.


# ==================== Database Manager ====================


def _split_sql_statements(sql: str) -> list[str]:
    """Split a multi-statement SQL blob into individual executable statements.

    Strips SQL comments first, then uses SQLite's parser to identify complete
    statements. This preserves compound statements such as triggers, whose
    bodies legitimately contain semicolons.

    * Whole-line ``--`` comments are dropped.
    * Inline ``-- ...`` tails are stripped, but only when the ``--`` is NOT
      inside a single-quoted string literal (so a default value like
      ``'a--b'`` survives). The migration files are pure DDL with no such
      literals, but the guard keeps this safe for future use.

    Splitting before comment-stripping would mis-split on a ``;`` inside a
    comment (e.g. ``-- ... lacked; effect_reviews`` leaked the bare token
    ``effect_reviews`` as a statement; ``-- UTC;]`` truncated a CREATE
    TABLE with "incomplete input"). Comment-only and empty blocks drop out.
    """
    without_comments_lines: list[str] = []
    for line in sql.split("\n"):
        stripped = line.strip()
        if stripped.startswith("--"):
            continue  # whole-line comment
        # Strip an inline -- comment that is outside a string literal.
        in_string = False
        cut = len(line)
        i = 0
        while i < len(line) - 1:
            ch = line[i]
            if ch == "'":
                in_string = not in_string
            elif not in_string and ch == "-" and line[i + 1] == "-":
                cut = i
                break
            i += 1
        without_comments_lines.append(line[:cut])
    without_comments = "\n".join(without_comments_lines)

    statements: list[str] = []
    buffer = ""
    for character in without_comments:
        buffer += character
        if character == ";" and sqlite3.complete_statement(buffer):
            stmt = buffer.strip()
            if stmt:
                statements.append(stmt)
            buffer = ""
    remainder = buffer.strip()
    if remainder:
        statements.append(remainder)
    return statements


class Database:
    """Async SQLite database manager with WAL mode.

    Provides connection pooling, schema initialization, and CRUD operations.
    All database access should go through this class.
    """

    def __init__(self, database_url: str):
        """Initialize the database manager.

        Args:
            database_url: SQLAlchemy database URL (e.g., sqlite+aiosqlite:///...).
        """
        self.database_url = database_url
        self.engine = None
        self.session_factory = None

    async def init_db(self) -> None:
        """Initialize the database engine and apply the migration-managed schema.

        Enables WAL mode, per-connection pragmas, then delegates ALL table
        creation to :meth:`apply_migrations` (the migration runner). The
        legacy ``SQL_SCHEMA`` big-string has been retired (Spec-007 dual-
        schema-debt consolidation, T104) so the migration runner is the
        sole schema authority — drift between SQL_SCHEMA and the
        ``NNN_*.sql`` migrations can no longer occur.
        """
        # Create engine with SQLite optimizations
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            connect_args={
                "check_same_thread": False,  # Required for async SQLite
            },
            pool_pre_ping=True,
        )

        # Enable WAL mode + per-connection pragmas (MUST be in same
        # connection for :memory:). These are runtime behavior, not schema.
        async with self.engine.begin() as conn:
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA foreign_keys=ON"))
            await conn.execute(text("PRAGMA busy_timeout=5000"))

        # The migration runner creates every table (000_initial + 001-006).
        await self.apply_migrations()

        # Create session factory
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info("Database initialized (migration-managed) with WAL mode")

    # ==================== Migration bridge (T102) ====================

    def _raw_path(self) -> str | None:
        """Strip the SQLAlchemy driver prefix to a raw sqlite3 file path.

        ``sqlite+aiosqlite:///./data/topicai.db`` -> ``./data/topicai.db``.
        ``sqlite+aiosqlite:///:memory:`` -> ``None`` (signals the memory
        branch of :meth:`apply_migrations`, because a sync
        ``sqlite3.connect(":memory:")`` would open a *different* in-memory DB
        than this instance's aiosqlite engine).

        Returns:
            The raw file path, or ``None`` for in-memory URLs.
        """
        if "///" in self.database_url:
            raw = self.database_url.split("///", 1)[-1]
            # ``sqlite+aiosqlite:///:memory:`` splits to ``:memory:``; treat
            # that as memory too (sync sqlite3 would diverge from aiosqlite).
            if raw == ":memory:":
                return None
            return raw
        return None

    async def apply_migrations(self) -> None:
        """Apply pending migrations through this instance's database.

        Two paths converge on the migration runner's idempotent + checksum +
        post-step machinery:

        * **File DB** (``_raw_path()`` is a real path): the sync runner is
          invoked via ``asyncio.to_thread`` against the SAME sqlite file the
          async engine uses. Reuses the runner's full power unchanged.
        * **In-memory DB** (``_raw_path()`` returns ``None``): a sync
          ``sqlite3.connect(":memory:")`` would be a different DB than this
          aiosqlite engine, so each migration file is executed through that
          engine. Migration 034's table rebuild is then applied on the same
          connection using the runner's shared CREATE TABLE statement.

        Must be called after :meth:`init_db` has created the engine (or the
        caller creates the engine itself for the memory path). ``init_db``
        itself calls this once the pragmas + session factory are set up.
        """
        from app.data.migrations.runner import (
            _CREATOR_SERIES_SCOPE_SQL,
            _INTENT_ACTION_EVENT_TRIGGER_SQL,
            _INTENT_ACTION_INDEX_TRIGGER_SQL,
            _INTENT_MODEL_CONTENT_PROJECTS_SQL,
            DEFAULT_MIGRATIONS_DIR,
            _intent_action_table_sql,
            _list_migration_files,
            _scope_learning_table_sql,
            _sha256,
        )

        raw_path = self._raw_path()
        if raw_path is not None:
            # File DB: delegate to the sync runner on a worker thread so the
            # event loop is not blocked by stdlib sqlite3 I/O.
            from app.data.migrations.runner import apply as _runner_apply

            await asyncio.to_thread(_runner_apply, raw_path, DEFAULT_MIGRATIONS_DIR)
            return

        # In-memory DB: replay migrations through the aiosqlite engine so the
        # schema lands on the SAME in-memory database the app/tests use.
        files = _list_migration_files(DEFAULT_MIGRATIONS_DIR)
        if not files:
            return

        applied_any = False
        # SQLAlchemy's async ``conn.execute(text(script))`` rejects multi-
        # statement scripts (ObjectNotExecutableError), and the aiosqlite
        # DBAPI connection exposes an *async* ``executescript`` that can't be
        # driven from ``run_sync`` (its calls return coroutines). So the
        # memory path splits each migration file into statements — the same
        # ``split(';')`` + comment-strip idiom ``init_db`` uses for
        # SQL_SCHEMA — and runs them one-by-one via the async connection.
        # Post-steps are skipped on the memory path: ``000_initial_schema``
        # ships the full-column baseline, so the legacy-DB back-fill the
        # post-steps provide is redundant on a fresh memory DB.
        async with self.engine.begin() as conn:  # type: ignore[union-attr]
            await conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS schema_migrations ("
                    "version TEXT PRIMARY KEY, applied_at TEXT NOT NULL, "
                    "checksum TEXT NOT NULL)"
                )
            )
            known = {
                row[0]
                for row in (
                    await conn.execute(
                        text("SELECT version FROM schema_migrations")
                    )
                ).fetchall()
            }
            for path in files:
                version = path.stem
                if version in known:
                    continue
                sql = path.read_text(encoding="utf-8")
                for stmt in _split_sql_statements(sql):
                    await conn.execute(text(stmt))
                await conn.execute(
                    text(
                        "INSERT INTO schema_migrations(version, applied_at, "
                        "checksum) VALUES (:v, datetime('now'), :c)"
                    ),
                    {"v": version, "c": _sha256(sql)},
                )
                applied_any = True
                logger.info("Applied migration %s (memory path)", version)
        if applied_any:
            logger.info("Migration run complete (memory path)")

        async with self.engine.connect() as conn:  # type: ignore[union-attr]
            action_sql = (
                await conn.execute(
                    text(
                        "SELECT sql FROM sqlite_master "
                        "WHERE type='table' AND name='next_best_actions'"
                    )
                )
            ).scalar_one_or_none()
            # Migrations 035 and 038 each widen the action_type CHECK. Both are
            # replayed in one rebuild here; the string transforms compose because
            # each only adds its own value.
            if action_sql and (
                "'lock_intent'" not in action_sql or "'scope_learning'" not in action_sql
            ):
                await conn.commit()
                await conn.execute(text("PRAGMA foreign_keys=OFF"))
                await conn.commit()
                try:
                    await conn.execute(
                        text(
                            "DROP TRIGGER IF EXISTS "
                            "trg_next_best_actions_experiment_context"
                        )
                    )
                    await conn.execute(
                        text(
                            "DROP TRIGGER IF EXISTS "
                            "trg_action_events_experiment_context"
                        )
                    )
                    columns = [
                        row[1]
                        for row in (
                            await conn.execute(
                                text("PRAGMA table_info(next_best_actions)")
                            )
                        ).fetchall()
                    ]
                    column_list = ",".join(columns)
                    await conn.execute(
                        text(
                            _scope_learning_table_sql(
                                _intent_action_table_sql(action_sql)
                            )
                        )
                    )
                    await conn.execute(
                        text(
                            f"INSERT INTO next_best_actions_intent_new ({column_list}) "
                            f"SELECT {column_list} FROM next_best_actions"
                        )
                    )
                    await conn.execute(text("DROP TABLE next_best_actions"))
                    await conn.execute(
                        text(
                            "ALTER TABLE next_best_actions_intent_new "
                            "RENAME TO next_best_actions"
                        )
                    )
                    await conn.commit()
                finally:
                    await conn.execute(text("PRAGMA foreign_keys=ON"))
                    await conn.commit()
            if action_sql:
                for sql in (
                    _INTENT_ACTION_INDEX_TRIGGER_SQL,
                    _INTENT_ACTION_EVENT_TRIGGER_SQL,
                ):
                    for stmt in _split_sql_statements(sql):
                        await conn.execute(text(stmt))
                await conn.commit()

            table_sql = (
                await conn.execute(
                    text(
                        "SELECT sql FROM sqlite_master "
                        "WHERE type='table' AND name='content_projects'"
                    )
                )
            ).scalar_one_or_none()
            if table_sql and "'working_confirmed'" not in table_sql:
                await conn.commit()
                await conn.execute(text("PRAGMA foreign_keys=OFF"))
                await conn.commit()
                try:
                    columns = [
                        row[1]
                        for row in (
                            await conn.execute(text("PRAGMA table_info(content_projects)"))
                        ).fetchall()
                    ]
                    column_list = ",".join(columns)
                    await conn.execute(text(_INTENT_MODEL_CONTENT_PROJECTS_SQL))
                    await conn.execute(
                        text(
                            f"INSERT INTO content_projects_intent_new ({column_list}) "
                            f"SELECT {column_list} FROM content_projects"
                        )
                    )
                    await conn.execute(text("DROP TABLE content_projects"))
                    await conn.execute(
                        text(
                            "ALTER TABLE content_projects_intent_new "
                            "RENAME TO content_projects"
                        )
                    )
                    await conn.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS idx_content_projects_owner_status "
                            "ON content_projects(owner_user_id, status, updated_at)"
                        )
                    )
                    await conn.execute(
                        text(
                            "CREATE UNIQUE INDEX IF NOT EXISTS "
                            "uq_content_projects_owner_idempotency "
                            "ON content_projects(owner_user_id, idempotency_key) "
                            "WHERE idempotency_key IS NOT NULL"
                        )
                    )
                    await conn.commit()
                finally:
                    await conn.execute(text("PRAGMA foreign_keys=ON"))
                    await conn.commit()
                violations = (
                    await conn.execute(text("PRAGMA foreign_key_check"))
                ).fetchall()
                if violations:
                    raise sqlite3.IntegrityError(
                        f"intent model migration broke foreign keys: {violations}"
                    )

            # Migration 036 (Spec-011): creator_series.content_intent /
            # content_format become nullable, because a series is connected by
            # an ongoing audience promise and its members may differ. Same
            # rebuild-on-the-same-connection shape as 034 above, since 026
            # created the table with NOT NULL and the memory path skips
            # post-steps.
            series_sql = (
                await conn.execute(
                    text(
                        "SELECT sql FROM sqlite_master "
                        "WHERE type='table' AND name='creator_series'"
                    )
                )
            ).scalar_one_or_none()
            if series_sql and "content_intent IS NULL" not in series_sql:
                await conn.commit()
                await conn.execute(text("PRAGMA foreign_keys=OFF"))
                await conn.commit()
                try:
                    columns = [
                        row[1]
                        for row in (
                            await conn.execute(text("PRAGMA table_info(creator_series)"))
                        ).fetchall()
                    ]
                    column_list = ",".join(columns)
                    await conn.execute(text(_CREATOR_SERIES_SCOPE_SQL))
                    await conn.execute(
                        text(
                            f"INSERT INTO creator_series_scope_new ({column_list}) "
                            f"SELECT {column_list} FROM creator_series"
                        )
                    )
                    await conn.execute(text("DROP TABLE creator_series"))
                    await conn.execute(
                        text(
                            "ALTER TABLE creator_series_scope_new "
                            "RENAME TO creator_series"
                        )
                    )
                    await conn.execute(
                        text(
                            "CREATE UNIQUE INDEX IF NOT EXISTS "
                            "uq_creator_series_owner_idempotency "
                            "ON creator_series(owner_user_id, idempotency_key)"
                        )
                    )
                    await conn.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS idx_creator_series_owner_status "
                            "ON creator_series(owner_user_id, status, updated_at DESC)"
                        )
                    )
                    await conn.commit()
                finally:
                    await conn.execute(text("PRAGMA foreign_keys=ON"))
                    await conn.commit()
                violations = (
                    await conn.execute(text("PRAGMA foreign_key_check"))
                ).fetchall()
                if violations:
                    raise sqlite3.IntegrityError(
                        f"creator series scope migration broke foreign keys: {violations}"
                    )

    async def get_session(self) -> AsyncSession:
        """Get a new async database session.

        Returns:
            AsyncSession: A new SQLAlchemy async session.

        Raises:
            RuntimeError: If the database has not been initialized.
        """
        if self.session_factory is None:
            raise RuntimeError(
                "Database not initialized. Call init_db() first."
            )
        return self.session_factory()

    async def close(self) -> None:
        """Close the database engine and release all connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")

    async def execute(self, query: str, params: dict | None = None) -> Any:
        """Execute a raw SQL query.

        Args:
            query: SQL query string.
            params: Query parameters.

        Returns:
            Query result.
        """
        async with await self.get_session() as session:
            result = await session.execute(text(query), params or {})
            await session.commit()
            return result

    async def fetch_all(
        self, query: str, params: dict | None = None
    ) -> list[dict]:
        """Execute a SELECT query and return all rows as dictionaries.

        Args:
            query: SELECT SQL query.
            params: Query parameters.

        Returns:
            List of dictionaries, one per row.
        """
        async with await self.get_session() as session:
            result = await session.execute(text(query), params or {})
            rows = result.fetchall()
            if not rows:
                return []
            columns = list(result.keys())
            return [dict(zip(columns, row, strict=False)) for row in rows]

    async def fetch_one(
        self, query: str, params: dict | None = None
    ) -> dict | None:
        """Execute a SELECT query and return the first row.

        Args:
            query: SELECT SQL query.
            params: Query parameters.

        Returns:
            Dictionary of the first row, or None if no rows.
        """
        async with await self.get_session() as session:
            result = await session.execute(text(query), params or {})
            row = result.fetchone()
            if row is None:
                return None
            columns = list(result.keys())
            return dict(zip(columns, row, strict=False))

    async def insert(
        self, table: str, data: dict[str, Any]
    ) -> None:
        """Insert a row into a table.

        Args:
            table: Table name.
            data: Column-value mapping.
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f":{k}" for k in data.keys()])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        async with await self.get_session() as session:
            await session.execute(text(query), data)
            await session.commit()

    async def update(
        self,
        table: str,
        data: dict[str, Any],
        where: dict[str, Any],
    ) -> int:
        """Update rows in a table.

        Args:
            table: Table name.
            data: Column-value mapping for SET clause.
            where: Column-value mapping for WHERE clause.

        Returns:
            Number of rows affected.
        """
        set_clause = ", ".join([f"{k} = :set_{k}" for k in data.keys()])
        where_clause = " AND ".join(
            [f"{k} = :where_{k}" for k in where.keys()]
        )
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

        params = {}
        for k, v in data.items():
            params[f"set_{k}"] = v
        for k, v in where.items():
            params[f"where_{k}"] = v

        async with await self.get_session() as session:
            result = await session.execute(text(query), params)
            await session.commit()
            return result.rowcount

    async def delete(
        self, table: str, where: dict[str, Any]
    ) -> int:
        """Delete rows from a table.

        Args:
            table: Table name.
            where: Column-value mapping for WHERE clause.

        Returns:
            Number of rows deleted.
        """
        where_clause = " AND ".join(
            [f"{k} = :{k}" for k in where.keys()]
        )
        query = f"DELETE FROM {table} WHERE {where_clause}"

        async with await self.get_session() as session:
            result = await session.execute(text(query), where)
            await session.commit()
            return result.rowcount
