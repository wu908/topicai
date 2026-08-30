-- First-party evidence is proposed before it can become creator state or
-- be referenced by a candidate content version.

CREATE TABLE IF NOT EXISTS evidence_items (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN (
        'user_fact','external_fact','ai_inference','validated_insight'
    )),
    statement TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    content_ref TEXT,
    privacy_level TEXT NOT NULL DEFAULT 'private' CHECK (
        privacy_level IN ('public','private','sensitive')
    ),
    confirmation_status TEXT NOT NULL DEFAULT 'proposed' CHECK (
        confirmation_status IN ('proposed','confirmed','rejected','revoked')
    ),
    reusable INTEGER NOT NULL DEFAULT 0 CHECK (reusable IN (0,1)),
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    decision_idempotency_key TEXT,
    decision_request_hash TEXT,
    revoked_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES content_projects(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_evidence_items_owner_idempotency
    ON evidence_items(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_evidence_items_owner_project
    ON evidence_items(owner_user_id, project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_evidence_items_owner_status
    ON evidence_items(owner_user_id, confirmation_status, updated_at DESC);
