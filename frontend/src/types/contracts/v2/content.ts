export type ProjectStatus =
  | 'inbox'
  | 'preparing'
  | 'creating'
  | 'ready_to_publish'
  | 'published'
  | 'awaiting_review'
  | 'settled';

export type ContentIntent = 'solve' | 'share' | 'record';
export type ContentFormat = 'graphic_note' | 'vlog_plan';
export type AutomationLevel = 'guided' | 'autopilot_to_ready';
export type IntentStatus =
  | 'candidate'
  | 'working_confirmed'
  | 'locked'
  | 'legacy_unclassified'
  | 'retrospective';
export type ExpectedBehavior = 'save' | 'comment' | 'profile_visit' | 'follow' | 'other';
export type EvidenceSourceType = 'user_fact' | 'external_fact' | 'ai_inference' | 'validated_insight';
export type EvidenceConfirmationStatus = 'proposed' | 'confirmed' | 'rejected' | 'revoked';
export type EvidencePrivacyLevel = 'public' | 'private' | 'sensitive';

export type IntentActionType =
  | 'create_project'
  | 'confirm_intent'
  | 'lock_intent'
  | 'answer_key_question'
  | 'review_candidate'
  | 'confirm_publish_scope'
  | 'record_publication'
  | 'add_performance'
  | 'review_result'
  | 'confirm_learning'
  | 'manage_learning'
  | 'await_observation_window'
  | 'scope_learning';

export interface HumanGate {
  id: string;
  gate_type: 'intent' | 'user_fact' | 'content_version' | 'public_scope' | 'publication' | 'long_term_learning' | 'privacy' | 'deletion';
  prompt: string;
  payload: Record<string, unknown>;
  status: 'pending' | 'confirmed' | 'rejected';
  version: number;
}

export interface Evidence {
  id: string;
  project_id: string;
  source_type: EvidenceSourceType;
  statement: string;
  source_ref: string;
  content_ref: string | null;
  privacy_level: EvidencePrivacyLevel;
  confirmation_status: EvidenceConfirmationStatus;
  reusable: boolean;
  version: number;
  created_at: string;
  updated_at: string;
  revoked_at: string | null;
  invalidation?: {
    content_version_ids: string[];
    affected_segments: Array<{
      id: string;
      segment_key: string;
      content_version_id: string;
    }>;
    publication_lock_blocked: boolean;
    required_action: 'replace_evidence_or_answer_key_question';
  };
}

export interface IntentAction {
  id: string;
  project_id: string | null;
  action_type: IntentActionType;
  content_intent: ContentIntent | null;
  title: string;
  reason: string;
  evidence_refs: string[];
  unknown_refs: string[];
  expected_state_change: Record<string, unknown>;
  estimated_effort_minutes: number;
  automation_level: AutomationLevel;
  human_gate_type: HumanGate['gate_type'] | null;
  human_gate: HumanGate | null;
  fallback_action: {
    action_type: string;
    path?: string;
    title?: string;
    mode?: 'generic_structure';
    limitations?: string[];
  };
  status: 'proposed' | 'accepted' | 'deferred' | 'completed' | 'superseded' | 'failed' | 'expired' | 'cancelled';
  version: number;
  expires_at: string | null;
  last_event: {
    event_type: string;
    payload: { reason?: string; error_code?: string | null };
    created_at: string;
  } | null;
}

export type NextAction =
  | 'create_version'
  | 'lock_hypothesis'
  | 'record_publication'
  | 'await_observation_window'
  | 'add_snapshot'
  | 'run_blind_review'
  | 'create_observation'
  | 'manage_observations'
  | 'add_comparable_snapshot'
  | 'review_calibration_issue';

