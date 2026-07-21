# Tasks: 008 TopicAI Content Project MVP

**Input**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/api-v2.md](./contracts/api-v2.md), [quickstart.md](./quickstart.md)  
**Method**: Test-first per Constitution v2.0.0. Every user-story phase is independently demonstrable.  
**Format**: `- [ ] T### [P?] [US?] Action with exact file path`

## Phase 1: Setup and Baseline

**Goal**: Establish a trustworthy writable-copy baseline and remove configuration/governance blockers before domain work.

- [ ] T001 Run backend tests and coverage in `backend/`, save exact passing/failing counts and classify the previously observed integration failure in `specs/008-content-project-mvp/baseline-results.md`
- [ ] T002 [P] Run frontend Vitest, build, lint, and Playwright discovery in `frontend/`, recording results in `specs/008-content-project-mvp/baseline-results.md`
- [ ] T003 [P] Add a UTF-8/mojibake regression test for displayed frontend strings in `frontend/src/__tests__/encoding.test.ts`
- [ ] T004 Fix only MVP-touched mojibake strings and normalize their files to UTF-8 in `frontend/src/pages/`, `frontend/src/components/`, and `frontend/src/utils/`
- [x] T005 [P] Add generic OpenAI-compatible settings tests in `backend/tests/core/test_llm_config_v2.py`
- [ ] T006 Replace fixed runtime model settings with `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS`, and `LLM_CAPABILITIES` in `backend/config/settings.py` and `backend/config/llm_config.py`
- [ ] T007 Adapt `LLMClient` to one provider-neutral OpenAI-compatible boundary and capability checks in `backend/app/core/llm.py`
- [ ] T008 [P] Update safe examples without copying real keys in `backend/.env.example`, `frontend/.env.example`, and `docker-compose.yml`
- [ ] T009 [P] Add tests for no-model startup, typed capability failures, and persisted AITrace outcomes in `backend/tests/core/test_llm_optional.py` and `backend/tests/services/test_ai_trace.py`
- [x] T010 [P] Add v2 router registration/health contract tests in `backend/tests/api/v2/test_router.py`
- [x] T011 Create and register `backend/app/api/v2/router.py` and `backend/app/api/v2/__init__.py` in `backend/main.py`
- [ ] T012 Update copied runtime guidance to mark Spec-008 as planned, not yet complete, in `README.md` and `backend/README.md`

**Checkpoint**: Writable baseline is understood; local startup no longer requires named model vendors or hotspot keys.

## Phase 2: Foundational Domain and Persistence

**Goal**: Create the shared schemas, migrations, state machine, idempotency, and frontend contracts that block all stories.

### Tests first

- [ ] T013 [P] Add fresh-database and repeat-application tests for migrations 009-017 in `backend/tests/data/test_content_project_migrations.py`
- [ ] T014 [P] Add copied-v4-baseline upgrade tests for migrations 009-017 in `backend/tests/data/test_content_project_upgrade.py`
- [ ] T015 [P] Add exhaustive allowed/blocked transition tests in `backend/tests/services/test_project_state.py`
- [ ] T016 [P] Add idempotency replay/conflict and immutable generic feedback-target tests in `backend/tests/services/test_idempotency.py` and `backend/tests/services/test_feedback_v2.py`
- [ ] T017 [P] Add optimistic concurrency and owner-isolation tests in `backend/tests/services/test_v2_concurrency.py`
- [ ] T018 [P] Add Pydantic contract tests for the stable v2 enums and errors in `backend/tests/models/test_v2_models.py`

### Migrations and common services

