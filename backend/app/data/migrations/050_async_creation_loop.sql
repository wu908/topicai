-- 050_async_creation_loop.sql (Spec-013 Phase 1 walking skeleton)
--
-- Four additive tables for the async creation loop: creative inbox,
-- deliverables (the shelf), production event log, and loop metrics.
-- Pure DDL; no business logic. Historical migrations stay immutable;
-- idempotency/versioning discipline matches the existing v2 tables.

CREATE TABLE IF NOT EXISTS inbox_items (
    id               TEXT PRIMARY KEY,
    owner_user_id    TEXT NOT NULL,
    kind             TEXT NOT NULL CHECK (kind IN ('text','image','voice','link','idea')),
    title            TEXT NOT NULL DEFAULT '',
    content          TEXT NOT NULL DEFAULT '',
    consent          TEXT NOT NULL DEFAULT 'publishable' CHECK (consent IN ('publishable','private')),
    status           TEXT NOT NULL DEFAULT 'intake' CHECK (status IN ('intake','digested','failed')),
    version          INTEGER NOT NULL DEFAULT 1,
    idempotency_key  TEXT NOT NULL,
    request_hash     TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_inbox_items_owner_idem
    ON inbox_items(owner_user_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_inbox_items_owner_created
    ON inbox_items(owner_user_id, created_at DESC, id);

CREATE TABLE IF NOT EXISTS deliverables (
    id                   TEXT PRIMARY KEY,
    owner_user_id        TEXT NOT NULL,
    thread_id            TEXT NOT NULL,
    title                TEXT NOT NULL,
    body_text            TEXT NOT NULL DEFAULT '',
    outline_json         TEXT NOT NULL DEFAULT '[]',
    facts_json           TEXT NOT NULL DEFAULT '[]',
    judgment_json        TEXT NOT NULL DEFAULT '{}',
    content_intent       TEXT CHECK (content_intent IS NULL OR content_intent IN ('solve','share','record')),
    proposed_publish_at  TEXT,
    is_exploration       INTEGER NOT NULL DEFAULT 0 CHECK (is_exploration IN (0,1)),
    status               TEXT NOT NULL DEFAULT 'queued'
                         CHECK (status IN ('queued','producing','ready','failed','expired','picked','discarded')),
    failure_reason       TEXT,
    retry_count          INTEGER NOT NULL DEFAULT 0,
    expire_at            TEXT,
    picked_project_id    TEXT,
    pickup_idem          TEXT,
    attribution          TEXT,
    confidence           TEXT NOT NULL DEFAULT 'medium',
    version              INTEGER NOT NULL DEFAULT 1,
    idempotency_key      TEXT NOT NULL,
    request_hash         TEXT NOT NULL DEFAULT '',
    created_at           TEXT NOT NULL,
    updated_at           TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_deliverables_owner_status
    ON deliverables(owner_user_id, status, created_at DESC, id);

CREATE TABLE IF NOT EXISTS production_events (
    id             TEXT PRIMARY KEY,
    owner_user_id  TEXT NOT NULL,
    thread_id      TEXT NOT NULL,
    deliverable_id TEXT,
    event_type     TEXT NOT NULL CHECK (event_type IN
                   ('queued','producing','ready','failed','retry','expired','needs_input','picked','discarded')),
    detail_json    TEXT NOT NULL DEFAULT '{}',
    created_at     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_production_events_thread
    ON production_events(thread_id, created_at, id);

CREATE TABLE IF NOT EXISTS loop_metrics (
    id             TEXT PRIMARY KEY,
    owner_user_id  TEXT NOT NULL,
    metric         TEXT NOT NULL CHECK (metric IN
                   ('pickup_seconds','weekly_minutes','published_count','discard_attribution')),
    value          REAL NOT NULL DEFAULT 0,
    meta_json      TEXT NOT NULL DEFAULT '{}',
    created_at     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_loop_metrics_owner_metric
    ON loop_metrics(owner_user_id, metric, created_at DESC, id);
