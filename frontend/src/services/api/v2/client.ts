// Share the single apiClient instance instead of building a second one —
// two singletons would diverge on any future client-level state.
export { default } from '@/services/api/client';
