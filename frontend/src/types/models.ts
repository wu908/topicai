/**
 * Business model types for TopicAI frontend.
 * Aligned with backend Pydantic models and SQL schema.
 */
import type {
  RecommendationMode,
  InputType,
  ContentFormat,
  ProductionComplexity,
  ContentDepth,
  HotspotPreference,
  FeedbackType,
  SourceType,
  RiskSeverity,
  DataSourceLevel,
  Platform,
} from './enums';

/** AI Quality metadata attached to every AI output */
export interface AIQualityMeta {
  confidence: number;
  data_source: DataSourceLevel | string;
  model_version: string;
  caveat: string | null;
  generated_at: string;
}

/** User model */
export interface User {
  id: string;
  email: string;
  username: string;
  ai_calls_today: number;
  ai_calls_reset_at: string;
  created_at: string;
  last_login: string | null;
}

/** Creator profile */
export interface CreatorProfile {
  id: string;
  user_id: string;
  track: string;
  content_formats: ContentFormat[];
  production_complexity: ProductionComplexity;
  content_depth: ContentDepth;
  hotspot_preference: HotspotPreference;
  recommendation_mode: RecommendationMode;
  rubric_weights: Record<string, number>;
  created_at: string;
  updated_at: string;
}

/** Topic item within a recommendation */
export interface TopicItem {
  title: string;
  reason: string;
  estimated_heat: number;
  content_angle: string;
  track_match_score: number;
  format_match_score: number;
  data_quality_score: number;
  composite_score: number;
  confidence: number;
  data_source: DataSourceLevel | string;
  caveat: string | null;
}

/** Topic recommendation result */
export interface TopicRecommendation {
  id: string;
  user_id: string;
  topics: TopicItem[];
  recommendation_mode: RecommendationMode;
  data_source_used: DataSourceLevel | string;
  /** Spec-007 US2 T044: AI confidence in [0, 1]. */
  confidence: number;
  created_at: string;
}

/** Attribution conclusion for viral analysis */
export interface AttributionConclusion {
  dimension: string;
  conclusion: string;
  relevance: number;
  evidence: string;
}

/** Viral analysis result */
export interface ViralAnalysis {
  id: string;
  user_id: string;
  input_type: InputType;
  input_text: string;
  viral_score: number;
  structural_analysis: Record<string, unknown>;
  attributions: AttributionConclusion[];
  transferable_template: string;
  rewrite_suggestions: string;
  risk_warnings: string[];
  confidence: number;
  data_source: DataSourceLevel | string;
  created_at: string;
}

/** Idea booster result */
export interface IdeaBoosterResult {
  id: string;
  user_id: string;
  input_idea: string;
  key_assumptions: string[];
  feasibility_assessment: string;
  title_candidates: string[];
  content_outline: string;
  publish_schedule: string;
  confidence: number;
  created_at: string;
}

/** Optimized title within title optimization */
export interface OptimizedTitle {
  title: string;
  ctr_estimate: number;
  technique_used: string;
  technique_reason: string;
}

/** Title optimization result */
export interface TitleOptimization {
  id: string;
  user_id: string;
  original_title: string;
  content_summary: string | null;
  optimized_titles: OptimizedTitle[];
  created_at: string;
}

/** Sub-track within track diagnosis */
export interface SubTrack {
  name: string;
  potential_score: number;
  reason: string;
}

/** Track diagnosis result */
export interface TrackDiagnosis {
  id: string;
  user_id: string;
  track_keyword: string;
  health_score: number;
  competitiveness_score: number;
  direction_advice: string;
  sub_tracks: SubTrack[];
  confidence: number;
  data_source: DataSourceLevel | string;
  created_at: string;
}

/** Feedback record */
export interface FeedbackRecord {
  id: string;
  user_id: string;
  source_type: SourceType;
  source_id: string;
  feedback_type: FeedbackType;
  feedback_value: string | null;
  reason: string | null;
  created_at: string;
}

/** Feedback analysis result */
export interface FeedbackAnalysis {
  id: string;
  user_id: string;
  feedback_record_id: string;
  success_factors: string | null;
  failure_factors: string | null;
  weight_adjustments: Record<string, number>;
  excluded_patterns: string[];
  created_at: string;
}

/** Effect review result */
export interface EffectReview {
  id: string;
  user_id: string;
  topic_title: string;
  prediction: Record<string, unknown>;
  actual_result: Record<string, unknown> | null;
  attribution: Record<string, unknown> | null;
  learnings: Record<string, unknown> | null;
  created_at: string;
}

/** Risk item within content risk report */
export interface RiskItem {
  category: string;
  description: string;
  severity: RiskSeverity;
  suggestion: string;
}

/** Content risk report */
export interface ContentRiskReport {
  id: string;
  user_id: string;
  content_text: string;
  risks: RiskItem[];
  overall_risk_score: number;
  created_at: string;
}

/** Time slot within publish suggestion */
export interface TimeSlot {
  time_range: string;
  reason: string;
  benchmark_source: string;
}

/** Publish suggestion */
export interface PublishSuggestion {
  id: string;
  user_id: string;
  platform: Platform;
  content_type: string;
  suggested_times: TimeSlot[];
  created_at: string;
}

/** Health check response */
export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'down';
  version: string;
  uptime_seconds: number;
  components: {
    database: { status: string; detail?: string };
    llm: { status: string; provider: string; model: string; detail?: string };
    data_sources: { status: string; active_level: string; detail?: string };
  };
}

/** Onboarding step data */
export interface OnboardingData {
  track: string;
  content_formats: ContentFormat[];
  production_complexity: ProductionComplexity;
  content_depth: ContentDepth;
  hotspot_preference: HotspotPreference;
  recommendation_mode: RecommendationMode;
}
