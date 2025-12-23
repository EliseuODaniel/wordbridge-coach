/** API utility functions for retry logic */

export interface RetryOptions {
  maxRetries?: number;
  baseDelay?: number;
  maxDelay?: number;
  backoffFactor?: number;
  retryCondition?: (error: any) => boolean;
}

const DEFAULT_RETRY_OPTIONS: Required<RetryOptions> = {
  maxRetries: 2,
  baseDelay: 1000, // 1 second
  maxDelay: 5000, // 5 seconds
  backoffFactor: 2,
  retryCondition: (error) => {
    // Retry on network errors and 5xx errors
    if (error.code === 'NETWORK_ERROR' || error.code === 'ECONNABORTED') {
      return true;
    }
    if (error.response?.status >= 500) {
      return true;
    }
    return false;
  }
};

/**
 * Retry function with exponential backoff
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const opts = { ...DEFAULT_RETRY_OPTIONS, ...options };
  let lastError: any;

  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    try {
      const result = await fn();
      return result;
    } catch (error) {
      lastError = error;

      // Don't retry if this is the last attempt or error doesn't meet retry condition
      if (attempt === opts.maxRetries || !opts.retryCondition(error)) {
        throw error;
      }

      // Calculate delay with exponential backoff
      const delay = Math.min(
        opts.baseDelay * Math.pow(opts.backoffFactor, attempt),
        opts.maxDelay
      );

      console.warn(`API call failed (attempt ${attempt + 1}/${opts.maxRetries + 1}), retrying in ${delay}ms:`, (error as Error).message);

      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}

/**
 * Create a wrapped API function with retry logic
 */
export function createRetryableApiFunction<T extends any[], R>(
  fn: (...args: T) => Promise<R>,
  options: RetryOptions = {}
) {
  return (...args: T): Promise<R> => {
    return withRetry(() => fn(...args), options);
  };
}