-- Append-only ContentProject status audit. The aggregate row remains the
-- current-state authority; these events are not replayed to rebuild it.

CREATE TABLE IF NOT EXISTS project_state_events (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    from_status TEXT NOT NULL CHECK (from_status IN (
        'inbox','preparing','creating','ready_to_publish',
        'published','awaiting_review','settled'
    )),
    to_status TEXT NOT NULL CHECK (to_status IN (
        'inbox','preparing','creating','ready_to_publish',
        'published','awaiting_review','settled'
    )),
    reason TEXT NOT NULL,
    actor_type TEXT NOT NULL CHECK (actor_type IN ('user','system')),
    project_version INTEGER NOT NULL CHECK (project_version >= 2),
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES content_projects(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_project_state_events_owner_idempotency
    ON project_state_events(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_project_state_events_project_created
    ON project_state_events(project_id, created_at, id);
