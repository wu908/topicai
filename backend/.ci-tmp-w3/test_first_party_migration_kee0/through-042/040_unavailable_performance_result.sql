ALTER TABLE performance_snapshots_v2
    ADD COLUMN result_availability TEXT NOT NULL DEFAULT 'observed'
    CHECK (result_availability IN ('observed','unavailable'));

ALTER TABLE performance_snapshots_v2
    ADD COLUMN unavailable_reason TEXT;
