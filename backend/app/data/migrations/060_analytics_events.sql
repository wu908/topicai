-- 060_analytics_events.sql (pilot 5: first-party analytics events)
--
-- One append-only table for the three whitelisted content-list events.
-- Payload keys/values are enforced in app/services/analytics.py (the DB
-- keeps a plain JSON blob so unknown events never widen the schema); the
-- event name itself stays CHECK-constrained. Idempotency is owner-scoped
-- through the unique (owner_user_id, idem_key) index. Retention is written
-- per row as retention_expires_at so GET /analytics/summary can enforce
-- the 90-day window even before the T8 physical cleanup exists.
-- Pure DDL; historical migrations stay immutable.

CREATE TABLE IF NOT EXISTS analytics_events (
    id                   TEXT PRIMARY KEY,
    owner_user_id        TEXT NOT NULL,
    event_name           TEXT NOT NULL CHECK (event_name IN
        ('content_list_view','content_list_project_open','content_list_action_click')),
    payload_json         TEXT NOT NULL DEFAULT '{}',
    client_ts            TEXT NOT NULL,
    server_ts            TEXT NOT NULL,
    retention_expires_at TEXT NOT NULL,
    idem_key             TEXT NOT NULL,
    created_at           TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_analytics_events_owner_idem
    ON analytics_events(owner_user_id, idem_key);
CREATE INDEX IF NOT EXISTS idx_analytics_events_owner_event_created
    ON analytics_events(owner_user_id, event_name, created_at DESC);
