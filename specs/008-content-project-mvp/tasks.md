# Tasks: 008 TopicAI Content Project MVP

**Input**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/api-v2.md](./contracts/api-v2.md), [quickstart.md](./quickstart.md)  
**Method**: Test-first per Constitution v3.0.0. Every user-story phase is independently demonstrable.
**Format**: `- [ ] T### [P?] [US?] Action with exact file path`

**Completion audit (2026-08-06)**: Paths below preserve the original implementation plan. Checkmarks are based on accepted behavior and runnable coverage. Later intent-driven design consolidated several planned one-file services/pages; the authoritative actual paths are mapped after Phase 11 rather than duplicating equivalent modules.

## Phase 1: Setup and Baseline

**Goal**: Establish a trustworthy writable-copy baseline and remove configuration/governance blockers before domain work.

- [x] T001 Run backend tests and coverage in `backend/`, save exact passing/failing counts and classify the previously observed integration failure in `specs/008-content-project-mvp/baseline-results.md`
- [x] T002 [P] Run frontend Vitest, build, lint, and Playwright discovery in `frontend/`, recording results in `specs/008-content-project-mvp/baseline-results.md`
- [x] T003 [P] Add a UTF-8/mojibake regression test for displayed frontend strings in `frontend/src/__tests__/encoding.test.ts`
- [x] T004 Fix only MVP-touched mojibake strings and normalize their files to UTF-8 in `frontend/src/pages/`, `frontend/src/components/`, and `frontend/src/utils/`
- [x] T005 [P] Add generic OpenAI-compatible settings tests in `backend/tests/core/test_llm_config_v2.py`
- [x] T006 Replace fixed runtime model settings with `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS`, and `LLM_CAPABILITIES` in `backend/config/settings.py` and `backend/config/llm_config.py`
- [x] T007 Adapt `LLMClient` to one provider-neutral OpenAI-compatible boundary and capability checks in `backend/app/core/llm.py`
- [x] T008 [P] Update safe examples without copying real keys in `backend/.env.example`, `frontend/.env.example`, and `docker-compose.yml`
- [x] T009 [P] Add tests for no-model startup, typed capability failures, and persisted AITrace outcomes in `backend/tests/core/test_llm_optional.py` and `backend/tests/services/test_ai_trace.py`
- [x] T010 [P] Add v2 router registration/health contract tests in `backend/tests/api/v2/test_router.py`
- [x] T011 Create and register `backend/app/api/v2/router.py` and `backend/app/api/v2/__init__.py` in `backend/main.py`
- [x] T012 Update copied runtime guidance to mark Spec-008 as planned, not yet complete, in `README.md` and `backend/README.md`

**Checkpoint**: Writable baseline is understood; local startup no longer requires named model vendors or hotspot keys.

## Phase 2: Foundational Domain and Persistence

**Goal**: Create the shared schemas, migrations, state machine, idempotency, and frontend contracts that block all stories.

### Tests first

- [x] T013 [P] Add fresh-database and migration-history tests through 045 in `backend/tests/data/`
- [x] T014 [P] Add upgrade-data preservation tests through 045 in `backend/tests/data/test_v2_only_cleanup_migration.py`
- [x] T015 [P] Add exhaustive allowed/blocked transition tests in `backend/tests/services/test_project_state.py`
- [x] T016 [P] Add idempotency replay/conflict and immutable generic feedback-target tests in `backend/tests/services/test_idempotency.py` and `backend/tests/services/test_feedback_v2.py`
- [x] T017 [P] Add optimistic concurrency and owner-isolation tests in `backend/tests/services/test_v2_concurrency.py`
- [x] T018 [P] Add Pydantic contract tests for the stable v2 enums and errors in `backend/tests/models/test_v2_models.py`

### Migrations and common services

