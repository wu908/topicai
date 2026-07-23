# Phase 19 - Trust boundaries and privacy

## Scope

This package closes only T005, T012, T028 and T032. It does not add synthetic
scenario coverage, benchmark calibration or automatic publication.

## Owner data rights

- Privacy and deletion are account-level HumanGates with no project or action
  association. Both require an authenticated owner request and an explicit,
  idempotent confirmation before data can leave or be destroyed.
- `GET /api/v2/account/data-export` returns the owner's account fields, every v2
  owner-scoped entity and the current ContentGenome for active projects. Password
  hashes and data belonging to other owners are excluded.
- `DELETE /api/v2/account` removes owner-scoped rows in dependency order and then
  removes the user. The owner-isolation test proves another user's project and
  account remain present.

## Publication boundary

- Opening a publication HumanGate freezes the locked content version, publish
  hypothesis, Xiaohongshu public scope and originating action AITrace in the gate
  payload.
- Recording publication requires that same owner-scoped, confirmed gate. The
  server rejects a missing gate or a mismatch in version, hypothesis, public
  scope or trace.
- The publish record stores `publication_gate_id` and `ai_trace_id`, preserving a
  direct audit path from the public release to the AI action that prepared it.
- The frontend opens and confirms this gate before recording the manual release.
  TopicAI still cannot publish or disclose content automatically.

## Learning boundary

- Confirming the long-term-learning gate creates the review Observation and adds
  one `observation:{id}` validated insight to CreatorState.
- Gate side effects run only after the confirmation event commits. They use the
  same gate-scoped idempotency keys on replay, so an interrupted projection can
  be retried without creating a second Observation or insight.
- ContentGenome includes only insights whose source Observation remains confirmed
  and active. Refuted or archived observations are removed from CreatorState and
  cannot influence subsequent action traces.
- Rejecting the gate creates neither an Observation nor a validated insight. No
  single result becomes durable creator knowledge without user confirmation.
- Gate decision replays are bound to the original gate and action. Account-level
  confirmations also recover concurrent identical requests as idempotent replays.
- Replaying a refuted or archived Observation still removes any stale validated
  insight, including when replay is detected inside the database transaction.

## Migration and compatibility

- Migration `031_trust_boundaries_privacy.sql` rebuilds `human_gates` so privacy
  and deletion gates may omit project/action identifiers while all other gate
  types must retain both identifiers.
- Existing project gates are copied unchanged. New publication provenance columns
  are nullable for historical records and required by the current write contract.
- Fresh migration, replay and upgrade from phase 15 all pass foreign-key checks.
- Pending legacy version/publication gates are enriched with missing provenance
  when reopened; already-decided historical gates remain unchanged and cannot be
  silently rewritten.

## Executable evidence

Focused backend verification covers migration replay, calibration, intent actions,
account rights and creator series. CI-equivalent verification on 2026-07-23:

```text
backend: 789 passed, 1 deselected, coverage 87.08% (minimum 80%)
frontend: 365 passed, 2 skipped
frontend lint: passed
frontend production build: passed
```

## Deferred work

The remaining completion packages are unchanged:

1. Synthetic acceptance matrix: T027 and T033.
2. Calibration completeness: T034, T036, T039 and T042.
