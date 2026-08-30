-- Explainable content opportunities that create projects only after user acceptance.

CREATE TABLE IF NOT EXISTS content_opportunities (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    opportunity_type TEXT NOT NULL CHECK (opportunity_type IN ('series_extension')),
    source_ref TEXT NOT NULL,
    content_intent TEXT NOT NULL CHECK (content_intent IN ('solve','share','record')),
    content_format TEXT NOT NULL CHECK (content_format IN ('graphic_note','vlog_plan')),
    proposed_title TEXT NOT NULL,
    proposed_audience_change TEXT NOT NULL,
    proposed_rationale TEXT NOT NULL,
    proposed_material_requirements_json TEXT NOT NULL DEFAULT '[]',
    confirmed_title TEXT,
    confirmed_audience_change TEXT,
    confirmed_material_requirements_json TEXT,
    evidence_refs_json TEXT NOT NULL DEFAULT '[]',
    unknown_refs_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL CHECK (status IN ('proposed','accepted','rejected')),
    proposal_source TEXT NOT NULL CHECK (proposal_source IN ('ai','deterministic_fallback')),
    ai_trace_id TEXT NOT NULL,
    created_project_id TEXT,
    limitations_json TEXT NOT NULL DEFAULT '[]',
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    decided_at TEXT,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (ai_trace_id) REFERENCES ai_traces_v2(id),
    FOREIGN KEY (created_project_id) REFERENCES content_projects(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_content_opportunities_owner_idempotency
    ON content_opportunities(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_content_opportunities_owner_status
    ON content_opportunities(owner_user_id, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_content_opportunities_source
    ON content_opportunities(owner_user_id, source_ref, updated_at DESC);

CREATE TABLE IF NOT EXISTS content_opportunity_events (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    opportunity_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('proposed','accepted','rejected','project_created')),
    from_status TEXT,
    to_status TEXT NOT NULL CHECK (to_status IN ('proposed','accepted','rejected')),
    payload_json TEXT NOT NULL DEFAULT '{}',
    opportunity_version INTEGER NOT NULL CHECK (opportunity_version >= 1),
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (opportunity_id) REFERENCES content_opportunities(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_content_opportunity_events_owner_idempotency
    ON content_opportunity_events(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_content_opportunity_events_created
    ON content_opportunity_events(opportunity_id, created_at);
