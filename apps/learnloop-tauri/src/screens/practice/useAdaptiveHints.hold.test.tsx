// Adaptive hints H2b, Codex re-review F2: `hold()` before the panel's
// surface is hidden. A poll already reading the job is waited for (its
// delivered hint is kept, never discarded), and a hold whose cancel cannot
// be established resolves false with the request still pending and polled,
// so the screen keeps the answer box (the delivery surface) open. The actual
// hook with deferred fake RPCs; no sidecar.
import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { useAdaptiveHints, type AdaptiveHintsOptions } from "./useAdaptiveHints";

const { api } = vi.hoisted(() => ({ api: {
  requestHint: vi.fn(), hintJob: vi.fn(), cancelHint: vi.fn(), answerDiscriminating: vi.fn(), setHelpStyle: vi.fn()
} }));
vi.mock("../../api/client", () => ({ api }));

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((done, fail) => { resolve = done; reject = fail; });
  return { promise, resolve, reject };
}

const pending = { version: 1, jobId: "hjob_1", state: "pending", result: null };
const delivered = {
  version: 1, jobId: "hjob_1", state: "done",
  result: {
    status: "ready", assistId: "ha_1", hintMd: "Evaluate your CDF.", kind: "next_step", level: 3,
    labels: { origin: "AI-written", kind: "the next step" }, replies: [], picks: [], shown: true
  }
};

function options(onError = vi.fn()): AdaptiveHintsOptions {
  return {
    enabled: true, sessionId: "s1", practiceItemId: "pi", submissionId: () => "k1", answer: () => "F(x)",
    flushDraft: async () => {}, secondsOnItem: () => 5, authoredHints: [], hintsUsed: 0,
    authoredOfferAfterSeconds: 60, onDisabled: vi.fn(), onAuthoredReveal: async () => null, onError
  };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  api.requestHint.mockResolvedValue(pending);
});
afterEach(() => vi.useRealTimers());

async function pollInFlight(read: Promise<unknown>) {
  api.hintJob.mockReturnValueOnce(read);
  const hook = renderHook(() => useAdaptiveHints(options()));
  await act(async () => { await hook.result.current.press(); });
  expect(hook.result.current.pending).toBe(true);
  // The first poll fires and is still reading the job.
  await waitFor(() => expect(api.hintJob).toHaveBeenCalledTimes(1));
  return hook;
}

it("F2: hold waits for a poll in flight and keeps the hint it delivered", async () => {
  const read = deferred<typeof delivered>();
  const hook = await pollInFlight(read.promise);
  api.cancelHint.mockResolvedValue({ version: 1, jobId: "hjob_1", state: "done", cancelled: false, reason: "already_shown" });
  let held: boolean | undefined;
  let settled = false;
  act(() => { void hook.result.current.hold().then((value) => { held = value; settled = true; }); });
  await new Promise((resolve) => setTimeout(resolve, 20));
  expect(settled).toBe(false); // the read is still answering
  expect(api.cancelHint).not.toHaveBeenCalled();
  await act(async () => { read.resolve(delivered); });
  await waitFor(() => expect(settled).toBe(true));
  expect(held).toBe(true);
  expect(hook.result.current.entries.map((entry) => entry.result.hintMd)).toEqual(["Evaluate your CDF."]);
  expect(hook.result.current.pending).toBe(false);
});

it("F2: a hold whose cancel fails resolves false, keeps the request pending and polls it to delivery", async () => {
  const read = deferred<typeof pending>();
  const onError = vi.fn();
  api.hintJob.mockReturnValueOnce(read.promise);
  const hook = renderHook(() => useAdaptiveHints(options(onError)));
  await act(async () => { await hook.result.current.press(); });
  await waitFor(() => expect(api.hintJob).toHaveBeenCalledTimes(1));
  api.cancelHint.mockRejectedValue(new Error("sidecar busy"));
  let holding!: Promise<boolean>;
  act(() => { holding = hook.result.current.hold(); });
  let held: boolean | undefined;
  await act(async () => { read.resolve(pending); held = await holding; });
  expect(held).toBe(false);
  expect(onError).toHaveBeenCalled();
  expect(hook.result.current.pending).toBe(true);
  // The job is delivered server-side by the next read: it is shown, not lost.
  api.hintJob.mockResolvedValue(delivered);
  await waitFor(() => expect(hook.result.current.entries).toHaveLength(1), { timeout: 3000 });
  expect(hook.result.current.pending).toBe(false);
});

it("F2: a delivered read whose response lands after the request was settled is still kept", async () => {
  const read = deferred<typeof delivered>();
  const hook = await pollInFlight(read.promise);
  // The cancel answers first that it was cancelled; the read that was
  // already answering delivers anyway: its hint is shown, never discarded.
  api.cancelHint.mockResolvedValue({ version: 1, jobId: "hjob_1", state: "cancelled", cancelled: true, reason: null });
  let holding!: Promise<boolean>;
  act(() => { holding = hook.result.current.hold(); });
  let held: boolean | undefined;
  await act(async () => { read.resolve(delivered); held = await holding; });
  expect(held).toBe(true);
  expect(hook.result.current.entries).toHaveLength(1);
});
