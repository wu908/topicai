-- 001_bootstrap.sql (Spec-007 T005)
-- Establishes the schema_migrations tracking table required by the
-- migration runner. Idempotent: the runner's CREATE TABLE IF NOT EXISTS
-- also creates this on first apply; the SQL file is kept as the
-- canonical source of truth for deployments that bypass the runner.

CREATE TABLE IF NOT EXISTS schema_migrations (
    version    TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL,
    checksum   TEXT NOT NULL
);