- [x] T019 [P] Add user mode, timezone, weekly goal, onboarding state, and consent migration in `backend/app/data/migrations/009_user_product_mode.sql`
- [x] T020 [P] Add starter assessment/candidate/sprint migration in `backend/app/data/migrations/029_starter_domain.sql`
- [x] T021 [P] Add opportunity migration and source-reference indexes in `backend/app/data/migrations/011_opportunities.sql`
- [x] T022 [P] Add project/state-event/brief/interview migration in `backend/app/data/migrations/012_content_projects.sql`
- [x] T023 [P] Add material extensions and project-material links in `backend/app/data/migrations/013_materials_v2.sql`
- [x] T024 [P] Add immutable versions and draft recovery migration in `backend/app/data/migrations/014_content_versions.sql`
- [x] T025 [P] Add publish checks/records/snapshots/reviews/insights migration in `backend/app/data/migrations/015_publish_review_v2.sql`
- [x] T026 [P] Add AI trace and generic feedback compatibility migration in `backend/app/data/migrations/016_ai_traces_feedback_v2.sql`
- [x] T027 [P] Add history-import/imported-note tables plus creator-profile reconciliation in `backend/app/data/migrations/017_creator_profile_v2.sql`
- [x] T028 [P] Create v2 Pydantic models in `backend/app/models/v2/common.py`, `starter.py`, `opportunity.py`, `content_project.py`, `material.py`, `publish_review.py`, and `ai_trace.py`
- [x] T029 Implement canonical transition validation and append-only state events in `backend/app/services/project_state.py`
- [x] T030 [P] Implement owner-scoped idempotency reservation/replay and generic immutable feedback targets in `backend/app/services/idempotency.py` and `backend/app/services/feedback_v2.py`
- [x] T031 [P] Implement optimistic concurrency helpers and typed `VERSION_CONFLICT` errors in `backend/app/services/concurrency.py` and `backend/app/core/exceptions.py`
- [x] T032 [P] Implement AITrace persistence plus shared v2 API envelope/error adapters in `backend/app/services/ai_trace.py`, `backend/app/api/v2/deps.py`, and `backend/app/api/v2/errors.py`
- [x] T033 [P] Add reviewed v2 TypeScript contracts in `frontend/src/types/contracts/v2/index.ts`, `project.ts`, `opportunity.ts`, `starter.ts`, `material.ts`, and `review.ts`
- [x] T034 [P] Create the v2 Axios services and stable error mapping in `frontend/src/services/api/v2/client.ts` and `frontend/src/services/api/v2/errors.ts`
- [x] T035 Add an architectural test proving v2 services do not import legacy hotspot sources in `backend/tests/architecture/test_v2_source_boundaries.py`

**Checkpoint**: Migrations apply twice safely; state/concurrency/idempotency contracts are green; frontend can type v2 responses.

## Phase 3: User Story 1 - Resume the next meaningful content task (P1)

**Independent test**: A user with an unfinished project opens Today, reaches the correct next step in <=2 interactions, leaves mid-edit, and is offered recovery on return.

### Tests first

- [x] T036 [P] [US1] Add Today task-precedence and empty-state service tests in `backend/tests/services/test_today_workspace.py`
- [x] T037 [P] [US1] Add Today API owner/auth contract tests in `backend/tests/api/v2/test_today.py`
- [x] T038 [P] [US1] Add navigation, primary-task, and local recovery-offer component tests in `frontend/src/features/today/__tests__/TodayPage.test.tsx`
- [x] T039 [P] [US1] Add five-node sidebar desktop/mobile tests in `frontend/src/components/layout/__tests__/PrimaryNavigation.test.tsx`

### Implementation

- [x] T040 [US1] Implement weekly progress and primary-task precedence in `backend/app/services/today_workspace.py`
- [x] T041 [US1] Expose `GET /api/v2/today` in `backend/app/api/v2/today.py` and register it in `backend/app/api/v2/router.py`
- [x] T042 [P] [US1] Replace sidebar metadata with `今日｜内容｜机会｜素材｜我的` using MUI icons in `frontend/src/components/layout/Sidebar.tsx`
- [x] T043 [P] [US1] Add nested route configuration and protected `/today` entry in `frontend/src/app/routes.tsx` and simplify `frontend/src/App.tsx`
- [x] T044 [US1] Implement Today weekly progress, primary task, secondary tasks, empty/blocked/overdue states in `frontend/src/features/today/TodayPage.tsx`
- [x] T045 [US1] Add Today API/query state and local recoverable-draft lookup in `frontend/src/services/api/v2/today.ts` and `frontend/src/store/todayStore.ts`

