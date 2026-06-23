# Feature Specification: TopicAI v4.1 Implementation-Gap Closure

**Feature Branch**: `007-v4-gap-closure` (blocked in sandbox; planned)
**Created**: 2026-06-12
**Status**: Draft
**Input**: Audit of current `topicai` repo + product-strategy docs at
`G:\workbuddy_project\No_1_agent\deliverables\product-strategy` + the
existing v4.0 plan at `specs/006-topicai-v4-roadmap/`.
**Constitution**: v1.1.0

## Overview

The v4.0 surface is complete (14 pages, 14 routers, 17 backend services,
327 tests reported, 7 frontend test files, full Sentry/LangFuse/PostHog
wiring, prompt-registry versioning, content analyzers, 4-tier
DataManager). However, the audit performed on 2026-06-12 found that
**most advertised AI behavior is still template-stubbed** rather than
calling the real LLM, and the data/feedback loops that the product
strategy identifies as the personalization moat are not closed:

| Layer | What the surface says | What the code does today |
|---|---|---|
| `idea_booster` | Real LLM idea crystallization | Hard-coded `f"假设1：..."` strings; never calls `LLMClient` |
| `title_optimizer` | 3-5 LLM variations with CTR | Hard-coded 4 patterns + heuristic CTR; never calls LLM |
| `track_diagnosis` | LLM market diagnosis | Hard-coded 10-keyword score table; never calls LLM |
| `publish_advisor` | Personalized LLM slots | Static 3-slot table for every (platform, content_type) |
| `topic_recommend` | 4-tier cascade with rubric ranking | Returns 5 hard-coded `default_topics`; ignores `rubric_weights` |
| `feedback` | Persisted + adapt profile | In-memory dict only; `analyze_feedback` always called with `[]` |
| `onboarding` | LLM-derived `rubric_weights` | `_build_profile_with_llm` is a no-op that returns defaults |
| `content_risk` | Hybrid keyword + LLM | Keyword-only with 16 hard-coded terms; no LLM layer |
| `effect_review` | 3-phase lifecycle (DB-backed) | `self._predictions` in-memory dict; data lost on restart |
| `account_service.trigger_sync` | Real platform API pull | Just stamps `last_sync_at`; no platform API call |
| All 9 `app/chains/*.py` | LangChain orchestration | Empty stubs returning `[]` / `""` / `{}` |
| Frontend `AnalyticsPage` | Charts + breakdown | `EmptyState` placeholder ("Phase 4 完工") |
| Coverage gate (80%) | Enforced in CI | Not wired into `pyproject.toml` / `vitest.config.ts` |
| `backend/app/data/migrations/` | Numbered SQL | Directory does not exist; effects_reviews / user_feedback tables missing |
| 7 endpoints frontend calls | `/topics/history`, `/feedback/history`, `/risk/check`, `/reviews/learnings`, etc. | Not registered in `router.py` |

This spec turns the most expensive of those gaps into a single
independently-testable backlog. It is intentionally narrower than the
99-task `006-topicai-v4-roadmap/tasks.md`: the goal is to ship a
production-honest AI surface in one sprint slice, not to execute the
full roadmap. The remaining 006 tasks remain valid and feed into
subsequent specs.

The user-visible outcome: every AI action returns a real
`data_source`-tagged answer that the user can audit; the topic
recommendation page is driven by the 4-tier cascade and the user's
`rubric_weights`; thumbs-up/thumbs-down actually change the next
recommendation; and the v3 surface (Analytics placeholder, missing
endpoints) is filled in.

## User Scenarios & Testing

### User Story 1 - Real LLM coach for idea / title / track / publish (P1, MVP)

As a content creator, I submit a fuzzy idea, a draft title, a track
keyword, or a platform/content-type pair and get back a real
LLM-generated structured response (`confidence > 0.5`,
`data_source = "llm_simulation"` or `"heuristic"`,
`model_version` set), not a string from a hard-coded template.

**Why this priority**: Single largest gap between marketing copy and
runtime behavior. Closing it removes the "fake AI" smell and is a
prerequisite for the feedback loop (US3) and risk guard (US5) to be
auditable.

**Independent test**: With a `DEEPSEEK_API_KEY` set, the four coach
endpoints return HTTP 200 with `data_source = "llm_simulation"` and a
distinct `model_version` per call. Without a key, the same endpoints
still return 200 with `data_source = "template_fallback"` and
`confidence <= 0.5` in under 1 second.

**Acceptance Scenarios**:

1. **Given** a 200-character idea, **when** the user POSTs to
   `/api/v1/ideas/boost`, **then** the response has
   `key_assumptions` (>= 3), `feasibility_assessment`, 3-5
   `title_candidates`, a 4-6-section `content_outline`,
   `publish_schedule`, `confidence >= 0.6`,
   `data_source = "llm_simulation"`, `model_version = "deepseek-v4-flash"`,
   all within 8 seconds.
