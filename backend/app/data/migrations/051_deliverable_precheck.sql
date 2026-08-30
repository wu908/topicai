-- 051_deliverable_precheck.sql (Spec-013 Phase 1 load-bearing quality gate)
--
-- Structural pre-check result for each deliverable: {"passed":bool,"issues":[]}.
-- Failed pre-checks never become ready (production writes needs_input instead).

ALTER TABLE deliverables ADD COLUMN precheck_json TEXT NOT NULL DEFAULT '{}';