**Checkpoint**: Today is independently demoable using seeded project data.

## Phase 4: User Story 2 - Complete a content project from opportunity to publication (P1)

**Independent test**: One project retains brief, interview evidence, versions, publish check, and a manual publish record through the canonical states.

### Tests first

- [x] T046 [P] [US2] Add project CRUD, transition, archive, and owner-isolation tests in `backend/tests/services/test_content_project_service.py`
- [x] T047 [P] [US2] Add brief completeness and evidence-gap tests in `backend/tests/services/test_content_brief_service.py`
- [x] T048 [P] [US2] Add immutable version, deduplication, lock, and ancestry tests in `backend/tests/services/test_content_version_service.py`
- [x] T049 [P] [US2] Add interview and local-suggestion AI success/timeout/malformed/missing-model tests in `backend/tests/services/test_interview_service.py` and `backend/tests/services/test_ai_suggestion.py`
- [x] T050 [P] [US2] Add project/brief/version/baseline-check/manual-publish v2 API contract tests in `backend/tests/api/v2/test_projects.py`
- [x] T051 [P] [US2] Add project list/detail/state UI tests in `frontend/src/features/projects/__tests__/ProjectFlow.test.tsx`
- [x] T052 [P] [US2] Add draft recovery and version-conflict store tests in `frontend/src/store/__tests__/projectDraftStore.test.ts`

### Implementation

- [x] T053 [US2] Implement transactional project CRUD/state/archive in `backend/app/services/content_project.py`
- [x] T054 [P] [US2] Implement brief revisions and evidence completeness in `backend/app/services/content_brief.py`
- [x] T055 [P] [US2] Implement interview questions and non-destructive local suggestions with first-party evidence refs in `backend/app/services/interview.py`, `backend/app/services/ai_suggestion.py`, `backend/app/prompts/interview/v1/system.md`, and `backend/app/prompts/local_rewrite/v1/system.md`
- [x] T056 [P] [US2] Implement immutable versions, hashes, ancestry, baseline deterministic publish check, version locking, and manual publish record in `backend/app/services/content_version.py`, `backend/app/services/publish_check.py`, and `backend/app/services/publish_record.py`
- [x] T057 [P] [US2] Implement draft-recovery expiry and restore behavior in `backend/app/services/draft_recovery.py`
- [x] T058 [US2] Expose projects, transitions, brief, interview, suggestions, versions, draft recovery, baseline checks, and manual publish records in `backend/app/api/v2/projects.py`
- [x] T059 [P] [US2] Add project API clients in `frontend/src/services/api/v2/projects.ts`
- [x] T060 [P] [US2] Add project list/status filters and empty states in `frontend/src/features/projects/ProjectListPage.tsx`
- [x] T061 [US2] Build the shared project shell with Brief, Create, baseline Publish, and Review stage navigation in `frontend/src/features/projects/ProjectWorkspacePage.tsx`
- [x] T062 [P] [US2] Build Brief and interview panels in `frontend/src/features/projects/BriefStage.tsx` and `frontend/src/features/projects/InterviewPanel.tsx`
- [x] T063 [P] [US2] Build structured title/body/cover/image-plan editor in `frontend/src/features/projects/CreateStage.tsx`
- [x] T064 [US2] Add suggestion accept/reject, immutable save, comparison, navigation guard, recovery, baseline check, and manual publish action in `frontend/src/features/projects/VersionPanel.tsx`, `frontend/src/features/projects/PublishStage.tsx`, and `frontend/src/store/projectDraftStore.ts`

**Checkpoint**: Core project creation through a locked publish candidate works without starter/profile/opportunity automation.

