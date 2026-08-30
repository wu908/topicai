-- 004_risk_keywords.sql (Spec-007 T013)
-- User-extensible keyword library (US5, FR-008). Global rows have
-- user_id = NULL; per-user overrides are keyed by user_id and
-- supersede the global entry of the same keyword for that user.
-- The 100-entry seed from backend/app/data/seed/risk_keywords.json
-- is loaded by ContentRiskService at runtime (US5, T075), not here,
-- to keep this migration pure DDL and idempotent.
-- Idempotent: safe to re-run; the runner records the version in schema_migrations.

CREATE TABLE IF NOT EXISTS risk_keywords (
    id          CHAR(36) PRIMARY KEY,
    user_id     CHAR(36),                  -- NULL = global library entry
    keyword     TEXT     NOT NULL,
    severity    TEXT     NOT NULL,         -- 'high' | 'medium' | 'low'
    category    TEXT     NOT NULL,         -- 'regulatory' | 'sensitive' | 'medical' | 'financial' | 'false_advertising'
    created_at  TEXT     NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- A user can override a global keyword's severity but not duplicate it.
CREATE UNIQUE INDEX IF NOT EXISTS idx_risk_keywords_user_keyword
    ON risk_keywords (user_id, keyword);

CREATE INDEX IF NOT EXISTS idx_risk_keywords_category
    ON risk_keywords (category);
