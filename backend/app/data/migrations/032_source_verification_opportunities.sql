-- User-submitted source opportunities remain blocked until provenance is verified.

ALTER TABLE content_opportunity_events
    RENAME TO content_opportunity_events_before_source_verification;
ALTER TABLE content_opportunities
    RENAME TO content_opportunities_before_source_verification;

CREATE TABLE content_opportunities (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    opportunity_type TEXT NOT NULL
        CHECK (opportunity_type IN ('series_extension','user_source')),
    source_ref TEXT NOT NULL,
    source_excerpt TEXT,
    source_url TEXT,
    source_published_at TEXT,
    source_authority TEXT,
    verification_status TEXT NOT NULL DEFAULT 'verified'
        CHECK (verification_status IN ('verified','pending_verification')),
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

INSERT INTO content_opportunities (
    id,owner_user_id,opportunity_type,source_ref,verification_status,
    content_intent,content_format,proposed_title,proposed_audience_change,
    proposed_rationale,proposed_material_requirements_json,confirmed_title,
    confirmed_audience_change,confirmed_material_requirements_json,evidence_refs_json,
    unknown_refs_json,status,proposal_source,ai_trace_id,created_project_id,
    limitations_json,version,idempotency_key,request_hash,created_at,updated_at,decided_at
)
SELECT
    id,owner_user_id,opportunity_type,source_ref,'verified',
    content_intent,content_format,proposed_title,proposed_audience_change,
    proposed_rationale,proposed_material_requirements_json,confirmed_title,
    confirmed_audience_change,confirmed_material_requirements_json,evidence_refs_json,
    unknown_refs_json,status,proposal_source,ai_trace_id,created_project_id,
    limitations_json,version,idempotency_key,request_hash,created_at,updated_at,decided_at
FROM content_opportunities_before_source_verification;

CREATE TABLE content_opportunity_events (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    opportunity_id TEXT NOT NULL,
    event_type TEXT NOT NULL
        CHECK (event_type IN ('proposed','accepted','rejected','project_created')),
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

INSERT INTO content_opportunity_events (
    id,owner_user_id,opportunity_id,event_type,from_status,to_status,payload_json,
    opportunity_version,idempotency_key,request_hash,created_at
)
SELECT
    id,owner_user_id,opportunity_id,event_type,from_status,to_status,payload_json,
    opportunity_version,idempotency_key,request_hash,created_at
FROM content_opportunity_events_before_source_verification;

DROP TABLE content_opportunity_events_before_source_verification;
DROP TABLE content_opportunities_before_source_verification;

CREATE UNIQUE INDEX uq_content_opportunities_owner_idempotency
    ON content_opportunities(owner_user_id, idempotency_key);
CREATE INDEX idx_content_opportunities_owner_status
    ON content_opportunities(owner_user_id, status, updated_at DESC);
CREATE INDEX idx_content_opportunities_source
    ON content_opportunities(owner_user_id, source_ref, updated_at DESC);
CREATE UNIQUE INDEX uq_content_opportunity_events_owner_idempotency
    ON content_opportunity_events(owner_user_id, idempotency_key);
CREATE INDEX idx_content_opportunity_events_created
    ON content_opportunity_events(opportunity_id, created_at);
