// The RW3a hook extraction moved ReaderScreen's orchestration into three hooks
// with no behaviour change: useReaderVisit (the funnel's visit), useReadingProgress
// (reading position, section progress, the check offers) and useReaderInquiry
// (Ask, branches, the return stack, reconnect, status, the passage check). The
// screen's own tests pass unchanged; these pin each hook's public behaviour,
// so later Reader phases can rely on it without the screen around it.
import { act, cleanup, renderHook } from "@testing-library/react";
import { createRef, useState } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReaderGuidePlanDto, ReaderGuideSectionDto, ReaderRenderViewDto, SourceLibraryCard } from "../../api/dto";
import { readerRenderViewFixture } from "../../fixtures/readerRenderView";
import { flushReaderActivity, resetReaderActivityForTests, setReaderActivityEnabled } from "./activity";
import * as offerModule from "./checkOffer";
import { useReaderInquiry, type ReaderInquiryInput } from "./useReaderInquiry";
import { useReaderVisit } from "./useReaderVisit";
import { readingPositionKey, useReadingProgress, type ReadingProgressInput } from "./useReadingProgress";
import { back as stackBack } from "./returnStack";

const api = vi.hoisted(() => ({
  readerLogActivity: vi.fn(), readerNoteReadingProgress: vi.fn(), readerAuthorSectionQuestion: vi.fn(),
  readerGuidePlan: vi.fn(), readerMarkSectionProgress: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
  readerRestoreSource: vi.fn(), readerReconnectAnswer: vi.fn(), readerSetInquiryStatus: vi.fn(),
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("./readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./guidePlan", () => ({ useGuideDiagnosisRefresh: () => undefined }));
// checkOffer stays the ONE offer authority: the spy passes every call through.
vi.mock("./checkOffer", async (importOriginal) => {
  const real = await importOriginal<typeof import("./checkOffer")>();
  return { ...real, checkOffer: vi.fn(real.checkOffer) };
});

// Five passages: section u1 is s0-s1, section u2 (with an after-section check) s2-s4.
const SPANS = ["s0", "s1", "s2", "s3", "s4"];
const view: ReaderRenderViewDto = {
  ...readerRenderViewFixture,
  blocks: SPANS.map((spanId) => ({ ...readerRenderViewFixture.blocks[1], spanId, displayNodeId: `node-${spanId}`, markdown: `Passage ${spanId}.` })),
};
const render = view;

function section(id: string, spanIds: string[], withCheck: boolean): ReaderGuideSectionDto {
  return {
    id, label: `Section ${id}`, startSpanId: spanIds[0], endSpanId: spanIds[spanIds.length - 1], spanIds,
    question: withCheck ? {
      authoredQuestionId: `raq_${id}`, practiceItemId: null, learningObjectId: null, learningObjectTitle: null,
      prompt: "Why?", expectedAnswer: "Because.", spanIds, reason: "A quick check.", learnerSignal: "auto_authored",
      goalId: null, goalTitle: null, goldenPathRunId: null, targetContractVersionId: null,
      readingPhase: "after_section", pattern: "self_explanation", placementEventId: null, blueprintVersionId: null,
      placement: "auto_authored", escalationLearningObjectId: null,
    } : null,
    suggestedPassages: [],
  } as unknown as ReaderGuideSectionDto;
}

const PLAN: ReaderGuidePlanDto = {
  version: 1, sourceId: view.sourceId, extractionId: view.extractionId, personalized: true, selectionBasis: "",
  goalContext: null,
  sections: [section("u1", SPANS.slice(0, 2), false), section("u2", SPANS.slice(2), true)],
};

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "requestAnimationFrame", "cancelAnimationFrame", "Date"] });
  vi.mocked(offerModule.checkOffer).mockClear();
  resetReaderActivityForTests();
  vi.stubGlobal("localStorage", memoryStorage());
  for (const fn of Object.values(api)) fn.mockReset();
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerNoteReadingProgress.mockResolvedValue({});
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerRestoreSource.mockResolvedValue({ eventId: "restored" });
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

function memoryStorage(): Storage {
  const values = new Map<string, string>();
  return {
    get length() {
      return values.size;
    },
    clear: () => values.clear(),
    getItem: (key: string) => values.get(key) ?? null,
    key: (index: number) => Array.from(values.keys())[index] ?? null,
    removeItem: (key: string) => void values.delete(key),
    setItem: (key: string, value: string) => void values.set(key, String(value)),
  };
}

