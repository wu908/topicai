# Implementation Plan: TopicAI Content Project MVP

**Branch**: `008-content-project-mvp` | **Date**: 2026-07-17 | **Spec**: [spec.md](./spec.md)  
**Research**: [research.md](./research.md) | **Data model**: [data-model.md](./data-model.md) | **API contract**: [contracts/api-v2.md](./contracts/api-v2.md)

## Summary

Transform the copied TopicAI v4 tool suite into a Xiaohongshu knowledge/experience graphic-creator MVP. Preserve the proven React/FastAPI/SQLite infrastructure, introduce a breaking `/api/v2` content-project domain, provide lightweight starter and complete growth entry paths, and make `ContentProject` the only path through opportunity, brief, evidence interview, versioned creation, publish check, manual publication, performance snapshot, review, and confirmed learning.

The implementation explicitly removes fake precision and runtime hotspot simulation from the new domain. AI uses one provider-neutral OpenAI-compatible boundary configured at deployment time. The release target is a fresh-data local Docker environment.

## Technical Context

**Language/Version**: Python 3.11+ backend; TypeScript 6 / React 19 frontend.  
**Primary Dependencies**: Existing FastAPI, Pydantic 2, SQLAlchemy 2, aiosqlite, OpenAI-compatible SDK, React Router, MUI 5, Zustand, Axios. No new production dependency is planned.  
**Storage**: Existing SQLite async database and local object storage; immutable SQL migration history through `045`. Chroma is not required.
**Testing**: pytest/pytest-asyncio/pytest-cov, Vitest/Testing Library, Playwright.  
**Target Platform**: Local Docker Compose on desktop; responsive web UI at mobile and desktop widths.  
**Project Type**: Existing full-stack web application.  
**Performance Goals**: Non-AI reads and writes p95 <500 ms locally; initial page shell <2 s on local Docker; autosave feedback <300 ms after debounce; AI tasks expose progress and time out with a manual path rather than blocking the project.  
**Constraints**: Fresh runtime data; one primary Xiaohongshu account; no automatic publish/sync; no continuous hotspot/news source; no fixed model vendor; no rich-text framework; no team/MCN surface.  
**Scale/Scope**: Single local deployment, dozens of test users, up to 200 imported notes per import, 1-4 weekly projects per user, seven project states, five primary navigation nodes.

## Constitution Check

Constitution v3.0.0 ends the compatibility release and makes the implemented product v2-only. Historical migrations remain upgradeable, but v1 runtime code and public routes are removed.

| Principle | Plan compliance |
|---|---|
| I. Service layer | New state, opportunity, AI, publish, review, and deletion rules live in services; routes remain adapters. |
| II. Test first | Each task phase begins with contract/state/service/UI tests; coverage floor remains 80%. |
| III. AI provenance | `AITrace` is a first-class entity and appears in every AI response/record. |
| IV. Provider neutrality | Existing client is adapted to generic OpenAI-compatible runtime config; no named vendor in domain code. |
| V. Observability/YAGNI | Existing hooks retained; optional services do not block startup; no new infrastructure dependency. |
| VI. User facts first | Interview gates full drafting; generation context uses source refs and confirmed insights only. |
| VII. Typed contracts | `/api/v2` Pydantic requests/responses mirror `contracts/api-v2.md`. |
| VIII. Source integrity | New opportunity service never calls legacy DataManager/LLMDataSource/preloaded trends. |
| IX. Review loop | Predictions removed; append-only snapshots feed fact/hypothesis/experiment review. |
| X. Confirmed learning | Automatic feedback weight mutation is disabled for v2; only confirmed insights enter context. |
| XI. Risk guard | Existing rules adapt to version-bound checks with provenance and staleness. |
| XII. Manual platform boundary | Export/copy/manual link/manual metrics only. |
| XIII. Security/privacy | Existing auth and owner scoping reused; export/deletion and retention added. |
| XIV. Versioning/migrations | The public surface is `/api/v2` only; migration 045 removes audited-empty v1 business tables while preserving users, creator profiles, and v2 data. |

**Gate result**: PASS before design and PASS after data/API design. No unjustified violation remains.

## Project Structure

```text
backend/
├── app/
│   ├── api/v2/                 # sole typed API, including auth and health
│   ├── models/                 # v2 domain and AI trace schemas
│   ├── services/               # aggregate/domain services
│   ├── prompts/                # versioned task policies
│   ├── core/                   # auth, database, generic LLM, storage
│   └── data/migrations/        # immutable upgrade chain through 045
└── tests/                      # contract, service, migration, integration
frontend/
├── src/
│   ├── app/                    # route definitions and navigation metadata
│   ├── components/             # retained common/layout/feedback + project UI
│   ├── features/               # onboarding, today, opportunities, projects, materials, me
│   ├── services/api/v2/        # typed v2 clients
│   ├── store/                  # auth/profile + project/draft stores
│   └── types/contracts/v2/     # v2 TypeScript contracts
└── e2e/                        # starter and growth journeys
specs/008-content-project-mvp/  # specification, design, contracts, tasks
```

