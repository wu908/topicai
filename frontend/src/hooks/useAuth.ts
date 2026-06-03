/**
 * Authentication hook.
 * Provides convenient access to auth state and actions.
 */
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { useProfileStore } from '@/store/profileStore';

export function useAuth() {
  const authStore = useAuthStore();
  const profileStore = useProfileStore();

  return {
    user: authStore.user,
    isAuthenticated: authStore.isAuthenticated,
    isLoading: authStore.isLoading,
    error: authStore.error,
    profile: profileStore.profile,
    isOnboarded: profileStore.isOnboarded,

    login: authStore.login,
    register: authStore.register,
    logout: authStore.logout,
    clearError: authStore.clearError,
    fetchCurrentUser: authStore.fetchCurrentUser,
    fetchProfile: profileStore.fetchProfile,
  };
}

/** Hook that redirects to login if not authenticated */
export function useRequireAuth() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const profile = useProfileStore((s) => s.profile);
  const isOnboarded = useProfileStore((s) => s.isOnboarded);
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    // Use getState() for stable function references that don't change on every render
    useAuthStore.getState().fetchCurrentUser().catch(() => {});
    useProfileStore.getState().fetchProfile().catch(() => {});
  }, [isAuthenticated, navigate]);

  return { isAuthenticated, profile, isOnboarded };
}
