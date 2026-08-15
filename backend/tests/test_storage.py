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


@pytest.mark.asyncio
@pytest.mark.parametrize("token", ["", ".", "..", "a/b"])
async def test_purge_quarantine_rejects_unsafe_token(tmp_path: Path, token: str):
    """A token that escapes its own subtree must never reach ``rmtree``.

    ``.deleting/..`` resolves to the storage root itself, which still passes
    the containment check, so an unguarded purge would delete every owner's
    objects.
    """
    storage = LocalObjectStorage(tmp_path)
    kept = await storage.put("owner-1", "keep.txt", b"keep")

    with pytest.raises(ValueError, match="storage path"):
        await storage.purge_quarantine(token)

    # The unrelated owner's data must survive the rejected purge.
    assert await storage.get(kept) == b"keep"


@pytest.mark.asyncio
@pytest.mark.parametrize("owner_id,token", [("", "t"), ("..", "t"), ("o", ".."), ("a/b", "t")])
async def test_restore_owner_rejects_unsafe_segments(tmp_path: Path, owner_id: str, token: str):
    storage = LocalObjectStorage(tmp_path)

    with pytest.raises(ValueError, match="storage path"):
        await storage.restore_owner(owner_id, token)


@pytest.mark.asyncio
async def test_quarantine_restore_round_trip(tmp_path: Path):
    storage = LocalObjectStorage(tmp_path)
    path = await storage.put("owner-1", "note.txt", b"hello")

    assert await storage.quarantine_owner("owner-1", "tok") is True
    assert await storage.get(path) is None

    await storage.restore_owner("owner-1", "tok")
    assert await storage.get(path) == b"hello"


@pytest.mark.asyncio
async def test_purge_quarantine_removes_only_that_token(tmp_path: Path):
    storage = LocalObjectStorage(tmp_path)
    await storage.put("owner-1", "a.txt", b"a")
    kept = await storage.put("owner-2", "b.txt", b"b")
    await storage.quarantine_owner("owner-1", "tok")

    await storage.purge_quarantine("tok")

    assert await storage.get(kept) == b"b"


@pytest.mark.asyncio
@pytest.mark.parametrize("owner_id", [".deleting", ".hidden"])
async def test_put_rejects_reserved_dot_owner(tmp_path: Path, owner_id: str):
    """An owner id equal to a reserved quarantine segment would write
    straight into the quarantine tree, and ``quarantine_owner`` for such an
    id would relocate the entire quarantine namespace."""
    storage = LocalObjectStorage(tmp_path)

    with pytest.raises(ValueError, match="storage path"):
        await storage.put(owner_id, "note.txt", b"hello")


@pytest.mark.asyncio
async def test_quarantine_owner_rejects_reserved_dot_owner(tmp_path: Path):
    storage = LocalObjectStorage(tmp_path)
    kept = await storage.put("owner-1", "keep.txt", b"keep")
    await storage.quarantine_owner("owner-1", "tok")

    with pytest.raises(ValueError, match="storage path"):
        await storage.quarantine_owner(".deleting", "tok")

    # The quarantined owner's data must survive the rejected relocation.
    await storage.restore_owner("owner-1", "tok")
    assert await storage.get(kept) == b"keep"
