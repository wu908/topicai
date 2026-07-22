# Phase 10 MVP Closure Validation

**Date**: 2026-07-22
**Branch**: `agent/phase-10-mvp-closure`
**Scope**: Intent-driven Xiaohongshu MVP closure, not full Spec 009 completion

## Release Boundary

This validation covers the first usable intent-driven vertical slice:

1. A creator creates a `solve`, `share`, or `record` content project.
2. The system confirms intent and asks for missing evidence before drafting.
3. A no-model fallback can prepare a candidate without inventing user facts.
4. The creator confirms candidate segments and locks a publish version.
5. Automation stops before publication.
6. Today selects one deterministic next action across active projects and pending series opportunities.

The validated product navigation is `今日 | 内容 | 机会 | 素材 | 我的`. Legacy standalone-tool routes are compatibility redirects and are not part of the primary product surface.

## Automated Evidence

| Area | Command or suite | Result |
|---|---|---|
| Backend CI equivalent | `python -m pytest -q -k "not test_scenario_g_coverage_gate" --cov=app --cov-report=term-missing --cov-report=xml --cov-fail-under=80` | 746 passed, 1 deselected; 86.68% coverage |
| Frontend unit tests | `pnpm --dir frontend test` | 353 passed, 2 skipped across 53 files |
| Frontend lint | `pnpm --dir frontend lint` | Passed |
| Frontend production build | `pnpm --dir frontend build` | Passed |
| Intent-driven browser journey | `frontend/e2e/intent-driven-loop.spec.ts` | 2 passed: desktop workflow and 390 x 844 navigation |
| Patch hygiene | `git diff --check` | Passed |

The browser journey verifies login, `share` project creation, intent confirmation, evidence interview, user-fact confirmation, deterministic no-model candidate preparation, segment confirmation, version lock, and the pre-publication automation boundary.

## Cross-Artifact Consistency

| Contract | Expected | Validation status |
|---|---|---|
| Product scope | Xiaohongshu knowledge/experience creators; stable publishing and learning | Consistent across the route graph, login positioning, Today and project workspace |
| Primary navigation | Five nodes only | Implemented in `Sidebar`; old tool routes redirect |
| Content intent | `solve`, `share`, `record` | Shared by backend contracts, project creation and the workspace flow |
| Primary action | One ranked action across active work | Implemented by `IntentOrchestratorService.today` |
| Series continuation | Opportunity is proposed, never silently accepted | Reuses auditable `create_project` action with `source=series_opportunity` |
| Evidence boundary | Confirm user evidence before factual candidate generation | Covered by service tests and the no-model browser journey |
| Automation boundary | Never auto-publish | Browser journey verifies the locked version still requires user publication |
| Legacy tools | Not visible in the production route graph | Routes redirect to the five-node product |

## Rendered QA Checklist

The following checks are completed against the local backend and frontend before branch delivery:

- Login renders without unsupported platform, social-login, password-reset, or legal-link claims.
- Today exposes one understandable primary action and a manual fallback.
- Opportunities has a truthful empty state and does not fabricate hotspot data.
- Materials distinguishes confirmed evidence from project requirements.
- My shows automation eligibility without an unsupported autopilot switch.
- The content workspace remains understandable before publication.
- Desktop and 390 x 844 layouts have no blocking overlap, blank screen, or framework error overlay.
- Relevant browser console errors are absent.

## Known Non-Blocking Warnings

- React Router emits existing v7 future-flag warnings in tests.
- Backend SQLite tests emit existing `ResourceWarning` messages.

Neither warning changes the validated MVP behavior or current CI result.

## Open Scope

This report does not close the full Spec 009 completion gate. The following remain open and must not be represented as shipped:

- Complete action `failed`, `expired`, and `cancelled` lifecycle behavior.
- Deletion and export guarantees for every new entity and dependent reference.
- Experiment/cohort instrumentation and action metrics with stable denominators.
- Full no-model, timeout, offline recovery, conflict, deletion, contamination, and rollback release matrix.
- Benchmark inclusion/exclusion and all invalid-review eligibility rules.

## Decision

The intent-driven MVP vertical slice is suitable for controlled local user validation after rendered QA. It is not yet suitable for a claim of full Spec 009 completion or production-grade autonomous operation.
