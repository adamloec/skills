/**
 * Formatters shared by every client. Pure: time is injected, so they run anywhere.
 */

const MINUTE_MS = 60_000;
const HOUR_MS = 60 * MINUTE_MS;
const DAY_MS = 24 * HOUR_MS;

/**
 * Describe how long ago an ISO timestamp was, coarsely: "just now", "5m ago", "3h ago", "2d ago".
 *
 * @param iso - ISO-8601 timestamp.
 * @param now - The reference time in epoch milliseconds. Defaults to the current time.
 */
export function relativeTime(iso: string, now: number = Date.now()): string {
  const elapsed = Math.max(0, now - new Date(iso).getTime());
  if (elapsed < MINUTE_MS) return "just now";
  if (elapsed < HOUR_MS) return `${Math.floor(elapsed / MINUTE_MS)}m ago`;
  if (elapsed < DAY_MS) return `${Math.floor(elapsed / HOUR_MS)}h ago`;
  return `${Math.floor(elapsed / DAY_MS)}d ago`;
}
