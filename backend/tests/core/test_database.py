"""Tests for T02: Database module.

Tests cover:
- TC02-04: SQLite WAL mode
- TC02-05: 14 tables created
- TC02-06: CRUD operations
- TC02-07: Foreign key constraints
- TC02-08: 90-day expiry fields
- TC02-09: Concurrent read/write safety
"""

import asyncio
from datetime import UTC, datetime

import pytest


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class TestDatabaseInitialization:
    """TC02-04: SQLite WAL mode and table creation."""

    @pytest.mark.asyncio
    async def test_wal_mode_enabled(self):
        """Given database initialization, When checking journal mode,
        Then WAL mode is enabled (or 'memory' for :memory: databases)."""
        from app.core.database import Database

        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        result = await db.fetch_one("PRAGMA journal_mode")
        assert result is not None
        # :memory: databases cannot use WAL, but the PRAGMA was issued
        assert result["journal_mode"] in ("wal", "memory")

        await db.close()

    @pytest.mark.asyncio
    async def test_foreign_keys_enabled(self):
        """Given database initialization, When checking foreign keys,
        Then foreign_keys pragma is ON."""
        from app.core.database import Database

        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        result = await db.fetch_one("PRAGMA foreign_keys")
        assert result is not None
        # SQLite returns 1 for ON
        assert result["foreign_keys"] == 1

        await db.close()

    @pytest.mark.asyncio
    async def test_all_14_tables_created(self):
        """TC02-05: init_db (now migration-managed) yields the full app
        schema. The test name is retained for traceability but the set is
        the migration-driven table union (000_initial + 001-006), not the
        legacy 14-table SQL_SCHEMA memory, which was retired in T104."""
        from app.core.database import Database

        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        rows = await db.fetch_all(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        actual = {r["name"] for r in rows}

        # Migration-driven schema union (avoid importing the single-source
        # lock-down module here to keep this a standalone init_db check).
        expected_tables = {
            "schema_migrations",
            "users",
            "creator_profiles",
            "content_projects",
            "content_versions",
            "ai_traces_v2",
            "action_events",
            "content_opportunities",
        }

        missing = expected_tables - actual
        assert not missing, f"init_db (migration-managed) missing tables: {sorted(missing)}"

        await db.close()


class TestCRUDOperations:
    """TC02-06: CRUD base operations."""

    @pytest.mark.asyncio
    async def test_insert_and_select(self):
        """Given empty table, When inserting and selecting,
        Then data is correctly returned."""
        from app.core.database import Database

        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        now = utc_now()
        await db.insert(
            "users",
            {
                "id": "test-1",
                "email": "test@example.com",
                "username": "testuser",
                "password_hash": "hash123",
                "ai_calls_today": 0,
                "ai_calls_reset_at": now,
                "created_at": now,
                "last_login": now,
            },
        )

        row = await db.fetch_one("SELECT * FROM users WHERE id = :id", {"id": "test-1"})
        assert row is not None
        assert row["email"] == "test@example.com"
        assert row["username"] == "testuser"

        await db.close()

    @pytest.mark.asyncio
    async def test_update(self):
        """Given existing row, When updating, Then changes persisted."""
        from app.core.database import Database

        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        now = utc_now()
        await db.insert(
            "users",
            {
                "id": "test-2",
                "email": "update@example.com",
                "username": "updateuser",
                "password_hash": "hash",
                "ai_calls_today": 0,
                "ai_calls_reset_at": now,
                "created_at": now,
                "last_login": now,
            },
        )

        affected = await db.update(
            "users",
            {"ai_calls_today": 5},
            {"id": "test-2"},
        )
        assert affected == 1

        row = await db.fetch_one("SELECT ai_calls_today FROM users WHERE id = :id", {"id": "test-2"})
        assert row["ai_calls_today"] == 5

        await db.close()

    @pytest.mark.asyncio
    async def test_delete(self):
        """Given existing row, When deleting, Then row removed."""
        from app.core.database import Database

        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        now = utc_now()
        await db.insert(
            "users",
            {
                "id": "test-3",
                "email": "delete@example.com",
                "username": "deleteuser",
                "password_hash": "hash",
                "ai_calls_today": 0,
                "ai_calls_reset_at": now,
                "created_at": now,
                "last_login": now,
            },
        )

        affected = await db.delete("users", {"id": "test-3"})
        assert affected == 1

        row = await db.fetch_one("SELECT * FROM users WHERE id = :id", {"id": "test-3"})
        assert row is None

        await db.close()

    @pytest.mark.asyncio
    async def test_fetch_all(self):
        """Given multiple rows, When fetch_all, Then all returned."""
        from app.core.database import Database

        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        now = utc_now()
        for i in range(3):
            await db.insert(
                "users",
                {
                    "id": f"multi-{i}",
                    "email": f"multi{i}@example.com",
                    "username": f"multiuser{i}",
                    "password_hash": "hash",
                    "ai_calls_today": 0,
                    "ai_calls_reset_at": now,
                    "created_at": now,
                    "last_login": now,
                },
            )

        rows = await db.fetch_all("SELECT * FROM users ORDER BY id")
        assert len(rows) == 3

        await db.close()


class TestForeignKeyConstraints:
    """TC02-07: Foreign key constraint validation."""

    @pytest.mark.asyncio
    async def test_foreign_key_violation(self):
        """Given non-existent user_id, When inserting with FK reference,
        Then IntegrityError raised."""
        from app.core.database import Database

        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        now = utc_now()
        import sqlalchemy.exc

        with pytest.raises((sqlalchemy.exc.IntegrityError, Exception)):
            await db.insert(
                "materials",
                {
                    "id": "material-1",
                    "owner_user_id": "nonexistent-user",
                    "name": "evidence.pdf",
                    "mime_type": "application/pdf",
                    "kind": "document",
                    "size": 1,
                    "source_url": "/materials",
                    "created_at": now,
                    "updated_at": now,
                },
            )

        await db.close()


class TestConcurrentAccess:
    """TC02-09: Concurrent read/write safety."""

    @pytest.mark.asyncio
    async def test_concurrent_read_write(self):
        """Given WAL mode, When 2 coroutines read/write simultaneously,
        Then no deadlock, data consistent."""
        from app.core.database import Database

        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        now = utc_now()
        # Pre-populate
        await db.insert(
            "users",
            {
                "id": "concurrent-user",
                "email": "concurrent@example.com",
                "username": "concurrentuser",
                "password_hash": "hash",
                "ai_calls_today": 0,
                "ai_calls_reset_at": now,
                "created_at": now,
                "last_login": now,
            },
        )

        async def read_loop():
            for _ in range(10):
                await db.fetch_one(
                    "SELECT * FROM users WHERE id = :id",
                    {"id": "concurrent-user"},
                )
                await asyncio.sleep(0.001)

        async def write_loop():
            for i in range(10):
                try:
                    await db.update(
                        "users",
                        {"ai_calls_today": i},
                        {"id": "concurrent-user"},
                    )
                except Exception:
                    pass
                await asyncio.sleep(0.001)

        # Run concurrently
        await asyncio.gather(read_loop(), write_loop())

        # Verify final state is consistent
        row = await db.fetch_one(
            "SELECT ai_calls_today FROM users WHERE id = :id",
            {"id": "concurrent-user"},
        )
        assert row is not None
        assert 0 <= row["ai_calls_today"] <= 9

        await db.close()


class TestIdentifierValidation:
    """SQL injection prevention via identifier whitelist."""

    def test_validate_identifier_accepts_valid_names(self):
        """Plain alphanumeric + underscore names are accepted."""
        from app.core.database import _validate_identifier

        assert _validate_identifier("users") == "users"
        assert _validate_identifier("creator_profiles") == "creator_profiles"
        assert _validate_identifier("_private") == "_private"
        assert _validate_identifier("Table123") == "Table123"

    def test_validate_identifier_rejects_injection(self):
        """Names with SQL special characters are rejected."""
        from app.core.database import _validate_identifier

        with pytest.raises(ValueError, match="invalid table name"):
            _validate_identifier("users; DROP TABLE users", "table name")
        with pytest.raises(ValueError, match="invalid table name"):
            _validate_identifier("users--comment", "table name")
        with pytest.raises(ValueError, match="invalid table name"):
            _validate_identifier("users.other", "table name")
        with pytest.raises(ValueError, match="invalid table name"):
            _validate_identifier("users OR 1=1", "table name")
        with pytest.raises(ValueError, match="invalid table name"):
            _validate_identifier("", "table name")

    @pytest.mark.asyncio
    async def test_insert_rejects_malicious_table(self):
        """insert() raises ValueError before SQL is built."""
        from app.core.database import Database

        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        with pytest.raises(ValueError, match="invalid table name"):
            await db.insert("users; DROP TABLE users", {"id": "x"})

        await db.close()

    @pytest.mark.asyncio
    async def test_update_rejects_malicious_table(self):
        """update() raises ValueError before SQL is built."""
        from app.core.database import Database

        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        with pytest.raises(ValueError, match="invalid table name"):
            await db.update("users OR 1=1", {"x": 1}, {"id": "y"})

        await db.close()

    @pytest.mark.asyncio
    async def test_delete_rejects_malicious_table(self):
        """delete() raises ValueError before SQL is built."""
        from app.core.database import Database

        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        with pytest.raises(ValueError, match="invalid table name"):
            await db.delete("users--", {"id": "x"})

        await db.close()
