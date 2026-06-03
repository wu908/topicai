"""Backup service for TopicAI v4.0.

Daily SQLite and ChromaDB backup with 30-day retention.
"""

import logging
import shutil
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class BackupService:
    """Manages daily database backups with retention policy."""

    def __init__(self, db_path: str = "data/topicai.db", chroma_path: str = "data/chroma"):
        self.db_path = Path(db_path)
        self.chroma_path = Path(chroma_path)
        self.backup_root = Path("backups")
        self.retention_days: int = 30

    def _backup_filename(self, suffix: str = ".db.bak") -> str:
        return f"{date.today().isoformat()}{suffix}"

    async def backup_sqlite(self) -> str:
        """Backup SQLite database.

        Returns:
            Path to backup file.
        """
        self.backup_root.mkdir(parents=True, exist_ok=True)
        today_dir = self.backup_root / date.today().isoformat()
        today_dir.mkdir(parents=True, exist_ok=True)

        dest = today_dir / f"topicai{self._backup_filename('.db.bak')}"
        if self.db_path.exists():
            shutil.copy2(self.db_path, dest)
            logger.info(f"SQLite backup created: {dest}")
        return str(dest)

    async def backup_chromadb(self) -> str:
        """Backup ChromaDB data.

        Returns:
            Path to backup directory.
        """
        if not self.chroma_path.exists():
            return ""

        today_dir = self.backup_root / date.today().isoformat()
        today_dir.mkdir(parents=True, exist_ok=True)

        dest = today_dir / "chroma"
        shutil.copytree(self.chroma_path, dest, dirs_exist_ok=True)
        logger.info(f"ChromaDB backup created: {dest}")
        return str(dest)

    async def cleanup_old_backups(self) -> int:
        """Remove backups older than retention_days.

        Returns:
            Number of removed backup directories.
        """
        cutoff = datetime.now(UTC) - timedelta(days=self.retention_days)
        removed = 0

        if not self.backup_root.exists():
            return 0

        for item in self.backup_root.iterdir():
            if item.is_dir():
                try:
                    dir_date = datetime.strptime(item.name, "%Y-%m-%d").replace(tzinfo=UTC)
                    if dir_date < cutoff:
                        shutil.rmtree(item)
                        removed += 1
                        logger.info(f"Old backup removed: {item}")
                except (ValueError, OSError):
                    pass

        return removed

    async def run_full_backup(self) -> dict:
        """Run complete backup of all databases.

        Returns:
            Dict with backup results.
        """
        sqlite_path = await self.backup_sqlite()
        chroma_path = await self.backup_chromadb()
        removed = await self.cleanup_old_backups()

        return {
            "sqlite_backup": sqlite_path,
            "chroma_backup": chroma_path,
            "old_backups_removed": removed,
        }
