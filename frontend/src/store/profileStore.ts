/**
 * Creator profile state store (Zustand).
 * Manages creator profile data and onboarding state.
 */
import { create } from 'zustand';
import type { CreatorProfile } from '@/types/models';
import * as profileApi from '@/services/api/profiles';
import { extractErrorMessage } from '@/utils/error';

interface ProfileState {
  profile: CreatorProfile | null;
  isLoading: boolean;
  error: string | null;
  isOnboarded: boolean;

  fetchProfile: () => Promise<void>;
  submitOnboarding: (data: Parameters<typeof profileApi.submitOnboarding>[0]) => Promise<void>;
  updateProfile: (data: Parameters<typeof profileApi.updateProfile>[0]) => Promise<void>;
  clearError: () => void;
}

export const useProfileStore = create<ProfileState>((set) => ({
  profile: null,
  isLoading: false,
  error: null,
  isOnboarded: false,

  fetchProfile: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await profileApi.getMyProfile();
      // Defensive: backend may wrap profile in {profile: {...}} — extract if so
      let profile = response.data;
      if (profile && typeof profile === 'object' && 'profile' in profile && !('track' in profile)) {
        profile = (profile as Record<string, unknown>).profile as CreatorProfile;
      }
      set({ profile, isOnboarded: !!profile, isLoading: false });
    } catch {
      set({ profile: null, isOnboarded: false, isLoading: false });
    }
  },

  submitOnboarding: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await profileApi.submitOnboarding(data);
      // Defensive: backend may wrap profile in {profile: {...}} — extract if so
      let profile = response.data;
      if (profile && typeof profile === 'object' && 'profile' in profile && !('track' in profile)) {
        profile = (profile as Record<string, unknown>).profile as CreatorProfile;
      }
      set({ profile, isOnboarded: true, isLoading: false });
    } catch (err: unknown) {
      const message = extractErrorMessage(err, 'Onboarding 提交失败');
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  updateProfile: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await profileApi.updateProfile(data);
      // Defensive: backend may wrap profile in {profile: {...}} — extract if so
      let profile = response.data;
      if (profile && typeof profile === 'object' && 'profile' in profile && !('track' in profile)) {
        profile = (profile as Record<string, unknown>).profile as CreatorProfile;
      }
      set({ profile, isLoading: false });
    } catch (err: unknown) {
      const message = extractErrorMessage(err, '画像更新失败');
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  clearError: () => set({ error: null }),
}));
