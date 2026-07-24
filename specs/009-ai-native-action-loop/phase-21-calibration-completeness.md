# Phase 21: Calibration Completeness

**Date**: 2026-07-23

**Status**: Complete

## Acceptance Matrix

| Task | Acceptance condition | Executable evidence |
|---|---|---|
| T034 | Calibration entities include typed `BenchmarkSample` contracts and migration-managed persistence. | Migration 033 replay/schema tests; request-model validation; HTTP lifecycle test. |
| T036 | Locked hypothesis fields cannot change; post-lock context is append-only and never enters the frozen blind-review snapshot. | SQLite immutable-field trigger; amendment service/API idempotency and owner-isolation tests. |
| T039 | Every review persists one eligibility reason; insufficient, contaminated, revoked-evidence and legacy reviews cannot create future learning. | Blind-review reason tests; Observation eligibility guard; CreatorRule source revalidation; post-review evidence-revocation test. |
| T042 | Only explicitly included samples enter relative comparison; excluded and unknown metrics never become zero or predictions. | Included/excluded benchmark comparison test; unknown-metric contract validation; prediction-key absence assertion. |

## Delivered Contract

- `publish_hypothesis_amendments` records clarification, correction, context or
  evidence updates without changing a locked hypothesis.
- `benchmark_samples` and append-only inclusion events preserve source,
  quality, metric snapshots, unknown values and explicit exclusion reasons.
- `BlindReview` stores `eligibility_reason_code` and only the IDs of benchmark
  samples that were included at comparison time.
- Relative calibration reports only below, within or above the observed sample
  range. It does not calculate traffic, virality, conversion or follower
  predictions.
- Revoking evidence invalidates both future reviews and already-persisted clean
  reviews that depend on the affected immutable content version.
- Rule proposal and confirmation re-check that every source observation still
  belongs to an eligible review.

## Boundaries

- No new calibration subsystem, model provider or dependency was added.
- Amendments do not rewrite historical hypotheses, content versions, reviews
  or AI traces.
- Benchmark samples do not activate rules directly; confirmed observations
  remain the only rule evidence path.
- Account export/deletion includes all Phase 21 owner-scoped records.

## Validation

- Focused Phase 21 and migration/API regression: `39 passed` before final
  additions; all added focused checks subsequently passed.
- Final backend CI-equivalent gate: `803 passed`, `1 deselected`, `86.95%`
  coverage.
- `git diff --check`: passed.

## Ponytail Review

The implementation reuses `PublishHypothesis -> BlindReview -> Observation ->
CreatorRule`. The only new service owns the one genuinely missing entity,
`BenchmarkSample`; no prediction engine, repository abstraction or parallel
learning pipeline was introduced.
