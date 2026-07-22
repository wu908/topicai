# Phase 11 MVP Experiment Metrics Contract

**Date**: 2026-07-22

**Scope**: Internal validation infrastructure for E1-E4

**Status**: Implemented contract; no real-user result claim

## Assignment Rules

- Supported experiments are exactly E1, E2, E3, and E4.
- Cohorts are `control`, `variant`, `observational`, and `excluded`.
- User segments are `starter`, `growth`, and `unknown`; reports must not combine starter and growth users without also showing the segmented result.
- An owner can have only one active experiment. Activating another experiment completes the previous active assignment and emits an immutable transition event.
- Assignment source is explicit: `manual_internal`, `deterministic`, or `imported`. The system does not describe a manual assignment as randomization.

## Action Funnel

All metrics use the selected half-open UTC window `[start_at, end_at)` with a maximum duration of 90 days.

| Metric | Numerator | Denominator |
|---|---|---|
| Offered | Distinct actions with an in-window `proposed` event | Same count; this is the cohort base |
| Accepted rate | Offered actions with `accepted` or `gate_confirmed` | Offered actions |
| Rejected rate | Offered actions with `deferred`, `manual_selected`, or `gate_rejected` | Offered actions |
| Completed rate | Offered actions that reach `to_status=completed` | Offered actions |
| Failed rate | Offered actions with at least one `success=false` event | Offered actions |

An action without an in-window offer is excluded from every funnel numerator, even if it has an accepted or completed event in the window. A zero denominator returns `null`, not zero. Missing latency is counted separately and is never imputed.

## Calibration Quality

- Valid-clean rate: reviews with `calibration_state=valid` and `contamination_status=clean` divided by all in-window reviews in scope.
- Contamination rate: reviews marked `suspected` or `contaminated` divided by all in-window reviews in scope.
- Rule-upgrade eligibility rate: explicitly eligible reviews divided by valid-clean reviews.
- Observation and rule-version status values are exported as counts, without statement text, scope JSON, evidence text, or review comparison payloads.

When experiment/cohort filters are present, calibration rows are limited to projects represented by offered actions in that filtered cohort. If no such projects exist, calibration denominators are zero and rates are `null`.

Without experiment or cohort filters, calibration quality is owner-wide for the selected window. Reviews, observations, and rule versions always use the same scope; filtered rule versions must trace through their source observations to an in-scope project.

## Privacy Boundary

The internal export includes only identifiers, enums, timestamps, state transitions, technical outcome fields, and aggregate counts. It never selects:

- `payload_json`;
- title or body text;
- material or evidence statements;
- email or account handles;
- credentials, API keys, or platform tokens.

`user_id_hash` is a domain-separated SHA-256 pseudonym. It is pseudonymization, not anonymization: the endpoint remains authenticated and owner-scoped, and exported files must still be handled as internal research data.

## Interpretation Boundary

This contract makes future evidence comparable. It does not prove that AI-native actions, interview-first drafting, personal context, or hotspot opportunities improve user outcomes. Causal language requires an explicit comparison design, eligible samples, guardrail review, and the real-user validation work still open in T049-T050.
