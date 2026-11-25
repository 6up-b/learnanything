// Ledger R4-G1: a figure request that settles after the Reader closed sets no state.
//
// A build is read, paced, until it ends (useFigures' `run`); a recheck likewise. The
// Reader can close (unmount) while one is in flight: a test's cleanup, the shell
// leaving the Reader, a side pane hidden by a comparison. The request must then end
// as "cancelled" at its next step and set nothing: React's setState on a closed
// component still reads `window.event`, so after a test environment is torn down a
// late state update throws ("window is not defined") as an unhandled rejection.
import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { FIGURE_POLL_MS, useFigures, type FiguresContract } from "./useFigures";

const { api } = vi.hoisted(() => ({
  api: {
    readerFigures: vi.fn(), readerFigureRequest: vi.fn(), readerFigureJob: vi.fn(), readerFigureJobCancel: vi.fn(),
    readerFigureRecheck: vi.fn(), figureManimOptIn: vi.fn(),
  },
}));
vi.mock("../../../api/client", () => ({ api }));

const CONTRACT: FiguresContract = { predictions: false, region: false, revisions: false };
const PENDING = { jobId: "fj1", kind: "figure_build", askId: null, state: "pending", result: null } as const;

beforeEach(() => {
  vi.resetAllMocks();
  api.readerFigures.mockResolvedValue({ figures: [] });
});
afterEach(() => { vi.useRealTimers(); cleanup(); vi.unstubAllGlobals(); });

function mount() {
  return renderHook(() => useFigures({ extractionId: "ext_1", contract: CONTRACT }));
}

/** Run `body` with `window` gone, as after the test environment's teardown. */
async function withoutWindow<T>(body: () => Promise<T>): Promise<T> {
  const saved = Object.getOwnPropertyDescriptor(globalThis, "window");
  expect(saved?.configurable).toBe(true);
  delete (globalThis as { window?: unknown }).window;
  try {
    return await body();
  } finally {
    Object.defineProperty(globalThis, "window", saved!);
  }
}

it("a build whose start fails after the Reader closed ends cancelled and sets nothing", async () => {
  let fail: (error: Error) => void = () => undefined;
  api.readerFigureRequest.mockReturnValue(new Promise((_resolve, reject) => { fail = reject; }));
  const { result, unmount } = mount();
  await act(async () => { await Promise.resolve(); });
  let outcome: Promise<string> = Promise.resolve("");
  act(() => { outcome = result.current.request({ spanIds: ["s1"] }); });
  expect(result.current.pending.map((item) => item.state)).toEqual(["pending"]);
  unmount();
  // Before the fix the catch branch still counted the request live and set its failed line,
  // which throws once `window` is gone (the unhandled rejection of R4-G1).
  await withoutWindow(async () => {
    fail(new Error("the sidecar went away"));
    await expect(outcome).resolves.toBe("cancelled");
  });
});

it("a build still running when the Reader closes is read no more and ends cancelled", async () => {
  vi.useFakeTimers();
  api.readerFigureRequest.mockResolvedValue(PENDING);
  api.readerFigureJob.mockResolvedValue(PENDING);
  const { result, unmount } = mount();
  await act(async () => { await Promise.resolve(); });
  let outcome: Promise<string> = Promise.resolve("");
  act(() => { outcome = result.current.request({ spanIds: ["s1"] }); });
  // One read while open: the loop is running.
  await act(async () => { await vi.advanceTimersByTimeAsync(FIGURE_POLL_MS); });
  expect(api.readerFigureJob).toHaveBeenCalledTimes(1);
  unmount();
  await vi.advanceTimersByTimeAsync(FIGURE_POLL_MS * 4);
  expect(api.readerFigureJob).toHaveBeenCalledTimes(1);
  await expect(outcome).resolves.toBe("cancelled");
  // The build itself is not cancelled: it lands with the figures when the source is opened again.
  expect(api.readerFigureJobCancel).not.toHaveBeenCalled();
});

it("a recheck still running when the Reader closes is read no more", async () => {
  vi.useFakeTimers();
  api.readerFigureRecheck.mockResolvedValue({ jobId: "rj1", state: "pending" });
  api.readerFigureJob.mockResolvedValue({ jobId: "rj1", state: "pending" });
  const { result, unmount } = mount();
  await act(async () => { await Promise.resolve(); });
  act(() => {
    result.current.recheck?.({ figureId: "fig_1" } as Parameters<NonNullable<typeof result.current.recheck>>[0]);
  });
  await act(async () => { await vi.advanceTimersByTimeAsync(FIGURE_POLL_MS); });
  expect(api.readerFigureJob).toHaveBeenCalledTimes(1);
  unmount();
  await vi.advanceTimersByTimeAsync(FIGURE_POLL_MS * 4);
  expect(api.readerFigureJob).toHaveBeenCalledTimes(1);
  expect(api.readerFigures).toHaveBeenCalledTimes(1); // the source's first read only: no refresh after closing
});

it("the Manim opt-in's answer arriving after the Reader closed sets nothing", async () => {
  let answer: (value: { manimOptIn: "standing" }) => void = () => undefined;
  api.figureManimOptIn.mockReturnValue(new Promise((resolve) => { answer = resolve; }));
  const { result, unmount } = renderHook(() => useFigures({
    extractionId: "ext_1", contract: { ...CONTRACT, rich: { manimOptIn: "ask" } },
  }));
  await act(async () => { await Promise.resolve(); });
  act(() => { result.current.answerManimOptIn("allow"); });
  unmount();
  const unhandled: unknown[] = [];
  const hear = (reason: unknown) => { unhandled.push(reason); };
  // Node's own event (the app's typings declare only `process.env`).
  const node = process as unknown as { on(event: string, listener: (reason: unknown) => void): void; off(event: string, listener: (reason: unknown) => void): void };
  node.on("unhandledRejection", hear);
  try {
    await withoutWindow(async () => {
      answer({ manimOptIn: "standing" });
      // A late setState would throw here and surface as an unhandled rejection.
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    await new Promise((resolve) => setTimeout(resolve, 0));
  } finally {
    node.off("unhandledRejection", hear);
  }
  expect(unhandled).toEqual([]);
});
