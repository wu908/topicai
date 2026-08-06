"""Local object storage lifecycle and path-boundary checks."""

from pathlib import Path

import pytest

from app.core.storage import LocalObjectStorage


@pytest.mark.asyncio
async def test_put_get_delete_round_trip(tmp_path: Path):
    storage = LocalObjectStorage(tmp_path)

    path = await storage.put("owner-1", "note.txt", b"hello")

    assert path == "owner-1/note.txt"
    assert await storage.get(path) == b"hello"
    await storage.delete(path)
    assert await storage.get(path) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["../outside.txt", "/absolute.txt", "owner/../../outside.txt"])
async def test_storage_rejects_paths_outside_root(tmp_path: Path, path: str):
    storage = LocalObjectStorage(tmp_path)

    with pytest.raises(ValueError, match="storage path"):
        await storage.get(path)
