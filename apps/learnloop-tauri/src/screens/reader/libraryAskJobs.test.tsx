// RW4a Codex re-review (stage reader-rw4a), the library jobs' fencing in
// useLibraryAsk: a cancelled or superseded run's late *failure* is dropped as
// its late result is (F12); leaving the Reader cancels every job still running
// and stops reading them, and a job that starts after the Reader is gone is
// cancelled without being read (F13); a job read never asks the sidecar to
// wait (the hook paces its polls, F11).
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { LibraryAskDto, ReaderPromptContractDto } from "../../api/dto";
import { useLibraryAsk, type LibraryAskRequest } from "./useLibraryAsk";

const { api } = vi.hoisted(() => ({
  api: {
    readerLibraryAsk: vi.fn(), readerLibraryAskNotes: vi.fn(), readerLibraryCompare: vi.fn(), readerLibraryAskTutor: vi.fn(),
    readerLibraryJob: vi.fn(), readerLibraryJobCancel: vi.fn(),
    findPractice: vi.fn(), recordProposalImpressions: vi.fn(), getSpanView: vi.fn(),
  },
}));
vi.mock("../../api/client", () => ({ api }));

const CONTRACT = { libraryAsk: { expandGraph: true, personalizedDefault: true, compare: true } } as unknown as ReaderPromptContractDto;
const REQUEST: LibraryAskRequest = { query: "symmetric matrices", entry: "where_else_explained", extractionId: "ext_a", spanIds: ["a1"] };

const ASK = {
  askId: "la_1", query: "symmetric matrices", entry: "where_else_explained", status: "ok", policy: "reading",
  personalized: true, basis: "keyword", learningObjectIds: [], extractionId: "ext_a", anchorSpanIds: ["a1"],
  hits: [
    { key: "ext_a:a1", extractionId: "ext_a", spanId: "a1", sourceId: "src_a", sourceTitle: "A", section: null, page: null, text: "one",
      role: "definition", group: "Foundation", expansion: null, learningObjectIds: [], authorship: "source", label: "source-authored" },
  ],
  groups: { sources: [], expansions: [] }, expansions: [], expandGraph: true, sourceCount: 1, passageCount: 1,
} as unknown as LibraryAskDto;

function job<T>(jobId: string, kind: string, state: "pending" | "done", result: T | null = null) {
  return { jobId, kind, askId: "la_1", state, result };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

/** A read that answers after a macrotask (a real sidecar round trip). */
function later<T>(value: T): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), 20));
}

function mountHook() {
  return renderHook(() => useLibraryAsk({ contract: CONTRACT, openSourceId: null, onError: vi.fn() }));
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  api.readerLibraryAsk.mockResolvedValue(job("ljob_ask", "ask", "done", ASK));
  api.readerLibraryAskNotes.mockResolvedValue(job("ljob_notes", "notes", "done", { askId: "la_1", status: "judged", notes: [], order: [] }));
  api.readerLibraryJobCancel.mockResolvedValue(job("ljob_x", "notes", "pending"));
});
afterEach(() => { cleanup(); });

it("a cancelled tutor request's late failure never replaces the next answer (F12)", async () => {
  const hook = mountHook();
  act(() => hook.result.current.ask(REQUEST));
  await waitFor(() => expect(hook.result.current.state?.ask.phase).toBe("landed"));
  act(() => hook.result.current.togglePin("ext_a:a1"));
  const old = deferred<unknown>();
  api.readerLibraryAskTutor.mockResolvedValueOnce(job("ljob_t1", "tutor", "pending"));
  api.readerLibraryJob.mockReturnValueOnce(old.promise);
  act(() => { void hook.result.current.askTutor("first"); });
  await waitFor(() => expect(api.readerLibraryJob).toHaveBeenCalledWith({ jobId: "ljob_t1" }));
  act(() => hook.result.current.cancelTutor());
  expect(api.readerLibraryJobCancel).toHaveBeenCalledWith({ jobId: "ljob_t1" });
  const answer = { askId: "la_1", eventId: "q2", answerMd: "the second answer", citations: [], groundedKeys: [], droppedPins: [], label: "x", remaining: 4 };
  api.readerLibraryAskTutor.mockResolvedValueOnce(job("ljob_t2", "tutor", "done", answer));
  act(() => { void hook.result.current.askTutor("second"); });
  await waitFor(() => expect(hook.result.current.state?.tutor.phase).toBe("landed"));
  await act(async () => { old.reject(new Error("the old request failed late")); await later(null); });
  expect(hook.result.current.state?.tutor.phase).toBe("landed");
  expect(hook.result.current.state?.tutor.value?.answerMd).toBe("the second answer");
  expect(hook.result.current.state?.tutor.failure).toBeNull();
});

it("a superseded comparison whose start fails late leaves the cancelled state alone (F12)", async () => {
  const hook = mountHook();
  act(() => hook.result.current.ask(REQUEST));
  await waitFor(() => expect(hook.result.current.state?.ask.phase).toBe("landed"));
  const start = deferred<unknown>();
  api.readerLibraryCompare.mockReturnValueOnce(start.promise);
  act(() => { void hook.result.current.compare(); });
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(1));
  act(() => hook.result.current.cancelCompare());
  await act(async () => { start.reject(new Error("late")); await later(null); });
  expect(hook.result.current.state?.compare.phase).toBe("idle");
  expect(hook.result.current.state?.compare.cancelled).toBe(true);
  expect(hook.result.current.state?.compare.failure).toBeNull();
});

