import type { ContentIntent, ContentProject } from './content';

export type StarterReadiness = 'not_ready' | 'ready' | 'paused';

export interface StarterAssessment {
  id: string;
  motivation: 'curious' | 'career' | 'expression' | 'other';
  available_hours_per_week: number;
  publish_commitment: boolean;
  accept_experiment: boolean;
  experience_assets: string[];
  interest_assets: string[];
  skill_assets: string[];
  privacy_limits: string[];
  readiness: StarterReadiness;
  version: number;
  completed_at: string | null;
}

export interface StarterTopic {
  title: string;
  content_intent: ContentIntent;
  audience_change: string;
  evidence_refs: string[];
}

export interface DirectionCandidate {
  id: string;
  label: string;
  audience: string;
  creator_credibility: string;
  content_supply: string[];
  first_three_topics: StarterTopic[];
  production_cost: 'low' | 'medium' | 'high';
  similarity_risk: 'low' | 'medium' | 'high' | 'unknown';
  validation_method: string;
  evidence_refs: string[];
  selection_state: 'proposed' | 'selected' | 'rejected';
  version: number;
}

export interface StarterSprint {
  id: string;
  starts_at: string;
  ends_at: string;
  target_publish_count: 3;
  published_count: number;
  graduation_state: 'active' | 'graduated' | 'expired' | 'paused' | 'exited';
  blocker_reasons: string[];
  next_topics: string[];
  review_summary: string | null;
  version: number;
}

export interface StarterWorkspace {
  assessment: StarterAssessment | null;
  candidates: DirectionCandidate[];
  sprint: StarterSprint | null;
  projects: ContentProject[];
  next_step: 'assessment' | 'directions' | 'sprint' | 'complete';
}

export interface StarterAssessmentInput {
  motivation: StarterAssessment['motivation'];
  available_hours_per_week: number;
  publish_commitment: boolean;
  accept_experiment: boolean;
  experience_assets: string[];
  interest_assets: string[];
  skill_assets: string[];
  privacy_limits: string[];
  idempotency_key: string;
}

export interface DirectionGenerateInput {
  expected_assessment_version: number;
  idempotency_key: string;
}

export interface DirectionSelectInput {
  expected_direction_version: number;
  idempotency_key: string;
}

export interface StarterReviewInput {
  observed_summary: string;
  blocker_reasons: string[];
  next_topics: string[];
  expected_sprint_version: number;
  idempotency_key: string;
}
