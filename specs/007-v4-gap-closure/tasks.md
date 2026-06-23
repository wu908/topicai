# Tasks: 007 TopicAI v4.1 Implementation-Gap Closure

**Input**: Design documents from `/specs/007-v4-gap-closure/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are INCLUDED per Constitution Principle II (test-first discipline) and spec requirements FR-013, SC-007.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, ...)
- Include exact file paths in descriptions

## Path Conventions

- Backend: `backend/app/`, `backend/tests/`, `backend/prompts/`
- Frontend: `frontend/src/`, `frontend/src/services/api/`
- Migrations: `backend/app/data/migrations/NNN_<topic>.sql`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Lock the gates, the migration runner, the prompt directory, and the shared fixtures before any user story begins.

- [x] T001 Add `pytest --cov=app --cov-fail-under=80` to `backend/pyproject.toml` and document in `backend/README`
- [x] T002 [P] Add Vitest coverage threshold (>=80%) in `frontend/vitest.config.ts`
- [x] T003 [P] Create `backend/app/data/migrations/runner.py` with idempotent `apply()` + `schema_migrations` tracking (Quality Gate 8, FR-012)
- [x] T004 [P] Wire migration runner into `backend/main.py` lifespan startup (Quality Gate 8, FR-012)
- [x] T005 [P] Create `backend/app/data/migrations/001_bootstrap.sql` with `CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL, checksum TEXT NOT NULL)` (FR-012)
- [x] T006 [P] Create prompt files at `backend/prompts/idea_boost.v1.md`, `title_optimize.v1.md`, `track_diagnose.v1.md`, `publish_suggest.v1.md`, `onboarding_rubric.v1.md`, `risk_check.v1.md`
- [x] T007 [P] Pin 5 fixture responses for `_clean_json_response` regression in `backend/tests/core/test_llm.py` (canonical mock pattern, Constitution Principle II)
- [x] T008 [P] Verify `LLMClient.generate` end-to-end with a 1-request ping test in `backend/tests/core/test_llm.py`; record expected `model_version` per provider
- [x] T009 [P] Extend `config/data_source_config.py` with per-tier `TierConfig` dataclass (timeout=3s, retry=1, circuit_breaker=3 fails / 30s half-open) (US2, FR-004)
- [x] T010 [P] Create `backend/app/data/seed/risk_keywords.json` with 100 entries across 5 categories (regulatory, sensitive, medical, financial, false-advertising)

**Checkpoint**: CI gate enforced, migrations wired, prompts staged, fixtures pinned. No business-logic change yet.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: New tables that all user stories depend on. Phase 2 must complete before Phase 3+.

**CRITICAL**: No user story work can begin until this phase is complete.

- [x] T011 [P] Create `backend/app/data/migrations/002_user_feedback.sql` (`id`, `user_id`, `source_type`, `source_id`, `feedback_type`, `feedback_value`, `reason`, `created_at`; idx `(user_id, created_at DESC)`) (US3, FR-005)
- [x] T012 [P] Create `backend/app/data/migrations/003_effect_reviews.sql` (`id`, `user_id`, `topic_title`, `content_outline`, `prediction` JSON, `actual_result` JSON, `attribution` JSON, `learnings` JSON, `status`, `created_at`, `updated_at`) (US4, FR-007)
- [x] T013 [P] Create `backend/app/data/migrations/004_risk_keywords.sql` (`id`, `user_id` NULL for global, `keyword`, `severity`, `category`, `created_at`; unique on `(user_id, keyword)`) (US5, FR-008)
- [x] T014 [P] Create `backend/app/data/migrations/005_platform_tokens.sql` (foundation only; full OAuth adapter deferred) (prep for future)
- [x] T015 [P] Add Pydantic models in `backend/app/models/effect_review.py` for `PredictionPayload`, `DimensionalConclusion`, `AttributionPayload`, `LearningsPayload` (US4, FR-007)
- [x] T016 [P] Add `FeedbackRecord` Pydantic model in `backend/app/models/feedback.py` (US3, FR-005)

**Checkpoint**: Tables exist; Pydantic models importable; the migration runner can apply 001-005 in order.

---

## Phase 3: User Story 1 - Real LLM coach for idea / title / track / publish (Priority: P1, MVP)

**Goal**: `idea_boost`, `title_optimize`, `track_diagnose`, `publish_advisor` invoke the LLM and return full Pydantic schemas; the existing heuristic outputs become the `template_fallback` path.

**Independent Test**: With `DEEPSEEK_API_KEY` set, the four endpoints return `data_source="llm_simulation"` and `confidence >= 0.6`. Without a key, the same endpoints return 200 with `data_source="template_fallback"`, `confidence <= 0.5`.

### Tests for User Story 1 (write FIRST; ensure they FAIL before implementation)

- [x] T017 [P] [US1] Mock-pattern test in `backend/tests/services/test_idea_booster.py::test_llm_path_returns_structured` -- patch `LLMClient.generate` to return valid JSON; assert `data_source="llm_simulation"`, `model_version` set, `confidence >= 0.6`
- [x] T018 [P] [US1] Fallback test in `backend/tests/services/test_idea_booster.py::test_fallback_returns_schema_with_low_confidence` -- patch `LLMClient.generate` to raise; assert `data_source="template_fallback"`, `confidence <= 0.5`
- [x] T019 [P] [US1] Truncation test in `backend/tests/services/test_idea_booster.py::test_oversized_input_truncated_to_5000` -- pass 6000-char input; assert only 5000 chars hit the LLM
- [x] T020 [P] [US1] Malformed-JSON test in `backend/tests/services/test_idea_booster.py::test_malformed_json_recovers` -- patch `LLMClient.generate` to return malformed text; assert `_clean_json_response` recovers or fallback fires
- [x] T021 [P] [US1] Mock-pattern test in `backend/tests/services/test_title_optimizer.py::test_llm_path_returns_3_to_5_variations` -- assert 3-5 variations, each with `ctr_estimate`, `technique_used`, `technique_reason`
- [x] T022 [P] [US1] Fallback test in `backend/tests/services/test_title_optimizer.py::test_fallback_returns_schema_with_low_confidence`
- [x] T023 [P] [US1] Mock-pattern test in `backend/tests/services/test_track_diagnosis.py::test_llm_path_returns_structured` -- assert `health_score`, `competitiveness_score`, `sub_tracks` (3+), `direction_advice` populated
- [x] T024 [P] [US1] Fallback test in `backend/tests/services/test_track_diagnosis.py::test_fallback_returns_schema_with_low_confidence`
- [x] T025 [P] [US1] Mock-pattern test in `backend/tests/services/test_publish_advisor.py::test_llm_path_returns_structured` -- assert 3 `suggested_times` with `time_range`, `reason`, `benchmark_source`
- [x] T026 [P] [US1] Fallback test in `backend/tests/services/test_publish_advisor.py::test_fallback_returns_schema_with_low_confidence`

### Implementation for User Story 1

- [x] T027 [US1] Add `_analyze_with_llm()` + `_template_xxx()` to `backend/app/services/idea_booster.py`; rewrite `boost()` to delegate; LLM path returns `data_source="llm_simulation"`, fallback returns `data_source="template_fallback"` (FR-001)
- [x] T028 [US1] Wire `LLMClient.generate()` + `_clean_json_response` into `idea_booster`; default to template when `confidence < 0.5` or LLM raises
- [x] T029 [US1] Apply the same `_analyze_with_llm()` + `_template_xxx()` pattern to `backend/app/services/title_optimizer.py` (FR-001)
- [x] T030 [US1] Apply the same pattern to `backend/app/services/track_diagnosis.py` (FR-001)
- [x] T031 [US1] Apply the same pattern to `backend/app/services/publish_advisor.py` (FR-001)
- [x] T032 [US1] Confirm the four endpoints return 200 with `confidence`, `data_source`, `model_version` populated (FR-013)
- [x] T033 [US1] Update the `AICreatedBadge` use in `frontend/src/pages/{IdeaBooster,TitleOptimizer,TrackDiagnosis,PublishAdvisor}/` to render `modelVersion` for the LLM path and `AIDegradedNotice` for the fallback path

**Checkpoint**: US1 fully functional and testable independently.

---

## Phase 4: User Story 2 - 4-tier data source actually drives topic recommendations (Priority: P1)

**Goal**: `TopicRecommendService.recommend()` consults `DataManager.get_trending_topics()` and returns tier-tagged topics with HTTP 200 even when all live tiers fail.

**Independent Test**: With all live tiers stubbed to fail, `POST /api/v1/topics/recommend` returns 200 with `data_source="preloaded"`, `confidence <= 0.5`, 5+ topics. With `TIANAPI_KEY` enabled, `data_source="tianapi"`, `confidence >= 0.6`.

### Tests for User Story 2

- [x] T034 [P] [US2] Test in `backend/tests/services/test_topic_recommend.py::test_preloaded_safety_net_returns_5_topics` -- stub all tiers to fail; assert preloaded tier returns 5 topics, `data_source="preloaded"`, `confidence <= 0.5`
- [x] T035 [P] [US2] Test in `backend/tests/services/test_topic_recommend.py::test_tianapi_tier_returns_tianapi_data_source` -- stub `TianAPISource` to return mock; assert `data_source="tianapi"`, `confidence >= 0.6`
- [x] T036 [P] [US2] Test in `backend/tests/services/test_topic_recommend.py::test_all_live_tiers_fail_falls_through_to_preloaded`
- [x] T037 [P] [US2] Test in `backend/tests/services/test_topic_recommend.py::test_tier_shift_emits_warning_log` -- use `caplog`; assert `logger.warning("tier_shift", extra=...)` is emitted
- [x] T038 [P] [US2] Integration test in `backend/tests/integration/test_data_manager_cascade.py` stubbing each tier to fail in turn

### Implementation for User Story 2

- [x] T039 [US2] Extend `TianAPISource` in `backend/app/data_sources/tianapi_source.py` -- real httpx call already exists, gated on `TIANAPI_KEY`; wire per-tier config from FR-004
- [x] T040 [P] [US2] Extend `BilibiliSource` in `backend/app/data_sources/bilibili_source.py` -- real httpx call already exists; wire per-tier config
- [x] T041 [P] [US2] REWRITE `LLMDataSource` in `backend/app/data_sources/llm_source.py` to actually call `LLMClient.generate` (replace the `_generate_mock_topics` shim at l103)
- [x] T042 [US2] Seed `PreloadedDataSource` in `backend/app/data_sources/preloaded_source.py` with 8 tracks (科技, 时�?, 美食, 职场, 教育, 财经, 游戏, 娱乐) -- currently 5; expand to 8 (FR-003)
- [x] T043 [US2] Refactor `TopicRecommendService.recommend()` in `backend/app/services/topic_recommend.py` to delegate to `DataManager.get_trending_topics()` and rank by `rubric_weights` (FR-003)
- [x] T044 [US2] Ensure the response carries `data_source`, `confidence`, and `model_version` (FR-013)
- [x] T045 [US2] Add `tier_shift` structured log in `DataManager._try_tier()` per FR-004
- [x] T046 [US2] Add `GET /api/v1/topics/history` endpoint in `backend/app/api/v1/topics.py` (US7, FR-011)

**Checkpoint**: US2 fully functional and testable independently; US1+US2 together form the MVP slice.

---

## Phase 5: User Story 3 - Feedback loop actually persists and adapts the creator profile (Priority: P2)

**Goal**: `FeedbackService.submit` persists feedback to `user_feedback` and triggers the creator profile update pipeline. Cold-start window respected.

**Independent Test**: 5 thumb-down events on a single dimension move `creator_profiles.rubric_weights` in the DB within 5 seconds; cold-start accounts (< 7 days OR < 5 events) keep default weights.

### Tests for User Story 3

- [x] T047 [P] [US3] Test in `backend/tests/api/test_feedback_router.py::test_submit_persists_row` -- POST `/api/v1/feedback`; assert row in `user_feedback` table; response 202 with persisted id
- [x] T048 [P] [US3] Test in `backend/tests/api/test_feedback_router.py::test_five_thumb_downs_update_rubric_weights` -- submit 5 thumb-downs; assert `creator_profiles.rubric_weights` decreased for the targeted dimension; bounded by `0.15`
- [x] T049 [P] [US3] Test in `backend/tests/services/test_feedback.py::test_cold_start_keeps_default_weights` -- new account (< 7 days, 0 events); submit feedback; assert `rubric_weights` unchanged
- [x] T050 [P] [US3] Test in `backend/tests/services/test_feedback.py::test_bounded_shift_per_dimension` -- established account; submit 10 thumb-downs; assert total shift <= 0.15
- [x] T051 [P] [US3] Test in `backend/tests/services/test_feedback.py::test_rolling_window_excludes_30d_old` -- backdate a feedback record to 31 days ago; assert `adjust_weights` excludes it
- [x] T052 [P] [US3] Test in `backend/tests/api/test_feedback_router.py::test_get_history_returns_paginated_records` -- `GET /api/v1/feedback/history` (US7, FR-011)

### Implementation for User Story 3

- [x] T053 [US3] Refactor `FeedbackService.submit` in `backend/app/services/feedback.py` to persist via injected `Database`; return 202 with persisted id (FR-005)
- [x] T054 [US3] Add `FeedbackService._maybe_update_profile(user_id)` enforcing cold-start grace (7d OR <5 events) and bounded shift (0.15) (FR-006)
- [x] T055 [US3] Add 30-day rolling-window filter inside `adjust_weights` (FR-006)
- [x] T056 [US3] Convert `submit` endpoint in `backend/app/api/v1/feedback.py` to `async`; return 202; remove the `analyze_feedback(user_id, [])` call from `get_feedback_analysis`
- [x] T057 [US3] Add `GET /api/v1/feedback/history` endpoint in `backend/app/api/v1/feedback.py` (US7, FR-011)

**Checkpoint**: US3 fully functional and testable independently; feedback-driven personalization now closes the loop with US2.

---

## Phase 6: User Story 4 - Effect review lifecycle is persistent and LLM-driven (Priority: P2)

**Goal**: `predict` -> `attribute` -> `derive_learnings` with persistence and 3-5 dimensional conclusions.

**Independent Test**: After `POST /api/v1/reviews/predict` and `POST /api/v1/reviews/{review_id}/attribute`, the data is in the `effect_reviews` table; `GET /api/v1/reviews/learnings` returns a non-empty report after >= 1 attribution. Restarting the server does not lose the prediction.

### Tests for User Story 4

- [x] T058 [P] [US4] Test in `backend/tests/chains/test_effect_review_chain.py::test_predict_returns_predicted_payload` -- patch `LLMClient.generate_structured`; assert the 4 numeric fields and `caveat` are populated
- [x] T059 [P] [US4] Test in `backend/tests/chains/test_effect_review_chain.py::test_attribute_returns_3_to_5_dimensional_conclusions`
- [x] T060 [P] [US4] Test in `backend/tests/services/test_effect_review.py::test_derive_learnings_aggregates_last_30_days`
- [x] T061 [P] [US4] Test in `backend/tests/services/test_effect_review.py::test_persistence_survives_restart` -- write a prediction; simulate restart (new `EffectReviewService` instance); assert the prediction is still retrievable by id
- [x] T062 [P] [US4] Test in `backend/tests/api/test_reviews_router.py::test_predict_endpoint_returns_schema` -- 201, schema matches `PredictionPayload`
- [x] T063 [P] [US4] Test in `backend/tests/api/test_reviews_router.py::test_attribute_endpoint_persists_conclusions` -- `actual_result` and `attribution` JSON written to the table

### Implementation for User Story 4

- [x] T064 [US4] Rewrite `EffectReviewChain` in `backend/app/chains/effect_review_chain.py` -- three methods: `predict(topic, outline)`, `attribute(prediction, actual)`, `derive_learnings(user_id)`, all calling `LLMClient.generate` or `generate_structured` (FR-007)
- [x] T065 [US4] REWRITE `EffectReviewService` in `backend/app/services/effect_review.py` -- persistence + chain wrapping + caching `learnings` for 1h; replace `self._predictions` with DB queries
- [x] T066 [US4] Add 4 endpoints to `backend/app/api/v1/reviews.py`: predict, attribute, learnings, list (with `?status=` filter) (FR-007, FR-011)
- [x] T067 [US4] Expand `frontend/src/pages/EffectReview/EffectReviewPage.tsx` to render the `/learnings` card and the `?status=awaiting` list
- [x] T068 [US4] Add API client at `frontend/src/services/api/reviews.ts` with 4 methods

**Checkpoint**: US4 fully functional and testable independently; the creator can now learn from their own history.

---

## Phase 7: User Story 5 - Content risk pre-publish guard with hybrid scoring (Priority: P3)

**Goal**: `POST /api/v1/risk/check` runs the hybrid keyword + LLM scan and blocks high-severity items from automated publish.

**Independent Test**: Risky text ("guaranteed no loss", "100% cure") gets flagged with `severity="high"`; benign text gets `risks: []`; LLM failure falls back to keyword-only.

### Tests for User Story 5

- [x] T069 [P] [US5] Test in `backend/tests/services/test_content_risk.py::test_financial_inducement_flagged_high` -- "guaranteed no loss" -> `severity="high"`, `category="financial_inducement"`
- [x] T070 [P] [US5] Test in `backend/tests/services/test_content_risk.py::test_medical_overclaim_flagged_high` -- "100% cure" -> `severity="high"`, `category="medical_overclaim"`
- [x] T071 [P] [US5] Test in `backend/tests/services/test_content_risk.py::test_benign_content_passes_with_empty_risks` -- `risks: []`, `overall_risk_score < 0.2`
- [x] T072 [P] [US5] Test in `backend/tests/services/test_content_risk.py::test_keyword_only_when_llm_unavailable` -- patch `LLMClient.generate` to raise; assert keyword path runs alone, `data_source="template_fallback"`, `confidence <= 0.5`
- [x] T073 [P] [US5] Test in `backend/tests/api/test_risk_router.py::test_risk_check_endpoint_returns_report`

### Implementation for User Story 5

- [x] T074 [US5] Create `backend/app/api/v1/risk_router.py` with `POST /api/v1/risk/check` (reuse existing `RiskCheckRequest` / `ContentRiskReport` from `backend/app/models/risk.py`) (FR-008)
- [x] T075 [US5] REWRITE `ContentRiskService` in `backend/app/services/content_risk.py` -- add LLM layer, keep keyword layer, blend 80/20 per Constitution Principle XI
- [x] T076 [US5] Mount risk router in `backend/app/api/v1/router.py`
- [x] T077 [US5] Add blocking badge to publish flow in `frontend/src/pages/PublishAdvisor/PublishAdvisorPage.tsx` -- consult `/risk/check` before submit
- [x] T078 [US5] Add `frontend/src/services/api/risk.ts` client

**Checkpoint**: US5 fully functional and testable independently; the lowest-effort, highest-stakes safeguard is online.

---

## Phase 8: User Story 6 - Onboarding LLM-driven rubric_weights (Priority: P3)

**Goal**: Onboarding derives `rubric_weights` from the user''s answers via the LLM rather than 7 equal defaults.

**Independent Test**: With a key, the LLM-derived `rubric_weights` reflect the priority (a "deep / evergreen" answer yields `content_depth_match > hotspot_relevance`); without a key, the fallback returns the existing defaults.

### Tests for User Story 6

- [x] T079 [P] [US6] Test in `backend/tests/services/test_onboarding.py::test_llm_path_returns_derived_weights` -- patch `LLMClient.generate_structured`; assert weights reflect the input
- [x] T080 [P] [US6] Test in `backend/tests/services/test_onboarding.py::test_llm_failure_returns_fallback` -- patch LLM to raise; assert fallback fires and `data_source="template_fallback"`
- [x] T081 [P] [US6] Test in `backend/tests/services/test_onboarding.py::test_weights_sum_to_one` -- assert `sum(rubric_weights.values()) == 1.0` within 1e-6

### Implementation for User Story 6

- [x] T082 [US6] REWRITE `_build_profile_with_llm` in `backend/app/services/onboarding.py` to use `LLMClient.generate_structured(schema=CreatorProfile, ...)` (FR-009)
- [x] T083 [US6] Confirm `_build_profile_fallback` path is preserved (existing behavior must match when no key) (FR-009)

**Checkpoint**: US6 fully functional and testable independently; new users get personalized weights from day 0.

---

## Phase 9: User Story 7 - Coverage gate and missing API endpoints wired (Priority: P2)

**Goal**: Lock the 80% coverage gate in CI; add the 7 endpoints the frontend already calls.

**Independent Test**: `pytest --cov=app --cov-fail-under=80` and `pnpm vitest run --coverage` both pass on the protected branch. Every frontend service method has a real handler.

### Tests for User Story 7

- [x] T084 [P] [US7] CI-config test asserting `backend/pyproject.toml` contains `cov-fail-under = 80`
- [x] T085 [P] [US7] CI-config test asserting `frontend/vitest.config.ts` has `coverage.thresholds.lines >= 80`
- [x] T086 [P] [US7] E2E test in `frontend/e2e/full-loop.spec.ts`: login -> topics -> feedback x5 -> weight change -> effect review predict -> attribute -> learnings card visible

### Implementation for User Story 7

- [x] T087 [US7] Confirm the 5 endpoint additions from T046 (topics/history), T057 (feedback/history), T066 (reviews/learnings, reviews/list), T074 (risk/check) are all in `backend/app/api/v1/router.py`
- [x] T088 [US7] Add `frontend/e2e/full-loop.spec.ts` covering the full flow
- [x] T089 [US7] Verify `pytest --cov=app --cov-fail-under=80` and `pnpm vitest run --coverage` both green on a fresh branch (this is the release gate)

**Checkpoint**: All 7 missing endpoints exist; coverage gate enforced.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [x] T090 [P] Add `ConfidenceBadge` + `AICreatedBadge` audit to the four coach outputs in `frontend/src/components/ai-badge/AICreatedBadge.tsx` (FR-013, Principle III)
- [x] T091 [P] Update `frontend/src/services/api/feedback.ts` to use the async `submit` endpoint (T056) and the `history` endpoint (T057)
- [x] T092 [P] Update `frontend/src/services/api/topics.ts` to surface `data_source` and `confidence` in the recommendations UI
- [x] T093 [P] Add integration test `backend/tests/integration/test_full_loop.py` covering: login -> topics -> feedback -> weight change -> effect-review
- [x] T094 [P] Verify `backend/app/data/seed/risk_keywords.json` has 100 entries; verify each category has >= 15 examples
- [x] T095 [P] Update `README.md` so the "Features" table matches runtime behavior post-roadmap
- [x] T096 [P] Sync `openapi3.json` with the new endpoints under `/api/v1/`
- [x] T097 [P] Final constitution-sync audit: open `AGENTS.md` SPECKIT block, re-run checklist, confirm Sync Impact Report mentions all 7 new principles (none added in 007; confirm 006''s additions still cover the surface)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies -- can start immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1 completion -- BLOCKS all user stories.
- **Phase 3 (US1)**: Depends on Phase 2 -- can run as soon as Phase 2 finishes.
- **Phase 4 (US2)**: Depends on Phase 2 -- can run in parallel with Phase 3.
- **Phase 5 (US3)**: Depends on Phase 2 + Phase 4 (US2 must be live to surface weight-driven recs).
- **Phase 6 (US4)**: Depends on Phase 2 only -- can run in parallel with US3 after Phase 2.
- **Phase 7 (US5)**: Depends on Phase 1 + Phase 2 only -- can run in parallel with US1-US4.
- **Phase 8 (US6)**: Depends on Phase 2 + Phase 3 (US1 LLMClient must be exercised first).
- **Phase 9 (US7)**: Depends on all desired user stories being complete (it is the gate).
- **Phase 10 (Polish)**: Depends on all desired user stories being complete.

### Within Each User Story

- Tests MUST be written and FAIL before implementation (Constitution Principle II)
- Prompts before chains; chains before services; services before endpoints
- DB migration before the service that depends on the table
- Core implementation before integration; story complete before the next priority

### Parallel Opportunities

- Phase 1 setup tasks marked `[P]` can run in parallel
- Phase 2 foundational tasks marked `[P]` can run in parallel
- US1, US2, US5, US6 can be staffed in parallel after Phase 2
- Within each story, all `[P]` test tasks can run in parallel
- All Polish tasks marked `[P]` can run in parallel

---

## Implementation Strategy

### MVP First (US1 + US2 + US7)

1. Complete Phase 1: Setup (coverage gate + runner + fixtures + prompts)
2. Complete Phase 2: Foundational (migrations 002-005 + Pydantic models)
3. Complete Phase 3: US1 (real LLM coaches)
4. Complete Phase 4: US2 (4-tier data source)
5. **STOP and VALIDATE**: Run SC-001 (no fake-AI data_source), SC-002 (pytest path filter), SC-005 (coverage gate), SC-007 (test count per service)
6. Tag a release candidate

### Incremental Delivery

1. Setup + Foundational -> Foundation ready
2. Add US1 -> test independently -> demo (MVP!)
3. Add US2 -> test independently -> demo
4. Add US3 -> test independently -> demo (personalization live)
5. Add US4 -> test independently -> demo (effect-review live)
6. Add US5 -> test independently -> demo (compliance live)
7. Add US6 -> test independently -> demo (onboarding live)
8. Add US7 -> test independently -> demo (gate + endpoints live)
9. Polish -> release

### Parallel Team Strategy

With two engineers:

1. Both complete Setup + Foundational together
2. Engineer A: US1 + US4 (LLM-heavy paths; leverages the `LLMClient` work in Phase 1)
3. Engineer B: US2 + US5 + US7 (data + compliance + integration)
4. Engineer A picks up US6 once US1 lands
5. Both share US3 + Polish after their respective stories finish

---

## Notes

- Tasks with `[US1]` ... `[US7]` labels map to the corresponding user story in [spec.md](./spec.md) for traceability
- Each user story is independently completable and testable
- Tests are required per Constitution Principle II (test-first discipline) and Quality Gate 7 (coverage >= 80%)
- Commit after each task or logical group; do not let tasks accumulate uncommitted
- Coverage drops below the 80% floor block merge; the floor MUST NOT be lowered without a constitution amendment
- All codegraph audit evidence lives in `.codegraph/codegraph.db`
