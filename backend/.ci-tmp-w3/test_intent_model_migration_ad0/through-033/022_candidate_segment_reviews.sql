-- Candidate review is an append-only decision layer over immutable content versions.

CREATE TABLE IF NOT EXISTS content_segments (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    content_version_id TEXT NOT NULL,
    segment_key TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    segment_type TEXT NOT NULL CHECK (segment_type IN ('title','body')),
    text TEXT NOT NULL,
    source_refs_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES content_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (content_version_id) REFERENCES content_versions(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_content_segments_version_key
    ON content_segments(content_version_id, segment_key);
CREATE INDEX IF NOT EXISTS idx_content_segments_owner_project
    ON content_segments(owner_user_id, project_id, content_version_id, ordinal);

CREATE TABLE IF NOT EXISTS content_segment_decisions (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    content_version_id TEXT NOT NULL,
    segment_id TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('accepted','rejected','replaced')),
    replacement_text TEXT,
    reason TEXT,
    version INTEGER NOT NULL CHECK (version >= 1),
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES content_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (content_version_id) REFERENCES content_versions(id) ON DELETE CASCADE,
    FOREIGN KEY (segment_id) REFERENCES content_segments(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_content_segment_decisions_owner_idempotency
    ON content_segment_decisions(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_content_segment_decisions_segment_version
    ON content_segment_decisions(segment_id, version DESC);
