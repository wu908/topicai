-- Growth onboarding: mode, historical evidence, and correctable profile fields.

ALTER TABLE users ADD COLUMN product_mode TEXT NOT NULL DEFAULT 'growth'
    CHECK (product_mode IN ('starter','growth'));
ALTER TABLE users ADD COLUMN onboarding_state TEXT NOT NULL DEFAULT 'not_started'
    CHECK (onboarding_state IN ('not_started','in_progress','completed'));
ALTER TABLE users ADD COLUMN onboarding_version INTEGER NOT NULL DEFAULT 1
    CHECK (onboarding_version >= 1);
ALTER TABLE users ADD COLUMN timezone TEXT NOT NULL DEFAULT 'Asia/Shanghai';
ALTER TABLE users ADD COLUMN weekly_publish_goal INTEGER NOT NULL DEFAULT 2
    CHECK (weekly_publish_goal BETWEEN 1 AND 4);
ALTER TABLE users ADD COLUMN consent_json TEXT NOT NULL DEFAULT '{}';

ALTER TABLE creator_profiles ADD COLUMN niche TEXT;
ALTER TABLE creator_profiles ADD COLUMN target_audience TEXT;
ALTER TABLE creator_profiles ADD COLUMN growth_goal TEXT NOT NULL DEFAULT 'stable_publish'
    CHECK (growth_goal IN ('stable_publish','follower_growth','both'));
ALTER TABLE creator_profiles ADD COLUMN content_pillars_json TEXT NOT NULL DEFAULT '[]';
ALTER TABLE creator_profiles ADD COLUMN voice_traits_json TEXT NOT NULL DEFAULT '[]';
ALTER TABLE creator_profiles ADD COLUMN avoid_traits_json TEXT NOT NULL DEFAULT '[]';
ALTER TABLE creator_profiles ADD COLUMN evidence_refs_json TEXT NOT NULL DEFAULT '[]';
ALTER TABLE creator_profiles ADD COLUMN confirmation_state TEXT NOT NULL DEFAULT 'provisional'
    CHECK (confirmation_state IN ('provisional','confirmed','needs_review'));
ALTER TABLE creator_profiles ADD COLUMN confirmed_at TEXT;
ALTER TABLE creator_profiles ADD COLUMN version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1);
ALTER TABLE creator_profiles ADD COLUMN profile_attributes_json TEXT NOT NULL DEFAULT '{}';

CREATE TABLE IF NOT EXISTS history_imports (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    method TEXT NOT NULL CHECK (method IN ('manual','csv','json')),
    status TEXT NOT NULL CHECK (status IN ('completed','partial','failed')),
    input_count INTEGER NOT NULL CHECK (input_count >= 1 AND input_count <= 200),
    success_count INTEGER NOT NULL DEFAULT 0 CHECK (success_count >= 0),
    failure_count INTEGER NOT NULL DEFAULT 0 CHECK (failure_count >= 0),
    item_results_json TEXT NOT NULL DEFAULT '[]',
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_history_import_owner_key
    ON history_imports(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_history_import_owner_started
    ON history_imports(owner_user_id, started_at DESC);

CREATE TABLE IF NOT EXISTS imported_notes (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    history_import_id TEXT NOT NULL,
    external_key TEXT,
    title TEXT NOT NULL,
    body_excerpt TEXT NOT NULL DEFAULT '',
    published_at TEXT,
    note_url TEXT,
    metrics_json TEXT NOT NULL DEFAULT '{}',
    audience_questions_json TEXT NOT NULL DEFAULT '[]',
    tags_json TEXT NOT NULL DEFAULT '[]',
    source_hash TEXT NOT NULL,
    retention_expires_at TEXT NOT NULL,
    user_confirmed INTEGER NOT NULL DEFAULT 0 CHECK (user_confirmed IN (0,1)),
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (history_import_id) REFERENCES history_imports(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_imported_note_owner_source
    ON imported_notes(owner_user_id, source_hash);
CREATE INDEX IF NOT EXISTS idx_imported_note_owner_published
    ON imported_notes(owner_user_id, published_at DESC, created_at DESC);