it("leaving the Reader cancels a pending job and stops reading it (F13)", async () => {
  api.readerLibraryAskNotes.mockResolvedValue(job("ljob_notes", "notes", "pending"));
  api.readerLibraryJob.mockImplementation(() => later(job("ljob_notes", "notes", "pending")));
  const hook = mountHook();
  act(() => hook.result.current.ask(REQUEST));
  await waitFor(() => expect(api.readerLibraryJob).toHaveBeenCalled());
  // A read never asks the sidecar to wait (F11).
  for (const [input] of api.readerLibraryJob.mock.calls) expect(input).toEqual({ jobId: "ljob_notes" });
  hook.unmount();
  expect(api.readerLibraryJobCancel).toHaveBeenCalledWith({ jobId: "ljob_notes" });
  const reads = api.readerLibraryJob.mock.calls.length;
  await act(async () => { await new Promise((resolve) => setTimeout(resolve, 700)); });
  expect(api.readerLibraryJob.mock.calls.length).toBeLessThanOrEqual(reads + 1);
  const settled = api.readerLibraryJob.mock.calls.length;
  await act(async () => { await new Promise((resolve) => setTimeout(resolve, 700)); });
  expect(api.readerLibraryJob.mock.calls.length).toBe(settled);
});

it("a job that starts after the Reader is gone is cancelled and never read (F13)", async () => {
  const start = deferred<unknown>();
  api.readerLibraryAsk.mockReturnValueOnce(start.promise);
  const hook = mountHook();
  act(() => hook.result.current.ask(REQUEST));
  await waitFor(() => expect(api.readerLibraryAsk).toHaveBeenCalledTimes(1));
  hook.unmount();
  await act(async () => { start.resolve(job("ljob_ask", "ask", "pending")); await later(null); });
  expect(api.readerLibraryJobCancel).toHaveBeenCalledWith({ jobId: "ljob_ask" });
  await act(async () => { await new Promise((resolve) => setTimeout(resolve, 500)); });
  expect(api.readerLibraryJob).not.toHaveBeenCalled();
});

// Reader CA5a Codex review F5: a comparison started from "find this section in
// my other books" stays a comparison of the same pins when its ask is retried
// or the personalization chip runs it again, and never starts the notes.
const PINS = ["ext_a:a1", "ext_b:b7"];
const TABLE = { askId: "la_1", status: "ok", rows: [], exposureEventIds: [] };

it("F5: retrying a failed compare reruns the comparison with the same pins and no notes", async () => {
  api.readerLibraryAsk.mockReset();
  api.readerLibraryAsk
    .mockRejectedValueOnce({ code: "internal", message: "the sidecar hiccuped" })
    .mockResolvedValue(job("ljob_ask", "ask", "done", ASK));
  api.readerLibraryCompare.mockResolvedValue(job("ljob_cmp", "compare", "done", TABLE));
  const hook = mountHook();
  await act(async () => { await hook.result.current.compareWith(REQUEST, PINS); });
  expect(hook.result.current.state?.ask.phase).toBe("failed");
  expect(api.readerLibraryCompare).not.toHaveBeenCalled();
  await act(async () => { hook.result.current.retry(); await later(null); });
  await waitFor(() => expect(hook.result.current.state?.compare.phase).toBe("landed"));
  expect(api.readerLibraryCompare).toHaveBeenCalledTimes(1);
  expect(api.readerLibraryCompare).toHaveBeenCalledWith({ askId: "la_1", pinnedSpanKeys: PINS, openSourceId: null });
  expect(hook.result.current.state?.pinned).toEqual(PINS);
  expect(hook.result.current.state?.intent).toEqual({ kind: "compare", pins: PINS });
  expect(api.readerLibraryAskNotes).not.toHaveBeenCalled();
  expect(hook.result.current.state?.notes.cancelled).toBe(true);
});

it("F5: the personalization chip reruns the comparison, not an ordinary answer with notes", async () => {
  api.readerLibraryCompare.mockResolvedValue(job("ljob_cmp", "compare", "done", TABLE));
  const hook = mountHook();
  await act(async () => { await hook.result.current.compareWith(REQUEST, PINS); });
  await waitFor(() => expect(hook.result.current.state?.compare.phase).toBe("landed"));
  await act(async () => { hook.result.current.setPersonalized(false); await later(null); });
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalledTimes(2));
  expect(api.readerLibraryAsk).toHaveBeenLastCalledWith(expect.objectContaining({ personalized: false }));
  expect(api.readerLibraryCompare).toHaveBeenLastCalledWith({ askId: "la_1", pinnedSpanKeys: PINS, openSourceId: null });
  expect(hook.result.current.state?.pinned).toEqual(PINS);
  expect(api.readerLibraryAskNotes).not.toHaveBeenCalled();
});

it("F5: an ordinary ask's retry is still an ordinary ask (its notes follow)", async () => {
  api.readerLibraryAsk.mockReset();
  api.readerLibraryAsk
    .mockRejectedValueOnce({ code: "internal", message: "hiccup" })
    .mockResolvedValue(job("ljob_ask", "ask", "done", ASK));
  const hook = mountHook();
  await act(async () => { hook.result.current.ask(REQUEST); await later(null); });
  await waitFor(() => expect(hook.result.current.state?.ask.phase).toBe("failed"));
  await act(async () => { hook.result.current.retry(); await later(null); });
  await waitFor(() => expect(api.readerLibraryAskNotes).toHaveBeenCalled());
  expect(api.readerLibraryCompare).not.toHaveBeenCalled();
  expect(hook.result.current.state?.intent).toEqual({ kind: "ask" });
});