export interface ContentProject {
  id: string;
  title: string;
  status: ProjectStatus;
  primary_goal: 'stable_publish' | 'follower_growth' | 'experiment';
  target_audience: string;
  /**
   * Null while the project is legacy_unclassified or retrospective — ADR 0002
   * keeps the Publication Intent unset for historical content. Read
   * retrospective_intent for the user-confirmed classification instead.
   */
  content_intent: ContentIntent | null;
  /** Set only by retrospective classification; never changes content_intent. */
  retrospective_intent: ContentIntent | null;
  content_format: ContentFormat;
  intent_status: IntentStatus;
  audience_change: string | null;
  material_requirements: string[];
  expected_responses: string[];
  success_signals: string[];
  automation_level: AutomationLevel;
  creator_state_version: number;
  starter_sprint_id?: string | null;
  current_version_id: string | null;
  locked_publish_version_id: string | null;
  publish_hypothesis_id: string | null;
  calibration_state: 'not_ready' | 'insufficient' | 'valid' | 'calibration_invalid';
  version: number;
  updated_at: string;
  next_action?: NextAction;
  orchestrated_action?: IntentAction;
}

export interface ContentVersion {
  id: string;
  title: string;
  body_text: string;
  cover_plan: string;
  image_plan: Array<Record<string, unknown>>;
  version_number: number;
}

export interface CandidateSegmentDecision {
  id: string;
  segment_id: string;
  decision: 'accepted' | 'rejected' | 'replaced';
  replacement_text: string | null;
  reason: string | null;
  version: number;
  created_at: string;
}

export interface CandidateSegment {
  id: string;
  segment_key: string;
  ordinal: number;
  segment_type: 'title' | 'body';
  text: string;
  source_refs: string[];
  decision: CandidateSegmentDecision | null;
}

export interface CandidateComparison {
  segment_key: string;
  segment_type: 'title' | 'body';
  base_text: string | null;
  current_text: string;
  changed: boolean;
}

export interface CandidateReview {
  project_id: string;
  content_version_id: string;
  version: ContentVersion & Record<string, unknown>;
  parent_version: (ContentVersion & Record<string, unknown>) | null;
  segments: CandidateSegment[];
  comparison: CandidateComparison[];
  blocked_reasons: string[];
  all_segments_decided: boolean;
  can_prepare_revision: boolean;
  can_lock: boolean;
}

export interface PublishHypothesis {
  id: string;
  content_intent: ContentIntent | null;
  audience_change: string | null;
  primary_response: ExpectedBehavior | null;
  supporting_responses: ExpectedBehavior[];
  audience_problem: string;
  reader_promise: string;
  viewpoint_anchor: string | null;
  continuation_promise: string | null;
  expected_behaviors: ExpectedBehavior[];
  basis_refs: string[];
  uncertainties: string[];
  observation_window_days: number | null;
  status: 'locked' | 'draft' | 'superseded' | 'legacy_missing';
}

export interface PublishRecord {
  id: string;
  note_url?: string | null;
  published_at: string;
}

export interface PerformanceMetrics {
  views?: number | null;
  likes?: number | null;
  favorites?: number | null;
  comments?: number | null;
  shares?: number | null;
  follows_gained?: number | null;
}

export interface PerformanceSnapshot {
  id: string;
  captured_at: string;
  result_availability: 'observed' | 'unavailable';
  unavailable_reason?: string | null;
  metrics: PerformanceMetrics;
  supersedes_id?: string | null;
}

export interface MaterialUsage {
  id: string;
  project_id: string;
  project_title: string;
  used_at: string;
}

export interface Material {
  id: string;
  title: string;
  kind: 'text' | 'link' | 'image' | 'document';
  mime_type: string;
  size: number;
  content?: string | null;
  privacy_level: 'public' | 'private' | 'sensitive';
  version: number;
  usages: MaterialUsage[];
  created_at: string;
  updated_at: string;
}

export interface PublishCheckFinding {
  id: string;
  field: 'title' | 'body_text' | 'cover_plan';
  start: number;
  end: number;
  excerpt: string;
  reason: string;
  severity: 'low' | 'medium' | 'high';
  rule_source: string;
  rule_updated_at: string;
  status: 'open' | 'acknowledged' | 'resolved';
}

export interface PublishCheck {
  id: string;
  content_version_id: string;
  status: 'clear' | 'needs_attention' | 'stale';
  stale: boolean;
  findings: PublishCheckFinding[];
  limitations: string[];
  checked_at: string;
}

export interface SnapshotExtractionProposal {
  id: string;
  material_id: string | null;
  metrics: PerformanceMetrics;
  confirmed_by_user: boolean;
  user_decision: 'pending' | 'confirmed' | 'rejected' | 'edited';
  decided_at: string | null;
  snapshot_id: string | null;
  ai_trace: {
    capability: 'vision';
    confidence_label: 'high' | 'medium' | 'low' | 'unavailable';
    limitations: string[];
    outcome: 'success' | 'fallback' | 'failed' | 'cancelled';
  };
}

