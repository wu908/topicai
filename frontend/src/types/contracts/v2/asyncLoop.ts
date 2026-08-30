/** Async creation loop contracts (Spec-013 Phase 1). */

export type InboxKind = 'text' | 'image' | 'voice' | 'link' | 'idea';
export type InboxConsent = 'publishable' | 'private';
export type ContentIntent = 'solve' | 'share' | 'record';
export type DeliverableStatus =
  | 'queued'
  | 'producing'
  | 'ready'
  | 'failed'
  | 'expired'
  | 'picked'
  | 'discarded';

export interface InboxAddInput {
  kind: InboxKind;
  title?: string;
  content: string;
  consent?: InboxConsent;
  idempotency_key: string;
}

export interface InboxItem {
  id: string;
  kind: InboxKind;
  title: string;
  content: string;
  consent: InboxConsent;
  status: 'intake' | 'digested' | 'failed';
  version: number;
  created_at: string;
  updated_at: string;
}

export interface DeliverableFact {
  statement: string;
  source_inbox_id: string;
  note?: string;
}

export interface DeliverableJudgment {
  audience_change?: string;
  primary_response?: string;
  supporting?: string[];
  window_days?: number;
}

export interface Deliverable {
  id: string;
  thread_id: string;
  title: string;
  body_text: string;
  outline: { step: string; label: string }[];
  facts: DeliverableFact[];
  judgment: DeliverableJudgment;
  content_intent: ContentIntent | null;
  proposed_publish_at: string | null;
  is_exploration: boolean;
  status: DeliverableStatus;
  attribution: string | null;
  expire_at: string | null;
  precheck: { passed: boolean; issues: string[] };
  version: number;
  created_at: string;
  updated_at: string;
}

export interface PickupInput {
  content_intent: ContentIntent;
  audience_change: string;
  primary_response?: 'save' | 'comment' | 'profile_visit' | 'follow';
  window_days?: number;
  schedule_at?: string;
  idempotency_key: string;
}

export interface DiscardInput {
  reason: string;
  idempotency_key: string;
}

export interface PickupResult {
  project: { id: string; title: string };
  deliverable: Deliverable;
}

export interface DigestResult {
  thread_id: string;
  deliverables: Deliverable[];
}

export interface MetricRecord {
  id: string;
  metric: 'pickup_seconds' | 'weekly_minutes' | 'published_count' | 'discard_attribution';
  value: number;
  meta: Record<string, unknown>;
  created_at: string;
}

export interface WeeklyRow {
  project_id: string;
  title: string;
  project_status: string;
  published_at: string;
  note_url: string | null;
  judgment: {
    audience_change: string | null;
    primary_response: string | null;
    window_days: number | null;
  };
  actual: {
    captured_at: string | null;
    metrics: Record<string, number | null>;
    result_availability: string | null;
  };
  review: {
    id: string;
    calibration_state: 'valid' | 'insufficient' | 'calibration_invalid';
    eligible_for_rule_upgrade: boolean;
    intent_outcome: string | null;
  } | null;
  observation: { id: string; status: string; next_test: string } | null;
  stage:
    | 'needs_snapshot'
    | 'needs_review'
    | 'review_insufficient'
    | 'ready_to_confirm'
    | 'confirmed';
}
