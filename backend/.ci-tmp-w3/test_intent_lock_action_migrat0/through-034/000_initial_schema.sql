-- 000_initial_schema.sql (Spec-007 dual-schema-debt consolidation, T101)
--
-- The single frozen baseline that lets the migration runner ALONE bootstrap
-- the full application schema on a fresh DB. This retires the redundant
-- ``SQL_SCHEMA`` big-string in ``app/core/database.py`` as a schema authority
-- (T104) and removes the need for ``tests/conftest.py`` to re-apply 002/003/
-- 004 inline (T103).
--
-- Scope: 21 tables.
--   * 19 business tables historically defined only by SQL_SCHEMA (users,
--     topic_recommendations, viral_analyses, idea_boosters,
--     title_optimizations, track_diagnoses, feedback_records,
--     feedback_analyses, content_risks, publish_suggestions, user_events,
--     llm_call_logs, upgrade_signals, assets, asset_tags, asset_tag_links,
--     asset_usages, platform_accounts, team_members).
--   * 2 tables that OVERLAP with later additive migrations
--     (creator_profiles<->005, effect_reviews<->003). For these two the
--     MIGRATION-AUTHORITATIVE definition is used here (creator_profiles gets
--     the recommendation_mode CHECK that SQL_SCHEMA lacked; effect_reviews
--     gets the post-step full-column shape). On a fresh DB 000 runs first and
--     establishes the authoritative shape; 003/005 then ``CREATE TABLE IF NOT
--     EXISTS`` no-op. On an existing prod DB 000 no-ops (tables pre-exist) and
--     the additive migrations stay recorded — see the plan's checksum/drift
--     analysis.
--
-- Idempotent: every statement is ``IF NOT EXISTS``. The runner records the
-- version + checksum in schema_migrations. Future additive schema changes go
-- in ``NNN_*.sql`` migrations (007+); this baseline is frozen.
--
-- Conventions preserved from the prior SQL_SCHEMA:
--   * SQLite ``TEXT`` for all id/timestamp columns (UUID-as-text, ISO-8601).
--   * Foreign keys declared inline; the runner's connection enables
--     ``PRAGMA foreign_keys=ON`` (T102 aligns the runner's pragmas with the
--     async engine).

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    ai_calls_today INTEGER NOT NULL DEFAULT 0,
    ai_calls_reset_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_login TEXT
);

