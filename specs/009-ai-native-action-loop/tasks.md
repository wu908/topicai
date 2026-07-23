# Tasks: TopicAI AI-native Action Loop

## Phase A - Contracts and persistence

- [x] T001 Add v2 typed models for `CreatorState`, `ContentGenome`, `Evidence`, `NextBestAction`, `AITrace`, `HumanGate`, `ActionEvent`, and `Experiment`.
- [x] T002 Add idempotency and optimistic-concurrency contracts for action lifecycle operations.
- [x] T003 Add migrations for state snapshots, evidence, actions, traces, gates, action events and experiments.
- [x] T004 Test fresh database migration, repeat migration, and upgrade from the 008 schema.
- [x] T005 Add owner-isolation and deletion/export coverage for every new entity.

## Phase B - Action policy and service

- [x] T006 Implement `CreatorStateService` with versioned snapshots and explicit uncertainty.
- [x] T007 Implement deterministic action eligibility by project status, blocker, urgency, capacity and evidence readiness.
- [x] T008 Implement action priority ordering and one-primary-action constraint.
- [x] T009 Implement `NextBestActionService` offer, accept, reject, execute, fail, expire and cancel operations.
- [x] T010 Enforce action idempotency and state-version checks in the service layer.
- [x] T011 Implement `AITraceService` and require traces for AI-generated actions.
- [x] T012 Implement `HumanGateService` for fact, version, publish, insight, privacy and deletion gates.
- [x] T013 Add source-integrity tests proving the action engine never calls legacy hotspot sources.
- [x] T014 Add timeout, malformed output, missing capability and manual fallback tests.

## Phase C - Today and project integration

- [x] T015 Replace the Today primary task calculation with the action service while preserving the five-node navigation.
- [x] T016 Build the primary action card with reason, evidence, expected result, effort, expiry and fallback.
- [x] T017 Add accept, skip, reject-with-reason, pause and manual-continue UI states.
- [x] T018 Add action event instrumentation with experiment and cohort fields.
- [x] T019 Link project list recovery to pending and failed actions.
- [x] T020 Add responsive and no-model UI tests for Today and action cards.

## Phase D - Evidence interview and creation

- [x] T021 Implement evidence-gap classification from Brief and ContentProject context.
- [x] T022 Implement targeted interview actions with per-answer confirmation.
- [x] T023 Bind evidence references to Brief fields and ContentVersion segments.
- [x] T024 Block fact-based complete drafts when evidence is insufficient unless the user chooses a marked generic structure.
- [x] T025 Implement evidence revocation and downstream invalidation.
- [x] T026 Implement candidate versions, segment acceptance/rejection, comparison and immutable confirmed versions.
- [ ] T027 Add synthetic scenario tests C-01 through C-04.

## Phase E - Publish, review and learning

- [x] T028 Create publish/version HumanGates and version-bound action traces.
- [x] T029 Connect manual publish record and performance snapshot actions to project state.
- [x] T030 Replace prediction semantics with fact/hypothesis/experiment review output.
- [x] T031 Create exactly one continue, stop and experiment action from a completed review.
- [x] T032 Add confirmed/rejected insight gates and ContentGenome update rules.
- [ ] T033 Add synthetic scenario tests C-05 through C-07.

## Phase F - Judgment calibration

- [ ] T034 Add typed models and migrations for `PublishHypothesis`, `BlindReview`, `Observation`, `CreatorRule`, `RuleVersion`, and `BenchmarkSample`.
- [x] T035 Implement atomic idempotent locking of publish version and minimum hypothesis.
- [ ] T036 Enforce immutable hypothesis snapshots and append-only post-lock amendments.
- [x] T037 Implement blind-review input allowlist and forbid post-hoc explanations during initial comparison.
- [x] T038 Add `AITrace.visibility_boundary`, source snapshot ids, contamination check, and calibration state.
- [ ] T039 Mark insufficient, contaminated, revoked-evidence, and legacy reviews as ineligible for rule upgrades.
- [x] T040 Implement Observation create, continue-testing, absorb, refute, archive, and workbench cleanup transitions.
- [x] T041 Implement CreatorRule candidate, full-sample reevaluation, consistency threshold, approval, rejection, rollback, and audit history.
- [ ] T042 Add BenchmarkSample inclusion/exclusion and unknown-metric handling without performance prediction.
- [x] T043 Extend Today with pending publication, pending review, active observation, refuted judgment, resumable-project summaries, and pending series opportunities.
- [x] T044 Add tests proving one sample cannot activate a rule and failed reevaluation leaves the active version unchanged.
- [x] T045 Add tests proving result leakage produces `calibration_invalid` and cannot influence future actions.