export interface UserSettings {
  weekly_publish_goal: number;
  timezone: string;
  content_strategy: string;
  xiaohongshu_account_reference: string | null;
  consent: Record<string, unknown>;
  version: number;
  ai: {
    enabled: boolean;
    configured: boolean;
    model_identifier: string | null;
    capabilities: string[];
    vision_enabled: boolean;
  };
}

export interface AccountDataJob {
  id: string;
  operation: 'data_export' | 'account_deletion';
  status: 'running' | 'completed' | 'failed';
  created_at: string;
  completed_at: string | null;
}

export interface OwnerDataExport {
  job: AccountDataJob;
  generated_at: string;
  owner: Record<string, unknown>;
  entities: Record<string, Array<Record<string, unknown>>>;
  content_genomes: Array<Record<string, unknown>>;
  stored_files: Array<{
    material_id: string;
    title: string;
    mime_type: string;
    size: number;
    status: 'exported' | 'missing';
    content_base64: string | null;
  }>;
}

export interface BlindReview {
  id: string;
  calibration_state: 'valid' | 'insufficient' | 'calibration_invalid';
  contamination_status: 'clean' | 'suspected' | 'contaminated';
  eligible_for_rule_upgrade: boolean;
  comparison: {
    expected_behavior_comparisons: Array<{
      claim: string;
      metric: string | null;
      observed_values: number[];
      assessment: 'supported' | 'contradicted' | 'unknown';
      reason: string;
      }>; 
    intent_review?: IntentReviewPlan;
  };
}

export interface IntentReviewFact {
  claim: string;
  metric: string | null;
  observed_values: number[];
  assessment: 'supported' | 'contradicted' | 'unknown';
  status: 'observed' | 'unknown';
}

export interface IntentReviewPlan {
  intent: ContentIntent;
  intent_label: string;
  sample_count: number;
  observed_facts: IntentReviewFact[];
  possible_causes: string[];
  continue_item: string;
  stop_item: string;
  experiment_item: string;
  confirmation_required: boolean;
  long_term_write_allowed: boolean;
  intent_outcome?: 'supported' | 'contradicted' | 'unknown';
  result_availability?: 'observed' | 'unavailable';
  follow_up_options?: Array<{
    action: 'collect_more_evidence' | 'repeat_observation' | 'run_bounded_experiment';
    label: string;
    statement: string;
    next_test: string;
  }>;
}

export interface CreatorRuleVersion {
  id: string;
  rule_id: string;
  version_number: number;
  statement: string;
  scope: Record<string, unknown>;
  source_observation_ids: string[];
  status: 'proposed' | 'active' | 'retired' | 'rejected';
  previous_version_id: string | null;
  created_at: string;
  confirmed_at: string | null;
  conflicts?: CreatorRuleConflict[];
}

export interface CreatorRuleConflict {
  rule_id: string;
  rule_key: string;
  content_intent: ContentIntent;
  active_version_id: string;
  rule_version: number;
  statement: string;
  applicability: {
    intent: string;
    experiment: string;
    audience: string;
    format: string;
  };
  reason: 'same_intent_and_overlapping_applicability';
  status: 'open' | 'acknowledged';
  resolution: CreatorRuleResolution | null;
}

export interface CreatorRuleResolution {
  id: string;
  rule_id: string;
  conflict_rule_id: string;
  resolution_type: 'narrow_scope' | 'keep_exception' | 'deactivate';
  scope: Record<string, unknown>;
  status: 'applied' | 'superseded';
  created_at: string;
}

export interface CreatorRule {
  id: string;
  rule_key: string;
  content_intent: ContentIntent;
  active_version_id: string | null;
  version: number;
  versions: CreatorRuleVersion[];
  active_version?: CreatorRuleVersion | null;
  conflicts: CreatorRuleConflict[];
}

