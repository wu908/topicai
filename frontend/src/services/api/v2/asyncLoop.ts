/** API client for the async creation loop (Spec-013 Phase 1). */

import v2Client from './client';
import type { ApiEnvelope } from '@/types/contracts/v2/content';
import type {
  Deliverable,
  DigestResult,
  DiscardInput,
  InboxAddInput,
  InboxItem,
  MetricRecord,
  PickupInput,
  PickupResult,
} from '@/types/contracts/v2/asyncLoop';

async function getData<T>(promise: Promise<{ data: ApiEnvelope<T> }>): Promise<T> {
  return (await promise).data.data;
}

export const addInboxItem = (input: InboxAddInput) =>
  getData(v2Client.post<ApiEnvelope<InboxItem>>('/loop/inbox', input));

export const listInbox = () =>
  getData(v2Client.get<ApiEnvelope<{ items: InboxItem[]; total: number }>>('/loop/inbox'));

export const digestInbox = () =>
  getData(v2Client.post<ApiEnvelope<DigestResult>>('/loop/inbox/digest'));

export const listDeliverables = (status = 'ready') =>
  getData(
    v2Client.get<ApiEnvelope<{ items: Deliverable[]; total: number }>>(
      `/loop/deliverables?status=${encodeURIComponent(status)}`,
    ),
  );

export const pickupDeliverable = (id: string, input: PickupInput) =>
  getData(
    v2Client.post<ApiEnvelope<PickupResult>>(
      `/loop/deliverables/${encodeURIComponent(id)}:pickup`,
      input,
    ),
  );

export const discardDeliverable = (id: string, input: DiscardInput) =>
  getData(
    v2Client.post<ApiEnvelope<Deliverable>>(
      `/loop/deliverables/${encodeURIComponent(id)}:discard`,
      input,
    ),
  );

export const recordLoopMetric = (input: {
  metric: 'pickup_seconds' | 'weekly_minutes' | 'published_count';
  value: number;
  meta?: Record<string, unknown>;
}) => getData(v2Client.post<ApiEnvelope<unknown>>('/loop/metrics', input));

export const listLoopMetrics = (metric?: string) =>
  getData(
    v2Client.get<ApiEnvelope<{ items: MetricRecord[]; total: number }>>(
      `/loop/metrics${metric ? `?metric=${encodeURIComponent(metric)}` : ''}`,
    ),
  );
