/**
 * API request/response types for TopicAI frontend.
 * Aligned with backend API endpoints (21 endpoints).
 */
import type {
  User,
  CreatorProfile,
  TopicRecommendation,
  ViralAnalysis,
  IdeaBoosterResult,
  TitleOptimization,
  TrackDiagnosis,
  FeedbackRecord,
  FeedbackAnalysis,
  EffectReview,
  ContentRiskReport,
  PublishSuggestion,
  HealthCheckResponse,
  AIQualityMeta,
  OnboardingData,
} from './models';
import type {
  RecommendationMode,
  InputType,
  FeedbackType,
  SourceType,
  Platform,
} from './enums';

/** Unified API response format */
export interface ApiResponse<T> {
  code: number;
  data: T;
  message: string;
  meta: {
    ai_quality?: AIQualityMeta;
  };
}

/** Paginated list response */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// ─── Auth API ───────────────────────────────────

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface RegisterResponse {
  user: {
    id: string;
    email: string;
    username: string;
    created_at: string;
  };
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
}

// ─── Profile API ────────────────────────────────

export interface OnboardingRequest extends OnboardingData {}

export interface UpdateProfileRequest {
  track?: string;
  content_formats?: string[];
  production_complexity?: string;
  content_depth?: string;
  hotspot_preference?: string;
  recommendation_mode?: RecommendationMode;
  rubric_weights?: Record<string, number>;
}

// ─── Topics API ─────────────────────────────────

export interface TopicRecommendRequest {
  mode?: RecommendationMode;
  count?: number;
}

// ─── Viral API ──────────────────────────────────

export interface ViralAnalyzeRequest {
  input_type: InputType;
  content: string;
}

// ─── Ideas API ──────────────────────────────────

export interface IdeaBoostRequest {
  idea_text: string;
  context?: string;
}

// ─── Titles API ─────────────────────────────────

export interface TitleOptimizeRequest {
  title: string;
  content_summary?: string;
  count?: number;
}

// ─── Tracks API ─────────────────────────────────

export interface TrackDiagnoseRequest {
  track_keyword: string;
}

// ─── Feedback API ───────────────────────────────

export interface FeedbackSubmitRequest {
  source_type: SourceType;
  source_id: string;
  feedback_type: FeedbackType;
  feedback_value?: string;
  reason?: string;
}

// ─── Publish API ────────────────────────────────

export interface PublishAdviceRequest {
  platform: Platform;
  content_type: string;
}

// ─── Reviews API ────────────────────────────────

export interface PredictRequest {
  topic_title: string;
  content_outline?: string;
}

export interface AttributeRequest {
  review_id: string;
  actual_views?: number;
  actual_likes?: number;
  actual_comments?: number;
  actual_shares?: number;
  actual_engagement_rate?: number;
  notes?: string;
}

// ─── Risk API ───────────────────────────────────

export interface RiskCheckRequest {
  content_text: string;
}

// ─── History list params ────────────────────────

export interface HistoryListParams {
  page?: number;
  page_size?: number;
}

// Re-export model types for convenience
export type {
  User,
  CreatorProfile,
  TopicRecommendation,
  ViralAnalysis,
  IdeaBoosterResult,
  TitleOptimization,
  TrackDiagnosis,
  FeedbackRecord,
  FeedbackAnalysis,
  EffectReview,
  ContentRiskReport,
  PublishSuggestion,
  HealthCheckResponse,
  AIQualityMeta,
};
