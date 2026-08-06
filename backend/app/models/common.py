"""Shared API envelope for v2 endpoints."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    data: T | Any | None = None
    message: str = "success"
    meta: dict = Field(default_factory=dict)
