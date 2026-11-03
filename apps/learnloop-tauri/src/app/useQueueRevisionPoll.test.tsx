// Mobile PR-7 (spec_mobile_tailnet_v1 §3.3, §6.5, G12): the app-level poll. The poll's
// cost is pinned: an idle tick is one token read, no refetch and no session read, and
// nothing runs behind a call in flight. An open answer or Reader holds the refetch, not
// the detection. The phone's bump itself is tested on the Python side
// (tests/test_host_queue_revision.py).
import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { subscribeQueueChanged } from "../queueEvents";
import { REVISION_POLL_MS, sessionMovedFrom, useQueueRevisionPoll, useSessionMoved, type QueueRevisionPollOptions } from "./useQueueRevisionPoll";

const stubs = vi.hoisted(() => ({
  getQueueRevision: vi.fn(),
  getSession: vi.fn()
}));

vi.mock("../api/client", () => ({ api: stubs }));

const OPEN = { vaultRoot: "/vault", sessionId: "ses_1", quiet: false };

function revision(value: number, reloaded?: boolean) {
  return { version: 1, revision: value, updatedAt: null, ...(reloaded ? { reloaded } : {}) };
}

function session(extra: Record<string, unknown> = {}) {
  return {
    version: 1, sessionId: "ses_1", startedAt: "2026-11-03T00:00:00Z", endedAt: null, energy: null,
    sleepQuality: null, availableMinutes: 20, notesMdPath: null, checkpoint: null, ...extra
  };
}

let refetches = 0;
let unsubscribe: () => void = () => undefined;

function mount(options: QueueRevisionPollOptions = OPEN) {
  return renderHook((props: QueueRevisionPollOptions) => useQueueRevisionPoll(props), { initialProps: options });
}

async function tick(times = 1) {
  for (let index = 0; index < times; index += 1) {
    await act(async () => {
      await vi.advanceTimersByTimeAsync(REVISION_POLL_MS);
    });
  }
}

async function settle() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(0);
  });
}

async function focusWindow() {
  await act(async () => {
    window.dispatchEvent(new Event("focus"));
    await vi.advanceTimersByTimeAsync(0);
  });
}

function setVisibility(state: "visible" | "hidden") {
  Object.defineProperty(document, "visibilityState", { configurable: true, get: () => state });
}

beforeEach(() => {
  vi.useFakeTimers();
  refetches = 0;
  unsubscribe = subscribeQueueChanged(() => {
    refetches += 1;
  });
  stubs.getQueueRevision.mockReset().mockResolvedValue(revision(5));
  stubs.getSession.mockReset().mockResolvedValue(session());
  setVisibility("visible");
});

afterEach(() => {
  unsubscribe();
  cleanup();
  vi.useRealTimers();
});