**Structure decision**: Preserve the two-project repository. Frontend behavior is grouped by product feature while shared visual primitives stay in existing component folders. Backend behavior follows existing model/service/router boundaries. The compatibility period is complete: v1 runtime code, routes, schemas, pages, providers, and tests are deleted.

## Implementation Changes

### 1. Baseline, encoding, and configuration

- Re-run backend and frontend tests inside the writable copy before behavior changes. Record passing count and coverage. Reproduce the one observed integration failure separately from source-path permission errors.
- Normalize source files to UTF-8 and add a check for mojibake markers in user-facing TypeScript/Markdown. Fix only displayed strings touched by the MVP; do not perform an unrelated whole-repo rewrite.
- Replace fixed provider settings with `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS`, and `LLM_CAPABILITIES=text[,vision]`. Keep the existing OpenAI client, structured parser, retry limits, and observability interface.
- Remove TianAPI, named-provider variables, and their runtime modules from Docker, environment examples, and dependencies.

### 2. Backend foundation and persistence

- Register only `app/api/v2/router.py`; authentication and health live under `/api/v2`.
- Add migrations `009`-`017` exactly as sequenced in [data-model.md](./data-model.md). Each migration is idempotent and covered on fresh DB plus copied-v4 baseline.
- Implement shared `IdempotencyService`, optimistic concurrency helper, owner-scoped repository helpers, and canonical `ProjectStateService`. Keep SQL behind services and transactions.
- Add Pydantic modules for starter, opportunity, content project, material, publish/review, AI trace, and common v2 errors. Generate/sync TypeScript contracts from the reviewed shapes without introducing runtime code generation.

### 3. Core vertical slice: Today and growth content project

- Replace the sidebar with `今日｜内容｜机会｜素材｜我的`; `/` redirects to `/today` after authentication.
- Implement Today from persisted weekly goal and project state. Primary task precedence: stale publish check/blocker, due review, ready-to-publish, creating, preparing, starter sprint task, create first project.
- Implement project list/detail and the state machine. Project detail is one shell with Brief, Create, Publish, and Review stages; stage controls are contextual, not separate primary tools.
- Implement structured plain-text creation with draft recovery, explicit immutable versions, local AI suggestions, accept/reject, and version comparison. AI cannot write directly to the current version.

### 4. Onboarding and profile

- Reuse login/register and add mode selection after first authentication.
- Starter path: assessment -> up to three candidates -> selected 14-day sprint -> three shared projects -> starter review. If readiness is false, save and exit without creating a sprint.
- Growth path: manual/CSV/JSON history import -> per-item results -> evidence-backed profile proposal -> user correction/confirmation -> Today.
- Reconcile the existing creator profile service; v2 ignores legacy rubric weights. Rejected attributes remain auditable and are excluded from context.

### 5. Explainable opportunities

- Add opportunity generation from history, questions, materials, series, evergreen needs, and confirmed insights. Ranking may use deterministic eligibility/order rules but returns qualitative dimensions, not probabilities.
- Add manual keyword/URL/official-inspiration intake. Store raw input and user-provided source metadata. URL verification is optional for P0; inability to verify yields `pending/insufficient`, never invented facts.
- Do not import Firecrawl into runtime. Do not call `DataManager`, TianAPI, Bilibili, `LLMDataSource`, or `PreloadedDataSource` from v2.
- Adopt/save/reject creates immutable feedback and an idempotent project only on adopt.

### 6. Publish, performance, and review

- Adapt `ContentRiskService` into a version-bound publish-check service. Preserve deterministic rules when AI is unavailable; add finding ranges, rule source/update time, staleness, and acknowledgements.
- Add copy/export commands using existing browser/local storage primitives. Partial image export is retryable per artifact.
- Publication locks one immutable version and creates a manual `PublishRecord`. Duplicate requests replay the same record.
- Add manual metrics and optional screenshot extraction when `vision` capability is declared. Extracted values remain proposed until user confirmation.
- Replace prediction/attribution flow with snapshot -> facts -> hypotheses -> exactly one continue/stop/experiment -> proposed insights. Only confirmed insights enter future context.

### 7. Materials, My, privacy, and v2-only cleanup

