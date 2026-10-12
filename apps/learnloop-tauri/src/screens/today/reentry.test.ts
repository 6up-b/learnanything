import { expect, it } from "vitest";
import type { QueueSnapshot, ReentrySummaryDto, ScheduledItemDto } from "../../api/dto";
import { reentryRefresherLine, reentryRefreshers } from "./reentry";

const summary = (refresherCount: number): ReentrySummaryDto => ({
  show: true, gapDays: 30, thresholdDays: 7, lastEndedAt: "2026-09-11T12:00:00Z",
  solidCount: 4, slippedCount: refresherCount, refresherCount, slippedTop: []
});

const queue = (count: number, cap: number | null): QueueSnapshot => ({
  version: 1, generatedAt: "2026-10-11T12:00:00Z", sessionId: "s1", totalItems: count,
  reentryRefresherCap: cap,
  sections: [{ title: "Due now", items: Array.from({ length: count }, (_, i) => ({ practiceItemId: `pi_${i}` }) as ScheduledItemDto) }]
});

// Daily-loop audit (2026-10-11): the welcome-back panel said "N refreshers" while
// the session served the whole queue. The sidecar now caps the re-entry queue,
// and the panel shows the number of items that queue actually serves.
it("shows the number of refreshers the capped queue serves", () => {
  expect(reentryRefreshers(summary(3), queue(3, 3))).toBe(3);
  // Fewer servable items than slipped facets: the panel names what is served.
  expect(reentryRefreshers(summary(3), queue(2, 3))).toBe(2);
});

it("falls back to the summary until the capped queue is known", () => {
  expect(reentryRefreshers(summary(3), null)).toBe(3);
  expect(reentryRefreshers(summary(3), queue(12, null))).toBe(3);
});

it("claims no refresher session when nothing will be served", () => {
  expect(reentryRefresherLine(0)).toBeNull();
  expect(reentryRefresherLine(1)).toBe("Your best next session: 1 refresher.");
  expect(reentryRefresherLine(4)).toBe("Your best next session: 4 refreshers.");
});
