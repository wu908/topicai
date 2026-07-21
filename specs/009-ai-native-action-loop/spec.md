# Feature Specification: TopicAI AI-native Action Loop

**Feature Branch**: `009-ai-native-action-loop`

**Created**: 2026-07-18

**Status**: Ready for planning

**Input**: Formal AI-native decision freeze and evidence-backed redesign of TopicAI from user-led isolated AI tools to an AI-driven creator-state and content-project action loop.

**Product sources**:

- `../../../12-formal-decision-freeze.md`
- `../../../08-current-state-and-ai-native-gap-matrix.md`
- `../../../09-ai-native-core-model-draft.md`
- `../../../10-synthetic-logic-validation.md`
- `../../../11-mvp-experiment-and-instrumentation-plan.md`
- `../../../13-cheat-on-content-reference-analysis.md`
- `../../../01-product-definition.md`
- `../../../02-information-architecture.md`
- `../../../03-content-project-data-model.md`
- `../../../04-page-prd-and-acceptance.md`

## Scope and Evidence Boundary

This feature converts the approved product direction into an implementation-ready AI action contract. It does not claim that AI-native behavior improves growth; that remains an experiment hypothesis. It does not add automatic Xiaohongshu publishing, continuous hotspot aggregation, team workflows, multi-platform workflows, or calibrated growth prediction.

The existing React/FastAPI/SQLite infrastructure and the `008-content-project-mvp` domain remain the implementation base. This feature adds the control loop around `CreatorState`, `ContentProject`, `Evidence`, `NextBestAction`, `AITrace`, `HumanGate`, and confirmed `LearnedInsight`.

## User Stories and Testing

### User Story 1 - See and execute the next meaningful action (Priority: P1)

As a growth creator, I can open Today and see one evidence-backed next action for the most important active project, accept it, skip it, or continue manually.

**Why this priority**: The central AI-native hypothesis is that the product reduces decision and context-transfer cost by choosing the next action instead of showing independent tools.

**Independent Test**: Seed a creator state with an unfinished project, a current blocker, and available evidence; open Today; accept or reject the action; verify an auditable action event and correct project-state response.

**Acceptance Scenarios**:

1. **Given** an active project has a known blocker, **When** Today loads, **Then** it shows one primary `NextBestAction` with target, reason, evidence references, user gate, and fallback.
2. **Given** the user accepts an action, **When** the action completes, **Then** the system records before/after state, duration, trace id, and expected result.
3. **Given** the user rejects an action with a reason, **When** Today reloads in the same period, **Then** the same action is not repeatedly presented as the primary action.
4. **Given** AI is unavailable, **When** Today loads, **Then** the user can open the project list and continue manually.

### User Story 2 - Interview for missing evidence before drafting (Priority: P1)

As a knowledge/experience creator, I can answer only the questions needed to fill a project's evidence gap, confirm which answers may be reused, and continue to a brief or draft.

**Why this priority**: The product must preserve creator authenticity and avoid substituting invented experience for missing material.

**Independent Test**: Seed a project whose audience and promise are known but whose evidence is missing; invoke the action loop; answer some questions; reject one answer for reuse; verify only confirmed evidence is cited.

**Acceptance Scenarios**:

1. **Given** a project lacks personal evidence, **When** the action loop evaluates the project, **Then** it offers `interview_for_evidence` before a complete fact-based draft.
2. **Given** the user answers an interview question, **When** the answer is saved, **Then** it remains a proposed `Evidence` item until the user confirms reuse.
3. **Given** the user rejects an answer for reuse, **When** creation runs, **Then** the rejected evidence is excluded from context and the rejection is auditable.
4. **Given** the user refuses the interview, **When** they choose manual continuation, **Then** the project remains usable with a clearly marked generic structure and no invented facts.

### User Story 3 - Make non-destructive AI changes (Priority: P1)

