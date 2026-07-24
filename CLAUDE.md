# TopicAI v4.1 Implementation-Gap Closure — Claude Code Master Prompt

> This CLAUDE.md is the authoritative instruction set for Claude Code
> when implementing the v4.1 gap-closure plan.

---

## 1. Context & Authoritative Documents

This project has a complete Spec Kit design suite at `specs/007-v4-gap-closure/`:

| Document | Path | Role |
|---|---|---|
| **spec.md** | `specs/007-v4-gap-closure/spec.md` | 7 user stories (US1-US7), 13 functional requirements, 8 success criteria, 2 audit appendices |
| **plan.md** | `specs/007-v4-gap-closure/plan.md` | Technical context, constitution check (16 rules), phased delivery, risk tracking, codegraph evidence |
| **tasks.md** | `specs/007-v4-gap-closure/tasks.md` | **97 TDD-first tasks (T001-T097)** across 10 phases — THIS IS YOUR EXECUTION ORDER |
| **data-model.md** | `specs/007-v4-gap-closure/data-model.md` | 5 new tables + Mermaid ER diagram |
| **research.md** | `specs/007-v4-gap-closure/research.md` | 7 design decisions (D1-D7) with rationale |
| **quickstart.md** | `specs/007-v4-gap-closure/quickstart.md` | 8 curl-able acceptance scenarios (A-H) |
| **contracts/** | `specs/007-v4-gap-closure/contracts/openapi-fragment.yaml` | 14 endpoint OpenAPI 3.1 contracts |
| **checklists/** | `specs/007-v4-gap-closure/checklists/requirements.md` | Quality checklist (18 items pass) |

The governing constitution is `.specify/memory/constitution.md` (v1.1.0).

### Required startup reading order

Every session, read these in order before acting:

1. `specs/007-v4-gap-closure/spec.md`  — What we are building (7 user stories)
2. `specs/007-v4-gap-closure/plan.md`  — How we are building it (Constitution Check, risk tracking)
3. `specs/007-v4-gap-closure/tasks.md` — The execution plan (97 tasks, TDD-first, dependency-ordered)

---

## 2. Development Workflow (how you work)

### 2.1 Phase execution order — follow tasks.md strictly

```
Phase 1: Setup     (T001-T010) — gates, migration runner, prompts, fixtures
Phase 2: Foundational (T011-T016) — BLOCKS all user stories
Phase 3: US1 (P1)  (T017-T033) — Real LLM coach endpoints ← MVP
Phase 4: US2 (P1)  (T034-T046) — 4-tier data source routing
Phase 5: US3 (P2)  (T047-T057) — Feedback loop persists + adapts
Phase 6: US4 (P2)  (T058-T068) — Effect review lifecycle
Phase 7: US5 (P3)  (T069-T078) — Content risk pre-publish guard
Phase 8: US6 (P3)  (T079-T083) — Onboarding LLM rubric_weights
Phase 9: US7 (P2)  (T084-T089) — Coverage gate + missing endpoints
Phase 10: Polish   (T090-T097) — Cross-cutting improvements
```

**CRITICAL**: Complete Phase 2 before beginning any user story.

### 2.2 TDD discipline (Constitution Principle II — NON-NEGOTIABLE)

For every implementation task:

```
1. Write the test first  →  ensure it FAILS
2. Implement the minimum  →  ensure it PASSES
3. Refactor               →  ensure tests still GREEN
4. Verify coverage         →  must be >= 80%
```

### 2.3 Per-task workflow (use ECC skills)

Before coding any task, use ECC's built-in skills:

```
/search-first: Re-read the spec section for this task, the corresponding
  plan.md section, and any referenced existing code.

/tdd-workflow: Follow the TDD cycle for this task. Tests must fail
  before implementation.

/verification-loop: After implementation, verify the acceptance scenario
  from quickstart.md passes.

/code-review: After completing a logical group of tasks (a full user
  story phase), run a comprehensive code review.

/quality-gate: Before declaring a phase complete, run the quality gate
  check against the constitution.
```

---

## 3. Constitution Rules (must always obey)

All code must pass these gates. THE FOLLOWING ARE HARD BLOCKS:

1. **I. Service-Layer Architecture** — Business logic in `app/services/` or `app/chains/` only. FastAPI endpoints delegate, never implement.
2. **II. Test-First Discipline** — Red → Green → Refactor. Coverage >= 80% (Quality Gate 7).
3. **III. AI Transparency** — Every AI response carries `confidence`, `data_source`, `model_version`.
4. **VI. Hybrid AI Discipline** — Heuristic-first, LLM only when heuristic confidence is low or `analysis_depth="deep"`.
5. **VII. Schema-Validated Contracts** — Pydantic on every boundary. Chain outputs parseable into Pydantic.
6. **VIII. Data Source Tiered Fallback** — 4-tier cascade with per-tier config, structured logs on every tier shift.
7. **XIII. Security & Data Minimization** — JWT only. Secrets from `.env`. 90-day content TTL. Rate limiting.

### Mock pattern (for all LLM-calling services)

```python
# Test the LLM path
def test_llm_path_returns_structured(mock_llm):
    mock_llm.return_value = valid_json_fixture
    result = service.do_thing()
    assert result.data_source == "llm_simulation"
    assert result.confidence >= 0.6

# Test the fallback path
def test_fallback_returns_schema_with_low_confidence(mock_llm):
    mock_llm.side_effect = Exception("LLM unavailable")
    result = service.do_thing()
    assert result.data_source == "template_fallback"
    assert result.confidence <= 0.5
```

---

## 4. ECC Integration (skills to use actively)

### Phase 1 (Setup): Use these ECC skills

| ECC Skill | When |
|---|---|
| `search-first` | Before creating any new file, verify it doesn't already exist |
| `coding-standards` (Python) | When writing `backend/pyproject.toml`, `runner.py` |
| `database-migrations` | When creating `NNN_*.sql` files |

### Phase 2 (Foundational): Use these

| ECC Skill | When |
|---|---|
| `database-migrations` | Creating 002-005 SQL migrations |
| `api-design` | Defining Pydantic models for the new entities |

### Phase 3-8 (User Stories): Use these

| ECC Skill | When |
|---|---|
| `tdd-workflow` | Every implementation task (tests first!) |
| `backend-patterns` | Writing FastAPI services, chains, endpoints |
| `frontend-patterns` | Updating React pages and components |
| `verification-loop` | After each user story checkpoint |
| `e2e-testing` | Writing Playwright scenarios (US3, US4, US7) |
| `security-review` | After US5 (risk check endpoint) and US7 (coverage gate) |
| `code-review` | After each user story phase completes |

**IMPORTANT**: The `ecc:` namespace prefix IS NOT needed for manually-installed ECC.

---

## 5. Quality Gates (must pass before advancing phases)

At the end of **every** phase, run these checks:

- [ ] `pytest --cov=app --cov-fail-under=80` — backend coverage gate
- [ ] `pnpm vitest run --coverage` — frontend coverage gate
- [ ] `ruff check` + `mypy` — backend lint + types
- [ ] `eslint .` + `tsc --noEmit` — frontend lint + types
- [ ] All new AI endpoints carry `confidence`, `data_source`, `model_version`
- [ ] Business logic is in `app/services/` or `app/chains/`, not in route handlers

Before declaring the project complete, verify ALL 8 acceptance scenarios in `quickstart.md`:

- Scenario A: US1 — Real LLM coach endpoints
- Scenario B: US2 — 4-tier data source
- Scenario C: US3 — Feedback loop persists + adapts
- Scenario D: US4 — Effect review lifecycle
- Scenario E: US5 — Content risk guard
- Scenario F: US6 — Onboarding LLM weights
- Scenario G: US7 — Coverage gate + endpoints
- Scenario H: AI transparency audit (zero `data_source="ai_inference"` in production paths)

---

## 6. Decision Tree (when you encounter ambiguity)

```
Q: Should I call the LLM or use a heuristic?
→ Constitution Principle VI: heuristic FIRST, LLM only if confidence < threshold

Q: Where should this business logic live?
→ Constitution Principle I: app/services/ or app/chains/. Never in api/v1/.

Q: Does this need a Pydantic model?
→ Constitution Principle VII: YES, for every request and response that crosses a boundary.

Q: What data_source should this return?
→ LLM success: "llm_simulation"
→ Heuristic: "heuristic" or "preloaded"
→ Fallback/error: "template_fallback" (NEVER silently claim real LLM)

Q: Is this task a blocker for the next phase?
→ Check the Phase Dependencies section in tasks.md

Q: Should I modify existing code or create new files?
→ Prefer modifying existing files (per plan.md "Modified backend files" section).
→ Only create new files when plan.md explicitly lists them under "New backend files".
```

---

## 7. File Path Quick Reference

### Services to rewrite (US1, US2, US5, US6)

| Service | Path | What changes |
|---|---|---|
| idea_booster | `backend/app/services/idea_booster.py` | Add `_analyze_with_llm()` + `_template_xxx()` |
| title_optimizer | `backend/app/services/title_optimizer.py` | Same pattern |
| track_diagnosis | `backend/app/services/track_diagnosis.py` | Same pattern |
| publish_advisor | `backend/app/services/publish_advisor.py` | Same pattern |
| topic_recommend | `backend/app/services/topic_recommend.py` | Delegate to DataManager |
| feedback | `backend/app/services/feedback.py` | Persist to DB + trigger profile update |
| content_risk | `backend/app/services/content_risk.py` | Add LLM layer (80/20 blend) |
| effect_review | `backend/app/services/effect_review.py` | Persist to DB |
| onboarding | `backend/app/services/onboarding.py` | Real LLM call for rubric_weights |

### New endpoints needed

| Endpoint | File | Task |
|---|---|---|
| `POST /api/v1/risk/check` | `backend/app/api/v1/risk_router.py` (NEW) | T074 |
| `GET /api/v1/topics/history` | `backend/app/api/v1/topics.py` (modify) | T046 |
| `GET /api/v1/feedback/history` | `backend/app/api/v1/feedback.py` (modify) | T057 |
| `GET /api/v1/reviews/learnings` | `backend/app/api/v1/reviews.py` (modify) | T066 |
| `GET /api/v1/reviews/list` | `backend/app/api/v1/reviews.py` (modify) | T066 |

---

## 8. Session Start Ritual (do this every session)

1. Read `specs/007-v4-gap-closure/spec.md` (user stories and requirements)
2. Read `specs/007-v4-gap-closure/plan.md` (constitution check, risks)
3. Read `specs/007-v4-gap-closure/tasks.md` (find next incomplete task)
4. Verify `git status` is clean (no unrelated changes)
5. Announce: "Starting Phase X, Task T00X: [description]"

---

## 9. Emergency Rules

- **If a test fails**: Fix the test within the same session. Do not proceed to the next task with failing tests.
- **If the LLM returns malformed JSON**: Use `_clean_json_response` (in `backend/app/core/llm/`). If unrecoverable, fall back to template path and log a `logger.warning`.
- **If coverage drops below 80%**: This is a release blocker per Constitution Quality Gate 7. Add missing tests before merging.
- **If you need to create a new migration**: Follow the `NNN_topic.sql` pattern. Add it to the `schema_migrations` table via the runner. NEVER use ad-hoc SQL in app code.

## Agent skills

### Issue tracker

Issues and PRDs are tracked in GitHub Issues for `wu908/topicai`. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default canonical triage labels. See `docs/agents/triage-labels.md`.

### Domain docs

Use the single-context layout with root `CONTEXT.md` and `docs/adr/`. See `docs/agents/domain.md`.
