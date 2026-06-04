/**
 * Phase 6 — Backend contract for Account + Team management.
 *
 * This file is the SINGLE SOURCE OF TRUTH for the Account API surface.
 * Frontend consumers (AccountsPage, OnboardingService, etc.) import the
 * types from here and call the mock service until the backend implements
 * the real endpoints.
 *
 * DELETE THIS FILE HEADER when the backend implements the routes.
 * Keep the exported types in place — pages and services will import
 * them as long as the feature is in use.
 */
import type { ApiResponse } from '@/types/api';

// ─── Resource types ───────────────────────────────────────────────

export type Platform =
  | 'wechat_mp' // 微信公众号
  | 'wechat_video' // 视频号
  | 'xhs' // 小红书
  | 'bilibili' // B 站
  | 'douyin' // 抖音
  | 'zhihu'; // 知乎

export type TeamRole = 'admin' | 'editor' | 'viewer';

export interface PlatformAccount {
  id: string;
  owner_id: string;
  platform: Platform;
  /** Display name shown in the AccountsPage card. */
  display_name: string;
  /** Whether this is the user's primary account on the platform. */
  is_primary: boolean;
  /** Connection status. */
  status: 'connected' | 'expired' | 'disconnected';
  /** OAuth token expiry (ISO 8601) when status === 'expired'. */
  token_expires_at?: string;
  /** Last successful data sync (ISO 8601). */
  last_sync_at?: string;
  /** Public stats from the platform. Optional. */
  stats?: {
    followers: number;
    articles: number;
    avg_read_count: number;
  };
  created_at: string;
  updated_at: string;
}

export interface TeamMember {
  id: string;
  email: string;
  username: string;
  /** Single character avatar initial. */
  initial: string;
  role: TeamRole;
  joined_at: string;
  last_active_at?: string;
}

export interface TeamInviteRequest {
  email: string;
  username: string;
  role: TeamRole;
}

export interface RoleChangeRequest {
  role: TeamRole;
}

// ─── API surface ──────────────────────────────────────────────────
//
// Backend MUST implement the following endpoints.
//
// ── Accounts (per user) ──
//
//  GET    /api/v1/accounts                  — list user's connected platform accounts
//  POST   /api/v1/accounts                  — register an account (body: { platform, display_name })
//  GET    /api/v1/accounts/{id}             — get one account
//  PATCH  /api/v1/accounts/{id}             — update (body: Partial<PlatformAccount>)
//  DELETE /api/v1/accounts/{id}             — disconnect account
//  POST   /api/v1/accounts/{id}/sync        — trigger a data sync (returns 202 Accepted)
//
// ── Account OAuth (placeholder for Phase 7+) ──
//
//  GET  /api/v1/accounts/{platform}/oauth-start   — returns redirect_url
//  GET  /api/v1/accounts/{platform}/oauth-callback — consumes ?code=...
//
// ── Team ──
//
//  GET    /api/v1/team/members           — list team members
//  POST   /api/v1/team/members           — invite (body: TeamInviteRequest)
//  PATCH  /api/v1/team/members/{id}      — change role (body: RoleChangeRequest)
//  DELETE /api/v1/team/members/{id}      — remove member
//
// All responses wrapped in ApiResponse<T>.

export type AccountListApiResponse = ApiResponse<PlatformAccount[]>;
export type AccountApiResponse = ApiResponse<PlatformAccount>;
export type TeamMemberListApiResponse = ApiResponse<TeamMember[]>;
export type TeamMemberApiResponse = ApiResponse<TeamMember>;
