-- 002_user_feedback.sql (Spec-007 T011)
-- Persisted feedback events feeding the personalization loop (US3, FR-005).
-- Mirrors the FeedbackRecord Pydantic model in backend/app/models/feedback.py.
-- Idempotent: safe to re-run; the runner records the version in schema_migrations.

CREATE TABLE IF NOT EXISTS user_feedback (
    id              CHAR(36) PRIMARY KEY,
    user_id         CHAR(36) NOT NULL,
    source_type     TEXT     NOT NULL,
    source_id       CHAR(36) NOT NULL,
    feedback_type   TEXT     NOT NULL,
    feedback_value  TEXT,
    reason          TEXT,
    created_at      TEXT     NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Rolling 30-day window for adjust_weights + GET /api/v1/feedback/history.
CREATE INDEX IF NOT EXISTS idx_user_feedback_user_id_created_at
    ON user_feedback (user_id, created_at DESC);

-- Back-ref from a source row (topic / title / idea / viral / etc.) to its feedback.
CREATE INDEX IF NOT EXISTS idx_user_feedback_source
    ON user_feedback (source_type, source_id);
