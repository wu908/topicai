/**
 * Account + Team API client — Phase 8 real endpoints.
 */
import apiClient from './client';
import type { ApiResponse } from '@/types/api';
import type {
  PlatformAccount,
  TeamMember,
  TeamInviteRequest,
  RoleChangeRequest,
} from '@/types/contracts/accounts';

// ── Accounts ──

export async function listAccounts(): Promise<ApiResponse<PlatformAccount[]>> {
  const r = await apiClient.get<ApiResponse<PlatformAccount[]>>('/accounts');
  return r.data;
}

export async function createAccount(
  body: { platform: string; display_name: string }
): Promise<ApiResponse<PlatformAccount>> {
  const r = await apiClient.post<ApiResponse<PlatformAccount>>('/accounts', body);
  return r.data;
}

export async function setPrimaryAccount(
  id: string,
): Promise<ApiResponse<PlatformAccount>> {
  const r = await apiClient.patch<ApiResponse<PlatformAccount>>('/accounts/' + id);
  return r.data;
}

export async function disconnectAccount(id: string): Promise<ApiResponse<Record<string, never>>> {
  const r = await apiClient.delete<ApiResponse<Record<string, never>>>('/accounts/' + id);
  return r.data;
}

export async function syncAccount(id: string): Promise<ApiResponse<{ last_sync_at: string }>> {
  const r = await apiClient.post<ApiResponse<{ last_sync_at: string }>>('/accounts/' + id + '/sync');
  return r.data;
}

// ── Team ──

export async function listTeam(): Promise<ApiResponse<TeamMember[]>> {
  const r = await apiClient.get<ApiResponse<TeamMember[]>>('/team/members');
  return r.data;
}

export async function inviteMember(
  body: TeamInviteRequest,
): Promise<ApiResponse<TeamMember>> {
  const r = await apiClient.post<ApiResponse<TeamMember>>('/team/members', body);
  return r.data;
}

export async function changeMemberRole(
  id: string,
  body: RoleChangeRequest,
): Promise<ApiResponse<TeamMember>> {
  const r = await apiClient.patch<ApiResponse<TeamMember>>('/team/members/' + id, body);
  return r.data;
}

export async function removeMember(id: string): Promise<ApiResponse<Record<string, never>>> {
  const r = await apiClient.delete<ApiResponse<Record<string, never>>>('/team/members/' + id);
  return r.data;
}
