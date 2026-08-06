# Quickstart Validation: TopicAI Content Project MVP

This guide defines the release validation for the implemented v2-only product.

## 1. Prerequisites

- Docker Desktop with Compose v2.
- Node.js and pnpm only for non-Docker frontend checks.
- Python 3.11 or 3.12 only for non-Docker backend checks.
- The canonical checkout at `G:\codex_project\topicAI\mvp`.
- Optional OpenAI-compatible endpoint. The complete manual flow must work without one.

## 2. Configure

Create local files from examples; never reuse source-project `.env` files.

Backend MVP variables:

```dotenv
ENVIRONMENT=development
DATABASE_URL=sqlite+aiosqlite:///./data/topicai.db
JWT_SECRET_KEY=<random-local-secret>
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
LLM_TIMEOUT_SECONDS=30
LLM_CAPABILITIES=text
AI_ENABLED=true
VISION_ENABLED=false
```

Rules:

- Empty `LLM_*` values are valid and must expose manual fallback states.
- `LLM_CAPABILITIES` is comma-separated: `text` or `text,vision`.
- No `DEEPSEEK_API_KEY`, `DASHSCOPE_API_KEY`, `ZHIPU_API_KEY`, `TIANAPI_KEY`, or Firecrawl key is required by the v2 runtime.

## 3. Local Quality Gates

Run in PowerShell:

```powershell
cd G:\codex_project\topicAI\mvp\backend
python -m pytest -q
python -m pytest --cov=app --cov-fail-under=80

cd G:\codex_project\topicAI\mvp
pnpm install --frozen-lockfile
pnpm --dir frontend test
pnpm --dir frontend build
```

Record exact passing counts and coverage; do not rely on historical README claims.

## 4. Docker Start

Use the repository's `$windows-wsl-docker-validation` workflow and an isolated Compose project:

```powershell
wsl -d Ubuntu -u root -- bash -lc "systemctl start docker && docker info >/dev/null && printf '__DOCKER_READY__\\n'"
wsl -d Ubuntu -- bash -lc "cd /mnt/g/codex_project/topicAI/mvp && docker compose config && docker compose -p topicai-v2-final up --build -d --wait && docker compose -p topicai-v2-final ps"
```

Expected:

- Backend becomes healthy at `http://localhost:8000/api/v2/health`.
- v2 schema is visible in the API docs and includes `/api/v2/projects`.
- Frontend opens at `http://localhost`.
- Fresh volumes apply the migration chain through 045 exactly once.
- Restarting Compose preserves created users/projects.

## 5. Manual No-AI Smoke

Leave model configuration empty.

1. Register and log in.
2. Choose Growth mode.
3. Import a mixed batch with at least one valid and one invalid historical note.
4. Confirm or manually create a creator profile.
5. Create a blank opportunity or project.
6. Complete Brief with personal evidence manually.
7. Create and save a version.
8. Run deterministic publish checks.
9. Copy body/export available artifacts and record a publication.
10. Enter a performance snapshot manually.
11. Complete a review with one continue, stop, and experiment action.
12. Confirm one insight and reject another.

Expected:

- No page dead-ends because AI is absent.
- No output claims to be AI-generated when no call occurred.
- No model or preloaded content appears as a factual hotspot source.

## 6. AI Text Smoke

Configure a valid OpenAI-compatible text model and restart backend.

Validate:

- Starter direction candidates are grounded only in assessment evidence.
- Interview questions identify missing evidence and do not invent answers.
- Local rewrite suggestions do not mutate the current version until accepted.
- Every result exposes AI trace, configured model identifier, limitations, and decision controls.
- Invalid model JSON produces a typed error/manual path and retains user input.

## 7. Vision Capability Smoke

Only run when the configured endpoint supports vision and both capability/config flags enable it.

1. Upload a metrics screenshot.
2. Request extraction.
3. Review proposed values.
4. Correct one value and confirm.

Expected:

- Extraction creates no confirmed snapshot before user confirmation.
- Missing vision capability returns `AI_CAPABILITY_MISSING` and manual fields remain available.

## 8. Automated Release Gates

```powershell
cd G:\codex_project\topicAI\mvp\backend
python -m pytest --cov=app --cov-fail-under=80
ruff check app tests
mypy app
bandit -r app

cd G:\codex_project\topicAI\mvp
pnpm --dir frontend test -- --coverage
pnpm --dir frontend lint
pnpm --dir frontend build
pnpm --dir frontend test:e2e
pnpm audit --audit-level high
```

Required scenarios:

- All project state transitions and blocked transitions.
- Idempotent project/publish/snapshot operations.
- Owner isolation and deletion/export.
- Starter and growth E2E.
- Draft recovery and version conflict.
- AI configured/unconfigured/malformed/timeout/missing capability.
- Desktop 1440x900 and mobile 390x844 smoke.

## 9. Source-Integrity Scan

The v2 runtime must produce no matches for prohibited source/provider concepts:

```powershell
rg -n "llm_simulation|estimated_heat|composite_score|ctr_estimate|viral_probability|TianAPI|BilibiliSource|PreloadedDataSource" backend/app/api/v2 backend/app/services frontend/src/features frontend/src/services/api/v2
```

Expected result: no matches.

Also scan user-facing source for common mojibake markers and manually inspect any match:

```powershell
rg -n "锟|鈥|鎴|鐨|鍐|绔" frontend/src specs/008-content-project-mvp
```

## 10. Acceptance Completion

Release candidate is ready when:

- Constitution v3.0.0 gates pass.
- Spec checklist remains 16/16.
- API contract, data model, implementation, and frontend types agree.
- Fresh Docker startup and restart persistence succeed.
- Both onboarding modes reach a shared project.
- Growth loop reaches confirmed insight.
- Manual mode works without AI.
- No continuous hotspot/news source or copied secret/runtime data exists.
