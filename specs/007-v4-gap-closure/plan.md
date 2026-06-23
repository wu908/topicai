# Implementation Plan: TopicAI v4.1 Implementation-Gap Closure (007)

**Branch**: `007-v4-gap-closure` (blocked in sandbox; planned)
**Date**: 2026-06-12 | **Spec**: [spec.md](./spec.md)
**Constitution**: v1.1.0
**Audit source**: codegraph v0.9.9 (225 files, 2,142 nodes, 3,644 edges)
**Source plan**: `.claude/plans/topicai-feature-audit-and-roadmap.plan.md` (parent roadmap)
**Source spec**: `specs/006-topicai-v4-roadmap/spec.md` (broader 99-task parent; this 007 is a focused subset)

## Summary

The current repo ships a polished v4.0 surface (14 pages, 14 routers,
327 reported tests) but a codegraph audit performed on 2026-06-12
shows that **17 of 18 service / chain modules that should call
`LLMClient` never do**:

```
codegraph query "LLMClient" --path G:\workbuddy_project\topicai
```

| Module | Imports `LLMClient`? | Actually calls it? | Evidence |
|---|---|---|---|
| `app/services/viral_analysis.py` | yes | **yes** | `viral_analysis.py:71`, `_analyze_with_llm` body uses `llm.generate(...)` |
| `app/services/onboarding.py` | yes | **no** | `_build_profile_with_llm` ignores `llm` arg, returns defaults (`onboarding.py:97-129`) |
| `app/services/idea_booster.py` | no | **no** | hard-coded `f"假设1：..."` strings (`idea_booster.py:34-49`) |
| `app/services/title_optimizer.py` | no | **no** | 4 hard-coded patterns (`title_optimizer.py:18-26`) |
| `app/services/track_diagnosis.py` | no | **no** | 10-keyword static score table (`track_diagnosis.py:23-37`) |
| `app/services/publish_advisor.py` | no | **no** | 3-slot static table (`publish_advisor.py:18-39`) |
| `app/services/topic_recommend.py` | no | **no** | returns 5 hard-coded `default_topics` (`topic_recommend.py:91-117`) |
| `app/services/feedback.py` | n/a | n/a | in-memory dict, no DB persist (`feedback.py:25-39`) |
| `app/services/content_risk.py` | no | **no** | keyword-only (`content_risk.py:8-19`, no LLM call site) |
| `app/services/effect_review.py` | no | **no** | `self._predictions` in-memory, no DB (`effect_review.py:21-24`) |
| `app/services/account_service.py` | no | **no** | `trigger_sync` only stamps timestamp (`account_service.py:1`) |
| `app/services/creator_profile.py` | no | n/a | real CRUD; no LLM needed (correct) |
| `app/services/asset_service.py` | no | n/a | real CRUD; no LLM needed (correct) |
| `app/services/team_service.py` | no | n/a | real CRUD; no LLM needed (correct) |
| `app/services/viral_analysis.py` (re-listed) | yes | **yes** | only real LLM call site in services |
| `app/chains/*.py` (9 modules) | n/a | **no** | every chain returns `[]` / `""` / `{}` |
| `app/data_sources/data_manager.py` | yes | **no** | builds the LLMDataSource but never executes it |
| `app/data_sources/llm_source.py` | yes (type) | **no** | `llm_source.py:103` comment: "When LLM is available, this would call the LLM. For now, ..." |

Confirmed via `codegraph callers 'DataManager'` and
`codegraph callers 'LLMClient.generate'`:

```
Callers of "LLMClient.generate" (4):
  - test_generate_structured_success              backend/tests/core/test_llm.py:155
  - test_generate_structured_retry_on_invalid_json backend/tests/core/test_llm.py:178
  - test_generate_structured_fails_after_max_retries backend/tests/core/test_llm.py:221
  - test_generate_produces_quality_meta           backend/tests/core/test_llm.py:358
```

**Zero production callers.** Every business-path call into the LLM
must be wired by this plan.

Additional audit findings:

- `codegraph query 'user_feedback'` returns only the frontend
  `useFeedback` hook; **no SQL table, no migration** exists.
