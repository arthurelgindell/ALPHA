/**
 * Retry Utility with Exponential Backoff
 * Translated from: arthur/generators/wan26_api.py
 */

export interface RetryOptions {
  maxRetries?: number;
  initialDelay?: number;
  backoffFactor?: number;
  retryableStatusCodes?: number[];
}

const DEFAULT_OPTIONS: Required<RetryOptions> = {
  maxRetries: 3,
  initialDelay: 1000, // ms
  backoffFactor: 2.0,
  retryableStatusCodes: [429, 500, 502, 503, 504],
};

/**
 * Execute a function with exponential backoff retry logic
 *
 * @param fn - Async function to execute
 * @param options - Retry configuration
 * @returns Promise resolving to function result
 * @throws Last error after all retries exhausted
 *
 * @example
 * ```typescript
 * const result = await retry(
 *   () => fetch("https://api.example.com/data"),
 *   { maxRetries: 3, initialDelay: 1000 }
 * );
 * ```
 */
export async function retry<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  let delay = opts.initialDelay;
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      if (attempt < opts.maxRetries) {
        console.warn(
          `Attempt ${attempt + 1} failed: ${lastError.message}. ` +
          `Retrying in ${delay}ms...`
        );
        await Bun.sleep(delay);
        delay *= opts.backoffFactor;
      } else {
        console.error(
          `Failed after ${opts.maxRetries + 1} attempts: ${lastError.message}`
        );
      }
    }
  }

  throw lastError ?? new Error("Retry failed");
}

/**
 * Retry fetch requests with exponential backoff
 *
 * @param url - URL to fetch
 * @param init - Fetch options
 * @param retryOptions - Retry configuration
 * @returns Promise resolving to Response
 *
 * @example
 * ```typescript
 * const response = await retryFetch(
 *   "https://api.example.com/generate",
 *   {
 *     method: "POST",
 *     headers: { "Content-Type": "application/json" },
 *     body: JSON.stringify({ prompt: "..." })
 *   },
 *   { maxRetries: 3 }
 * );
 * ```
 */
export async function retryFetch(
  url: string,
  init?: RequestInit,
  retryOptions: RetryOptions = {}
): Promise<Response> {
  const opts = { ...DEFAULT_OPTIONS, ...retryOptions };
  let delay = opts.initialDelay;
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    try {
      const response = await fetch(url, init);

      // Retry on specified status codes
      if (opts.retryableStatusCodes.includes(response.status)) {
        const errorMessage = `HTTP ${response.status}`;

        if (attempt < opts.maxRetries) {
          // Use longer delay for rate limiting (429)
          const retryDelay = response.status === 429 ? delay * 2 : delay;
          console.warn(
            `${errorMessage}. Retrying in ${retryDelay}ms...`
          );
          await Bun.sleep(retryDelay);
          delay *= opts.backoffFactor;
          continue;
        } else {
          throw new Error(`${errorMessage} after ${opts.maxRetries + 1} attempts`);
        }
      }

      return response;
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      // Network errors (connection refused, timeout, etc.)
      if (
        lastError.message.includes("ECONNREFUSED") ||
        lastError.message.includes("ETIMEDOUT") ||
        lastError.message.includes("fetch failed")
      ) {
        if (attempt < opts.maxRetries) {
          console.warn(
            `Network error: ${lastError.message}. Retrying in ${delay}ms...`
          );
          await Bun.sleep(delay);
          delay *= opts.backoffFactor;
          continue;
        }
      }

      throw lastError;
    }
  }

  throw lastError ?? new Error("Retry failed");
}

/**
 * Create a retry wrapper for any async function
 *
 * @param fn - Function to wrap
 * @param options - Retry options
 * @returns Wrapped function with retry logic
 *
 * @example
 * ```typescript
 * const fetchWithRetry = withRetry(
 *   async (url: string) => fetch(url),
 *   { maxRetries: 3 }
 * );
 *
 * const response = await fetchWithRetry("https://api.example.com");
 * ```
 */
export function withRetry<T extends (...args: unknown[]) => Promise<unknown>>(
  fn: T,
  options: RetryOptions = {}
): T {
  return (async (...args: Parameters<T>) => {
    return retry(() => fn(...args) as Promise<Awaited<ReturnType<T>>>, options);
  }) as T;
}
