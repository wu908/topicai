"""Small local object store used by v2 materials and account deletion."""

from pathlib import Path


class LocalObjectStorage:
    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or Path(__file__).resolve().parents[2] / "data" / "objects").resolve()

    def _resolve(self, path: str) -> Path:
        candidate = (self.root / path).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("storage path must stay inside the configured root") from exc
        return candidate

    async def put(self, owner_id: str, filename: str, data: bytes) -> str:
        if any(value in {"", ".", ".."} or Path(value).name != value for value in (owner_id, filename)):
            raise ValueError("storage path must use a single owner and filename segment")
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
