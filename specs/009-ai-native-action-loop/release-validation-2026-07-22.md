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
- Full no-model, timeout, offline recovery, conflict, deletion, contamination, and rollback release matrix.
- Benchmark inclusion/exclusion and all invalid-review eligibility rules.

## Phase 11 Instrumentation Addendum

The MVP now has internal, owner-scoped instrumentation for E1-E4 experiment assignments and action/calibration exports. This closes the previous schema and denominator gap, not the experiments themselves.

| Contract | Implemented behavior |
|---|---|
| Experiment assignment | E1-E4 only; control, variant, observational, or excluded cohort; starter, growth, or unknown segment; one active experiment per owner |
| Assignment audit | Every explicit assignment and automatic completion is append-only and idempotent |
| Action context | Experiment, cohort, trace, latency, success, error, model, and prompt fields are available; action/event triggers freeze active context |
| Stable denominator | Distinct actions with `proposed` inside `[start_at, end_at)` UTC; actions offered outside the window are excluded |
| Missing data | Zero denominators return `null`; missing latency is counted and never imputed |
| Privacy | Export never selects `payload_json` or product content; user ID is pseudonymized; access remains authenticated and owner-scoped |
| Calibration quality | Reports clean-valid reviews, contamination, rule-upgrade eligibility, observation states, and rule-version states |

Focused validation:

- Experiment metrics API and privacy contracts: 5 passed.
- Migration and schema authority contracts: 26 passed.

No real-user experiment data exists yet. E1-E4 remain hypotheses and must not be presented as validated product outcomes.

## Decision

The intent-driven MVP vertical slice is suitable for controlled local user validation after rendered QA. It is not yet suitable for a claim of full Spec 009 completion or production-grade autonomous operation.

## Phase 12 Recovery Addendum

Phase 12 adds local draft recovery and verifies deterministic fallback after model timeout or malformed structured output. The current evidence and blockers are maintained in `phase-12-release-matrix.md`.

The rendered release pass also exposed and fixed concurrent `NextBestAction` creation during overlapping project-list and calibration requests. Creation is now transactional and conflict-safe, with regression coverage that rejects duplicate actions, events and orphan traces.

Phase 13 closes the executable growth publication-to-learning journey through explicit user confirmation and one persisted next experiment. The release matrix remains open because the starter entry flow and v2 deletion/cascade contract are still missing product capabilities.

# Phase 14 Update

- Added the owner-scoped permanent `ContentProject` deletion contract and API.
- Extended the complete growth journey through deletion, deterministic retry and cross-owner isolation.
- Verified removal of raw project content, project-derived rules, series, opportunities, CreatorState references, orphan traces and project-only screenshots.
- Phase 12-14 backend release matrix: `33 passed`.
- Backend CI equivalent: `761 passed`, `1 deselected`, `86.54%` coverage.
- T050 is complete. T049 remains open until the bounded starter journey exists.
