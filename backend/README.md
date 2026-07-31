# TopicAI Backend

> FastAPI + SQLAlchemy + LangChain service for the TopicAI v4.0 "Air Pro" stack.

This README is the **runbook** for backend development. The architectural
intent lives in `specs/007-v4-gap-closure/spec.md`; the engineering
governance lives in `.specify/memory/constitution.md`.

---

## Quality Gates (Constitution Principle II)

| Gate | Command | Floor | Status |
|---|---|---|---|
| Backend coverage | `pytest tests/ -q --cov=app --cov=config` | **≥ 80%** | RED (baseline 69.10% at 2026-06-07) |
| Ruff lint | `ruff check app/ tests/` | 0 errors | enforce in CI |
| Mypy | `mypy app/ config/` | 0 errors | warn-only for now |
| Pytest | `pytest tests/ -q` | 274+ passing | live |

The coverage gate is **enforced** in `pyproject.toml` via
`[tool.coverage.report].fail_under = 80`. A PR that drops coverage below
80% is blocked from merge. The floor is constitutional; lowering it
requires a constitution amendment (Constitution Principle II).

### TDD rhythm for service code

1. Write a failing test that captures the contract (e.g. `data_source`,
   `confidence`, `model_version`).
2. Run the test — it should be RED.
3. Write the minimum implementation to make it GREEN.
4. Refactor (IMPROVE).
5. Re-run coverage — gate must stay GREEN.

The canonical mock pattern for LLM-touching services is:

```python
with patch("app.services.idea_booster.LLMClient") as MockLLM:
    MockLLM.return_value.generate.return_value = '{"id": "...", ...}'
    result = svc.boost("u1", "some idea")
    assert result["data_source"] == "llm_simulation"
    assert result["confidence"] >= 0.6
```

See `.specify/memory/constitution.md` Principle II for the full contract.

---

## Running tests

```bash
# Install runtime and development dependencies
pip install -r requirements-dev.txt

# All tests with coverage gate
pytest tests/ -q

# One module
pytest tests/services/test_idea_booster.py -v

# Skip slow tests
pytest tests/ -q -m "not slow"

# Coverage report only
pytest tests/ --cov=app --cov=config --cov-report=term-missing
```

## Running the server

```bash
# Activate venv
source .venv/Scripts/activate   # Windows
# source .venv/bin/activate      # macOS/Linux

# Dev server with reload
uvicorn "main:create_app" --factory --host 127.0.0.1 --port 8000 --reload

# E2E port (matches frontend vite proxy)
uvicorn "main:create_app" --factory --host 127.0.0.1 --port 8765
```

## Database

- Default: SQLite at `data/topicai.db` (auto-created on first start).
- For migrations see `app/data/migrations/` (runner lands in Phase 2,
  T003-T005 per `specs/007-v4-gap-closure/tasks.md`).
