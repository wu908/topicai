-- Spec-009 Phase 21: complete immutable hypothesis and relative calibration records.

CREATE TABLE IF NOT EXISTS publish_hypothesis_amendments (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    publish_hypothesis_id TEXT NOT NULL,
    amendment_type TEXT NOT NULL CHECK (amendment_type IN (
        'clarification','correction','context','evidence_update'
    )),
    statement TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_by TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (publish_hypothesis_id) REFERENCES publish_hypotheses(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_hypothesis_amendments_owner_idempotency
    ON publish_hypothesis_amendments(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_hypothesis_amendments_hypothesis_created
    ON publish_hypothesis_amendments(publish_hypothesis_id, created_at);

CREATE TRIGGER IF NOT EXISTS trg_publish_hypothesis_locked_fields_immutable
BEFORE UPDATE ON publish_hypotheses
WHEN NEW.owner_user_id IS NOT OLD.owner_user_id
  OR NEW.project_id IS NOT OLD.project_id
  OR NEW.content_version_id IS NOT OLD.content_version_id
  OR NEW.audience_problem IS NOT OLD.audience_problem
  OR NEW.reader_promise IS NOT OLD.reader_promise
  OR NEW.expected_behaviors_json IS NOT OLD.expected_behaviors_json
  OR NEW.basis_refs_json IS NOT OLD.basis_refs_json
  OR NEW.uncertainties_json IS NOT OLD.uncertainties_json
  OR NEW.locked_at IS NOT OLD.locked_at
  OR NEW.locked_by IS NOT OLD.locked_by
BEGIN
    SELECT RAISE(ABORT, 'locked publish hypothesis fields are immutable');
END;

CREATE TABLE IF NOT EXISTS benchmark_samples (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('historical_project','imported_post')),
    source_ref TEXT NOT NULL,
    project_id TEXT,
    publish_record_id TEXT,
    metric_snapshot_ids_json TEXT NOT NULL DEFAULT '[]',
    metrics_json TEXT NOT NULL DEFAULT '{}',
    quality_state TEXT NOT NULL CHECK (quality_state IN ('verified','partial','legacy')),
    inclusion_state TEXT NOT NULL CHECK (inclusion_state IN ('included','excluded')),
    exclusion_reason_code TEXT,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES content_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (publish_record_id) REFERENCES publish_records_v2(id) ON DELETE SET NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_benchmark_samples_owner_idempotency
    ON benchmark_samples(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_benchmark_samples_owner_inclusion
    ON benchmark_samples(owner_user_id, inclusion_state, updated_at DESC);

CREATE TABLE IF NOT EXISTS benchmark_sample_events (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    benchmark_sample_id TEXT NOT NULL,
    from_state TEXT,
    to_state TEXT NOT NULL CHECK (to_state IN ('included','excluded')),
    reason_code TEXT,
    sample_version INTEGER NOT NULL CHECK (sample_version >= 1),
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (benchmark_sample_id) REFERENCES benchmark_samples(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_benchmark_sample_events_owner_idempotency
    ON benchmark_sample_events(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_benchmark_sample_events_sample_created
    ON benchmark_sample_events(benchmark_sample_id, created_at);

ALTER TABLE blind_reviews
    ADD COLUMN eligibility_reason_code TEXT NOT NULL DEFAULT 'insufficient_metrics'
    CHECK (eligibility_reason_code IN (
        'eligible_clean','insufficient_metrics','contaminated_input',
        'revoked_evidence','legacy_hypothesis'
    ));

ALTER TABLE blind_reviews
    ADD COLUMN benchmark_sample_ids_json TEXT NOT NULL DEFAULT '[]';

UPDATE blind_reviews
SET eligibility_reason_code = CASE
    WHEN eligible_for_rule_upgrade = 1
        AND calibration_state = 'valid'
        AND contamination_status = 'clean' THEN 'eligible_clean'
    WHEN contamination_status <> 'clean' THEN 'contaminated_input'
    ELSE 'insufficient_metrics'
END;
