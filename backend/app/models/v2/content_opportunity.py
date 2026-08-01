"""Contracts for explainable opportunities that require explicit acceptance."""

from typing import Annotated, Literal

from pydantic import (
    AnyHttpUrl,
    AwareDatetime,
    Field,
    StringConstraints,
    model_validator,
)

from app.models.v2.intent_actions import StrictModel

NonBlankText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class OpportunityDraft(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    audience_change: str = Field(min_length=1, max_length=1000)
    rationale: str = Field(min_length=1, max_length=4000)
    material_requirements: list[str] = Field(min_length=1, max_length=20)
    unknown_refs: list[str] = Field(default_factory=list, max_length=20)
    limitations: list[str] = Field(default_factory=list, max_length=20)


class SeriesExtensionDraft(OpportunityDraft):
    """A series extension proposal that must also propose intent and format.

    Spec-011: a Creator Series no longer carries a single authoritative
    intent/format, so the next project's intent cannot be inherited. The AI
    proposes both; the user confirms or overrides them when accepting.
    """

    content_intent: Literal["solve", "share", "record"]
    content_format: Literal["graphic_note", "vlog_plan"]


class SeriesExtensionCreate(StrictModel):
    expected_series_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)


class OpportunityGenerateRequest(StrictModel):
    desired_count: int = Field(default=6, ge=1, le=10)


class OpportunityDimensions(StrictModel):
    audience_fit: Literal["strong", "medium", "weak", "unknown"]
    creator_fit: Literal["strong", "medium", "weak", "unknown"]
    material_readiness: Literal["ready", "partial", "missing"]
    growth_role: Literal["discovery", "trust", "series", "retention", "experiment"]
    series_potential: Literal["high", "medium", "low", "unknown"]
    timeliness: Literal["evergreen", "current", "expiring", "expired", "unknown"]
    similarity_risk: Literal["high", "medium", "low", "unknown"]
    safety_risk: Literal["high", "medium", "low", "unknown"]


class VerifySourceAction(StrictModel):
    action_type: Literal["verify_source"]
    reason: str
    accepted_inputs: list[
        Literal["original_url", "published_at", "authoritative_source", "timeliness"]
    ]
    fallback: Literal["manual_verification"]


class SourceExpiredAction(StrictModel):
    action_type: Literal["source_expired"]
    reason: str
    fallback: Literal["reverify_source"]


OpportunityRequiredAction = Annotated[
    VerifySourceAction | SourceExpiredAction,
    Field(discriminator="action_type"),
]


class SourceReference(StrictModel):
    ref_type: Literal[
        "imported_note",
        "material",
        "validated_insight",
        "creator_profile",
        "creator_series",
        "user_keyword",
        "user_url",
        "official_inspiration",
    ]
    entity_id: str | None
    url: str | None
    publisher: str | None
    published_at: str | None
    collected_at: str | None
    title: str | None
    excerpt: str | None
    verification_state: Literal["verified", "pending", "insufficient"]
    rights_note: str | None


class OpportunityProjectView(StrictModel):
    id: str
    title: str
    status: Literal[
        "inbox",
        "preparing",
        "creating",
        "ready_to_publish",
        "published",
        "awaiting_review",
        "settled",
    ]
    primary_goal: Literal["stable_publish", "follower_growth", "experiment"]
    target_audience: str
    content_intent: Literal["solve", "share", "record"] | None
    content_format: Literal["graphic_note", "vlog_plan"]
    intent_status: Literal[
        "candidate",
        "working_confirmed",
        "locked",
        "legacy_unclassified",
        "retrospective",
    ]
    audience_change: str | None
    material_requirements: list[str]
    opportunity_id: str | None
    version: int = Field(ge=1)
    updated_at: str


