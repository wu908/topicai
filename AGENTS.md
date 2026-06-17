<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan at
`specs/007-v4-gap-closure/plan.md` (with the supporting spec, data model,
contracts, quickstart, research, and tasks in the same directory).
The governing Constitution is `.specify/memory/constitution.md` (v1.1.0).
The v4.0 roadmap source audit lives at `.claude/plans/topicai-feature-audit-and-roadmap.plan.md`.
The v4.1 implementation-gap-closure is tracked in `specs/007-v4-gap-closure/tasks.md`.

## Spec-007 progress (as of Phase 10 Polish)

Phases 1-2 (Setup + Foundational) and all 7 user stories (US1-US7) plus
Phase 10 Polish (T090-T097) are complete as of commit `9199613`-line.
Remaining in spec-007: T084-T089 (CI/E2E scope — explicitly deferred
per directive; out of scope for backend-only delivery).

### Sync Impact Report (T097 audit)

- 7 Constitution principles surfaced for spec-007 (I, II, III, VI, VII,
  VIII, XIII) — none added beyond spec-006; spec-006's `data_source`
  transparency + 4-tier cascade additions still cover the surface.
- New endpoints exposed (US7): `/api/v1/feedback/history`,
  `/api/v1/reviews/learnings`, `/api/v1/reviews/list`,
  `/api/v1/risk/check`. All carry Pydantic-validated responses.
- New persistence tables (Phase 2): `user_feedback`, `effect_reviews`,
  `risk_keywords`, `platform_tokens`.
- New chains: `EffectReviewChain` (US4).
- Coverage gate held throughout: 80.51% backend line coverage with
  `pytest --cov=app --cov-fail-under=80` enforced in `pyproject.toml`.

<!-- SPECKIT END -->
