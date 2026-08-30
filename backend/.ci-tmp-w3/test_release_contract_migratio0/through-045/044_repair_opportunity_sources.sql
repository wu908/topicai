-- Backfill source_trigger, source_refs_json, and dimensions_json for rows
-- left with hard-coded placeholder values by the original
-- 043_first_party_opportunities migration (before the runner-marker fix in
-- commit 08f289c).  The original INSERT SELECT unconditionally wrote
-- 'system', '[]', and '{}'; this repair applies the same derivation logic
-- that the corrected 043 markers now use.
--
-- WHERE conditions target only the exact placeholder values, so the UPDATE
-- is a safe no-op on fresh databases and on rows that were already migrated
-- correctly by the patched 043.

-- Repair source_trigger: only user_source rows should ever have a value
-- other than 'system', so we limit the WHERE to that opportunity_type.
UPDATE content_opportunities
SET source_trigger = CASE
        WHEN opportunity_type = 'user_source'
             AND NULLIF(TRIM(source_url), '') IS NOT NULL THEN 'user_url'
        WHEN opportunity_type = 'user_source'
             AND NULLIF(TRIM(source_authority), '') IS NOT NULL THEN 'official_inspiration'
        WHEN opportunity_type = 'user_source' THEN 'user_keyword'
        ELSE 'system'
    END
WHERE source_trigger = 'system'
  AND opportunity_type = 'user_source';

-- Repair source_refs_json: derive one structured ref from the columns that
-- the original migration already copied into the new table.
UPDATE content_opportunities
SET source_refs_json = json_array(json_object(
    'ref_type', CASE
        WHEN opportunity_type = 'series_extension' THEN 'creator_series'
        WHEN NULLIF(TRIM(source_url), '') IS NOT NULL THEN 'user_url'
        WHEN NULLIF(TRIM(source_authority), '') IS NOT NULL THEN 'official_inspiration'
        ELSE 'user_keyword'
    END,
    'entity_id', CASE
        WHEN opportunity_type = 'series_extension' AND INSTR(source_ref, ':') > 0
            THEN SUBSTR(source_ref, INSTR(source_ref, ':') + 1)
        ELSE id
    END,
    'url',            source_url,
    'publisher',      source_authority,
    'published_at',   source_published_at,
    'collected_at',   created_at,
    'title',          proposed_title,
    'excerpt',        source_excerpt,
    'verification_state', CASE
        WHEN verification_status = 'pending_verification' THEN 'pending'
        ELSE verification_status
    END,
    'rights_note', '迁移自既有内容机会来源'
))
WHERE source_refs_json = '[]';

-- Repair dimensions_json: apply the same initial-upgrade defaults that the
-- corrected 043 marker expression generates.
UPDATE content_opportunities
SET dimensions_json = json_object(
    'audience_fit',       'unknown',
    'creator_fit',        'unknown',
    'material_readiness', 'partial',
    'growth_role',        'experiment',
    'series_potential',   'unknown',
    'timeliness',         'unknown',
    'similarity_risk',    'unknown',
    'safety_risk',        'unknown'
)
WHERE dimensions_json = '{}';
