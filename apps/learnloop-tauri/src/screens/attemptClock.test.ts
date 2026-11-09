// RE0: the attempt's active clock. A pause or a day's gap adds nothing, resumes sum, and the clock is the Reader's.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";
import {
  attemptActiveSeconds,
  carriedActiveMs,
  forgetActiveMs,
  keepActiveMs,
  openAttemptClock,
  touchAttempt,
  type ActiveStorage
} from "./attemptClock";
import { useAttemptClock } from "./useAttemptClock";
import { VISIT_IDLE_MS, accrueVisit } from "./reader/visitClock";

function memory(): ActiveStorage & { map: Map<string, string> } {
  const map = new Map<string, string>();
  return {
    map,
    getItem: (key) => map.get(key) ?? null,
    setItem: (key, value) => void map.set(key, value),
    removeItem: (key) => void map.delete(key)
  };
}

describe("the attempt's active clock", () => {
  it("is the Reader's visit clock: gaps under the idle threshold are active, longer ones count for nothing", () => {
    const attempt = openAttemptClock(0);
    const visit = { lastActive: 0, active: 0, idle: 0 };
    for (const at of [10_000, 40_000, 40_000 + VISIT_IDLE_MS + 1, 40_000 + VISIT_IDLE_MS + 6_000]) {
      touchAttempt(attempt, at);
      accrueVisit(visit, at);
    }
    expect(attempt.active).toBe(visit.active);
    expect(attemptActiveSeconds(attempt, 40_000 + VISIT_IDLE_MS + 6_000)).toBe(40 + 6);
  });

  it("is unchanged by a pause: a gap past the idle threshold adds nothing, however long", () => {
    const clock = openAttemptClock(0);
    touchAttempt(clock, 30_000);
    const before = attemptActiveSeconds(clock, 30_000);
    // Walked away for forty minutes, then looked at it once.
    expect(attemptActiveSeconds(clock, 30_000 + 40 * 60_000)).toBe(before);
  });

  it("sums across resumes and is unchanged by a day's gap between them", () => {
    const storage = memory();
    const first = openAttemptClock(0, carriedActiveMs(storage, "draft"));
    touchAttempt(first, 20_000);
    keepActiveMs(storage, "draft", first.active);
    // The draft sat closed for a day, then was reopened: the clock restarts at the reopening.
    const day = 24 * 3_600_000;
    const second = openAttemptClock(day, carriedActiveMs(storage, "draft"));
    expect(attemptActiveSeconds(second, day)).toBe(20);
    touchAttempt(second, day + 15_000);
    expect(attemptActiveSeconds(second, day + 15_000)).toBe(35);
  });

  it("reads a missing, corrupt or negative carry as none, and forgets a draft's entry", () => {
    const storage = memory();
    expect(carriedActiveMs(storage, "k")).toBe(0);
    storage.setItem("learnloop.activeMs.k", "not a number");
    expect(carriedActiveMs(storage, "k")).toBe(0);
    storage.setItem("learnloop.activeMs.k", "-5");
    expect(carriedActiveMs(storage, "k")).toBe(0);
    keepActiveMs(storage, "k", 12_000);
    expect(carriedActiveMs(storage, "k")).toBe(12_000);
    forgetActiveMs(storage, "k");
    expect(storage.map.size).toBe(0);
    expect(carriedActiveMs(null, "k")).toBe(0);
  });
});

describe("useAttemptClock", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("carries a draft's active seconds into its next open, counts only touches, and forgets once acknowledged", () => {
    const storage = memory();
    vi.setSystemTime(0);
    const first = renderHook(() => useAttemptClock(storage));
    act(() => first.result.current.open("draft-1"));
    expect(first.result.current.seconds()).toBe(0);
    vi.setSystemTime(25_000);
    act(() => void window.dispatchEvent(new Event("keydown")));
    vi.setSystemTime(25_000 + 3 * VISIT_IDLE_MS);
    expect(first.result.current.seconds()).toBe(25);
    first.unmount();
    expect(carriedActiveMs(storage, "draft-1")).toBe(25_000);

    vi.setSystemTime(25_000 + 24 * 3_600_000);
    const second = renderHook(() => useAttemptClock(storage));
    act(() => second.result.current.open("draft-1"));
    expect(second.result.current.seconds()).toBe(25);
    act(() => second.result.current.forget());
    second.unmount();
    expect(storage.map.size).toBe(0);
  });

  it("starts a draft with no key from zero and writes nothing", () => {
    const storage = memory();
    const turn = renderHook(() => useAttemptClock(storage));
    expect(turn.result.current.seconds()).toBeNull();
    act(() => turn.result.current.open(null));
    expect(turn.result.current.seconds()).toBe(0);
    turn.unmount();
    expect(storage.map.size).toBe(0);
  });
});
