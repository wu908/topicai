# Research: 007 TopicAI v4.1 Implementation-Gap Closure

**Feature**: 007-v4-gap-closure
**Date**: 2026-06-12
**Audit source**: codegraph v0.9.9 (225 files, 2,142 nodes, 3,644 edges)
**Source spec**: [spec.md](./spec.md)
**Source plan**: [plan.md](./plan.md)

This document captures the design decisions reached during Phase 0 of
the speckit-plan workflow. Each section states the decision, the
rationale, and the alternatives that were considered. The decisions
are scoped narrowly to this 007 spec; the broader 006 roadmap's
research lives at `specs/006-topicai-v4-roadmap/research.md`.

## D1: Heuristic-first LLM invocation (kept from 006 D1)

- **Decision**: All four coach services keep the existing heuristic
  pipeline as the `template_fallback` path and add an LLM path that
  calls `LLMClient.generate` (or `generate_structured` for the
  schema-validated coach outputs). The router's response always
  returns 200; the `data_source` field tells the UI which path
  served the answer.
- **Rationale**: Constitution Principle VI mandates
  heuristic-first hybrid AI; this also keeps p95 latency and token
  spend bounded. The heuristic path is already shipping (the
  current code), so the failure path is correct by construction;
  the new code only adds the success path.
- **Alternatives considered**:
  - "Always call LLM" rejected on cost, latency, and Constitution V
    (YAGNI).
  - "Replace the heuristic with a real LLM-only path" rejected
    because the heuristic path is the only one that works without
    a key; a key-less developer would see a 5xx instead of 200.

## D2: 4-tier data source with per-tier config (kept from 006 D2)

- **Decision**: Reuse the existing `DataManager` orchestration; move
  per-tier timeout / retry / circuit-breaker config from inline
  constants into a `TierConfig` dataclass in
  `config/data_source_config.py`. Defaults: timeout 3s, retry 1,
  circuit opens after 3 consecutive failures, half-opens after 30s.
- **Rationale**: Constitution Principle VIII requires explicit
  per-tier config. Centralizing in one place makes it auditable
  and lets tests inject fault scenarios deterministically.
- **Alternatives considered**:
  - "Use a library like `pybreaker`" rejected under YAGNI
    (Principle V) for ~30 lines of code.
  - "Per-tier daemon threads" rejected because the call sites are
    already async; mixing a sync circuit breaker into async code
    is more confusing than helpful.

## D3: Persistence migration strategy

- **Decision**: Create `backend/app/data/migrations/` with a
  numbered SQL file per new table. The runner applies pending
  migrations on app startup (wired in `main.py` lifespan) and
  records each in `schema_migrations` (Quality Gate 8). The
  001-005 sequence bootstraps the system:
    - `001_bootstrap.sql` -- `schema_migrations` table.
    - `002_user_feedback.sql` -- US3.
    - `003_effect_reviews.sql` -- US4.
    - `004_risk_keywords.sql` -- US5.
    - `005_platform_tokens.sql` -- prep for 006 OAuth.
- **Rationale**: Constitution Quality Gate 8 mandates
  `NNN_<topic>.sql` with idempotent `IF NOT EXISTS` and a
  tracking table. The existing `app/core/database.py` already
  calls `init_db()` from the lifespan; the migration runner is
  added alongside it.
- **Alternatives considered**:
  - "Use Alembic" rejected under YAGNI (Principle V); the existing
    SQLAlchemy `Base.metadata.create_all` call in `init_db()` is
    enough for the dev environment, and the explicit SQL files are
    what production needs.
  - "Inline CREATE TABLE in service code" rejected as a Quality
    Gate 8 violation.

## D4: LLM mock pattern (canonical, kept from 006 + Constitution)

- **Decision**: For every service that calls the LLM, tests use
  the canonical mock pattern from Constitution Principle II:
  `mock LLMClient.generate` returning fixed JSON, with separate
  tests for the LLM success path, the LLM exception fallback
  path, oversized input truncation, and malformed-JSON recovery.
  The fallback test asserts the *same* Pydantic schema returns
  and that `data_source` differs from the LLM path and
  `confidence` is lower.
- **Rationale**: This is the canonical pattern codified in
  Constitution v1.1.0 (line 80 of
  `.specify/memory/constitution.md`). Reusing it verbatim avoids
  drift and makes the test suite legible to anyone familiar with
  the constitution.
- **Alternatives considered**:
  - "Use a recorded-response fixture" rejected because the
    fallback path requires that the LLM raises, which is easier
    to express as a `side_effect` than a fixture.
  - "VCR cassettes" rejected under YAGNI (Principle V); the
    canonical mock pattern is 5 lines.

## D5: Coverage gate enforcement

- **Decision**: Add `--cov-fail-under=80` to
  `backend/pyproject.toml`'s `addopts` and add
  `coverage.thresholds.lines = 80` to
  `frontend/vitest.config.ts`. The gate runs on every CI build.
  Local developers can use `pytest --no-cov` for fast iteration
  if they explicitly opt out.
- **Rationale**: Constitution Quality Gate 7 mandates the 80%
  floor. Without the CI wiring, the floor is unenforceable and
  the prior 99-task roadmap's "regression-proof" promise is
  hollow.
- **Alternatives considered**:
  - "Per-module thresholds" rejected as over-engineered for the
    scope of this 007 spec.
  - "Allow the floor to be temporarily lowered" rejected as a
    Constitution violation (Quality Gate 7 is non-negotiable).

## D6: Frontend test surface (out of scope)

- **Decision**: This 007 spec does not add new Vitest unit tests
  beyond what the backend coverage gate requires. The existing 7
  frontend test files and 4 Playwright `.spec.ts` files at
  `frontend/e2e/` are unchanged. The new E2E scenario
  (`e2e/full-loop.spec.ts`, task T-088) is the only new frontend
  test artifact.
- **Rationale**: Constitution Quality Gate 7 sets a coverage
  floor, not a target. The frontend's user-visible surface is
  the four coach pages (already covered by existing unit tests
  for `useFeedback` and the layout components); the gap in
  test coverage is the *backend* (which is the focus of this
  spec), not the frontend.
- **Alternatives considered**:
  - "Add Vitest tests for every new component" rejected as
    over-spec; the existing Playwright scenario covers the
    end-to-end flow.

## D7: Sandbox .git ACL limitation

- **Decision**: The work is preserved on disk at
  `specs/007-v4-gap-closure/` but cannot be committed or
  branched in this sandbox. The `.git/refs/heads/` directory has
  explicit `DENY (W,D,Rc,DC)` ACLs that block the
  `speckit.git.feature` hook.
- **Rationale**: Per the speckit skill ("the spec directory name
  and the git branch name are independent"), the spec lives
  independently of the branch. A maintainer with the
  `BUILTIN\Administrators` ACE (visible in `icacls
  G:\workbuddy_project\topicai\.git\refs`) can create the
  branch from the working tree and commit the spec.
- **Alternatives considered**:
  - "Work around the ACL with `git update-ref`" rejected because
    the deny rule blocks all writes to `.git/refs/`, not just
    `index.lock`.
  - "Use a different VCS" out of scope.
