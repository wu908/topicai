/**
 * Authentication state store (Zustand).
 * Manages user, tokens, and auth state.
 */
import { create } from 'zustand';
import type { User } from '@/types/models';
import * as authApi from '@/services/api/auth';
import { extractErrorMessage } from '@/utils/error';

/** Safe localStorage accessor — fails silently in sandboxed / privacy-mode browsers. */
function safeGet(key: string): string | null {
  try { return localStorage.getItem(key); }
  catch { return null; }
}
function safeSet(key: string, value: string): void {
  try { localStorage.setItem(key, value); }
  catch { /* no-op */ }
}
function safeRemove(key: string): void {
  try { localStorage.removeItem(key); }
  catch { /* no-op */ }
}


interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: !!safeGet('access_token'),
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authApi.login({ email, password });
      // Backend returns ApiResponse<LoginResponse>: { code, data: { access_token, refresh_token, user }, message }
      const { access_token, refresh_token, user } = response.data;
      safeSet('access_token', access_token);
      safeSet('refresh_token', refresh_token);
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (err: unknown) {
      const message = extractErrorMessage(err, '登录失败，请检查邮箱和密码');
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  register: async (email: string, username: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authApi.register({ email, username, password });
      // Backend returns tokens directly in registration response
      const { access_token, refresh_token, user } = response.data;
      safeSet('access_token', access_token);
      safeSet('refresh_token', refresh_token);
      const userObj: User = {
        id: user.id,
        email: user.email,
        username: user.username,
        ai_calls_today: 0,
        ai_calls_reset_at: '',
        created_at: user.created_at,
        last_login: null,
      };
      set({ user: userObj, isAuthenticated: true, isLoading: false });
    } catch (err: unknown) {
      const message = extractErrorMessage(err, '注册失败，请稍后重试');
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  logout: () => {
    safeRemove('access_token');
    safeRemove('refresh_token');
    set({ user: null, isAuthenticated: false, error: null });
  },

  refreshToken: async () => {
    const refreshTokenValue = safeGet('refresh_token');
    if (!refreshTokenValue) {
      get().logout();
      return;
    }
    try {
      const response = await authApi.refreshToken({ refresh_token: refreshTokenValue });
      safeSet('access_token', response.data.access_token);
    } catch {
      get().logout();
    }
  },

  fetchCurrentUser: async () => {
    set({ isLoading: true });
    try {
      const response = await authApi.getCurrentUser();
      // Backend returns { code: 200, data: { user: {...} } } per auth.ts:36
      const user = response.data?.user ?? null;
      set({ user, isAuthenticated: true, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  clearError: () => set({ error: null }),
}));
