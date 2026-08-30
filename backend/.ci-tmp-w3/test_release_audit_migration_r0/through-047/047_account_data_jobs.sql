-- Persist the minimum audit state for owner export and deletion operations.
CREATE TABLE IF NOT EXISTS account_data_jobs (
    id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL,
    gate_id TEXT NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN ('data_export','account_deletion')),
    status TEXT NOT NULL CHECK (status IN ('running','completed','failed')),
    created_at TEXT NOT NULL,
    completed_at TEXT,
    UNIQUE(subject_id, gate_id, operation)
);

CREATE INDEX IF NOT EXISTS idx_account_data_jobs_subject_created
    ON account_data_jobs(subject_id, created_at DESC);