-- Creator profiles table (overlap with 005_creator_profiles.sql).
-- Authoritative = migration 005 definition: carries the recommendation_mode
-- CHECK that the legacy SQL_SCHEMA version lacked, plus updated_at DEFAULT.
CREATE TABLE IF NOT EXISTS creator_profiles (
    id                    TEXT PRIMARY KEY,
    user_id               TEXT NOT NULL UNIQUE,
    track                 TEXT NOT NULL,
    content_formats       TEXT NOT NULL,
    production_complexity TEXT NOT NULL,
    content_depth         TEXT NOT NULL,
    hotspot_preference    TEXT NOT NULL,
    recommendation_mode   TEXT NOT NULL CHECK (recommendation_mode IN ('hotspot_fusion','evergreen_deep')),
    rubric_weights        TEXT NOT NULL DEFAULT '{}',
    created_at            TEXT NOT NULL,
    updated_at            TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_creator_profiles_user_id ON creator_profiles(user_id);

-- Topic recommendations table
CREATE TABLE IF NOT EXISTS topic_recommendations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    topics TEXT NOT NULL,
    recommendation_mode TEXT NOT NULL,
    data_source_used TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Viral analyses table
CREATE TABLE IF NOT EXISTS viral_analyses (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    input_type TEXT NOT NULL DEFAULT 'text',
    input_text TEXT NOT NULL,
    input_text_expires_at TEXT,
    viral_score REAL NOT NULL,
    structural_analysis TEXT NOT NULL,
    attributions TEXT NOT NULL,
    transferable_template TEXT NOT NULL,
    rewrite_suggestions TEXT NOT NULL,
    risk_warnings TEXT NOT NULL,
    confidence REAL NOT NULL,
    data_source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Idea boosters table
CREATE TABLE IF NOT EXISTS idea_boosters (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    input_idea TEXT NOT NULL,
    input_idea_expires_at TEXT,
    key_assumptions TEXT NOT NULL,
    feasibility_assessment TEXT NOT NULL,
    title_candidates TEXT NOT NULL,
    content_outline TEXT NOT NULL,
    publish_schedule TEXT NOT NULL,
    confidence REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Title optimizations table
CREATE TABLE IF NOT EXISTS title_optimizations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    original_title TEXT NOT NULL,
    content_summary TEXT,
    optimized_titles TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Track diagnoses table
CREATE TABLE IF NOT EXISTS track_diagnoses (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    track_keyword TEXT NOT NULL,
    health_score REAL NOT NULL,
    competitiveness_score REAL NOT NULL,
    direction_advice TEXT NOT NULL,
    sub_tracks TEXT NOT NULL,
    confidence REAL NOT NULL,
    data_source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Feedback records table (legacy; production writes user_feedback, not this
-- table — kept here to preserve fresh-DB == old-prod-DB parity until a
-- dedicated 007_drop_unused_feedback_tables migration retires it).
CREATE TABLE IF NOT EXISTS feedback_records (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    feedback_type TEXT NOT NULL,
    feedback_value TEXT,
    reason TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Feedback analyses table (legacy; FK -> feedback_records; orphaned by the
-- migration to user_feedback, kept for parity until 007 retires it).
CREATE TABLE IF NOT EXISTS feedback_analyses (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    feedback_record_id TEXT NOT NULL,
    success_factors TEXT,
    failure_factors TEXT,
    weight_adjustments TEXT NOT NULL,
    excluded_patterns TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (feedback_record_id) REFERENCES feedback_records(id)
);

-- Effect reviews table (overlap with 003_effect_reviews.sql).
-- Authoritative = migration 003 full-column shape (the post-step back-fills
-- these same columns on old DBs). Indexes that 003 deliberately moved to its
-- post-step are declared here too — on a fresh DB the columns already exist,
-- so the indexes are safe; on an old DB 000 no-ops and the post-step creates
-- them. Both paths converge on the same index set.
CREATE TABLE IF NOT EXISTS effect_reviews (
    id                CHAR(36) PRIMARY KEY,
    user_id           CHAR(36) NOT NULL,
    topic_title       TEXT     NOT NULL,
    content_outline   TEXT     NOT NULL DEFAULT '',
    prediction        TEXT     NOT NULL,
    actual_result     TEXT,
    attribution       TEXT,
    learnings         TEXT,
    status            TEXT     NOT NULL DEFAULT 'awaiting_actuals',
    created_at        TEXT     NOT NULL,
    updated_at        TEXT     NOT NULL DEFAULT '',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- NOTE: the two effect_reviews indexes (idx_effect_reviews_user_id_created_at,
-- idx_effect_reviews_status) are intentionally NOT created here. They live in
-- migration 003's post-step (_post_step_003_effect_reviews), which back-fills
-- the ``status`` column on a legacy pre-Bug-3 table BEFORE creating the
-- index. Declaring them here would crash on a legacy table missing the
-- column ("no such column: status"). On a fresh DB 003's post-step is a
-- no-op for columns and then creates the indexes — so they still land. Both
-- the fresh and legacy paths converge on the same index set via 003's
-- post-step, not here.

-- Content risks table
CREATE TABLE IF NOT EXISTS content_risks (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    content_text TEXT NOT NULL,
    content_text_expires_at TEXT,
    risks TEXT NOT NULL,
    overall_risk_score REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Publish suggestions table
CREATE TABLE IF NOT EXISTS publish_suggestions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    content_type TEXT NOT NULL,
    suggested_times TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- User events table (PostHog)
CREATE TABLE IF NOT EXISTS user_events (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- LLM call logs table (LangFuse)
CREATE TABLE IF NOT EXISTS llm_call_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    model_version TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    chain_name TEXT NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    latency_ms INTEGER,
    success INTEGER NOT NULL DEFAULT 1,
    error_message TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Upgrade signals table
CREATE TABLE IF NOT EXISTS upgrade_signals (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    feature_name TEXT NOT NULL,
    action TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Phase 6/7 contract: assets
CREATE TABLE IF NOT EXISTS assets (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('image','document','audio','video','template')),
    size INTEGER NOT NULL,
    url TEXT NOT NULL,
    thumbnail_url TEXT,
    used_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_assets_owner_id ON assets(owner_id);
CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(type);

CREATE TABLE IF NOT EXISTS asset_tags (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    name TEXT NOT NULL,
    color TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (owner_id, name),
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_asset_tags_owner_id ON asset_tags(owner_id);

CREATE TABLE IF NOT EXISTS asset_tag_links (
    asset_id TEXT NOT NULL,
    tag_id TEXT NOT NULL,
    PRIMARY KEY (asset_id, tag_id),
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES asset_tags(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS asset_usages (
    id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    article_id TEXT NOT NULL,
    used_at TEXT NOT NULL,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_asset_usages_asset_id ON asset_usages(asset_id);

-- Phase 6/7 contract: platform_accounts (human-facing account pointers;
-- distinct from platform_tokens which holds encrypted OAuth tokens).
CREATE TABLE IF NOT EXISTS platform_accounts (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    platform TEXT NOT NULL CHECK (platform IN ('wechat_mp','wechat_video','xhs','bilibili','douyin','zhihu')),
    display_name TEXT NOT NULL,
    is_primary INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL CHECK (status IN ('connected','expired','disconnected')) DEFAULT 'disconnected',
    token_expires_at TEXT,
    last_sync_at TEXT,
    stats_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (owner_id, platform, display_name),
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_platform_accounts_owner_id ON platform_accounts(owner_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_platform_accounts_primary
    ON platform_accounts(owner_id, platform)
    WHERE is_primary = 1;

-- Phase 6/7 contract: team_members
CREATE TABLE IF NOT EXISTS team_members (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    email TEXT NOT NULL,
    username TEXT NOT NULL,
    initial TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin','editor','viewer')),
    joined_at TEXT NOT NULL,
    last_active_at TEXT,
    UNIQUE (owner_id, email),
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_team_members_owner_id ON team_members(owner_id);
