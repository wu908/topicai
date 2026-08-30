-- Spec-009: immutable pre-publication judgment bound to one content version.

CREATE TABLE IF NOT EXISTS publish_hypotheses (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    content_version_id TEXT NOT NULL,
    audience_problem TEXT NOT NULL,
    reader_promise TEXT NOT NULL,
    expected_behaviors_json TEXT NOT NULL,
    basis_refs_json TEXT NOT NULL DEFAULT '[]',
    uncertainties_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL CHECK (status IN ('draft','locked','superseded','legacy_missing')),
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    locked_at TEXT NOT NULL,
    locked_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES content_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (content_version_id) REFERENCES content_versions(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_publish_hypotheses_project_version
    ON publish_hypotheses(project_id, content_version_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_publish_hypotheses_project_idempotency
    ON publish_hypotheses(project_id, idempotency_key);
