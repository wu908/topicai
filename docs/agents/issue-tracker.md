# Issue tracker: GitHub

Issues and PRDs for this repository live in GitHub Issues:
`wu908/topicai`.

Use the `gh` CLI from inside this repository.

## Operations

- Create: `gh issue create --title "..." --body "..."`
- Read: `gh issue view <number> --comments`
- List: `gh issue list --state open`
- Comment: `gh issue comment <number> --body "..."`
- Label: `gh issue edit <number> --add-label "..."`
- Remove label: `gh issue edit <number> --remove-label "..."`
- Close: `gh issue close <number> --comment "..."`

Infer the repository from `git remote -v`.

## Pull requests as a triage surface

**PRs as a request surface: no.**

GitHub PRs are not included in the issue triage queue unless this flag is
changed to `yes`.

## Skill conventions

When a skill says "publish to the issue tracker", create a GitHub issue.

When a skill says "fetch the relevant ticket", run:

`gh issue view <number> --comments`