- `codegraph files --pattern '**/migrations/**'` returns **0
  files**; the entire `backend/app/data/migrations/` directory
  is absent.
- `codegraph query '/risk/check'` returns **no results**; the
  router is not registered in `app/api/v1/router.py`.
- `codegraph query 'risk_router'` returns **no results**;
  `app/api/v1/risk_router.py` does not exist.
- `codegraph impact 'IdeaBoosterService.boost'` returns 12
  affected symbols (the method, its helpers, the API route, and
  3 tests in `test_core_services.py`), so the no-op version is
  what the existing test suite covers.

The fix is intentionally conservative: heuristic-first with LLM
augmentation (Constitution Principle VI), Pydantic-on-the-boundary
(Principle VII), tiered data source with per-tier config
(Principle VIII), and the 80% coverage gate locked into CI
(Quality Gate 7). Every coach endpoint carries `confidence`,
`data_source`, `model_version` so the UI can audit AI
contributions (Principle III).

## Technical Context

**Language/Version**: Python 3.12 (backend, current), TypeScript 5.x
(frontend, current).
**Primary Dependencies (existing)**: FastAPI 0.115.6, Pydantic 2.10.5,
LangChain 0.3.13, SQLAlchemy 2.0.36 (async), APScheduler 3.11.0,
aiosqlite 0.20.0 (dev), openai 1.58.1 (DeepSeek V4 + Qwen compatible
endpoints), React 19, Vitest, Playwright.
**Storage**: SQLite via SQLAlchemy async (default dev); the new
`backend/app/data/migrations/` directory will use the
`NNN_<topic>.sql` numbering pattern with idempotent
`IF NOT EXISTS` and a `schema_migrations` tracking table.
**Testing**: pytest + pytest-cov (>= 80% gate, Quality Gate 7),
Vitest with `@vitest/coverage-v8` (>= 80%), Playwright E2E
(4 existing `.spec.ts` files at `frontend/e2e/`).
**Target Platform**: Linux server (Docker compose parity required).
**Project Type**: Web application (FastAPI backend + React frontend)
— no new structural change from the parent roadmap.
**Performance Goals** (per Constitution V / YAGNI):
- Coach endpoints (idea / title / track / publish) p95 < 8s on the
  LLM path, p95 < 1s on the template path.
- Topic recommendation p95 < 3s on tier-1, p95 < 1s on preloaded.
- `/api/v1/risk/check` p95 < 4s (LLM only when keyword scan flags
  low confidence).
- Feedback submit p95 < 1s (single row insert + bounded weight
  update).
**Constraints** (from Constitution v1.1.0):
- No silent degradation: every AI response carries the provenance
  triplet (Principle III).
- 90-day user content TTL, 30-day feedback rolling window, 7-day
  OAuth token refresh window (Constitution Data Lifecycle section).
- 80% coverage gate, both backend and frontend (Quality Gate 7).
- All migrations idempotent and tracked in `schema_migrations`
  (Quality Gate 8).