- [ ] T019 [P] Add user mode, timezone, weekly goal, onboarding state, and consent migration in `backend/app/data/migrations/009_user_product_mode.sql`
- [ ] T020 [P] Add starter assessment/candidate/sprint migration in `backend/app/data/migrations/010_starter_domain.sql`
- [ ] T021 [P] Add opportunity migration and source-reference indexes in `backend/app/data/migrations/011_opportunities.sql`
- [ ] T022 [P] Add project/state-event/brief/interview migration in `backend/app/data/migrations/012_content_projects.sql`
- [ ] T023 [P] Add material extensions and project-material links in `backend/app/data/migrations/013_materials_v2.sql`
- [ ] T024 [P] Add immutable versions and draft recovery migration in `backend/app/data/migrations/014_content_versions.sql`
- [ ] T025 [P] Add publish checks/records/snapshots/reviews/insights migration in `backend/app/data/migrations/015_publish_review_v2.sql`
- [ ] T026 [P] Add AI trace and generic feedback compatibility migration in `backend/app/data/migrations/016_ai_traces_feedback_v2.sql`
- [ ] T027 [P] Add history-import/imported-note tables plus creator-profile reconciliation in `backend/app/data/migrations/017_creator_profile_v2.sql`
- [ ] T028 [P] Create v2 Pydantic models in `backend/app/models/v2/common.py`, `starter.py`, `opportunity.py`, `content_project.py`, `material.py`, `publish_review.py`, and `ai_trace.py`
- [ ] T029 Implement canonical transition validation and append-only state events in `backend/app/services/project_state.py`
- [ ] T030 [P] Implement owner-scoped idempotency reservation/replay and generic immutable feedback targets in `backend/app/services/idempotency.py` and `backend/app/services/feedback_v2.py`
- [ ] T031 [P] Implement optimistic concurrency helpers and typed `VERSION_CONFLICT` errors in `backend/app/services/concurrency.py` and `backend/app/core/exceptions.py`
- [ ] T032 [P] Implement AITrace persistence plus shared v2 API envelope/error adapters in `backend/app/services/ai_trace.py`, `backend/app/api/v2/deps.py`, and `backend/app/api/v2/errors.py`
- [ ] T033 [P] Add reviewed v2 TypeScript contracts in `frontend/src/types/contracts/v2/index.ts`, `project.ts`, `opportunity.ts`, `starter.ts`, `material.ts`, and `review.ts`
- [ ] T034 [P] Create the v2 Axios services and stable error mapping in `frontend/src/services/api/v2/client.ts` and `frontend/src/services/api/v2/errors.ts`
- [ ] T035 Add an architectural test proving v2 services do not import legacy hotspot sources in `backend/tests/architecture/test_v2_source_boundaries.py`

**Checkpoint**: Migrations apply twice safely; state/concurrency/idempotency contracts are green; frontend can type v2 responses.

## Phase 3: User Story 1 - Resume the next meaningful content task (P1)

**Independent test**: A user with an unfinished project opens Today, reaches the correct next step in <=2 interactions, leaves mid-edit, and is offered recovery on return.

### Tests first

- [ ] T036 [P] [US1] Add Today task-precedence and empty-state service tests in `backend/tests/services/test_today_workspace.py`
- [ ] T037 [P] [US1] Add Today API owner/auth contract tests in `backend/tests/api/v2/test_today.py`
- [ ] T038 [P] [US1] Add navigation, primary-task, and local recovery-offer component tests in `frontend/src/features/today/__tests__/TodayPage.test.tsx`
- [ ] T039 [P] [US1] Add five-node sidebar desktop/mobile tests in `frontend/src/components/layout/__tests__/PrimaryNavigation.test.tsx`

### Implementation

- [ ] T040 [US1] Implement weekly progress and primary-task precedence in `backend/app/services/today_workspace.py`
- [ ] T041 [US1] Expose `GET /api/v2/today` in `backend/app/api/v2/today.py` and register it in `backend/app/api/v2/router.py`
- [ ] T042 [P] [US1] Replace sidebar metadata with `今日｜内容｜机会｜素材｜我的` using MUI icons in `frontend/src/components/layout/Sidebar.tsx`
- [ ] T043 [P] [US1] Add nested route configuration and protected `/today` entry in `frontend/src/app/routes.tsx` and simplify `frontend/src/App.tsx`
- [ ] T044 [US1] Implement Today weekly progress, primary task, secondary tasks, empty/blocked/overdue states in `frontend/src/features/today/TodayPage.tsx`
- [ ] T045 [US1] Add Today API/query state and local recoverable-draft lookup in `frontend/src/services/api/v2/today.ts` and `frontend/src/store/todayStore.ts`

