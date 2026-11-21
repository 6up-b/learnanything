// The progress report names WHICH passages the learner's own reading observed (not only
// how many), and that a section's last passage was among them. A restore, a jump or a completion observes nothing;
// the count's position-derived prefix and its leave-after-60% rule never become passages; a passage is sent until
// the backend acknowledges it (which unions), and never again after.
import { act, cleanup, renderHook } from "@testing-library/react";
import { createRef, useState } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReaderGuidePlanDto, ReaderGuideSectionDto, ReaderRenderViewDto } from "../../api/dto";
import { readerRenderViewFixture } from "../../fixtures/readerRenderView";
import { observedPassages, SEEN_REPORT_MS, useReadingProgress, type ReadingProgressInput } from "./useReadingProgress";

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

function section(id: string, spanIds: string[]): ReaderGuideSectionDto {
  return {
    id, label: `Section ${id}`, startSpanId: spanIds[0], endSpanId: spanIds[spanIds.length - 1], spanIds,
    question: null, suggestedPassages: [],
  } as unknown as ReaderGuideSectionDto;
}

const PLAN: ReaderGuidePlanDto = {
  version: 1, sourceId: view.sourceId, extractionId: view.extractionId, personalized: false, selectionBasis: "",
  goalContext: null, sections: [section("u1", SPANS.slice(0, 5)), section("u2", SPANS.slice(5))],
};

function progressInput(overrides: Partial<ReadingProgressInput> = {}): ReadingProgressInput {
  return {
    render: view, offline: false, blocks: view.blocks, guidePlan: PLAN, setGuidePlan: vi.fn(), guideLoading: false,
    pdfView: null, pdfViewPending: false, surface: "text", watch: null, watchLoading: false, mode: "skim",
    inquiry: true, muted: false, activeSpan: null, setActiveSpan: vi.fn(), bodyRef: createRef<HTMLDivElement>(),
    railRef: createRef<HTMLDivElement>(), paneRef: createRef(), watchRef: createRef(), noteProactive: vi.fn(() => true),
    showGuideRail: vi.fn(), ...overrides,
  };
}

function useHarness(overrides: Partial<ReadingProgressInput> = {}) {
  const [activeSpan, setActiveSpan] = useState<string | null>(null);
  return useReadingProgress(progressInput({ activeSpan, setActiveSpan, ...overrides }));
}

type Report = { extractionId: string; sectionId: string; spansSeen?: number; spanCount?: number; seenSpanIds?: string[]; reachedEnd?: boolean };
const reports = () => api.readerNoteReadingProgress.mock.calls.map(([input]) => input as Report);
const passagesSent = (sectionId: string) => reports().filter((one) => one.sectionId === sectionId).flatMap((one) => one.seenSpanIds ?? []);

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "requestAnimationFrame", "cancelAnimationFrame", "Date"] });
  for (const fn of Object.values(api)) fn.mockReset();
  api.readerNoteReadingProgress.mockResolvedValue({});
  api.readerMarkSectionProgress.mockResolvedValue({});
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

type Harness = { current: ReturnType<typeof useReadingProgress> };

/** The learner's own hand moves the page (after a placement has settled). */
async function scrollByHand(result: Harness) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(2000);
    result.current.noteUserScroll();
    result.current.onReadingScroll();
    await vi.advanceTimersByTimeAsync(20);
  });
}

/** Reading on: the marker comes to another passage (as `updateReadingPosition` sets it from the page). */
async function markerAt(result: Harness, spanId: string) {
  await act(async () => {
    result.current.setReadingSpan(spanId);
    await vi.advanceTimersByTimeAsync(20);
  });
}

async function saved() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(SEEN_REPORT_MS + 50);
  });
}

it("a restore observes nothing; the learner's own reading observes the passage under the marker, never the prefix before it", async () => {
  const { result } = renderHook(() => useHarness());
  act(() => result.current.placeAtOpen(view.sourceId, "s3", null));
  await act(async () => {
    await vi.advanceTimersByTimeAsync(4000);
  });
  expect(reports()).toEqual([]);
  await scrollByHand(result);
  await saved();
  // The count is a position (four passages up to the marker); the passages are what was observed: s3 alone.
  expect(reports()).toEqual([{ extractionId: view.extractionId, sectionId: "u1", spansSeen: 4, spanCount: 5, seenSpanIds: ["s3"] }]);
});

it("a jump observes nothing, not even the passage the reading left; reading on after it observes again", async () => {
  const { result } = renderHook(() => useHarness());
  act(() => result.current.placeAtOpen(view.sourceId, "s0", null));
  await scrollByHand(result);
  await markerAt(result, "s1");
  act(() => result.current.jumpToSpan("s7"));
  await act(async () => {
    await vi.advanceTimersByTimeAsync(4000);
  });
  // Landing on u2's last passage by a jump is no end, and observes nothing.
  expect(reports().some((one) => one.reachedEnd)).toBe(false);
  expect(passagesSent("u2")).toEqual([]);
  expect(passagesSent("u1")).toEqual(["s0", "s1"]);
  await scrollByHand(result);
  await saved();
  expect(passagesSent("u2")).toEqual(["s7"]);
  // Reached by the learner's own reading, it is u2's end.
  expect(reports().filter((one) => one.reachedEnd).map((one) => one.sectionId)).toEqual(["u2"]);
});

