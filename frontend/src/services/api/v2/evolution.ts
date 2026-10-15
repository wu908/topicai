/** 进化可见区（P4-F1）：「哪里变了」。 */
import type { ApiEnvelope } from '@/types/contracts/v2/content';
import v2Client from './client';

async function getData<T>(promise: Promise<{ data: ApiEnvelope<T> }>): Promise<T> {
  return (await promise).data.data;
}

export interface EvolutionChange {
  kind: string;
  summary: string;
  at: string;
}

export interface EvolutionSummary {
  changes: EvolutionChange[];
  capability_trust: Record<string, number>;
  recent_signals: Array<Record<string, unknown>>;
}

export const getEvolutionSummary = () =>
  getData(v2Client.get<ApiEnvelope<EvolutionSummary>>('/evolution/summary'));