export interface CreatorViewpoint {
  id: string;
  project_id: string;
  content_intent: ContentIntent;
  proposed_statement: string;
  proposed_rationale: string;
  confirmed_statement: string | null;
  scope: Record<string, unknown>;
  source_evidence_ids: string[];
  source_content_version_id: string | null;
  privacy_level: 'private' | 'sensitive';
  status: 'proposed' | 'confirmed' | 'rejected' | 'revoked';
  proposal_source: 'ai' | 'deterministic_fallback';
  ai_trace_id: string;
  limitations: string[];
  version: number;
  created_at: string;
  updated_at: string;
  confirmed_at: string | null;
  revoked_at: string | null;
}

export interface CreatorSeries {
  id: string;
  content_intent: ContentIntent | null;
  content_format: ContentFormat | null;
  proposed_name: string;
  proposed_promise: string;
  proposed_rationale: string;
  proposed_continuation_prompt: string;
  confirmed_name: string | null;
  confirmed_promise: string | null;
  confirmed_continuation_prompt: string | null;
  scope: {
    member_intents?: ContentIntent[];
    member_formats?: ContentFormat[];
    content_intent?: ContentIntent | null;
    format?: ContentFormat | null;
    [key: string]: unknown;
  };
  source_project_ids: string[];
  status: 'proposed' | 'confirmed' | 'rejected' | 'revoked';
  proposal_source: 'ai' | 'deterministic_fallback';
  ai_trace_id: string;
  limitations: string[];
  version: number;
  created_at: string;
  updated_at: string;
  confirmed_at: string | null;
  revoked_at: string | null;
}

export interface OpportunitySourceReference {
  ref_type: 'imported_note' | 'material' | 'validated_insight' | 'creator_profile' | 'creator_series' | 'user_keyword' | 'user_url' | 'official_inspiration';
  entity_id: string | null;
  url: string | null;
  publisher: string | null;
  published_at: string | null;
  collected_at: string | null;
  title: string | null;
  excerpt: string | null;
  verification_state: 'verified' | 'pending' | 'insufficient';
  rights_note: string | null;
}

export interface ContentOpportunity {
  id: string;
  opportunity_type: 'series_extension' | 'user_source' | 'history_derivative' | 'user_question' | 'material_derivative' | 'insight_derivative' | 'evergreen';
  source_trigger: 'system' | 'user_keyword' | 'user_url' | 'official_inspiration';
  source_ref: string;
  source_excerpt: string | null;
  source_url: string | null;
  source_published_at: string | null;
  source_authority: string | null;
  source_refs: OpportunitySourceReference[];
  verification_status: 'verified' | 'pending_verification' | 'insufficient';
  expires_at: string | null;
  content_intent: ContentIntent;
  content_format: ContentFormat;
  proposed_title: string;
  proposed_audience_change: string;
  proposed_rationale: string;
  proposed_material_requirements: string[];
  confirmed_title: string | null;
  confirmed_audience_change: string | null;
  confirmed_material_requirements: string[];
  evidence_refs: string[];
  unknown_refs: string[];
  status: 'proposed' | 'saved' | 'accepted' | 'rejected';
  proposal_source: 'ai' | 'deterministic_fallback';
  ai_trace_id: string;
  created_project_id: string | null;
  limitations: string[];
  dimensions: {
    audience_fit: 'strong' | 'medium' | 'weak' | 'unknown';
    creator_fit: 'strong' | 'medium' | 'weak' | 'unknown';
    material_readiness: 'ready' | 'partial' | 'missing';
    growth_role: 'discovery' | 'trust' | 'series' | 'retention' | 'experiment';
    series_potential: 'high' | 'medium' | 'low' | 'unknown';
    timeliness: 'evergreen' | 'current' | 'expiring' | 'expired' | 'unknown';
    similarity_risk: 'high' | 'medium' | 'low' | 'unknown';
    safety_risk: 'high' | 'medium' | 'low' | 'unknown';
  } | null;
  version: number;
  created_at: string;
  updated_at: string;
  decided_at: string | null;
  required_action: {
    action_type: 'verify_source';
    reason: string;
    accepted_inputs: Array<'original_url' | 'published_at' | 'authoritative_source' | 'timeliness'>;
    fallback: 'manual_verification';
  } | {
    action_type: 'source_expired';
    reason: string;
    fallback: 'reverify_source';
  } | null;
  project?: ContentProject;
}

