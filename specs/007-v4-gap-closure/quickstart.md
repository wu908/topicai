# Quickstart: 007 TopicAI v4.1 Implementation-Gap Closure

**Feature**: 007-v4-gap-closure
**Date**: 2026-06-12
**Source spec**: [spec.md](./spec.md)
**Source plan**: [plan.md](./plan.md)
**Constitution**: v1.1.0

This quickstart is the acceptance-script for the 7 user stories in
spec.md. Each scenario is a curl-able (or `httpx`-callable) check
that maps to a success criterion in the spec.

## Prerequisites

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate  # Windows; on macOS/Linux use .venv/bin/activate
pip install -r requirements.txt
pip install "bcrypt==4.0.1" "pydantic[email]"

cp .env.example .env
# Fill DEEPSEEK_API_KEY for the LLM-path scenarios; leave empty
# for the template-fallback scenarios.

uvicorn "main:create_app" --factory --host 127.0.0.1 --port 8000 --reload
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 (frontend) and http://localhost:8000/docs
(API).

## Scenario A: US1 - Real LLM coach endpoints

Tests `idea_boost` (and analogously `title_optimize`,
`track_diagnose`, `publish_suggest`).

```bash
# Login first (replace with your test creds)
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"u@x.com","password":"password"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

# 1. With a key -- expect data_source="llm_simulation", confidence >= 0.6
curl -s -X POST http://localhost:8000/api/v1/ideas/boost \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"idea_text":"How to make a sourdough starter at home"}' \
  | python -m json.tool

# Look for: data_source == "llm_simulation", model_version present,
# confidence >= 0.6, key_assumptions with >= 3 items.

# 2. Without a key -- unset DEEPSEEK_API_KEY and restart, repeat:
# Expect: data_source == "template_fallback", confidence <= 0.5,
# response time < 1s.
```

## Scenario B: US2 - 4-tier data source

```bash
# 1. With no TIANAPI_KEY and a stub Bilibili response that raises,
#    expect data_source="preloaded", confidence <= 0.5
curl -s -X GET "http://localhost:8000/api/v1/topics/recommend?track=%E7%A7%91%E6%8A%80" \
  -H "Authorization: Bearer $TOKEN" \
  | python -m json.tool

# Look for: data["topics"] length >= 5, data_source == "preloaded".

# 2. With TIANAPI_KEY configured, expect data_source="tianapi",
#    confidence >= 0.6
#    (requires a real TIANAPI_KEY in .env)
```

Confirm tier shifts appear in LangFuse (if `LANGFUSE_PUBLIC_KEY` /
`LANGFUSE_SECRET_KEY` are set) and as `logger.warning` lines in the
server log.

## Scenario C: US3 - Feedback loop persists + adapts

```bash
# Establish an account, run a week of activity (or backdate the
# creator_profiles.created_at to > 7 days ago in a test fixture),
# then submit 5 thumb-down events on a single dimension.

for i in 1 2 3 4 5; do
  curl -s -X POST http://localhost:8000/api/v1/feedback \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"source_type":"title","source_id":"t-1","feedback_type":"thumb_down"}'
done

# Within 5 seconds, the creator_profiles.rubric_weights for this
# user should be updated. Inspect via:
sqlite3 backend/data/topicai.db \
  "SELECT user_id, rubric_weights FROM creator_profiles WHERE user_id='...'"

# Cold-start: a brand-new account should keep the default weights.
```

## Scenario D: US4 - Effect review lifecycle

```bash
# 1. Predict
REVIEW_ID=$(curl -s -X POST http://localhost:8000/api/v1/reviews/predict \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"topic_title":"Sourdough starter","content_outline":"Intro + 3 steps"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")

# 2. Attribute (after the content is published, with actuals)
curl -s -X POST "http://localhost:8000/api/v1/reviews/$REVIEW_ID/attribute" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"actual_data":{"views":4200,"likes":110,"comments":12}}'

# 3. Derive learnings
curl -s -X GET http://localhost:8000/api/v1/reviews/learnings \
  -H "Authorization: Bearer $TOKEN"

# Expect: at least 3-5 dimensional conclusions in step 2; a
# non-empty report in step 3.
```

## Scenario E: US5 - Content risk pre-publish guard

```bash
# Risky content
curl -s -X POST http://localhost:8000/api/v1/risk/check \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Our product guarantees 100% no-loss returns."}'
# Expect: risks[] contains severity="high", category="financial_inducement"

# Benign content
curl -s -X POST http://localhost:8000/api/v1/risk/check \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"We made pancakes this morning."}'
# Expect: risks=[], overall_risk_score < 0.2
```

## Scenario F: US6 - Onboarding LLM rubric_weights

```bash
# With a key -- the rubric_weights should reflect the answers
curl -s -X POST http://localhost:8000/api/v1/profiles/onboarding \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "track":"缇庨",
    "content_formats":["鐭棰?"],
    "production_complexity":"medium",
    "content_depth":"deep",
    "hotspot_preference":"evergreen"
  }'

# Expect: rubric_weights.content_depth_match > rubric_weights.hotspot_relevance.

# Without a key -- the response is the existing defaults.
```

## Scenario G: US7 - Coverage gate and missing endpoints

```bash
# 1. Coverage gate
cd backend
pytest --cov=app --cov-fail-under=80
# Expect: exit 0, coverage >= 80% lines.

cd ../frontend
pnpm vitest run --coverage
# Expect: exit 0, coverage threshold met.

# 2. Endpoint coverage -- the frontend's service methods all
#    resolve to real handlers:
pnpm playwright test frontend/e2e/full-loop.spec.ts
# Expect: exit 0, no 404s in the trace.
```

## Scenario H: AI transparency audit

```bash
# Grep the codebase for the forbidden "data_source":"ai_inference"
# (the v3.9 placeholder used by the no-op services).
grep -r "ai_inference" backend/app/ --include="*.py"
# Expect: 0 matches in services/ or api/v1/ (the data_sources/
# layer may still carry it for the preloaded fallback path;
# confirm by inspecting the response).
```

## Reset

```bash
# Wipe the local DB to start fresh
rm -f backend/data/topicai.db

# Or reset just the new tables (preserves users, profiles, etc.)
sqlite3 backend/data/topicai.db <<'SQL'
DELETE FROM user_feedback;
DELETE FROM effect_reviews;
DELETE FROM risk_keywords;
SQL
```

## Troubleshooting

- **"No LLMClient in services" warning in logs** -- expected during
  US1 dev. It means the heuristic path is running. Set
  `DEEPSEEK_API_KEY` to exercise the LLM path.
- **Tier-1 (TianAPI) returns 402 / 403** -- check the key in
  `.env`. TianAPI is a paid service; the free tier is 100
  calls / day.
- **Coverage gate fails on a refactor** -- the gate is a *floor*
  (Constitution Quality Gate 7). Adding code without tests is
  the only way to drop it; the fix is to add tests, not lower
  the threshold.
- **Migration runner hangs on startup** -- the
  `schema_migrations` table is in `001_bootstrap.sql`. If the
  file is missing, the runner logs `WARN migration file not
  found: 001_bootstrap.sql` and skips; the new tables
  (`user_feedback`, `effect_reviews`, etc.) will then fail to
  create.
