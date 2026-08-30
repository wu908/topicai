-- Explicitly confirmed creator viewpoints. Candidates and events remain auditable;
-- only confirmed, source-valid viewpoints may enter ContentGenome.

CREATE TABLE IF NOT EXISTS creator_viewpoints (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    content_intent TEXT NOT NULL CHECK (content_intent IN ('solve','share','record')),
    proposed_statement TEXT NOT NULL,
    proposed_rationale TEXT NOT NULL,
    confirmed_statement TEXT,
    scope_json TEXT NOT NULL DEFAULT '{}',
    source_evidence_ids_json TEXT NOT NULL DEFAULT '[]',
    source_content_version_id TEXT,
    privacy_level TEXT NOT NULL DEFAULT 'private' CHECK (privacy_level IN ('private','sensitive')),
    status TEXT NOT NULL CHECK (status IN ('proposed','confirmed','rejected','revoked')),
    proposal_source TEXT NOT NULL CHECK (proposal_source IN ('ai','deterministic_fallback')),
    ai_trace_id TEXT NOT NULL,
    limitations_json TEXT NOT NULL DEFAULT '[]',
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    confirmed_at TEXT,
    revoked_at TEXT,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES content_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (source_content_version_id) REFERENCES content_versions(id),
    FOREIGN KEY (ai_trace_id) REFERENCES ai_traces_v2(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_creator_viewpoints_owner_idempotency
    ON creator_viewpoints(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_creator_viewpoints_owner_status
    ON creator_viewpoints(owner_user_id, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_creator_viewpoints_project_status
    ON creator_viewpoints(project_id, status, updated_at DESC);

CREATE TABLE IF NOT EXISTS creator_viewpoint_events (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    viewpoint_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('proposed','confirmed','rejected','revoked')),
    from_status TEXT,
    to_status TEXT NOT NULL CHECK (to_status IN ('proposed','confirmed','rejected','revoked')),
    payload_json TEXT NOT NULL DEFAULT '{}',
    viewpoint_version INTEGER NOT NULL CHECK (viewpoint_version >= 1),
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (viewpoint_id) REFERENCES creator_viewpoints(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_creator_viewpoint_events_owner_idempotency
    ON creator_viewpoint_events(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_creator_viewpoint_events_viewpoint_created
    ON creator_viewpoint_events(viewpoint_id, created_at);