As a creator, I can accept, reject, partially accept, compare, and undo AI suggestions without overwriting a confirmed version.

**Why this priority**: Trust requires a reversible relationship between AI output and creator-owned content.

**Independent Test**: Lock a confirmed version, request a local edit, accept one segment, reject another, regenerate, and verify version ancestry and locked-content immutability.

**Acceptance Scenarios**:

1. **Given** a confirmed version exists, **When** AI suggests a change, **Then** it creates a candidate version or segment proposal and does not modify the confirmed version.
2. **Given** the user accepts only one segment, **When** the decision is saved, **Then** a new version contains that segment change and preserves the other segments.
3. **Given** AI generation times out, **When** the user returns, **Then** the confirmed version and local recovery draft remain available.

### User Story 4 - Learn from publication and review (Priority: P1)

As a creator, I can see which facts were observed, which explanations are hypotheses, and which one continue/stop/experiment actions are proposed; only my confirmation changes long-term context.

**Why this priority**: The product's long-term value must come from an auditable feedback loop rather than one-off generated advice.

**Independent Test**: Publish a locked version, enter partial metrics, complete review, reject one proposed insight, confirm one, and verify only the confirmed insight affects a future action trace.

**Acceptance Scenarios**:

1. **Given** metrics are incomplete, **When** review runs, **Then** the result is marked data-insufficient and does not make deterministic attribution.
2. **Given** a review has facts, hypotheses, and experiments, **When** it is displayed, **Then** the three classes are visually and structurally distinct.
3. **Given** the user confirms an insight, **When** the next action is generated, **Then** the trace can show the confirmed insight as context.
4. **Given** the user rejects an insight, **When** the next action is generated, **Then** the rejected insight is excluded from long-term context.

### User Story 5 - Control autonomy and data rights (Priority: P1)

As a creator, I can see what AI may do, approve critical actions, revoke evidence use, delete materials, export my data, and continue manually when AI fails.

**Why this priority**: An AI-driven workflow without explicit control would create trust, privacy, and recovery failures.

**Independent Test**: Revoke a material, attempt a dependent action, reject a HumanGate, export data, and request deletion; verify access and references are updated.

**Acceptance Scenarios**:

1. **Given** a material is deleted, **When** an action references it, **Then** the action fails with an evidence-invalid reason and offers replacement or manual continuation.
2. **Given** a critical action requires approval, **When** approval is rejected, **Then** the action cannot complete and the rejection is recorded.
3. **Given** account deletion is requested, **When** the deletion job completes, **Then** user-generated content, derived context, screenshots, feedback, and AI traces are removed or anonymized according to retention rules.

### User Story 6 - Calibrate my own content judgment (Priority: P1)

As a growth creator, I can lock why I believe a note will be useful before publication, compare that original judgment with later results, and promote a recurring observation into a personal rule only when evidence is sufficient.

**Why this priority**: The defensible product asset is not generated copy but the creator-specific relationship between judgments, materials, published versions, outcomes, counterexamples, and rule evolution.

**Independent Test**: Lock a publish hypothesis with a version, enter a result snapshot, run a blind review, create an observation, add supporting and contradicting samples, and verify that rule activation requires backtesting and user approval.

**Acceptance Scenarios**:

1. **Given** a publish version is ready, **When** the user confirms publication preparation, **Then** the version and minimum `PublishHypothesis` are locked atomically.
2. **Given** outcome data and a later explanation exist, **When** blind review runs, **Then** it compares the locked hypothesis with result snapshots without reading the later explanation.
3. **Given** only one project supports an observation, **When** review completes, **Then** the observation cannot become an active creator rule.
4. **Given** a rule candidate has sufficient samples, **When** it fails full-sample consistency or has unresolved counterexamples, **Then** activation is blocked and the active version remains unchanged.
5. **Given** a result leaks into the judgment input channel, **When** calibration validation runs, **Then** the review is marked `calibration_invalid` and cannot support a rule version.

