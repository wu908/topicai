# TopicAI Content Creation

TopicAI helps a creator turn an intended audience impact into a content,
publication, and learning loop while preserving the creator's facts and
decisions.

## Language

**Content Project**:
The complete preparation, single publication, and review loop for one piece of
content. Draft versions belong to the same project; later publications on the
same theme are separate projects connected as a series.
_Avoid_: Topic collection, multi-publication campaign

**Project State Event**:
An immutable audit fact that a Content Project moved between canonical states;
the project's current state remains authoritative and is not rebuilt from events.
_Avoid_: Event-sourced project, current project state

**Content Opportunity**:
An explainable, user-decidable candidate derived before a Content Project. It
becomes a project only after the user accepts its direction and provisional
Primary Content Intent.
_Avoid_: Empty project, automatically generated topic

**Creator Anchor**:
A user-confirmed experience, knowledge area, viewpoint, ongoing process, or
genuine question that gives a Content Opportunity creator-specific substance.
_Avoid_: Generic AI premise, trend alone

**Historical Content Evidence**:
A source-bound record of the creator's earlier published content that may support profile attributes and future opportunities but is not itself a Content Project or proof of effectiveness.
_Avoid_: Imported project, validated insight, performance proof

**Creator Profile**:
A user-correctable set of creator direction, audience, content pillars, expression preferences, and constraints whose attributes retain their evidence and confirmation state.
_Avoid_: Fixed niche, AI-assigned identity, creator score

**External Context**:
Source-bound outside information that may add timeliness, audience language,
or background to a Creator Anchor but cannot replace it.
_Avoid_: Creator evidence, standalone opportunity

**Reviewed Content Loop**:
A published Content Project with an observed or explicitly unavailable result,
a user-confirmed Intent Outcome, and a decided next action. An unknown outcome
still closes the loop and does not imply success.
_Avoid_: Effective content, successful post, publication count

**Publishing Commitment**:
The creator's chosen sustainable weekly publication target, between one and
four publications in the first release.
_Avoid_: Platform-mandated posting frequency

**Publishing Consistency**:
The rolling comparison of actual publications with the creator's Publishing
Commitment, independent of content performance and without resetting after a
missed week.
_Avoid_: Viral performance, streak

**Follower Growth Learning**:
The evidence-backed practice of comparing follower-related observations and
deciding what to test next without predicting, guaranteeing, or causally
attributing follower growth.
_Avoid_: Guaranteed growth, follower prediction

**Creator Series**:
A user-confirmed relationship among published Content Projects that share an
ongoing audience promise and continuation, while each project retains its own
intent, format, Publish Judgment, and review lens.
_Avoid_: Same-template collection, multi-publication Content Project

**Content Intent**:
The kind of impact a creator wants one piece of content to have: solve a
problem, share an experience or viewpoint, or record a process and change.
_Avoid_: Content template, post type

**Solve Intent**:
A Content Intent whose main audience change is gaining a method, answer, or
understanding that can be tried or applied.
_Avoid_: Any educational-looking format

**Share Intent**:
A Content Intent whose main audience change is understanding an experience or
viewpoint and reaching resonance, discussion, or a new perspective within the
current publication.
_Avoid_: Any first-person story

**Record Intent**:
A Content Intent whose main audience change comes from following an unfolding
process, change, or result for which continuation is part of the experience.
_Avoid_: Any chronological narrative

**Audience Change**:
The intended difference for an audience after encountering the content, which
may concern understanding, emotion, perspective, action, or continued interest.
It is required for publish-oriented content and need not solve a problem.
_Avoid_: Guaranteed outcome, creator-only purpose

**Audience Context**:
The audience's relevant situation, prior understanding, and reason to care
about a publication. Demographic attributes belong only when they materially
change the content.
_Avoid_: Invented persona, mandatory demographic profile

**Primary Content Intent**:
The single Content Intent that governs one publication's preparation and main
review lens.
_Avoid_: Multiple equal intents

