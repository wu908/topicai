# Domain Docs

This repository uses a single-context domain documentation layout.

## Reading order

Before exploring domain behavior, read these files when they exist:

1. `CONTEXT.md`
2. Relevant ADRs under `docs/adr/`

Missing files are not errors. Continue silently. Create domain documentation
only when terminology or architectural decisions need to be recorded.

## Layout

- `CONTEXT.md`: domain glossary, boundaries, invariants, and avoided synonyms.
- `docs/adr/`: repository-wide architectural decisions.

Use terminology defined in `CONTEXT.md`. If work conflicts with an existing
ADR, identify that conflict explicitly instead of silently overriding it.
