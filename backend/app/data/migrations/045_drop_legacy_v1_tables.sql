-- v2-only cutover. Preserve shared data under v2 names before dropping v1 tables.
CREATE TABLE IF NOT EXISTS materials (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN (
        'text','link','image','document','audio','video','template'
    )),
    size INTEGER NOT NULL DEFAULT 0,
    source_url TEXT NOT NULL,
    thumbnail_url TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE
);

INSERT OR IGNORE INTO materials (
    id,owner_user_id,name,mime_type,kind,size,source_url,thumbnail_url,created_at,updated_at
)
SELECT id,owner_id,filename,mime_type,type,size,url,thumbnail_url,created_at,updated_at
FROM assets;

CREATE INDEX IF NOT EXISTS idx_materials_owner_updated
    ON materials(owner_user_id, updated_at DESC, id);

CREATE TABLE IF NOT EXISTS material_usages (
    id TEXT PRIMARY KEY,
    material_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    used_at TEXT NOT NULL,
    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE
);

INSERT OR IGNORE INTO material_usages (id,material_id,project_id,used_at)
SELECT id,asset_id,article_id,used_at FROM asset_usages;

CREATE INDEX IF NOT EXISTS idx_material_usages_material
    ON material_usages(material_id);

CREATE TABLE creator_profiles_v2 (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    niche TEXT,
    target_audience TEXT,
    growth_goal TEXT NOT NULL DEFAULT 'stable_publish'
        CHECK (growth_goal IN ('stable_publish','follower_growth','both')),
    content_pillars_json TEXT NOT NULL DEFAULT '[]',
    voice_traits_json TEXT NOT NULL DEFAULT '[]',
    avoid_traits_json TEXT NOT NULL DEFAULT '[]',
    evidence_refs_json TEXT NOT NULL DEFAULT '[]',
    confirmation_state TEXT NOT NULL DEFAULT 'provisional'
        CHECK (confirmation_state IN ('provisional','confirmed','needs_review')),
    confirmed_at TEXT,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    profile_attributes_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

INSERT INTO creator_profiles_v2 (
    id,user_id,niche,target_audience,growth_goal,content_pillars_json,
    voice_traits_json,avoid_traits_json,evidence_refs_json,confirmation_state,
    confirmed_at,version,profile_attributes_json,created_at,updated_at
)
SELECT
    id,user_id,COALESCE(NULLIF(niche,''),track),target_audience,growth_goal,
    content_pillars_json,voice_traits_json,avoid_traits_json,evidence_refs_json,
    confirmation_state,confirmed_at,version,profile_attributes_json,created_at,updated_at
FROM creator_profiles;

DROP TABLE creator_profiles;
ALTER TABLE creator_profiles_v2 RENAME TO creator_profiles;
CREATE INDEX IF NOT EXISTS idx_creator_profiles_user_id ON creator_profiles(user_id);

DROP TABLE IF EXISTS asset_tag_links;
DROP TABLE IF EXISTS asset_usages;
DROP TABLE IF EXISTS asset_tags;
DROP TABLE IF EXISTS assets;
DROP TABLE IF EXISTS platform_tokens;
DROP TABLE IF EXISTS platform_accounts;
DROP TABLE IF EXISTS team_members;
DROP TABLE IF EXISTS user_feedback;
DROP TABLE IF EXISTS feedback_analyses;
DROP TABLE IF EXISTS feedback_records;
DROP TABLE IF EXISTS risk_keywords;
DROP TABLE IF EXISTS content_risks;
DROP TABLE IF EXISTS effect_reviews;
DROP TABLE IF EXISTS publish_suggestions;
DROP TABLE IF EXISTS topic_recommendations;
DROP TABLE IF EXISTS viral_analyses;
DROP TABLE IF EXISTS idea_boosters;
DROP TABLE IF EXISTS title_optimizations;
DROP TABLE IF EXISTS track_diagnoses;
DROP TABLE IF EXISTS user_events;
DROP TABLE IF EXISTS llm_call_logs;
DROP TABLE IF EXISTS upgrade_signals;
