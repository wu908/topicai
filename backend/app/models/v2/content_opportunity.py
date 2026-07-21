"""Contracts for explainable opportunities that require explicit acceptance."""

from typing import Literal

from pydantic import Field, model_validator

from app.models.v2.intent_actions import StrictModel


class OpportunityDraft(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    audience_change: str = Field(min_length=1, max_length=1000)
    rationale: str = Field(min_length=1, max_length=4000)
    material_requirements: list[str] = Field(min_length=1, max_length=20)
    unknown_refs: list[str] = Field(default_factory=list, max_length=20)
    limitations: list[str] = Field(default_factory=list, max_length=20)


class SeriesExtensionCreate(StrictModel):
    expected_series_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class OpportunityDecision(StrictModel):
    decision: Literal["accept", "reject"]
    confirmed_title: str | None = Field(default=None, max_length=200)
    confirmed_audience_change: str | None = Field(default=None, max_length=1000)
    confirmed_material_requirements: list[str] | None = Field(default=None, max_length=20)
    reason: str | None = Field(default=None, max_length=2000)
    expected_opportunity_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def validate_confirmed_values(self):
        for value in (self.confirmed_title, self.confirmed_audience_change):
            if value is not None and not value.strip():
                raise ValueError("confirmed opportunity values cannot be blank")
        if self.confirmed_material_requirements is not None and not all(
            item.strip() for item in self.confirmed_material_requirements
        ):
            raise ValueError("confirmed material requirements cannot contain blanks")
        return self
