"""Contracts for owner-controlled export and account deletion."""

from typing import Any, Literal

from app.models.v2.intent_actions import StrictModel


class AccountDataJob(StrictModel):
    id: str
    operation: Literal["data_export", "account_deletion"]
    status: Literal["running", "completed", "failed"]
    created_at: str
    completed_at: str | None


class StoredFileExport(StrictModel):
    material_id: str
    title: str
    mime_type: str
    size: int
    status: Literal["exported", "missing"]
    content_base64: str | None


class OwnerDataExport(StrictModel):
    job: AccountDataJob
    generated_at: str
    owner: dict[str, Any]
    entities: dict[str, list[dict[str, Any]]]
    content_genomes: list[dict[str, Any]]
    stored_files: list[StoredFileExport]
