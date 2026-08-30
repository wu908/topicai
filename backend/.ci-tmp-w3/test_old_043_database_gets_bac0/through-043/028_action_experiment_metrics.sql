-- Privacy-safe experiment assignment and action measurement for MVP validation.
-- Product content stays in operational tables; analytics only stores identifiers,
-- enums, timestamps, state transitions, and technical outcome metadata.

CREATE TABLE IF NOT EXISTS experiments (
    id TEXT PRIMARY KEY CHECK (id IN ('E1','E2','E3','E4')),
    name TEXT NOT NULL,
    hypothesis TEXT NOT NULL,
    metric_definitions_json TEXT NOT NULL,
    default_window_days INTEGER NOT NULL CHECK (default_window_days BETWEEN 1 AND 365),
    status TEXT NOT NULL DEFAULT 'planned'
        CHECK (status IN ('planned','running','completed','stopped')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

INSERT OR IGNORE INTO experiments
    (id,name,hypothesis,metric_definitions_json,default_window_days,status,created_at,updated_at)
VALUES
    ('E1','Next best action','A state-aware next action improves valid project progress compared with tool navigation.','{"primary":["action_completion_rate","project_progression_rate"],"guardrails":["rejection_rate","failed_rate"]}',28,'planned',datetime('now'),datetime('now')),
    ('E2','Interview before drafting','Confirming missing first-party evidence before drafting improves evidence retention without reducing publication completion.','{"primary":["action_completion_rate","confirmed_evidence_rate"],"guardrails":["failed_rate","publication_abandonment_rate"]}',28,'planned',datetime('now'),datetime('now')),
    ('E3','Personal context feedback loop','Confirmed evidence and learnings improve later action acceptance without increasing corrections or contamination.','{"primary":["action_acceptance_rate","calibration_valid_rate"],"guardrails":["rejection_rate","contamination_rate"]}',28,'planned',datetime('now'),datetime('now')),
    ('E4','Verified hotspot opportunity','Source-verifiable, creator-matched hotspot opportunities add value without disrupting stable publishing.','{"primary":["action_completion_rate","publication_completion_rate"],"guardrails":["rejection_rate","failed_rate"]}',28,'planned',datetime('now'),datetime('now'));

CREATE TABLE IF NOT EXISTS experiment_assignments (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    cohort TEXT NOT NULL CHECK (cohort IN ('control','variant','observational','excluded')),
    user_segment TEXT NOT NULL CHECK (user_segment IN ('starter','growth','unknown')),
    assignment_source TEXT NOT NULL
        CHECK (assignment_source IN ('manual_internal','deterministic','imported')),
    status TEXT NOT NULL DEFAULT 'planned'
        CHECK (status IN ('planned','active','completed','excluded')),
    exclusion_reason_code TEXT,
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    assigned_at TEXT NOT NULL,
    activated_at TEXT,
    completed_at TEXT,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_experiment_assignments_owner_experiment
    ON experiment_assignments(owner_user_id, experiment_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_experiment_assignments_owner_idempotency
    ON experiment_assignments(owner_user_id, idempotency_key);
CREATE UNIQUE INDEX IF NOT EXISTS uq_experiment_assignments_one_active
    ON experiment_assignments(owner_user_id) WHERE status='active';
CREATE INDEX IF NOT EXISTS idx_experiment_assignments_experiment_cohort
    ON experiment_assignments(experiment_id, cohort, status);

CREATE TABLE IF NOT EXISTS experiment_assignment_events (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    assignment_id TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT NOT NULL,
    cohort TEXT NOT NULL,
    user_segment TEXT NOT NULL,
    assignment_source TEXT NOT NULL,
    exclusion_reason_code TEXT,
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assignment_id) REFERENCES experiment_assignments(id) ON DELETE CASCADE,
    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_experiment_assignment_events_owner_idempotency
    ON experiment_assignment_events(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_experiment_assignment_events_assignment_created
    ON experiment_assignment_events(assignment_id, created_at);

ALTER TABLE next_best_actions ADD COLUMN experiment_id TEXT REFERENCES experiments(id);
ALTER TABLE next_best_actions ADD COLUMN cohort TEXT
    CHECK (cohort IN ('control','variant','observational','excluded'));

ALTER TABLE action_events ADD COLUMN experiment_id TEXT REFERENCES experiments(id);
ALTER TABLE action_events ADD COLUMN cohort TEXT
    CHECK (cohort IN ('control','variant','observational','excluded'));
ALTER TABLE action_events ADD COLUMN ai_trace_id TEXT REFERENCES ai_traces_v2(id);
ALTER TABLE action_events ADD COLUMN latency_ms INTEGER CHECK (latency_ms IS NULL OR latency_ms >= 0);
ALTER TABLE action_events ADD COLUMN success INTEGER NOT NULL DEFAULT 1 CHECK (success IN (0,1));
ALTER TABLE action_events ADD COLUMN error_code TEXT
    CHECK (error_code IS NULL OR length(error_code) <= 100);
ALTER TABLE action_events ADD COLUMN model_version TEXT;
ALTER TABLE action_events ADD COLUMN prompt_version TEXT;

CREATE INDEX IF NOT EXISTS idx_action_events_metrics_window
    ON action_events(owner_user_id, created_at, experiment_id, cohort, event_type);

CREATE TRIGGER IF NOT EXISTS trg_next_best_actions_experiment_context
AFTER INSERT ON next_best_actions
WHEN NEW.experiment_id IS NULL
BEGIN
    UPDATE next_best_actions
    SET experiment_id = (
            SELECT experiment_id FROM experiment_assignments
            WHERE owner_user_id=NEW.owner_user_id AND status='active'
            ORDER BY activated_at DESC, assigned_at DESC LIMIT 1
        ),
        cohort = (
            SELECT cohort FROM experiment_assignments
            WHERE owner_user_id=NEW.owner_user_id AND status='active'
            ORDER BY activated_at DESC, assigned_at DESC LIMIT 1
        )
    WHERE id=NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_action_events_experiment_context
AFTER INSERT ON action_events
BEGIN
    UPDATE action_events
    SET experiment_id = COALESCE(
            NEW.experiment_id,
            (SELECT experiment_id FROM next_best_actions WHERE id=NEW.action_id),
            (SELECT experiment_id FROM experiment_assignments
             WHERE owner_user_id=NEW.owner_user_id AND status='active'
             ORDER BY activated_at DESC, assigned_at DESC LIMIT 1)
        ),
        cohort = COALESCE(
            NEW.cohort,
            (SELECT cohort FROM next_best_actions WHERE id=NEW.action_id),
            (SELECT cohort FROM experiment_assignments
             WHERE owner_user_id=NEW.owner_user_id AND status='active'
             ORDER BY activated_at DESC, assigned_at DESC LIMIT 1)
        ),
        ai_trace_id = COALESCE(
            NEW.ai_trace_id,
            (SELECT ai_trace_id FROM next_best_actions WHERE id=NEW.action_id)
        ),
        model_version = COALESCE(
            NEW.model_version,
            (SELECT model_identifier FROM ai_traces_v2 WHERE id=(
                SELECT ai_trace_id FROM next_best_actions WHERE id=NEW.action_id
            ))
        ),
        prompt_version = COALESCE(
            NEW.prompt_version,
            (SELECT policy_version FROM ai_traces_v2 WHERE id=(
                SELECT ai_trace_id FROM next_best_actions WHERE id=NEW.action_id
            ))
        )
    WHERE id=NEW.id;
END;