## Phase 5: User Story 3 - Start from a vague idea and run a three-post experiment (P1)

**Independent test**: A starter completes assessment, receives <=3 grounded directions, selects one, receives three linked projects, publishes at least one, and completes starter review without permanent-niche claims.

### Tests first

- [x] T065 [P] [US3] Add readiness, max-three-candidate, selection, and sprint lifecycle tests in `backend/tests/services/test_starter_service.py`
- [x] T066 [P] [US3] Add starter AI evidence/prohibited-claim tests in `backend/tests/services/test_starter_service.py`
- [x] T067 [P] [US3] Add starter v2 API tests in `backend/tests/api/v2/test_starter.py`
- [x] T068 [P] [US3] Add assessment/direction/sprint/review UI tests in `frontend/src/pages/Starter/__tests__/StarterPage.test.tsx`

### Implementation

- [x] T069 [US3] Implement starter assessment and readiness rules in `backend/app/services/starter_assessment.py`
- [x] T070 [P] [US3] Implement evidence-backed deterministic direction generation and AI trace in `backend/app/services/direction_candidate.py`
- [x] T071 [US3] Implement sprint creation, three idempotent experiment projects, progress, and graduation in `backend/app/services/starter_sprint.py`
- [x] T072 [US3] Expose starter assessment, directions, sprint, and review in `backend/app/api/v2/starter.py`
- [x] T073 [P] [US3] Add starter API client in `frontend/src/services/api/v2/starter.ts`; keep resumable server state in the workspace instead of duplicating it in a client store
- [x] T074 [US3] Build the resumable assessment, direction, sprint, and review flow in `frontend/src/pages/Starter/StarterPage.tsx`

**Checkpoint**: Starter path reaches the shared ContentProject shell and is independently demoable.

## Phase 6: User Story 4 - Build a correctable creator profile from real history (P1)

**Independent test**: Import ten notes with partial failures, correct inferred profile attributes, confirm them, and prove rejected attributes are excluded later.

### Tests first

- [x] T075 [P] [US4] Add per-item import, retry, deduplication, and 200-item limit tests in `backend/tests/services/test_history_import.py`
- [x] T076 [P] [US4] Add profile evidence/confirmation/rejection tests in `backend/tests/services/test_creator_profile_v2.py`
- [x] T077 [P] [US4] Add mode-selection/import/profile API tests in `backend/tests/api/v2/test_growth_onboarding.py`
- [x] T078 [P] [US4] Add mixed-result import and profile-review UI tests in `frontend/src/features/onboarding/__tests__/GrowthOnboarding.test.tsx`

### Implementation

- [x] T079 [US4] Implement product-mode selection plus manual/CSV/JSON history import and result persistence in `backend/app/services/onboarding_mode.py` and `backend/app/services/history_import.py`
- [x] T080 [US4] Reconcile profile inference, evidence, corrections, and confirmation in `backend/app/services/creator_profile_v2.py` and `backend/app/prompts/creator_profile/v2/system.md`
- [x] T081 [US4] Expose mode selection, history import, and creator profile endpoints in `backend/app/api/v2/onboarding.py`
- [x] T082 [P] [US4] Add mode/import/profile clients in `frontend/src/services/api/v2/onboarding.ts`
- [x] T083 [US4] Build mode selection, history import, result review, and profile confirmation in `frontend/src/features/onboarding/ModePage.tsx`, `HistoryImportPage.tsx`, and `ProfileReviewPage.tsx`

**Checkpoint**: Growth onboarding reaches Today with a confirmed or explicitly provisional profile.

## Phase 7: User Story 5 - Choose explainable opportunities without fake precision (P2)

**Independent test**: Generate source-backed opportunities, inspect qualitative dimensions, reject one, adopt one, and prove no legacy hotspot source or predictive field is used.

### Tests first