export interface BlindReviewTrace {
  id: string;
  visibility_boundary: {
    allowed: string[];
    forbidden: string[];
    actual: string[];
  };
  source_snapshot_ids: string[];
  contamination_check: {
    status: 'clean' | 'suspected' | 'contaminated';
    unexpected_classes: string[];
    missing_classes: string[];
  };
  limitations: string[];
}

export type ObservationStatus =
  | 'observing'
  | 'pending_validation'
  | 'absorbed'
  | 'refuted'
  | 'archived';

export interface Observation {
  id: string;
  statement: string;
  scope: Record<string, unknown>;
  next_test: string;
  lifecycle_status: ObservationStatus;
  sample_count: number;
  version: number;
}

export type ContentGenomeRuleStatus =
  | 'applicable'
  | 'needs_context'
  | 'needs_review'
  | 'conflicted'
  | 'not_applicable';

export interface ContentGenomeDecisionContext {
  source_ref: string;
  statement: string;
  content_intent: ContentIntent;
  applicability: {
    intent: string;
    experiment: string;
    audience: string;
    format: string;
  };
  evidence_refs: string[];
  source_project_refs: string[];
  sample_count: number;
  reason: 'confirmed_rule_matches_project_context';
}

export interface ContentGenomeEvidenceContext {
  source_ref: string;
  statement: string;
  source_type: EvidenceSourceType;
  privacy_level: EvidencePrivacyLevel;
  project_id: string;
  reusable: boolean;
  reason: 'current_project_confirmed' | 'confirmed_reusable_same_intent';
}

export interface ContentGenomeViewpointContext {
  source_ref: string;
  statement: string;
  rationale: string;
  content_intent: ContentIntent;
  applicability: {
    intent: string;
    experiment: string;
    audience: string;
    format: string;
  };
  evidence_refs: string[];
  project_id: string;
  privacy_level: 'private' | 'sensitive';
  reason: 'user_confirmed_viewpoint_matches_project_context';
}

export interface ContentGenomeSeriesContext {
  source_ref: string;
  name: string;
  promise: string;
  continuation_prompt: string;
  rationale: string;
  /** Null when members disagree; read member_intents for the authoritative set. */
  content_intent: ContentIntent | null;
  content_format: ContentFormat | null;
  member_intents: ContentIntent[];
  member_formats: ContentFormat[];
  applicability: {
    intent: string;
    experiment: string;
    audience: string;
    format: string;
  };
  source_project_refs: string[];
  reason: 'user_confirmed_series_matches_project_context';
}

export interface ContentGenomeInsightContext {
  source_ref: string;
  statement: string;
  project_id: string;
  scope: Record<string, unknown>;
  reason: string;
}

export interface ContentGenome {
  project_id: string | null;
  query: {
    content_intent: string;
    intent_confirmed: boolean;
    audience: string;
    format: string;
    experiment: string;
  };
  fingerprint: string;
  nodes: Array<Record<string, unknown> & {
    id: string;
    node_type: 'creator_rule' | 'observation' | 'validated_insight' | 'evidence' | 'viewpoint' | 'series' | 'content_project';
    status?: ContentGenomeRuleStatus | string;
  }>;
  edges: Array<Record<string, unknown> & {
    id: string;
    edge_type:
      | 'supported_by'
      | 'conflicts_with'
      | 'exception_to'
      | 'derived_from'
      | 'part_of'
      | 'observed_in'
      | 'belongs_to';
  }>;
  decision_context: ContentGenomeDecisionContext[];
  evidence_context: ContentGenomeEvidenceContext[];
  viewpoint_context: ContentGenomeViewpointContext[];
  series_context: ContentGenomeSeriesContext[];
  insight_context: ContentGenomeInsightContext[];
  summary: {
    relevant_rule_count: number;
    applicable_rule_count: number;
    withheld_rule_count: number;
    open_conflict_count: number;
    applicable_evidence_count: number;
    applicable_viewpoint_count: number;
    applicable_series_count: number;
    applicable_insight_count: number;
  };
}

