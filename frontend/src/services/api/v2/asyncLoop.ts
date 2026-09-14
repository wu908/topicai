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
  WeeklyRow,
} from '@/types/contracts/v2/asyncLoop';

async function getData<T>(promise: Promise<{ data: ApiEnvelope<T> }>): Promise<T> {
  return (await promise).data.data;
}

export const addInboxItem = (input: InboxAddInput) =>
  getData(v2Client.post<ApiEnvelope<InboxItem>>('/loop/inbox', input));

export const listInbox = () =>
  getData(v2Client.get<ApiEnvelope<{ items: InboxItem[]; total: number }>>('/loop/inbox'));

/** 消化收件箱。limit 用于逐条消化：单条 AI 生成要几十秒，
 *  一次请求塞整批会撞上网关读超时，逐条还能显示进度并隔离单条失败。 */
export const digestInbox = (limit?: number) =>
  getData(
    v2Client.post<ApiEnvelope<DigestResult>>(
      limit === undefined
        ? '/loop/inbox/digest'
        : `/loop/inbox/digest?limit=${encodeURIComponent(String(limit))}`,
    ),
  );

export const listDeliverables = (status = 'ready') =>
  getData(
    v2Client.get<ApiEnvelope<{ items: Deliverable[]; total: number }>>(
      `/loop/deliverables?status=${encodeURIComponent(status)}`,
    ),
  );

/** 灵感池 = 过期未拾取 ∪ 用户主动丢弃。 */
export const POOL_STATUSES = 'expired,discarded';

export const listPool = () =>
  getData(
    v2Client.get<ApiEnvelope<{ items: Deliverable[]; total: number }>>(
      `/loop/deliverables?status=${encodeURIComponent(POOL_STATUSES)}`,
    ),
  );

/** 池内条目重新上架（重置 7 天观察窗）。 */
export const restoreDeliverable = (id: string) =>
  getData(
    v2Client.post<ApiEnvelope<Deliverable>>(
      `/loop/deliverables/${encodeURIComponent(id)}:restore`,
    ),
  );

/** 永久删除池内条目。 */
export const deleteDeliverable = (id: string) =>
  getData(
    v2Client.delete<ApiEnvelope<{ id: string }>>(
      `/loop/deliverables/${encodeURIComponent(id)}`,
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

export const listWeekly = (days = 7) =>
  getData(
    v2Client.get<ApiEnvelope<{ items: WeeklyRow[]; total: number }>>(
      `/loop/weekly?days=${days}`,
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
