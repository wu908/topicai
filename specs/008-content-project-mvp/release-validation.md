# V2-Only Release Validation

**Date**: 2026-08-06
**Branch**: `008-content-project-mvp-completion`
**Scope**: release-contract gaps, release-audit fixes through migration 048, v2-only runtime, and fresh/upgrade Docker Compose validation.

## Automated Evidence

| Area | Command or check | Result |
|---|---|---|
| Backend tests | `python -m pytest -q -k "not test_scenario_g_coverage_gate" --cov=app --cov-report=term-missing --cov-report=xml --cov-fail-under=80` | 281 passed; 87.60% coverage |
| Migration tests | Included in the full backend suite plus isolated Compose fresh/upgrade runs | Fresh database and `047 -> 048` upgrade passed; migration history ends at 048 |
| Backend Ruff | `ruff check app tests` | Passed |
| Backend mypy | `mypy --no-site-packages app config` | Passed across 97 source files |
| Backend Bandit | `bandit -q -r app -lll` | No high/critical findings |
| Frontend tests | `vitest run --coverage` | 141 passed across 25 files; 80.34% line coverage |
| Frontend type/lint/build | `tsc -b`; `eslint .`; `pnpm build` | Passed |
| Frontend E2E | `playwright test e2e/starter-flow.spec.ts e2e/intent-driven-loop.spec.ts` | 3 passed with Chromium 1.62.0 |
| Dependency audit | `pnpm audit --audit-level high` | No high/critical findings; three moderate React Router advisories remain |
| OpenAPI | Generated `backend/openapi3.json` plus runtime schema | 81 paths; 0 `/api/v1` paths; account deletion returns 202/422 |
| Source integrity | `scripts/check-v2-source-integrity.ps1`; `scripts/check-utf8.ps1` | Both passed locally and are required by CI |

React Router remains on the latest available v6 line. The published advisory fix requires a breaking v7 upgrade, so it is outside this release-gaps change.

## Rendered Frontend QA

Repository Playwright exercised the real local FastAPI backend with AI disabled; Docker HTTP/schema/migration checks ran separately against the rebuilt Compose stack.

- Growth: real login, history import, profile confirmation, shared project, evidence confirmation, immutable candidate review, publish check, manual publication, snapshot, review, and confirmed next experiment.
- Starter: real assessment, deterministic directions, exactly three linked projects, and entry into the shared project workspace.
- Recovery: offline draft persisted locally and was explicitly restored after reload.
- Desktop 1440x900 and mobile 390x844: no horizontal overflow; sidebar/main and mobile navigation items did not overlap.

## Fresh Docker Validation

Validation used the canonical Windows tree through Ubuntu WSL with isolated Compose projects `topicai-validate-008-fresh` and `topicai-validate-008-upgrade`.

- Backend and frontend images rebuilt successfully; Compose dependency health gating completed.
- Frontend `/`: HTTP 200 through the host IPv4 binding.
- `/api/v2/health`: HTTP 200 with `status=ok`.
- Runtime OpenAPI: 81 paths and no `/api/v1` path.
- Fresh SQLite schema: latest migration `048_release_audit_fixes`; credential revocation and screenshot-decision fields exist.
- Register: HTTP 201.
- Compose restart: both services returned healthy.
- Login after restart: HTTP 200; the validation user remained in SQLite.
- Upgrade fixture first applied migrations only through `047_account_data_jobs`, then current startup applied 048 exactly once.
- The pre-048 user and password remained valid; `credentials_revoked_at` was added with a null value.

The recurring WSL systemd user-session warning did not affect Docker commands or service health.

## Cleanup Boundary

After validation, plain `docker compose down` removed each isolated project's containers and network. Four confirmed validation volumes and four validation images were then removed explicitly:

- `topicai-validate-008-fresh_topicai_data`
- `topicai-validate-008-fresh_topicai_logs`
- `topicai-validate-008-upgrade_topicai_data`
- `topicai-validate-008-upgrade_topicai_logs`
- `topicai-validate-008-fresh-backend:latest`
- `topicai-validate-008-fresh-frontend:latest`
- `topicai-validate-008-upgrade-backend:latest`
- `topicai-validate-008-upgrade-frontend:latest`

Post-cleanup inspection found no containers, volumes, or images with either validation project label. Global prune was not used; base images and reusable build cache were retained per the project Docker policy.
