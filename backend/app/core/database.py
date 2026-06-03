"""SQLite database module for TopicAI v4.0.

Provides WAL mode SQLite connection via aiosqlite with SQLAlchemy async engine.
All database operations go through this module — no raw SQL elsewhere.
"""

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)

# ==================== SQL Schema ====================

SQL_SCHEMA = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    ai_calls_today INTEGER NOT NULL DEFAULT 0,
    ai_calls_reset_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_login TEXT
);

-- Creator profiles table
CREATE TABLE IF NOT EXISTS creator_profiles (
    id TEXT PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL REFERENCES users(id),
    track TEXT NOT NULL,
    content_formats TEXT NOT NULL,
    production_complexity TEXT NOT NULL,
    content_depth TEXT NOT NULL,
    hotspot_preference TEXT NOT NULL,
    recommendation_mode TEXT NOT NULL,
    rubric_weights TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Topic recommendations table
CREATE TABLE IF NOT EXISTS topic_recommendations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    topics TEXT NOT NULL,
    recommendation_mode TEXT NOT NULL,
    data_source_used TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Viral analyses table
CREATE TABLE IF NOT EXISTS viral_analyses (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    input_type TEXT NOT NULL DEFAULT 'text',
    input_text TEXT NOT NULL,
    input_text_expires_at TEXT,
    viral_score REAL NOT NULL,
    structural_analysis TEXT NOT NULL,
    attributions TEXT NOT NULL,
    transferable_template TEXT NOT NULL,
    rewrite_suggestions TEXT NOT NULL,
    risk_warnings TEXT NOT NULL,
    confidence REAL NOT NULL,
    data_source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Idea boosters table
CREATE TABLE IF NOT EXISTS idea_boosters (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    input_idea TEXT NOT NULL,
    input_idea_expires_at TEXT,
    key_assumptions TEXT NOT NULL,
    feasibility_assessment TEXT NOT NULL,
    title_candidates TEXT NOT NULL,
    content_outline TEXT NOT NULL,
    publish_schedule TEXT NOT NULL,
    confidence REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Title optimizations table
CREATE TABLE IF NOT EXISTS title_optimizations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    original_title TEXT NOT NULL,
    content_summary TEXT,
    optimized_titles TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Track diagnoses table
CREATE TABLE IF NOT EXISTS track_diagnoses (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    track_keyword TEXT NOT NULL,
    health_score REAL NOT NULL,
    competitiveness_score REAL NOT NULL,
    direction_advice TEXT NOT NULL,
    sub_tracks TEXT NOT NULL,
    confidence REAL NOT NULL,
    data_source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Feedback records table
CREATE TABLE IF NOT EXISTS feedback_records (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    feedback_type TEXT NOT NULL,
    feedback_value TEXT,
    reason TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Feedback analyses table
CREATE TABLE IF NOT EXISTS feedback_analyses (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    feedback_record_id TEXT NOT NULL,
    success_factors TEXT,
    failure_factors TEXT,
    weight_adjustments TEXT NOT NULL,
    excluded_patterns TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (feedback_record_id) REFERENCES feedback_records(id)
);

-- Effect reviews table
CREATE TABLE IF NOT EXISTS effect_reviews (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    topic_title TEXT NOT NULL,
    prediction TEXT NOT NULL,
    actual_result TEXT,
    attribution TEXT,
    learnings TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Content risks table
CREATE TABLE IF NOT EXISTS content_risks (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    content_text TEXT NOT NULL,
    content_text_expires_at TEXT,
    risks TEXT NOT NULL,
    overall_risk_score REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Publish suggestions table
CREATE TABLE IF NOT EXISTS publish_suggestions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    content_type TEXT NOT NULL,
    suggested_times TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- User events table (PostHog)
CREATE TABLE IF NOT EXISTS user_events (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- LLM call logs table (LangFuse)
CREATE TABLE IF NOT EXISTS llm_call_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    model_version TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    chain_name TEXT NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    latency_ms INTEGER,
    success INTEGER NOT NULL DEFAULT 1,
    error_message TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Upgrade signals table
CREATE TABLE IF NOT EXISTS upgrade_signals (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    feature_name TEXT NOT NULL,
    action TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""

# ==================== Database Manager ====================


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
        """Initialize the database engine and create all tables.

        Enables WAL mode for better concurrent read/write performance.
        Creates all 14 tables if they don't exist.
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

        # Enable WAL mode + create tables (MUST be in same connection for :memory:)
        async with self.engine.begin() as conn:
            # Configure SQLite pragmas
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA foreign_keys=ON"))
            await conn.execute(text("PRAGMA busy_timeout=5000"))

            # Create all 14 tables
            for block in SQL_SCHEMA.split(";"):
                block = block.strip()
                if not block:
                    continue
                # Strip comment lines (lines starting with --)
                clean_lines = [
                    line
                    for line in block.split("\n")
                    if not line.strip().startswith("--")
                ]
                clean_stmt = "\n".join(clean_lines).strip()
                if clean_stmt:
                    await conn.execute(text(clean_stmt + ";"))

        # Create session factory
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info("Database initialized (14 tables) with WAL mode")

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
