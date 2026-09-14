import type { ApiEnvelope } from '@/types/contracts/v2/content';
import type { HistoryImportResult } from '@/types/contracts/v2/onboarding';
import type {
  ReferenceAnchor,
  ReferenceAnchorUpdate,
  ReferenceNoteInput,
} from '@/types/contracts/v2/referenceAnchor';
import v2Client from './client';

async function getData<T>(promise: Promise<{ data: ApiEnvelope<T> }>): Promise<T> {
  return (await promise).data.data;
}

/** 导入「我想做成这样」的参考内容。每一行都必须带来源。 */
export const importReferences = (items: ReferenceNoteInput[], idempotencyKey: string) =>
  getData(
    v2Client.post<ApiEnvelope<HistoryImportResult>>('/reference-imports', {
      method: 'manual',
      items,
      idempotency_key: idempotencyKey,
    }),
  );

/**
 * 读锚点。参考集没变时是命中缓存的快速返回；刚贴完新参考的那次会读内容本身，
 * 通常十几秒——调用方必须给出等待状态。
 */
export const getReferenceAnchor = () =>
  getData(v2Client.get<ApiEnvelope<ReferenceAnchor>>('/reference-anchor'));

export const updateReferenceAnchor = (input: ReferenceAnchorUpdate) =>
  getData(v2Client.put<ApiEnvelope<ReferenceAnchor>>('/reference-anchor', input));
