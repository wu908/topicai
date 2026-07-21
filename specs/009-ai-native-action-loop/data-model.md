# Data Model: TopicAI AI-native Action Loop

**Feature**: `009-ai-native-action-loop`  
**Status**: Logical model, not a database migration

## Entities

### CreatorState

One current versioned snapshot of the creator context used for action selection.

| Field | Type | Required | Source | Editable |
| --- | --- | --- | --- | --- |
| `id` | string | yes | system | no |
| `user_id` | string | yes | auth | no |
| `version` | integer | yes | system | no |
| `goal_refs` | list[string] | yes | user | partly |
| `capacity` | object | yes | user + inference | yes |
| `active_project_refs` | list[string] | yes | ContentProject | no |
| `blocker_refs` | list[string] | yes | system/AI proposal | reviewable |
| `recent_action_refs` | list[string] | yes | action events | no |
| `confirmed_insight_refs` | list[string] | yes | LearnedInsight | no |
| `uncertainty` | object | yes | AITrace | no |
| `created_at` / `updated_at` | timestamp | yes | system | no |

### ContentGenome

Long-term graph of creator promise, experiences, viewpoints, audience questions, series, voice patterns and outcomes.

Nodes and edges must retain source references, confirmation state, privacy, validity and deletion effects. A vector index may be an optimization, never the source of truth.

### Evidence

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `id` | string | yes | immutable identifier |
| `owner_id` | string | yes | owner scoped |
| `type` | enum | yes | `user_fact`, `external_fact`, `ai_inference`, `validated_insight` |
| `content_ref` | string | yes | pointer to encrypted/user content, not analytics payload |
| `source_ref` | object | conditional | URL, material, interview, snapshot or insight |
| `confirmed` | boolean | yes | only user can promote factual reuse |
| `privacy_level` | enum | yes | public, account_private, sensitive |
| `validity` | enum | yes | valid, pending, revoked, deleted |
| `created_at` / `updated_at` | timestamp | yes | system |

`ai_inference` cannot automatically become `user_fact` or `validated_insight`.

### CreatorViewpoint

A creator viewpoint is an AI-proposed, user-confirmed statement derived only from Evidence currently allowed by the project's ContentGenome.

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `id` / `owner_id` / `project_id` | string | yes | immutable and owner scoped |
| `content_intent` | enum | yes | `solve`, `share`, or `record` |
| `proposed_statement` / `proposed_rationale` | string | yes | AI candidate or conservative fallback |
| `confirmed_statement` | string | conditional | required only after user confirmation; may contain user edits |
| `source_evidence_ids` | list[string] | yes | every source must be confirmed and allowed in the project Genome |
| `source_content_version_id` | string | no | when present, must be the current project version |
| `privacy_level` | enum | yes | inherits the most restrictive source boundary |
| `status` | enum | yes | `proposed`, `confirmed`, `rejected`, `revoked` |
| `proposal_source` | enum | yes | `ai` or `deterministic_fallback` |
| `ai_trace_id` | string | yes | structured proposal provenance |
| `version` | integer | yes | optimistic concurrency |

Proposal, confirmation, rejection and revocation append immutable events. A proposed or rejected viewpoint never enters CreatorState or future action context. Confirmation revalidates every source to close the race between candidate creation and user decision.

### CreatorSeries

A creator series is a user-confirmed relationship among two or more published ContentProjects. It records a shared reader promise and a possible continuation direction without changing the source projects.

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `id` / `owner_id` | string | yes | immutable and owner scoped |
| `content_intent` / `content_format` | enum | yes | all source projects must share both values |
| `proposed_name` / `proposed_promise` | string | yes | AI candidate or conservative fallback |
| `proposed_rationale` / `proposed_continuation_prompt` | string | yes | explains the relationship and one possible next direction |
| `confirmed_name` / `confirmed_promise` | string | conditional | user-confirmed or user-edited values |
| `confirmed_continuation_prompt` | string | conditional | required after confirmation |
| `source_project_ids` | list[string] | yes | 2-20 published, non-archived projects with confirmed intent |
| `status` | enum | yes | `proposed`, `confirmed`, `rejected`, `revoked` |
| `proposal_source` | enum | yes | `ai` or `deterministic_fallback` |
| `ai_trace_id` / `version` | string/integer | yes | provenance and optimistic concurrency |

Titles alone are not sufficient evidence of a series. AI proposals must also use the projects' confirmed intent and intended audience change. The deterministic fallback preserves only the selected project relationship and does not infer a shared theme.

### NextBestAction

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `id` | string | yes | immutable |
| `user_id` | string | yes | owner scoped |
| `target_type` / `target_id` | enum/string | yes | project, opportunity, evidence, review or state |
| `action_type` | enum | yes | policy-registered action |
| `status` | enum | yes | proposed, accepted, executing, completed, rejected, expired, failed, cancelled |
| `reason` | string | yes | explain current priority |
| `evidence_refs` | list[string] | yes | may be empty only for a state observation |
| `state_before` / `expected_state_after` | enum/object | yes | optimistic concurrency |
| `user_gate_id` | string | conditional | required for L3 actions |
| `fallback` | object | yes | manual continuation |
| `idempotency_key` | string | yes | duplicate protection |
| `ai_trace_id` | string | conditional | required for AI-generated action |
| `expires_at` | timestamp | conditional | required for time-sensitive action |

`fallback` is the explicit manual fallback contract for timeout, unavailable model, invalid evidence, permission failure and user rejection; it is not an untracked UI message.

### AITrace

Records task type, input entity references, evidence references, policy version, model identifier, generation time, capability, limitations, output reference, fallback and user decision. It must not store secrets or raw analytics content by default.

