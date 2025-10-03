import { useState, useCallback, useRef } from 'react';

interface RateLimitOptions {
  maxRequests: number;
  windowMs: number;
}

interface RateLimitResult {
  isLimited: boolean;
  remainingRequests: number;
  resetTime: Date | null;
  checkLimit: () => boolean;
}

/**
 * Client-side rate limiting hook to prevent API abuse
 *
 * @param options - Configuration for rate limiting
 * @returns Rate limit state and check function
 */
export function useRateLimit(options: RateLimitOptions): RateLimitResult {
  const { maxRequests, windowMs } = options;

  const [remainingRequests, setRemainingRequests] = useState(maxRequests);
  const [resetTime, setResetTime] = useState<Date | null>(null);
  const requestTimestamps = useRef<number[]>([]);

  const checkLimit = useCallback(() => {
    const now = Date.now();
    const windowStart = now - windowMs;

    // Remove timestamps outside the current window
    requestTimestamps.current = requestTimestamps.current.filter(
      (timestamp) => timestamp > windowStart
    );

    // Check if limit is exceeded
    if (requestTimestamps.current.length >= maxRequests) {
      const oldestRequest = requestTimestamps.current[0];
      const nextResetTime = new Date(oldestRequest + windowMs);
      setResetTime(nextResetTime);
      setRemainingRequests(0);
      return false; // Rate limited
    }

    // Add current request timestamp
    requestTimestamps.current.push(now);
    setRemainingRequests(maxRequests - requestTimestamps.current.length);
    setResetTime(null);

    return true; // Not rate limited
  }, [maxRequests, windowMs]);

  return {
    isLimited: remainingRequests === 0 && resetTime !== null,
    remainingRequests,
    resetTime,
    checkLimit,
  };
}

/**
 * Predefined rate limit configurations
 */
export const RATE_LIMITS = {
  // 10 searches per minute
  SEARCH: { maxRequests: 10, windowMs: 60 * 1000 },
  // 20 follow-ups per minute
  FOLLOW_UP: { maxRequests: 20, windowMs: 60 * 1000 },
  // 5 exports per minute
  EXPORT: { maxRequests: 5, windowMs: 60 * 1000 },
};
