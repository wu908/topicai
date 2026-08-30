-- Audited, explicit decisions for overlapping creator rules.
CREATE TABLE IF NOT EXISTS creator_rule_resolutions (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    conflict_rule_id TEXT NOT NULL,
    resolution_type TEXT NOT NULL CHECK (resolution_type IN ('narrow_scope','keep_exception','deactivate')),
    scope_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL CHECK (status IN ('applied','superseded')),
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (rule_id) REFERENCES creator_rules(id) ON DELETE CASCADE,
    FOREIGN KEY (conflict_rule_id) REFERENCES creator_rules(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_creator_rule_resolutions_owner_idempotency
    ON creator_rule_resolutions(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_creator_rule_resolutions_pair
    ON creator_rule_resolutions(owner_user_id, rule_id, conflict_rule_id, created_at DESC);