**Checkpoint**: Today is independently demoable using seeded project data.

## Phase 4: User Story 2 - Complete a content project from opportunity to publication (P1)

**Independent test**: One project retains brief, interview evidence, versions, publish check, and a manual publish record through the canonical states.

### Tests first

- [ ] T046 [P] [US2] Add project CRUD, transition, archive, and owner-isolation tests in `backend/tests/services/test_content_project_service.py`
- [ ] T047 [P] [US2] Add brief completeness and evidence-gap tests in `backend/tests/services/test_content_brief_service.py`
- [ ] T048 [P] [US2] Add immutable version, deduplication, lock, and ancestry tests in `backend/tests/services/test_content_version_service.py`
- [ ] T049 [P] [US2] Add interview and local-suggestion AI success/timeout/malformed/missing-model tests in `backend/tests/services/test_interview_service.py` and `backend/tests/services/test_ai_suggestion.py`
- [ ] T050 [P] [US2] Add project/brief/version/baseline-check/manual-publish v2 API contract tests in `backend/tests/api/v2/test_projects.py`
- [ ] T051 [P] [US2] Add project list/detail/state UI tests in `frontend/src/features/projects/__tests__/ProjectFlow.test.tsx`
- [ ] T052 [P] [US2] Add draft recovery and version-conflict store tests in `frontend/src/store/__tests__/projectDraftStore.test.ts`

### Implementation

- [ ] T053 [US2] Implement transactional project CRUD/state/archive in `backend/app/services/content_project.py`
- [ ] T054 [P] [US2] Implement brief revisions and evidence completeness in `backend/app/services/content_brief.py`
- [ ] T055 [P] [US2] Implement interview questions and non-destructive local suggestions with first-party evidence refs in `backend/app/services/interview.py`, `backend/app/services/ai_suggestion.py`, `backend/app/prompts/interview/v1/system.md`, and `backend/app/prompts/local_rewrite/v1/system.md`
- [ ] T056 [P] [US2] Implement immutable versions, hashes, ancestry, baseline deterministic publish check, version locking, and manual publish record in `backend/app/services/content_version.py`, `backend/app/services/publish_check.py`, and `backend/app/services/publish_record.py`
- [ ] T057 [P] [US2] Implement draft-recovery expiry and restore behavior in `backend/app/services/draft_recovery.py`
- [ ] T058 [US2] Expose projects, transitions, brief, interview, suggestions, versions, draft recovery, baseline checks, and manual publish records in `backend/app/api/v2/projects.py`
- [ ] T059 [P] [US2] Add project API clients in `frontend/src/services/api/v2/projects.ts`
- [ ] T060 [P] [US2] Add project list/status filters and empty states in `frontend/src/features/projects/ProjectListPage.tsx`
- [ ] T061 [US2] Build the shared project shell with Brief, Create, baseline Publish, and Review stage navigation in `frontend/src/features/projects/ProjectWorkspacePage.tsx`
- [ ] T062 [P] [US2] Build Brief and interview panels in `frontend/src/features/projects/BriefStage.tsx` and `frontend/src/features/projects/InterviewPanel.tsx`
- [ ] T063 [P] [US2] Build structured title/body/cover/image-plan editor in `frontend/src/features/projects/CreateStage.tsx`
- [ ] T064 [US2] Add suggestion accept/reject, immutable save, comparison, navigation guard, recovery, baseline check, and manual publish action in `frontend/src/features/projects/VersionPanel.tsx`, `frontend/src/features/projects/PublishStage.tsx`, and `frontend/src/store/projectDraftStore.ts`

