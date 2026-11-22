// A section's end finishes it (algorithm tag mvp-0.63, docs/reviews/algorithm-mvp-0.63.md), on the desktop's hook:
// the save that carries the end (the learner's own reading reached the section's last passage) is what finishes it, by
// the backend's answer; the Reader never shows a finished section the backend does not have (a failed save, a restart,
// a tag below mvp-0.63 that finishes nothing by its end); a restore at the end sends no end; closing a quick check and
// choosing its idea's fate are passed on as what they are; a check the learner has open stays open when its section
// finishes under it.
import { act, cleanup, renderHook } from "@testing-library/react";
import { createRef, useState } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReaderGuidePlanDto, ReaderGuideSectionDto, ReaderRenderViewDto } from "../../api/dto";
import { readerRenderViewFixture } from "../../fixtures/readerRenderView";
import { finishOf, SEEN_REPORT_MS, useReadingProgress, type ReadingProgressInput } from "./useReadingProgress";

const api = vi.hoisted(() => ({
  readerLogActivity: vi.fn(), readerNoteReadingProgress: vi.fn(), readerAuthorSectionQuestion: vi.fn(),
  readerGuidePlan: vi.fn(), readerMarkSectionProgress: vi.fn(), readerSavedPlace: vi.fn(),
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("./guidePlan", () => ({ useGuideDiagnosisRefresh: () => undefined }));

// Eight passages: section u1 is s0-s4, section u2 is s5-s7.
const SPANS = ["s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7"];
const view: ReaderRenderViewDto = {
  ...readerRenderViewFixture,
  blocks: SPANS.map((spanId) => ({ ...readerRenderViewFixture.blocks[1], spanId, displayNodeId: `node-${spanId}`, markdown: `Passage ${spanId}.` })),
};

function section(id: string, spanIds: string[], question: unknown = null): ReaderGuideSectionDto {
  return {
    id, label: `Section ${id}`, startSpanId: spanIds[0], endSpanId: spanIds[spanIds.length - 1], spanIds,
    question, suggestedPassages: [],
  } as unknown as ReaderGuideSectionDto;
}

const CHECK = { placement: "auto_authored", authoredQuestionId: "aq1", prompt: "Why?", expectedAnswer: "Because.", reason: "r", spanIds: ["s2"], readingPhase: "after_section" };
const PLAN: ReaderGuidePlanDto = {
  version: 1, sourceId: view.sourceId, extractionId: view.extractionId, personalized: false, selectionBasis: "",
  goalContext: null, sections: [section("u1", SPANS.slice(0, 5), CHECK), section("u2", SPANS.slice(5))],
};
const FINISHED = (extra: Record<string, unknown> = {}) => ({
  progress: { completedAt: "2026-11-21T10:00:00Z" }, enqueuedGeneration: true, batchId: "batch_1", ...extra,
});
const UNFINISHED = { progress: { completedAt: null }, enqueuedGeneration: false, batchId: null };

function progressInput(overrides: Partial<ReadingProgressInput> = {}): ReadingProgressInput {
  return {
    render: view, offline: false, blocks: view.blocks, guidePlan: PLAN, setGuidePlan: vi.fn(), guideLoading: false,
    pdfView: null, pdfViewPending: false, surface: "text", watch: null, watchLoading: false, mode: "anchor",
    inquiry: true, muted: false, activeSpan: null, setActiveSpan: vi.fn(), bodyRef: createRef<HTMLDivElement>(),
    railRef: createRef<HTMLDivElement>(), paneRef: createRef(), watchRef: createRef(), noteProactive: vi.fn(() => true),
    showGuideRail: vi.fn(), ...overrides,
  };
}

function useHarness(overrides: Partial<ReadingProgressInput> = {}) {
  const [activeSpan, setActiveSpan] = useState<string | null>(null);
  return useReadingProgress(progressInput({ activeSpan, setActiveSpan, ...overrides }));
}

type Report = { sectionId: string; reachedEnd?: boolean; seenSpanIds?: string[] };
const ends = () => api.readerNoteReadingProgress.mock.calls.map(([input]) => input as Report).filter((one) => one.reachedEnd);

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "requestAnimationFrame", "cancelAnimationFrame", "Date"] });
  for (const fn of Object.values(api)) fn.mockReset();
  api.readerNoteReadingProgress.mockResolvedValue(UNFINISHED);
  api.readerMarkSectionProgress.mockResolvedValue(UNFINISHED);
  api.readerAuthorSectionQuestion.mockResolvedValue({ status: "exists" });
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

type Harness = { current: ReturnType<typeof useReadingProgress> };

async function scrollByHand(result: Harness) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(2000);
    result.current.noteUserScroll();
    result.current.onReadingScroll();
    await vi.advanceTimersByTimeAsync(20);
  });
}

