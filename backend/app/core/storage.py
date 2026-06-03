"""ObjectStorage — simple local file storage abstraction.
Phase 6/7 implementation. S3/OSS/Minio can replace this module later
without changing any caller (same interface).
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Protocol

LOCAL_STORAGE_ROOT = os.path.join(os.path.dirname(__file__), "..", "data", "assets")


class ObjectStorage(Protocol):
    """Abstract storage interface."""

    async def put(self, owner_id: str, filename: str, data: bytes) -> str:
        ...

    async def get(self, path: str) -> bytes | None:
        ...

    async def delete(self, path: str) -> None:
        ...

    def sign_url(self, path: str, ttl_seconds: int = 300) -> str:
        ...


class LocalObjectStorage:
    """Local filesystem storage.

    Writes to LOCAL_STORAGE_ROOT / {owner_id} / {uuid}.{ext}.
    Signed URLs are stateless — a short-lived HMAC token is appended.
    """

    SIGNING_SECRET = os.environ.get("STORAGE_SIGNING_SECRET", "topicai-local-dev-key")

    async def put(self, owner_id: str, filename: str, data: bytes) -> str:
        rel = os.path.join(owner_id, filename)
        full = os.path.join(LOCAL_STORAGE_ROOT, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(data)
        return rel

    async def get(self, path: str) -> bytes | None:
        full = os.path.join(LOCAL_STORAGE_ROOT, path)
        if not os.path.isfile(full):
            return None
        with open(full, "rb") as f:
            return f.read()

    async def delete(self, path: str) -> None:
        full = os.path.join(LOCAL_STORAGE_ROOT, path)
        if os.path.isfile(full):
            os.remove(full)

    def sign_url(self, path: str, ttl_seconds: int = 300) -> str:
        expires = int(time.time()) + ttl_seconds
        token = hmac.new(
            self.SIGNING_SECRET.encode(),
            f"{path}:{expires}".encode(),
            hashlib.sha256,
        ).hexdigest()[:16]
        return f"/api/v1/assets/download/{path}?token={token}&expires={expires}"

    def verify(self, path: str, token: str, expires: int) -> bool:
        if int(time.time()) > expires:
            return False
        expected = hmac.new(
            self.SIGNING_SECRET.encode(),
            f"{path}:{expires}".encode(),
            hashlib.sha256,
        ).hexdigest()[:16]
        return hmac.compare_digest(expected, token)