- Adapt assets into lightweight Materials with text/link/image/document kinds, privacy, project links, usage inspection, and locked-version reference snapshots.
- My contains creator strategy, weekly goal, Xiaohongshu account reference, AI configuration status (never key value), privacy/export/deletion, and sign-out.
- Add export/deletion jobs using existing scheduler/task patterns; local MVP may execute synchronously behind a job-state contract but the API remains asynchronous.
- Remove all legacy frontend routes instead of redirecting them; unknown paths use the normal Not Found view.
- Remove all `/api/v1` routers, schemas, services, data sources, providers, tests, and dependencies. OpenAPI must contain no v1 path.
- Retain immutable migration history for upgrades. Migration 045 moves reused asset rows to `materials`, rebuilds `creator_profiles` with v2 columns, drops v1-only tables, and preserves `users`, `schema_migrations`, and every v2 record.

## Delivery Phases

1. **Phase A - Baseline and foundation**: writable test baseline, Constitution v2, UTF-8 guard, generic LLM config, v2 router, schemas, migrations, state/idempotency helpers.
2. **Phase B - Core loop**: Today, project list/detail, brief, interview, versions, draft recovery, basic publish record. This is the earliest runnable vertical slice.
3. **Phase C - Growth onboarding and opportunities**: history import, profile confirmation, first-party opportunity generation, adoption.
4. **Phase D - Starter path**: assessment, direction candidates, sprint, three experiment projects, starter review.
5. **Phase E - Publish and learning**: risk checks, export, snapshots, screenshot fallback, reviews, confirmed insights.
6. **Phase F - Materials, privacy, v2-only cleanup**: Materials, My, export/delete, removal of v1 runtime surfaces, cleanup migration, and documentation.
7. **Phase G - Release validation**: full tests/coverage, fresh-volume Docker quickstart, desktop/mobile Playwright, source-integrity scan, OpenAPI sync.

Each phase lands only when its independent test is green; later phases may not weaken earlier contracts.

## Test Plan

### Backend

- Fresh and upgrade migration tests through 045, including repeat application, checksums, v1-table removal, and retained-data assertions.
- Project-state matrix tests for every allowed/blocked transition and archive behavior.
- Idempotency tests for project, version, publish, snapshot, and screenshot extraction.
- Concurrency tests returning `409` with no silent overwrite.
- Owner-isolation tests for every v2 resource.
- AI tests for success, timeout, malformed JSON, missing configuration, missing vision capability, evidence omissions, and manual fallback.
- Source-integrity tests proving v2 never calls legacy hotspot sources and never emits prohibited predictive fields.
- Deletion/export tests including stored files and locked reference snapshots.

### Frontend

- Component tests for five-node navigation, Today precedence, empty/loading/error states, state controls, version decisions, stale checks, metric confirmation, and insight decisions.
- Store tests for local draft recovery and version-conflict handling.
- Contract tests for v2 client envelopes and stable error mapping.
- Mojibake regression scan for displayed Chinese strings.

### End-to-end

- Starter: register -> starter assessment -> direction -> sprint -> first project -> publish -> starter review.
- Growth: register -> import mixed valid/invalid history -> confirm profile -> adopt opportunity -> brief/interview -> version -> check/export -> publish -> snapshots -> review -> confirm insight.
- Recovery: interrupt editing, refresh/offline simulation, restore draft, then resolve a version conflict.
- AI unavailable: complete core flow manually with no configured model.
- Responsive smoke: 390x844 and 1440x900 for onboarding and all five primary navigation nodes.
- Docker: fresh volumes, migrations, health, auth, core loop, restart persistence.

## Release and Recovery

- Validate a fresh named Docker project and an existing-database upgrade before release; never mount source runtime data into the validation project.
- There is no v1 runtime rollback. Recover by restoring a verified database backup and deploying a compatible v2 release; never reverse migration 045 in place.
- `AI_ENABLED` controls model calls while preserving manual paths. Vision requires both `VISION_ENABLED=true` and `vision` in `LLM_CAPABILITIES`.

## Complexity Tracking

| Decision | Why needed | Simpler alternative rejected because |
|---|---|---|
| New `/api/v2` domain | Old public schemas contain prohibited concepts and incompatible lifecycle semantics | In-place v1 mutation would silently break clients and violate API governance |
| Immutable migration chain plus cleanup migration 045 | Existing databases must upgrade without losing users, profiles, or v2 aggregates | Rewriting migration 000 or deleting history would make upgrades unsafe |
| Draft recovery separate from immutable versions | Users need refresh/offline recovery without polluting version history | Saving every keystroke as a version creates noise and storage churn |

No new production dependency, queue, external database, or runtime web-research service is introduced.
