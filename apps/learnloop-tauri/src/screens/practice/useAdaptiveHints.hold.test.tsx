// Adaptive hints H2b, Codex re-review F2 and fix round 3's ruling R2:
// `hold()` before the panel's surface is hidden. A poll already reading the
// job is waited for (its delivered hint is kept, never discarded). A job
// whose outcome is unknown (its cancel or a read failed) is never forgotten:
// the hold retries its cancel once, stops every poll and resolves true (the
// learner enters steps), and `resume()` reads it once, so a hint delivered
// meanwhile shows on the answer box and a closed one shows nothing. The
// actual hook with deferred fake RPCs; no sidecar.
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

const failedCancel = () => api.cancelHint.mockRejectedValue(new Error("sidecar busy"));
const closed = {
  version: 1, jobId: "hjob_1", state: "done",
  result: { status: "unavailable", assistId: "ha_1", reason: "submission_complete",
    message: "This answer was already submitted, so the hint was not shown." }
};
const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

it("R2: a hold whose cancel fails keeps the job, stops polling, resolves true, and resume reads it", async () => {
  const onError = vi.fn();
  api.hintJob.mockResolvedValue(pending);
  const hook = renderHook(() => useAdaptiveHints(options(onError)));
  await act(async () => { await hook.result.current.press(); });
  await waitFor(() => expect(api.hintJob).toHaveBeenCalledTimes(1));
  failedCancel();
  let held: boolean | undefined;
  await act(async () => { held = await hook.result.current.hold(); });
  expect(held).toBe(true);
  expect(onError).toHaveBeenCalledTimes(1);
  expect(hook.result.current.pending).toBe(false);
  // In steps: no poll reads the job, so nothing is delivered there.
  const reads = api.hintJob.mock.calls.length;
  await act(async () => { await wait(1300); });
  expect(api.hintJob.mock.calls.length).toBe(reads);
  // Back on the answer box: the retained job is read once and shown.
  api.hintJob.mockResolvedValue(delivered);
  act(() => { hook.result.current.resume(); });
  await waitFor(() => expect(hook.result.current.entries).toHaveLength(1));
  expect(api.hintJob.mock.calls.length).toBe(reads + 1);
});

it("R2: the verify's sequence (cancel fails, a read rejects after delivery, steps again) never loses the job", async () => {
  const onError = vi.fn();
  api.hintJob.mockResolvedValue(pending);
  const hook = renderHook(() => useAdaptiveHints(options(onError)));
  await act(async () => { await hook.result.current.press(); });
  await waitFor(() => expect(api.hintJob).toHaveBeenCalledTimes(1));
  failedCancel();
  let held: boolean | undefined;
  await act(async () => { held = await hook.result.current.hold(); });
  expect(held).toBe(true);
  // Back on the answer box: the read delivers server-side, but its response rejects.
  api.hintJob.mockRejectedValue(new Error("connection reset"));
  await act(async () => { hook.result.current.resume(); await wait(10); });
  expect(hook.result.current.entries).toHaveLength(0);
  // "Work in steps" again: the job is still retained, so its cancel is retried.
  const cancels = api.cancelHint.mock.calls.length;
  await act(async () => { held = await hook.result.current.hold(); });
  expect(held).toBe(true);
  expect(api.cancelHint.mock.calls.length).toBe(cancels + 1);
  expect(api.cancelHint).toHaveBeenLastCalledWith("hjob_1");
  // Back again: it is read and the delivered hint shows on the answer box.
  api.hintJob.mockResolvedValue(delivered);
  act(() => { hook.result.current.resume(); });
  await waitFor(() => expect(hook.result.current.entries.map((entry) => entry.result.hintMd)).toEqual(["Evaluate your CDF."]));
});

it("R2: a retained job whose read answers closed shows nothing", async () => {
  api.hintJob.mockResolvedValue(pending);
  const hook = renderHook(() => useAdaptiveHints(options()));
  await act(async () => { await hook.result.current.press(); });
  await waitFor(() => expect(api.hintJob).toHaveBeenCalledTimes(1));
  failedCancel();
  await act(async () => { await hook.result.current.hold(); });
  // An attempt of the session and item committed meanwhile (in steps).
  api.hintJob.mockResolvedValue(closed);
  await act(async () => { hook.result.current.resume(); await wait(10); });
  expect(hook.result.current.entries).toHaveLength(0);
  expect(hook.result.current.notice).toBeNull();
  // Settled: a later hold has nothing left to cancel.
  const cancels = api.cancelHint.mock.calls.length;
  await act(async () => { await hook.result.current.hold(); });
  expect(api.cancelHint.mock.calls.length).toBe(cancels);
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

it("F11: a resume of a hold a later hold superseded reads nothing; the latest one reads the job", async () => {
  api.hintJob.mockResolvedValue(pending);
  const hook = renderHook(() => useAdaptiveHints(options()));
  await act(async () => { await hook.result.current.press(); });
  await waitFor(() => expect(api.hintJob).toHaveBeenCalledTimes(1));
  failedCancel();
  await act(async () => { await hook.result.current.hold(); });
  const first = hook.result.current.holdGeneration();
  await act(async () => { await hook.result.current.hold(); });
  const reads = api.hintJob.mock.calls.length;
  api.hintJob.mockResolvedValue(delivered);
  await act(async () => { hook.result.current.resume(first); await wait(10); });
  expect(api.hintJob.mock.calls.length).toBe(reads);
  expect(hook.result.current.entries).toHaveLength(0);
  act(() => { hook.result.current.resume(hook.result.current.holdGeneration()); });
  await waitFor(() => expect(hook.result.current.entries).toHaveLength(1));
});

it("F11: a read that answers after a later hold began shows nothing and keeps the job", async () => {
  api.hintJob.mockResolvedValue(pending);
  const hook = renderHook(() => useAdaptiveHints(options()));
  await act(async () => { await hook.result.current.press(); });
  await waitFor(() => expect(api.hintJob).toHaveBeenCalledTimes(1));
  failedCancel();
  await act(async () => { await hook.result.current.hold(); });
  const read = deferred<typeof delivered>();
  api.hintJob.mockReturnValueOnce(read.promise);
  act(() => { hook.result.current.resume(); });
  // Held again before the read answers (steps opened again).
  let holding!: Promise<boolean>;
  act(() => { holding = hook.result.current.hold(); });
  await act(async () => { read.resolve(delivered); await holding; });
  expect(hook.result.current.entries).toHaveLength(0);
  // Back on the answer box: the retained job is read and shown.
  api.hintJob.mockResolvedValue(delivered);
  act(() => { hook.result.current.resume(); });
  await waitFor(() => expect(hook.result.current.entries).toHaveLength(1));
});
