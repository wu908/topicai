# Phase 20 - Synthetic acceptance matrix

## Scope

This package defines and automates C-01 through C-07 from
`10-synthetic-logic-validation.md`. It closes T027 and T033. These scenarios
validate deterministic product logic and trust boundaries; they do not prove
user demand, usability, retention, growth impact or willingness to pay.

## Scenario contract

| ID | Given | Required result | Forbidden result | Executable evidence |
|---|---|---|---|---|
| C-01 | A confirmed project promise lacks first-party evidence | Offer one evidence interview, keep the project status stable, persist the answer as proposed evidence and create a candidate only after fact confirmation | Invent a creator experience or bypass the near-complete project | `test_c01_missing_evidence_creates_interview_before_candidate` |
| C-02 | The creator refuses the interview and chooses manual continuation | Return a `generic_structure` fallback with explicit missing-evidence limitations; allow a user-authored version to continue | Fabricate facts, block the project or immediately repeat the interview after the user creates the manual version | `test_c02_refused_interview_uses_marked_manual_structure` |
| C-03 | Version 3 is locked and an AI revision is proposed | Create version 4 as a child candidate while preserving version 3 and its publication lock byte-for-byte | Overwrite the locked version or silently move the publication lock | `test_c03_ai_revision_never_overwrites_locked_version` |
| C-04 | The creator pastes a source excerpt without an original URL, publication time or authority | Persist a `user_source` opportunity as `pending_verification`, request provenance, use no model and block acceptance | Claim realtime status, produce a heat/growth score, create a project or create content | `test_c04_unknown_hotspot_stays_pending_verification` |
| C-05 | A published note has only a partial, intent-inadequate metric snapshot | Preserve the snapshot, move the project to review, mark calibration `insufficient` and block Observation/long-term learning | Produce deterministic attribution, compare with a nonexistent baseline or write durable insight | `test_c05_partial_metrics_remain_insufficient_and_do_not_learn` |
| C-06 | The creator rejects the primary action and explicitly supplies current available time | Record the rejection, atomically update short-term capacity, keep the project recoverable and return one defer option | Repeat the same primary action, archive the project, lower the goal or change long-term facts/insights | `test_c06_rejection_updates_explicit_capacity_without_archiving` |
| C-07 | A candidate version references evidence that the creator revokes | Return affected version/segment references, block publication locking and route the project back to evidence replacement | Reuse the revoked source, silently replace it or continue treating the candidate as publishable | `test_c07_revoked_material_reports_impact_and_blocks_lock` |

## Product decisions frozen by the matrix

- Capacity is updated only from an explicit `available_minutes` value supplied
  with the rejection. TopicAI does not infer numeric capacity from free text.
- A user-submitted source remains `pending_verification` even when some metadata
  is present. The first implementation records the request and required inputs;
  it does not claim that URL presence proves authority or freshness.
- Pending source opportunities are excluded from Today project-creation actions.
  They cannot be accepted until a later verification decision establishes
  `verified` status.
- Content versions remain immutable after evidence revocation. TopicAI marks the
  source invalid, reports affected versions and segments, clears dependent
  publication locks and blocks reuse instead of rewriting historical content.
- Manual continuation after interview refusal is user-authored. The fallback is
  explicitly marked as a generic structure and cannot be represented as a
  creator fact.

## Persistence and compatibility

Migration `032_source_verification_opportunities.sql` extends the existing
`content_opportunities` aggregate with:

- `opportunity_type=user_source`;
- source excerpt and optional provenance fields;
- `verification_status=verified|pending_verification`.

Existing `series_extension` rows and events are copied unchanged and receive
`verification_status=verified`. Migration replay and foreign-key integrity are
covered by an upgrade test.

No automatic hotspot aggregation, realtime source call, growth prediction,
automatic publication or automatic long-term learning is added.

## Executable evidence

Focused verification on 2026-07-23:

```text
synthetic matrix: 7 passed
affected backend and migration regression: 58 passed
frontend TypeScript and production build: passed
git diff check: passed
```

Full CI-equivalent verification on 2026-07-23:

```text
backend: 797 passed, 1 deselected; 87.14% coverage
frontend: 365 passed, 2 skipped
frontend lint and production build: passed
```

## Exit condition

T027 and T033 are complete when all seven named tests pass, the source
opportunity upgrade preserves historical rows, and the full repository quality
gates remain green. The remaining Spec 009 implementation package is calibration
completeness: T034, T036, T039 and T042.
