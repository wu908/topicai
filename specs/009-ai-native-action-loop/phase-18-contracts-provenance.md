# Phase 18 - Contracts and provenance completion

## Scope

This package closes only T001, T011, T013 and T014. It adds no migration,
dependency, route or product behavior.

## Completed contracts

- `action_domain.py` defines strict read contracts for `CreatorState`,
  `ContentGenome`, `Evidence`, `NextBestAction`, `AITrace`, `HumanGate`,
  `ActionEvent` and `Experiment`.
- The runtime-contract test validates those models against records produced by
  the current services and migrated database instead of model-only fixtures.
- `AITraceCreate` is the write contract used by the provenance service.

## Provenance boundary

- `AITraceService.create` is the only production writer for `ai_traces_v2`.
- All seven former direct insertions use the caller-owned transaction, so a
  trace and its action, review, viewpoint, series, direction or opportunity
  still commit or roll back together.
- Caller-generated trace identifiers remain unchanged because actions and
  generated records reference them in the same transaction.

## Source isolation and recovery

- An AST regression test rejects imports or references to `DataManager`,
  `LLMDataSource`, `TianAPISource`, `BilibiliSource`, `PreloadedDataSource` and
  their legacy data-source modules from the action-engine service set.
- Candidate preparation is tested for timeout, malformed output and a client
  that advertises text availability but lacks structured generation.
- In every model failure case, the confirmed first-party answer remains in the
  deterministic candidate and no confirmed version is overwritten.
- A source-derived series opportunity action is tested through expiry,
  replacement and explicit manual continuation using its persisted fallback.

## Executable evidence

Focused package verification:

```bash
python -m pytest -q \
  tests/services/test_action_engine_source_integrity.py \
  tests/services/test_calibration_loop.py \
  tests/services/test_creator_series.py \
  tests/services/test_creator_viewpoint.py \
  tests/api/v2/test_intent_driven_actions.py \
  tests/api/v2/test_experiment_metrics.py \
  tests/api/v2/test_starter.py
```

Result on 2026-07-23: `65 passed` for the related service and API set. The full
CI-equivalent backend run completed with `784 passed`, `1 deselected`, and
`87.16%` coverage against the required `80%` floor.

## Deferred work

The remaining completion packages are unchanged:

1. Trust boundaries and privacy: T005, T012, T028 and T032.
2. Synthetic acceptance matrix: T027 and T033.
3. Calibration completeness: T034, T036, T039 and T042.
