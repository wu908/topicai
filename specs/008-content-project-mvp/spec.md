# Feature Specification: TopicAI Content Project MVP

**Feature Branch**: `008-content-project-mvp`

**Created**: 2026-07-17

**Status**: Implemented; v2-only cleanup in release validation

**Input**: Rebuild the existing TopicAI product for Xiaohongshu knowledge and experience graphic creators. Reuse proven infrastructure, replace isolated AI tools with a unified content-project lifecycle, support a lightweight starter path and a complete growth-creator path, and validate locally before user research.

**Product sources**: `../../../01-product-definition.md`, `../../../02-information-architecture.md`, `../../../03-content-project-data-model.md`, `../../../04-page-prd-and-acceptance.md`, `../../../05-product-iteration-and-refactoring.md`, `../../../06-hotspot-data-source-research.md`.

## User Scenarios & Testing

### User Story 1 - Resume the next meaningful content task (Priority: P1)

As a signed-in creator, I can open Today and immediately continue the highest-priority unfinished task for my weekly publishing goal without reconstructing context across separate tools.

**Why this priority**: Stable publishing depends on reducing the distance between opening the product and taking the next action. This story proves the product is a workflow rather than a collection of AI utilities.

**Independent Test**: Create a user with one unfinished project, open Today, follow the primary task, leave mid-edit, return, and confirm the same project and unsaved recovery state are available.

**Acceptance Scenarios**:

1. **Given** a user has a weekly goal and an unfinished project, **When** Today loads, **Then** the page shows the weekly progress, one primary next task, and the project context needed to continue.
2. **Given** a user leaves a project after making recoverable local changes, **When** the user returns, **Then** the product offers to restore the latest recoverable draft without overwriting the last saved version.
3. **Given** the user has no project, **When** Today loads, **Then** the primary action leads to creating a project from an opportunity or a blank brief rather than displaying a generic dashboard.

---

### User Story 2 - Complete a content project from opportunity to publication (Priority: P1)

As a growth creator, I can turn a relevant opportunity into a brief, supply real experience and evidence through an interview, create and revise a graphic note, run a pre-publish check, export it, and record publication within one project.

**Why this priority**: This is the core value loop and the minimum product slice that can be tested with real creators.

**Independent Test**: Starting with a saved opportunity, complete every project state through Published and verify that titles, body, cover plan, source materials, checks, versions, and publish record remain attached to the same project.

**Acceptance Scenarios**:

1. **Given** an adopted opportunity, **When** the user creates a project, **Then** the project enters `准备中` once and retains the opportunity evidence and rationale.
2. **Given** the brief lacks personal experience, cases, or evidence, **When** the user requests a draft, **Then** the product asks targeted interview questions before offering a full draft.
3. **Given** the user accepts or rejects an AI suggestion, **When** the decision is applied, **Then** a new version and decision record are created without overwriting confirmed content.
4. **Given** a project has a selected publish version, **When** the user confirms publication, **Then** the version is locked, a publish record is created idempotently, and the project enters `已发布`.

---

### User Story 3 - Start from a vague idea and run a three-post experiment (Priority: P1)

As a person who wants to create on Xiaohongshu but has not started, I can inventory my real experiences, interests, skills, constraints, and willingness to act, choose a testable direction, and receive a 14-day three-post experiment that uses the same content-project workflow as growth creators.

**Why this priority**: The starter segment is a selected MVP audience, but it must remain a bounded experiment rather than a promise to discover a permanent or profitable niche.

**Independent Test**: Complete the starter assessment with a vague idea, choose one of at most three direction candidates, create three linked experiment projects, record at least one publication, and complete the starter review.

**Acceptance Scenarios**:

1. **Given** a starter has no clear niche, **When** the assessment is completed, **Then** the product returns at most three testable directions grounded in the user's supplied assets and constraints.
2. **Given** the user does not commit time or publication intent, **When** the assessment is submitted, **Then** the product does not start the accelerator and instead preserves the assessment for later continuation.
3. **Given** the user selects a direction, **When** the starter sprint begins, **Then** three experiment projects are created or proposed with explicit audiences, learning goals, and low production cost.
4. **Given** the sprint ends, **When** the user completes the review, **Then** the product reports observed evidence and next experiments without claiming a permanent niche, guaranteed growth, or monetization.

---

### User Story 4 - Build a correctable creator profile from real history (Priority: P1)

As a creator with at least ten historical notes, I can import note records, review the system's profile inferences, correct or remove them, and confirm a profile used by later opportunities and writing assistance.

**Why this priority**: Recommendations are only trustworthy when grounded in the creator's actual content and explicitly confirmed strategy.

**Independent Test**: Import ten notes by supported MVP methods, observe partial failures, edit inferred audience and content pillars, confirm the profile, and verify rejected inferences are not used later.