- [x] T084 [P] [US5] Add first-party source eligibility, ordering, expiry, and empty-result tests in `backend/tests/services/test_opportunity_service.py`
- [x] T085 [P] [US5] Add manual keyword/URL/official-inspiration verification tests in `backend/tests/services/test_manual_opportunity.py`
- [x] T086 [P] [US5] Add prohibited-field and no-legacy-import tests in `backend/tests/architecture/test_opportunity_integrity.py`
- [x] T087 [P] [US5] Add opportunity list/create/decision API tests in `backend/tests/api/v2/test_opportunities.py`
- [x] T088 [P] [US5] Add dimension/source/decision UI tests in `frontend/src/features/opportunities/__tests__/OpportunityPages.test.tsx`

### Implementation

- [x] T089 [US5] Implement opportunity derivation from history, questions, materials, series, evergreen needs, and confirmed insights in `backend/app/services/opportunity.py`
- [x] T090 [P] [US5] Implement manual hotspot intake with pending/insufficient verification and expiry in `backend/app/services/manual_opportunity.py`
- [x] T091 [US5] Implement immutable adopt/save/reject decisions and adopted-project idempotency in `backend/app/services/opportunity_decision.py`
- [x] T092 [US5] Expose opportunity list/generate/manual/decision endpoints in `backend/app/api/v2/opportunities.py`
- [x] T093 [P] [US5] Add v2 opportunity client in `frontend/src/services/api/v2/opportunities.ts`
- [x] T094 [US5] Build opportunity list, filters, evidence drawer, manual intake, and decision controls in `frontend/src/features/opportunities/OpportunityListPage.tsx` and `OpportunityDetailPage.tsx`

**Checkpoint**: Opportunity adoption creates one shared project with evidence and no fake score.

## Phase 8: User Story 6 - Publish with transparent assistance and manual control (P2)

**Independent test**: Select a version, run version-bound checks, resolve findings, export, record publication twice with one logical result, and observe stale checks after content changes.

### Tests first

- [x] T095 [P] [US6] Add version-bound risk, finding-location, provenance, stale, and no-model tests in `backend/tests/services/test_release_gaps.py`
- [x] T096 [P] [US6] Add publish-record lock/idempotency tests in `backend/tests/services/test_release_gaps.py`
- [x] T097 [P] [US6] Add per-artifact failure/retry tests in `frontend/src/features/content/__tests__/StageForms.test.tsx`
- [x] T098 [P] [US6] Add publish-check/publish-record API tests in `backend/tests/api/v2/test_release_gaps.py`
- [x] T099 [P] [US6] Add publish-stage responsive and stale-state UI tests in `frontend/src/features/projects/__tests__/PublishStage.test.tsx`

### Implementation

- [x] T100 [US6] Adapt deterministic and optional AI risk checks to content versions in `backend/app/services/publish_check.py`
- [x] T101 [US6] Implement version locking and immutable manual publication in `backend/app/services/publication.py`
- [x] T102 [US6] Expose publish checks, resolutions, and publish records in `backend/app/api/v2/publish_checks.py` and `calibration.py`
- [x] T103 [P] [US6] Add publish v2 client methods in `frontend/src/services/api/v2/projects.ts`
- [x] T104 [US6] Build check findings, acknowledgement, copy text, image-plan export, and publication form in `frontend/src/features/content/StageForms.tsx`
- [x] T105 [US6] Add per-artifact export retry and completion state in `frontend/src/features/content/StageForms.tsx`

**Checkpoint**: A real manual publication can be recorded with an auditable locked version.

## Phase 9: User Story 7 - Record performance and turn review into one next experiment (P2)

**Independent test**: Add manual 24h/72h snapshots, optionally extract unconfirmed screenshot values, complete a fact/hypothesis review, and confirm exactly one insight while rejecting another.

### Tests first

