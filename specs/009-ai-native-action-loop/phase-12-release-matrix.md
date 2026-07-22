# Phase 12-13 Action Protocol Release Matrix

**Date**: 2026-07-22

**Status**: In progress; T049 and T050 remain open

## Decision

Phase 12 validates user journeys against the persisted action protocol. Existing unit tests are evidence only when they exercise the same production service and state transitions. Missing product capabilities remain explicit blockers and are not replaced by mocks or documentation-only checks.

## T049 Journey Matrix

| Journey | Action-protocol evidence | Status | Remaining gap |
|---|---|---|---|
| Growth creator | `test_growth_creator_completes_confirmed_learning_loop` and `intent-driven-loop.spec.ts` cover Today, project creation, intent confirmation, evidence interview, immutable version lock, manual publication, intent-specific metrics, blind review, explicit long-term-learning confirmation and one persisted next experiment | Covered | None for this journey; real-user outcome validation remains separate |
| Starter creator | No starter assessment, direction candidate, sprint service, API or page exists in the current repository | Blocked | Implement the bounded starter entry flow, then hand its created projects to the same `NextBestAction` protocol |

The existing `starter_sprint_id` column is an extension point, not a working starter journey. T049 must remain unchecked until both rows pass.

## T050 Recovery Matrix

| Scenario | Automated evidence | Expected invariant | Status |
|---|---|---|---|
| No model | `test_growth_creator_completes_confirmed_learning_loop`; `intent-driven-loop.spec.ts` | Confirmed user evidence produces a marked deterministic candidate and never invents facts | Covered |
| Model timeout | `test_model_failure_after_fact_confirmation_preserves_input_and_uses_fallback[TimeoutError]` | Preserve confirmed input and return the same reviewable fallback candidate | Covered |
| Malformed model output | `test_model_failure_after_fact_confirmation_preserves_input_and_uses_fallback[ValueError]` | Preserve confirmed input and return the same reviewable fallback candidate | Covered |
| Concurrent workspace loads | `test_concurrent_project_action_creation_is_idempotent`; `test_concurrent_opportunity_action_creation_is_idempotent` | Concurrent project or series-opportunity reads create one action, one proposed event and one referenced AI trace without returning 500 | Covered |
| Concurrent HumanGate opens | `test_growth_creator_completes_confirmed_learning_loop`; `intent-driven-loop.spec.ts` | Concurrent requests for the same action and gate type return one persisted HumanGate without a uniqueness-index 500 | Covered |
| Offline editing and refresh | `ProjectWorkspace.test.tsx`; `intent-driven-loop.spec.ts` | Keep edits local, make no server save while offline, offer recovery after reload, and require user confirmation | Covered |
| Version conflict | `test_stale_project_version_returns_typed_conflict`; candidate and rule version-conflict tests | Reject stale writes without overwriting the current version | Covered |
| Revoked evidence | `test_revoked_evidence_blocks_candidate_lock` | Revoked evidence cannot lock an unpublished candidate | Covered |
| Entity deletion | No v2 project/evidence deletion API or cascade contract exists | Delete or anonymize dependent actions, gates, traces and context without retaining user content | Blocked |
| Calibration contamination | `test_contamination_invalidates_review_and_blocks_observation` | Mark review invalid and prevent observation/rule promotion | Covered |
| Rule rollback | `test_creator_rule_requires_two_observations_and_supports_activation_and_rollback` | Restore the prior active version and preserve append-only history | Covered |

T050 remains unchecked because revocation is not equivalent to deletion. The release gate requires a real v2 deletion contract and cascade test.

## Validation Evidence

- Backend release matrix: 32 passed on Windows with Python 3.13, including the complete confirmed learning loop.
- Frontend Vitest: 357 passed and 2 skipped; lint and production build passed.
- Intent-driven Playwright journey: 2 passed, including real browser offline recovery, publication-to-learning confirmation and the 390 x 844 mobile navigation check.
- Rendered desktop QA reached the persisted next experiment without an application console error. The remaining console warnings are React Router v7 future-flag notices.

## Commands

Backend matrix:

```bash
python -m pytest -q \
  tests/api/v2/test_intent_driven_actions.py \
  tests/api/v2/test_publish_hypothesis.py \
  tests/services/test_calibration_loop.py \
  --basetemp=.ci-tmp/phase-12-release
```

Frontend matrix:

```bash
pnpm --dir frontend lint
pnpm --dir frontend build
pnpm --dir frontend test
pnpm --dir frontend test:e2e -- intent-driven-loop.spec.ts
```

## Next Implementation Order

1. Define v2 deletion scope, retention exceptions and cascade behavior before writing endpoints.
2. Implement the bounded starter assessment and three-project experiment as an entry flow, not a second content lifecycle.
3. Re-run this matrix and only then close T049/T050.