## Functional Requirements

- **FR-001**: The system MUST persist a versioned `CreatorState` for each user and expose the state inputs used by an AI action.
- **FR-002**: The system MUST preserve `ContentProject` as the only lifecycle aggregate for project work.
- **FR-003**: The system MUST represent AI work as a `NextBestAction` with a target, reason, evidence references, expected state change, user gate, expiry, and fallback.
- **FR-004**: `NextBestAction` MUST use `proposed`, `accepted`, `executing`, `completed`, `rejected`, `expired`, `failed`, and `cancelled` states.
- **FR-005**: The system MUST prevent duplicate action execution with an idempotency key tied to user, target, action type, and state version.
- **FR-006**: The system MUST record an `AITrace` for every AI action, including task type, input references, evidence references, policy version, model identifier, generation time, limitations, and user decision.
- **FR-007**: The system MUST classify evidence as `user_fact`, `external_fact`, `ai_inference`, or `validated_insight`.
- **FR-008**: `ai_inference` MUST NOT be promoted automatically to `user_fact` or `validated_insight`.
- **FR-009**: The system MUST create a `HumanGate` for fact confirmation, publish-version locking, publication confirmation, long-term insight confirmation, privacy authorization, and deletion confirmation where applicable.
- **FR-010**: The MVP MUST permit AI levels L0 observation, L1 suggestion, L2 reversible execution, and L3 critical confirmation only; automatic publishing and identity/fact confirmation remain prohibited.
- **FR-011**: The action engine MUST choose a primary action using current state, blocker, weekly goal, evidence readiness, project urgency, recent user decisions, and active experiment context.
- **FR-012**: The action engine MUST not replace a near-complete project with a new opportunity unless the user explicitly chooses exploration.
- **FR-013**: When evidence is insufficient, the system MUST offer targeted interview actions before a complete fact-based draft.
- **FR-014**: AI-generated changes MUST be candidate or segment-level changes and MUST NOT overwrite confirmed versions.
- **FR-015**: Deleted or revoked evidence MUST invalidate dependent action references, candidate versions, and unpublished content checks.
- **FR-016**: The review engine MUST output observed facts, possible causes, one continue action, one stop action, and one experiment action.
- **FR-017**: Only user-confirmed insights MAY enter `ContentGenome` or influence future action selection.
- **FR-018**: The action engine MUST expose a manual fallback for timeout, unavailable model, malformed output, missing capability, expired source, and permission failure.
- **FR-019**: All action lifecycle events MUST be emitted with experiment id, cohort, project id, before/after state, trace id, latency, success, and error code.
- **FR-020**: Analytics events MUST exclude raw body text, private material content, credentials, API keys, and platform tokens by default.
- **FR-021**: The MVP MUST not call legacy `DataManager`, `LLMDataSource`, TianAPI, Bilibili, or preloaded hotspot sources from the new action engine.
- **FR-022**: The MVP MUST not display viral probability, CTR prediction, exact traffic prediction, or model-generated realtime claims.
- **FR-023**: The system MUST persist a `PublishHypothesis` containing audience problem, reader promise, expected behaviors, evidence basis, uncertainty, and a lock timestamp.
- **FR-024**: Locking a publish version and its minimum `PublishHypothesis` MUST be atomic and idempotent.
- **FR-025**: A locked `PublishHypothesis` MUST be immutable; later changes create an appended amendment or a new candidate associated with a new content version.
- **FR-026**: `BlindReview` MUST compare the locked judgment snapshot with result snapshots before reading or generating post-hoc causal explanations.
- **FR-027**: The calibration service MUST record its visibility boundary, source snapshot ids, contamination check, and calibration state in `AITrace`.
- **FR-028**: A contaminated, revoked, or structurally incomplete calibration MUST be marked `calibration_invalid` or `insufficient` and MUST NOT support a rule upgrade.
- **FR-029**: The system MUST model an `Observation` lifecycle of `observing`, `pending_validation`, `absorbed`, `refuted`, and `archived` without adding project statuses.
- **FR-030**: One completed project MAY create an observation but MUST NOT activate or silently modify a `CreatorRule`.
- **FR-031**: A `RuleVersion` candidate MUST contain scope, supporting samples, counterexamples, old/new differences, backtest result, approval gate, and rollback reference.
- **FR-032**: Rule activation MUST require full-sample reevaluation, a configured consistency threshold, no unresolved blocking counterexample, and explicit user approval.
- **FR-033**: Rejecting or rolling back a rule version MUST preserve its evidence and audit record while restoring the previous active version for future actions.
- **FR-034**: `BenchmarkSample` MUST use unknown for missing metrics and MUST NOT be used to produce exact traffic, viral, CTR, or follower predictions.
- **FR-035**: Today MUST summarize pending publication, pending review, active observations, recently refuted judgments, and the best resumable project without replacing the one-primary-action constraint.

