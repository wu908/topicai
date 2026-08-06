# TopicAI Backend

FastAPI backend for the v2-only `ContentProject` product.

## Runtime

- Public API: `/api/v2`
- Health: `/api/v2/health`
- Auth: `/api/v2/auth/register`, `/login`, `/refresh`, `/me`
- Materials/settings: `/api/v2/materials`, `/api/v2/settings`
- Publish guard: version-bound `/api/v2/projects/{id}/publish-checks`
- Owner data: HumanGate-confirmed export and deletion with persisted job state; deletion revokes credentials and quarantines files until its database transaction commits
- Storage: SQLite plus local object storage
- AI: one optional OpenAI-compatible endpoint

Copy `.env.example` to `.env`, set a strong `JWT_SECRET_KEY`, and optionally set `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, and `LLM_CAPABILITIES`.

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:create_app --factory --host 127.0.0.1 --port 8000 --reload
```

## Quality Gates

```powershell
.\.venv\Scripts\python.exe -m ruff check app config tests main.py
.\.venv\Scripts\mypy.exe --no-site-packages app config
.\.venv\Scripts\bandit.exe -q -r app -lll
.\.venv\Scripts\python.exe -m pytest -q --cov=app --cov=config --cov-report=term-missing --cov-fail-under=80
```

Migrations under `app/data/migrations/` are the only schema authority. Keep historical migrations for upgrades; migration 045 removes v1 business tables, 046 closes release contracts, 047 persists minimal export/deletion job audit state, and 048 closes credential/export/screenshot audit findings. Migration 048 preserves screenshot-extraction audit records when a material or snapshot is deleted by setting those references to `NULL`. `openapi3.json` is generated from `main:create_app` and must contain no `/api/v1` paths.
