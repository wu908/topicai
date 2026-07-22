# Phase 12-15 Action Protocol Release Matrix

**Date**: 2026-07-22

**Status**: Complete; T049 and T050 are covered

## Decision

Phase 12 validates user journeys against the persisted action protocol. Existing unit tests are evidence only when they exercise the same production service and state transitions. Missing product capabilities remain explicit blockers and are not replaced by mocks or documentation-only checks.

## T049 Journey Matrix

| Journey | Action-protocol evidence | Status | Remaining gap |
|---|---|---|---|
| Growth creator | `test_growth_creator_completes_confirmed_learning_loop` and `intent-driven-loop.spec.ts` cover Today, project creation, intent confirmation, evidence interview, immutable version lock, manual publication, intent-specific metrics, blind review, explicit long-term-learning confirmation and one persisted next experiment | Covered | None for this journey; real-user outcome validation remains separate |
| Starter creator | `test_starter_service.py`, `test_starter.py`, `StarterPage.test.tsx`, and `starter-flow.spec.ts` cover readiness, privacy exclusions, <=3 grounded directions, one selected 14-day experiment, three idempotent linked projects, shared `confirm_intent` actions, sprint progress and bounded review | Covered | Real-user outcome validation remains separate |

Both entry paths now converge on the same persisted `ContentProject` and `NextBestAction` lifecycle. The starter path does not introduce a second content workflow.

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
| Entity deletion | `test_growth_creator_completes_confirmed_learning_loop`; `test_project_deletion_is_owner_scoped`; `phase-14-project-deletion.md` | Permanently remove owner-scoped project content, invalid derived context and orphan traces; retries do not disclose resource existence | Covered |
| Calibration contamination | `test_contamination_invalidates_review_and_blocks_observation` | Mark review invalid and prevent observation/rule promotion | Covered |
| Rule rollback | `test_creator_rule_requires_two_observations_and_supports_activation_and_rollback` | Restore the prior active version and preserve append-only history | Covered |

T050 is complete. Every listed recovery journey now has executable evidence.

## Validation Evidence

- Backend release matrix: 45 passed on Windows with Python 3.13, including starter entry, the complete confirmed learning loop, and project deletion.
- Frontend Vitest: 363 passed and 2 skipped; lint and production build passed.
- Intent-driven Playwright journey: 2 passed, including real browser offline recovery, publication-to-learning confirmation and the 390 x 844 mobile navigation check.
- Starter Playwright journey is implemented. This sandbox rejected Chromium launch with `spawn EPERM`; service/API and component journeys remain green, and the browser test must run in CI or an unsandboxed local session.
- Rendered desktop QA reached the persisted next experiment without an application console error. The remaining console warnings are React Router v7 future-flag notices.

## Commands

Backend matrix:

```bash
python -m pytest -q \
  tests/api/v2/test_intent_driven_actions.py \
  tests/api/v2/test_publish_hypothesis.py \
  tests/services/test_calibration_loop.py \
  tests/services/test_starter_service.py \
  tests/api/v2/test_starter.py \
  --basetemp=.ci-tmp/phase-12-release
```

Frontend matrix:

```bash
pnpm --dir frontend lint
pnpm --dir frontend build
pnpm --dir frontend test
pnpm --dir frontend test:e2e -- intent-driven-loop.spec.ts
```

## Result

T049 and T050 are complete. Product outcome validation still requires real starter and growth creators; synthetic tests prove workflow and safety invariants, not user demand or growth outcomes.
