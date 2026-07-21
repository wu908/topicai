# API Contract: TopicAI v2 Content Project

**Base path**: `/api/v2`  
**Authentication**: Bearer JWT from compatible `/api/v1/auth/*` endpoints.  
**Envelope**: `{ code, data, message, meta }`; `meta` may include `request_id`, `idempotency_replayed`, and `ai_trace`.

## Shared Rules

- Every non-public endpoint scopes reads and writes to the authenticated owner.
- Aggregate writes include `expected_version`; mismatches return `409 VERSION_CONFLICT` with current version.
- Creation side effects include `idempotency_key`; replay returns the original resource with `meta.idempotency_replayed=true`.
- AI failures use a typed error and preserve a manual path. They never return fabricated fallback content.
- `AITrace` contains task, evidence refs, prompt-policy version, configured model identifier, capability set, time, confidence label, limitations, outcome, and user decision.
- Timestamps are UTC ISO-8601. IDs are UUID strings.

## Endpoints

| Method and path | Purpose | Request | Success |
|---|---|---|---|
| `PUT /onboarding/mode` | Select `starter` or `growth` | `mode`, `expected_version` | Updated user context |
| `GET/PUT /starter/assessment` | Resume/save readiness and real asset inventory | Assessment fields, `expected_version` | Assessment |
| `POST /starter/directions:generate` | Produce at most three evidence-backed directions | none; reads assessment | Candidates + AI trace or typed unavailable state |
| `POST /starter/sprints` | Select direction and begin 14-day experiment | `direction_candidate_id`, `idempotency_key` | Sprint and three proposed/created projects |
| `PUT /starter/sprints/{id}/review` | Complete starter review | evidence, blockers, next experiment, `expected_version` | Reviewed sprint |
| `POST /history-imports` | Import historical note records | `method=manual|csv|json`, `items[]`, `idempotency_key` | Per-item success/failure results |
| `GET/PUT /creator-profile` | Read/correct/confirm creator profile | profile fields, confirmation state, `expected_version` | Profile with evidence refs |
| `GET /today` | Weekly progress and one primary next task | optional local date | Goal, completed count, primary and secondary tasks |
| `GET /opportunities` | Filter explainable opportunities | optional type/decision/timeliness | Opportunity list |
| `POST /opportunities:generate` | Generate from first-party and evergreen sources | optional desired count | Opportunity list or empty list |
| `POST /opportunities` | Manual keyword/URL/official-inspiration intake | trigger, raw input, source metadata, `idempotency_key` | Opportunity with verification state |
| `PUT /opportunities/{id}/decision` | Adopt/save/reject | decision, optional reason | Updated opportunity + immutable feedback event |
| `GET/POST /projects` | List or create content projects | filters; or title, goal, audience, source ids, `idempotency_key` | Project list/project |
| `GET/PATCH /projects/{id}` | Read/update project metadata or archive | changed fields, `expected_version` | Project |
| `POST /projects/{id}/transitions` | Apply canonical state transition | `to_status`, reason, `expected_version`, `idempotency_key` | Project + state event |
| `GET/PUT /projects/{id}/brief` | Read/save structured brief | brief fields, `expected_version` | Brief |
| `POST /projects/{id}/interview:generate` | Ask for missing first-party evidence | optional targeted gaps | Questions + AI trace |
| `POST /projects/{id}/interview-answers` | Save user answers/material links | answers, `expected_version` | Updated completeness |
| `GET/POST /projects/{id}/versions` | List/create immutable versions | title, body, cover/image plan, parent, origin, project version, idempotency | Version list/version |
| `POST /projects/{id}/ai-suggestions` | Create non-destructive local suggestion | task type, target range/field, instructions, evidence refs | Suggestion + AI trace |
| `PUT /ai-suggestions/{id}/decision` | Accept/reject suggestion | decision, reason, expected project version | New version if accepted; feedback event always |
| `PUT /projects/{id}/draft-recovery` | Store recoverable working draft | device id, base version, draft, expiry | Recovery pointer |
| `POST /projects/{id}/publish-checks` | Check a selected version | `content_version_id`, `idempotency_key` | Version-bound findings |
| `PUT /publish-checks/{id}/resolution` | Acknowledge/resolve findings | finding decisions | Updated check; original findings unchanged |
| `POST /projects/{id}/publish-records` | Lock version and record publication | version id, note URL, published time, idempotency | Immutable publish record |
| `POST /publish-records/{id}/snapshots` | Append manual/confirmed screenshot metrics | captured time, source, metrics, confirmation, supersedes id, idempotency | Snapshot |
| `POST /snapshots:extract` | Extract proposed metrics from screenshot | material id | Unconfirmed values + AI trace or vision-unavailable error |
| `GET/PUT /projects/{id}/review` | Read/save fact-hypothesis-experiment review | facts, hypotheses, one continue/stop/experiment, `expected_version` | Review and proposed insights |
| `PUT /insights/{id}/decision` | Confirm/reject/retire insight | state | Insight; only confirmed enters context |
| `GET/POST /materials` | List/create text/link/image/document materials | filters; or kind/title/content/privacy/project | Material list/material |
| `GET/PATCH/DELETE /materials/{id}` | Read/update/delete with impact check | changes, expected version | Material or dependency impact |
| GET/PUT /settings | Read/update weekly goal, strategy, account reference, and consent | changed fields, expected_version | User settings and AI capability status |
| `POST /account/export` | Request full personal-data export | none | Job state |
| `POST /account/deletion` | Revoke credentials and request deletion | confirmation | Job state |