**Working Intent Confirmation**:
The user's permission for AI to continue preparing content under the current
Primary Content Intent. It remains correctable until Intent Lock.
_Avoid_: Intent Lock, automatic AI intent change

**Secondary Effect**:
A plausible additional audience effect that does not control the workflow or
independently create long-term learning.
_Avoid_: Secondary content intent

**Intent Lock**:
The point at which a Content Intent and Publish Judgment become the immutable
historical basis for one publication. Before this point the intent may be
corrected; afterward a correction is appended rather than overwriting it.
_Avoid_: Intent confirmation at project creation, editable published intent

**Publication Intent**:
The Content Intent preserved at Intent Lock as the record of how a creator
understood the content before publication.
_Avoid_: Current classification

**Retrospective Intent Classification**:
A user-confirmed, post-publication interpretation used to scope future
comparison and learning without changing the Publication Intent.
_Avoid_: Rewritten publication intent, unconfirmed AI reclassification

**Unclassified Historical Content**:
Imported or legacy content whose Publication Intent was not locked at the time
of publication. AI may propose a Retrospective Intent Classification, but it
remains outside intent-specific learning until the user confirms it.
_Avoid_: Default solve intent, confirmed historical judgment

**Reconstructed Historical Loop**:
Historical content for which publication, intent classification, observable
result, observation-window quality, Intent Outcome, and next decision have
been explicitly reconstructed and confirmed. It does not count as prior
acceptance of an AI capability.
_Avoid_: Imported post count, assumed completed loop

**Publish Judgment**:
A creator's pre-publication judgment about the intended audience change,
expected response, supporting basis, and uncertainty, expressed according to
the Content Intent. A problem and answer belong only to a solve intent.
_Avoid_: Universal problem-answer hypothesis

**Complete Publish Judgment**:
A Publish Judgment whose shared audience, response, basis, uncertainty, and
Observation Window are confirmed together with the facts required by its
Primary Content Intent.
_Avoid_: Generic form completion, publish-ready copy

**Platform Metric**:
A raw value reported by the publishing platform, such as views, saves,
comments, or follows. It does not establish audience change or causality.
_Avoid_: Success result

**Observation Window**:
The elapsed time after publication selected before publication for the main
review. Relative comparisons require matching windows or an explicit allowed
tolerance.
_Avoid_: Unqualified snapshot date, universal best review time

**Comparable Sample**:
A user-included historical publication from the same creator account,
platform, Primary Content Intent, content format, metric definition, and
Observation Window, with traceable source data.
_Avoid_: Any prior post, AI-selected benchmark

**Observed Range**:
The minimum-to-maximum values from at least three Comparable Samples, shown
with its sample count as a descriptive reference rather than a prediction.
_Avoid_: Expected performance, calibrated forecast

**Audience Response Signal**:
An observed behavior or feedback item relevant to a Publish Judgment that may
support interpretation but cannot prove causality by itself.
_Avoid_: Proof of impact

**Primary Response**:
The single Audience Response Signal selected before publication as the main
observation target for an Intent Outcome.
_Avoid_: A checklist of equally important metrics

**Supporting Response**:
One of at most two additional Audience Response Signals that may add context
but cannot replace the Primary Response.
_Avoid_: Alternative primary response

**Audience Response Evidence**:
A source-bound qualitative audience response captured with its observation
form, time, privacy boundary, and permitted use. It records what was observed,
not why the result occurred.
_Avoid_: Audience insight, causal explanation

**Evidence Use Scope**:
The user-authorized boundary within which Evidence may be used. Audience
Response Evidence is project-scoped by default and requires explicit approval
for cross-project reuse.
_Avoid_: Implied reuse from visibility, AI-selected reuse scope

**Creator Fact**:
A user-confirmed statement about the creator's own experience, action, process,
or feeling, expressed as personal experience rather than universal truth.
_Avoid_: Independently verified fact, AI-authored experience

