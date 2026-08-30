-- 005_creator_profiles.sql
-- Creator profile table for TopicAI v4.0 onboarding.
-- Stores user content-creation preferences and AI-inferred rubric weights.
CREATE TABLE IF NOT EXISTS creator_profiles (
    id                    TEXT PRIMARY KEY,
    user_id               TEXT NOT NULL UNIQUE,
    track                 TEXT NOT NULL,
    content_formats        TEXT NOT NULL,  -- JSON-encoded list
    production_complexity  TEXT NOT NULL,
    content_depth         TEXT NOT NULL,
    hotspot_preference     TEXT NOT NULL,
    recommendation_mode   TEXT NOT NULL CHECK (recommendation_mode IN ('hotspot_fusion','evergreen_deep')),
    rubric_weights        TEXT NOT NULL DEFAULT '{}',  -- JSON-encoded object
    created_at            TEXT NOT NULL,
    updated_at            TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_creator_profiles_user_id ON creator_profiles(user_id);