### HumanGate

Records `gate_type`, target, required reason, evidence refs, decision, decision source, decided by, decided at, and expiry. Gate types include fact confirmation, version lock, publish confirmation, insight confirmation, privacy authorization and deletion confirmation.

### ActionEvent

Append-only event for offer, accept, reject, start, complete, fail, expire and cancel. Includes experiment id, cohort, state before/after, trace id, latency, error code and optional reason code.

### Experiment

Stores hypothesis, control/variant assignment, project refs, metric definitions, window, cohort, result summary and decision. It does not store a causal claim without an explicit comparison design.

### PublishHypothesis

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `id` / `project_id` / `version_id` | string | yes | project and publish candidate binding |
| `audience_problem` | string | yes | user-confirmed target situation |
| `reader_promise` | string | yes | no unsupported outcome promise |
| `expected_behaviors` | list[enum] | yes | save, comment, profile_visit, follow, other |
| `basis_refs` | list[string] | yes | Evidence, prior project, user judgment or rule refs |
| `uncertainties` | list[string] | yes | explicit unknowns; may be empty only after confirmation |
| `status` | enum | yes | draft, locked, superseded, legacy_missing |
| `locked_at` / `locked_by` | timestamp/string | conditional | required for locked |

A locked hypothesis is append-only. Locking it and `locked_publish_version_id` uses one transaction and one idempotency key.

### BlindReview

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `project_id` | string | yes | owner-scoped project |
| `hypothesis_snapshot_ref` | string | yes | immutable pre-publication snapshot |
| `result_snapshot_refs` | list[string] | yes | append-only performance snapshots |
| `comparison` | object | yes | supported, contradicted, unknown per claim |
| `visibility_boundary` | object | yes | allowed and forbidden input classes |
| `contamination_status` | enum | yes | clean, suspected, contaminated |
| `calibration_state` | enum | yes | valid, insufficient, calibration_invalid |
| `ai_trace_id` | string | conditional | required when AI compares inputs |

Post-hoc user explanations and completed review causes are forbidden inputs to the initial comparison.

### Observation

Stores `statement`, `scope`, supporting project refs, counterexample refs, sample count, next test, lifecycle status, user decision, and timestamps. Lifecycle is `observing`, `pending_validation`, `absorbed`, `refuted`, or `archived`. Terminal observations leave the current workbench but retain audit history.

### CreatorRule and RuleVersion

`CreatorRule` owns one active version and zero or more candidates. `RuleVersion` stores complete definition, applicability scope, support refs, counterexamples, full-sample reevaluation summary, consistency threshold/result, prior version ref, approval gate, decision reason, and rollback state.

One project cannot activate a rule. Activation is atomic: approve candidate, supersede previous version, and update the active pointer. Rejection and rollback preserve all history.

### BenchmarkSample

Links a historical project, imported post, metric snapshots, sample quality, inclusion state, and exclusion reason. Missing metrics remain unknown, never zero. Benchmark samples support relative calibration only and never exact performance predictions.

## Relations to 008

- `CreatorState` belongs to `CreatorProfile` and references `ContentProject`.
- `Evidence` extends the logical role of `Material`, Brief interview answers and confirmed review facts.
- `NextBestAction` targets existing v2 entities; it does not create a second project lifecycle.
- `AITrace` attaches to every AI-generated output in the v2 domain.
- `HumanGate` protects existing ContentVersion, PublishRecord and LearnedInsight transitions.
- `ContentGenome` receives only confirmed insights and user-approved evidence relationships.
- `CreatorViewpoint` enters `CreatorState` only after explicit confirmation and enters `ContentGenome.viewpoint_context` only while all source Evidence remains valid.
- `CreatorSeries` enters `CreatorState` only after explicit confirmation and enters `ContentGenome.series_context` only while every source project remains published, non-archived and owner scoped.

### ContentOpportunity

`ContentOpportunity` is an explainable, user-decidable candidate that may create one ContentProject. The first supported type is `series_extension`. It stores inherited intent and format, proposed and confirmed title/audience change/material requirements, evidence and unknown references, AITrace, decision status, created project reference, optimistic version and append-only decision events. A proposed opportunity never creates a project; acceptance uses a stable project idempotency key and replay repairs an interrupted project link without duplication.
- `PublishHypothesis` belongs to one `ContentProject` and one candidate/publish `ContentVersion`.
- `BlindReview` reads one locked hypothesis and one or more append-only `PerformanceSnapshot` records.
- `Observation` is proposed by a `Review` and may later support one or more `RuleVersion` candidates.
- `CreatorRule` belongs to `CreatorProfile`; `RuleVersion` references `BenchmarkSample`, supporting projects, counterexamples, and a `HumanGate`.

## Deletion and invalidation

Deleting or revoking an Evidence/Material invalidates action references, candidate versions, unpublished checks and genome edges. Confirmed published records retain only the minimum auditable reference snapshot permitted by the product retention policy. Deleted content must not be recoverable from a vector cache.

If revoked Evidence supported a confirmed CreatorViewpoint, the viewpoint and its events remain in audit history, its Genome node becomes `needs_review`, and it is removed from `viewpoint_context`. Revoking the viewpoint itself also removes its CreatorState reference without deleting history.

Archiving or deleting a source ContentProject, removing its locked publish version, or invalidating its publication removes the related CreatorSeries from `series_context`. The series node and append-only decision events remain for audit with `needs_review` provenance.

If deletion invalidates evidence used by a hypothesis or rule candidate, the immutable historical snapshot remains as an inaccessible/tombstoned reference, while calibration state changes to `calibration_invalid` and future rule activation is blocked.
