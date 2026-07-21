# Data Model: TopicAI Content Project MVP

**Feature**: `008-content-project-mvp`  
**Storage target**: SQLite through the existing async SQLAlchemy database boundary.  
**Migration policy**: additive, numbered migrations after `008_creator_profiles_reconcile.sql`; existing baseline files remain immutable.

## Conventions

All new mutable aggregate rows use:

- `id TEXT PRIMARY KEY`: UUID string.
- `owner_user_id TEXT NOT NULL`: authenticated owner.
- `created_at TEXT NOT NULL`, `updated_at TEXT NOT NULL`: UTC ISO-8601.
- `version INTEGER NOT NULL DEFAULT 1`: optimistic concurrency token.
- `deleted_at TEXT NULL`: soft deletion where recovery or dependency inspection matters.
- `idempotency_key TEXT NULL`: unique within owner and operation scope for creation side effects.
- JSON values are serialized text validated by Pydantic at service boundaries.
- User-facing Chinese status labels are presentation values; APIs persist stable English enum values.

## Existing Entities Reused or Reconciled

### User

Existing `users` remains the identity authority.

New fields through migration:

| Field | Type | Rules |
|---|---|---|
| `product_mode` | enum text | `starter` or `growth`; default `growth` for compatibility |
| `timezone` | text | IANA timezone; default `Asia/Shanghai` |
| `weekly_publish_goal` | integer | 1..4; default 2 |
| `onboarding_state` | enum text | `not_started`, `in_progress`, `completed` |
| `consent_json` | JSON text | explicit import, AI, screenshot, and external-source consent flags |

### CreatorProfile

The existing table is reconciled by a new migration; legacy columns remain readable during one compatibility release.

| Field | Type | Rules |
|---|---|---|
| `niche` | text | user editable; provisional until confirmed |
| `target_audience` | text | user editable |
| `growth_goal` | enum text | `stable_publish`, `follower_growth`, `both` |
| `content_pillars_json` | JSON list | 1..5 confirmed or provisional pillars |
| `voice_traits_json` | JSON list | each item includes origin and confirmation |
| `avoid_traits_json` | JSON list | user-owned constraints |
| `evidence_refs_json` | JSON list | references to imported notes, materials, or confirmed insights |
| `confirmation_state` | enum text | `provisional`, `confirmed`, `needs_review` |
| `confirmed_at` | datetime nullable | set by explicit user confirmation |

Legacy rubric weights and hotspot preference are not used by v2 opportunity generation.

### PlatformAccount

Reuse `platform_accounts`; enforce at most one non-deleted `platform='xhs'` row per owner in MVP. OAuth status fields remain extension points and are not required for manual use.

## Historical Content Import

### HistoryImport

Tracks one idempotent import attempt: `method` (`manual`, `csv`, `json`), `status`, `input_count`, `success_count`, `failure_count`, `item_results_json`, `idempotency_key`, `started_at`, and `completed_at`.

### ImportedNote

Normalized historical evidence used by profile and opportunity services:
`history_import_id`, `external_key`, `title`, `body_excerpt`, `published_at`, `note_url`, `metrics_json`, `audience_questions_json`, `tags_json`, `source_hash`, `retention_expires_at`, and `user_confirmed`. Unique `(owner_user_id, source_hash)` prevents duplicates across retries/import methods. Missing metrics remain null. Raw body content follows the 90-day retention rule unless promoted to a Material.
## Starter Domain

### StarterAssessment

| Field | Type | Required | Notes |
|---|---|---:|---|
| `owner_user_id` | UUID | yes | one active assessment per user |
| `motivation` | enum | yes | `curious`, `career`, `expression`, `other` |
| `available_hours_per_week` | number | yes | 0..40 |
| `publish_commitment` | bool | yes | explicit intent to publish |
| `accept_experiment` | bool | yes | accepts test-not-permanent framing |
| `experience_assets_json` | list | no | user facts only |
| `interest_assets_json` | list | no | user facts only |
| `skill_assets_json` | list | no | user facts only |
| `privacy_limits_json` | list | no | topics or facts not to use |
| `readiness` | enum | yes | `not_ready`, `ready`, `paused` |
| `completed_at` | datetime | no | set after review |

