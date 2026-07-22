# Phase 17: Completion Gate Audit

**Date**: 2026-07-22

**Status**: Complete; implementation gaps remain

## Decision

Phase 16 closes the action lifecycle, but Spec 009 is not complete. The task
list contained 16 unchecked items. This audit closes two stale entries and
keeps fourteen open because their full acceptance condition is not yet backed
by executable evidence.

## Audit Result

| Task | Result | Evidence or remaining gap |
|---|---|---|
| T001 | Open | Domain tables exist, but there is no complete typed contract for every named entity. Do not count dictionary-shaped SQL rows as typed models. |
| T003 | Complete | Migrations 019, 020, 021 and 028 persist traces, state, actions, gates, events, evidence and experiments; migration replay is tested. |
| T005 | Open | Project deletion covers project-derived records, and the metrics export is owner-scoped, but there is no complete owner data export/deletion matrix for every new entity. |
| T011 | Open | AI traces are persisted and actions reference them, but trace creation is duplicated across services; the required `AITraceService` contract does not exist. |
| T012 | Open | `HumanGateService` supports intent, user fact, content version and long-term learning paths. Privacy and deletion gates are not implemented as first-class decisions. |
| T013 | Open | The new orchestrator currently has no imports or calls to legacy hotspot sources, but there is no executable source-integrity test preventing regression. |
| T014 | Open | Timeout, malformed-output and manual fallback tests exist. Missing-capability and permission/expired-source fallback evidence is incomplete. |
| T018 | Complete | Migration 028 freezes experiment/cohort context on actions and events; the privacy-safe metrics tests verify the exported context and stable denominator. |
| T027 | Open | C-01 through C-04 are not defined by ID in the current spec artifacts and therefore cannot be claimed as an executable named matrix. |
| T028 | Open | Version confirmation and publication actions are version-bound, but publication/public-scope gate behavior and trace binding need one explicit acceptance matrix. |
| T032 | Open | Long-term learning confirmation creates an Observation and rejection does not write it. The named insight-to-ContentGenome update contract is not fully specified or tested. |
| T033 | Open | C-05 through C-07 have the same missing named-scenario contract as T027. |
| T034 | Open | PublishHypothesis, BlindReview, Observation, CreatorRule and RuleVersion exist. `BenchmarkSample` has no v2 typed model or migration. |
| T036 | Open | Locked hypotheses are immutable, but append-only post-lock amendments are not implemented. |
| T039 | Open | Contaminated and insufficient reviews are ineligible. Revoked-evidence and legacy-review invalidation need explicit persisted eligibility behavior and tests. |
| T042 | Open | Missing metrics remain unknown in blind review, but `BenchmarkSample` inclusion/exclusion does not exist. |

## Remaining Work Packages

The fourteen tasks are grouped into four implementation packages instead of
fourteen artificial phases:

1. **Contracts and provenance**: T001, T011, T013 and the remaining T014 cases.
2. **Trust boundaries and privacy**: T005, T012, T028 and T032.
3. **Synthetic acceptance matrix**: define and automate C-01 through C-07 for T027 and T033.
4. **Calibration completeness**: T034, T036, T039 and T042.

Package order is intentional. Calibration types and migrations should not be
added until their inclusion, exclusion and invalidation behavior is frozen by
the acceptance matrix.

## Ponytail Review

No Phase 16 abstraction or dependency can be safely removed. SQLite cannot
alter an existing `CHECK` constraint, so migration 030 must rebuild the two
constrained tables and restore indexes and triggers. Shortening that post-step
would trade visible lines for an unsafe database upgrade.

## Exit Condition

Phase 17 is complete when the stale task statuses are corrected and every open
item is assigned to exactly one package. Spec 009 remains incomplete until all
four packages and the final release validation are green.