**Acceptance Scenarios**:

1. **Given** an import contains valid and invalid records, **When** the import finishes, **Then** valid records are retained, failures are itemized, and retrying does not duplicate successful records.
2. **Given** the system proposes profile attributes, **When** the user edits, rejects, or confirms them, **Then** each attribute records its evidence and confirmation state.
3. **Given** there is insufficient history, **When** the profile is generated, **Then** uncertain attributes are labeled as provisional and the user can continue with manual input.

---

### User Story 5 - Choose explainable opportunities without fake precision (Priority: P2)

As a creator, I can review content opportunities derived from my history, audience questions, materials, series, and evergreen needs, and understand why each opportunity fits before adopting, saving, or rejecting it.

**Why this priority**: Opportunity quality drives the loop, but it must not depend on uncalibrated virality scores or simulated real-time trends.

**Independent Test**: Generate opportunities from seeded history and materials, inspect evidence and dimensions, reject one with a reason, adopt another, and verify the decision is retained.

**Acceptance Scenarios**:

1. **Given** creator context exists, **When** opportunities are requested, **Then** each item shows audience fit, creator fit, material readiness, growth role, series potential, timeliness, similarity risk, rationale, and traceable source references.
2. **Given** no trustworthy source supports a current trend claim, **When** opportunities are generated, **Then** no item is labeled real-time, hot, trending, or likely to go viral.
3. **Given** a user enters a keyword, source URL, or official inspiration manually, **When** analysis succeeds, **Then** the result is treated as an optional hotspot opportunity with freshness and verification state; the language model is never the factual source.
4. **Given** an external link cannot be verified, **When** analysis finishes, **Then** the source is marked insufficient and the user can still save the raw input without fabricated facts.

---

### User Story 6 - Publish with transparent assistance and manual control (Priority: P2)

As a creator, I can compare content versions, choose a publish version, see risk findings with locations and reasons, export the body and images, and manually record the Xiaohongshu link and publication time.

**Why this priority**: The MVP must support real publication while avoiding unsupported automatic publishing and approval guarantees.

**Independent Test**: Select a version, run checks, resolve or acknowledge findings, copy text, export images, submit a publish record twice with the same idempotency key, and verify only one record exists.

**Acceptance Scenarios**:

1. **Given** a check finds a risk, **When** the user opens it, **Then** the product shows the matched location, reason, rule source, update time, severity, and an explicit statement that approval is not guaranteed.
2. **Given** the content changes after a check, **When** the user returns to publishing, **Then** the previous check is marked stale and a new check is required for the changed version.
3. **Given** export partially fails, **When** retry is requested, **Then** completed artifacts are not duplicated and failed artifacts can be regenerated independently.

---

### User Story 7 - Record performance and turn review into one next experiment (Priority: P2)

As a creator, I can manually enter or extract performance snapshots, compare them with my own baseline, separate facts from hypotheses, and confirm exactly one item to continue, one to stop, and one to experiment with next.

**Why this priority**: Growth comes from repeated learning, not from one-off generation or generic advice.

**Independent Test**: Add 24-hour and 72-hour snapshots, complete a review, confirm one insight, reject another, and verify only confirmed insight affects later creator context.

**Acceptance Scenarios**:

1. **Given** a published project has no metrics, **When** the review opens, **Then** the product asks for a manual entry or screenshot and does not infer performance values.
2. **Given** multiple snapshots exist, **When** the review is generated, **Then** facts, possible causes, and proposed experiments are visually and structurally distinct.
3. **Given** the user confirms the review, **When** it is saved, **Then** it contains one continue action, one stop action, and one experiment action; only user-confirmed insights enter long-term context.

---

### User Story 8 - Manage materials and settings without a separate asset system (Priority: P3)

As a creator, I can add lightweight text, link, image, and document materials from a project or the Materials list, reuse them in projects, and manage weekly goals, content strategy, account, AI configuration status, privacy, export, and deletion from My.

**Why this priority**: Materials and settings support the core loop, but the first release does not need a complex digital asset management system.

**Independent Test**: Add a material from a project, reuse it in another project, inspect usages, update weekly goal, export user data, and request account deletion.

**Acceptance Scenarios**:

1. **Given** a material is referenced by a locked publish version, **When** deletion is requested, **Then** the user sees affected projects and the locked version retains an auditable reference snapshot.
2. **Given** an AI service is not configured or unavailable, **When** the user opens My or invokes an AI task, **Then** the product shows an actionable unavailable state and preserves a manual path.

### Edge Cases

