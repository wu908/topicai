# Phase 14 ContentProject Deletion Contract

**Date**: 2026-07-22

**Status**: Implemented and validated

## Decision

`DELETE /api/v2/projects/{project_id}` permanently deletes an owner-scoped v2
content project. The endpoint returns `204` when the project was deleted and on
later retries. A project owned by another user is untouched and produces the
same `204`, so the endpoint does not disclose whether another user's ID exists.

The deletion is one database transaction. No deleted project, raw content,
external note URL, evidence, review, action or trace may remain available to
orchestration or ContentGenome.

## Retention And Cascade Matrix

| Data | Deletion behavior | Reason |
|---|---|---|
| `content_projects` | Hard delete | The aggregate root contains user-authored title and audience context. |
| Versions, segments and segment decisions | Database cascade | These are immutable copies of project content. |
| Evidence and evidence decisions | Database cascade | Statements and source references are project content. |
| Publish hypotheses, records and snapshots | Database cascade | Includes hypotheses, external note URLs and user-entered metrics. |
| Blind reviews, observations and their events | Database cascade | Includes derived statements and review snapshots. |
| Next actions, HumanGates and action events | Database cascade | Payloads can contain interview answers and decisions. |
| Creator viewpoints | Database cascade | A viewpoint belongs to one project and loses all provenance when it is deleted. |
| Creator rules using a deleted observation | Delete the complete rule and its history | A cross-project rule must not silently survive after its validated sample loses provenance. It can be learned again from retained projects. |
| Creator series containing the project | Delete the complete series and its opportunities | Names, promises and continuation prompts were derived from every selected source project. |
| Opportunities that created the project | Delete the opportunity and its events | Confirmed opportunity fields may have become project-authored content. |
| AI traces reachable only from deleted data | Delete after dependent records are gone | Trace references must not retain deleted project context. Shared traces are not deleted while a surviving foreign key exists. |
| Screenshot assets used only by deleted snapshots | Delete | A project-only screenshot is raw user material. Shared assets remain. |
| CreatorState entries referencing deleted actions, viewpoints, rules or series | Remove | Deleted facts and invalidated long-term knowledge must not influence later actions. |
| Experiment assignments and assignment events | Retain | They are account-level enums and timestamps, not project content. Project action events are deleted, so exports retain no deleted raw content. |

## Invariants

- Deletion is owner scoped and does not reveal cross-owner existence.
- A retry is successful and produces no additional mutation.
- The transaction either removes the complete aggregate and invalidated
  cross-project context or changes nothing.
- ContentGenome and the orchestrator cannot read a deleted project or any
  evidence, viewpoint, rule or series whose provenance depended on it.
- Analytics never retains action payloads, note URLs, metrics snapshots or raw
  content from a deleted project.
- The first release does not retain a project deletion tombstone. Add one only
  if a legal retention requirement needs proof of deletion without user content.

## Executable Evidence

The Phase 13 full growth-creator API journey is extended to delete the completed
project and verify project inaccessibility, dependent-table removal,
CreatorState cleanup, trace cleanup, orchestration cleanup, privacy-safe metrics
output, owner isolation and deterministic retry behavior.

Validation results:

- Phase 12-14 backend release matrix: `33 passed`.
- Backend CI equivalent: `761 passed`, `1 deselected`, `86.54%` coverage.
