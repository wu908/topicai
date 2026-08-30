-- 008_creator_profiles_reconcile.sql (Spec-007 T301-T305)
--
-- Reconcile legacy ``creator_profiles`` tables that predate the
-- ``CHECK (recommendation_mode IN ('hotspot_fusion','evergreen_deep'))``
-- constraint. Migration 005 adds the CHECK on fresh DBs only
-- (``CREATE TABLE IF NOT EXISTS`` is a no-op on an existing table), so
-- any prod DB created before 005 ships with a CHECK-less
-- ``recommendation_mode`` column — a buggy write can land any string.
--
-- SQLite has no ``ALTER TABLE ADD CONSTRAINT`` (and no
-- ``ADD COLUMN IF NOT EXISTS``), so the only path to attach a CHECK to
-- an existing table is the 12-step rebuild:
--
--   1. CREATE TABLE creator_profiles_new (full authoritative shape, with
--      the CHECK the legacy table lacks).
--   2. INSERT INTO creator_profiles_new (...) SELECT ... FROM creator_profiles
--      (copy every row, every column — no data loss).
--   3. DROP TABLE creator_profiles.
--   4. ALTER TABLE creator_profiles_new RENAME TO creator_profiles.
--   5. CREATE INDEX IF NOT EXISTS idx_creator_profiles_user_id ...
--
-- Safety properties (verified in
-- ``tests/data/test_schema_single_source_of_truth.py::TestCreatorProfilesReconcile``):
--
--   * Column order matches 000_initial_schema.sql:51-63 and
--     005_creator_profiles.sql:4-16 byte-for-byte. Each column is
--     enumerated explicitly in both the CREATE and the INSERT-SELECT to
--     guard against column-order drift in either the source or target
--     table (a future ALTER on the legacy table would not silently
--     re-shape the column list).
--   * ``rubric_weights`` is included in BOTH the CREATE and the
--     SELECT — omitting it would silently lose the personalization data
--     every existing row carries.
--   * ``creator_profiles`` has no inbound FK (no other table references
--     ``creator_profiles.id`` / ``creator_profiles.user_id``) and the
--     column-level ``user_id`` is not declared as a FK in 000/005, so
--     ``DROP TABLE`` is safe under ``PRAGMA foreign_keys=ON`` (the
--     runner's connection sets this — see runner.py:208). The
--     ``PRAGMA foreign_keys=OFF`` switch inside ``executescript`` is a
--     no-op in SQLite, so we do not try to toggle it.
--   * Fresh-DB safety: when 000 has already created ``creator_profiles``
--     WITH the CHECK, this migration rebuilds it as a same-shape
--     drop-and-rename. All existing rows are valid, so the
--     INSERT-SELECT succeeds, and ``CREATE INDEX IF NOT EXISTS`` is a
--     no-op because the index already exists on the new (renamed) table.
--     Net effect: zero observable change on a fresh DB.
--   * Idempotency: the runner's schema_migrations version check prevents
--     re-application on a DB that has already recorded 008.

CREATE TABLE creator_profiles_new (
    id                    TEXT PRIMARY KEY,
    user_id               TEXT NOT NULL UNIQUE,
    track                 TEXT NOT NULL,
    content_formats       TEXT NOT NULL,
    production_complexity TEXT NOT NULL,
    content_depth         TEXT NOT NULL,
    hotspot_preference    TEXT NOT NULL,
    recommendation_mode   TEXT NOT NULL CHECK (recommendation_mode IN ('hotspot_fusion','evergreen_deep')),
    rubric_weights        TEXT NOT NULL DEFAULT '{}',
    created_at            TEXT NOT NULL,
    updated_at            TEXT NOT NULL DEFAULT ''
);

INSERT INTO creator_profiles_new (
    id, user_id, track, content_formats, production_complexity,
    content_depth, hotspot_preference, recommendation_mode,
    rubric_weights, created_at, updated_at
)
SELECT
    id, user_id, track, content_formats, production_complexity,
    content_depth, hotspot_preference, recommendation_mode,
    rubric_weights, created_at, updated_at
FROM creator_profiles;

DROP TABLE creator_profiles;

ALTER TABLE creator_profiles_new RENAME TO creator_profiles;

CREATE INDEX IF NOT EXISTS idx_creator_profiles_user_id ON creator_profiles(user_id);