**Scale/Scope**: 7 user stories, ~40 implementation tasks,
~12 person-days of work, 4-5 sprints at two engineers.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence (this plan) |
|---|---|---|
| I. Service-Layer Architecture | PASS | All new logic lives in `app/services/` (FR-001..FR-009); endpoints remain thin adapters. |
| II. Test-First Discipline | PASS | TDD ordering in tasks.md: tests in Phase 2-3 precede implementation in Phase 4-7. Canonical mock pattern (Constitution line 80) reused for every LLM call site. |
| III. AI Transparency & Provenance | PASS | FR-013 mandates `confidence` / `data_source` / `model_version` on every new endpoint; FR-001 mandates the fallback path sets `data_source="template_fallback"` and `confidence <= 0.5`. |
| IV. Multi-LLM Tiered Routing | PASS | The existing `LLMClient` tier cascade is reused; failover traces go to LangFuse (no new tier work in this 007 spec). |
| V. Observability & Simplicity | PASS | Sentry / LangFuse / PostHog already wired; new tier-shift and fallback events follow the existing `logger.warning` / `logger.info` pattern. |
| VI. Hybrid AI Discipline | PASS | Heuristic pipelines (existing `_extract_assumptions`, `_generate_variations`, etc.) remain the `template_fallback`; LLM is invoked first on the coach endpoints, fallback on LLM error. |
| VII. Schema-Validated Service Contracts | PASS | FR-013: every new response uses the existing Pydantic models (`IdeaBoosterResult`, `TitleOptimization`, `TrackDiagnosis`, `PublishTimeSuggestion`, `TopicRecommendation`, `ContentRiskReport`). |
| VIII. Data Source Tiered Fallback | PASS | US2 mandates per-tier config in `config/data_source_config.py`; tier shifts emit `logger.warning`; preloaded safety net is the last resort (FR-003, FR-004). |
| IX. Effect Review Loop | PASS | US4 persists to the new `effect_reviews` table; the predict / attribute / derive_learnings 3-phase lifecycle is the only writer of that table. |
| X. User Feedback-Driven Personalization | PASS | US3 enforces the 7-day OR 5-event cold-start grace, bounded `+/- 0.15` shift, 30-day rolling window (FR-006); SQLite default isolation is sufficient (Constitution Principle X). |
| XI. Content Risk Pre-Publish Guard | PASS | US5 adds the 80/20 keyword/LLM blend (FR-008); `risk_keywords.json` seed at 100 entries (task T-XX). |
| XII. Platform Integration Adapter Pattern | NOT IN SCOPE | The 006 roadmap's OAuth work is not in this 007 subset; only the `platform_tokens` table is added as a foundation (FR-012, task T-XX). |
| XIII. Security & Data Minimization | PASS | All new tables carry `user_id` FK to `users.id`; `expires_at` is set 90 days out per existing TTL pattern (Constitution Data Lifecycle). |
| XIV. API Versioning & SemVer | PASS | All new endpoints live under `/api/v1/`; the 7 missing endpoints are added without breaking existing contracts. |
| Quality Gate 7 (Coverage >=80%) | PASS | FR-010 wires the gate into both `backend/pyproject.toml` and `frontend/vitest.config.ts`; SC-005 is the success criterion. |
| Quality Gate 8 (Migration Discipline) | PASS | FR-012 creates `backend/app/data/migrations/runner.py` and a `schema_migrations` table; all new SQL is idempotent. |

No unjustified violations; Complexity Tracking is empty.

## Project Structure

This spec does **not** introduce a new module layout. The existing
`backend/app` + `frontend/src` layout is kept. Files added or
modified by this plan:

### New backend files

```text
backend/app/
  services/
    __init__.py                        # (modified) re-exports updated services
  data/
    migrations/                        # NEW DIRECTORY
      runner.py                        # NEW: idempotent migration runner
      001_bootstrap.sql                # NEW: schema_migrations table
      002_user_feedback.sql            # NEW: US3
      003_effect_reviews.sql           # NEW: US4
      004_risk_keywords.sql            # NEW: US5
      005_platform_tokens.sql          # NEW: prep for US6 (deferred)
  models/
    effect_review.py                   # (modified) PredictionPayload, AttributionPayload, LearningsPayload
    feedback.py                        # (modified) FeedbackRecord (existing schema, expand docstring)
    risk.py                            # (exists; reuse ContentRiskReport)
  api/v1/
    reviews.py                         # (modified) add /learnings, /list endpoints
    risk_router.py                     # NEW: US5 /risk/check endpoint
    topics.py                          # (modified) add /history endpoint
    feedback.py                        # (modified) add /history endpoint, persist on submit
  prompts/                             # NEW DIRECTORY (or .md files alongside services)
    idea_boost.v1.md                   # NEW: US1
    title_optimize.v1.md               # NEW: US1
    track_diagnose.v1.md               # NEW: US1
    publish_suggest.v1.md              # NEW: US1
    onboarding_rubric.v1.md            # NEW: US6
    risk_check.v1.md                   # NEW: US5
  tests/
    services/
      test_idea_booster.py             # NEW: TDD for US1
      test_title_optimizer.py          # NEW: TDD for US1
      test_track_diagnosis.py          # NEW: TDD for US1
      test_publish_advisor.py         # NEW: TDD for US1
      test_topic_recommend.py          # NEW: TDD for US2
      test_feedback.py                 # NEW: TDD for US3 (replaces in-memory test)
      test_content_risk.py             # NEW: TDD for US5
      test_onboarding.py               # (exists; expand for US6 LLM path)
    api/
      test_reviews_router.py           # NEW: TDD for US4
      test_risk_router.py              # NEW: TDD for US5
      test_feedback_router.py          # NEW: TDD for US3
      test_topics_router.py            # NEW: TDD for US2
    integration/
      test_full_loop.py                # NEW: login -> topics -> feedback -> weight change
      test_data_manager_cascade.py     # NEW: tier-shift behavior
    chains/
      test_effect_review_chain.py      # NEW: TDD for US4 LLM path
```