async function markerAt(result: Harness, spanId: string) {
  await act(async () => {
    result.current.setReadingSpan(spanId);
    await vi.advanceTimersByTimeAsync(20);
  });
}

async function saved(ms = SEEN_REPORT_MS + 50) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

async function readToTheEndOfU1(result: Harness) {
  act(() => result.current.placeAtOpen(view.sourceId, "s0", null));
  await scrollByHand(result);
  for (const spanId of ["s1", "s2", "s3", "s4"]) await markerAt(result, spanId);
  await saved();
}

it("reading to the section's end finishes it once the backend's answer says so, with what the finish started", async () => {
  api.readerNoteReadingProgress.mockImplementation(async (input: Report) => (input.reachedEnd ? FINISHED() : UNFINISHED));
  const { result } = renderHook(() => useHarness());
  await readToTheEndOfU1(result);
  expect(ends().map((one) => one.sectionId)).toEqual(["u1"]);
  expect(result.current.completedSections).toEqual(["u1"]);
  expect(result.current.sectionFinishes).toEqual({ u1: "writing" });
  // Never a second completion of its own: the end went with the save, and no completion call was made.
  expect(api.readerMarkSectionProgress).not.toHaveBeenCalled();
});

it("below the tag an end finishes nothing: the Reader shows what the backend answered", async () => {
  const { result } = renderHook(() => useHarness());
  await readToTheEndOfU1(result);
  expect(ends().map((one) => one.sectionId)).toEqual(["u1"]);
  expect(result.current.completedSections).toEqual([]);
});

it("a skim to the bottom by the learner's own scrolling is an end; a restore at the end is not", async () => {
  api.readerNoteReadingProgress.mockImplementation(async (input: Report) => (input.reachedEnd ? FINISHED() : UNFINISHED));
  const restored = renderHook(() => useHarness());
  act(() => restored.result.current.placeAtOpen(view.sourceId, "s4", null));
  await saved(4000);
  expect(ends()).toEqual([]);
  expect(restored.result.current.completedSections).toEqual([]);
  restored.unmount();

  const { result } = renderHook(() => useHarness());
  act(() => result.current.placeAtOpen(view.sourceId, "s0", null));
  await scrollByHand(result);
  await markerAt(result, "s4"); // one flick from the top to the bottom
  await saved();
  expect(ends().map((one) => one.sectionId)).toEqual(["u1"]);
  expect(result.current.completedSections).toEqual(["u1"]);
});

it("a failed save carrying the end shows nothing finished; its retry carries the end again and finishes it", async () => {
  api.readerNoteReadingProgress
    .mockRejectedValueOnce({ code: "database_busy", message: "busy", retryable: true })
    .mockImplementation(async (input: Report) => (input.reachedEnd ? FINISHED() : UNFINISHED));
  const { result } = renderHook(() => useHarness());
  act(() => result.current.placeAtOpen(view.sourceId, "s0", null));
  await scrollByHand(result);
  for (const spanId of ["s1", "s2", "s3"]) await markerAt(result, spanId);
  // The first save (passages and the end together) fails.
  api.readerNoteReadingProgress.mockReset();
  api.readerNoteReadingProgress
    .mockRejectedValueOnce({ code: "database_busy", message: "busy", retryable: true })
    .mockImplementation(async (input: Report) => (input.reachedEnd ? FINISHED() : UNFINISHED));
  await markerAt(result, "s4");
  await saved();
  expect(ends().map((one) => one.sectionId)).toEqual(["u1"]);
  expect(result.current.completedSections).toEqual([]);
  await saved(SEEN_REPORT_MS * 2 + 50);
  expect(ends().map((one) => one.sectionId)).toEqual(["u1", "u1"]);
  expect(result.current.completedSections).toEqual(["u1"]);
});

it("after a restart the Reader shows what the backend has: a section whose end never reached it is not finished", async () => {
  const { result } = renderHook(() => useHarness());
  act(() => result.current.hydrateProgress(view.extractionId, {
    extractionId: view.extractionId,
    sections: [
      { extractionId: view.extractionId, sectionId: "u1", spansSeen: 5, spanCount: 5, revealedAt: null, completedAt: null, generationBatchId: null },
      { extractionId: view.extractionId, sectionId: "u2", spansSeen: 1, spanCount: 3, revealedAt: null, completedAt: "2026-11-20T10:00:00Z", generationBatchId: null },
    ],
  } as never));
  expect(result.current.completedSections).toEqual(["u2"]);
  // A finished section's position is a position: not forced to 100 %.
  await markerAt(result, "s5");
  expect(result.current.currentSectionRead).toBeCloseTo(1 / 3);
});

