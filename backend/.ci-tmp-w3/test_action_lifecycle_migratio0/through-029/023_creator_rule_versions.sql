-- Cross-project validated creator rules. Content and events are immutable;
-- only the aggregate's active_version_id moves during activation/rollback.

CREATE TABLE IF NOT EXISTS creator_rules (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    rule_key TEXT NOT NULL,
    content_intent TEXT NOT NULL CHECK (content_intent IN ('solve','share','record')),
    active_version_id TEXT,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_creator_rules_owner_key
    ON creator_rules(owner_user_id, rule_key);

CREATE TABLE IF NOT EXISTS creator_rule_versions (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    version_number INTEGER NOT NULL CHECK (version_number >= 1),
    statement TEXT NOT NULL,
    scope_json TEXT NOT NULL DEFAULT '{}',
    source_observation_ids_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL CHECK (status IN ('proposed','active','retired','rejected')),
    previous_version_id TEXT,
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    confirmed_at TEXT,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (rule_id) REFERENCES creator_rules(id) ON DELETE CASCADE,
    FOREIGN KEY (previous_version_id) REFERENCES creator_rule_versions(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_creator_rule_versions_owner_idempotency
    ON creator_rule_versions(owner_user_id, idempotency_key);
CREATE UNIQUE INDEX IF NOT EXISTS uq_creator_rule_versions_rule_number
    ON creator_rule_versions(rule_id, version_number);
CREATE INDEX IF NOT EXISTS idx_creator_rule_versions_owner_status
    ON creator_rule_versions(owner_user_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS creator_rule_events (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    rule_version_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('proposed','confirmed','rejected','rollback')),
    payload_json TEXT NOT NULL DEFAULT '{}',
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (rule_id) REFERENCES creator_rules(id) ON DELETE CASCADE,
    FOREIGN KEY (rule_version_id) REFERENCES creator_rule_versions(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_creator_rule_events_owner_idempotency
    ON creator_rule_events(owner_user_id, idempotency_key);
