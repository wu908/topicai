/**
 * Global application state store (Zustand).
 * Manages sidebar state, rate limit info, AI degradation status.
 */
import { create } from 'zustand';
import type { HealthStatus } from '@/types/enums';

interface RateLimitInfo {
  ai_calls_today: number;
  ai_calls_limit: number;
  reset_at: string | null;
}

interface AppNotification {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  message: string;
  duration?: number;
}

interface AppState {
  // Sidebar
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;

  // Rate limit
  rateLimit: RateLimitInfo;
  updateRateLimit: (info: Partial<RateLimitInfo>) => void;
  getRemainingCalls: () => number;

  // System health
  systemHealth: HealthStatus;
  isAIDegraded: boolean;
  degradationMessage: string | null;
  setSystemHealth: (status: HealthStatus) => void;
  setAIDegraded: (degraded: boolean, message?: string | null) => void;

  // Notifications
  notifications: AppNotification[];
  addNotification: (notification: Omit<AppNotification, 'id'>) => void;
  removeNotification: (id: string) => void;

  // Global loading
  globalLoading: boolean;
  setGlobalLoading: (loading: boolean) => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  // Sidebar
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open: boolean) => set({ sidebarOpen: open }),

  // Rate limit
  rateLimit: {
    ai_calls_today: 0,
    ai_calls_limit: 20,
    reset_at: null,
  },
  updateRateLimit: (info: Partial<RateLimitInfo>) =>
    set((state) => ({
      rateLimit: { ...state.rateLimit, ...info },
    })),
  getRemainingCalls: () => {
    const { rateLimit } = get();
    return Math.max(0, rateLimit.ai_calls_limit - rateLimit.ai_calls_today);
  },

  // System health
  systemHealth: 'healthy' as HealthStatus,
  isAIDegraded: false,
  degradationMessage: null,
  setSystemHealth: (status: HealthStatus) => set({ systemHealth: status }),
  setAIDegraded: (degraded: boolean, message?: string | null) =>
    set({ isAIDegraded: degraded, degradationMessage: message || null }),

  // Notifications
  notifications: [],
  addNotification: (notification: Omit<AppNotification, 'id'>) => {
    const id = `notif-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    set((state) => ({
      notifications: [...state.notifications, { ...notification, id }],
    }));
    // Auto-remove after duration (default 5 seconds)
    const duration = notification.duration ?? 5000;
    if (duration > 0) {
      setTimeout(() => {
        get().removeNotification(id);
      }, duration);
    }
  },
  removeNotification: (id: string) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),

  // Global loading
  globalLoading: false,
  setGlobalLoading: (loading: boolean) => set({ globalLoading: loading }),
}));