## Phase G - Experiments and release validation

- [x] T046 Add E1-E4 experiment and cohort assignment fields without storing raw content in analytics.
- [x] T047 Add metric queries with documented numerator, denominator, window and missing-data handling.
- [x] T048 Add action funnel and calibration-quality export for internal validation only.
- [x] T049 Run existing 008 starter and growth journeys against the action protocol.
- [x] T050 Run no-model, timeout, offline recovery, version conflict, deletion, contamination and rule-rollback journeys.
- [x] T051 Verify legacy routes redirect or become project-context compatibility shims.
- [x] T052 Run cross-artifact consistency checks and update the release validation report in `release-validation-2026-07-22.md`.

## Completion Gate

The feature is not complete until all P1 tasks are green, synthetic logic scenarios are automated, no confirmed content, hypothesis, insight, or active rule can be silently overwritten, contaminated calibration is blocked, the no-model manual path works, and action metrics can be calculated with stable denominators.

## Phase 10 closure evidence (2026-07-22)

- `IntentOrchestratorService.today` now ranks all active projects plus the latest pending series opportunity and returns one deterministic primary action.
- Pending series opportunities are persisted as auditable `create_project` actions with `source=series_opportunity`; accepting the opportunity remains a separate user decision.
- Primary navigation is frozen to `今日｜内容｜机会｜素材｜我的`; legacy tool routes redirect into those five nodes.
- Playwright covers the no-model path from a share idea through intent confirmation, evidence confirmation, deterministic candidate review and version lock, and verifies the product stops before publishing.
- The same Playwright suite verifies the five-node navigation at `390x844`.
- Remaining unchecked items are still real scope: full action failure/expiry/cancel lifecycle, deletion/export guarantees across every entity, stable analytics denominators, and the complete release-validation matrix.

## Phase 11 instrumentation evidence (2026-07-22)

- Migration `028_action_experiment_metrics.sql` defines E1-E4, append-only assignment events, one active experiment per owner, and frozen experiment/cohort context on actions and events.
- `GET /api/v2/internal/validation/action-metrics` uses distinct actions with an in-window `proposed` event as the stable denominator for accepted, rejected, completed, and failed rates.
- The export is owner-scoped and omits all action payloads, raw content, material content, email, credentials, API keys, and platform tokens. User identifiers are domain-separated SHA-256 pseudonyms.
- Every rate includes numerator, denominator, a half-open UTC window, and explicit zero/missing-data handling. Calibration output separately reports valid-clean reviews, contamination, upgrade eligibility, observation states, and rule-version states.
- These changes make E1-E4 measurable; they do not supply real-user samples or prove any experiment hypothesis. T049 and T050 remain open.

## Phase 12 release-matrix progress (2026-07-22)

- `phase-12-release-matrix.md` maps every T049/T050 journey to executable evidence and keeps missing capabilities blocked.
- The production HumanGate path now receives the optional model used for evidence-bound candidate generation; model timeout and malformed output preserve confirmed user input and fall back to a reviewable deterministic candidate.
- The content workspace persists unsaved edits per project and base version, blocks server saves while offline, protects navigation, and requires explicit recovery or discard after reload.
- Concurrent project, calibration and series-opportunity reads now converge on one persisted `NextBestAction`, proposed event and referenced AI trace instead of racing on the idempotency index.
- T049 remains open because the starter assessment/direction/sprint flow does not exist.
- T050 remains open because evidence revocation is covered but v2 entity deletion and cascade guarantees are not implemented.

## Phase 13 growth-learning progress (2026-07-22)