### DirectionCandidate

| Field | Type | Required | Notes |
|---|---|---:|---|
| `assessment_id` | UUID FK | yes | cascade delete before sprint creation |
| `audience` | text | yes | candidate audience |
| `creator_credibility` | text | yes | evidence-backed reason the user can speak |
| `content_supply_json` | list | yes | real repeatable sources |
| `first_three_topics_json` | list | yes | exactly 3 experiment ideas |
| `production_cost` | enum | yes | `low`, `medium`, `high` |
| `similarity_risk` | enum | yes | `low`, `medium`, `high`, `unknown` |
| `validation_method` | text | yes | what the experiment should learn |
| `evidence_refs_json` | list | yes | assessment field references |
| `selection_state` | enum | yes | `proposed`, `selected`, `rejected` |

Constraint: maximum three non-deleted candidates per assessment; exactly one may be selected.

### StarterSprint

| Field | Type | Required | Notes |
|---|---|---:|---|
| `assessment_id` | UUID FK | yes | source assessment |
| `selected_direction_id` | UUID FK | yes | selected candidate |
| `starts_at`, `ends_at` | datetime | yes | 14-day default |
| `target_publish_count` | integer | yes | fixed at 3 in MVP |
| `published_count` | integer | yes | derived transactionally |
| `graduation_state` | enum | yes | `active`, `graduated`, `expired`, `paused`, `exited` |
| `blocker_reasons_json` | list | no | user-confirmed blockers |
| `next_topics_json` | list | no | post-review experiments |

Relation: one sprint has up to three `ContentProject` rows through `starter_sprint_id`.

## Opportunity Domain

### Opportunity

| Field | Type | Required | Notes |
|---|---|---:|---|
| `title` | text | yes | no predictive score |
| `opportunity_type` | enum | yes | `history_derivative`, `user_question`, `personal_material`, `series_followup`, `evergreen`, `hotspot` |
| `source_trigger` | enum | yes | `system`, `user_keyword`, `user_url`, `official_inspiration` |
| `audience_problem` | text | yes | explicit reader need |
| `source_refs_json` | list | yes | one or more `SourceReference` objects |
| `verification_state` | enum | yes | `verified`, `pending`, `insufficient` |
| `expires_at` | datetime | no | required when time-sensitive |
| `timeliness` | enum | yes | `evergreen`, `current`, `expiring`, `expired`, `unknown` |
| `creator_fit` | enum | yes | `strong`, `medium`, `weak`, `unknown` |
| `audience_fit` | enum | yes | same values |
| `material_readiness` | enum | yes | `ready`, `partial`, `missing` |
| `growth_role` | enum | yes | `discovery`, `trust`, `series`, `retention`, `experiment` |
| `series_potential` | enum | yes | `high`, `medium`, `low`, `unknown` |
| `similarity_risk` | enum | yes | `high`, `medium`, `low`, `unknown` |
| `safety_risk` | enum | yes | `high`, `medium`, `low`, `unknown` |
| `rationale` | text | yes | evidence-based explanation |
| `decision` | enum nullable | no | `adopt`, `save`, `reject` |
| `decision_reason` | text nullable | no | optional except configured reject reasons |
| `decided_at` | datetime nullable | no | immutable decision event also stored as feedback |

`SourceReference` fields: `ref_type`, `entity_id`, `url`, `publisher`, `published_at`, `collected_at`, `title`, `excerpt`, `verification_state`, `rights_note`. A model identifier is never valid as `ref_type`.

## Content Project Aggregate

### ContentProject