**Checkpoint**: Core project creation through a locked publish candidate works without starter/profile/opportunity automation.

## Phase 5: User Story 3 - Start from a vague idea and run a three-post experiment (P1)

**Independent test**: A starter completes assessment, receives <=3 grounded directions, selects one, receives three linked projects, publishes at least one, and completes starter review without permanent-niche claims.

### Tests first

- [ ] T065 [P] [US3] Add readiness, max-three-candidate, selection, and sprint lifecycle tests in `backend/tests/services/test_starter_service.py`
- [ ] T066 [P] [US3] Add starter AI evidence/prohibited-claim tests in `backend/tests/services/test_direction_candidate_service.py`
- [ ] T067 [P] [US3] Add starter v2 API tests in `backend/tests/api/v2/test_starter.py`
- [ ] T068 [P] [US3] Add assessment/direction/sprint/review UI tests in `frontend/src/features/starter/__tests__/StarterFlow.test.tsx`

### Implementation

- [ ] T069 [US3] Implement starter assessment and readiness rules in `backend/app/services/starter_assessment.py`
- [ ] T070 [P] [US3] Implement evidence-backed direction candidate generation in `backend/app/services/direction_candidate.py` and `backend/app/prompts/starter_direction/v1/system.md`
- [ ] T071 [US3] Implement sprint creation, three idempotent experiment projects, progress, and graduation in `backend/app/services/starter_sprint.py`
- [ ] T072 [US3] Expose starter assessment, directions, sprint, and review in `backend/app/api/v2/starter.py`
- [ ] T073 [P] [US3] Add starter API client/store in `frontend/src/services/api/v2/starter.ts` and `frontend/src/store/starterStore.ts`
- [ ] T074 [US3] Build assessment, directions, sprint, and review pages in `frontend/src/features/starter/AssessmentPage.tsx`, `DirectionPage.tsx`, `SprintPage.tsx`, and `StarterReviewPage.tsx`

**Checkpoint**: Starter path reaches the shared ContentProject shell and is independently demoable.

## Phase 6: User Story 4 - Build a correctable creator profile from real history (P1)

**Independent test**: Import ten notes with partial failures, correct inferred profile attributes, confirm them, and prove rejected attributes are excluded later.

### Tests first

- [ ] T075 [P] [US4] Add per-item import, retry, deduplication, and 200-item limit tests in `backend/tests/services/test_history_import.py`
- [ ] T076 [P] [US4] Add profile evidence/confirmation/rejection tests in `backend/tests/services/test_creator_profile_v2.py`
- [ ] T077 [P] [US4] Add mode-selection/import/profile API tests in `backend/tests/api/v2/test_growth_onboarding.py`
- [ ] T078 [P] [US4] Add mixed-result import and profile-review UI tests in `frontend/src/features/onboarding/__tests__/GrowthOnboarding.test.tsx`

### Implementation

- [ ] T079 [US4] Implement product-mode selection plus manual/CSV/JSON history import and result persistence in `backend/app/services/onboarding_mode.py` and `backend/app/services/history_import.py`
- [ ] T080 [US4] Reconcile profile inference, evidence, corrections, and confirmation in `backend/app/services/creator_profile_v2.py` and `backend/app/prompts/creator_profile/v2/system.md`
- [ ] T081 [US4] Expose mode selection, history import, and creator profile endpoints in `backend/app/api/v2/onboarding.py`
- [ ] T082 [P] [US4] Add mode/import/profile clients in `frontend/src/services/api/v2/onboarding.ts`
- [ ] T083 [US4] Build mode selection, history import, result review, and profile confirmation in `frontend/src/features/onboarding/ModePage.tsx`, `HistoryImportPage.tsx`, and `ProfileReviewPage.tsx`

**Checkpoint**: Growth onboarding reaches Today with a confirmed or explicitly provisional profile.

## Phase 7: User Story 5 - Choose explainable opportunities without fake precision (P2)

