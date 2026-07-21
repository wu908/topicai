# Specification Analysis Report

**Feature**: `008-content-project-mvp`  
**Artifacts**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/api-v2.md`, `quickstart.md`, `tasks.md`, Constitution v2.0.0  
**Analysis date**: 2026-07-17

## Findings

| ID | Category | Severity | Status | Location(s) | Summary | Resolution / Recommendation |
|---|---|---|---|---|---|---|
| C1 | Constitution | CRITICAL | Resolved | Constitution v1.1.0 principles IV, VIII, IX | Old governance required fixed vendors, LLM-simulated hotspots, preloaded trend fallback, and predictive review. | Constitution amended to v2.0.0 before planning; plan gate now passes all principles. |
| I1 | Inconsistency | HIGH | Resolved | US2 in `spec.md`; Phase 4 in `tasks.md` | Core-project story required publication, while initial tasks ended at a publish candidate. | T049-T050, T055-T058, T061, and T064 now include baseline checks, suggestions, version lock, and manual publication; US6 remains the transparency/export enhancement. |
| D1 | Data coverage | HIGH | Resolved | FR-005; `data-model.md` | History import originally lacked persistent import and imported-note entities. | Added `HistoryImport` and `ImportedNote`; migration T027 now creates their tables and profile reconciliation. |
| I2 | Interface coverage | MEDIUM | Resolved | US8; `contracts/api-v2.md` | Weekly goal/account reference/AI capability status had UI tasks but no explicit settings API. | Added `GET/PUT /settings`; T119-T124 cover service/API tests and implementation. |
| I3 | AI audit coverage | MEDIUM | Resolved | FR-019; foundation tasks | AITrace had schema/migration coverage but no explicit persistence service. | T009, T032 now require AITrace service tests and persistence. |
| F1 | Formatting | MEDIUM | Resolved | `spec.md` requirements section | Patch-style leading `+` markers would have broken Markdown parsing and requirement counting. | Removed markers; counts now resolve to 35 FRs and 10 SCs. |
| B1 | Baseline evidence | MEDIUM | Outstanding, planned | `baseline-results.md` not yet created | Source test run was affected by read-only temp DB/storage/coverage paths and one integration assertion; copied-workspace baseline is not yet authoritative. | T001-T002 are the first implementation tasks and block feature coding until exact results are recorded. |
| R1 | Runtime docs | LOW | Outstanding, planned | root/backend/frontend README and env examples | Copied runtime documentation still describes the old provider and hotspot stack. | T008, T012, T143-T144 update docs/config only when matching implementation lands, preventing false documentation. |

No unresolved CRITICAL or HIGH issue remains in the planning artifacts.

## Requirement Coverage

| Requirement group | Covered by tasks | Notes |
|---|---|---|
| FR-001 authentication/isolation | T001, T017, T032, T077, T120 | Reuses v1 auth; v2 owner tests remain mandatory. |
| FR-002-FR-004 dual entry and starter experiment | T065-T074, T134, T137 | Candidate limit, readiness, three projects, and review are explicit. |
| FR-005-FR-006 history/profile | T027, T075-T083 | Partial import, dedupe, evidence, rejection, and confirmation covered. |
| FR-007-FR-010 navigation/Today/project aggregate | T036-T064, T128-T130, T139 | Five nodes, resume task, states, recovery, and aggregate shell covered. |
| FR-011-FR-015 explainable opportunities/source integrity | T084-T094, T140 | No predictive fields or legacy source imports. |
| FR-016-FR-021 brief/interview/AI/versioning | T047-T064 | Evidence gaps, suggestions, immutable versions, recovery, and AI failure paths covered. |
| FR-022-FR-025 publish checks/manual publication | T048-T050, T056, T058, T064, T095-T105 | Baseline publication in US2; richer transparency/export in US6. |
| FR-026-FR-029 snapshots/review/insights | T106-T117 | Manual and confirmed screenshot data, append-only correction, three actions, confirmed learning. |
| FR-030 materials | T023, T118, T122, T126 | Lightweight kinds, privacy, usages, and locked references. |
| FR-031 immutable feedback | T016, T026, T030, T064, T091, T114 | Generic target adapter plus decisions across output types. |
| FR-032 failure/recovery states | Story test-first tasks, T135-T139 | Loading, partial, timeout, conflict, offline, and responsive paths covered. |
| FR-033 export/deletion | T119-T127 | Credential revocation, job state, files, and user data covered. |
| FR-034 scope limits | T128-T132, T139-T140 | Team/matrix paths removed from active reachability; one-platform assumptions tested. |
| FR-035 legacy migration | T128-T132 | Frontend redirects and typed v1 deprecation shims. |

## Success-Criteria Coverage

| Criterion | Tasks |
|---|---|
| SC-001 both onboarding paths reach action | T133-T137 |
| SC-002 core loop decision count | T133, T136, T147 |
| SC-003 Today <=2 interactions | T036-T045, T136 |
| SC-004 AI provenance/control 100% | T009, T018, T032, AI tests in each story |
| SC-005 hotspot source integrity 100% | T084-T094, T140 |
| SC-006 idempotent side effects | T016, T046-T050, T096, T106, T133-T134 |
| SC-007 state matrix | T015, T029, T046, T133-T134 |
| SC-008 navigation/responsive smoke | T039, T042-T044, T128, T139 |
| SC-009 fresh local deployment | T013-T014, T144, T147 |
| SC-010 >=80% coverage/no test loss | T001-T002, T145-T146 |

## Constitution Alignment

All 14 principles are addressed in `plan.md`. The v2 contract contains no permitted path for:

- fixed model-vendor selection in product code;
- LLM as a factual source;
- continuous hotspot/news aggregation;
- estimated heat, CTR, viral probability, or predicted performance;
- automatic profile-weight mutation;
- automatic publish or platform metric synchronization.

## Unmapped Tasks

No orphan implementation task was found. Setup, documentation, scans, compatibility, and release tasks map to Constitution gates, migration safety, or measurable success criteria even when they do not carry a user-story label.

## Metrics

- User stories: 8
- Functional requirements: 35
- Buildable success criteria: 10
- Tasks: 148
- Task IDs: continuous T001-T148; no duplicates
- Task format compliance: 148/148
- Requirement groups with at least one task: 35/35 (100%)
- Success criteria with at least one task: 10/10 (100%)
- Relative Markdown links: all resolved
- Placeholder or `[NEEDS CLARIFICATION]` markers: 0
- Critical issues outstanding: 0
- High issues outstanding: 0
- Medium issues outstanding: 1 (writable-copy baseline, intentionally first implementation gate)

## Next Actions

1. Begin T001-T002 only; record a trustworthy writable-copy baseline.
2. Do not implement user stories if baseline permission failures or the integration assertion remain unexplained.
3. Continue in task order through foundation; use CodeGraph before changing existing symbols.
4. Re-run this analysis after T148 with actual code/contracts/OpenAPI and resolve every CRITICAL/HIGH issue before release.
