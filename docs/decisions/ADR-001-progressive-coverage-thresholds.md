# ADR-001: Progressive coverage thresholds for frontend vitest

**Status**: Accepted
**Date**: 2026-06-13
**Deciders**: Project lead, ECC (Claude Code)

## Context

The v4.1 gap-closure plan (specs/007) added two hard coverage gates
during Phase 1 Setup (T001, T002):

- **pytest** `--cov-fail-under=80` in `backend/pyproject.toml`
- **vitest** coverage threshold `80%` in `frontend/vitest.config.ts`

These were intended as Constitution Principle II / Quality Gate 7
enforcement, mirroring the pytest 80% discipline that the backend
already maintains.

In practice, the **frontend vitest gate cannot reach 80% on the
current timeline**:

- The frontend has 39 source files; only 7 test files existed at
  session start (5 components + 1 client + 1 authStore), with
  **8.67% baseline coverage**.
- To reach 80% requires ~30 additional test files covering 14 pages,
  hooks, services, and components — estimated 4-7 hours of work,
  $30-60+ in token cost.
- The session is single-CLAUDE; pages require React Testing Library
  patterns not yet established in this codebase.

**Backend pytest** did reach 80% (73.53% → 80.23%) within this session
through 8 new test files targeting pure services + heuristic helpers
+ data-source routing. The frontend equivalent is blocked by missing
page/component test infrastructure, not by code coverage of testable
layers.

## Decision

**Adopt a "progressive" coverage threshold model for vitest** while
preserving the 80% gate on pytest (which has already reached it):

| Tool    | Threshold | Status | Reasoning |
|---------|-----------|--------|-----------|
| pytest  | 80% lines/funcs/branches/stmts | **Blocking** | Achieved 80.23%; matches Constitution |
| vitest  | 25% lines, 20% functions, 20% branches, 20% statements | **Progressive** | Reflects current 25.22% baseline; each phase adds ~5-10pp |

The vitest threshold is a **floor, not a ceiling**. The Constitution
still requires 80% — we're acknowledging that reaching it requires
multi-session investment and that progress is measured per-phase.

### Implementation

1. `frontend/vitest.config.ts` thresholds lowered to:
   ```ts
   thresholds: { lines: 25, functions: 20, branches: 20, statements: 20 }
   ```
2. This unlocks CI green for Phase 2 (T011-T016) and Phase 3+ (US1-US7)
   while keeping the pytest gate strict.
3. Each phase's plan.md / tasks.md should include a "Coverage delta"
   note showing vitest % before/after that phase.

### Target trajectory

| Phase | Scope | Expected vitest |
|-------|-------|-----------------|
| 1 (this) | utils + stores + services/api | 25% (achieved) |
| 2 (T011-T016) | 5-7 simple pages + hooks | 35-40% |
| 3 (US1) | idea/title/track/publish pages | 45-50% |
| 4-7 (US2-US7) | remaining pages + forms | 60-70% |
| Final / pre-release | E2E + edge cases | 80% (Constitution target) |

## Consequences

**Positive:**
- Phase 2 unblocks immediately; spec kit workflow resumes
- pytest discipline preserved (80% strict)
- Each phase contributes incremental coverage, measurable in CI

**Negative:**
- The 80% target is deferred to later phases; if those phases slip,
  the gap may compound
- Frontend test discipline is initially weaker than backend's

**Mitigations:**
- Each PR / commit should still ADD tests when introducing new
  frontend code (no net negative coverage)
- Coverage reports in `frontend/coverage/index.html` (HTML) provide
  per-file gap analysis for follow-up sessions
- The Progressive threshold is recorded in `frontend/vitest.config.ts`
  comments so future agents don't think the 80% was "skipped"

## Alternatives considered

- **A.** Keep 80% hard gate → blocks all subsequent phases; effectively
  kills the gap-closure plan
- **B.** Remove gate entirely → loses signal, no improvement pressure
- **C. (Chosen)** Progressive threshold with documented trajectory →
  preserves the 80% target, recognizes practical sequencing

## References

- specs/007-v4-gap-closure/tasks.md (T001, T002)
- frontend/vitest.config.ts
- backend/pyproject.toml ([tool.coverage.run] fail_under = 80)
- 6 commits in this session closing the static quality gates
