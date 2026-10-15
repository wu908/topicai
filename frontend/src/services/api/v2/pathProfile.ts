/** 路径画像与探索位（P3-B1 / P3-B4）。 */
import type { ApiEnvelope } from '@/types/contracts/v2/content';
import v2Client from './client';

async function getData<T>(promise: Promise<{ data: ApiEnvelope<T> }>): Promise<T> {
  return (await promise).data.data;
}

export interface PathProfile {
  statement: string;
  publish_focus: string;
  avoid: string;
  cadence: string;
  tone: string;
  version: number;
}

export interface PathRevisionProposal {
  field: string;
  current: string;
  proposed: string;
  reason: string;
}

export interface PathRevisionView {
  proposals: PathRevisionProposal[];
  reason: string;
}

export interface ExplorationSlot {
  id: string;
  title: string;
  hypothesis: string;
  status: 'running' | 'adopted' | 'rejected';
  attribution: string;
}

export const getPathProfile = () =>
  getData(v2Client.get<ApiEnvelope<PathProfile>>('/path-profile'));

export const updatePathProfile = (input: Partial<PathProfile> & { expected_version: number }) =>
  getData(v2Client.put<ApiEnvelope<PathProfile>>('/path-profile', input));

/** AI 修订提案：只提议不落库（P3-B1）。 */
export const proposePathRevision = () =>
  getData(
    v2Client.post<ApiEnvelope<PathRevisionView>>('/path-profile:propose-revision', {}),
  );

export const listExplorationSlots = () =>
  getData(v2Client.get<ApiEnvelope<{ items: ExplorationSlot[]; version: number }>>('/exploration-slots'));

export const createExplorationSlot = (input: {
  title: string;
  hypothesis?: string;
  expected_version: number;
}) =>
  getData(
    v2Client.post<ApiEnvelope<{ items: ExplorationSlot[]; version: number }>>(
      '/exploration-slots',
      input,
    ),
  );

export const decideExplorationSlot = (
  slotId: string,
  input: { status: 'running' | 'adopted' | 'rejected'; attribution?: string; expected_version: number },
) =>
  getData(
    v2Client.post<ApiEnvelope<{ items: ExplorationSlot[]; version: number }>>(
      `/exploration-slots/${encodeURIComponent(slotId)}:decide`,
      input,
    ),
  );
