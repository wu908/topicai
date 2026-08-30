-- 003_effect_reviews.sql (Spec-007 T012)
-- Three-phase lifecycle (predict -> attribute -> derive_learnings)
-- backed by EffectReviewService (US4, FR-007).
-- Idempotent: safe to re-run; the runner records the version in schema_migrations.
--
-- The two CREATE INDEX statements that reference the additive ``status``
-- column live in the runner's post-step (``_post_step_003_effect_reviews``),
-- NOT here. On a database that predates the column addition,
-- ``CREATE TABLE IF NOT EXISTS`` is a no-op and the column would be
-- missing, so an index on ``status`` would raise "no such column" (Bug 3).
-- The post-step back-fills the columns first, then creates the indexes.
-- On a fresh DB this .sql builds the full table; the post-step is a no-op
-- for columns and just adds the indexes.

CREATE TABLE IF NOT EXISTS effect_reviews (
    id                CHAR(36) PRIMARY KEY,
    user_id           CHAR(36) NOT NULL,
    topic_title       TEXT     NOT NULL,
    content_outline   TEXT     NOT NULL,
    prediction        TEXT     NOT NULL,  -- JSON: PredictionPayload
    actual_result     TEXT,               -- JSON: ActualResultPayload
    attribution       TEXT,               -- JSON: list[DimensionalConclusion]
    learnings         TEXT,               -- JSON: LearningsPayload (cached)
    status            TEXT     NOT NULL DEFAULT 'awaiting_actuals',
    created_at        TEXT     NOT NULL,
    updated_at        TEXT     NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Learning aggregation: derive_learnings scans the last 30 days for a user.
-- Index idx_effect_reviews_user_id_created_at and idx_effect_reviews_status
-- are created by the runner post-step (see runner._post_step_003_effect_reviews).