- `test_growth_creator_completes_confirmed_learning_loop` exercises the production API from Today through manual publication, intent-specific metrics, blind review and the `long_term_learning` HumanGate.
- The test proves no Observation exists before confirmation, and that confirmation persists exactly one next experiment with the reviewed continue/stop context before advancing to `manage_learning`.
- Concurrent requests to open the same learning gate now converge through the database uniqueness contract instead of surfacing an idempotency-index 500.
- `intent-driven-loop.spec.ts` covers the same journey in Chromium, including real offline draft recovery before publication and the user-visible facts, possible causes, continue, stop and experiment sections.
- The growth creator row is Covered in `phase-12-release-matrix.md`; T049 remains open only because the bounded starter entry flow is still absent.

## Phase 14 project-deletion progress (2026-07-22)

- `DELETE /api/v2/projects/{project_id}` now permanently removes an owner-scoped project while returning the same `204` for retries and foreign IDs.
- Existing foreign-key cascades remove project content, evidence, publication data, reviews, actions and gates; project-derived rules, series and opportunities are explicitly removed because their provenance is no longer complete.
- CreatorState references, orphan AI traces and project-only screenshot assets are removed in the same transaction.
- `test_growth_creator_completes_confirmed_learning_loop` now continues through deletion and proves that ContentGenome, Today and privacy-safe metrics no longer expose the deleted project.
- The Phase 12-14 backend release matrix passes `33` tests. T050 is complete; T049 remains open for the bounded starter journey.

## Phase 15 starter-experiment closure (2026-07-22)

- Migration `029_starter_domain.sql` adds only the bounded assessment, direction and sprint records; generated content still uses the existing `ContentProject` aggregate.
- Readiness requires time, publication intent, experiment consent and at least one user-supplied asset after privacy exclusions. It does not classify the user into a permanent niche.
- Direction generation returns at most three evidence-referenced, low-cost experiments through a traced deterministic fallback and contains no traffic, virality, monetization or guaranteed-growth claim.
- Selecting a direction idempotently creates exactly three linked projects. Every project enters the existing action protocol at `confirm_intent` and continues through the same evidence, candidate, publication and learning gates as growth projects.
- Starter review requires at least one real publication and records only observed evidence, blockers and next experiments.
- The Phase 12-15 backend release matrix passes `45` tests; the frontend suite passes `363` tests with `2` skipped, plus lint and production build. T049 and T050 are complete.

## Phase 16 action-lifecycle progress (2026-07-22)

- Added explicit rejected, failed, expired and cancelled action outcomes with idempotent, version-checked event records.
- Failed and expired actions create a fresh recovery action; cancelled suggestions remain stopped until the project version changes.
- Today now shows expected outcome and expiry, requires a reason to reject a suggestion, and preserves the manual path.
- Existing phase-15 SQLite databases upgrade through migration 030 with indexes, experiment triggers and foreign keys restored.
- Final validation: backend `779 passed`, `1 deselected`, `86.69%` coverage; frontend `364 passed`, `2 skipped`, plus lint and build.
- T009, T016, T017 and T019 are complete. Remaining unchecked tasks still require a separate evidence audit or implementation.

## Phase 17 completion-gate audit (2026-07-22)

- Audited all 16 unchecked tasks against current models, migrations, services,
  routes and executable tests.
- T003 and T018 were stale checklist entries and are now closed with existing
  migration-replay and metrics evidence.
- Fourteen tasks remain open. They are grouped into contracts/provenance,
  trust/privacy, synthetic scenarios and calibration completeness in
  `phase-17-completion-gate-audit.md`.
- Spec 009 is not complete and no unchecked item is represented as shipped.

## Phase 19 trust-boundary and privacy closure (2026-07-23)

- Migration `031_trust_boundaries_privacy.sql` adds account-level privacy and
  deletion gates without weakening project/action gate ownership constraints.
- Owner-confirmed export covers every v2 owner entity, excludes credentials and
  includes current ContentGenome projections; confirmed account deletion removes
  all owner rows while preserving other users.
- Publication records now require a confirmed publication gate bound to the
  locked content version, publish hypothesis, public scope and action AI trace.
- Confirmed long-term learning enters CreatorState and ContentGenome as a
  source-linked validated insight; rejected gates write nothing, while refuted or
  archived source observations remove the insight from future action context.
- Final validation: backend `789 passed`, `1 deselected`, `87.08%` coverage;
  frontend `365 passed`, `2 skipped`, plus lint and production build.