export interface CalibrationWorkspace {
  project: ContentProject;
  current_version: ContentVersion | null;
  publish_hypothesis: PublishHypothesis | null;
  publish_record: PublishRecord | null;
  snapshots: PerformanceSnapshot[];
  latest_snapshot: PerformanceSnapshot | null;
  latest_blind_review: BlindReview | null;
  blind_review_trace: BlindReviewTrace | null;
  observations: Observation[];
  next_action: NextAction;
  orchestrated_action?: IntentAction;
  candidate_review?: CandidateReview | null;
  creator_rules?: CreatorRule[];
  creator_state?: CreatorState;
  content_genome?: ContentGenome;
  creator_viewpoints?: CreatorViewpoint[];
  creator_series?: CreatorSeries[];
  content_opportunities?: ContentOpportunity[];
}

export interface ApiEnvelope<T> {
  code: number;
  data: T;
  message: string;
  meta: {
    idempotency_replayed?: boolean;
    error_code?: string;
    details?: {
      current_version: number;
      expected_version: number;
    };
  };
}

export interface ProjectList {
  items: ContentProject[];
  total: number;
}

export interface ProjectCreateInput {
  title: string;
  primary_goal: ContentProject['primary_goal'];
  target_audience: string;
  content_intent?: ContentIntent;
  content_format?: ContentFormat;
  audience_change?: string;
  idempotency_key: string;
}

export interface CreatorState {
  id: string;
  facts: Array<Record<string, unknown>>;
  inferences: Array<Record<string, unknown>>;
  validated_insights: Array<Record<string, unknown>>;
  unknowns: Array<Record<string, unknown>>;
  contradictions: Array<Record<string, unknown>>;
  current_goal: string;
  available_minutes: number | null;
  automation_trust_level: 'guided' | 'eligible' | 'autopilot_to_ready';
  completed_project_count: number;
  candidate_acceptance_rate: number;
  unresolved_correction_count: number;
  autopilot_consent: boolean;
  /** ADR 0002: accepted-result count per auto-prepare capability. */
  capability_trust: Record<string, number>;
  autopilot_eligible: boolean;
  version: number;
}

export interface TodayWorkspace {
  action: IntentAction;
  creator_state: CreatorState;
}

export interface IntentConfirmationInput {
  content_intent: ContentIntent;
  audience_change: string;
  material_requirements: string[];
  expected_responses: string[];
  success_signals: string[];
  expected_project_version: number;
  idempotency_key: string;
}

/**
 * Retrospective Intent Classification for published historical content.
 * Writes retrospective_intent only; content_intent stays NULL per ADR 0002.
 */
export interface RetrospectiveClassificationInput {
  retrospective_intent: ContentIntent;
  classification_basis: string;
  expected_project_version: number;
  idempotency_key: string;
}

export interface ActionResponseInput {
  decision: 'accept' | 'defer' | 'reject' | 'manual';
  response_payload?: Record<string, unknown>;
  expected_action_version: number;
  idempotency_key: string;
}

export interface ActionLifecycleInput {
  operation: 'fail' | 'expire' | 'cancel';
  reason: string;
  error_code?: string;
  expected_action_version: number;
  idempotency_key: string;
}

export interface HumanGateDecisionInput {
  decision: 'confirm' | 'reject';
  decision_payload?: Record<string, unknown>;
  expected_gate_version: number;
  idempotency_key: string;
}

export interface EvidenceDecisionInput {
  decision: 'confirm' | 'reject';
  expected_evidence_version: number;
  idempotency_key: string;
}

export interface EvidenceRevocationInput {
  expected_evidence_version: number;
  idempotency_key: string;
}

export interface ViewpointCandidateCreateInput {
  source_evidence_ids: string[];
  source_content_version_id?: string;
  expected_project_version: number;
  idempotency_key: string;
}

export interface ViewpointDecisionInput {
  decision: 'confirm' | 'reject';
  confirmed_statement?: string;
  reason?: string;
  expected_viewpoint_version: number;
  idempotency_key: string;
}

export interface ViewpointRevocationInput {
  reason: string;
  expected_viewpoint_version: number;
  idempotency_key: string;
}

export interface SeriesCandidateCreateInput {
  source_project_ids: string[];
  expected_project_versions: Record<string, number>;
  idempotency_key: string;
}

export interface SeriesDecisionInput {
  decision: 'confirm' | 'reject';
  confirmed_name?: string;
  confirmed_promise?: string;
  confirmed_continuation_prompt?: string;
  reason?: string;
  expected_series_version: number;
  idempotency_key: string;
}