**Independent test**: Generate source-backed opportunities, inspect qualitative dimensions, reject one, adopt one, and prove no legacy hotspot source or predictive field is used.

### Tests first

- [ ] T084 [P] [US5] Add first-party source eligibility, ordering, expiry, and empty-result tests in `backend/tests/services/test_opportunity_service.py`
- [ ] T085 [P] [US5] Add manual keyword/URL/official-inspiration verification tests in `backend/tests/services/test_manual_opportunity.py`
- [ ] T086 [P] [US5] Add prohibited-field and no-legacy-import tests in `backend/tests/architecture/test_opportunity_integrity.py`
- [ ] T087 [P] [US5] Add opportunity list/create/decision API tests in `backend/tests/api/v2/test_opportunities.py`
- [ ] T088 [P] [US5] Add dimension/source/decision UI tests in `frontend/src/features/opportunities/__tests__/OpportunityPages.test.tsx`

### Implementation

- [ ] T089 [US5] Implement opportunity derivation from history, questions, materials, series, evergreen needs, and confirmed insights in `backend/app/services/opportunity.py`
- [ ] T090 [P] [US5] Implement manual hotspot intake with pending/insufficient verification and expiry in `backend/app/services/manual_opportunity.py`
- [ ] T091 [US5] Implement immutable adopt/save/reject decisions and adopted-project idempotency in `backend/app/services/opportunity_decision.py`
- [ ] T092 [US5] Expose opportunity list/generate/manual/decision endpoints in `backend/app/api/v2/opportunities.py`
- [ ] T093 [P] [US5] Add v2 opportunity client in `frontend/src/services/api/v2/opportunities.ts`
- [ ] T094 [US5] Build opportunity list, filters, evidence drawer, manual intake, and decision controls in `frontend/src/features/opportunities/OpportunityListPage.tsx` and `OpportunityDetailPage.tsx`

**Checkpoint**: Opportunity adoption creates one shared project with evidence and no fake score.

## Phase 8: User Story 6 - Publish with transparent assistance and manual control (P2)

**Independent test**: Select a version, run version-bound checks, resolve findings, export, record publication twice with one logical result, and observe stale checks after content changes.

### Tests first

- [ ] T095 [P] [US6] Add version-bound risk, finding-location, provenance, stale, and no-model tests in `backend/tests/services/test_publish_check_v2.py`
- [ ] T096 [P] [US6] Add publish-record lock/idempotency/correction tests in `backend/tests/services/test_publish_record.py`
- [ ] T097 [P] [US6] Add partial export retry tests in `frontend/src/features/projects/__tests__/PublishExport.test.tsx`
- [ ] T098 [P] [US6] Add publish-check/publish-record API tests in `backend/tests/api/v2/test_publish.py`
- [ ] T099 [P] [US6] Add publish-stage responsive and stale-state UI tests in `frontend/src/features/projects/__tests__/PublishStage.test.tsx`

### Implementation

- [ ] T100 [US6] Adapt deterministic and optional AI risk checks to content versions in `backend/app/services/publish_check.py` and version `backend/app/prompts/content_risk/v2/system.md`
- [ ] T101 [US6] Implement version locking and immutable manual publication in `backend/app/services/publish_record.py`
- [ ] T102 [US6] Expose publish checks, resolutions, and publish records in `backend/app/api/v2/publish.py`
- [ ] T103 [P] [US6] Add publish v2 client in `frontend/src/services/api/v2/publish.ts`
- [ ] T104 [US6] Build check findings, acknowledgement, copy text, image export, and publication form in `frontend/src/features/projects/PublishStage.tsx`
- [ ] T105 [US6] Add per-artifact export retry and completion state in `frontend/src/features/projects/exportContent.ts`

**Checkpoint**: A real manual publication can be recorded with an auditable locked version.

## Phase 9: User Story 7 - Record performance and turn review into one next experiment (P2)