2. **Given** no API key, **when** the user POSTs the same idea,
   **then** the same schema returns with
   `data_source = "template_fallback"`, `confidence <= 0.5` in < 1s.
3. **Given** a 6000-character input, **when** the user POSTs to
   `/api/v1/ideas/boost`, **then** the service truncates to 5000
   characters before the LLM call and the response still validates.
4. **Given** the LLM returns malformed JSON, **when** the service
   processes it, **then** `_clean_json_response` recovers, or the
   service falls back to a template output with a `logger.warning`;
   the caller still receives 200.

---

### User Story 2 - 4-tier data source actually drives topic recommendations (P1)

As a creator on a fresh account, I open the Topics page and see real,
track-filtered, rubric-weighted recommendations that came from a live
data source (or a clearly-labelled preloaded benchmark when all live
tiers fail), rather than 5 hard-coded entries with identical
`composite_score` ordering.

**Why this priority**: Topics is the front door of the product and
currently the most visible stub. This also de-risks the feedback loop
(US3) because real recommendations produce real feedback.

**Independent test**: Stubbing `TIANAPI_KEY` empty and `BilibiliSource`
to fail forces `DataManager` to land on `PreloadedDataSource`; the
response is HTTP 200, `data_source = "preloaded"`, `confidence <= 0.5`,
5+ topics. With a working `TIANAPI_KEY` the response carries
`data_source = "tianapi"` and `confidence >= 0.6`. Each tier failure
emits a `WARNING` log with `tier` + `reason`; tier shifts are visible
in LangFuse traces.

**Acceptance Scenarios**:

1. **Given** no live tier configured, **when** the user requests
   recommendations for track `科技`, **then** they receive >= 5
   topics with `data_source = "preloaded"`, `confidence <= 0.5`.
2. **Given** `TianAPI` enabled and responsive, **when** the user
   requests recommendations, **then** they receive >= 5 topics with
   `data_source = "tianapi"`, `confidence >= 0.6`.
3. **Given** `TianAPI` returns 5xx, **when** the user requests
   recommendations, **then** the system retries once, falls through
   to `Bilibili`, and logs `tier=tianapi reason=5xx` at WARNING.
4. **Given** all live tiers fail, **when** the user requests
   recommendations, **then** the response is 200 with the preloaded
   safety net and a `data_source` badge in the UI; never an empty
   array, never a 5xx.

---

### User Story 3 - Feedback loop actually persists and adapts the creator profile (P2)

As a returning creator who has been giving thumbs-up/thumbs-down for a
week, my next recommendations reflect my taste. My `rubric_weights`
respond to feedback within seconds, and the change is auditable in
the database.

**Why this priority**: The math already exists in
`FeedbackService.analyze_feedback` and `adjust_weights`, but feedback
is dropped on the floor (in-memory dict, never persisted). Wiring
this closes the personalization moat and makes US1/US2 visibly better
over time.

**Independent test**: 5 thumb-down events on a single dimension move
`creator_profiles.rubric_weights` in the database within 5 seconds; the
next `/api/v1/topics/recommend` response reflects the new weights in
its `composite_score`. Cold-start accounts (< 7 days OR < 5 feedback
events) keep default weights and the API returns 202 with a
persisted id.

**Acceptance Scenarios**:

1. **Given** a brand-new account (< 7 days old, no feedback yet),
   **when** the user submits feedback, **then** the feedback row is
   persisted but `rubric_weights` remain at the default.
2. **Given** an established account, **when** the user submits a
   thumb-down on a title, **then** within 5 seconds
   `creator_profiles.rubric_weights` shows a bounded adjustment
   (`<= 0.15` per cycle per dimension).
3. **Given** feedback older than 30 days, **when** `adjust_weights`
   runs, **then** those records are excluded from the math but
   remain in the table for audit.
4. **Given** two concurrent feedback events for the same user,
   **when** they arrive within milliseconds, **then** the second
   write does not silently overwrite the first.

---

### User Story 4 - Effect review lifecycle is persistent and LLM-driven (P2)

As a creator who just published a piece, I fill in the actual
play/like/comment/share numbers from the platform after T+1 day. The
system shows me a clear comparison of what the LLM predicted vs.
reality, with 3-5 dimensional conclusions and a monthly learning
report I can act on.

**Why this priority**: Without effect review, US3 is blind: there is
no signal for the personalization loop to learn from.