export interface SeriesRevocationInput {
  reason: string;
  expected_series_version: number;
  idempotency_key: string;
}

export interface SeriesExtensionCreateInput {
  expected_series_version: number;
  idempotency_key: string;
}

export interface OpportunityDecisionInput {
  decision: 'accept' | 'save' | 'reject';
  confirmed_title?: string;
  confirmed_audience_change?: string;
  confirmed_material_requirements?: string[];
  /** Spec-011: override the AI-proposed intent/format when accepting a series_extension. */
  confirmed_content_intent?: ContentIntent;
  confirmed_content_format?: ContentFormat;
  reason?: string;
  expected_opportunity_version: number;
  idempotency_key: string;
}

export interface ManualOpportunityCreateInput {
  trigger: 'user_keyword' | 'user_url' | 'official_inspiration';
  pasted_text: string;
  original_url?: string;
  published_at?: string;
  authoritative_source?: string;
  expires_at?: string;
  content_intent?: ContentIntent;
  idempotency_key: string;
}

export interface OpportunitySourceVerificationInput {
  verification_status: 'verified' | 'insufficient';
  original_url?: string;
  published_at?: string;
  authoritative_source?: string;
  timeliness?: 'current' | 'expiring' | 'expired';
  reason?: string;
  confirmed_by_user: true;
  expected_opportunity_version: number;
  idempotency_key: string;
}

export interface VersionCreateInput {
  title: string;
  body_text: string;
  expected_project_version: number;
  idempotency_key: string;
}

export interface SegmentDecisionInput {
  content_version_id: string;
  decision: 'accept' | 'reject' | 'replace';
  replacement_text?: string;
  reason?: string;
  expected_segment_version: number;
  idempotency_key: string;
}

export interface CandidateRevisionInput {
  content_version_id: string;
  expected_project_version: number;
  idempotency_key: string;
}

export interface CandidateRestoreInput {
  source_version_id: string;
  expected_project_version: number;
  idempotency_key: string;
}

export interface HypothesisLockInput {
  content_version_id: string;
  content_intent: ContentIntent;
  audience_change: string;
  primary_response: ExpectedBehavior;
  supporting_responses: ExpectedBehavior[];
  audience_problem?: string;
  reader_promise?: string;
  viewpoint_anchor?: string;
  continuation_promise?: string;
  basis_refs: string[];
  uncertainties: string[];
  observation_window_days: number;
  expected_project_version: number;
  idempotency_key: string;
}

export interface PublicationInput {
  content_version_id: string;
  publication_gate_id: string;
  note_url?: string;
  published_at: string;
  expected_project_version: number;
  idempotency_key: string;
}

export interface SnapshotInput {
  captured_at: string;
  source: 'manual' | 'screenshot';
  result_availability?: 'observed' | 'unavailable';
  unavailable_reason?: string;
  metrics: PerformanceMetrics;
  screenshot_material_id?: string;
  snapshot_extraction_id?: string;
  confirmed_by_user: true;
  supersedes_id?: string;
  expected_project_version: number;
  idempotency_key: string;
}

export interface BlindReviewInput {
  result_snapshot_ids: string[];
  expected_project_version: number;
  idempotency_key: string;
}

export interface ObservationInput {
  statement: string;
  scope: Record<string, unknown>;
  next_test: string;
  expected_project_version: number;
  idempotency_key: string;
}

export interface ObservationTransitionInput {
  to_status: ObservationStatus;
  reason: string;
  expected_observation_version: number;
  idempotency_key: string;
}

export interface RuleCandidateCreateInput {
  expected_creator_state_version: number;
  idempotency_key: string;
}

export interface RuleCandidateDecisionInput {
  decision: 'confirm' | 'reject';
  expected_candidate_version: number;
  idempotency_key: string;
}

export interface RuleRollbackInput {
  target_version_id: string;
  expected_rule_version: number;
  idempotency_key: string;
}

export interface RuleConflictResolutionInput {
  resolution_type: 'narrow_scope' | 'keep_exception' | 'deactivate';
  scope?: Record<string, unknown>;
  expected_rule_version: number;
  expected_conflict_rule_version: number;
  idempotency_key: string;
}