it("reaching a section's last passage by reading is its end, sent with that passage; the count's leave-after-60% rule is neither", async () => {
  const { result } = renderHook(() => useHarness());
  act(() => result.current.placeAtOpen(view.sourceId, "s0", null));
  await scrollByHand(result);
  for (const spanId of ["s1", "s2", "s3"]) await markerAt(result, spanId);
  // Into u2 past most of u1: its count fills, though s4 was never under the marker.
  await markerAt(result, "s5");
  await saved();
  const u1 = reports().filter((one) => one.sectionId === "u1");
  expect(Math.max(...u1.map((one) => one.spansSeen ?? 0))).toBe(5);
  expect(passagesSent("u1")).toEqual(["s0", "s1", "s2", "s3"]);
  expect(u1.some((one) => one.reachedEnd)).toBe(false);
  for (const spanId of ["s6", "s7"]) await markerAt(result, spanId);
  await saved();
  const ended = reports().filter((one) => one.reachedEnd);
  expect(ended).toHaveLength(1);
  expect(ended[0]).toMatchObject({ sectionId: "u2", reachedEnd: true });
  expect(ended[0].seenSpanIds).toContain("s7");
});

it("a passage is sent until acknowledged (a failed save sends it again), and never after", async () => {
  api.readerNoteReadingProgress.mockRejectedValueOnce({ code: "database_busy", message: "busy", retryable: true });
  const { result } = renderHook(() => useHarness());
  act(() => result.current.placeAtOpen(view.sourceId, "s0", null));
  await scrollByHand(result);
  await saved();
  expect(reports().map((one) => one.seenSpanIds)).toEqual([["s0"]]);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(SEEN_REPORT_MS * 2 + 50);
  });
  expect(reports().map((one) => one.seenSpanIds)).toEqual([["s0"], ["s0"]]);
  await markerAt(result, "s1");
  await saved();
  // Only what the backend has not acknowledged: it unions, so nothing already there needs to go again.
  expect(reports().map((one) => one.seenSpanIds)).toEqual([["s0"], ["s0"], ["s1"]]);
  // Back over s0: the count does not grow and s0 is acknowledged, so nothing is sent.
  await markerAt(result, "s0");
  await saved();
  expect(reports()).toHaveLength(3);
});

it("an answered report acknowledges every passage it carried, those the backend left out too: none is sent again", async () => {
  // The backend keeps the section's own passages and leaves out any other, answering the report as usual.
  const { result } = renderHook(() => useHarness());
  act(() => result.current.placeAtOpen(view.sourceId, "s0", null));
  await scrollByHand(result);
  await saved();
  await markerAt(result, "s1");
  await saved();
  await act(async () => {
    await vi.advanceTimersByTimeAsync(SEEN_REPORT_MS * 8);
  });
  expect(reports().map((one) => one.seenSpanIds)).toEqual([["s0"], ["s1"]]);
});

it("finishing a section by its control sends the completion alone: no passage is invented for it", async () => {
  const { result } = renderHook(() => useHarness());
  act(() => result.current.placeAtOpen(view.sourceId, "s0", null));
  await act(async () => {
    await result.current.completeSection("u1");
    await vi.advanceTimersByTimeAsync(4000);
  });
  expect(api.readerMarkSectionProgress).toHaveBeenCalledWith({ extractionId: view.extractionId, sectionId: "u1", completed: true });
  expect(reports()).toEqual([]);
});

it("a guide answered for another reading observes nothing: its spans are not this reading's", async () => {
  const { result } = renderHook(() => useHarness({ guidePlan: { ...PLAN, extractionId: "ext_other" } }));
  act(() => result.current.placeAtOpen(view.sourceId, "s2", null));
  await scrollByHand(result);
  await saved();
  expect(reports().flatMap((one) => one.seenSpanIds ?? [])).toEqual([]);
});

it("observedPassages: the marker's passage on the text view; on a page-only PDF, once the marker is through its share of the page", () => {
  expect(observedPassages({ spanId: "s1", pageSpans: null, offset: null, through: 0.85, left: null })).toEqual(["s1"]);
  expect(observedPassages({ spanId: "s1", pageSpans: null, offset: null, through: 0.85, left: "s0" })).toEqual(["s0", "s1"]);
  const pages = [{ spanId: "a", page: 3 }, { spanId: "b", page: 3 }, { spanId: "c", page: 4 }];
  // Two passages share page 3: a is [0, 0.5) of it, b [0.5, 1).
  expect(observedPassages({ spanId: "a", pageSpans: pages, offset: 0.3, through: 0.85, left: null })).toEqual([]);
  expect(observedPassages({ spanId: "a", pageSpans: pages, offset: 0.45, through: 0.85, left: null })).toEqual(["a"]);
  expect(observedPassages({ spanId: "b", pageSpans: pages, offset: 0.6, through: 0.85, left: "a" })).toEqual(["a"]);
  expect(observedPassages({ spanId: "b", pageSpans: pages, offset: 0.95, through: 0.85, left: null })).toEqual(["b"]);
  // One passage on its page: the count's own within-page rule.
  expect(observedPassages({ spanId: "c", pageSpans: pages, offset: 0.8, through: 0.85, left: null })).toEqual([]);
  expect(observedPassages({ spanId: "c", pageSpans: pages, offset: 0.85, through: 0.85, left: null })).toEqual(["c"]);
});
