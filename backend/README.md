# TopicAI Backend

FastAPI backend for the v2-only `ContentProject` product.

## Runtime

- Public API: `/api/v2`
- Health: `/api/v2/health`
- Auth: `/api/v2/auth/register`, `/login`, `/refresh`, `/me`
- Storage: SQLite plus local object storage
- AI: one optional OpenAI-compatible endpoint

Copy `.env.example` to `.env`, set a strong `JWT_SECRET_KEY`, and optionally set `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, and `LLM_CAPABILITIES`.

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:create_app --factory --host 127.0.0.1 --port 8000 --reload
```

## Quality Gates

```powershell
.\.venv\Scripts\python.exe -m ruff check app config tests main.py
.\.venv\Scripts\python.exe -m pytest -q --cov=app --cov=config --cov-report=term-missing --cov-fail-under=80
```

Migrations under `app/data/migrations/` are the only schema authority. Keep historical migrations for upgrades; the final schema is v2-only after migration 045.
