# Implementation Plan: TopicAI AI-native Action Loop

**Branch**: `009-ai-native-action-loop`  
**Date**: 2026-07-18  
**Spec**: [spec.md](./spec.md)  
**Base feature**: [008-content-project-mvp](../008-content-project-mvp/plan.md)

## Summary

Add an auditable AI action loop and a creator-specific judgment-calibration layer on top of the ContentProject MVP. Reuse the existing authentication, owner isolation, SQLite transaction boundary, React/MUI shell, API client, LLM boundary, migration runner, local storage, risk rules, draft recovery, and test harness. Add state/action/trace services and only the minimum UI needed to make Today and project stages AI-driven.

The action loop is not a general workflow engine and does not use Firecrawl as a runtime dependency. Firecrawl and Agent-Reach remain research tools. No automatic publishing, continuous hotspot source, team surface, or multi-platform behavior enters this feature.

## Evidence-Based Design Constraints

| Constraint | Evidence | Implementation consequence |
| --- | --- | --- |
| AI-native means workflow control, not more generation | Anthropic/OpenAI agent guidance and current-state audit | Build `NextBestAction`, not an AI chat page |
| User facts need evidence and confirmation | Product decision freeze and synthetic validation | Add `Evidence`, `HumanGate`, `AITrace` |
| ContentProject remains the lifecycle aggregate | Existing 008 model and migration plan | Add fields/children; do not create a second project state machine |
| Growth impact is unproven | Evidence log and experiment plan | Instrument outcomes; do not add growth prediction fields |
| Hotspot value is unproven | Hotspot research | Action engine excludes legacy data sources in P0 |
| Post-hoc results can contaminate pre-publication judgment | `cheat-on-content` blind scoring and 1.3→1.4 migration evidence | Separate immutable hypothesis, result snapshots, and later explanations |
| One result is not a durable personal rule | Reference observation lifecycle and TopicAI evidence policy | Add provisional observations and versioned rule promotion gates |
| Exact growth prediction remains uncalibrated | Product decision freeze | Benchmarks support relative review only, never viral/traffic prediction |

## Reuse Matrix

| Existing area | Action | Rationale |
| --- | --- | --- |
| JWT/auth/owner scope | Direct reuse | Security boundary already exists and must remain stable |
| SQLite/migrations/transactions | Direct reuse | MVP scale needs atomic state/idempotency without a new workflow engine |
| React Router/MUI/layout/loading/errors | Adapt | Today and project stages need action cards and human gates |
| LLM client/structured parser/timeout | Adapt | Add action policy and provenance, not a new model SDK |
| ContentProject/state service | Extend | Add blocker, action, evidence coverage, and state version |
| Materials/assets | Adapt | Add evidence type, confirmation, privacy and invalidation |
| Reviews/performance | Adapt | Feed action loop and confirmed insights; remove prediction semantics |
| Feedback | Adapt | Record action acceptance/rejection/reason without silent weight mutation |
| Topic/viral/title/publish tools | Stop as primary flow | Keep only reusable rules/prompts behind project actions |
| TianAPI/Bilibili/LLM hotspot fallback | Exclude from action engine | No P0 continuous hotspot/news dependency |

## Architecture

```text
Today / Project stage
        |
        v
CreatorStateService -> ActionPolicy -> EvidencePolicy
        |                    |
        |                    v
        |               NextBestActionService
        |                    |
        v                    v
ContentProjectService <- HumanGateService <- AITraceService
        |
        v
Review / Experiment / Confirmed Insight
        |
        v
PublishHypothesis -> BlindReview -> Observation -> RuleVersion
```

Routes remain adapters. State transitions, permissions, idempotency, evidence checks and action execution belong in services. AI output cannot write directly to confirmed content or long-term context.

## Delivery Phases

### Phase A - Contracts and persistence

- Add migrations for creator state snapshots, content genome nodes/edges, evidence, actions, traces, gates, experiments and action events.
- Add typed v2 models and API contracts.
- Add evidence classification, permission, deletion and idempotency helpers.
- Add source-integrity tests proving the action engine does not call legacy hotspot sources.

