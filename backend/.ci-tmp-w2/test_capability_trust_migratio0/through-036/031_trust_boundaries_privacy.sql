-- Account-level privacy/deletion gates and publication-gate provenance.
-- human_gates has no inbound foreign keys, so SQLite can rebuild it safely
-- while preserving every existing project gate.

ALTER TABLE human_gates RENAME TO human_gates_before_privacy;

CREATE TABLE human_gates (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    project_id TEXT,
    action_id TEXT,
    gate_type TEXT NOT NULL CHECK (gate_type IN (
        'intent','user_fact','content_version','public_scope','publication',
        'long_term_learning','privacy','deletion'
    )),
    prompt TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','confirmed','rejected')),
    decision_payload_json TEXT,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    decision_idempotency_key TEXT,
    decision_request_hash TEXT,
    decided_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (
        (gate_type IN ('privacy','deletion') AND project_id IS NULL AND action_id IS NULL)
        OR
        (gate_type NOT IN ('privacy','deletion') AND project_id IS NOT NULL AND action_id IS NOT NULL)
    ),
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES content_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (action_id) REFERENCES next_best_actions(id) ON DELETE CASCADE
);

INSERT INTO human_gates (
    id,owner_user_id,project_id,action_id,gate_type,prompt,payload_json,status,
    decision_payload_json,version,idempotency_key,request_hash,decided_at,created_at,updated_at
)
SELECT
    id,owner_user_id,project_id,action_id,gate_type,prompt,payload_json,status,
    decision_payload_json,version,idempotency_key,request_hash,decided_at,created_at,updated_at
FROM human_gates_before_privacy;

DROP TABLE human_gates_before_privacy;

CREATE UNIQUE INDEX uq_human_gates_owner_idempotency
    ON human_gates(owner_user_id, idempotency_key);
CREATE UNIQUE INDEX uq_human_gates_action_type
    ON human_gates(action_id, gate_type);
CREATE UNIQUE INDEX uq_human_gates_owner_decision_idempotency
    ON human_gates(owner_user_id, decision_idempotency_key)
    WHERE decision_idempotency_key IS NOT NULL;

ALTER TABLE publish_records_v2 ADD COLUMN publication_gate_id TEXT;
ALTER TABLE publish_records_v2 ADD COLUMN ai_trace_id TEXT;
