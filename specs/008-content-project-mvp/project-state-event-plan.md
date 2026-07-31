# Project State Event Research / Plan

**Date**: 2026-07-31
**Status**: Implemented
**Scope**: Append-only audit for `ContentProject.status`; not event sourcing

## Outcome

Add one `ProjectStateService` module that owns canonical project-status changes
and appends a `ProjectStateEvent` in the same database transaction. Keep
`content_projects.status` as the current-state authority. Events are audit facts;
they are not replayed to rebuild projects.

This completes the missing foundation described by Spec-008 T029 without adding
projections, a message bus, or a parallel workflow.

## Verified Current State

Spec-008 defines `ProjectStateEvent` and
`POST /api/v2/projects/{id}/transitions`, but migration 012 creates only
`content_projects`. There is no project state-event table or transition module.

Current status writes are distributed across six paths:

| From | To | Current owner | Reason | Actor |
|---|---|---|---|---|
| `preparing` | `ready_to_publish` | `PublishHypothesisService.lock` | `publish_hypothesis_locked` | user |
| `ready_to_publish` | `published` | `PublicationService.record` | `publication_recorded` | user |
| `published` | `awaiting_review` | `PerformanceSnapshotService.append` | `performance_snapshot_added` | user |
| `published` | `awaiting_review` | `ObservationWindowService.mark_due` | `observation_window_elapsed` | system |
| `awaiting_review` | `settled` | `HumanGateService._confirm_learning` for unknown outcomes | `unknown_outcome_confirmed` | user |
| `ready_to_publish` | `creating` | `EvidenceService.revoke` for locked evidence | `evidence_revoked` | user |

`PerformanceSnapshotService.append` may also run while already
`awaiting_review`. That is a same-state aggregate update and must not append a
state event.

Project creation establishes an initial state; it is not a transition in this
slice. Project deletion remains a destructive aggregate operation, not a state
transition.

## Model Boundary

A Project State Event records:

- event id and owner id;
- project id;
- `from_status` and `to_status`;
- stable reason code;
- actor type (`user` or `system` for the current product);
- resulting project version;
- idempotency key and request hash;
- creation time.

The extra owner, version, and request-hash fields reuse the repository's existing
append-only event pattern and make owner isolation, ordering, and replay conflicts
testable.

Events are append-only. Updating or deleting an individual event is unsupported.
Deleting the owning Content Project cascades its events because the product's
existing delete operation removes the whole aggregate and related user data.

## Transition Rules

Use the Spec-008 canonical graph with one explicit compatibility edge required by
the current vertical slice:

| From | Allowed to |
|---|---|
| `inbox` | `preparing` |
| `preparing` | `inbox`, `creating`, `ready_to_publish` |
| `creating` | `preparing`, `ready_to_publish` |
| `ready_to_publish` | `creating`, `published` |
| `published` | `awaiting_review` |
| `awaiting_review` | `settled` |
| `settled` | none |

`preparing -> ready_to_publish` is the compatibility edge: the live
publish-hypothesis flow does not currently persist an intermediate `creating`
state. Removing it would break the working calibration loop and is not part of
this audit task.

Every backward pre-publication transition requires a non-empty reason. A project
cannot move from `published`, `awaiting_review`, or `settled` back to a
pre-publication state. Same-state requests are rejected at the explicit
transition interface; workflow code that updates non-state fields while the
status is unchanged does not append an event.

## Interface and Seam

The external seam is:

```text
ProjectStateService.transition(owner_user_id, project_id, command)
    -> { project, event }, replayed
```

The command contains `to_status`, `reason`, `actor_type`, `expected_version`, and
`idempotency_key`. The module owns owner scoping, transition validation,
optimistic concurrency, the status update, and event append.

Existing workflow modules call the same transition implementation inside their
current transaction so the domain side effect and audit event commit or roll back
together. `ObservationWindowService.mark_due` keeps its scheduler-facing
interface but processes due projects through this module in one transaction.

The HTTP adapter adds the already-specified
`POST /api/v2/projects/{project_id}/transitions` endpoint. HTTP callers cannot
claim `actor_type=system`; the adapter supplies `user`. The scheduler supplies
`system` internally.

## TDD Slices

Tests should observe behavior only through these seams:

1. `ProjectStateService.transition`:
   - appends one event and increments the project version;
   - replays the same idempotency key and rejects a conflicting payload;
   - rejects owner mismatch, stale version, invalid edges, and post-publication rollback.
2. `POST /api/v2/projects/{id}/transitions`:
   - returns the updated project plus event and preserves the v2 envelope.
3. Existing workflow interfaces:
   - one publish-to-review-to-settle vertical loop proves the five lifecycle
     forward paths append the expected ordered events;
   - `ObservationWindowService.mark_due` proves a system event is appended once;
   - a corrected snapshot while already awaiting review proves no duplicate
     state event is appended;
   - revoking locked evidence proves the pre-publication rollback is audited.
4. Migration runner:
   - fresh apply, replay, upgrade from 040, table/index/constraint checks.

Each slice follows red -> green. Existing workflow tests remain the main behavior
tests; do not add per-helper tests.

## File Plan

Minimum expected changes:

- add migration `041_project_state_events.sql`;
- add transition command/event contracts to
  `backend/app/models/v2/content_project.py`;
- add `backend/app/services/project_state.py`;
- add the transition route to `backend/app/api/v2/projects.py`;
- route the six existing status changes through the module;
- extend the existing migration, service, and API tests;
- retain the new `Project State Event` definition in `CONTEXT.md`.

## Explicitly Skipped

- event sourcing, projections, snapshots, queues, and event replay;
- synthetic backfill for existing projects, because actor and reason would be
  invented;
- event list/read endpoints and frontend history UI until a consumer exists;
- an AI actor type until AI can directly change project status;
- changing the known-outcome review lifecycle or introducing the missing
  persisted `creating` step; both are separate product decisions;
- database triggers, because they cannot reliably receive the command actor and
  idempotency context.

## Evidence Read

- `CONTEXT.md`
- `specs/008-content-project-mvp/data-model.md`
- `specs/008-content-project-mvp/contracts/api-v2.md`
- `specs/008-content-project-mvp/tasks.md`
- migration 012 and the migration runner through migration 040
- the five status-writing services and their calibration, scheduler, API, and
  migration tests
- existing append-only event implementations for observations, actions,
  opportunities, viewpoints, series, and benchmark samples

> AI-assisted research and planning, checked against the local source and tests.

## Verification

- migration apply/replay and interrupted-DDL recovery pass;
- service transition, owner, version, graph, and idempotency tests pass;
- API transition contract passes;
- publish, snapshot, scheduler, unknown-outcome, and evidence-revocation paths
  append ordered audit events;
- Ruff, mypy, Bandit, and the backend coverage gate pass.
