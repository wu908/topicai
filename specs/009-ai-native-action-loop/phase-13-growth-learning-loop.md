# Phase 13 Growth Learning Loop

**Date**: 2026-07-22

**Status**: Complete; T049 remains open for the starter creator journey

## Decision

Phase 13 completes the growth creator journey through confirmed post-publication learning. It reuses the existing publication, snapshot, blind review, HumanGate and Observation services rather than introducing a parallel lifecycle.

The product boundary remains unchanged:

- TopicAI never publishes on the user's behalf.
- Observed metrics are facts, not causal explanations.
- One result cannot become a long-term creator rule.
- The reviewed next experiment is persisted only after explicit user confirmation.

## Executable Journey

```text
Today
→ confirm content intent
→ confirm first-party evidence
→ review and lock candidate content
→ record manual publication
→ enter intent-specific performance metrics
→ compare the locked hypothesis with observed results
→ review facts, possible causes, continue, stop and experiment
→ confirm the long-term-learning HumanGate
→ persist one Observation
→ advance to manage_learning
```

## Evidence

- Backend contract: `test_growth_creator_completes_confirmed_learning_loop`.
- Browser contract: `frontend/e2e/intent-driven-loop.spec.ts`.
- Backend release matrix: 32 passed.
- Frontend unit tests: 357 passed and 2 skipped.
- Frontend lint and production build: passed.
- Playwright: 2 passed, including the full growth loop and 390 x 844 navigation.

## Invariants Proven

- `record`, `share` and `solve` continue to use intent-specific review plans.
- The growth journey records only user-confirmed metrics.
- The blind review exposes facts separately from possible causes.
- The plan contains exactly one continue item, one stop item and one experiment item.
- No Observation exists before the `long_term_learning` gate is confirmed.
- Concurrent attempts to open the same HumanGate converge on one persisted gate without returning 500.
- Confirmation persists exactly one Observation and advances the orchestrated action to `manage_learning`.
- `long_term_write_allowed` remains false; a single project does not update a long-term creator rule.

## Remaining Gates

- T049 remains open until the bounded starter assessment, direction and three-project entry flow exists.
- T050 remains open until v2 deletion, retention and cascade behavior is implemented and tested.
- Real-user outcome validation remains required before making growth-effect claims.
