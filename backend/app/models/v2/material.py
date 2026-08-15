"""Typed contracts for lightweight personal materials."""

import re
from typing import Literal

from pydantic import Field, field_validator, model_validator

from app.models.v2.intent_actions import StrictModel

MaterialKind = Literal["text", "link", "image", "document"]
MaterialPrivacy = Literal["public", "private", "sensitive"]

# Strict ``type/subtype`` token form. The stored value is later echoed as
# the response ``Content-Type`` at download time, so anything beyond simple
# tokens (CR/LF, parameters, spaces) is rejected outright.
_MIME_TOKEN = r"[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]*"
_MIME_TYPE_PATTERN = re.compile(rf"^{_MIME_TOKEN}/{_MIME_TOKEN}$")


class MaterialCreate(StrictModel):
    kind: MaterialKind
    title: str = Field(min_length=1, max_length=200)
    content: str | None = Field(default=None, max_length=100_000)
    content_base64: str | None = None
    mime_type: str | None = Field(default=None, max_length=200)
    privacy_level: MaterialPrivacy = "private"
    project_id: str | None = Field(default=None, max_length=100)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @field_validator("mime_type")
    @classmethod
    def _validate_mime_type(cls, value: str | None) -> str | None:
        if value is not None and not _MIME_TYPE_PATTERN.match(value):
            raise ValueError("mime_type must be a valid type/subtype token")
        return value

    @model_validator(mode="after")
    def validate_content(self):
        if self.kind in {"text", "link"} and not (self.content or "").strip():
            raise ValueError("text and link materials require content")
        if self.kind in {"image", "document"} and not self.content_base64:
            raise ValueError("image and document materials require base64 content")
        return self


class MaterialUpdate(StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    privacy_level: MaterialPrivacy | None = None
    expected_version: int = Field(ge=1)


class MaterialUsageCreate(StrictModel):
    project_id: str = Field(min_length=1, max_length=100)
    idempotency_key: str = Field(min_length=1, max_length=200)


class MaterialUsageView(StrictModel):
    id: str
    project_id: str
    project_title: str
    used_at: str


class MaterialView(StrictModel):
    id: str
    title: str
    kind: MaterialKind
    mime_type: str
    size: int = Field(ge=0)
    content: str | None = None
    privacy_level: MaterialPrivacy
    version: int = Field(ge=1)
    usages: list[MaterialUsageView]
    created_at: str
    updated_at: str


class MaterialListResult(StrictModel):
    items: list[MaterialView]
    total: int = Field(ge=0)
