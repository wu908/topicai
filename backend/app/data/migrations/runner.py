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
"""

from __future__ import annotations

import hashlib
import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_MIGRATIONS_DIR = Path(__file__).resolve().parent


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


__all__ = ["AppliedMigration", "apply", "status"]