**Independent test**: After creating an effect-review via
`POST /api/v1/reviews/predict` and submitting actuals via
`POST /api/v1/reviews/{review_id}/attribute`, the data is in the
`effect_reviews` table; a follow-up `GET /api/v1/reviews/learnings`
returns a non-empty report after the user has >= 1 attribution.
Restarting the process does not lose the prediction.

**Acceptance Scenarios**:

1. **Given** a topic and outline, **when** the user requests a
   prediction, **then** the response includes `estimated_views`,
   `estimated_likes`, `estimated_comments`, `engagement_rate`, and
   a `caveat` ("AI estimate, not a guarantee").
2. **Given** a prediction and actuals, **when** the user submits
   actuals, **then** the response includes 3-5 dimensional
   conclusions (title hook, opening, rhythm, CTA, visual punch),
   each with a `relevance` score and an `evidence` pointer.
3. **Given** >= 1 completed attribution, **when** the user requests
   learnings, **then** they receive a personal report grouping
   conclusions by dimension with frequency and impact.
4. **Given** a prediction was made, **when** the server restarts,
   **then** the prediction is still retrievable by id.

---

### User Story 5 - Content risk pre-publish guard with hybrid scoring (P3)

As a creator about to publish a draft that contains
"guaranteed no loss" or "100% cure", I want the system to flag the
risk and surface a blocking badge in the publish flow.

**Why this priority**: Lowest-effort, highest-stakes safeguard. Half a
day of work closes the compliance gap; the keyword library is already
seeded in `content_risk.py`; only the LLM layer and the `/risk/check`
endpoint are missing.

**Independent test**: POSTing content with "guaranteed no loss" to
`/api/v1/risk/check` returns a risk item with
`category = "financial_inducement"` and `severity = "high"`. POSTing
benign marketing copy returns `risks: []` and
`overall_risk_score < 0.2`. The endpoint exists in `router.py` and
the existing `RiskCheckRequest` / `ContentRiskReport` Pydantic models
are reused.

**Acceptance Scenarios**:

1. **Given** content containing "100% cure", **when** the user
   requests a risk check, **then** the response includes a
   `severity = "high"` item with `category = "medical_overclaim"`
   and a suggestion.
2. **Given** benign content, **when** the user requests a risk
   check, **then** the response is `risks: []` and
   `overall_risk_score < 0.2`.
3. **Given** the LLM is unavailable, **when** the user requests a
   risk check, **then** the keyword-only scan still runs,
   `data_source = "template_fallback"`, `confidence <= 0.5`.

---

### User Story 6 - Onboarding LLM-driven `rubric_weights` (P3)

As a new user completing onboarding, my answers shape
`rubric_weights` via a real LLM call instead of 7 equal defaults. The
priorities I expressed (e.g. "evergreen" vs "hotspot") are visible in
the profile immediately.

**Why this priority**: Sits on the US1 hot-path; once `LLMClient` is
exercised by US1, US6 becomes a one-day wrapper.

**Independent test**: With a key, the LLM-derived `rubric_weights`
reflect the answer priority (a "deep / evergreen" answer yields
`content_depth_match > hotspot_relevance`); without a key, the
fallback returns the existing defaults and the schema is identical.

**Acceptance Scenarios**:

1. **Given** answers with `content_depth = "deep"` and
   `hotspot_preference = "evergreen"`, **when** the user completes
   onboarding, **then** the resulting `rubric_weights` satisfies
   `content_depth_match > hotspot_relevance`.
2. **Given** no API key, **when** the user completes onboarding,
   **then** the response schema is identical to the LLM path and
   the values are the existing defaults.
3. **Given** the LLM raises, **when** the user completes onboarding,
   **then** the fallback fires, `data_source = "template_fallback"`,
   and the caller still receives 201.

---

### User Story 7 - Coverage gate and missing API endpoints wired (P2)

As a maintainer merging to `main`, the coverage gate in CI blocks
merge below 80% (backend) / 80% (frontend) and the seven endpoints
the frontend already calls (`/topics/history`, `/feedback/history`,
`/risk/check`, `/reviews/learnings`, `/reviews/list`, etc.) exist and
return documented schemas.

**Why this priority**: Without the gate, the 006 roadmap's
"regression-proof" promise is unenforceable. Without the endpoints,
the frontend is calling 404s in production (verified by reading
`feedback.ts` and `topics.ts` in `frontend/src/services/api/`).

**Independent test**: `pytest --cov=app --cov-fail-under=80` and
`pnpm vitest run --coverage` both pass on the protected branch. Every
method in `frontend/src/services/api/{topics,feedback,reviews,risk}.ts`
has a real handler in `backend/app/api/v1/router.py`.

**Acceptance Scenarios**:

1. **Given** the coverage gate configured, **when** a PR drops
   coverage below 80%, **then** the CI check fails.
