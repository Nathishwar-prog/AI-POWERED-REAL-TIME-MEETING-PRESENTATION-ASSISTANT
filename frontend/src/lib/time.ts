/** Small time-formatting helpers for the UI. */

/**
 * Compact relative time, e.g. "now", "12s", "3m", "1h".
 *
 * @param iso - An ISO-8601 timestamp.
 * @param now - Reference time in epoch ms (defaults to `Date.now()`, injectable for tests).
 */
export function timeAgo(iso: string, now: number = Date.now()): string {
  const seconds = Math.max(0, Math.round((now - new Date(iso).getTime()) / 1000));
  if (seconds < 5) return "now";
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.round(minutes / 60);
  return `${hours}h`;
}