| Field | Type | Required | Notes |
|---|---|---:|---|
| `title` | text | yes | working title |
| `status` | enum | yes | stable English state below |
| `platform` | enum | yes | fixed `xiaohongshu` in MVP |
| `format` | enum | yes | fixed `graphic_note` in MVP |
| `primary_goal` | enum | yes | `stable_publish`, `follower_growth`, `experiment` |
| `target_audience` | text | yes | project-specific |
| `opportunity_id` | UUID FK nullable | no | source opportunity |
| `starter_sprint_id` | UUID FK nullable | no | starter experiment source |
| `planned_publish_at` | datetime nullable | no | user plan, not AI forecast |
| `current_version_id` | UUID FK nullable | no | latest explicit version |
| `locked_publish_version_id` | UUID FK nullable | no | set once per publish record |
| `last_action` | enum/text | no | Today resume calculation |
| `last_action_at` | datetime | yes | ordering |
| `archived_at` | datetime nullable | no | archive without deletion |

Canonical persisted states:

| API value | UI label | Entry condition | Normal exits |
|---|---|---|---|
| `inbox` | 灵感箱 | manual blank capture or saved idea | `preparing`, archive |
| `preparing` | 准备中 | project created/adopted | `creating`, `inbox` |
| `creating` | 创作中 | brief baseline saved | `ready_to_publish`, `preparing` |
| `ready_to_publish` | 待发布 | publish candidate version selected | `published`, `creating` |
| `published` | 已发布 | publish record committed | `awaiting_review` |
| `awaiting_review` | 待复盘 | review due or user starts review | `settled` |
| `settled` | 已沉淀 | review completed and insights decided | derivative/revision project only |

Rules:

- Backward transitions before publication create `ProjectStateEvent` rows.
- `published` cannot transition to a pre-publication state.
- Revision after publication creates a new child version and, if republished, a new derivative project or explicit revision publication flow; it never rewrites the original publish fact.
- Archive is orthogonal to status and cannot hide deletion impact.

### ProjectStateEvent

Append-only event: `project_id`, `from_status`, `to_status`, `reason`, `actor_type`, `created_at`, and `idempotency_key`.

### ContentBrief

One active brief per project with immutable baseline revisions:
`audience`, `reader_promise`, `core_conclusion`, `evidence_needed_json`, `structure`, `image_plan_json`, `differentiation`, `known_risks_json`, `completeness`, and `baseline_saved_at`.

### InterviewQuestion / InterviewAnswer

Questions store `project_id`, `question_text`, `reason`, `target_gap`, `sort_order`, and AI trace reference when generated. Answers store user text, referenced materials, and confirmation state. AI cannot create an answer row.

## Materials and Versions

### Material

Reconciles the existing asset domain.

| Field | Type | Notes |
|---|---|---|
| `kind` | enum | `text`, `link`, `image`, `document` |
| `title` | text | user-facing name |
| `body_text` | text nullable | text fact/case/quote |
| `source_url` | text nullable | links |
| `storage_path` | text nullable | reuse local object storage |
| `mime_type`, `size` | existing | file metadata |
| `privacy_level` | enum | `public`, `account_private`, `sensitive` |
| `origin` | enum | `manual`, `history_import`, `interview`, `screenshot` |
| `source_ref_json` | JSON nullable | traceable external/import source |

### ProjectMaterialLink

Join table: `project_id`, `material_id`, `usage_type` (`evidence`, `example`, `image`, `reference`), `created_at`. Unique on project/material/usage.

### ContentVersion

Append-only:
`project_id`, `parent_version_id`, `version_number`, `title`, `body_text`, `cover_plan_json`, `image_plan_json`, `change_origin` (`user`, `ai_accepted`, `import`, `recovery`), `change_summary`, `evidence_snapshot_json`, `ai_trace_id`, `content_hash`, `created_at`.

Unique `(project_id, version_number)` and content hash deduplication within a project. A locked version cannot be deleted or altered.

### DraftRecovery

One recoverable local/server draft pointer per project/device:
`project_id`, `device_id`, `base_version`, `draft_json`, `saved_at`, `expires_at`. It is not a ContentVersion until the user saves or restores it.

## Publishing and Review

### PublishCheck

