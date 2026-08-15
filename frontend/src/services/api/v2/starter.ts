import v2Client from './client';
import type { ApiEnvelope } from '@/types/contracts/v2/content';
import type {
  DirectionGenerateInput,
  DirectionSelectInput,
  StarterAssessmentInput,
  StarterReviewInput,
  StarterWorkspace,
} from '@/types/contracts/v2/starter';

async function getData<T>(promise: Promise<{ data: ApiEnvelope<T> }>): Promise<T> {
  return (await promise).data.data;
}

export const getStarterWorkspace = () =>
  getData(v2Client.get<ApiEnvelope<StarterWorkspace>>('/starter'));

export const submitStarterAssessment = (input: StarterAssessmentInput) =>
  getData(
    v2Client.post<ApiEnvelope<{ assessment: StarterWorkspace['assessment']; next_step: string }>>(
      '/starter/assessment',
      input,
    ),
  );

export const generateStarterDirections = (input: DirectionGenerateInput) =>
  getData(
    v2Client.post<ApiEnvelope<{ candidates: StarterWorkspace['candidates']; next_step: string }>>(
      '/starter/directions:generate',
      input,
    ),
  );

export const selectStarterDirection = (directionId: string, input: DirectionSelectInput) =>
  getData(
    v2Client.post<ApiEnvelope<StarterWorkspace>>(
      `/starter/directions/${encodeURIComponent(directionId)}:select`,
      input,
    ),
  );

export const reviewStarterSprint = (sprintId: string, input: StarterReviewInput) =>
  getData(
    v2Client.post<ApiEnvelope<StarterWorkspace>>(
      `/starter/sprints/${encodeURIComponent(sprintId)}:review`,
      input,
    ),
  );
