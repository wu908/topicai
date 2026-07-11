-- 006_platform_tokens.sql (Spec-007 T014)
-- Foundation table for the 006 roadmap's PlatformOAuthAdapter work.
-- Created in 007 (instead of 006) to avoid a future schema migration
-- disrupting the 007 release. NO endpoints/services in 007 read or
-- write this table; the columns and constraint are locked in here.
-- Idempotent: safe to re-run; the runner records the version in schema_migrations.
--
-- Renumbered from 005 -> 006 (2026-07-03) to resolve a duplicate version
-- prefix collision with 005_creator_profiles.sql (both shared NNN=005).
-- The runner keys schema_migrations by path.stem, so the two never
-- collided at runtime, but the duplicate prefix broke the monotonic NNN
-- invariant and made the status() diagnostic ambiguous.

CREATE TABLE IF NOT EXISTS platform_tokens (
    id              CHAR(36) PRIMARY KEY,
    user_id         CHAR(36) NOT NULL,
    platform        TEXT     NOT NULL,        -- 'xhs' | 'douyin' | 'bilibili' | 'weibo'
    access_token    TEXT     NOT NULL,        -- encrypted at rest (Constitution Principle XIII)
    refresh_token   TEXT,                     -- encrypted at rest
    expires_at      TEXT     NOT NULL,        -- UTC; refresh within 7 days of expiry
    last_sync_at    TEXT,                     -- last successful trigger_sync
    created_at      TEXT     NOT NULL,
    updated_at      TEXT     NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- One credential per (user, platform) pair.
CREATE UNIQUE INDEX IF NOT EXISTS idx_platform_tokens_user_platform
    ON platform_tokens (user_id, platform);
