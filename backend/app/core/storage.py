"""Small local object store used by v2 materials and account deletion."""

import os
import shutil
from pathlib import Path


class LocalObjectStorage:
    def __init__(self, root: str | Path | None = None):
        configured = root or os.getenv("OBJECT_STORAGE_ROOT")
        self.root = Path(
            configured or Path(__file__).resolve().parents[2] / "data" / "objects"
        ).resolve()

    @staticmethod
    def _require_safe_segments(*values: str) -> None:
        """Reject anything that is not a single, literal path segment.

        Empty strings, ``.``/``..``, dot-prefixed names and any value
        containing a separator are refused. Without this guard a
        caller-supplied ``token``/``owner_id`` can collapse a derived path
        back onto an ancestor directory (e.g. ``.deleting/..`` resolves to
        the storage root itself, which still passes the containment check
        in :meth:`_resolve`), or collide with the reserved quarantine
        namespace: an owner id of ``.deleting`` would write into the
        quarantine tree and ``quarantine_owner`` would relocate the whole
        namespace, including other owners' pending-deletion data.
        """
        for value in values:
            if not value or value.startswith(".") or Path(value).name != value:
                raise ValueError("storage path must use single, literal path segments")

    def _resolve(self, path: str) -> Path:
        candidate = (self.root / path).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("storage path must stay inside the configured root") from exc
        return candidate

    async def put(self, owner_id: str, filename: str, data: bytes) -> str:
        self._require_safe_segments(owner_id, filename)
        relative = Path(owner_id) / filename
        target = self._resolve(str(relative))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return relative.as_posix()

    async def get(self, path: str) -> bytes | None:
        target = self._resolve(path)
        return target.read_bytes() if target.is_file() else None

    async def delete(self, path: str) -> None:
        target = self._resolve(path)
        if target.is_file():
            target.unlink()

    async def quarantine_owner(self, owner_id: str, token: str) -> bool:
        self._require_safe_segments(owner_id, token)
        source = self._resolve(owner_id)
        if not source.is_dir():
            return False
        target = self._resolve(str(Path(".deleting") / token / owner_id))
        target.parent.mkdir(parents=True, exist_ok=True)
        source.replace(target)
        return True

    async def restore_owner(self, owner_id: str, token: str) -> None:
        self._require_safe_segments(owner_id, token)
        source = self._resolve(str(Path(".deleting") / token / owner_id))
        if not source.exists():
            return
        target = self._resolve(owner_id)
        if target.exists():
            raise FileExistsError(f"cannot restore storage for owner {owner_id}")
        source.replace(target)

    async def purge_quarantine(self, token: str) -> None:
        self._require_safe_segments(token)
        target = self._resolve(str(Path(".deleting") / token))
        if target.exists():
            shutil.rmtree(target)
