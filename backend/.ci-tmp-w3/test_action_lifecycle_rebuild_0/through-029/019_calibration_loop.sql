-- Spec-008/009: manual publication facts and an auditable calibration loop.

CREATE TABLE IF NOT EXISTS publish_records_v2 (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    locked_version_id TEXT NOT NULL,
    publish_hypothesis_id TEXT NOT NULL,
    platform TEXT NOT NULL DEFAULT 'xiaohongshu' CHECK (platform = 'xiaohongshu'),
    note_url TEXT,
    published_at TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES content_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (locked_version_id) REFERENCES content_versions(id),
    FOREIGN KEY (publish_hypothesis_id) REFERENCES publish_hypotheses(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_publish_records_v2_project
    ON publish_records_v2(project_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_publish_records_v2_owner_idempotency
    ON publish_records_v2(owner_user_id, idempotency_key);

CREATE TABLE IF NOT EXISTS performance_snapshots_v2 (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    publish_record_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('manual','screenshot')),
    metrics_json TEXT NOT NULL,
    screenshot_material_id TEXT,
    confirmed_by_user INTEGER NOT NULL CHECK (confirmed_by_user = 1),
    supersedes_id TEXT,
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (publish_record_id) REFERENCES publish_records_v2(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES content_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (supersedes_id) REFERENCES performance_snapshots_v2(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_performance_snapshots_v2_owner_idempotency
    ON performance_snapshots_v2(owner_user_id, idempotency_key);
CREATE UNIQUE INDEX IF NOT EXISTS uq_performance_snapshots_v2_supersedes
    ON performance_snapshots_v2(supersedes_id) WHERE supersedes_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_performance_snapshots_v2_record_captured
    ON performance_snapshots_v2(publish_record_id, captured_at);

CREATE TABLE IF NOT EXISTS ai_traces_v2 (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    input_refs_json TEXT NOT NULL,
    evidence_refs_json TEXT NOT NULL DEFAULT '[]',
    policy_version TEXT NOT NULL,
    model_identifier TEXT,
    capability TEXT NOT NULL,
    visibility_boundary_json TEXT NOT NULL,
    source_snapshot_ids_json TEXT NOT NULL DEFAULT '[]',
    contamination_check_json TEXT NOT NULL,
    calibration_state TEXT NOT NULL CHECK (calibration_state IN (
        'valid','insufficient','calibration_invalid'
    )),
    limitations_json TEXT NOT NULL DEFAULT '[]',
    output_ref TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ai_traces_v2_owner_task
    ON ai_traces_v2(owner_user_id, task_type, generated_at);

CREATE TABLE IF NOT EXISTS blind_reviews (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    publish_hypothesis_id TEXT NOT NULL,
    hypothesis_snapshot_json TEXT NOT NULL,
    result_snapshot_ids_json TEXT NOT NULL,
    comparison_json TEXT NOT NULL,
    visibility_boundary_json TEXT NOT NULL,
    contamination_status TEXT NOT NULL CHECK (contamination_status IN (
        'clean','suspected','contaminated'
    )),
    calibration_state TEXT NOT NULL CHECK (calibration_state IN (
        'valid','insufficient','calibration_invalid'
    )),
    eligible_for_rule_upgrade INTEGER NOT NULL DEFAULT 0 CHECK (
        eligible_for_rule_upgrade IN (0,1)
    ),
    ai_trace_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES content_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (publish_hypothesis_id) REFERENCES publish_hypotheses(id),
    FOREIGN KEY (ai_trace_id) REFERENCES ai_traces_v2(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_blind_reviews_owner_idempotency
    ON blind_reviews(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_blind_reviews_project_created
    ON blind_reviews(project_id, created_at);

CREATE TABLE IF NOT EXISTS observations (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    blind_review_id TEXT NOT NULL,
    statement TEXT NOT NULL,
    scope_json TEXT NOT NULL DEFAULT '{}',
    support_project_refs_json TEXT NOT NULL,
    counterexample_refs_json TEXT NOT NULL DEFAULT '[]',
    sample_count INTEGER NOT NULL DEFAULT 1 CHECK (sample_count >= 1),
    next_test TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL CHECK (lifecycle_status IN (
        'observing','pending_validation','absorbed','refuted','archived'
    )),
    user_decision TEXT NOT NULL DEFAULT 'confirmed' CHECK (user_decision IN (
        'confirmed','rejected'
    )),
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES content_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (blind_review_id) REFERENCES blind_reviews(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_observations_owner_idempotency
    ON observations(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_observations_owner_status
    ON observations(owner_user_id, lifecycle_status, updated_at);

CREATE TABLE IF NOT EXISTS observation_events (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    observation_id TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT NOT NULL,
    reason TEXT NOT NULL,
    observation_version INTEGER NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (observation_id) REFERENCES observations(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_observation_events_owner_idempotency
    ON observation_events(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_observation_events_observation_created
    ON observation_events(observation_id, created_at);
