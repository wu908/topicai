-- User-confirmed relationships among multiple published content projects.
-- Candidates remain auditable; only confirmed, source-valid series enter ContentGenome.

CREATE TABLE IF NOT EXISTS creator_series (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    content_intent TEXT NOT NULL CHECK (content_intent IN ('solve','share','record')),
    content_format TEXT NOT NULL CHECK (content_format IN ('graphic_note','vlog_plan')),
    proposed_name TEXT NOT NULL,
    proposed_promise TEXT NOT NULL,
    proposed_rationale TEXT NOT NULL,
    proposed_continuation_prompt TEXT NOT NULL,
    confirmed_name TEXT,
    confirmed_promise TEXT,
    confirmed_continuation_prompt TEXT,
    scope_json TEXT NOT NULL DEFAULT '{}',
    source_project_ids_json TEXT NOT NULL DEFAULT '[]',
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
    FOREIGN KEY (ai_trace_id) REFERENCES ai_traces_v2(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_creator_series_owner_idempotency
    ON creator_series(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_creator_series_owner_status
    ON creator_series(owner_user_id, status, updated_at DESC);

CREATE TABLE IF NOT EXISTS creator_series_events (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    series_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('proposed','confirmed','rejected','revoked')),
    from_status TEXT,
    to_status TEXT NOT NULL CHECK (to_status IN ('proposed','confirmed','rejected','revoked')),
    payload_json TEXT NOT NULL DEFAULT '{}',
    series_version INTEGER NOT NULL CHECK (series_version >= 1),
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (series_id) REFERENCES creator_series(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_creator_series_events_owner_idempotency
    ON creator_series_events(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_creator_series_events_series_created
    ON creator_series_events(series_id, created_at);