function progressInput(overrides: Partial<ReadingProgressInput> = {}): ReadingProgressInput {
  return {
    render, offline: false, blocks: view.blocks, guidePlan: PLAN, setGuidePlan: vi.fn(), guideLoading: false,
    pdfView: null, pdfViewPending: false, surface: "text", watch: null, watchLoading: false, mode: "anchor",
    inquiry: true, muted: false, activeSpan: null, setActiveSpan: vi.fn(), bodyRef: createRef<HTMLDivElement>(),
    railRef: createRef<HTMLDivElement>(), paneRef: createRef(), watchRef: createRef(), noteProactive: vi.fn(() => true),
    showGuideRail: vi.fn(), ...overrides,
  };
}

function useProgressHarness(overrides: Partial<ReadingProgressInput> = {}) {
  const [activeSpan, setActiveSpan] = useState<string | null>(null);
  return useReadingProgress(progressInput({ activeSpan, setActiveSpan, ...overrides }));
}

it("useReadingProgress: the offered set is exactly checkOffer's verdict for every section (the one offer rule)", async () => {
  const { result } = renderHook(() => useProgressHarness());
  // Opened at the end of the checked section by a resume: placed, not read.
  act(() => result.current.placeAtOpen(view.sourceId, SPANS[4], null));
  const spy = vi.mocked(offerModule.checkOffer);
  const verdicts = () => {
    const last = new Map<string, boolean>();
    PLAN.sections.forEach((entry, index) => {
      const calls = spy.mock.calls.filter(([input]) => input.kind === "section");
      const call = calls[calls.length - PLAN.sections.length + index];
      last.set(entry.id, spy.mock.results[spy.mock.calls.indexOf(call)].value.offer as boolean);
    });
    return last;
  };
  expect(result.current.currentGuideSection?.id).toBe("u2");
  const offered = verdicts();
  expect([...result.current.offeredCheckSections]).toEqual([...offered].filter(([, offer]) => offer).map(([id]) => id));
  // Every section was asked of the one rule, with the section's own inputs.
  const lastCalls = spy.mock.calls.slice(-PLAN.sections.length).map(([input]) => input);
  expect(lastCalls.map((input) => input.kind)).toEqual(["section", "section"]);
  expect(lastCalls[1]).toMatchObject({ readingPhase: "after_section", position: "current", surface: "text", available: true, readingMoved: false });
  expect(result.current.offeredCheckSections.size).toBe(0);
});

it("useReadingProgress: a jump is a placement, the learner's own scroll is reading, and an offered check stays pinned", async () => {
  const { result } = renderHook(() => useProgressHarness());
  act(() => result.current.placeAtOpen(view.sourceId, SPANS[4], null));
  expect(result.current.readingMoved).toBe(false);
  expect(result.current.offeredCheckSections.has("u2")).toBe(false);
  // The learner's own hand moves the page (after the settle time).
  await act(async () => {
    await vi.advanceTimersByTimeAsync(2000);
    result.current.noteUserScroll();
    result.current.onReadingScroll();
    await vi.advanceTimersByTimeAsync(20);
  });
  expect(result.current.readingMoved).toBe(true);
  expect(result.current.offeredCheckSections.has("u2")).toBe(true);
  // A jump elsewhere is not reading: the movement resets, the offer stays pinned.
  act(() => result.current.jumpToSpan(SPANS[0]));
  expect(result.current.readingMoved).toBe(false);
  expect(result.current.readingSpan).toBe(SPANS[0]);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(0);
  });
  expect(result.current.offeredCheckSections.has("u2")).toBe(true);
  expect(result.current.openQuestionSections.map((entry) => entry.id)).toEqual(["u2"]);
});

it("useReadingProgress: an arrow key is the learner's own scroll; Alt+↓ to a margin mark (RW3a) is not", async () => {
  const { result } = renderHook(() => useProgressHarness());
  act(() => result.current.placeAtOpen(view.sourceId, SPANS[2], null));
  await act(async () => {
    await vi.advanceTimersByTimeAsync(2000);
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown", altKey: true }));
    result.current.onReadingScroll();
    await vi.advanceTimersByTimeAsync(20);
  });
  expect(result.current.readingMoved).toBe(false);
  await act(async () => {
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown" }));
    result.current.onReadingScroll();
    await vi.advanceTimersByTimeAsync(20);
  });
  expect(result.current.readingMoved).toBe(true);
});

it("useReadingProgress (RW3a review F1): a placement without a jump resets the learner's movement, like a jump", async () => {
  const { result } = renderHook(() => useProgressHarness());
  act(() => result.current.placeAtOpen(view.sourceId, SPANS[0], null));
  await act(async () => {
    await vi.advanceTimersByTimeAsync(2000);
    result.current.noteUserScroll();
    result.current.onReadingScroll();
    await vi.advanceTimersByTimeAsync(20);
  });
  expect(result.current.readingMoved).toBe(true);
  // A transcript's margin mark focused in place: the scroll it causes is not reading.
  act(() => result.current.notePlacement());
  expect(result.current.readingMoved).toBe(false);
  await act(async () => {
    result.current.onReadingScroll();
    await vi.advanceTimersByTimeAsync(20);
  });
  expect(result.current.readingMoved).toBe(false);
  expect(result.current.readingSpan).toBe(SPANS[0]);
});

