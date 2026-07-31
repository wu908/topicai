import type { ApiEnvelope } from '@/types/contracts/v2/content';
import type {
  GrowthCreatorProfile,
  GrowthCreatorProfileUpdate,
  HistoryImportResult,
  HistoryNoteInput,
  OnboardingContext,
  ProductMode,
} from '@/types/contracts/v2/onboarding';
import v2Client from './client';

async function getData<T>(promise: Promise<{ data: ApiEnvelope<T> }>): Promise<T> {
  return (await promise).data.data;
}

export const getOnboardingContext = () =>
  getData(v2Client.get<ApiEnvelope<OnboardingContext>>('/onboarding'));

export const selectProductMode = (mode: ProductMode, expectedVersion: number) =>
  getData(v2Client.put<ApiEnvelope<OnboardingContext>>('/onboarding/mode', {
    mode,
    expected_version: expectedVersion,
  }));

export const importHistory = (
  method: 'manual' | 'csv' | 'json',
  items: HistoryNoteInput[],
  idempotencyKey: string,
) => getData(v2Client.post<ApiEnvelope<HistoryImportResult>>('/history-imports', {
  method,
  items,
  idempotency_key: idempotencyKey,
}));

export const getGrowthCreatorProfile = () =>
  getData(v2Client.get<ApiEnvelope<GrowthCreatorProfile>>('/creator-profile'));

export const updateGrowthCreatorProfile = (input: GrowthCreatorProfileUpdate) =>
  getData(v2Client.put<ApiEnvelope<GrowthCreatorProfile>>('/creator-profile', input));
