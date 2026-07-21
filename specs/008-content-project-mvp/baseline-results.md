# Spec-008 Baseline Results

**Run date**: 2026-07-18  
**Copy**: `G:\codex_project\no_1_project\mvp`  
**Source branch**: `008-content-project-mvp`

## Backend

Command:

```powershell
python -m pytest --basetemp='G:\codex_project\no_1_project\mvp\backend\.pytest-tmp' -q
```

Result: **680 passed, 1 failed** in 122.68s.

The single failure is `tests/integration/test_acceptance_scenarios.py::test_scenario_g_coverage_gate`. The test hard-codes `backend/.venv/Scripts/python.exe`, but the clean copy intentionally excludes `.venv`; the current interpreter and test suite are otherwise usable. This is an environment/fixture portability defect to fix before the coverage gate task.

The earlier run without `--basetemp` produced 643 passed, 37 environment errors, and 1 failure because the host's system temp path was not writable. Using `backend/.pytest-tmp` removed all temp, migration, backup, and preloaded-data errors.

## Frontend

Dependency setup:

```powershell
pnpm.cmd install --dir frontend --ignore-workspace --no-frozen-lockfile
```

The copied `frontend/package-lock.json` is not synchronized with `frontend/package.json`; npm `ci` was rejected. The existing root pnpm lock contains the current dependency graph, so pnpm was used for the baseline. Lockfile cleanup is tracked for the setup phase.

Command:

```powershell
pnpm.cmd --dir frontend test
```

Result: **327 passed, 2 skipped** across 46 test files in 204.01s.

## Baseline gate

- Backend: **not green** due to one hard-coded virtualenv path in a legacy acceptance test.
- Frontend: **green** for the existing suite.
- New v2 behavior: not yet implemented.
- No source-project runtime data or secrets were used.

## Immediate fixes before feature work

1. Make the coverage-gate acceptance test invoke the active interpreter or skip only when the governed command is unavailable.
2. Add a reproducible frontend dependency install path around the existing pnpm lock; do not silently replace it with a stale npm lock.
3. Keep `.pytest-tmp` and frontend `node_modules` out of version control.
