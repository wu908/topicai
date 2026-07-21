# Tasks: TopicAI AI-native Action Loop

## Phase A - Contracts and persistence

- [ ] T001 Add v2 typed models for `CreatorState`, `ContentGenome`, `Evidence`, `NextBestAction`, `AITrace`, `HumanGate`, `ActionEvent`, and `Experiment`.
- [x] T002 Add idempotency and optimistic-concurrency contracts for action lifecycle operations.
- [ ] T003 Add migrations for state snapshots, evidence, actions, traces, gates, action events and experiments.
- [x] T004 Test fresh database migration, repeat migration, and upgrade from the 008 schema.
- [ ] T005 Add owner-isolation and deletion/export coverage for every new entity.

## Phase B - Action policy and service

- [x] T006 Implement `CreatorStateService` with versioned snapshots and explicit uncertainty.
- [ ] T007 Implement deterministic action eligibility by project status, blocker, urgency, capacity and evidence readiness.
- [ ] T008 Implement action priority ordering and one-primary-action constraint.
- [ ] T009 Implement `NextBestActionService` offer, accept, reject, execute, fail, expire and cancel operations.
- [x] T010 Enforce action idempotency and state-version checks in the service layer.
- [ ] T011 Implement `AITraceService` and require traces for AI-generated actions.
- [ ] T012 Implement `HumanGateService` for fact, version, publish, insight, privacy and deletion gates.
- [ ] T013 Add source-integrity tests proving the action engine never calls legacy hotspot sources.
- [ ] T014 Add timeout, malformed output, missing capability and manual fallback tests.

## Phase C - Today and project integration

- [x] T015 Replace the Today primary task calculation with the action service while preserving the five-node navigation.
- [ ] T016 Build the primary action card with reason, evidence, expected result, effort, expiry and fallback.
- [ ] T017 Add accept, skip, reject-with-reason, pause and manual-continue UI states.
- [ ] T018 Add action event instrumentation with experiment and cohort fields.
- [ ] T019 Link project list recovery to pending and failed actions.
- [ ] T020 Add responsive and no-model UI tests for Today and action cards.

## Phase D - Evidence interview and creation

- [ ] T021 Implement evidence-gap classification from Brief and ContentProject context.
- [x] T022 Implement targeted interview actions with per-answer confirmation.
- [ ] T023 Bind evidence references to Brief fields and ContentVersion segments.
- [ ] T024 Block fact-based complete drafts when evidence is insufficient unless the user chooses a marked generic structure.
- [x] T025 Implement evidence revocation and downstream invalidation.
- [x] T026 Implement candidate versions, segment acceptance/rejection, comparison and immutable confirmed versions.
- [ ] T027 Add synthetic scenario tests C-01 through C-04.

## Phase E - Publish, review and learning

- [ ] T028 Create publish/version HumanGates and version-bound action traces.
- [x] T029 Connect manual publish record and performance snapshot actions to project state.
- [x] T030 Replace prediction semantics with fact/hypothesis/experiment review output.
- [x] T031 Create exactly one continue, stop and experiment action from a completed review.
- [ ] T032 Add confirmed/rejected insight gates and ContentGenome update rules.
- [ ] T033 Add synthetic scenario tests C-05 through C-07.

## Phase F - Judgment calibration

- [ ] T034 Add typed models and migrations for `PublishHypothesis`, `BlindReview`, `Observation`, `CreatorRule`, `RuleVersion`, and `BenchmarkSample`.
- [x] T035 Implement atomic idempotent locking of publish version and minimum hypothesis.
- [ ] T036 Enforce immutable hypothesis snapshots and append-only post-lock amendments.
- [x] T037 Implement blind-review input allowlist and forbid post-hoc explanations during initial comparison.
- [x] T038 Add `AITrace.visibility_boundary`, source snapshot ids, contamination check, and calibration state.
- [ ] T039 Mark insufficient, contaminated, revoked-evidence, and legacy reviews as ineligible for rule upgrades.
- [x] T040 Implement Observation create, continue-testing, absorb, refute, archive, and workbench cleanup transitions.
- [ ] T041 Implement CreatorRule candidate, full-sample reevaluation, consistency threshold, approval, rejection, rollback, and audit history.
- [ ] T042 Add BenchmarkSample inclusion/exclusion and unknown-metric handling without performance prediction.
- [ ] T043 Extend Today with pending publication, pending review, active observation, refuted judgment, and resumable-project summaries.
- [ ] T044 Add tests proving one sample cannot activate a rule and failed reevaluation leaves the active version unchanged.
- [ ] T045 Add tests proving result leakage produces `calibration_invalid` and cannot influence future actions.

## Phase G - Experiments and release validation

- [ ] T046 Add E1-E4 experiment and cohort assignment fields without storing raw content in analytics.
- [ ] T047 Add metric queries with documented numerator, denominator, window and missing-data handling.
- [ ] T048 Add action funnel and calibration-quality export for internal validation only.
- [ ] T049 Run existing 008 starter and growth journeys against the action protocol.
- [ ] T050 Run no-model, timeout, offline recovery, version conflict, deletion, contamination and rule-rollback journeys.
- [ ] T051 Verify legacy routes redirect or become project-context compatibility shims.
- [ ] T052 Run cross-artifact consistency checks and update the release validation report.

## Completion Gate

The feature is not complete until all P1 tasks are green, synthetic logic scenarios are automated, no confirmed content, hypothesis, insight, or active rule can be silently overwritten, contaminated calibration is blocked, the no-model manual path works, and action metrics can be calculated with stable denominators.