- [x] T106 [P] [US7] Add append-only snapshot, correction, null-metric, and idempotency tests in `backend/tests/services/test_performance_snapshot.py`
- [x] T107 [P] [US7] Add screenshot extraction and unconfirmed/manual-fallback tests in `backend/tests/services/test_release_gaps.py` and `backend/tests/api/v2/test_release_gaps.py`
- [x] T108 [P] [US7] Add review separation, exact-three-actions, revision, and confirmed-insight tests in `backend/tests/services/test_review_v2.py`
- [x] T109 [P] [US7] Add snapshot/review/insight API tests in `backend/tests/api/v2/test_reviews.py`
- [x] T110 [P] [US7] Add metric confirmation and fact/hypothesis/experiment UI tests in `frontend/src/features/review/__tests__/ReviewFlow.test.tsx`

### Implementation

- [x] T111 [US7] Implement manual and superseding snapshots in `backend/app/services/performance_snapshot.py`
- [x] T112 [P] [US7] Implement optional vision extraction as unconfirmed proposals in `backend/app/services/snapshot_extraction.py`
- [x] T113 [US7] Replace prediction logic with facts, hypotheses, three actions, revisions, and proposed insights in `backend/app/services/review_v2.py` and `backend/app/prompts/review/v2/system.md`
- [x] T114 [US7] Implement confirmed/rejected/retired insight decisions and context filtering in `backend/app/services/learned_insight.py`
- [x] T115 [US7] Expose snapshot extraction alongside the existing review routes in `backend/app/api/v2/calibration.py`
- [x] T116 [P] [US7] Add review v2 client in `frontend/src/services/api/v2/reviews.ts`
- [x] T117 [US7] Build metric entry/screenshot confirmation and review stages in `frontend/src/features/content/StageForms.tsx`

**Checkpoint**: Published projects reach `settled`; only confirmed insights affect later context.

## Phase 10: User Story 8 - Manage materials and settings without a separate asset system (P3)

**Independent test**: Create/reuse a material, inspect usages, protect locked references, update weekly goal, view AI capability status, export data, and request deletion.

### Tests first

- [x] T118 [P] [US8] Add text/link/file material, privacy, usage, and locked-reference deletion tests in `backend/tests/services/test_release_gaps.py`
- [x] T119 [P] [US8] Add settings plus HumanGate export/deletion, persisted job, credential-removal, and stored-file cleanup tests in `backend/tests/api/v2/test_account_data.py`
- [x] T120 [P] [US8] Add material/settings/account-data v2 API and owner-isolation tests in `backend/tests/api/v2/test_release_gaps.py` and `test_account_data.py`
- [x] T121 [P] [US8] Add Materials/My UI tests in `frontend/src/pages/Materials/__tests__/MaterialsPage.test.tsx` and `frontend/src/pages/Me/__tests__/MePage.test.tsx`

### Implementation

- [x] T122 [US8] Adapt local storage to Material kinds, privacy, project links, and locked reference snapshots in `backend/app/services/material.py`
- [x] T123 [US8] Implement settings plus synchronous personal-data export/deletion behind persisted job-state contracts in `backend/app/services/settings.py` and `account_data.py`
- [x] T124 [US8] Expose Materials, settings, AI-capability status, and account export/deletion endpoints in `backend/app/api/v2/materials.py`, `settings.py`, and `account_data.py`
- [x] T125 [P] [US8] Add Materials/My v2 client methods in `frontend/src/services/api/v2/projects.ts`
- [x] T126 [US8] Build the lightweight Materials list, project association, usages, privacy, and safe-delete flow in `frontend/src/pages/Materials/MaterialsPage.tsx`
- [x] T127 [US8] Build My strategy, weekly goal, Xiaohongshu reference, AI capability status, privacy/export/deletion, and sign-out in `frontend/src/pages/Me/MePage.tsx`

**Checkpoint**: Supporting material and account controls work without a complex DAM or platform OAuth.

## Phase 11: V2-Only Cleanup, Polish, and Release Validation

**Goal**: Retire old primary workflows safely, synchronize documentation/contracts, and prove the local Docker MVP.

### V2-only removal