`project_id`, `content_version_id`, `status`, `ruleset_version`, `findings_json`, `ai_trace_id`, `created_at`, `stale_at`, `user_resolution_json`.

A finding includes `finding_id`, `start`, `end`, `matched_text`, `reason`, `severity`, `rule_source`, `rule_updated_at`, and `suggested_action`.

### PublishRecord

`project_id`, `locked_version_id`, `platform`, `note_url`, `published_at`, `recorded_at`, `idempotency_key`, `revision_of_id`. Immutable except audited note URL correction.

### PerformanceSnapshot

`publish_record_id`, `captured_at`, `source` (`manual`, `screenshot`, future `api`), `metrics_json`, `screenshot_material_id`, `confirmed_by_user`, `supersedes_id`, `idempotency_key`. Append-only; screenshot extraction is not persisted as confirmed metrics until user confirmation.

MVP metric keys: `views`, `likes`, `favorites`, `comments`, `shares`, `follows_gained`. Missing metrics are null, not zero.

### Review

`project_id`, `publish_record_id`, `status` (`draft`, `completed`, `reopened`), `facts_json`, `hypotheses_json`, `continue_action`, `stop_action`, `experiment_action`, `ai_trace_id`, `completed_at`, `revision_number`.

### LearnedInsight

`review_id`, `category`, `statement`, `evidence_refs_json`, `state` (`proposed`, `confirmed`, `rejected`, `retired`), `decided_at`, `retired_at`. Only `confirmed` rows enter generation context.

## AI and Feedback

### AITrace

`owner_user_id`, `task_type`, `input_entity_refs_json`, `evidence_refs_json`, `prompt_policy_version`, `model_identifier`, `capabilities_json`, `generated_at`, `confidence_label` (`high`, `medium`, `low`, `unavailable`), `limitations_json`, `outcome` (`success`, `fallback`, `failed`, `cancelled`), `trace_id`, `user_decision`.

### UserFeedback

Reconcile existing table to generic targets:
`target_type`, `target_id`, `feedback_type`, `reason`, `created_at`. Rows are immutable. Remove automatic rubric mutation from the v2 path.

## Idempotency and Concurrency

- Create-project uniqueness: `(owner_user_id, operation='create_project', idempotency_key)`.
- Publish uniqueness: `(project_id, idempotency_key)` and one primary publish record per locked version.
- Snapshot uniqueness: `(publish_record_id, captured_at, source, idempotency_key)`.
- Every aggregate update requires `expected_version`; mismatch returns `409 VERSION_CONFLICT` with current version metadata.
- Idempotent retries return the previously created resource and `meta.idempotency_replayed=true`.

## Deletion and Retention

- Soft-delete projects/materials first to calculate references; account deletion physically removes them and stored files.
- Locked version evidence snapshots remain while the account exists even if the source material is deleted.
- Raw imported content and screenshot materials default to 90-day expiry unless promoted to a retained Material.
- External excerpts retain only the minimal text needed for provenance plus rights note.
- AI traces retain identifiers, policy, limitations, and decisions; raw prompts/responses are not required domain fields.

## Migration Sequence

Proposed migrations:

1. `009_user_product_mode.sql`: user mode, timezone, weekly goal, onboarding state, consent.
2. `010_starter_domain.sql`: assessment, candidates, sprint.
3. `011_opportunities.sql`: opportunities and source references JSON.
4. `012_content_projects.sql`: projects, state events, briefs, interview data.
5. `013_materials_v2.sql`: material extensions and project links while preserving assets.
6. `014_content_versions.sql`: versions and draft recovery.
7. `015_publish_review_v2.sql`: checks, publish records, snapshots, reviews, learned insights.
8. `016_ai_traces_feedback_v2.sql`: AI traces and generic feedback compatibility fields.
9. `017_creator_profile_v2.sql`: history import/imported note tables, profile reconciliation, and indexes.

Legacy tables remain during one compatibility release. No migration copies old recommendation, title, viral, publish-suggestion, or prediction rows into the new domain.

