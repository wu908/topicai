-- The fresh-schema status constraints live in migration 020. Existing SQLite
-- databases are rebuilt by the matching migration-runner post-step because
-- SQLite cannot alter CHECK constraints in place.
SELECT 1;
