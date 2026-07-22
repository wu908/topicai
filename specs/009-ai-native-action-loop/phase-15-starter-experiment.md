# Phase 15: Bounded Starter Experiment

**Status**: Contract frozen for implementation

## Outcome

Give a person with a vague or absent content idea one bounded way to start:

```text
real assets and constraints
-> readiness check
-> at most three grounded directions
-> user selects one experiment
-> exactly three linked ContentProjects
-> existing NextBestAction lifecycle
-> review observed evidence
```

This is an onboarding path, not a second content workflow and not a permanent
account label. Every generated project enters the existing
`confirm_intent -> evidence -> candidate -> publish -> review -> learning`
protocol.

## Frozen Rules

### Readiness

An assessment is `ready` only when all of the following are true:

- `available_hours_per_week > 0`;
- the user explicitly intends to publish;
- the user accepts that the result is a temporary experiment;
- at least one experience, interest, or skill remains after privacy limits are
  applied.

It is `paused` when time, publication commitment, or experiment consent is
missing. It is `not_ready` when willingness exists but no usable first-party
asset exists. Both states preserve the assessment and can be resubmitted.

### Direction candidates

- Generate at most three candidates, using only user-supplied experience,
  skill, and interest assets.
- Privacy limits are exclusion rules and never become content inputs.
- Every candidate names its evidence references and contains exactly three
  low-cost experiment topics.
- Candidate generation has a deterministic no-model fallback and an AI trace.
- Candidate copy must not claim a correct/permanent niche, guaranteed traffic,
  follower growth, virality, or monetization.
- Exactly one candidate can be selected for an assessment.

### Starter sprint

- Selecting a direction creates one 14-day sprint and exactly three projects.
- Selection and project creation are idempotent. A retry returns the same
  sprint and project IDs.
- Projects use `primary_goal=experiment`, `content_format=graphic_note`, and
  retain `starter_sprint_id`.
- Topic intent is only a candidate. The existing intent HumanGate remains the
  first irreversible confirmation.
- The sprint can be reviewed after at least one linked project is published.
- Review reports observed completion and user-supplied next experiments. It
  never upgrades a direction into a permanent niche conclusion.

## API Contract

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v2/starter` | Resume the current assessment, candidates, sprint and linked projects |
| `POST` | `/api/v2/starter/assessment` | Create or revise the bounded assessment |
| `POST` | `/api/v2/starter/directions:generate` | Generate or replay grounded direction candidates |
| `POST` | `/api/v2/starter/directions/{id}:select` | Select one direction and ensure three projects |
| `POST` | `/api/v2/starter/sprints/{id}:review` | Close the experiment after a real publication |

## Failure Boundaries

- A non-ready assessment cannot generate directions.
- Updating an assessment is blocked after a sprint starts.
- A foreign assessment, direction, sprint, or project is indistinguishable
  from a missing resource.
- Partial project creation can be retried; deterministic idempotency keys fill
  only missing projects.
- Deleting one project does not silently delete the sprint or its other
  projects. Sprint progress is derived from remaining owned projects.
- AI/model unavailability never blocks assessment, direction selection, or
  entry into the existing manual content workflow.

## Release Evidence

T049 can close only when tests prove:

1. readiness and privacy exclusion;
2. no more than three grounded candidates and no prohibited claims;
3. selection replay returns exactly the same three projects;
4. each project exposes the existing `confirm_intent` NextBestAction;
5. at least one published project enables a bounded starter review;
6. the frontend can resume assessment, direction selection, sprint progress,
   and open a generated project without exposing internal workflow terms.