- [x] T128 [P] Add frontend tests proving removed legacy paths reach Not Found in `frontend/src/__tests__/App.test.tsx`
- [x] T129 [P] Add OpenAPI and removed-v1 contract tests in `backend/tests/api/v2/test_v2_only_contract.py`
- [x] T130 Remove all legacy frontend routes and redirects from `frontend/src/App.tsx`
- [x] T131 Remove `/api/v1`, legacy services/models/data sources/providers, and their tests and dependencies
- [x] T132 Remove team/account-matrix entries from active navigation and build reachability in `frontend/src/components/layout/Sidebar.tsx` and `frontend/src/App.tsx`
- [x] T149 Add migration 045 and upgrade tests that migrate reused asset/profile data, drop v1-only tables, and preserve users, migration history, and v2 data
- [x] T150 Synchronize Constitution, plan, spec, research, data model, API contract, quickstart, READMEs, and agent guidance with the v2-only release
- [x] T151 Run final backend and frontend lint, tests, coverage, and production build
- [x] T152 Validate the rebuilt Compose stack, then remove only approved TopicAI images/volumes and global build cache while retaining base dependency images
- [x] T153 Add migration 046 and tests for material, publish-check, and screenshot-extraction release contracts
- [x] T154 Add migration 047 and tests for minimal auditable account export/deletion job state
- [x] T155 Add migration 048 and tests for credential revocation, complete export linkage, screenshot decisions, and material-kind normalization

### Cross-cutting validation

- [x] T133 [P] Cover the full growth loop in `backend/tests/api/v2/test_intent_driven_actions.py` and `test_calibration_loop.py`
- [x] T134 [P] Cover the starter-to-shared-project loop in `backend/tests/api/v2/test_starter.py` and `backend/tests/services/test_starter_service.py`
- [x] T135 [P] Cover the real manual/no-model journey in `frontend/e2e/intent-driven-loop.spec.ts`
- [x] T136 [P] Cover Growth onboarding and the complete shared loop in `frontend/e2e/intent-driven-loop.spec.ts`
- [x] T137 [P] Cover the real Starter onboarding and three-project handoff in `frontend/e2e/starter-flow.spec.ts`
- [x] T138 [P] Cover offline draft recovery and immutable-version continuation in `frontend/e2e/intent-driven-loop.spec.ts`
- [x] T139 [P] Cover desktop/mobile overflow and navigation overlap in `frontend/e2e/intent-driven-loop.spec.ts`
- [x] T140 [P] Add prohibited source/field scan to `scripts/check-v2-source-integrity.ps1`
- [x] T141 [P] Add UTF-8/mojibake scan to `scripts/check-utf8.ps1`
- [x] T142 Synchronize generated OpenAPI, v2 TypeScript contracts, and `specs/008-content-project-mvp/contracts/api-v2.md` in `backend/openapi3.json`
- [x] T143 Update `README.md`, `backend/README.md`, and `frontend/README.md` to the implemented five-node MVP and generic model config
- [x] T144 Validate `docker-compose.yml`, both Dockerfiles, and health checks against a fresh isolated Compose runtime
- [x] T145 Run backend pytest/ruff/mypy/bandit and enforce >=80% coverage from `backend/pyproject.toml`
- [x] T146 Run frontend Vitest coverage/lint/build/npm audit and all Playwright suites from `frontend/`
- [x] T147 Execute [quickstart.md](./quickstart.md) against fresh Docker volumes, restart services, and record results in `specs/008-content-project-mvp/release-validation.md`
- [x] T148 Run SpecKit cross-artifact analysis and resolve every CRITICAL/HIGH inconsistency before implementation is declared complete in `specs/008-content-project-mvp/`

## Consolidated Implementation Map