**Independent test**: Add manual 24h/72h snapshots, optionally extract unconfirmed screenshot values, complete a fact/hypothesis review, and confirm exactly one insight while rejecting another.

### Tests first

- [ ] T106 [P] [US7] Add append-only snapshot, correction, null-metric, and idempotency tests in `backend/tests/services/test_performance_snapshot.py`
- [ ] T107 [P] [US7] Add screenshot extraction success/missing-vision/malformed/unconfirmed tests in `backend/tests/services/test_snapshot_extraction.py`
- [ ] T108 [P] [US7] Add review separation, exact-three-actions, revision, and confirmed-insight tests in `backend/tests/services/test_review_v2.py`
- [ ] T109 [P] [US7] Add snapshot/review/insight API tests in `backend/tests/api/v2/test_reviews.py`
- [ ] T110 [P] [US7] Add metric confirmation and fact/hypothesis/experiment UI tests in `frontend/src/features/review/__tests__/ReviewFlow.test.tsx`

### Implementation

- [x] T111 [US7] Implement manual and superseding snapshots in `backend/app/services/performance_snapshot.py`
- [ ] T112 [P] [US7] Implement optional vision extraction as unconfirmed proposals in `backend/app/services/snapshot_extraction.py` and `backend/app/prompts/snapshot_extract/v1/system.md`
- [ ] T113 [US7] Replace prediction logic with facts, hypotheses, three actions, revisions, and proposed insights in `backend/app/services/review_v2.py` and `backend/app/prompts/review/v2/system.md`
- [ ] T114 [US7] Implement confirmed/rejected/retired insight decisions and context filtering in `backend/app/services/learned_insight.py`
- [ ] T115 [US7] Expose snapshots, extraction, review, and insight decisions in `backend/app/api/v2/reviews.py`
- [ ] T116 [P] [US7] Add review v2 client in `frontend/src/services/api/v2/reviews.ts`
- [ ] T117 [US7] Build metric entry/screenshot confirmation and review stages in `frontend/src/features/review/PerformancePanel.tsx` and `frontend/src/features/review/ReviewStage.tsx`

**Checkpoint**: Published projects reach `settled`; only confirmed insights affect later context.

## Phase 10: User Story 8 - Manage materials and settings without a separate asset system (P3)

**Independent test**: Create/reuse a material, inspect usages, protect locked references, update weekly goal, view AI capability status, export data, and request deletion.

### Tests first

- [ ] T118 [P] [US8] Add text/link/file material, privacy, usage, and locked-reference deletion tests in `backend/tests/services/test_material_v2.py`
- [ ] T119 [P] [US8] Add weekly-goal/account-reference settings plus export/deletion, credential-revocation, and stored-file cleanup tests in `backend/tests/services/test_account_data_jobs.py`
- [ ] T120 [P] [US8] Add material/settings/account-data v2 API and owner-isolation tests in `backend/tests/api/v2/test_materials_account.py`
- [ ] T121 [P] [US8] Add Materials/My UI tests in `frontend/src/features/materials/__tests__/MaterialsPage.test.tsx` and `frontend/src/features/me/__tests__/MePage.test.tsx`

### Implementation

- [ ] T122 [US8] Adapt existing asset/storage service to Material kinds, privacy, project links, and reference snapshots in `backend/app/services/material_v2.py`
- [ ] T123 [US8] Implement weekly-goal/Xiaohongshu-reference settings plus personal-data export and deletion jobs in `backend/app/services/user_settings.py`, `backend/app/services/account_data.py`, and `backend/app/tasks/account_data.py`
- [ ] T124 [US8] Expose Materials, settings, AI-capability status, and account export/deletion endpoints in `backend/app/api/v2/materials.py`, `backend/app/api/v2/settings.py`, and `backend/app/api/v2/account_data.py`
- [ ] T125 [P] [US8] Add Materials/My v2 clients in `frontend/src/services/api/v2/materials.ts` and `frontend/src/services/api/v2/account.ts`
- [ ] T126 [US8] Build lightweight Materials list/project drawer/usage dialog in `frontend/src/features/materials/MaterialsPage.tsx` and `frontend/src/features/projects/MaterialDrawer.tsx`
- [ ] T127 [US8] Build My strategy, weekly goal, Xiaohongshu reference, AI capability status, privacy/export/deletion, and sign-out in `frontend/src/features/me/MePage.tsx`

