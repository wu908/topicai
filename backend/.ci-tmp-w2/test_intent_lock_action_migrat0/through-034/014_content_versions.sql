-- Immutable content snapshots. Editing always inserts a new row.

CREATE TABLE IF NOT EXISTS content_versions (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    parent_version_id TEXT,
    version_number INTEGER NOT NULL CHECK (version_number >= 1),
    title TEXT NOT NULL,
    body_text TEXT NOT NULL,
    cover_plan TEXT NOT NULL DEFAULT '',
    image_plan_json TEXT NOT NULL DEFAULT '[]',
    change_origin TEXT NOT NULL DEFAULT 'user' CHECK (change_origin IN ('user','ai','import')),
    change_summary TEXT,
    evidence_snapshot_json TEXT NOT NULL DEFAULT '[]',
    ai_trace_id TEXT,
    content_hash TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES content_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_version_id) REFERENCES content_versions(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_content_versions_project_number
    ON content_versions(project_id, version_number);
CREATE UNIQUE INDEX IF NOT EXISTS uq_content_versions_project_idempotency
    ON content_versions(project_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_content_versions_project_created
    ON content_versions(project_id, created_at);
