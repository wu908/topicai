-- 049_release_audit_batch3.sql (full-repo audit be776634, batch 3)
--
-- Migration 033 created the publish_hypotheses immutability trigger without
-- a lock-state guard, so it aborts EVERY UPDATE touching the guarded
-- columns — including legitimate edits of rows that are still 'draft'.
-- Historical migrations stay immutable (their checksums are recorded), so
-- the trigger is rebuilt here with the guard: only mutation of rows that
-- are actually locked is rejected. Status transitions (superseding a locked
-- hypothesis) never touch guarded columns and remain allowed.

DROP TRIGGER IF EXISTS trg_publish_hypothesis_locked_fields_immutable;

CREATE TRIGGER trg_publish_hypothesis_locked_fields_immutable
BEFORE UPDATE ON publish_hypotheses
WHEN OLD.status = 'locked' AND (
     NEW.owner_user_id IS NOT OLD.owner_user_id
  OR NEW.project_id IS NOT OLD.project_id
  OR NEW.content_version_id IS NOT OLD.content_version_id
  OR NEW.audience_problem IS NOT OLD.audience_problem
  OR NEW.reader_promise IS NOT OLD.reader_promise
  OR NEW.expected_behaviors_json IS NOT OLD.expected_behaviors_json
  OR NEW.basis_refs_json IS NOT OLD.basis_refs_json
  OR NEW.uncertainties_json IS NOT OLD.uncertainties_json
  OR NEW.locked_at IS NOT OLD.locked_at
  OR NEW.locked_by IS NOT OLD.locked_by
)
BEGIN
    SELECT RAISE(ABORT, 'locked publish hypothesis fields are immutable');
END;
