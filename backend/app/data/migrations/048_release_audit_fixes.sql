-- Additive columns are guarded by the migration runner for partial-DDL recovery.

CREATE UNIQUE INDEX IF NOT EXISTS idx_snapshot_extractions_snapshot
    ON snapshot_extractions_v2(snapshot_id)
    WHERE snapshot_id IS NOT NULL;

UPDATE materials SET kind='document'
WHERE kind IN ('audio','video','template');