## Canonical Types

### `ProjectStatus`

`inbox | preparing | creating | ready_to_publish | published | awaiting_review | settled`

UI mapping is fixed: `灵感箱 | 准备中 | 创作中 | 待发布 | 已发布 | 待复盘 | 已沉淀`.

### `Opportunity`

Required fields:

```text
id, title, opportunity_type, source_trigger, audience_problem,
source_refs[], verification_state, timeliness, creator_fit, audience_fit,
material_readiness, growth_role, series_potential, similarity_risk,
safety_risk, rationale, decision?, expires_at?, version
```

Prohibited fields in v2: `estimated_heat`, `composite_score`, `viral_probability`, `ctr_estimate`, or model-generated realtime source claims.

### `ContentProject`

Required summary fields:

```text
id, title, status, platform=xiaohongshu, format=graphic_note,
primary_goal, target_audience, opportunity_id?, starter_sprint_id?,
planned_publish_at?, current_version_id?, locked_publish_version_id?,
last_action, last_action_at, archived_at?, version
```

### `ContentVersion`

```text
id, project_id, parent_version_id?, version_number, title, body_text,
cover_plan, image_plan[], change_origin, change_summary?, evidence_snapshot[],
ai_trace_id?, content_hash, created_at
```

Versions are immutable. Any accepted AI change creates a new version.

### `PerformanceSnapshot`

```text
id, publish_record_id, captured_at, source=manual|screenshot,
metrics{views?,likes?,favorites?,comments?,shares?,follows_gained?},
screenshot_material_id?, confirmed_by_user, supersedes_id?, created_at
```

Missing metrics are `null`, never inferred as zero. Screenshot extraction is proposed data until user confirmation.

### `Review`

```text
id, project_id, publish_record_id, status, facts[], hypotheses[],
continue_action, stop_action, experiment_action, proposed_insights[],
revision_number, completed_at?, version
```

Exactly one non-empty continue, stop, and experiment action is required to complete.

## Error Contract

```json
{
  "code": 409,
  "data": null,
  "message": "Project changed since you opened it",
  "error": {
    "error_code": "VERSION_CONFLICT",
    "details": { "current_version": 7, "expected_version": 6 }
  },
  "meta": { "request_id": "..." }
}
```

Stable error codes:

- `AUTH_REQUIRED`, `FORBIDDEN`, `NOT_FOUND`
- `VALIDATION_ERROR`, `INVALID_STATE_TRANSITION`
- `VERSION_CONFLICT`, `IDEMPOTENCY_CONFLICT`
- `SOURCE_UNVERIFIED`, `SOURCE_EXPIRED`
- `AI_NOT_CONFIGURED`, `AI_UNAVAILABLE`, `AI_CAPABILITY_MISSING`, `AI_OUTPUT_INVALID`
- `PUBLISH_CHECK_STALE`, `LOCKED_VERSION_IMMUTABLE`
- `MATERIAL_IN_USE`, `EXPORT_PARTIAL_FAILURE`

## Legacy Compatibility

- `/api/v1/auth/*`, `/api/v1/health*`, and compatible upload/download primitives remain available.
- `/api/v1/topics`, `/ideas`, `/titles`, `/viral`, `/publish`, and prediction-oriented review endpoints become typed deprecation shims after equivalent v2 navigation is live.
- Shims return `replacement`, `deprecated=true`, and a removal target release; they do not generate new legacy records.
- New frontend code imports only v2 domain contracts except auth and low-level file upload.

