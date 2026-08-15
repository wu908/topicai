export type ProductMode = 'starter' | 'growth';
export type ProfileAttributeStatus = 'provisional' | 'confirmed' | 'rejected';

export interface OnboardingContext {
  mode: ProductMode;
  state: 'not_started' | 'in_progress' | 'completed';
  version: number;
}

export interface HistoryNoteInput {
  external_key?: string | null;
  title: string;
  body_excerpt?: string;
  published_at?: string | null;
  note_url?: string | null;
  metrics?: Record<string, number | null>;
  audience_questions?: string[];
  tags?: string[];
}

export interface HistoryImportResult {
  id: string;
  success_count: number;
  failure_count: number;
  /** Discriminated union: each status pins its own payload fields. */
  item_results: Array<
    | { index: number; status: 'imported'; note_id: string }
    | { index: number; status: 'duplicate'; note_id?: string }
    | { index: number; status: 'failed'; error: string }
  >;
}

export interface ProfileAttribute {
  value: string;
  status: ProfileAttributeStatus;
  origin: 'inferred' | 'user';
  evidence_refs: string[];
  confidence: 'low' | 'medium' | 'high';
  limitations: string[];
}

export interface GrowthCreatorProfile {
  id: string;
  confirmation_state: 'provisional' | 'confirmed' | 'needs_review';
  version: number;
  attributes: {
    niche: ProfileAttribute;
    target_audience: ProfileAttribute;
    growth_goal: ProfileAttribute;
    content_pillars: ProfileAttribute[];
    voice_traits: ProfileAttribute[];
    avoid_traits: ProfileAttribute[];
  };
  rejected_attributes: Array<ProfileAttribute & { field: RejectableProfileField }>;
}

export type RejectableProfileField =
  | 'niche'
  | 'target_audience'
  | 'growth_goal'
  | 'content_pillar'
  | 'voice_trait';

export interface GrowthCreatorProfileUpdate {
  niche: string;
  target_audience: string;
  growth_goal: 'stable_publish' | 'follower_growth' | 'both';
  content_pillars: string[];
  voice_traits: string[];
  avoid_traits: string[];
  rejected: Array<{ field: RejectableProfileField; value: string }>;
  confirm: boolean;
  expected_version: number;
}
