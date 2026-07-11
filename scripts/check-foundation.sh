#!/usr/bin/env bash
# TopicAI Foundation Quality Gate
# Runs all checks: backend (pytest + ruff + mypy) and frontend (vitest + eslint + tsc)
# Exit 0 only if all pass.

set -euo pipefail
cd "$(dirname "$0")/.."

FAIL=0

echo "=== [1/6] Backend: ruff check ==="
(cd backend && .venv/Scripts/python -m ruff check app tests) || { echo "RUFF FAILED"; FAIL=1; }

echo "=== [2/6] Backend: mypy ==="
(cd backend && .venv/Scripts/python -m mypy app) || { echo "MYPY FAILED"; FAIL=1; }

echo "=== [3/6] Backend: pytest with coverage gate ==="
(cd backend && .venv/Scripts/python -m pytest tests/ --cov=app --cov-fail-under=80 --tb=short -q) || { echo "PYTEST FAILED"; FAIL=1; }

echo "=== [4/6] Frontend: tsc --noEmit ==="
(cd frontend && pnpm exec tsc --noEmit) || { echo "TSC FAILED"; FAIL=1; }

echo "=== [5/6] Frontend: eslint ==="
(cd frontend && pnpm exec eslint src) || { echo "ESLINT FAILED"; FAIL=1; }

echo "=== [6/6] Frontend: vitest run ==="
(cd frontend && pnpm exec vitest run) || { echo "VITEST FAILED"; FAIL=1; }

if [ "$FAIL" -eq 0 ]; then
  echo "=== ALL CHECKS PASSED ==="
  exit 0
else
  echo "=== SOME CHECKS FAILED ==="
  exit 1
fi