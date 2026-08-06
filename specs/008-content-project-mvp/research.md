# Research: TopicAI Content Project MVP

**Feature**: `008-content-project-mvp`  
**Date**: 2026-07-17  
**Method**: Product-document review, CodeGraph call-path inspection, manifest/schema review, and a read-only baseline test run against the source repository.

## Decision 1: Fork a clean working copy instead of editing the source repository

**Decision**: Implement only in `G:\codex_project\topicAI\mvp`. Exclude `.git`, `.codegraph`, agent worktrees, `node_modules`, virtual environments, caches, builds, test artifacts, `.env`, local databases, Chroma data, logs, uploads, and user/API secrets.

**Rationale**: The source worktree contains untracked user documents and local configuration. A clean copy protects the original, creates a fresh-data MVP, and prevents runtime data or credentials from leaking into the new project.

**Alternatives considered**:
- Edit the source in place: rejected because it risks user changes and mixes old/new product behavior.
- Copy runtime data: rejected because old tool records do not map cleanly to the new aggregate.

## Decision 2: Keep the existing stack and replace domain behavior incrementally

**Decision**: Retain React/Vite/MUI/Zustand/TypeScript, FastAPI/Pydantic/SQLAlchemy/SQLite, the migration runner, Docker Compose, pytest/Vitest/Playwright, and existing shared UI/API infrastructure.

**Rationale**: The source already has 681 collected backend tests, typed API envelopes, auth, owner scoping, migrations, local storage, feedback, risk checks, observability hooks, and Docker. Re-platforming would add risk without improving the core product hypothesis.

**Alternatives considered**:
- New frontend framework or design system: rejected; no product requirement justifies it.
- New database or event system: rejected for local MVP scale.

## Decision 3: Use a reuse matrix, not a blanket rewrite

| Existing area | Decision | Required change |
|---|---|---|
| JWT auth, auth middleware, password hashing | Direct reuse | Preserve routes and owner scoping; add onboarding mode fields through migration |
| `ApiResponse`, error handlers, `useApi`, API client | Direct reuse | Add v2 domain services and typed errors |
| Database, migration runner, backup abstraction | Direct reuse | Add migrations 009+; fix writable-path tests in copied workspace |
| MUI theme, `AppLayout`, common loading/empty/modal components | Adapt reuse | Replace nine-tool sidebar with five-node IA; replace manual SVG icons with MUI icons |
| Zustand auth/profile stores | Adapt reuse | Add onboarding/project stores and local draft recovery; remove obsolete tool state |
| Creator profile service and page | Adapt reuse | Replace v4 rubric fields with evidence-backed, user-confirmable profile fields |
| Asset service, local object storage, asset API | Adapt reuse | Rename user-facing concept to Material; add text/link kinds, privacy, project links, reference snapshots |
| Feedback service and components | Adapt reuse | Make feedback target generic; stop automatic rubric-weight mutation |
| Content risk service and rules | Adapt reuse | Bind reports to content version; expose locations, rule provenance, staleness, acknowledgement |
| LLM client, prompt registry, structured-output parser | Adapt reuse | Collapse vendor-specific config to one OpenAI-compatible boundary and capability declaration |
| Effect review persistence | Adapt reuse | Remove predictions; add append-only snapshots, fact/hypothesis/experiment review, confirmed insights |
| Account service | Minimal reuse | Restrict MVP UI to one primary Xiaohongshu reference; no OAuth/sync implementation |
| Topic recommendation/DataManager/data sources | Delete | V2 opportunities use first-party evidence and manual source intake only |
| Idea/title/viral/publish-time independent services/pages | Delete | Their approved behavior is represented inside ContentProject services |
| Team service and team pages | Delete | Team/MCN behavior is outside the MVP |

## Decision 4: Introduce a new v2 domain contract

**Decision**: `/api/v2/` is the only public API. It includes authentication, health, onboarding, opportunities, content projects, publication, performance, reviews, and account-data operations. Removed v1 paths return the standard not-found response.

**Rationale**: `TopicItem`, title optimization, publish advice, and effect prediction contain breaking concepts such as estimated heat, composite scores, CTR estimates, fixed models, and performance forecasts. Mutating those response shapes under v1 would violate the Constitution.

**Alternatives considered**:
- Rewrite v1 in place: rejected because it silently breaks clients and tests.
- Keep compatibility shims after the v2 release: rejected because they retain duplicate runtime behavior and dependencies.

## Decision 5: Make ContentProject the aggregate and SQLite the transaction boundary

