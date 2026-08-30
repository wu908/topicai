-- Additive columns are guarded by the migration runner for partial-DDL recovery.

CREATE UNIQUE INDEX IF NOT EXISTS idx_materials_owner_idempotency
    ON materials(owner_user_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS publish_checks_v2 (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    content_version_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    findings_json TEXT NOT NULL DEFAULT '[]',
    limitations_json TEXT NOT NULL DEFAULT '[]',
    ai_trace_id TEXT,
    rule_version TEXT NOT NULL,
    rule_updated_at TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    UNIQUE(owner_user_id, idempotency_key),
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES content_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (content_version_id) REFERENCES content_versions(id),
    FOREIGN KEY (ai_trace_id) REFERENCES ai_traces_v2(id)
);

CREATE INDEX IF NOT EXISTS idx_publish_checks_project_version
    ON publish_checks_v2(owner_user_id, project_id, content_version_id, checked_at DESC);

CREATE TABLE IF NOT EXISTS publish_check_resolutions_v2 (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    publish_check_id TEXT NOT NULL,
    findings_json TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(owner_user_id, idempotency_key),
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (publish_check_id) REFERENCES publish_checks_v2(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS snapshot_extractions_v2 (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    material_id TEXT,
    metrics_json TEXT NOT NULL,
    ai_trace_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(owner_user_id, idempotency_key),
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE SET NULL,
    FOREIGN KEY (ai_trace_id) REFERENCES ai_traces_v2(id)
);
