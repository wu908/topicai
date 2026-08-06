# V2-Only Release Validation

**Date**: 2026-08-06
**Branch**: `feature/explainable-opportunities`
**Scope**: v2-only cleanup, fresh Docker Compose runtime, and approved Docker cleanup.

## Automated Evidence

| Area | Command or check | Result |
|---|---|---|
| Backend tests | `pytest -q --cov=app --cov-report=term-missing --cov-fail-under=80` | 267 passed; 87.07% coverage |
| Backend Ruff | `ruff check app tests` | Passed |
| Frontend tests | Vitest coverage | 131 passed across 25 files; 80% line coverage |
| Frontend lint/build | `npm run lint`; `npm run build` | Passed |
| Frontend E2E | `playwright test e2e/starter-flow.spec.ts e2e/intent-driven-loop.spec.ts` | Added to the required `ci-frontend` GitHub Actions job |
| Patch hygiene | `git diff --check` | Passed |
| Mypy | `mypy app` | Host interpreter cannot parse NumPy 3.12 stubs; no application diagnostics produced |
| Bandit | `bandit -r app` | No high-severity findings; existing low/medium controlled dynamic-SQL findings remain |
| pnpm audit | `pnpm audit --audit-level high` | No high-severity findings; three moderate React Router advisories remain, and full remediation requires a breaking v7 upgrade |

## Fresh Docker Validation

Validation used the canonical Windows tree `G:\codex_project\topicAI\mvp` through Ubuntu WSL at `/mnt/g/codex_project/topicAI/mvp`, with isolated Compose project `topicai-v2-final`.

- `docker compose up --build -d --wait`: backend and frontend built and started successfully.
- `/api/v2/health`: HTTP 200, `api_version=v2`, `status=ok`.
- Frontend `/`: HTTP 200 and React root present.
- OpenAPI: 72 paths, 0 `/api/v1` paths; v2 register/login paths present.
- v2 register/login/me smoke flow: passed.
- Backend restart persistence: registered v2 user logged in successfully after restart.
- `/api/v1/health`: HTTP 404.

## Cleanup Boundary

After validation, the isolated Compose project was stopped with plain `docker compose down`. Cleanup then removed 12 approved TopicAI images, 6 explicitly named TopicAI volumes, and all Docker build cache objects, reclaiming about 3.698 GB of build cache.

Post-cleanup inspection confirmed:

- TopicAI containers: 0.
- TopicAI images: 0.
- TopicAI volumes: 0.
- Docker build cache: 0 B.
- Retained base dependency images: `python:3.12-slim`, `node:22-alpine`, and `nginx:alpine`.
- Retained unrelated images: `image-studio-validation-python:local`, `image-studio-validation-web:local`, and `hello-world:latest`.
- Windows local data and the historical SQL migration chain were not removed.