### Modified backend files

```text
backend/app/
  services/
    idea_booster.py                    # REWRITE: heuristic + LLM split
    title_optimizer.py                 # REWRITE: heuristic + LLM split
    track_diagnosis.py                 # REWRITE: heuristic + LLM split
    publish_advisor.py                 # REWRITE: heuristic + LLM split
    topic_recommend.py                 # REWRITE: delegate to DataManager
    feedback.py                        # REWRITE: persist + adjust_weights
    content_risk.py                    # REWRITE: add LLM layer (80/20 blend)
    effect_review.py                   # REWRITE: persist to DB
    onboarding.py                      # REWRITE: real LLM call
    account_service.py                 # (modified) trigger_sync calls adapter
  data_sources/
    data_manager.py                    # (modified) per-tier config, tier-shift logs
    llm_source.py                      # REWRITE: actually call LLM
  config/
    data_source_config.py              # (modified) per-tier dataclass
  main.py                              # (modified) wire migration runner
  pyproject.toml                       # (modified) enable --cov-fail-under=80
```

### New frontend files

```text
frontend/src/
  services/api/
    reviews.ts                         # NEW: client for /reviews/{predict,attribute,learnings,list}
    risk.ts                            # NEW: client for /risk/check
  pages/EffectReview/
    EffectReviewPage.tsx               # (exists; expand to add /learnings card)
```

### Modified frontend files

```text
frontend/src/
  services/api/
    topics.ts                          # (modified) consume /topics/history
    feedback.ts                        # (exists; verify payload matches backend)
  components/ai-badge/
    AICreatedBadge.tsx                 # (exists; ensure all coach outputs render it)
  vitest.config.ts                     # (modified) enable coverage threshold
  playwright.config.ts                 # (modified) add e2e/full-loop.spec.ts
```

## Phased Delivery (mirrors spec user stories)

| Phase | User Story | Sprint | Deliverable | Key code change |
|---|---|---|---|---|
| **Setup** | (gates) | S1 | T-001..T-010 | Coverage gate in `pyproject.toml` + `vitest.config.ts`; migration runner + `001_bootstrap.sql`; prompts dir + 5 `.v1.md` files |
| **US1** | Real LLM coach (P1) | S1-S2 | T-011..T-024 | Rewrite the 4 service modules to call `LLMClient.generate_structured` on the LLM path; preserve the heuristic path as `template_fallback`; tests first |
| **US2** | 4-tier topic routing (P1) | S2 | T-025..T-032 | `DataManager` per-tier config + `topic_recommend.recommend` delegation + `tier_shift` structured logs |
| **US3** | Feedback loop (P2) | S3 | T-033..T-040 | `user_feedback` table; `FeedbackService.submit` persists; `_maybe_update_profile` enforces cold-start + bounded shift + 30-day window |
| **US4** | Effect review (P2) | S3-S4 | T-041..T-048 | `effect_reviews` table; `EffectReviewService` persists; 4 endpoints; `EffectReviewPage` learnings card |
| **US5** | Risk guard (P3) | S4 | T-049..T-054 | `risk_keywords` table (100 entries); `risk_router.py`; LLM layer; UI badge in `PublishAdvisor` |
| **US6** | Onboarding LLM (P3) | S5 | T-055..T-058 | `_build_profile_with_llm` calls `LLMClient.generate_structured(schema=CreatorProfile)`; fallback path preserved |
| **US7** | Endpoints + gate (P2) | S5 | T-059..T-064 | Add 5 missing endpoints; CI gate verified; `e2e/full-loop.spec.ts` green |
| **Polish** | (cross-cutting) | S5 | T-065..T-070 | `openapi3.json` sync; `README.md` feature table update; `AIDegradedNotice` smoke test |