**Decision**: Persist project state and child entities in normalized SQLite tables. State transition, idempotency, version locking, and owner checks execute in a single service-layer transaction. Optimistic concurrency uses an integer `version` field.

**Rationale**: The workflow needs auditable versions and atomic transitions, but MVP scale does not justify a workflow engine or event store.

**Alternatives considered**:
- Store the project as one JSON blob: rejected because version, publish, metrics, and deletion queries become fragile.
- Add a workflow/orchestration dependency: rejected by YAGNI.

## Decision 6: Configure one provider-neutral OpenAI-compatible model boundary

**Decision**: Runtime config uses `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, timeouts, and declared capabilities such as `text` and `vision`. Product code never selects a named vendor. Missing capability returns a typed unavailable result and manual fallback.

**Rationale**: This matches the user's explicit preference and avoids coupling product semantics to a provider. The existing OpenAI client and structured parser remain reusable.

**Alternatives considered**:
- Preserve fixed DeepSeek/Qwen/GLM tiers: rejected by product direction and Constitution v3.0.0.
- Automatically probe arbitrary models: rejected because capability probing is unreliable and complicates deterministic tests.

## Decision 7: Remove fake precision and simulated hotspot fallback

**Decision**: Opportunity dimensions are qualitative enums with evidence and rationale. P0 uses history, questions, materials, series, evergreen needs, and user-triggered hotspot input. `LLMDataSource`, preloaded trends, TianAPI/Bilibili cascade, estimated heat, composite score, CTR forecast, and predicted performance are excluded from the new contract.

**Rationale**: The product cannot calibrate virality probabilities before real user data and must not present generated text as real-time evidence.

**Alternatives considered**:
- Keep old scores as internal ranking only: rejected because they still shape recommendations without a validated basis.
- Integrate Firecrawl or news feeds in P0: rejected; the product research explicitly requires validation before continuous sources. Firecrawl remains a research tool, not an MVP runtime dependency.

## Decision 8: Use lightweight editing and immutable snapshots

**Decision**: Build the first editor from existing MUI inputs plus structured title/body/cover/image-plan sections. Autosave produces mutable working draft state; explicit save, accepted suggestion, and publish selection create immutable `ContentVersion` rows. No rich-text framework is added in P0.

**Rationale**: Current writing UI is a simple TextField-based tool, not a reusable editor. A rich-text dependency would delay the end-to-end hypothesis; Xiaohongshu graphic notes can be represented with structured plain text and image plans in MVP.

**Alternatives considered**:
- Add TipTap/Lexical: deferred until formatting needs are validated.
- Edit immutable versions in place: rejected because it destroys audit and publish reproducibility.

## Decision 9: Immutable migration history and audited cleanup

**Decision**: Keep every historical migration so old databases can upgrade. Migration 045 converts reused asset data to `materials`, rebuilds `creator_profiles` with v2 columns, and drops the v1-only tables after the local data audit. Tests prove fresh bootstrap and upgrade-data preservation.

**Rationale**: Runtime compatibility code can be deleted without making existing user/profile/v2 data disposable.

**Alternatives considered**:
- Rewrite `000_initial_schema.sql`: rejected because the baseline is frozen.
- Delete migration history: rejected because existing databases would no longer be upgradeable.

## Decision 10: Local Docker is the release environment

**Decision**: Acceptance is based on Docker Compose with fresh volumes, plus local Vite/Uvicorn parity. No public cloud, domain, TLS, billing, or production SLO work is included.

**Rationale**: The current goal is a runnable MVP for later user validation.

## Baseline Findings and Planning Implications

- Source backend collection: 681 tests.
- Read-only source run reached 641 passing tests; 37 errors and 3 failures were observed. Most errors came from the source path being non-writable for temporary SQLite, backup, storage, and coverage files. One integration assertion also failed and must be reproduced in the writable copy before implementation.
- Frontend source contains mojibake in several Chinese strings. UTF-8 normalization and a regression check are required before UI work.
- The old project reports an 80% coverage floor, but the fresh-copy baseline must be rerun in a writable environment before claiming it passes.
- Source Git had untracked user documents and local config; none were altered.

## Resolved Clarifications

- Target directory: `G:\codex_project\topicAI\mvp`.
- Audience: shared foundation with lightweight starter entry and complete growth loop.
- Authentication: preserve login/registration.
- Runtime data: fresh database and files.
- Model: any operator-configured OpenAI-compatible endpoint; no fixed vendor/model.
- Validation: local Docker end-to-end.
- Hotspots: manual intake only; no continuous feeds in P0.
