-- Spec-010: Intent model migration.
--
-- Goals:
--   1. Expand content_projects.intent_status CHECK constraint to include
--      working_confirmed, locked, legacy_unclassified, retrospective.
--      Add intent_locked_at and retrospective_intent columns.
--      (Done in the post-step: SQLite forbids ALTER CONSTRAINT, so the table
--      is rebuilt with foreign_keys=OFF to avoid cascading child deletes.)
--   2. Add intent-model columns to publish_hypotheses (audience_change,
--      primary_response, supporting_responses_json, observation_window_days,
--      viewpoint_anchor, continuation_promise, content_intent snapshot).
--
-- Backward-compatible invariants:
--   * Existing rows are copied verbatim — no status value is rewritten.
--   * Old values 'confirmed' and 'legacy_missing' remain valid in the CHECK
--     so the service layer can do a read-time mapping without a data migration.
--   * audience_problem / reader_promise columns are preserved (not dropped).
--   * All new columns are nullable to avoid breaking existing rows.
--
-- NOTE: The content_projects rebuild is intentionally NOT in this .sql file.
-- Rebuilding a parent table via executescript() would run with
-- foreign_keys=ON and cascade-delete child rows (human_gates, actions, etc.)
-- when the old table is dropped. The rebuild lives in the Python post-step
-- (_post_step_034_intent_model) which toggles foreign_keys=OFF safely, the
-- same pattern as _post_step_030_action_lifecycle.

-- ============================================================
-- publish_hypotheses: add intent-model columns (additive, safe)
-- ============================================================

-- All new columns are nullable for backward compatibility with existing rows.
-- audience_problem / reader_promise (legacy columns) are preserved unchanged.

ALTER TABLE publish_hypotheses ADD COLUMN content_intent TEXT
    CHECK (content_intent IN ('solve','share','record') OR content_intent IS NULL);

ALTER TABLE publish_hypotheses ADD COLUMN audience_change TEXT;

ALTER TABLE publish_hypotheses ADD COLUMN primary_response TEXT
    CHECK (primary_response IN ('save','comment','profile_visit','follow','other')
           OR primary_response IS NULL);

-- JSON array of ExpectedBehavior values, max 2 items enforced at service layer.
ALTER TABLE publish_hypotheses ADD COLUMN supporting_responses_json TEXT NOT NULL DEFAULT '[]';

ALTER TABLE publish_hypotheses ADD COLUMN observation_window_days INTEGER
    CHECK ((observation_window_days >= 1 AND observation_window_days <= 365)
           OR observation_window_days IS NULL);

-- share-specific
ALTER TABLE publish_hypotheses ADD COLUMN viewpoint_anchor TEXT;

-- record-specific
ALTER TABLE publish_hypotheses ADD COLUMN continuation_promise TEXT;
