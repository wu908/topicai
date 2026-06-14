-- 003_effect_reviews.sql (Spec-007 T012)
-- Three-phase lifecycle (predict -> attribute -> derive_learnings)
-- backed by EffectReviewService (US4, FR-007).
-- Idempotent: safe to re-run; the runner records the version in schema_migrations.

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
CREATE INDEX IF NOT EXISTS idx_effect_reviews_user_id_created_at
    ON effect_reviews (user_id, created_at DESC);

-- GET /api/v1/reviews/list?status=awaiting_actuals filter.
CREATE INDEX IF NOT EXISTS idx_effect_reviews_status
    ON effect_reviews (status);
