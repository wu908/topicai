-- Phase 15: bounded starter assessment, grounded directions, and one 14-day sprint.
-- Content execution remains in content_projects and the existing action protocol.

CREATE TABLE IF NOT EXISTS starter_assessments (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL UNIQUE,
    motivation TEXT NOT NULL CHECK (motivation IN ('curious','career','expression','other')),
    available_hours_per_week REAL NOT NULL CHECK (
        available_hours_per_week >= 0 AND available_hours_per_week <= 40
    ),
    publish_commitment INTEGER NOT NULL CHECK (publish_commitment IN (0,1)),
    accept_experiment INTEGER NOT NULL CHECK (accept_experiment IN (0,1)),
    experience_assets_json TEXT NOT NULL DEFAULT '[]',
    interest_assets_json TEXT NOT NULL DEFAULT '[]',
    skill_assets_json TEXT NOT NULL DEFAULT '[]',
    privacy_limits_json TEXT NOT NULL DEFAULT '[]',
    readiness TEXT NOT NULL CHECK (readiness IN ('not_ready','ready','paused')),
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    completed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_starter_assessment_owner_key
    ON starter_assessments(owner_user_id, idempotency_key);

CREATE TABLE IF NOT EXISTS starter_direction_candidates (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    assessment_id TEXT NOT NULL,
    direction_key TEXT NOT NULL,
    label TEXT NOT NULL,
    audience TEXT NOT NULL,
    creator_credibility TEXT NOT NULL,
    content_supply_json TEXT NOT NULL,
    first_three_topics_json TEXT NOT NULL,
    production_cost TEXT NOT NULL CHECK (production_cost IN ('low','medium','high')),
    similarity_risk TEXT NOT NULL CHECK (similarity_risk IN ('low','medium','high','unknown')),
    validation_method TEXT NOT NULL,
    evidence_refs_json TEXT NOT NULL,
    selection_state TEXT NOT NULL DEFAULT 'proposed'
        CHECK (selection_state IN ('proposed','selected','rejected')),
    assessment_version INTEGER NOT NULL CHECK (assessment_version >= 1),
    ai_trace_id TEXT,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    generation_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assessment_id) REFERENCES starter_assessments(id) ON DELETE CASCADE,
    FOREIGN KEY (ai_trace_id) REFERENCES ai_traces_v2(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_starter_direction_assessment_key
    ON starter_direction_candidates(assessment_id, direction_key);
CREATE INDEX IF NOT EXISTS idx_starter_direction_owner_assessment
    ON starter_direction_candidates(owner_user_id, assessment_id, created_at);

CREATE TABLE IF NOT EXISTS starter_sprints (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    assessment_id TEXT NOT NULL UNIQUE,
    selected_direction_id TEXT NOT NULL UNIQUE,
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL,
    target_publish_count INTEGER NOT NULL DEFAULT 3 CHECK (target_publish_count = 3),
    graduation_state TEXT NOT NULL DEFAULT 'active'
        CHECK (graduation_state IN ('active','graduated','expired','paused','exited')),
    blocker_reasons_json TEXT NOT NULL DEFAULT '[]',
    next_topics_json TEXT NOT NULL DEFAULT '[]',
    review_summary TEXT,
    reviewed_at TEXT,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    review_idempotency_key TEXT,
    review_request_hash TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assessment_id) REFERENCES starter_assessments(id) ON DELETE CASCADE,
    FOREIGN KEY (selected_direction_id) REFERENCES starter_direction_candidates(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_starter_sprint_owner_key
    ON starter_sprints(owner_user_id, idempotency_key);