## Key Entities

- **CreatorState**: Current goal, capacity, blockers, active projects, recent actions, evidence readiness, uncertainty, and confirmed context.
- **ContentGenome**: Long-term graph of creator promise, experience, viewpoints, audience questions, series, voice patterns, outcomes, and confirmed insights.
- **Evidence**: Source-bound fact or inference with confirmation, privacy, validity, and deletion effects.
- **NextBestAction**: Action object selected by the engine and controlled through a lifecycle.
- **AITrace**: Provenance and limitation record for the action.
- **HumanGate**: Approval record for decisions AI cannot make alone.
- **Experiment**: Hypothesis, control/variant, project refs, metrics, and result.
- **ContentProject**: Existing aggregate extended with blocker, next action, evidence coverage, active experiment, confirmed version, and locked publish version.
- **PublishHypothesis**: Immutable pre-publication statement of audience promise, expected behavior, evidence basis, and uncertainty.
- **BlindReview**: Calibration comparison between the locked judgment snapshot and append-only result snapshots.
- **Observation**: A provisional pattern with supporting samples, counterexamples, next test, and lifecycle status.
- **CreatorRule / RuleVersion**: Versioned personal judgment rule with backtesting, approval, rejection, and rollback history.
- **BenchmarkSample**: Historical project selected for relative calibration, with explicit quality and missing-data state.

## Success Criteria

- **SC-001**: Every displayed AI action has target, reason, evidence references, user gate, fallback, and trace id.
- **SC-002**: A user can accept, reject, complete, retry, or manually bypass every MVP action without losing user content.
- **SC-003**: Confirmed content versions are never silently overwritten by an AI task.
- **SC-004**: Deleted evidence cannot be used by a subsequent action or unpublished version.
- **SC-005**: The system can calculate action-offered, accepted, rejected, completed, and failed rates with stable denominators and user cohorts.
- **SC-006**: A complete project can proceed through manual publication even when the model is unavailable.
- **SC-007**: A review with incomplete data never creates a deterministic attribution or confirmed insight.
- **SC-008**: The existing five-node navigation and seven project statuses remain unchanged across the new action loop.
- **SC-009**: Every published project has an immutable version-linked hypothesis or an explicit legacy/no-hypothesis marker.
- **SC-010**: No active rule can be traced only to a single result, contaminated review, or missing user approval.
- **SC-011**: Every active rule version can be compared with and rolled back to its previous version without altering historical reviews.

## Assumptions

- This feature is implemented on the `008-content-project-mvp` domain and does not introduce a second content lifecycle.
- First release remains local Docker, one user workspace, one primary Xiaohongshu account, and graphic knowledge/experience notes.
- The model endpoint is provider-neutral and configured outside domain code.
- Product outcome claims require later real-user experiments defined in `11-mvp-experiment-and-instrumentation-plan.md`.
