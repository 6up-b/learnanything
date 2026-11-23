// The one client poller (spec §3.6): one cadence, coalesced requests per job, backoff on failure, a
// paused window's polls skipped, and the timer gone when nothing is polled.
import { describe, expect, it, vi } from "vitest";
import { Poller } from "./poller";

function manual() {
  let tick: (() => void) | null = null;
  const poller = new Poller({
    tickMs: 1000,
    setInterval: (fn) => {
      tick = fn;
      return 1;
    },
    clearInterval: () => {
      tick = null;
    },
  });
  return { poller, running: () => tick !== null };
}

describe("the poller", () => {
  it("coalesces two registrations of one job into one request per tick", async () => {
    const { poller } = manual();
    const request = vi.fn(async () => ({ status: "running" }));
    const a = vi.fn();
    const b = vi.fn();
    poller.register({ key: "job:1", request, onResult: a });
    poller.register({ key: "job:1", request, onResult: b });
    await poller.tick();
    expect(request).toHaveBeenCalledTimes(1);
    expect(a).toHaveBeenCalledWith({ status: "running" });
    expect(b).toHaveBeenCalledWith({ status: "running" });
  });

  it("stops a job when a listener says it is done, and stops the timer with nothing left", async () => {
    const { poller, running } = manual();
    const request = vi.fn(async () => "done");
    poller.register({ key: "job:2", request, onResult: () => ({ done: true }) });
    expect(running()).toBe(true);
    await poller.tick();
    await poller.tick();
    expect(request).toHaveBeenCalledTimes(1);
    expect(poller.size).toBe(0);
    expect(running()).toBe(false);
  });

  it("backs off after failures (one tick, then two, then four) and resumes on success", async () => {
    const { poller } = manual();
    let fail = true;
    const request = vi.fn(async () => {
      if (fail) throw new Error("down");
      return "ok";
    });
    const onError = vi.fn();
    poller.register({ key: "job:3", request, onResult: () => undefined, onError });
    const calls: number[] = [];
    for (let tick = 1; tick <= 8; tick += 1) {
      const before = request.mock.calls.length;
      await poller.tick();
      if (request.mock.calls.length > before) calls.push(tick);
    }
    // Requests at ticks 1, 3 (after skipping 1), 6 (after skipping 2).
    expect(calls).toEqual([1, 3, 6]);
    fail = false;
    for (let tick = 9; tick <= 14; tick += 1) await poller.tick();
    const afterRecovery = request.mock.calls.length;
    await poller.tick();
    expect(request.mock.calls.length).toBe(afterRecovery + 1);
    expect(onError).toHaveBeenCalled();
  });

  it("skips the polls of a paused window until it is shown again", async () => {
    const { poller } = manual();
    const request = vi.fn(async () => "x");
    poller.register({ key: "job:4", request, onResult: () => undefined, owner: "w1" });
    poller.setOwnerPaused("w1", true);
    await poller.tick();
    expect(request).not.toHaveBeenCalled();
    poller.setOwnerPaused("w1", false);
    await poller.tick();
    expect(request).toHaveBeenCalledTimes(1);
  });

  it("unregistering the last listener removes the job", () => {
    const { poller, running } = manual();
    const off = poller.register({ key: "job:5", request: async () => 1, onResult: () => undefined });
    off();
    expect(poller.size).toBe(0);
    expect(running()).toBe(false);
  });
});