2. **Given** the endpoint list in `router.py`, **when** the frontend
   boots, **then** no service-method call results in 404.
3. **Given** the gate, **when** a prompt or chain is added without
   tests, **then** CI fails and the PR cannot merge.

---

### Edge Cases

- **What happens when both `DEEPSEEK_API_KEY` and `DASHSCOPE_API_KEY`
  are missing?** All US1-US6 endpoints fall back to the template
  path; the response always returns 200 with
  `data_source = "template_fallback"` and `confidence <= 0.5`. The
  UI's `AIDegradedNotice` is rendered.
- **What happens when the LLM responds with non-JSON prose?** The
  service calls `_clean_json_response` (existing helper in
  `app/core/llm/`); on failure, it logs at WARNING and returns the
  template path.
- **What happens when the LLM times out (>8s)?** The service falls
  through to the template path; the `data_source` and `model_version`
  reflect the fallback, and the response is still under 1s.
- **What happens when the SQLite WAL file is locked by a previous
  crashed process?** Migration runner logs a clear error and refuses
  to start (existing behavior of `app/core/database.py`); the gate
  test `test_database.py` covers this.
- **What happens when feedback arrives during the cold-start grace
  window?** The row is persisted but `rubric_weights` are not
  adjusted; the response is 202 with the persisted id, the user
  sees a notification "Feedback received, profile will adapt after 5
  more signals".

## Requirements

### Functional Requirements

- **FR-001 (US1)** Each of `idea_booster`, `title_optimizer`,
  `track_diagnosis`, `publish_advisor` MUST call `LLMClient.generate`
  on the LLM path and return a `template_*` fallback on the heuristic
  path; the existing Pydantic response models MUST continue to
  validate in both paths. The `data_source` MUST be `"llm_simulation"`
  on success and `"template_fallback"` on the fallback; the
  `model_version` MUST be the real provider id on success and
  `"template_fallback"` on the fallback.
- **FR-002 (US1)** Inputs > 5000 characters MUST be truncated before
  the LLM call; the truncated text MUST still round-trip through
  the response schema.
- **FR-003 (US2)** `TopicRecommendService.recommend` MUST delegate
  to `DataManager.get_trending_topics` and rank the returned topics
  by `rubric_weights` composite score; the response MUST include
  `data_source` and `confidence` and MUST always return >= 1 topic
  (preloaded as the safety net).
- **FR-004 (US2)** `DataManager` MUST honor per-tier config
  (`timeout_seconds`, `retry_count`, `circuit_breaker`) declared in
  `config/data_source_config.py`; tier shifts MUST emit
  `logger.warning("tier_shift", extra=...)`; every successful
  fallback MUST emit `logger.info`.
- **FR-005 (US3)** `FeedbackService.submit` MUST persist the
  feedback row to a new `user_feedback` table and MUST return 202
  with the persisted id; `analyze_feedback` MUST run with the
  user's actual records, not `[]`.
- **FR-006 (US3)** `adjust_weights` MUST enforce a 7-day OR 5-event
  cold-start grace (no adjustment during grace), a bounded
  `+/- 0.15` per dimension per cycle, and a 30-day rolling window.
- **FR-007 (US4)** `EffectReviewService` MUST persist predictions,
  attributions, and learnings to a new `effect_reviews` table; the
  three endpoint methods `predict`, `attribute`, `derive_learnings`
  MUST be implemented and registered in `api/v1/reviews.py`.
- **FR-008 (US5)** A new `POST /api/v1/risk/check` endpoint MUST
  return the existing `ContentRiskReport` schema; the service MUST
  run keyword scan first (weight 0.8) and LLM layer second (weight
  0.2); on LLM failure, the keyword path runs alone and
  `data_source = "template_fallback"`.
- **FR-009 (US6)** `OnboardingService._build_profile_with_llm` MUST
  call `LLMClient.generate_structured` and derive
  `rubric_weights` from the user's answers; the existing
  `_build_profile_fallback` MUST continue to be the failure path.
- **FR-010 (US7)** `backend/pyproject.toml` MUST enable
  `pytest --cov=app --cov-fail-under=80`; `frontend/vitest.config.ts`
  MUST enable the same threshold. CI MUST fail the build when the
  threshold is not met.
- **FR-011 (US7)** The router in `backend/app/api/v1/router.py`
  MUST register the seven endpoints the frontend already calls
  (`/topics/history`, `/feedback/history`, `/risk/check`,
  `/reviews/list`, `/reviews/learnings`, plus the missing
  `/accounts/{id}/stats` and `/topics/{id}/adopt`).