- Duplicate project creation, version locking, publish confirmation, screenshot parsing, and metric submission MUST be idempotent.
- Concurrent edits MUST produce a conflict and recoverable comparison; last-write-wins must not silently overwrite user content.
- Unsaved changes MUST trigger navigation protection and maintain a local recovery draft after refresh or temporary offline use.
- AI timeout, malformed output, missing source, missing model capability, and quota exhaustion MUST preserve user input and expose a manual continuation path.
- Partial history import and partial export MUST report per-item outcomes and allow retry without duplicating successful work.
- A project may move backward before publication with an audit event; a published project cannot become unpublished and instead creates a revision or derivative project.
- Expired hotspot inputs MUST require explicit user confirmation before project creation.
- Screenshot extraction MUST never store inferred metrics until the user reviews and confirms them.
- Account deletion MUST include project, material, source excerpt, metric screenshot, learned-insight, and AI trace data, while preserving only legally or operationally required audit records.

## Requirements

### Functional Requirements

- **FR-001**: The product MUST retain email/password registration, login, token refresh, session restoration, and user-scoped data isolation.
- **FR-002**: The product MUST support two entry modes: `starter` and `growth`, selected during onboarding and changeable without creating a second account.
- **FR-003**: Starter mode MUST capture action readiness and real content assets before proposing at most three testable directions.
- **FR-004**: Starter mode MUST create a 14-day experiment linked to shared content projects and MUST avoid permanent-niche, monetization, or guaranteed-growth claims.
- **FR-005**: Growth onboarding MUST support manual and structured history import with per-item validation, partial success, retry, and deduplication.
- **FR-006**: Profile inferences MUST expose evidence, confidence labels, limitations, and user confirmation; rejected inferences MUST not be reused.
- **FR-007**: The primary navigation MUST be `今日｜内容｜机会｜素材｜我的` and every MVP function MUST be reachable through one of these nodes or onboarding.
- **FR-008**: `ContentProject` MUST be the single lifecycle aggregate for brief, materials, versions, publish checks, publication, performance, review, and learned insights.
- **FR-009**: Project status MUST use exactly `灵感箱 → 准备中 → 创作中 → 待发布 → 已发布 → 待复盘 → 已沉淀`, with validated transitions and audit history.
- **FR-010**: Today MUST prioritize weekly publishing progress and one next task, with empty, overdue, blocked, and recovery states.
- **FR-011**: Opportunities MUST be explainable through source references and qualitative dimensions; uncalibrated virality scores, heat probabilities, CTR forecasts, and guaranteed outcomes are prohibited.
- **FR-012**: MVP opportunity sources MUST prioritize history derivatives, user questions, personal materials, series follow-ups, and evergreen needs.
- **FR-013**: Hotspot support MUST be user-triggered through a keyword, URL, or manually entered official inspiration; continuous news/hotspot aggregation is outside MVP.
- **FR-014**: A language model MUST NOT be recorded or displayed as the factual source of real-time hotspot, news, publication time, heat, or trend claims.
- **FR-015**: An adopted opportunity MUST create at most one project for a given idempotency key and MUST preserve the opportunity's evidence and user decision.
- **FR-016**: Brief creation MUST collect audience, promise, conclusion, evidence needs, structure, image plan, differentiation, and known risks.
- **FR-017**: When personal evidence is insufficient, AI assistance MUST ask interview questions before offering a complete draft.
- **FR-018**: AI modifications MUST default to local suggestions with accept/reject, reason feedback, version comparison, and non-destructive regeneration.
- **FR-019**: Every AI output MUST record task type, input entity references, evidence references, prompt-policy version, configured model identifier, generation time, confidence label, limitations, and user decision.
- **FR-020**: AI failure MUST not fabricate a substitute answer; it MUST preserve input and provide a deterministic or manual path appropriate to the task.
- **FR-021**: Content versions MUST be immutable after creation; edits and accepted AI changes MUST create child versions.
- **FR-022**: Publish checks MUST be bound to a version and show finding location, reason, severity, rule source, and rule update time.
- **FR-023**: Publish checks MUST be described as assistance only and MUST NOT promise platform approval.
- **FR-024**: MVP publishing MUST support copying body text, exporting images, entering a note link, and recording publication manually; automatic publishing is outside MVP.
- **FR-025**: The selected publish version MUST be locked and remain auditable after publication.
- **FR-026**: Performance data MUST support manual entry and user-confirmed screenshot extraction; automatic Xiaohongshu synchronization is outside MVP.
- **FR-027**: Performance snapshots MUST be append-only; corrections create a new snapshot linked to the superseded snapshot.
- **FR-028**: Reviews MUST distinguish observed facts, possible causes, and next experiments and MUST produce exactly one continue, one stop, and one experiment action.
- **FR-029**: Only user-confirmed learned insights MAY influence long-term creator context or later recommendations.
- **FR-030**: Materials MUST support lightweight list, project drawer, usage references, privacy level, and safe deletion behavior.
- **FR-031**: The product MUST preserve feedback on AI suggestions, opportunities, reviews, and risk findings as immutable user decision events.
- **FR-032**: Pages MUST provide loading, empty, partial failure, timeout, stale source, duplicate submission, unsaved change, offline recovery, and insufficient-data states where applicable.
- **FR-033**: The product MUST provide data export and account deletion covering user-generated content, derived profile data, source excerpts, metrics, feedback, and AI traces.
- **FR-034**: The MVP MUST remain limited to one user workspace, one primary Xiaohongshu account, and graphic knowledge/experience notes; team, MCN, matrix accounts, live commerce, video editing, and multi-platform publishing are excluded.
- **FR-035**: Legacy isolated tools, frontend routes, and `/api/v1` endpoints MUST be absent. Requests to removed paths use the standard not-found response and MUST NOT redirect into v2 or create legacy records.
- **FR-036**: Existing databases MUST upgrade through migration 045 without losing `users`, `creator_profiles`, `schema_migrations`, or v2 aggregate data; audited-empty v1 business tables MUST be removed.

