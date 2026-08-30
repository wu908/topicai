-- Spec-008/009: minimal ContentProject aggregate required by the first
-- publish-calibration vertical slice. Later brief/interview tables remain
-- additive migrations; this table is the lifecycle aggregate root.

CREATE TABLE IF NOT EXISTS content_projects (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN (
        'inbox','preparing','creating','ready_to_publish',
        'published','awaiting_review','settled'
    )),
    platform TEXT NOT NULL DEFAULT 'xiaohongshu' CHECK (platform = 'xiaohongshu'),
    format TEXT NOT NULL DEFAULT 'graphic_note' CHECK (format = 'graphic_note'),
    primary_goal TEXT NOT NULL CHECK (primary_goal IN (
        'stable_publish','follower_growth','experiment'
    )),
    target_audience TEXT NOT NULL,
    opportunity_id TEXT,
    starter_sprint_id TEXT,
    planned_publish_at TEXT,
    current_version_id TEXT,
    locked_publish_version_id TEXT,
    publish_hypothesis_id TEXT,
    calibration_state TEXT NOT NULL DEFAULT 'not_ready' CHECK (calibration_state IN (
        'not_ready','insufficient','valid','calibration_invalid'
    )),
    last_action TEXT,
    last_action_at TEXT NOT NULL,
    archived_at TEXT,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    idempotency_key TEXT,
    request_hash TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_content_projects_owner_status
    ON content_projects(owner_user_id, status, updated_at);
CREATE UNIQUE INDEX IF NOT EXISTS uq_content_projects_owner_idempotency
    ON content_projects(owner_user_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;
