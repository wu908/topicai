"""Contracts for owner-controlled export and account deletion."""

from typing import Any

from app.models.v2.intent_actions import StrictModel


class OwnerDataExport(StrictModel):
    generated_at: str
    owner: dict[str, Any]
    entities: dict[str, list[dict[str, Any]]]
    content_genomes: list[dict[str, Any]]
