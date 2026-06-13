"""Unit tests for BackupService."""

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from app.tasks.backup import BackupService


@pytest.mark.asyncio
async def test_backup_sqlite_copies_existing_db(tmp_path: Path) -> None:
    """backup_sqlite copies the db file into a dated backup folder."""
    db = tmp_path / "src.db"
    db.write_text("payload")
    svc = BackupService(db_path=str(db), chroma_path=str(tmp_path / "chroma"))
    svc.backup_root = tmp_path / "backups"

    path = await svc.backup_sqlite()
    assert Path(path).exists()
    assert Path(path).read_text() == "payload"


@pytest.mark.asyncio
async def test_backup_sqlite_missing_db_returns_path_without_raising(tmp_path: Path) -> None:
    """Missing source db returns the would-be path; no exception."""
    svc = BackupService(db_path=str(tmp_path / "absent.db"))
    svc.backup_root = tmp_path / "backups"
    path = await svc.backup_sqlite()
    assert path  # returns string, but no file copy made


@pytest.mark.asyncio
async def test_backup_chromadb_skips_when_missing(tmp_path: Path) -> None:
    """backup_chromadb returns '' when chroma path does not exist."""
    svc = BackupService(chroma_path=str(tmp_path / "no-such-chroma"))
    svc.backup_root = tmp_path / "backups"
    assert await svc.backup_chromadb() == ""


@pytest.mark.asyncio
async def test_backup_chromadb_copies_tree(tmp_path: Path) -> None:
    """backup_chromadb copies the chroma tree into a dated folder."""
    chroma = tmp_path / "chroma"
    chroma.mkdir()
    (chroma / "index.bin").write_text("x")
    svc = BackupService(chroma_path=str(chroma))
    svc.backup_root = tmp_path / "backups"
    out = await svc.backup_chromadb()
    assert Path(out).exists()
    assert (Path(out) / "index.bin").read_text() == "x"


@pytest.mark.asyncio
async def test_cleanup_old_backups_removes_old_dirs(tmp_path: Path) -> None:
    """cleanup_old_backups removes dated dirs older than retention_days."""
    svc = BackupService()
    svc.backup_root = tmp_path / "backups"
    svc.backup_root.mkdir()
    svc.retention_days = 30

    old_dir = svc.backup_root / (date.today() - timedelta(days=60)).isoformat()
    old_dir.mkdir()
    new_dir = svc.backup_root / date.today().isoformat()
    new_dir.mkdir()

    removed = await svc.cleanup_old_backups()
    assert removed == 1
    assert not old_dir.exists()
    assert new_dir.exists()


@pytest.mark.asyncio
async def test_cleanup_old_backups_handles_missing_root(tmp_path: Path) -> None:
    """cleanup_old_backups returns 0 when backup root does not exist."""
    svc = BackupService()
    svc.backup_root = tmp_path / "no-backups"
    assert await svc.cleanup_old_backups() == 0


@pytest.mark.asyncio
async def test_run_full_backup_returns_summary(tmp_path: Path) -> None:
    """run_full_backup aggregates the three steps into a single dict."""
    db = tmp_path / "x.db"
    db.write_text("z")
    chroma = tmp_path / "chroma"
    chroma.mkdir()
    (chroma / "f").write_text("y")
    svc = BackupService(db_path=str(db), chroma_path=str(chroma))
    svc.backup_root = tmp_path / "backups"
    summary = await svc.run_full_backup()
    assert "sqlite_backup" in summary
    assert "chroma_backup" in summary
    assert "old_backups_removed" in summary
    assert isinstance(summary["old_backups_removed"], int)


def test_backup_filename_uses_today() -> None:
    """_backup_filename uses today's ISO date."""
    svc = BackupService()
    name = svc._backup_filename(".db.bak")  # noqa: SLF001 - intentional
    assert name == f"{date.today().isoformat()}.db.bak"
    assert (datetime.now(UTC) - datetime.fromisoformat(name.split('.')[0]).replace(tzinfo=UTC)).days == 0
