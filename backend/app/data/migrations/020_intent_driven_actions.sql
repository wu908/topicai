-- Intent-driven orchestration. Existing publish/calibration tables remain the
-- execution layer; these additive fields and records decide what should happen next.

ALTER TABLE content_projects ADD COLUMN content_intent TEXT NOT NULL DEFAULT 'solve'
    CHECK (content_intent IN ('solve','share','record'));
ALTER TABLE content_projects ADD COLUMN content_format TEXT NOT NULL DEFAULT 'graphic_note'
    CHECK (content_format IN ('graphic_note','vlog_plan'));
ALTER TABLE content_projects ADD COLUMN intent_status TEXT NOT NULL DEFAULT 'legacy_missing'
    CHECK (intent_status IN ('candidate','confirmed','legacy_missing'));
ALTER TABLE content_projects ADD COLUMN audience_change TEXT;
ALTER TABLE content_projects ADD COLUMN material_requirements_json TEXT NOT NULL DEFAULT '[]';
ALTER TABLE content_projects ADD COLUMN expected_responses_json TEXT NOT NULL DEFAULT '[]';
ALTER TABLE content_projects ADD COLUMN success_signals_json TEXT NOT NULL DEFAULT '[]';
ALTER TABLE content_projects ADD COLUMN automation_level TEXT NOT NULL DEFAULT 'guided'
    CHECK (automation_level IN ('guided','autopilot_to_ready'));
ALTER TABLE content_projects ADD COLUMN creator_state_version INTEGER NOT NULL DEFAULT 1
    CHECK (creator_state_version >= 1);

CREATE TABLE IF NOT EXISTS creator_states (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL UNIQUE,
    facts_json TEXT NOT NULL DEFAULT '[]',
    inferences_json TEXT NOT NULL DEFAULT '[]',
    validated_insights_json TEXT NOT NULL DEFAULT '[]',
    unknowns_json TEXT NOT NULL DEFAULT '[]',
    contradictions_json TEXT NOT NULL DEFAULT '[]',
    intent_preferences_json TEXT NOT NULL DEFAULT '{}',
    current_goal TEXT NOT NULL DEFAULT 'stable_publish',
    available_minutes INTEGER,
    automation_trust_level TEXT NOT NULL DEFAULT 'guided'
        CHECK (automation_trust_level IN ('guided','eligible','autopilot_to_ready')),
    completed_project_count INTEGER NOT NULL DEFAULT 0 CHECK (completed_project_count >= 0),
    candidate_acceptance_rate REAL NOT NULL DEFAULT 0
        CHECK (candidate_acceptance_rate >= 0 AND candidate_acceptance_rate <= 1),
    unresolved_correction_count INTEGER NOT NULL DEFAULT 0
        CHECK (unresolved_correction_count >= 0),
    autopilot_consent INTEGER NOT NULL DEFAULT 0 CHECK (autopilot_consent IN (0,1)),
    source_refs_json TEXT NOT NULL DEFAULT '[]',
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS next_best_actions (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    project_id TEXT,
    action_type TEXT NOT NULL CHECK (action_type IN (
        'create_project','confirm_intent','answer_key_question','review_candidate',
        'confirm_publish_scope','record_publication','add_performance',
        'review_result','confirm_learning','manage_learning'
    )),
    content_intent TEXT CHECK (content_intent IN ('solve','share','record')),
    title TEXT NOT NULL,
    reason TEXT NOT NULL,
    evidence_refs_json TEXT NOT NULL DEFAULT '[]',
    unknown_refs_json TEXT NOT NULL DEFAULT '[]',
    expected_state_change_json TEXT NOT NULL DEFAULT '{}',
    estimated_effort_minutes INTEGER NOT NULL CHECK (estimated_effort_minutes >= 0),
    automation_level TEXT NOT NULL DEFAULT 'guided'
        CHECK (automation_level IN ('guided','autopilot_to_ready')),
    human_gate_type TEXT CHECK (human_gate_type IN (
        'intent','user_fact','content_version','public_scope','publication','long_term_learning'
    )),
    fallback_action_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'proposed'
        CHECK (status IN ('proposed','accepted','deferred','completed','superseded')),
    ai_trace_id TEXT,
    expires_at TEXT,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES content_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (ai_trace_id) REFERENCES ai_traces_v2(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_next_best_actions_owner_idempotency
    ON next_best_actions(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_next_best_actions_owner_status
    ON next_best_actions(owner_user_id, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_next_best_actions_project_status
    ON next_best_actions(project_id, status, updated_at DESC);

CREATE TABLE IF NOT EXISTS human_gates (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    action_id TEXT NOT NULL,
    gate_type TEXT NOT NULL CHECK (gate_type IN (
        'intent','user_fact','content_version','public_scope','publication','long_term_learning'
    )),
    prompt TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','confirmed','rejected')),
    decision_payload_json TEXT,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    decided_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES content_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (action_id) REFERENCES next_best_actions(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_human_gates_owner_idempotency
    ON human_gates(owner_user_id, idempotency_key);
CREATE UNIQUE INDEX IF NOT EXISTS uq_human_gates_action_type
    ON human_gates(action_id, gate_type);

CREATE TABLE IF NOT EXISTS action_events (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    action_id TEXT NOT NULL,
    project_id TEXT,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'proposed','accepted','deferred','manual_selected','completed','superseded',
        'gate_confirmed','gate_rejected','fallback_used'
    )),
    from_status TEXT,
    to_status TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    action_version INTEGER NOT NULL CHECK (action_version >= 1),
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (action_id) REFERENCES next_best_actions(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES content_projects(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_action_events_owner_idempotency
    ON action_events(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_action_events_action_created
    ON action_events(action_id, created_at);
