<!-- SPECKIT START -->
For the active rebuild, read `specs/008-content-project-mvp/plan.md` first.
Supporting artifacts are in the same directory: `spec.md`, `research.md`,
`data-model.md`, `contracts/api-v2.md`, `quickstart.md`, and `tasks.md`.

The governing Constitution is `.specify/memory/constitution.md` (v2.0.0).
It supersedes the copied v4 assumptions about fixed model vendors, simulated
hotspots, preloaded trend fallback, and predicted content performance.

## Spec-008 operating rules

- Implement only in this copied repository; do not edit the source repository.
- Reuse auth, database/migrations, API envelope, storage, feedback, risk,
  observability, MUI, Zustand, and test infrastructure before adding new code.
- New product behavior uses `/api/v2` and the `ContentProject` aggregate.
- New v2 code must not call legacy `DataManager`, `LLMDataSource`, TianAPI,
  Bilibili, or preloaded trend sources.
- AI is configured through an OpenAI-compatible endpoint and never acts as a
  factual source for realtime claims or user experience.
- Tests precede implementation and backend/frontend coverage remains >=80%.
- Do not copy `.env`, local databases, Chroma data, uploads, keys, caches,
  generated output, agent worktrees, or source Git metadata into the project.

## Copied v4 baseline

Spec-007 is retained as historical implementation context. Its completed auth,
migration, feedback, risk, profile, asset, and test foundations are candidates
for reuse. Its fixed provider routing, tiered hotspot cascade, fake precision,
independent tool pages, and prediction-oriented effect review are not the active
product contract.
<!-- SPECKIT END -->