### Key Entities

- **User**: Identity, mode, timezone, consent, weekly goal, and lifecycle status.
- **CreatorProfile**: User-correctable niche, audience, growth goal, content pillars, voice, constraints, evidence, and confirmation state.
- **StarterAssessment / DirectionCandidate / StarterSprint**: Readiness, content assets, bounded direction options, and the 14-day experiment.
- **PlatformAccount**: The user's primary Xiaohongshu account reference and future synchronization extension point.
- **Opportunity**: Evidence-backed candidate content idea with source, fit, readiness, growth role, risk, expiry, and user decision.
- **ContentProject**: The single aggregate owning lifecycle status and all downstream work.
- **ContentBrief**: The audience promise, conclusion, evidence, structure, image plan, differentiation, and risks for a project.
- **Material**: User fact, case, quote, link, image, or document and its usage references.
- **ContentVersion**: Immutable title, body, cover plan, image plan, ancestry, author origin, and evidence snapshot.
- **PublishCheck / PublishRecord**: Version-bound risk assistance and immutable publication fact.
- **PerformanceSnapshot**: Append-only metrics collected manually, by confirmed screenshot extraction, or future API synchronization.
- **Review / LearnedInsight**: Fact-hypothesis-experiment review and user-confirmed reusable learning.
- **UserFeedback**: Immutable user decision about an AI or product output.
- **AITrace**: Provenance and user-control record for each AI task.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A test user can register, complete either onboarding path, and reach the first actionable task without encountering an orphan page or dead end.
- **SC-002**: A growth user can complete one project from creation to published record in no more than 12 primary user decisions, excluding writing and optional edits.
- **SC-003**: A returning user with an unfinished project can reach the correct next task from Today in no more than two interactions.
- **SC-004**: 100% of AI-created or AI-modified records expose provenance, limitations, and an accept/reject or confirm path.
- **SC-005**: 100% of hotspot opportunities include a non-LLM source reference, freshness or verification state, and no simulated real-time claim.
- **SC-006**: Duplicate submissions for project creation, version lock, publication, and performance snapshot produce one logical result in automated acceptance tests.
- **SC-007**: All seven project-state transitions, allowed reversals, blocked transitions, and recovery paths are covered by automated state tests.
- **SC-008**: The five primary navigation nodes and both onboarding paths pass desktop and mobile end-to-end smoke tests with no inaccessible MVP page.
- **SC-009**: A complete local deployment can start from documented configuration, create a fresh database through migrations, and finish the core publish-review loop without copying any source-project runtime data or secrets.
- **SC-010**: Backend and frontend automated test coverage remain at or above the governed 80% floor, and the number of passing tests does not decrease from the recorded clean-copy baseline after environment-related failures are resolved.

## Assumptions

- The first runnable release is for local Docker validation, not public production deployment.
- The copied project starts with a fresh database, empty uploads, and no copied `.env`, API keys, tokens, Chroma data, or user content.
- Email/password authentication and single-user ownership rules are reused.
- AI access is configured through an OpenAI-compatible endpoint; provider and model names are deployment configuration, not product constants.
- A configured model may lack image capability; screenshot flows must always retain a manual-entry fallback.
- Newcomer success is evaluated by real publishing and learning, while growth-user success is evaluated by completed content loops and stable updating; neither path promises follower growth.
- The existing product documents in the parent directory are the product authority for this feature; the SpecKit artifacts translate them into an implementation-ready scope.
- Automatic publishing, official Xiaohongshu data synchronization, continuous hotspot/news feeds, billing, teams, and public-cloud operations are deferred.
