import { describe, expect, it, vi } from "vitest";
import type { LessonActivityBatch } from "./lessonActivity";
import { createLessonActivity } from "./lessonActivity";
import { VISIT_IDLE_MS } from "./reader/useReaderVisit";

const T0 = Date.parse("2026-11-05T15:00:00.000Z");
const at = (ms: number) => new Date(T0 + ms).toISOString();

function tracker(options: { foreground?: boolean; fail?: boolean } = {}) {
  let clock = T0;
  const batches: LessonActivityBatch[] = [];
  const send = vi.fn(async (batch: LessonActivityBatch) => {
    if (options.fail) throw new Error("sidecar down");
    batches.push(batch);
    return { recorded: batch.intervals.length, enabled: true };
  });
  const t = createLessonActivity({ lessonId: "les1", send, now: () => clock, foreground: options.foreground,
                                   screenSession: "s1" });
  return { t, send, batches, advance: (ms: number) => { clock += ms; } };
}

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0));

describe("the lesson screen's activity intervals", () => {
  it("cuts foreground time at a flush and numbers the intervals from 1", async () => {
    const { t, batches, advance } = tracker();
    advance(30_000);
    t.input();
    advance(30_000);
    t.flush();
    await flushPromises();
    expect(batches).toHaveLength(1);
    expect(batches[0].lessonId).toBe("les1");
    expect(batches[0].intervals).toEqual([
      { screenSession: "s1", seq: 1, startedAt: at(0), endedAt: at(60_000), foreground: true }]);
  });

  it("counts a gap of the Reader's idle length as open but not active, from the last input", async () => {
    const { t, batches, advance } = tracker();
    advance(10_000);
    t.input();
    advance(VISIT_IDLE_MS + 5_000);
    t.input();
    advance(1_000);
    t.stop();
    await flushPromises();
    const intervals = batches.flatMap((batch) => batch.intervals);
    expect(intervals.map((i) => [i.seq, i.startedAt, i.endedAt, i.foreground])).toEqual([
      [1, at(0), at(10_000), true],
      [2, at(10_000), at(10_000 + VISIT_IDLE_MS + 5_000), false],
      [3, at(10_000 + VISIT_IDLE_MS + 5_000), at(10_000 + VISIT_IDLE_MS + 6_000), true],
    ]);
  });

  it("marks hidden time as not foreground and sends when the window hides", async () => {
    const { t, batches, advance } = tracker();
    advance(5_000);
    t.foreground(false);
    await flushPromises();
    expect(batches).toHaveLength(1);
    advance(20_000);
    t.foreground(true);
    advance(5_000);
    t.stop();
    await flushPromises();
    const intervals = batches.flatMap((batch) => batch.intervals);
    expect(intervals.map((i) => [i.startedAt, i.endedAt, i.foreground])).toEqual([
      [at(0), at(5_000), true], [at(5_000), at(25_000), false], [at(25_000), at(30_000), true]]);
  });

  it("never sends the same interval twice when sends succeed, and resends a failed batch", async () => {
    const failing = tracker({ fail: true });
    failing.advance(1_000);
    failing.t.flush();
    await flushPromises();
    failing.advance(1_000);
    failing.t.flush();
    await flushPromises();
    // The first batch failed: the second send carries it again with the new interval.
    const second = failing.send.mock.calls[1][0] as LessonActivityBatch;
    expect(second.intervals.map((i) => i.seq)).toEqual([1, 2]);
  });

  it("sends nothing after it stops", async () => {
    const { t, send, advance } = tracker();
    advance(1_000);
    t.stop();
    await flushPromises();
    advance(1_000);
    t.input();
    t.flush();
    await flushPromises();
    expect(send).toHaveBeenCalledTimes(1);
  });
});
