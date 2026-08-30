-- Spec-012: Per-capability auto-prepare trust (ADR 0002).
-- Automatic preparation is authorised per capability after three accepted
-- results, never by a global trust score.  This column stores a JSON object
-- keyed by action_type with the count of gate_confirmed events for each
-- auto-prepare capability (review_candidate, confirm_learning).
-- No post-step required: ADD COLUMN + DEFAULT is natively supported by SQLite.

ALTER TABLE creator_states
    ADD COLUMN capability_trust_json TEXT NOT NULL DEFAULT '{}';