- **FR-012 (cross-cutting)** A migration runner MUST be created at
  `backend/app/data/migrations/runner.py`, registered with
  `schema_migrations` tracking, and invoked from
  `backend/main.py` startup. New tables (`user_feedback`,
  `effect_reviews`, `risk_keywords`, `platform_tokens`) MUST be
  added as numbered idempotent SQL files in
  `backend/app/data/migrations/`.
- **FR-013 (cross-cutting)** Every new AI-returning endpoint MUST
  carry `confidence`, `data_source`, `model_version` in the
  Pydantic response model and MUST have at least one test asserting
  those fields are populated.

### Key Entities

- **`user_feedback`** (US3): `id`, `user_id`, `source_type`,
  `source_id`, `feedback_type`, `feedback_value`, `reason`,
  `created_at`. Indexed by `(user_id, created_at DESC)`.
- **`effect_reviews`** (US4): `id`, `user_id`, `topic_title`,
  `content_outline`, `prediction` (JSON), `actual_result` (JSON),
  `attribution` (JSON), `learnings` (JSON), `created_at`,
  `updated_at`. Indexed by `(user_id, created_at DESC)`.
- **`risk_keywords`** (US5): `id`, `user_id` (NULL for global),
  `keyword`, `severity`, `category`, `created_at`. Unique on
  `(user_id, keyword)`.
- **`platform_tokens`** (US6, prep for OAuth): `id`, `user_id`,
  `platform`, `access_token`, `refresh_token`, `expires_at`,
  `last_sync_at`, `created_at`. Unique on `(user_id, platform)`.
- **`schema_migrations`** (FR-012): `version` (PK), `applied_at`,
  `checksum`. Migration runner bookkeeping.

## Success Criteria

- **SC-001**: 100% of the AI-returning endpoints advertise
  `data_source != "ai_inference"` in the response (no fake-AI smell);
  the audit `grep -r "data_source.*ai_inference" backend/app/api` returns
  zero matches.
- **SC-002**: With `DEEPSEEK_API_KEY` set, `pytest tests/services
  -k llm_path` passes for all four coach services; the
  `template_fallback` path passes with the key removed.
- **SC-003**: Topic recommendation page shows distinct
  `composite_score` values for the 5 returned topics; the
  `data_source` badge is visible in the UI; tier shifts appear in
  LangFuse.
- **SC-004**: 5 thumb-down events on a single dimension move
  `rubric_weights` in the DB within 5 seconds; a UI smoke test
  confirms the next recommendations reflect the new weights.
- **SC-005**: `pytest --cov=app --cov-fail-under=80` and
  `pnpm vitest run --coverage` both pass on the protected branch;
  the gate is enforced in CI.
- **SC-006**: Zero 404s when the frontend's existing service methods
  are exercised end-to-end (Playwright scenario `e2e/full-loop.spec.ts`).
- **SC-007**: The 4 coach services and the topic recommendation
  service have at least one test for the LLM success path, the LLM
  exception fallback path, the oversized-input truncation case, and
  the malformed-JSON case (the canonical mock pattern from
  Constitution Principle II).
- **SC-008**: `AIDegradedNotice` is rendered in the UI whenever
  `data_source = "template_fallback"`; verified by a Playwright
  scenario that toggles the env var.

## Assumptions

- The product strategy docs in
  `G:\workbuddy_project\No_1_agent\deliverables\product-strategy`
  are the source of truth for *what* the product should do; the
  current repo is the source of truth for *what* is built. This
  spec reconciles the two.
- The existing v4.0 spec at `specs/006-topicai-v4-roadmap/`
  remains valid; this 007 spec is a narrower, executable subset
  (the 7 user stories here map onto US1-US7 of 006, but drop the
  cross-cutting polish and the 006-only platform OAuth work).
- The Constitution at v1.1.0 governs; in particular: heuristic-
  first LLM invocation (Principle VI), Pydantic-on-the-boundary
  (Principle VII), tiered data source with per-tier config
  (Principle VIII), and the 80% coverage gate (Quality Gate 7).
- The user has admin access to the working tree and can run
  `pytest` / `pnpm` locally; CI parity is via GitHub Actions
  (the existing workflow files are unchanged).
- Branch creation is blocked in the current sandbox by .git ACLs
  (deny rule on `refs/heads/`); the work itself proceeds on
  `main` for now, with the spec branch created by the maintainer
  when this is committed.

## Appendix A - Current State Inventory (audit 2026-06-12)

Read directly from the working tree.

### Backend - Real (no change needed)
- `app/core/llm.py` - multi-provider LLMClient with retry,
  structured output, AIQualityMeta (verified lines 1-100).
- `app/core/database.py` - SQLAlchemy async, WAL, JSON columns
  (mentioned in `creator_profile.py` and `asset_service.py`).
