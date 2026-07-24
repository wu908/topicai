# TopicAI Handoff

Generated: 2026-07-23

## Immediate objective

Review and deliver the current Phase 21 calibration-completeness work. The
likely next action is to make logical commits, push the branch, open/review a
PR, merge it after CI, and then choose the next incomplete product phase.

## Repository state

- Repository: `G:\codex_project\no_1_project\mvp`
- Remote: private GitHub repository `wu908/topicai`
- Current branch: `agent/phase-21-calibration-completeness`
- HEAD: `13e5ca9 feat: automate synthetic acceptance matrix`
- `origin/main`: `e5ce70c Close trust and privacy boundaries for AI-native loop (#12)`
- Phase 20 is one local commit on top of `origin/main`; Phase 21 is currently
  uncommitted on top of Phase 20.
- The worktree is intentionally dirty. Do not discard or reset any changes.
- `.codegraph/` exists; use CodeGraph before grep/file-by-file exploration.
- Ponytail full mode is active.

Run `git status --short --branch`, `git diff --stat`, and
`git log origin/main..HEAD` for the current file-level state rather than relying
on this snapshot.

## Existing source of truth

Do not restate or redesign completed work. Read these artifacts:

- Spec 009 tasks: `specs/009-ai-native-action-loop/tasks.md`
- Phase 21 contract and validation:
  `specs/009-ai-native-action-loop/phase-21-calibration-completeness.md`
- Data model: `specs/009-ai-native-action-loop/data-model.md`
- Governing repository instructions: `AGENTS.md`
- Existing Claude instructions plus newly added agent configuration:
  `CLAUDE.md`

## Completed but uncommitted

Phase 21 closes Spec 009 tasks T034, T036, T039, and T042. Its implementation,
boundaries, and acceptance evidence are recorded in the Phase 21 document
above. The latest full backend gate reported there is:

- `803 passed`, `1 deselected`
- `86.95%` coverage
- `git diff --check` passed

Separately, the prompt-driven `setup-matt-pocock-skills` setup was completed:

- `CLAUDE.md` has one new `## Agent skills` block.
- `docs/agents/issue-tracker.md` selects GitHub Issues for `wu908/topicai`.
- `docs/agents/triage-labels.md` uses the five default canonical labels.
- `docs/agents/domain.md` selects a single-context layout.
- No empty `CONTEXT.md` or `docs/adr/` scaffolding was created; domain docs are
  intentionally lazy.

The pre-existing body of `CLAUDE.md` still describes the historical v4.1 plan.
Only the approved agent-skills block was added. Do not silently rewrite the
surrounding file as part of Phase 21 delivery.

## Recommended next steps

1. Review `origin/main..HEAD` and the uncommitted diff for correctness and
   accidental scope. Keep Phase 21 and agent-skill setup as separate logical
   commits even if they share one PR.
2. Confirm no generated test artifacts are staged. A mistaken
   `backend/backend/.ci-tmp` directory was already removed; normal ignored
   `.ci-tmp` artifacts may remain.
3. Rerun only the checks needed after review. The full backend gate already
   passed after Phase 21 implementation; documentation-only agent setup does
   not require another full test run unless code changes.
4. Push `agent/phase-21-calibration-completeness`. The PR will contain the
   Phase 20 commit plus the Phase 21 commit because Phase 20 is not in
   `origin/main`.
5. Use the GitHub integration for PR creation, review, CI observation, and
   merge. Previous direct GitHub network access from the local shell was
   unreliable.
6. After merge, update local `main`, inspect Spec 009 completion state, and
   select the next genuinely incomplete phase rather than creating speculative
   work.

## Guardrails

- Keep the repository private.
- Never include local credentials, API keys, databases, uploads, caches, or
  generated output in commits.
- Do not weaken the existing backend/frontend CI gates.
- Reuse existing services and contracts; no speculative abstractions.
- Preserve human gates: no automatic publishing, public disclosure, confirmed
  content overwrite, or automatic long-term learning writes.

## Suggested skills

- `code-review`: review Phase 20 plus Phase 21 before committing.
- `ponytail:ponytail-review`: catch unnecessary abstractions or duplicated
  mechanisms without weakening trust boundaries.
- `github:yeet`: publish the reviewed local commits and open the PR.
- `github:github`: inspect PR state, reviews, checks, and merge readiness.
- `github:gh-fix-ci`: use only if GitHub Actions fails.
- `domain-modeling`: use later when a real glossary or ADR need appears; it is
  not required for the current delivery.

## Sensitive-data note

No API keys, passwords, email addresses, tokens, or other personal identifiers
are included in this handoff.