class ContentOpportunityView(StrictModel):
    id: str
    opportunity_type: Literal[
        "series_extension",
        "user_source",
        "history_derivative",
        "user_question",
        "material_derivative",
        "insight_derivative",
        "evergreen",
    ]
    source_trigger: Literal[
        "system", "user_keyword", "user_url", "official_inspiration"
    ]
    source_ref: str
    source_excerpt: str | None = None
    source_url: str | None = None
    source_published_at: str | None = None
    source_authority: str | None = None
    source_refs: list[SourceReference]
    verification_status: Literal["verified", "pending_verification", "insufficient"]
    expires_at: str | None = None
    content_intent: Literal["solve", "share", "record"]
    content_format: Literal["graphic_note", "vlog_plan"]
    proposed_title: str
    proposed_audience_change: str
    proposed_rationale: str
    proposed_material_requirements: list[str]
    confirmed_title: str | None = None
    confirmed_audience_change: str | None = None
    confirmed_material_requirements: list[str]
    evidence_refs: list[str]
    unknown_refs: list[str]
    dimensions: OpportunityDimensions | None = None
    status: Literal["proposed", "saved", "accepted", "rejected"]
    proposal_source: Literal["ai", "deterministic_fallback"]
    ai_trace_id: str
    created_project_id: str | None = None
    limitations: list[str]
    version: int = Field(ge=1)
    created_at: str
    updated_at: str
    decided_at: str | None = None
    required_action: OpportunityRequiredAction | None = None
    project: OpportunityProjectView | None = None


class OpportunityListResult(StrictModel):
    items: list[ContentOpportunityView]


class UserSourceOpportunityCreate(StrictModel):
    trigger: Literal["user_keyword", "user_url", "official_inspiration"]
    pasted_text: str = Field(min_length=1, max_length=10000)
    original_url: AnyHttpUrl | None = Field(default=None, max_length=2000)
    published_at: AwareDatetime | None = None
    authoritative_source: NonBlankText | None = Field(default=None, max_length=500)
    expires_at: AwareDatetime | None = None
    content_intent: Literal["solve", "share", "record"] = "share"
    idempotency_key: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def validate_trigger_metadata(self):
        if self.trigger == "user_url" and self.original_url is None:
            raise ValueError("user_url intake requires original_url")
        if self.trigger == "official_inspiration" and self.authoritative_source is None:
            raise ValueError("official_inspiration intake requires authoritative_source")
        return self


class OpportunitySourceVerification(StrictModel):
    verification_status: Literal["verified", "insufficient"]
    original_url: AnyHttpUrl | None = Field(default=None, max_length=2000)
    published_at: AwareDatetime | None = None
    authoritative_source: NonBlankText | None = Field(default=None, max_length=500)
    timeliness: Literal["current", "expiring", "expired"] | None = None
    reason: str | None = Field(default=None, max_length=2000)
    confirmed_by_user: Literal[True]
    expected_opportunity_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def validate_verification(self):
        if self.verification_status == "verified" and not all(
            (
                self.original_url,
                self.published_at,
                self.authoritative_source,
                self.timeliness,
            )
        ):
            raise ValueError("verified sources require complete source metadata")
        if self.verification_status == "insufficient" and not (
            self.reason and self.reason.strip()
        ):
            raise ValueError("insufficient sources require a reason")
        return self


class OpportunityDecision(StrictModel):
    decision: Literal["accept", "save", "reject"]
    confirmed_title: str | None = Field(default=None, max_length=200)
    confirmed_audience_change: str | None = Field(default=None, max_length=1000)
    confirmed_material_requirements: list[str] | None = Field(default=None, max_length=20)
    # Spec-011: series_extension opportunities carry a proposed intent/format
    # from the AI draft; the user may override either at accept time.
    confirmed_content_intent: Literal["solve", "share", "record"] | None = None
    confirmed_content_format: Literal["graphic_note", "vlog_plan"] | None = None
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
        if self.confirmed_content_intent is not None and self.decision != "accept":
            raise ValueError("confirmed_content_intent is only valid on accept")
        if self.confirmed_content_format is not None and self.decision != "accept":
            raise ValueError("confirmed_content_format is only valid on accept")
        return self