describe("what a tick costs", () => {
  it("reads only the token while nothing changed: no refetch of Today, no session read", async () => {
    mount();
    await settle();
    await tick(10);

    expect(stubs.getQueueRevision).toHaveBeenCalledTimes(11);
    expect(refetches).toBe(0);
    expect(stubs.getSession).not.toHaveBeenCalled();
  });

  it("refetches once per change, and re-reads the open session once", async () => {
    mount();
    await settle();
    stubs.getQueueRevision.mockResolvedValue(revision(6));
    await tick(4);

    expect(refetches).toBe(1);
    expect(stubs.getSession).toHaveBeenCalledTimes(1);
    expect(stubs.getSession).toHaveBeenCalledWith("ses_1");
  });

  it("refetches when the read itself reloaded the vault, on the first read too", async () => {
    stubs.getQueueRevision.mockResolvedValueOnce(revision(5, true));
    mount();
    await settle();
    expect(refetches).toBe(1);
    await tick(2);
    expect(refetches).toBe(1);
  });

  it("never holds a second call behind one in flight (a long grade on the pipe)", async () => {
    let release: (value: unknown) => void = () => undefined;
    stubs.getQueueRevision.mockImplementationOnce(() => new Promise((resolve) => { release = resolve; }));
    mount();
    await settle();
    await tick(20);
    await focusWindow();
    expect(stubs.getQueueRevision).toHaveBeenCalledTimes(1);

    // The focus that came in meanwhile is served when the call returns, once.
    await act(async () => {
      release(revision(5));
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(stubs.getQueueRevision).toHaveBeenCalledTimes(2);
    expect(stubs.getSession).toHaveBeenCalledTimes(1);
  });

  it("keeps polling after a failed read", async () => {
    mount();
    await settle();
    stubs.getQueueRevision.mockRejectedValueOnce({ code: "database_busy", message: "busy", retryable: true });
    await tick();
    expect(refetches).toBe(0);
    stubs.getQueueRevision.mockResolvedValue(revision(6));
    await tick();
    expect(refetches).toBe(1);
  });

  it("sleeps while the window is hidden and reads at once when it comes back", async () => {
    mount();
    await settle();
    setVisibility("hidden");
    await tick(5);
    expect(stubs.getQueueRevision).toHaveBeenCalledTimes(1);

    stubs.getQueueRevision.mockResolvedValue(revision(9));
    setVisibility("visible");
    await act(async () => {
      document.dispatchEvent(new Event("visibilitychange"));
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(stubs.getQueueRevision).toHaveBeenCalledTimes(2);
    expect(refetches).toBe(1);
  });

  it("polls nothing without a vault, and starts from a fresh token for a new one", async () => {
    const { rerender } = mount({ ...OPEN, vaultRoot: null });
    await tick(3);
    expect(stubs.getQueueRevision).not.toHaveBeenCalled();

    rerender(OPEN);
    await settle();
    await tick();
    expect(stubs.getQueueRevision).toHaveBeenCalledTimes(2);

    // Another vault's revision is not a change.
    stubs.getQueueRevision.mockResolvedValue(revision(99));
    rerender({ ...OPEN, vaultRoot: null });
    rerender({ ...OPEN, vaultRoot: "/other" });
    await settle();
    expect(refetches).toBe(0);
  });

  it("stops when the App goes away", async () => {
    const { unmount } = mount();
    await settle();
    unmount();
    await tick(3);
    expect(stubs.getQueueRevision).toHaveBeenCalledTimes(1);
  });
});

describe("when the window regains focus", () => {
  it("reads the token and the session at once, and refetches nothing when nothing changed", async () => {
    mount();
    await settle();
    await focusWindow();

    expect(stubs.getQueueRevision).toHaveBeenCalledTimes(2);
    expect(stubs.getSession).toHaveBeenCalledTimes(1);
    expect(refetches).toBe(0);
  });

  it("refetches when the phone changed something while the window was away", async () => {
    mount();
    await settle();
    stubs.getQueueRevision.mockResolvedValue(revision(6));
    await focusWindow();
    expect(refetches).toBe(1);
  });
});

describe("an open practice answer or Reader", () => {
  it("holds the refetch while quiet and runs it once on leaving", async () => {
    const { rerender } = mount({ ...OPEN, quiet: true });
    await settle();
    stubs.getQueueRevision.mockResolvedValue(revision(6));
    await tick(2);
    stubs.getQueueRevision.mockResolvedValue(revision(7));
    await tick(2);
    expect(refetches).toBe(0);

    rerender({ ...OPEN, quiet: false });
    await settle();
    expect(refetches).toBe(1);

    await tick(3);
    expect(refetches).toBe(1);
  });

  it("does not refetch on leaving when nothing changed", async () => {
    const { rerender } = mount({ ...OPEN, quiet: true });
    await settle();
    await tick(3);
    rerender({ ...OPEN, quiet: false });
    await settle();
    expect(refetches).toBe(0);
  });

  it("holds a reload's refetch too", async () => {
    const { rerender } = mount({ ...OPEN, quiet: true });
    await settle();
    stubs.getQueueRevision.mockResolvedValue(revision(5, true));
    await tick();
    expect(refetches).toBe(0);
    rerender({ ...OPEN, quiet: false });
    await settle();
    expect(refetches).toBe(1);
  });

  it("still detects that the session moved while quiet", async () => {
    const seen = renderHook(() => useSessionMoved());
    mount({ ...OPEN, quiet: true });
    await settle();
    stubs.getQueueRevision.mockResolvedValue(revision(6));
    stubs.getSession.mockResolvedValue(session({ ownerDeviceId: "dev_phone", ownerLabel: "Phone", ownerGeneration: 1 }));
    await tick();

    expect(seen.result.current?.reason).toBe("adopted");
    expect(refetches).toBe(0);
  });
});

describe("session_moved detection", () => {
  it("names the owner of a session a phone adopted, without a restart", async () => {
    const seen = renderHook(() => useSessionMoved());
    mount();
    await settle();
    expect(seen.result.current).toBeNull();

    stubs.getQueueRevision.mockResolvedValue(revision(6));
    stubs.getSession.mockResolvedValue(session({ ownerDeviceId: "dev_phone", ownerLabel: "Phone", ownerGeneration: 1 }));
    await tick();

    expect(seen.result.current).toEqual({ sessionId: "ses_1", reason: "adopted", ownerLabel: "Phone", ownerGeneration: 1 });
  });

  it("clears when the session comes back, and when another session opens", async () => {
    const seen = renderHook(() => useSessionMoved());
    const { rerender } = mount();
    await settle();
    stubs.getSession.mockResolvedValue(session({ ownerDeviceId: "dev_phone", ownerLabel: "Phone", ownerGeneration: 1 }));
    await focusWindow();
    expect(seen.result.current?.reason).toBe("adopted");

    stubs.getSession.mockResolvedValue(session({ ownerDeviceId: null, ownerLabel: "desktop", ownerGeneration: 2 }));
    await focusWindow();
    expect(seen.result.current).toBeNull();

    stubs.getSession.mockResolvedValue(session({ endedAt: "2026-11-03T01:00:00Z" }));
    await focusWindow();
    expect(seen.result.current?.reason).toBe("ended");
    rerender({ ...OPEN, sessionId: "ses_2" });
    await settle();
    expect(seen.result.current).toBeNull();
  });

  it("drops a read that comes back for a session no longer open", async () => {
    const seen = renderHook(() => useSessionMoved());
    let release: (value: unknown) => void = () => undefined;
    stubs.getSession.mockImplementationOnce(() => new Promise((resolve) => { release = resolve; }));
    const { rerender } = mount();
    await settle();
    await focusWindow();
    rerender({ ...OPEN, sessionId: "ses_2" });
    await act(async () => {
      release(session({ ownerDeviceId: "dev_phone", ownerLabel: "Phone", ownerGeneration: 1 }));
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(seen.result.current).toBeNull();
  });

  it("reads no session when none is open", async () => {
    mount({ ...OPEN, sessionId: null });
    await settle();
    stubs.getQueueRevision.mockResolvedValue(revision(6));
    await tick();
    await focusWindow();
    expect(stubs.getSession).not.toHaveBeenCalled();
    expect(refetches).toBe(1);
  });

  it("reads a session with no owner keys as still the desktop's", () => {
    expect(sessionMovedFrom(session() as never)).toBeNull();
  });
});