it("the learner's word and a check's close go as what they are; nothing is shown finished before the answer, nor after a failure", async () => {
  const { result } = renderHook(() => useHarness());
  let answer: unknown;
  await act(async () => {
    answer = await result.current.completeSection("u1", "check_closed");
  });
  expect(api.readerMarkSectionProgress).toHaveBeenLastCalledWith({
    extractionId: view.extractionId, sectionId: "u1", completed: true, completedBy: "check_closed" });
  expect(answer).toEqual(UNFINISHED);
  expect(result.current.completedSections).toEqual([]);
  await act(async () => {
    await result.current.completeSection("u1", "idea_chosen");
  });
  expect(api.readerMarkSectionProgress).toHaveBeenLastCalledWith({
    extractionId: view.extractionId, sectionId: "u1", completed: true, completedBy: "idea_chosen" });
  expect(result.current.completedSections).toEqual([]);
  api.readerMarkSectionProgress.mockRejectedValueOnce({ code: "database_busy", message: "busy" });
  await act(async () => {
    answer = await result.current.completeSection("u1");
  });
  expect(answer).toBeNull();
  expect(result.current.completedSections).toEqual([]);
  api.readerMarkSectionProgress.mockResolvedValueOnce(FINISHED({ enqueuedGeneration: false, waitingForBuild: true }));
  await act(async () => {
    await result.current.completeSection("u1");
  });
  expect(api.readerMarkSectionProgress).toHaveBeenLastCalledWith({ extractionId: view.extractionId, sectionId: "u1", completed: true });
  expect(result.current.completedSections).toEqual(["u1"]);
  expect(result.current.sectionFinishes).toEqual({ u1: "waiting" });
});

it("a quick check the learner has open stays open when its section finishes under it (its end arrives mid-answer)", async () => {
  api.readerNoteReadingProgress.mockImplementation(async (input: Report) => (input.reachedEnd ? FINISHED() : UNFINISHED));
  const { result } = renderHook(() => useHarness());
  act(() => result.current.placeAtOpen(view.sourceId, "s0", null));
  await scrollByHand(result);
  act(() => result.current.openQuickCheck("u1"));
  await act(async () => {
    await vi.advanceTimersByTimeAsync(20);
  });
  expect(result.current.openQuestionSections.map((one) => one.id)).toEqual(["u1"]);
  for (const spanId of ["s1", "s2", "s3", "s4"]) await markerAt(result, spanId);
  await saved();
  expect(result.current.completedSections).toEqual(["u1"]);
  expect(result.current.openQuestionSections.map((one) => one.id)).toEqual(["u1"]);
  // Its own control closes it.
  act(() => result.current.setDismissedSections(["u1"]));
  expect(result.current.openQuestionSections).toEqual([]);
});

it("finishOf reads the backend's answer, never a guess", () => {
  expect(finishOf(null)).toBeNull();
  expect(finishOf(UNFINISHED as never)).toBeNull();
  expect(finishOf(FINISHED() as never)).toBe("writing");
  expect(finishOf(FINISHED({ enqueuedGeneration: false, waitingForBuild: true }) as never)).toBe("waiting");
  expect(finishOf(FINISHED({ enqueuedGeneration: false }) as never)).toBe("done");
});

// UX-78 and UX-81 (the live walk sectionend-1): a section finished by its end is told apart from one the learner said
// they read, from the backend's stored cause: its position reads the end and its control's place says the reading
// finished it, in this visit and after a restart. One finished by the learner's word half-way keeps its real position.
it("a section finished by its end is known as such from the backend's answer, and after a restart from its progress", async () => {
  api.readerNoteReadingProgress.mockImplementation(async (input: Report) => (input.reachedEnd
    ? FINISHED({ progress: { completedAt: "2026-11-21T10:00:00Z", completionCause: "reached_end" } }) : UNFINISHED));
  const live = renderHook(() => useHarness());
  await readToTheEndOfU1(live.result);
  expect(live.result.current.endedSections).toEqual(["u1"]);
  live.unmount();

  const { result } = renderHook(() => useHarness());
  act(() => result.current.hydrateProgress(view.extractionId, {
    extractionId: view.extractionId,
    sections: [
      { extractionId: view.extractionId, sectionId: "u1", spansSeen: 4, spanCount: 5, revealedAt: null, completedAt: "2026-11-21T10:00:00Z",
        completionCause: "reached_end", generationBatchId: null },
      { extractionId: view.extractionId, sectionId: "u2", spansSeen: 1, spanCount: 3, revealedAt: null, completedAt: "2026-11-21T10:05:00Z",
        completionCause: "learner_said", generationBatchId: null },
    ],
  } as never));
  expect(result.current.endedSections).toEqual(["u1"]);
  await markerAt(result, "s1");
  expect(result.current.currentSectionRead).toBe(1);
  await markerAt(result, "s5");
  expect(result.current.currentSectionRead).toBeCloseTo(1 / 3);
});