it("useReadingProgress (RW3a): the passage the Reader placed the learner at is the restored one; a walk back names its own", () => {
  const { result } = renderHook(() => useProgressHarness());
  expect(result.current.restoredSpan).toBeNull();
  act(() => result.current.placeAtOpen(view.sourceId, SPANS[3], null));
  expect(result.current.restoredSpan).toBe(SPANS[3]);
  act(() => result.current.noteRestored(SPANS[1]));
  expect(result.current.restoredSpan).toBe(SPANS[1]);
  act(() => result.current.noteRestored(null));
  expect(result.current.restoredSpan).toBe(SPANS[1]);
  act(() => result.current.resetProgress());
  expect(result.current.restoredSpan).toBeNull();
});

it("useReadingProgress: the saved place opens, a search hit wins over it, and with neither the history decides", () => {
  window.localStorage.setItem(readingPositionKey(view.sourceId), SPANS[1]);
  const setActiveSpan = vi.fn();
  const { result } = renderHook(() => useReadingProgress(progressInput({ setActiveSpan })));
  act(() => result.current.placeAtOpen(view.sourceId, undefined, null));
  expect(result.current.readingSpan).toBe(SPANS[1]);
  act(() => result.current.placeAtOpen(view.sourceId, SPANS[3], null));
  expect(result.current.readingSpan).toBe(SPANS[3]);
  expect(setActiveSpan).toHaveBeenLastCalledWith(SPANS[3]);
});

it("useReadingProgress: leaving a book saves what was read in it and resets the per-source state", async () => {
  const { result } = renderHook(() => useProgressHarness());
  act(() => result.current.hydrateProgress(view.extractionId, {
    extractionId: view.extractionId,
    sections: [{ extractionId: view.extractionId, sectionId: "u1", spansSeen: 1, spanCount: 2, revealedAt: "x", completedAt: null, generationBatchId: null }],
  }));
  expect(result.current.sectionSeen).toEqual({ u1: 1 });
  expect(result.current.revealedSections).toEqual(["u1"]);
  act(() => result.current.resetProgress());
  expect(result.current.sectionSeen).toEqual({});
  expect(result.current.revealedSections).toEqual([]);
  expect(result.current.readingSpan).toBeNull();
});

it("useReaderVisit: one visit per opened source, and each proactive element counts once", async () => {
  const { result, unmount } = renderHook(() => useReaderVisit({ render, offline: false, inquiry: true, pdfView: null }));
  expect(result.current.noteProactive("quick_check_waiting:u2", "quick_check_waiting")).toBe(true);
  expect(result.current.noteProactive("quick_check_waiting:u2", "quick_check_waiting")).toBe(false);
  result.current.noteUsableResult("job1", "ask");
  result.current.noteBackToReading();
  result.current.noteBackToReading();
  unmount();
  flushReaderActivity();
  const events = api.readerLogActivity.mock.calls.flatMap((call) => call[0].events as Array<{ kind: string; event?: string }>);
  const kinds = events.map((event) => `${event.kind}${event.event ? `:${event.event}` : ""}`);
  expect(kinds).toEqual([
    "reader_view_opened", "reader_action_invoked:proactive_shown", "reader_action_invoked:back_to_reading", "reader_view_closed",
  ]);
});

function inquiryInput(overrides: Partial<ReaderInquiryInput>, progress: { jumpToSpan: (spanId: string) => void }): ReaderInquiryInput {
  return {
    render, offline: false, inquiry: true, muted: false, library: [], sourceTitle: "Matrices",
    selection: null, setSelection: vi.fn(), setSelectionActions: vi.fn(), activeSpan: SPANS[1], railTab: "ask",
    setRailTab: vi.fn(), answerMode: "answer_directly", setBusy: vi.fn(), onError: vi.fn(), annotations: [],
    refreshAnnotations: vi.fn(async () => undefined), setArc: vi.fn(),
    visit: {
      touchVisit: vi.fn(), visitPayload: () => ({ visit_id: "v1", extraction_id: view.extractionId }),
      noteBackToReading: vi.fn(), noteUsableResult: vi.fn(), noteSelection: vi.fn(), noteProactive: vi.fn(() => true),
      resetVisitState: vi.fn(), visitRef: { current: null },
    },
    readingSpan: SPANS[1], guideSectionBySpan: new Map(), jumpToSpan: progress.jumpToSpan, onReadingScroll: vi.fn(),
    jumpGuardRef: { current: 0 }, bodyRef: createRef<HTMLDivElement>(), askComposerRef: createRef<HTMLTextAreaElement>(),
    openSourceRef: { current: null }, ...overrides,
  };
}

