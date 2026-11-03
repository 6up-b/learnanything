// Mobile PR-7 (spec_mobile_tailnet_v1 §3.3, §6.5, G12): the app-level poll. The poll's
// cost is pinned: an idle tick is one token read, no refetch and no session read, and
// nothing runs behind a call in flight. A window's return reads the token and the session
// and refetches nothing at an unchanged token (orchestrator ruling R1). An open answer or
// Reader holds the refetch, not the detection. The phone's bump itself is tested on the Python side
// (tests/test_host_queue_revision.py).
import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { subscribeQueueChanged } from "../queueEvents";
import {
  REVISION_POLL_MS,
  revisionPollHeld,
  sessionMovedFrom,
  useQueueRevisionPoll,
  useSessionMoved,
  type QueueRevisionPollOptions
} from "./useQueueRevisionPoll";

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

    // The focus that came in meanwhile is served when the call returns, once: the
    // session read runs after it, so no second token read.
    await act(async () => {
      release(revision(5));
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(stubs.getQueueRevision).toHaveBeenCalledTimes(1);
    expect(stubs.getSession).toHaveBeenCalledTimes(1);
    expect(refetches).toBe(0);
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
  it("reads the token and the session and refetches nothing at an unchanged token (R1)", async () => {
    mount();
    await settle();
    await focusWindow();

    expect(stubs.getQueueRevision).toHaveBeenCalledTimes(2);
    expect(stubs.getSession).toHaveBeenCalledTimes(1);
    expect(refetches).toBe(0);

    await tick(3);
    expect(refetches).toBe(0);
    expect(stubs.getSession).toHaveBeenCalledTimes(1);
  });

  it("200 returns at an unchanged revision: no invalidation, and every session read runs (R1)", async () => {
    mount();
    await settle();
    for (let index = 0; index < 200; index += 1) await focusWindow();

    expect(refetches).toBe(0);
    expect(stubs.getQueueRevision).toHaveBeenCalledTimes(201);
    expect(stubs.getSession).toHaveBeenCalledTimes(200);
  });

  it("counts visibility and focus arriving together as one return", async () => {
    mount();
    await settle();
    await act(async () => {
      document.dispatchEvent(new Event("visibilitychange"));
      window.dispatchEvent(new Event("focus"));
      await vi.advanceTimersByTimeAsync(0);
    });

    expect(refetches).toBe(0);
    expect(stubs.getQueueRevision).toHaveBeenCalledTimes(2);
    expect(stubs.getSession).toHaveBeenCalledTimes(1);
  });

  it("owes nothing on leaving after a return while quiet", async () => {
    const { rerender } = mount({ ...OPEN, quiet: true });
    await settle();
    await focusWindow();
    expect(stubs.getSession).toHaveBeenCalledTimes(1);

    rerender({ ...OPEN, quiet: false });
    await settle();
    expect(refetches).toBe(0);
  });

  it("keeps a return's session read through a failed token read, without looping", async () => {
    mount();
    await settle();
    stubs.getQueueRevision.mockRejectedValueOnce({ code: "database_busy", message: "busy", retryable: true });
    await focusWindow();
    expect(stubs.getSession).not.toHaveBeenCalled();
    expect(stubs.getQueueRevision).toHaveBeenCalledTimes(2);

    await tick();
    expect(stubs.getSession).toHaveBeenCalledTimes(1);
    expect(refetches).toBe(0);
    expect(stubs.getQueueRevision).toHaveBeenCalledTimes(3);
  });

  it("refetches on a return only for a read that reloaded the vault (a job landed)", async () => {
    mount();
    await settle();
    stubs.getQueueRevision.mockResolvedValueOnce(revision(5, true));
    await focusWindow();
    expect(refetches).toBe(1);
  });

  it("does not refetch on a return that happens while nothing is open", async () => {
    mount({ ...OPEN, vaultRoot: null });
    await settle();
    await focusWindow();
    expect(refetches).toBe(0);
    expect(stubs.getQueueRevision).not.toHaveBeenCalled();
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

describe("while held (ruling R2)", () => {
  it("asks the read not to reload, and the first read after the hold may", async () => {
    const { rerender } = mount({ ...OPEN, quiet: true });
    await settle();
    await tick(2);
    expect(stubs.getQueueRevision.mock.calls).toEqual([[{ holdReload: true }], [{ holdReload: true }], [{ holdReload: true }]]);

    rerender({ ...OPEN, quiet: false });
    await settle();
    expect(stubs.getQueueRevision).toHaveBeenCalledTimes(4);
    expect(stubs.getQueueRevision).toHaveBeenLastCalledWith({});
  });

  it("a held change and the reload the hold kept back are one refetch, after the reload", async () => {
    const { rerender } = mount({ ...OPEN, quiet: true });
    await settle();
    stubs.getQueueRevision.mockResolvedValue(revision(6));
    await tick(2);
    expect(refetches).toBe(0);

    let refetchesAtReload = -1;
    stubs.getQueueRevision.mockImplementation(async () => {
      refetchesAtReload = refetches;
      return revision(6, true);
    });
    rerender({ ...OPEN, quiet: false });
    await settle();
    expect(refetchesAtReload).toBe(0);
    expect(refetches).toBe(1);

    stubs.getQueueRevision.mockResolvedValue(revision(6));
    await tick(3);
    expect(refetches).toBe(1);
  });

  it("a read in flight when the hold lifts is followed by one that may reload", async () => {
    let release: (value: unknown) => void = () => undefined;
    const { rerender } = mount({ ...OPEN, quiet: true });
    await settle();
    stubs.getQueueRevision.mockImplementationOnce(() => new Promise((resolve) => { release = resolve; }));
    await tick();
    expect(stubs.getQueueRevision).toHaveBeenLastCalledWith({ holdReload: true });

    rerender({ ...OPEN, quiet: false });
    await settle();
    expect(stubs.getQueueRevision).toHaveBeenCalledTimes(2);

    stubs.getQueueRevision.mockResolvedValueOnce(revision(5, true));
    await act(async () => {
      release(revision(5));
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(stubs.getQueueRevision).toHaveBeenCalledTimes(3);
    expect(stubs.getQueueRevision).toHaveBeenLastCalledWith({});
    expect(refetches).toBe(1);
  });

  it("a failed read on leaving keeps the held refetch for the next tick", async () => {
    const { rerender } = mount({ ...OPEN, quiet: true });
    await settle();
    stubs.getQueueRevision.mockResolvedValue(revision(6));
    await tick();
    stubs.getQueueRevision.mockRejectedValueOnce({ code: "database_busy", message: "busy", retryable: true });
    rerender({ ...OPEN, quiet: false });
    await settle();
    expect(refetches).toBe(0);

    await tick();
    expect(refetches).toBe(1);
  });

  it("a hold that begins during a plain read keeps that read's reload for the leaving", async () => {
    let release: (value: unknown) => void = () => undefined;
    const { rerender } = mount();
    await settle();
    stubs.getQueueRevision.mockImplementationOnce(() => new Promise((resolve) => { release = resolve; }));
    await tick();
    rerender({ ...OPEN, quiet: true });
    await act(async () => {
      release(revision(5, true));
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(refetches).toBe(0);

    rerender({ ...OPEN, quiet: false });
    await settle();
    expect(refetches).toBe(1);
  });
});

describe("where the hold lifts: where Today's own poll ran (ruling R2)", () => {
  const TODAY = {
    tab: "today", todayStage: "queue", simple: false,
    examOpen: false, calibrationOpen: false, lessonOpen: false, goldenRunOpen: false
  };

  it("lifts on Today's list", () => {
    expect(revisionPollHeld(TODAY)).toBe(false);
    expect(revisionPollHeld({ ...TODAY, simple: true })).toBe(false);
  });

  it("the simple shell's Start is Today with no session; the classic shell's is its own screen", () => {
    expect(revisionPollHeld({ ...TODAY, tab: "start", simple: true })).toBe(false);
    expect(revisionPollHeld({ ...TODAY, tab: "start", simple: false })).toBe(true);
  });

  it.each(["reader", "library", "graph", "ingest", "proposals", "registry", "maintain", "golden"])("holds on %s", (tab) => {
    expect(revisionPollHeld({ ...TODAY, tab })).toBe(true);
    expect(revisionPollHeld({ ...TODAY, tab, simple: true })).toBe(true);
  });

  it.each(["practice", "feedback", "blockReview"])("holds on Today's %s stage, which replaces the list", (todayStage) => {
    expect(revisionPollHeld({ ...TODAY, todayStage })).toBe(true);
  });

  it.each(["examOpen", "calibrationOpen", "lessonOpen", "goldenRunOpen"])("holds with %s over Today", (overlay) => {
    expect(revisionPollHeld({ ...TODAY, [overlay]: true })).toBe(true);
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

  it("keeps a failed read owed: the next tick at the same revision reads again (Codex F5)", async () => {
    const seen = renderHook(() => useSessionMoved());
    mount();
    await settle();
    stubs.getQueueRevision.mockResolvedValue(revision(6));
    stubs.getSession.mockRejectedValueOnce({ code: "database_busy", message: "busy", retryable: true });
    await tick();
    expect(stubs.getSession).toHaveBeenCalledTimes(1);
    expect(seen.result.current).toBeNull();

    stubs.getSession.mockResolvedValue(session({ ownerDeviceId: "dev_phone", ownerLabel: "Phone", ownerGeneration: 1 }));
    await tick();
    expect(stubs.getSession).toHaveBeenCalledTimes(2);
    expect(seen.result.current?.reason).toBe("adopted");

    // Paid off: nothing more at a stable revision.
    await tick(3);
    expect(stubs.getSession).toHaveBeenCalledTimes(2);
    expect(refetches).toBe(1);
  });

  it("retries a failing read once a tick, never in a loop and never beside a read in flight", async () => {
    mount();
    await settle();
    stubs.getQueueRevision.mockResolvedValue(revision(6));
    stubs.getSession.mockRejectedValue({ code: "database_busy", message: "busy", retryable: true });
    await tick();
    expect(stubs.getSession).toHaveBeenCalledTimes(1);
    await tick(2);
    expect(stubs.getSession).toHaveBeenCalledTimes(3);

    let release: (value: unknown) => void = () => undefined;
    stubs.getSession.mockImplementationOnce(() => new Promise((resolve) => { release = resolve; }));
    await tick(4);
    expect(stubs.getSession).toHaveBeenCalledTimes(4);
    await act(async () => {
      release(session());
      await vi.advanceTimersByTimeAsync(0);
    });
    await tick(2);
    expect(stubs.getSession).toHaveBeenCalledTimes(4);
  });

  it("reads a session with no owner keys as still the desktop's", () => {
    expect(sessionMovedFrom(session() as never)).toBeNull();
  });
});
