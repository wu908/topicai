<!-- SPECKIT START -->
## Active Rebuild

- Read `specs/008-content-project-mvp/plan.md` first. Use its adjacent `spec.md`,
  `research.md`, `data-model.md`, `contracts/api-v2.md`, `quickstart.md`, and
  `tasks.md` as needed.
- `.specify/memory/constitution.md` v3.0.0 governs and overrides copied v4
  assumptions.
- Implement only in this copied repository; do not edit the source repository.
- Reuse auth, database/migrations, API envelope, storage, feedback, risk,
  observability, MUI, Zustand, and test infrastructure before adding new code.
- `/api/v2` is the only public API and `ContentProject` is the product aggregate.
  Do not add v1 routes, compatibility shims, legacy data sources, or named-provider
  runtime code. Keep historical SQL migrations only for safe database upgrades.
- Configure AI through an OpenAI-compatible endpoint; never use it as a factual
  source for realtime claims or user experience.
- Write tests before implementation and keep backend/frontend coverage >=80%.
- Do not copy `.env`, databases, Chroma data, uploads, keys, caches, generated
  output, agent worktrees, or source Git metadata into the project.
- Treat Spec-007 as historical implementation context: reuse completed
  foundations, not fixed providers, hotspot cascades, fake precision,
  independent tool pages, or prediction-oriented product assumptions.
<!-- SPECKIT END -->

## Windows Development and Docker Validation

- `G:\codex_project\topicAI\mvp` is the only source tree; WSL exposes the same
  files at `/mnt/g/codex_project/topicAI/mvp`. Do not create another clone or
  make lasting source changes inside containers.
- Keep ordinary editing, Git, dependencies, builds, unit tests, linting, and
  type checks in PowerShell.
- For Docker Compose, full-stack runtime, or container validation, explicitly
  invoke `$windows-wsl-docker-validation`. Read
  `docs/agents/wsl-docker-development.md` for project-specific paths, commands,
  and volume retention; do not duplicate the Skill workflow here.
- Improve that Skill only after a reproducible gap and stop at its stated
  maturity limit.