- `app/core/chroma.py` - ChromaDB client (initialized in lifespan).
- `app/data_sources/data_manager.py` - 3-tier cascade present.
- `app/data_sources/tianapi_source.py` - real httpx calls.
- `app/data_sources/bilibili_source.py` - real httpx calls.
- `app/data_sources/preloaded_source.py` - 5 tracks seeded.
- `app/content_analyzers/text_analyzer.py`,
  `app/content_analyzers/image_analyzer.py` - factory + concrete
  (verified `text_analyzer.py:25-35`).
- `app/services/viral_analysis.py` - real LLM call present
  (`_analyze_with_llm`, lines 65-130).
- `app/services/creator_profile.py` - real CRUD + JSON columns.
- `app/services/asset_service.py` - real SQLAlchemy CRUD.
- `app/services/account_service.py` - real CRUD (sync is the
  exception, see below).
- `app/services/team_service.py` - real CRUD.
- `app/api/v1/auth.py` - real JWT register/login/refresh.
- `app/api/v1/profiles.py` - real onboarding + get/update.
- `app/api/v1/accounts.py` - real CRUD (uses `get_current_user`).
- `app/api/v1/team.py` - real CRUD.
- `app/api/v1/assets.py` - real CRUD.
- `app/prompts/registry.py` - version-resolvable prompt loader.
- `app/middleware/auth_middleware.py`, `app/middleware/rate_limit.py`
  - real middleware wired in `main.py`.

### Backend - Template-stubbed (rewrite target for US1, US2, US5, US6)
- `app/services/idea_booster.py` - hard-coded `假设1` strings,
  `confidence = 0.75` baked in, no LLM call.
- `app/services/title_optimizer.py` - hard-coded 4 patterns, no LLM.
- `app/services/track_diagnosis.py` - hard-coded 10-keyword score
  table, no LLM.
- `app/services/publish_advisor.py` - hard-coded 3-slot table, no LLM.
- `app/services/topic_recommend.py` - returns 5 hard-coded
  `default_topics`, ignores `rubric_weights` and `DataManager`.
- `app/services/feedback.py` - in-memory only, no DB persist,
  `analyze_feedback(user_id, [])` always called from API.
- `app/services/content_risk.py` - keyword-only with 6+6+4
  hard-coded patterns, no LLM layer.
- `app/services/onboarding.py` - `_build_profile_with_llm` is a
  no-op that returns defaults; the `_get_llm()` call never lands
  on a prompt.
- `app/services/effect_review.py` - `self._predictions` in-memory
  dict, no DB, predictions lost on restart.
- `app/services/account_service.trigger_sync` - stamps
  `last_sync_at`, no platform API call.
- `app/chains/idea_chain.py`, `title_chain.py`, `track_chain.py`,
  `publish_chain.py`, `topic_chain.py`, `feedback_chain.py`,
  `effect_review_chain.py`, `risk_chain.py` - all return
  empty dicts / lists.
- `app/chains/viral_chain.py` - has methods but they all return
  empty (the real LLM call lives in the service, not the chain).

### Backend - Missing files / endpoints
- `app/data/migrations/` directory does not exist (verified `ls`).
- `POST /api/v1/risk/check` not in `app/api/v1/router.py`.
- `GET /api/v1/reviews/learnings` not in `app/api/v1/router.py`.
- `GET /api/v1/reviews/list` not in `app/api/v1/router.py`.
- `GET /api/v1/topics/history` not in `app/api/v1/router.py`.
- `GET /api/v1/feedback/history` not in `app/api/v1/router.py`.
- `app/integrations/oauth/` does not exist.
- `app/tasks/oauth_token_refresh.py` does not exist.

### Frontend - Real (no change)
- 12 protected routes registered in `App.tsx` (9 V3 sidebar tabs
  + 3 legacy aliases).
- 14 page modules: Home, TopicRecommend, ViralAnalysis,
  Writing/IdeaBooster, TitleOptimizer, TrackDiagnosis,
  PublishAdvisor, EffectReview, CreatorProfile, Assets, Accounts,
  Login, NotFound.
- AICreatedBadge + AIDegradedNotice + EmptyState + LoadingCard +
  ErrorBoundary + Modal + ScoreBar + BarChart + ChipRow +
  ConfidenceBadge + DataSourceTag + Calendar + StatsRow present.
- Sidebar (8.8KB) + AppLayout + Header + PageContainer + RightPanel.
- 4 hooks: useApi, useAuth, useFeedback, useRateLimit.
- 11 API service modules in `services/api/`.
- Zustand stores: auth, profile, app, (store dirs visible).

### Frontend - Stubs (target for follow-on specs)
- `pages/Analytics/AnalyticsPage.tsx` (839 bytes) - renders
  `EmptyState` "Phase 4 完工". Out of scope for 007; tracked.