**Creator Viewpoint**:
A user-confirmed position attributed to the creator that does not require
external proof and must not be presented as a universal fact.
_Avoid_: External fact, AI-assigned opinion

**External Fact**:
A claim about people, platforms, research, news, or the outside world that
requires a traceable source.
_Avoid_: Unsourced AI knowledge, creator memory treated as authority

**AI Inference**:
An AI-proposed interpretation that remains a candidate until the user confirms
the relevant personal claim or supplies an appropriate external source.
_Avoid_: Fact, confirmed insight

**Evidence Gap**:
A fact or viewpoint required by a Content Intent that is missing, unconfirmed,
revoked, or outside its permitted use scope.
_Avoid_: Permission to invent, generic uncertainty

**Key Evidence Question**:
The single highest-value question selected to resolve one current Evidence Gap,
with its purpose and intended use made visible to the user.
_Avoid_: Mandatory interview questionnaire, generic prompt

**Evidence-Bounded Candidate**:
Candidate content that uses confirmed Evidence, marks Evidence Gaps explicitly,
and may add structure or non-factual expression without inventing claims.
_Avoid_: Publish-ready draft with hidden assumptions

**Validated Insight**:
A user-confirmed learning supported by repeated Reviewed Content Loops rather
than a single publication.
_Avoid_: One-post lesson, AI inference

**Expression Preference**:
A user-confirmed pattern derived from creator-selected content that may shape
candidate wording without adding facts, changing intent, or implying growth
effectiveness.
_Avoid_: Voice clone, Creator Rule, inferred authorship

**Intent Outcome**:
A user-confirmed assessment that a Publication Intent has supporting evidence,
contradicting evidence, or remains unknown when compared with its locked
Publish Judgment.
_Avoid_: Universal success score, automatic success or failure

**Review Follow-up**:
The single primary action selected after an Intent Outcome: continue, stop or
adjust, run a bounded experiment, collect more evidence, or repeat observation.
The action must match the available evidence.
_Avoid_: Mandatory continue-stop-experiment trio

**Content Experiment**:
A user-confirmed test that pre-registers one primary change, one Primary
Response, an Observation Window, a baseline or repetition plan, and known
confounders. One publication provides directional evidence, not causality.
_Avoid_: Any changed post, causal proof

**Content Attempt**:
A publication that tries a direction without a sufficient baseline or
repetition plan and therefore cannot produce an experiment conclusion.
_Avoid_: Content Experiment

**Creator Rule**:
A user-approved, scoped decision aid derived from repeated Reviewed Content
Loops. It may influence future action ranking but does not claim causality or
override current evidence and user-controlled decisions.
_Avoid_: Automatic instruction, growth law

**Action Policy**:
The deterministic boundary that decides which actions are allowed, blocked, or
require user confirmation in the current state.
_Avoid_: Content judgment, AI substitute

**AI Orchestrator**:
The context-aware planner that selects and prepares the most valuable allowed
action using current evidence, intent, and applicable Creator Rules.
_Avoid_: Unrestricted workflow authority, chat assistant

**Next Best Action**:
The one primary action prepared for the user by the AI Orchestrator within the
Action Policy, with its reason, evidence, unknowns, and fallback.
_Avoid_: Tool menu, mandatory automatic action

**Action Deferral**:
A decision that an otherwise appropriate Next Best Action should return after
a chosen time because the user is not ready to do it now.
_Avoid_: Action rejection

**Action Rejection**:
A decision that a Next Best Action is inappropriate in its current form or
context and must not be repeated unchanged in the same state.
_Avoid_: Temporary delay, confirmed long-term preference

**Manual Completion**:
The user's completion of the same intended state change without AI execution.
It advances the Content Project while preserving the manual path in history.
_Avoid_: Action rejection, fallback failure

**Capability Trust**:
The user's permission for one specific AI capability to prepare reversible
work automatically after at least three accepted results of that capability
and no unresolved correction. It never authorizes protected decisions.
_Avoid_: Global AI trust score, implicit consent