**Checkpoint**: Supporting material and account controls work without a complex DAM or platform OAuth.

## Phase 11: Compatibility, Polish, and Release Validation

**Goal**: Retire old primary workflows safely, synchronize documentation/contracts, and prove the local Docker MVP.

### Legacy compatibility

- [ ] T128 [P] Add frontend redirect tests for all legacy paths in `frontend/src/__tests__/legacyRoutes.test.tsx`
- [ ] T129 [P] Add typed v1 deprecation-shim tests in `backend/tests/api/test_legacy_deprecation.py`
- [ ] T130 Implement legacy frontend redirects in `frontend/src/app/routes.tsx` per `plan.md`
- [ ] T131 Implement v1 business endpoint deprecation responses without new legacy writes in `backend/app/api/v1/topics.py`, `ideas.py`, `titles.py`, `viral.py`, `publish.py`, and `reviews.py`
- [ ] T132 Remove team/account-matrix entries from active navigation and build reachability in `frontend/src/components/layout/Sidebar.tsx` and `frontend/src/app/routes.tsx`

### Cross-cutting validation

- [ ] T133 [P] Add full growth loop integration test in `backend/tests/integration/test_content_project_growth_loop.py`
- [ ] T134 [P] Add full starter loop integration test in `backend/tests/integration/test_content_project_starter_loop.py`
- [ ] T135 [P] Add manual/no-model Playwright journey in `frontend/e2e/content-project-manual.spec.ts`
- [ ] T136 [P] Add growth Playwright journey in `frontend/e2e/content-project-growth.spec.ts`
- [ ] T137 [P] Add starter Playwright journey in `frontend/e2e/content-project-starter.spec.ts`
- [ ] T138 [P] Add draft recovery/version conflict Playwright journey in `frontend/e2e/content-project-recovery.spec.ts`
- [ ] T139 [P] Add desktop/mobile visual and overlap checks in `frontend/e2e/content-project-responsive.spec.ts`
- [ ] T140 [P] Add prohibited source/field scan to `scripts/check-v2-source-integrity.ps1`
- [ ] T141 [P] Add UTF-8/mojibake scan to `scripts/check-utf8.ps1`
- [ ] T142 Synchronize generated OpenAPI, v2 TypeScript contracts, and `specs/008-content-project-mvp/contracts/api-v2.md` in `backend/openapi3.json`
- [ ] T143 Update `README.md`, `backend/README.md`, and `frontend/README.md` to the implemented five-node MVP and generic model config
- [ ] T144 Update `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, and health checks for fresh-volume runtime
- [ ] T145 Run backend pytest/ruff/mypy/bandit and enforce >=80% coverage from `backend/pyproject.toml`
- [ ] T146 Run frontend Vitest coverage/lint/build/npm audit and all Playwright suites from `frontend/`
- [ ] T147 Execute [quickstart.md](./quickstart.md) against fresh Docker volumes, restart services, and record results in `specs/008-content-project-mvp/release-validation.md`
- [ ] T148 Run SpecKit cross-artifact analysis and resolve every CRITICAL/HIGH inconsistency before implementation is declared complete in `specs/008-content-project-mvp/`

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

- Total tasks: 148.
- Setup/foundational tasks: 35.
- US1: 10 tasks.
- US2: 19 tasks.
- US3: 10 tasks.
- US4: 9 tasks.
- US5: 11 tasks.
- US6: 11 tasks.
- US7: 12 tasks.
- US8: 10 tasks.
- Compatibility/release: 21 tasks.
- Every task includes a checkbox, sequential ID, story label where required, concrete action, and file path.



