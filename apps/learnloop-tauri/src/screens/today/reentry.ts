import type { QueueSnapshot, ReentrySummaryDto } from "../../api/dto";

/**
 * How many refreshers the welcome-back panel names. Owner decision P6: re-entry
 * is a small automatic session, so the sidecar caps the Today queue at the
 * summary's refresher count and reports the cap. When it did, the panel names
 * what that queue actually serves, so the number shown and the session can never
 * disagree (daily-loop audit 2026-10-11). Until that queue is known, the summary.
 */
export function reentryRefreshers(summary: ReentrySummaryDto, queue: QueueSnapshot | null): number {
  if (queue == null || queue.reentryRefresherCap == null) return summary.refresherCount;
  return queue.sections.reduce((total, section) => total + section.items.length, 0);
}

/** The panel's session line, or null when no refresher will be served. */
export function reentryRefresherLine(refreshers: number): string | null {
  if (refreshers <= 0) return null;
  return `Your best next session: ${refreshers} refresher${refreshers === 1 ? "" : "s"}.`;
}