- `pages/Writing/WritingPage.tsx` (345 bytes) - aliases
  IdeaBooster. Cosmetic.

### Test coverage
- 17 backend test files, 7 frontend test files (`.test.tsx`).
- 0 Playwright `.spec.ts` files in the working tree
  (`Get-ChildItem -Filter "*.spec.*"` returned 0) - the README
  advertises 8 cases; they are not present.
- No service-layer tests for the 4 coach services
  (`test_idea_booster.py`, `test_title_optimizer.py`,
  `test_track_diagnosis.py`, `test_publish_advisor.py` are
  missing).
- Coverage gate not wired: `grep "cov-fail-under"` finds no
  match in `pyproject.toml` (read directly).


## Appendix B - Cross-Reference to Product Strategy Documents

This spec is grounded in the product-strategy deliverables at
`G:\workbuddy_project\No_1_agent\deliverables\product-strategy` (the
"0-1 documentation"). Every user story in this spec maps back to a
specific product-strategy decision.

### B.1 - Calibration cycle composite scores (priority)

The composite scores from
`topicai_product_calibration_cycle.md` (v0 cold-start rubric) inform
the user-story priorities in this spec:

| Strategy feature ID | composite | This spec | Why this priority |
|---|---|---|---|
| R01 閫夐鎺ㄨ崘 | **9.43** | US2 (P1) | Highest composite (pain directness 5/5, frequency 5/5); 3-tier data dependency (PDP 5/5) - the personalization moat hinges on this. |
| R18 鐖嗘鎷嗚В | **8.29** | (deferred to 006) | Real LLM call already exists in `viral_analysis._analyze_with_llm`; the only gap is the 4-step chain orchestration (PML 5/5). |
| R12 鏁堟灉澶嶇洏 | **7.14** | US4 (P2) | Closes the personalization loop; without this, US3 is blind. |
| R15 璧涢亾璇婃柇 | **6.86** | (deferred to 006) | Already exists in `track_diagnosis` template-stub form; rewrite is the same pattern as US1. |
| R02 鏍囬浼樺寲 | **6.57** | US1 (P1) | High frequency (PFY 5/5) + high action conversion (PCT 5/5) - users actually apply these. |
| R19 鎯虫硶鎺ㄨ繘 | **6.00** | US1 (P1) | Bundled with R02 in the "idea / title coach" surface; PRD simplified version (skip multi-round) per `requirement-review-2026-05-18.md` C02. |
| R05 鍒涗綔鐢诲儚 | **6.00** | US6 (P3) | Per C03 in requirement-review: R05 is the Onboarding flow (one-time), not a separate track-diagnosis duplicate. |
| R03 鍙戝竷鏃堕棿 | **4.29** | US1 (P1) | Lower composite; included in US1 because the rewrite cost is the same as the other three coaches. |
| R10 鏀惰棌/鍘嗗彶 | **2.57** | (deferred) | Pure record CRUD (PDP 0/5, PML 0/5); out of 007 scope per spec. |

### B.2 - 5-layer AI quality protection (technical decisions)

`topicai_v4_technical_decisions.md` (section 6) defines a 5-layer
protection system. This spec's user stories address each layer:

| Layer | What | This spec's enforcement |
|---|---|---|
| **L1 缁撴瀯鍖?Prompt** | Templated prompts with stable output format | `backend/prompts/*.v1.md` files (T-006) + PromptRegistry versioning (already in repo) |
| **L2 JSON Schema 绾︽潫** | Pydantic validation, max 2 retries | FR-013 + `_clean_json_response` in `app/core/llm/` (already in repo) |
| **L3 涓嶇‘瀹氭€ф爣娉?** | Every output carries `confidence` + `data_source` + `caveat` | FR-001..FR-009 + AIQualityMeta (already in repo) |
| **L4 棣栨帹闄嶇骇鍏滃簳** | Core=DeepSeek→Qwen→降级提示; auxiliary=降级提示; decorative=隐藏 | LLMClient tier cascade (already in repo); this spec inherits it |
| **L5 绾犳鍙嶉寰幆** | User 👍/👎 → record → affect next recommendation weights | US3 (P2) - this is the gap |

US3 in this spec is the L5 layer. The 006 roadmap's broader US1-US4
cover L1-L4 (L1-L3 are already implemented in the repo; L4 is the
LLMClient tier cascade).

### B.3 - Data source tier strategy (technical decisions, section 3)

The v4 strategy document describes a 3-layer cascade:

```
Layer 1: 平台公开热搜/趋势 API (TianAPI, Bilibili)
Layer 2: LLM 模拟生成 (DeepSeek V4 Flash)
Layer 3: 预置基准数据 (50 tracks)
```