## Risk Tracking

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `LLMClient` raises on missing `DEEPSEEK_API_KEY` | Medium | High | Service catches `Exception` (canonical mock pattern), falls back to template path; `logger.warning` carries the exception type. |
| `_clean_json_response` regression on new prompts | Medium | High | Pin 5 fixture responses in `tests/core/test_llm.py`; rerun before each new prompt. |
| `DataManager` 4-tier cascade deadlock (all tiers time out) | Low | High | Per-tier timeout (3s) + circuit breaker (3 fails, 30s half-open); preloaded tier 4 always returns 200 (FR-003). |
| Coverage gate false-positive on the protected branch | Low | Medium | `pyproject.toml` and `vitest.config.ts` set the threshold; tests are run in CI on every PR. |
| Two concurrent feedback writes for the same user | Low (SQLite) / Medium (PG) | Medium | On SQLite, default isolation is sufficient. Constitution Principle X mandates `SELECT FOR UPDATE` on PostgreSQL — captured in tasks as T-038 with a stub. |
| `tier_shift` log noise in production | Low | Low | Use `logger.warning` with `extra={"event": "tier_shift", "from": "tianapi", "to": "bilibili", "reason": "5xx"}`; aggregate in LangFuse. |
| Sandbox branch-creation block (.git ACLs) | Already blocking | Low | Specs and plan live on `main`; a maintainer creates the branch from the working tree. |
| Existing 327 tests drop below 80% with new code paths | Low | High | New tests are added in the same Phase as the implementation (TDD); the gate is a *floor*, not a *target* (Constitution Quality Gate 7). |
| Provider switching during failover loses trace | Low | Medium | `LLMClient` already emits `model_version` on every response; `LangFuse` is wired in `main.py`; no new wiring needed. |

## Complexity Tracking

No Constitution violations. Complexity Tracking is empty by design.

## Evidence Appendix (codegraph audit, 2026-06-12)

```text
$ codegraph status G:\workbuddy_project\topicai
  Files:     225
  Nodes:     2,142
  Edges:     3,644
  Backend:   node:sqlite - built-in (full WAL)

$ codegraph callers "LLMClient.generate" --path G:\workbuddy_project\topicai
  (4 results, all in backend/tests/core/test_llm.py)

$ codegraph query "LLMClient" --path G:\workbuddy_project\topicai
  13 methods, all in backend/app/core/llm.py
  (no service or chain module outside viral_analysis.py calls it)

$ codegraph callers "DataManager" --path G:\workbuddy_project\topicai
  0 results

$ codegraph query "user_feedback" --path G:\workbuddy_project\topicai
  1 result: frontend/src/hooks/useFeedback.ts (no SQL table)

$ codegraph query "effect_reviews" --path G:\workbuddy_project\topicai
  2 results: backend/app/models/effect_review.py and a TS interface
  (no SQL table, no migration)

$ codegraph files --pattern "**/migrations/**" --path G:\workbuddy_project\topicai
  0 results (entire directory missing)

$ codegraph query "/risk/check" --path G:\workbuddy_project\topicai
  0 results (endpoint not registered)

$ codegraph impact "IdeaBoosterService.boost" --path G:\workbuddy_project\topicai
  12 affected symbols (the method, its helpers, the API route, 3 tests)
```

These queries are reproducible on any machine with the bundled
`codegraph` CLI installed; the index is at
`G:\workbuddy_project\topicai\.codegraph\codegraph.db`.