### Phase B - Action engine and Today

- Implement state snapshot assembly.
- Implement deterministic action eligibility and priority rules.
- Add action offer/accept/reject/complete/fail/expire/cancel endpoints.
- Add Today primary action card and manual fallback.
- Add action trace and event instrumentation.

### Phase C - Evidence interview and creation

- Add evidence gap detection.
- Add targeted interview action and confirmed evidence flow.
- Bind evidence references to Brief and ContentVersion.
- Add candidate version, local acceptance, rejection, comparison and lock behavior.

### Phase D - Publish, review and learning

- Bind publish checks and lock gates to actions.
- Add publish record and performance snapshot action triggers.
- Add fact/hypothesis/experiment review output.
- Add confirmed insight gate and ContentGenome update.

### Phase E - Judgment calibration

- Atomically lock `PublishHypothesis` with the selected publish version.
- Compare hypothesis and append-only results through `BlindReview` before post-hoc explanation.
- Add Observation lifecycle and workbench cleanup.
- Add CreatorRule/RuleVersion candidate, backtest, approval, rejection and rollback.
- Add BenchmarkSample with explicit missing-data and quality state.

### Phase F - Recovery, privacy and experiment instrumentation

- Add timeout, unavailable-model, offline, deletion, revoked-evidence and permission recovery.
- Add export/deletion coverage for action traces and genome data.
- Add experiment/cohort fields and metric queries.
- Run synthetic scenarios and existing 008 acceptance journeys.

## Technical Guardrails

- The action engine must be deterministic at the policy boundary; the model may propose content or explanations, but state eligibility, permission, idempotency and forbidden actions are code-enforced.
- Every action has a manual fallback and an immutable event trail.
- L0-L2 actions may execute only when they are reversible and owner-scoped; L3 actions require a `HumanGate`.
- `user_fact`, `external_fact`, `ai_inference`, and `validated_insight` are not interchangeable.
- A missing `AITrace` makes an AI result unavailable rather than trustworthy by default.
- No raw content is placed in product analytics events by default.
- Locked hypotheses, result snapshots and active rule versions are immutable; corrections append new records.
- Calibration input boundaries are code-enforced and recorded in `AITrace`; contamination blocks rule promotion.
- Rule changes require a version, complete evidence set, counterexamples, full-sample reevaluation and `HumanGate` approval.

## Testing Strategy

### Unit and service tests

- Action eligibility for every project state and blocker.
- Priority ordering with overdue, ready-to-publish, review-due and starter tasks.
- Idempotency for action acceptance, interview answer, version proposal, version lock, publish record, snapshot and insight confirmation.
- Evidence classification, confirmation, revocation and deletion invalidation.
- HumanGate permissions and rejection behavior.
- AI timeout, malformed output, missing capability and manual fallback.
- Hypothesis/version atomic lock, blind-review allowlist, contamination invalidation and rule rollback.

### Integration tests

- Today to action to project state transition.
- Interview to evidence confirmation to Brief/content version.
- Confirmed version to publish lock to manual publish record.
- Snapshot to review to confirmed insight to next action.
- Locked hypothesis to blind review to observation to approved/rejected rule candidate.
- Owner isolation and deletion/export.

### End-to-end tests

- Growth creator: Today → evidence interview → project → version → publish → review → next action.
- Starter creator: existing 008 starter flow enters the same action protocol after project creation.
- Recovery: refresh/offline, action retry, rejected action, deleted evidence and version conflict.
- No-model mode: complete core project manually.

## Release Gate

Do not declare the feature complete unless:

1. The synthetic validation scenarios pass in automated tests.
2. All action lifecycle transitions are audited and idempotent.
3. No confirmed version or confirmed insight is silently overwritten.
4. Manual completion works with no model configured.
5. Existing 008 navigation and project states remain stable.
6. Action and experiment metrics have documented denominators.
7. The source-integrity scan confirms no legacy hotspot source is called by the new action engine.
8. A single result or contaminated review cannot activate a creator rule.
9. Every active rule version can be traced, compared, rejected and rolled back without rewriting history.