The current `DataManager` already implements this. This spec
preserves the existing layout (TianAPI and Bilibili as parallel
"Layer 1" sources; LLM as Layer 2; preloaded as Layer 3) and only
fixes the gap that **the orchestrator is built but not connected**
(US2). The 50-track preloaded target from the strategy is a
follow-on scope expansion beyond this 007 spec - the 007 task T-042
seeds 8 tracks as the minimum for the safety net, with a follow-on
issue for the remaining 42.

### B.4 - Storage and retention (technical decisions, section 4)

The v4 strategy mandates:
- 90-day user content TTL: enforced in `app/tasks/cleanup_expired.py`
  (existing) - no change in this spec.
- 30-day feedback rolling window: US3 task T-051 enforces this
  (the active window) while retaining rows indefinitely for audit.
- 7-day OAuth token refresh: deferred to 006 (table `platform_tokens`
  is added in 007 as foundation only).
- Daily backup, 30 generations retained: handled by
  `app/tasks/backup.py` (existing) - no change in this spec.

### B.5 - Test plan alignment

`topicai_v4_test_plan.md` defines:
- Coverage targets: core layer >90%, service layer >80%, API
  layer >70%. This spec inherits the Constitution Quality Gate 7
  floor (80% globally) and adds it to `pyproject.toml` + `vitest.config.ts`
  in T-001 and T-002.
- TDD order: red → green → refactor. This spec's task ordering
  (T-017..T-026 all tests-first) follows the same pattern.
- Specific test case IDs (TC01-15, TC02-09, etc.) are referenced
  in the per-service test tasks; the per-test test cases are in
  the per-task acceptance scenarios.

### B.6 - Requirement review resolutions (requirement-review-2026-05-18.md)

| Issue | Resolution | This spec |
|---|---|---|
| C01 R18 input format | MVP: paste-text only, no URL scraping | already in repo (US1-style) |
| C02 R19 simplified | Single-step input/output, no multi-round | already in repo (US1-style) |
| C03 R05 vs R15 | R05 = Onboarding, R15 = independent track diagnosis | US6 (R05) is the only onboarding gap; R15 deferred to 006 |
| C04 auth method | Email+password MVP, OAuth later | already in repo (US7 endpoints) |
| C05 storage | SQLite local, 90-day TTL | already in repo (no change) |
| C06 payment | Skipped for MVP, no payment logic | out of scope |
| C07 sequencing | Mock earlier modules, integrate later | US2 uses real DataManager; US1 mocks aren't needed |
| C08 R18 URL scraping | Deferred, paste-text only | already in repo |
| C09 data source API | Use TianAPI + preloaded safety net | US2 |
| C10 acceptance criteria | Quantified (returned topics, TTFT, fields) | US1-US7 acceptance scenarios |

### B.7 - Class / sequence diagram alignment

The product-strategy `docs/class-diagram.mermaid` defines entities
that match this spec's data model (`User`, `CreatorProfile`,
`TopicRecommendation`, `TopicItem`, `ViralAnalysis`,
`IdeaBoosterResult`, `TitleOptimization`, `PublishTimeSuggestion`,
`FeedbackRecord`, `FeedbackAnalysis`, `LLMClient`).

The product-strategy `docs/sequence-diagram.mermaid` shows 5 flows
(Onboarding, Topic Recommendation, Viral Analysis, Idea Booster,
Effect Review) - all 5 are addressed in this spec's user stories
or the 006 roadmap.

### B.8 - Items from product strategy that are OUT of 007 scope

These are explicitly noted as not in this 007 spec:

1. **Full Xiaohongshu OAuth automation** (PRD R05-followup): the
   006 roadmap owns this; 007 only creates the `platform_tokens`
   table as a foundation.
2. **URL scraping for viral analysis** (PRD R18 C08): paste-text
   only; deferred.
3. **Multi-round Onboarding** (PRD R19 C02): single-step; deferred.
4. **Payment / subscription tier** (PRD C06): out of scope for MVP.
5. **50-track preloaded data** (PRD v4 strategy L3): 007 seeds
   8 tracks (the safety-net minimum); the remaining 42 are a
   follow-on scope expansion.
6. **Frontend `AnalyticsPage` real charts** (PRD design summary):
   the placeholder at `frontend/src/pages/Analytics/AnalyticsPage.tsx`
   stays as an `EmptyState`; the full charts are a follow-on spec.
7. **Service-level observability dashboards** (PRD blind-spot
   section 2.1): not in 007; tracked separately.
8. **Prompt 版本管理 git hooks** (PRD lifecycle section): the
   prompt registry already versions, but the PR-gating hook is a
   follow-on.

These are noted here so a maintainer reviewing this spec knows
which items the product strategy calls for but this 007 slice
explicitly defers.