| Original tasks | Accepted implementation and coverage |
|---|---|
| T001-T012 | Baseline evidence in `baseline-results.md`; provider-neutral config in `backend/config/`, `backend/app/core/llm.py`, environment examples, `test_llm_config_v2.py`, and the repository UTF-8 gate. T012's temporary "planned" wording is superseded by the completed release docs. |
| T015-T035 | State, concurrency, idempotency, envelopes, and AI traces are consolidated in `project_state.py`, `v2_utils.py`, `ai_trace.py`, shared API dependencies/exceptions, migrations `012`-`048`, consolidated v2 model/TypeScript contract files, and source-integrity tests/scripts. Planned migration numbers that were never shipped are superseded by the immutable implemented sequence. |
| T036-T045 | Today precedence is part of `IntentOrchestratorService` and `/api/v2/today` in `intent_actions.py`; the five-node UI uses `HomePage`, `Sidebar`, `App`, and local recovery in `features/content/projectDraft.ts`. Coverage lives in `test_calibration_loop.py`, `HomePage.test.tsx`, `Sidebar.test.tsx`, and Playwright. |
| T046-T064 | The shared project workflow is implemented by `content_project.py`, `content_version.py`, `evidence.py`, `candidate_review.py`, `publish_check.py`, `publication.py`, v2 project/action APIs, `ContentPage`, `ProjectWorkspace`, `StageForms`, and `projectDraft.ts`, with API/service/component/E2E coverage. This supersedes the planned Brief/Create/Publish page split. |
| T075-T083 | Growth onboarding uses `history_import.py`, `creator_profile_v2.py`, `onboarding_mode.py`, `api/v2/onboarding.py`, `services/api/v2/onboarding.ts`, and the consolidated `GrowthOnboardingPage` plus their existing service/API/UI tests. |
| T084-T094 | Opportunity generation, verification, decisions, and project adoption are consolidated in `content_opportunity.py`, `api/v2/content_opportunities.py`, `OpportunitiesPage`, `projects.ts`, and the opportunity service/API/UI tests. |
| T099, T106-T116 | Responsive/stale publish UI, append-only snapshots, fact/cause/experiment review, and confirmed learning use `StageForms`, `ContentPage`, `performance_snapshot.py`, `blind_review.py`, `observation.py`, calibration/action APIs, and consolidated project clients; coverage lives in `test_calibration_loop.py`, `test_intent_driven_actions.py`, `StageForms.test.tsx`, `ContentPage.test.tsx`, and Playwright. |
| T133-T141 | Cross-layer journeys are intentionally kept in two Playwright specs and existing API integration suites; static release checks are standalone PowerShell scripts invoked by CI. |

## Dependencies and Execution Order

- Phase 1 blocks all work.
- Phase 2 blocks every user story.
- US1 can use seeded project fixtures after Phase 2.
- US2 is the core aggregate and blocks production integration for US3, US5, US6, and US7.
- US3 and US4 may proceed in parallel after US2 service contracts exist.
- US5 depends on US4 for history/profile sources and US2 for adoption.
- US6 depends on US2 versions.
- US7 depends on US6 publication records.
- US8 may proceed in parallel after Phase 2, but locked-reference validation depends on US2 versions.
- Phase 11 starts after all selected MVP stories are green.

## Parallel Opportunities

- Migration files T019-T027 are parallel after their tests exist, then validated together.
- Pydantic/TypeScript/client foundation tasks T028-T034 are parallel by write scope.
- Backend service tests and frontend component tests within each story are parallel.
- Starter US3 and growth onboarding US4 can run in parallel after the core project contract.
- Publish US6 and material US8 can run in parallel after immutable versions land.
- Release E2E and static scans T133-T141 are parallel once feature behavior stabilizes.

## MVP Delivery Recommendation

The first usable internal build is Phases 1-4: baseline/foundation + Today + one manually created content project through publication. The approved full validation MVP additionally includes US3-US8 because both starter and growth audiences were selected. Do not expose the product to test users until Phase 11 passes fresh-Docker validation.

## Task Format Validation

- Total tasks: 155.
- Setup/foundational tasks: 35.
- US1: 10 tasks.
- US2: 19 tasks.
- US3: 10 tasks.
- US4: 9 tasks.
- US5: 11 tasks.
- US6: 11 tasks.
- US7: 12 tasks.
- US8: 10 tasks.
- Compatibility/release: 28 tasks.
- Every task includes a checkbox, sequential ID, story label where required, concrete action, and file path.



