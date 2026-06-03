/**
 * Rate limit hook.
 * Tracks and displays AI call usage.
 */
import { useAppStore } from '@/store/appStore';

export function useRateLimit() {
  const rateLimit = useAppStore((s) => s.rateLimit);
  const updateRateLimit = useAppStore((s) => s.updateRateLimit);
  const getRemainingCalls = useAppStore((s) => s.getRemainingCalls);
  const addNotification = useAppStore((s) => s.addNotification);

  const remaining = getRemainingCalls();
  const usagePercent = (rateLimit.ai_calls_today / rateLimit.ai_calls_limit) * 100;
  const isLow = remaining <= 5 && remaining > 0;
  const isExhausted = remaining <= 0;

  /** Check if the user can make an AI call, show warning if low */
  const checkAndConsume = (): boolean => {
    if (isExhausted) {
      addNotification({
        type: 'warning',
        message: '今日AI调用次数已用完，请明天再试',
        duration: 5000,
      });
      return false;
    }
    if (isLow) {
      addNotification({
        type: 'info',
        message: `今日AI调用剩余 ${remaining} 次`,
        duration: 3000,
      });
    }
    // Increment usage
    updateRateLimit({ ai_calls_today: rateLimit.ai_calls_today + 1 });
    return true;
  };

  /** Rollback a consumed AI call (e.g. when API call fails) */
  const rollback = () => {
    updateRateLimit({ ai_calls_today: Math.max(0, rateLimit.ai_calls_today - 1) });
  };

  return {
    remaining,
    usagePercent,
    isLow,
    isExhausted,
    checkAndConsume,
    rollback,
    rateLimit,
    updateRateLimit,
  };
}
