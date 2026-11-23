// A paused desk window (offscreen, hidden, a preview) starts no background work and reads no job; back on
// screen it goes on with the same job rather than starting another (spec §3.6's lifecycle contract).
// One test per kind of producer: a discovery started on open, a job read in a loop, a timed re-read.
import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import { DIRECT_HUB, WindowScope, useWhenLive, type WindowState } from "../desks/lifecycle";
import type { ReaderCueDiscoveryDto, ReaderPromptContractDto } from "../../api/dto";

const api = vi.hoisted(() => ({
  readerCueDiscovery: vi.fn(), readerCueDiscoveryJob: vi.fn(), readerLibraryJob: vi.fn(), readerLibraryJobCancel: vi.fn(), readerLibraryAsk: vi.fn(),
  readerRecap: vi.fn(), readerRecapEvent: vi.fn(), readerWrapUp: vi.fn(),
}));
vi.mock("../../api/client", () => ({ api }));

import { useCueDiscovery, DISCOVERY_POLL_MS } from "./useCueDiscovery";
import { JOB_POLL_MS, useLibraryAsk } from "./useLibraryAsk";

let windowState: WindowState = "active";
function Scope({ children }: { children: ReactNode }) {
  return <WindowScope lifecycle={{ windowId: "w1", state: windowState }} hub={DIRECT_HUB}>{children}</WindowScope>;
}

async function advance(ms: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.resetAllMocks();
  windowState = "active";
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

it("the live wait resolves at once when not paused, and on the window's return when paused", async () => {
  windowState = "hidden";
  const { result, rerender } = renderHook(() => useWhenLive(), { wrapper: Scope });
  let resolved = false;
  void result.current().then(() => { resolved = true; });
  await advance(10_000);
  expect(resolved).toBe(false);
  windowState = "visible";
  rerender();
  await advance(0);
  expect(resolved).toBe(true);
});

const DISCOVERY = { targetsKey: "t1", targetsPending: false } as unknown as ReaderCueDiscoveryDto;

it("an offscreen source starts no cue discovery until it is on screen", async () => {
  api.readerCueDiscovery.mockResolvedValue({ jobId: "j1", state: "pending" });
  api.readerCueDiscoveryJob.mockResolvedValue({ jobId: "j1", state: "pending" });
  windowState = "offscreen";
  const { rerender } = renderHook(() => useCueDiscovery({ extractionId: "ext1", discovery: DISCOVERY, offline: false, reloadGuidePlan: async () => undefined }), { wrapper: Scope });
  await advance(DISCOVERY_POLL_MS[0] * 4);
  expect(api.readerCueDiscovery).not.toHaveBeenCalled();
  windowState = "active";
  rerender();
  await advance(0);
  expect(api.readerCueDiscovery).toHaveBeenCalledTimes(1);
  // Hidden again: the running job is not read while hidden, and is read again (the same job) after.
  await advance(DISCOVERY_POLL_MS[0]);
  const reads = api.readerCueDiscoveryJob.mock.calls.length;
  windowState = "hidden";
  rerender();
  await advance(DISCOVERY_POLL_MS[3] * 3);
  expect(api.readerCueDiscoveryJob.mock.calls.length).toBe(reads);
  windowState = "visible";
  rerender();
  await advance(DISCOVERY_POLL_MS[3]);
  expect(api.readerCueDiscoveryJob.mock.calls.length).toBeGreaterThan(reads);
  expect(api.readerCueDiscovery).toHaveBeenCalledTimes(1);
  expect(new Set(api.readerCueDiscoveryJob.mock.calls.map(([input]) => (input as { jobId: string }).jobId))).toEqual(new Set(["j1"]));
});

it("a library job is not read while its window is hidden, and the same job is read once it is back", async () => {
  api.readerLibraryAsk.mockResolvedValue({ jobId: "lj1", kind: "ask", askId: "la_1", state: "pending", result: null });
  api.readerLibraryJob.mockResolvedValue({ jobId: "lj1", kind: "ask", askId: "la_1", state: "pending", result: null });
  api.readerLibraryJobCancel.mockResolvedValue({ jobId: "lj1", kind: "ask", askId: "la_1", state: "cancelled", result: null });
  const contract = { libraryAsk: { expandGraph: true, personalizedDefault: true, compare: true } } as unknown as ReaderPromptContractDto;
  const { result, rerender } = renderHook(() => useLibraryAsk({ contract, openSourceId: null, onError: () => undefined }), { wrapper: Scope });
  act(() => result.current.ask({ query: "q", entry: "where_else_explained", extractionId: "ext_a", spanIds: ["a1"], identity: null }));
  await advance(JOB_POLL_MS * 3);
  const reads = api.readerLibraryJob.mock.calls.length;
  expect(reads).toBeGreaterThan(0);
  windowState = "hidden";
  rerender();
  await advance(JOB_POLL_MS * 40);
  // At most the read already waiting when it was hidden.
  expect(api.readerLibraryJob.mock.calls.length).toBeLessThanOrEqual(reads + 1);
  const whileHidden = api.readerLibraryJob.mock.calls.length;
  windowState = "active";
  rerender();
  await advance(JOB_POLL_MS * 3);
  expect(api.readerLibraryJob.mock.calls.length).toBeGreaterThan(whileHidden);
  expect(api.readerLibraryAsk).toHaveBeenCalledTimes(1);
  expect(new Set(api.readerLibraryJob.mock.calls.map(([input]) => (input as { jobId: string }).jobId))).toEqual(new Set(["lj1"]));
});