it("useReaderInquiry: a follow-up is a branch detour, and walking back to the origin returns it and asks to reconnect", async () => {
  api.readerAskHistory.mockResolvedValue({
    exchanges: [{
      eventId: "root", parentExchangeId: null, extractionId: view.extractionId, spanId: SPANS[1], questionMd: "Why weighted by p?",
      answerMd: "Because.", answerMode: "answer_directly", citations: [], selectionSpanIds: [SPANS[1]], selectionQuoteMd: null,
      createdAt: "2026-10-13T09:00:00Z", questionEventId: "q_root", resolution: "open",
    }],
  });
  api.readerAsk.mockResolvedValue({
    eventId: "q_child", readerAnswerEventId: "child", parentExchangeId: "root", answerMd: "A follow-up answer.",
    answerMode: "answer_directly", citations: [], manifest: { version: "p3-reader-branches-v1" }, model: "stub",
  });
  setReaderActivityEnabled(true);
  const jumpToSpan = vi.fn();
  const { result } = renderHook(() => useReaderInquiry(inquiryInput({}, { jumpToSpan })));
  await act(async () => {
    await vi.advanceTimersByTimeAsync(0);
  });
  expect(result.current.history.map((exchange) => exchange.id)).toEqual(["root"]);
  const root = result.current.history[0];
  await act(async () => {
    await result.current.submitAsk("And conditioning?", root);
  });
  // The strip's path: where I was › the root › the follow-up.
  expect(result.current.returnStack.entries.map((entry) => entry.kind)).toEqual(["origin", "branch", "branch"]);
  expect(api.readerAsk.mock.calls[0][0]).toMatchObject({ parentExchangeId: "root", question: "And conditioning?" });
  // Alt+← twice: back at the origin, the open detours return and the reconnect line asks about the root.
  let stack = result.current.returnStackRef.current;
  for (let step = 0; step < 2; step += 1) {
    const moved = stackBack(stack);
    await act(async () => {
      await result.current.restoreEntry(moved.stack, moved.target!, "alt_back");
    });
    stack = result.current.returnStackRef.current;
  }
  expect(jumpToSpan).toHaveBeenLastCalledWith(SPANS[1]);
  expect(api.readerRestoreSource).toHaveBeenCalledWith({ extractionId: view.extractionId, spanId: SPANS[1] });
  expect(result.current.reconnect).toMatchObject({ rootId: "root", question: "Why weighted by p?", inline: true });
  // The passage check is offered by the one rule (an open inquiry the learner raised).
  expect(result.current.passageCheckOffered).toBe(true);
  expect(vi.mocked(offerModule.checkOffer).mock.calls.some(([input]) => input.kind === "passage")).toBe(true);
  flushReaderActivity();
  const events = api.readerLogActivity.mock.calls.flatMap((call) => call[0].events as Array<{ kind: string; event?: string }>);
  const detours = events.filter((event) => event.event === "detour_opened" || event.event === "detour_returned").map((event) => event.event);
  expect(detours).toEqual(["detour_opened", "detour_opened", "detour_returned", "detour_returned"]);
});

it("useReaderInquiry: opening another source after leaving one is a detour; reopening reading resets the stack", () => {
  const { result } = renderHook(() => useReaderInquiry(inquiryInput({}, { jumpToSpan: vi.fn() })));
  const card = { sourceId: "other", title: "Other book" } as SourceLibraryCard;
  act(() => result.current.rememberLeftSource({
    id: "o1", kind: "origin", sourceId: view.sourceId, sourceTitle: "Matrices", extractionId: view.extractionId,
    spanId: SPANS[1], selection: null, railTab: "guide", exchangeId: null, label: "Matrices", openedAt: 0,
  }));
  act(() => result.current.noteSourceOpened(card, "ext_other", undefined, "search"));
  expect(result.current.returnStack.entries.map((entry) => entry.kind)).toEqual(["origin", "source"]);
  act(() => result.current.noteSourceOpened(card, "ext_other", undefined, undefined));
  expect(result.current.returnStack.entries).toEqual([]);
});

it("useReaderInquiry: the switch off records no detour and sends no parent", async () => {
  api.readerAsk.mockResolvedValue({
    eventId: "q1", readerAnswerEventId: "a1", answerMd: "Answer.", answerMode: "answer_directly", citations: [],
  });
  const { result } = renderHook(() => useReaderInquiry(inquiryInput({ inquiry: false }, { jumpToSpan: vi.fn() })));
  await act(async () => {
    await result.current.submitAsk("Why?", null);
  });
  expect("parentExchangeId" in api.readerAsk.mock.calls[0][0]).toBe(false);
  act(() => result.current.peekPassage(SPANS[3]));
  expect(result.current.returnStack.entries).toEqual([]);
});
