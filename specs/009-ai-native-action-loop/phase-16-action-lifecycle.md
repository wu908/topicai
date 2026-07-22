# Phase 16 Action Lifecycle And Recovery

**Date**: 2026-07-22

**Status**: Implemented and validated

## Decision

`NextBestAction` is not complete when only the successful path works. Every
active action now has explicit rejection, technical failure, expiry and
cancellation behavior with optimistic concurrency, idempotency and an audit
event.

The lifecycle is deliberately bounded:

```text
proposed/accepted/deferred
  -> completed/superseded
  -> failed/expired/cancelled
```

- `failed` and `expired` actions are terminal. The orchestrator creates one new
  retry action for the same current project state and retains the old event.
- `cancelled` is terminal and does not immediately reproduce the rejected
  suggestion. The manual fallback remains available. A project-version change
  permits orchestration to evaluate a new action.
- A user rejection records `rejected -> cancelled` and requires a reason.
- Failure events may store a bounded error code and safe reason, never a stack
  trace, raw model output or user content.
- Reading a due active action atomically marks it expired before replacement.
- A pending HumanGate cannot confirm an action after it becomes terminal or its
  expiry time passes.
- Explicit rejection and cancellation enter the existing rejection-rate
  numerator. Expiry does not masquerade as rejection or technical failure.

## Migration

Fresh databases receive the expanded constraints from migration 020. Existing
SQLite databases apply migration 030, whose runner post-step rebuilds
`next_best_actions` and `action_events`, restores their indexes and experiment
triggers, and runs `PRAGMA foreign_key_check` before completion.

## User Experience

Today shows one action with reason, evidence, unknowns, effort, expiry and the
expected result. A creator may defer it, continue manually, or reject it with a
reason. A rejected action remains visibly stopped instead of silently returning
as the same recommendation.

The project workspace falls back to the existing manual stage controls when its
AI action is cancelled. Technical failures and expiry recover to a new action,
so a project cannot be stranded by a dead orchestration record.

## Executable Evidence

- User rejection is idempotent and remains cancelled for the same project version.
- Technical failure records `success=0` plus a bounded error code and creates one recovery action.
- Due actions expire automatically and are replaced once.
- A simulated phase-15 database upgrades through the constraint-rebuild path with no foreign-key violations.
- Home requires a rejection reason and renders the stopped state.

Final validation:

- Backend CI equivalent: `779 passed`, `1 deselected`, `86.69%` coverage.
- Frontend Vitest: `364 passed`, `2 skipped` across 54 files.
- Frontend lint and production build: passed.
- Action, metrics and migration focused suites: passed.
