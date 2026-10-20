// Reader RW3b, Codex review fixes on the real hooks (docs/reviews/reader-rw3b-codex-review.md):
// F4 a held-out cue goes through the Reader's spacing and restored-line rules
// as a mark does, keeps its place and is never drawn; F5 both arms are
// measured by their passage, and on the original PDF neither is recorded;
// F6 a receipt queued in one book is sent to that book with its visit when
// the learner opens another, and sent again once when the sidecar did not take
// it; F7 a search that answered for older targets (a joined job) is asked
// again for the current ones.
import { act, cleanup, fireEvent, render, renderHook } from "@testing-library/react";
import { useRef } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReaderCueDto, ReaderCuesDto } from "../../api/dto";
import { placeCueMarks, type CuePlacement } from "./cues";

const api = vi.hoisted(() => ({
  readerCueImpressions: vi.fn(), readerCueDiscovery: vi.fn(), readerCueDiscoveryJob: vi.fn(),
}));
vi.mock("../../api/client", () => ({ api }));

import { useCueImpressions, passageThresholds, IMPRESSION_FLUSH_MS, IMPRESSION_RETRY_MS } from "./useCueImpressions";
import { useCueDiscovery, DISCOVERY_POLL_MS } from "./useCueDiscovery";
import { MarginMark } from "./MarginMark";

function cue(spanId: string, rank: number, extra: Partial<ReaderCueDto> = {}): ReaderCueDto {
  return {
    cueId: `cue_${spanId}`, kind: "revisit", spanId, sectionId: "u1", learningObjectId: "lo", learningObjectTitle: "LO",
    targetId: "err_1", rank, sectionRank: rank, note: "n", because: "b", label: "l",
    earlier: { attemptId: null, practiceItemId: null, prompt: null, answer: null, answeredAt: null, answeredOn: null,
      statement: null, statementPending: false },
    foundBy: "guide", linkId: null, ...extra,
  };
}
const discovered = (spanId: string, rank: number) =>
  cue(spanId, rank, { cueId: `dcue_${spanId}`, kind: "distinction", foundBy: "model", linkId: `plink_${spanId}`, propensity: 0.9 });

function cues(marks: ReaderCueDto[], heldOut: ReaderCueDto[] = [], targetsKey = "tk1", planId = "cplan_1"): ReaderCuesDto {
  return {
    version: "v", density: "normal", budgetPerSection: 2, onePerViewport: true, sourceOff: false, marks, withheld: {},
    discovery: { version: "d", planId, targetsKey, targets: 1, holdoutRate: 0.1, valueOrder: true, tryFirst: true, heldOut,
      suppressed: [] },
  } as ReaderCuesDto;
}

const EMPTY: CuePlacement = { shown: [], suppressed: [] };

beforeEach(() => {
  vi.resetAllMocks();
  api.readerCueImpressions.mockResolvedValue({ recorded: [] });
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

// -- F4 ---------------------------------------------------------------------------------------

it("F4: a held-out cue is placed like a mark, spaces out a lower mark, and is never drawn", () => {
  const tops: Record<string, number> = { a: 100, b: 300, c: 1200, d: 2000 };
  const base = { muted: false, working: false, onePerViewport: true, viewportHeight: 600,
    positionOf: (spanId: string) => tops[spanId] ?? null };
  const held = discovered("a", 0);
  const placement = placeCueMarks({ ...base, restoredSpanId: "c", marks: [discovered("b", 1), discovered("d", 3)],
    heldOut: [held, discovered("c", 2)] });
  expect(placement.shown.map((entry) => entry.spanId)).toEqual(["d"]);
  expect(placement.heldOutPlaced?.map((entry) => entry.spanId)).toEqual(["a"]);
  // b sits within a screenful of the held-out a: spaced out exactly as if a were drawn.
  expect(placement.suppressed).toEqual([{ cue: expect.objectContaining({ spanId: "b" }), reason: "spacing" }]);
  // A held-out cue on the restored line was never eligible to show: not a control.
  expect(placement.heldOutSuppressed).toEqual([{ cue: expect.objectContaining({ spanId: "c" }), reason: "restored_line" }]);
  // Without held-out cues the placement is RW3a's, key for key.
  expect(Object.keys(placeCueMarks({ ...base, restoredSpanId: null, marks: [cue("a", 0)] }))).toEqual(["shown", "suppressed"]);
});

// -- F5 ---------------------------------------------------------------------------------------

class FakeObserver {
  static all: FakeObserver[] = [];
  callback: IntersectionObserverCallback;
  targets: Element[] = [];
  constructor(callback: IntersectionObserverCallback) {
    this.callback = callback;
    FakeObserver.all.push(this);
  }
  observe(target: Element) { this.targets.push(target); }
  unobserve() {}
  disconnect() {}
}

function body(spans: string[]) {
  const element = document.createElement("div");
  element.innerHTML = spans.map((spanId) => `<p data-span-id="${spanId}"></p>`).join("");
  return { current: element };
}

it("F5: both arms are measured by their passage on the text view (a tall passage counts by the reading area)", async () => {
  vi.useFakeTimers();
  FakeObserver.all = [];
  vi.stubGlobal("IntersectionObserver", FakeObserver);
  const shown = discovered("s1", 0);
  const held = discovered("s2", 1);
  const placement: CuePlacement = { shown: [shown], suppressed: [], heldOutPlaced: [held], heldOutSuppressed: [] };
  const { result } = renderHook(() => useCueImpressions({ extractionId: "A", cues: cues([shown], [held]), placement,
    surface: "text", bodyRef: body(["s1", "s2"]), visitId: () => "visit_A" }));
  // MarginMark's "in view" for a discovered mark is not its receipt (its button is not the passage).
  act(() => result.current.noteShown(shown));
  const observer = FakeObserver.all[FakeObserver.all.length - 1];
  expect(observer.targets).toHaveLength(2);
  act(() => {
    observer.callback(observer.targets.map((target) => ({ isIntersecting: true, intersectionRatio: 0.3, target,
      intersectionRect: { height: 400 }, rootBounds: { height: 600 } })) as unknown as IntersectionObserverEntry[],
    observer as unknown as IntersectionObserver);
  });
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  const sent = api.readerCueImpressions.mock.calls.flatMap((call) => call[0].entries);
  expect(sent).toEqual([{ cueId: "dcue_s1", shown: true }, { cueId: "dcue_s2", shown: false }]);
});

it("F5: on the original PDF no discovered cue is recorded in either arm; a Guide mark still is", async () => {
  vi.useFakeTimers();
  FakeObserver.all = [];
  vi.stubGlobal("IntersectionObserver", FakeObserver);
  const shown = discovered("s1", 0);
  const guideMark = cue("s3", 2);
  const placement: CuePlacement = { shown: [shown, guideMark], suppressed: [], heldOutPlaced: [discovered("s2", 1)],
    heldOutSuppressed: [] };
  const { result } = renderHook(() => useCueImpressions({ extractionId: "A", cues: cues([shown, guideMark]),
    placement, surface: "pdf", bodyRef: body([]), visitId: () => "visit_A" }));
  act(() => {
    result.current.noteShown(shown);
    result.current.noteShown(guideMark);
  });
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  expect(FakeObserver.all).toHaveLength(0);
  expect(api.readerCueImpressions.mock.calls.flatMap((call) => call[0].entries)).toEqual([{ cueId: "cue_s3", shown: true }]);
});

// -- F14 (re-review) ----------------------------------------------------------------------------

/** Calls back only when the ratio crosses one of its thresholds, as a browser's does. */
class ThresholdObserver {
  static all: ThresholdObserver[] = [];
  callback: IntersectionObserverCallback;
  thresholds: number[];
  targets: Element[] = [];
  last = new Map<Element, number>();
  constructor(callback: IntersectionObserverCallback, options?: IntersectionObserverInit) {
    this.callback = callback;
    const threshold = options?.threshold ?? 0;
    this.thresholds = Array.isArray(threshold) ? threshold : [threshold];
    ThresholdObserver.all.push(this);
  }
  observe(target: Element) { this.targets.push(target); this.last.set(target, -1); }
  unobserve(target: Element) { this.targets = this.targets.filter((entry) => entry !== target); }
  disconnect() { this.targets = []; }
  /** The passage now shows this many pixels of a viewport this tall. */
  scroll(target: Element, visible: number, height: number, area: number) {
    if (!this.targets.includes(target)) return;
    const ratio = visible / height;
    const before = this.last.get(target) ?? -1;
    this.last.set(target, ratio);
    const crossed = this.thresholds.some((t) => (before < t) !== (ratio < t)) || before < 0;
    if (!crossed) return;
    this.callback([{ isIntersecting: visible > 0, intersectionRatio: ratio, target,
      intersectionRect: { height: visible }, rootBounds: { height: area } }] as unknown as IntersectionObserverEntry[],
    this as unknown as IntersectionObserver);
  }
}

it("F14: a passage taller than the reading area is recorded once it fills half of it", async () => {
  vi.useFakeTimers();
  ThresholdObserver.all = [];
  vi.stubGlobal("IntersectionObserver", ThresholdObserver);
  vi.stubGlobal("innerHeight", 600);
  const shown = discovered("tall", 0);
  const placement: CuePlacement = { shown: [shown], suppressed: [], heldOutPlaced: [], heldOutSuppressed: [] };
  const ref = body(["tall"]);
  const passage = ref.current.querySelector("[data-span-id=\"tall\"]") as HTMLElement;
  passage.getBoundingClientRect = () => ({ height: 4000, width: 500, top: 0, left: 0, bottom: 4000, right: 500,
    x: 0, y: 0, toJSON: () => ({}) }) as DOMRect;
  renderHook(() => useCueImpressions({ extractionId: "A", cues: cues([shown]), placement, surface: "text",
    bodyRef: ref, visitId: () => "visit_A" }));
  const observer = ThresholdObserver.all.find((entry) => entry.targets.includes(passage));
  expect(observer).toBeDefined();
  // Scrolling in: a sliver, a sixth of the area, then more than half, then the area filled (ratio 0.15).
  act(() => {
    for (const visible of [50, 100, 250, 320, 450, 600]) observer!.scroll(passage, visible, 4000, 600);
  });
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  expect(api.readerCueImpressions.mock.calls.flatMap((call) => call[0].entries)).toEqual([{ cueId: "dcue_tall", shown: true }]);
});

it("F14: a sliver of a tall passage is not in view", async () => {
  vi.useFakeTimers();
  ThresholdObserver.all = [];
  vi.stubGlobal("IntersectionObserver", ThresholdObserver);
  vi.stubGlobal("innerHeight", 600);
  const shown = discovered("tall", 0);
  const placement: CuePlacement = { shown: [shown], suppressed: [], heldOutPlaced: [], heldOutSuppressed: [] };
  const ref = body(["tall"]);
  const passage = ref.current.querySelector("[data-span-id=\"tall\"]") as HTMLElement;
  passage.getBoundingClientRect = () => ({ height: 4000, width: 500, top: 0, left: 0, bottom: 4000, right: 500,
    x: 0, y: 0, toJSON: () => ({}) }) as DOMRect;
  renderHook(() => useCueImpressions({ extractionId: "A", cues: cues([shown]), placement, surface: "text",
    bodyRef: ref, visitId: () => "visit_A" }));
  const observer = ThresholdObserver.all.find((entry) => entry.targets.includes(passage))!;
  act(() => { for (const visible of [50, 200, 280]) observer.scroll(passage, visible, 4000, 600); });
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  expect(api.readerCueImpressions).not.toHaveBeenCalled();
});

// -- F14 (verify: width-only reflow) ----------------------------------------------------------

/** A ResizeObserver whose notifications the test sends (jsdom has none). */
class FakeResizeObserver {
  static all: FakeResizeObserver[] = [];
  callback: ResizeObserverCallback;
  targets: Element[] = [];
  constructor(callback: ResizeObserverCallback) {
    this.callback = callback;
    FakeResizeObserver.all.push(this);
  }
  observe(target: Element) { this.targets.push(target); }
  unobserve(target: Element) { this.targets = this.targets.filter((entry) => entry !== target); }
  disconnect() { this.targets = []; }
}

/** Well past the hook's settle time for size changes (it does not depend on the export). */
const REFLOW_SETTLE_WAIT_MS = 1_000;

/** A passage whose height the test changes, as a reflow would. */
function sizedPassage(ref: { current: HTMLDivElement }, spanId: string, height: { value: number }) {
  const passage = ref.current.querySelector(`[data-span-id="${spanId}"]`) as HTMLElement;
  passage.getBoundingClientRect = () => ({ height: height.value, width: 500, top: 0, left: 0, bottom: height.value,
    right: 500, x: 0, y: 0, toJSON: () => ({}) }) as DOMRect;
  return passage;
}

/** The window narrows: the passages reflow, the window's height stays. Every
 *  size watcher hears of it (the window's resize event too), then it settles. */
async function reflow() {
  act(() => {
    for (const watcher of FakeResizeObserver.all) {
      if (watcher.targets.length === 0) continue;
      watcher.callback(watcher.targets.map((target) => ({ target })) as unknown as ResizeObserverEntry[],
        watcher as unknown as ResizeObserver);
    }
    window.dispatchEvent(new Event("resize"));
  });
  await act(async () => { vi.advanceTimersByTime(REFLOW_SETTLE_WAIT_MS); });
}

/** Scroll a passage of this height through a 600 px viewport, on every observer now watching it. */
function scrollThrough(passage: Element, height: number) {
  act(() => {
    for (const visible of [0, 50, 100, 250, 320, 450, 600]) {
      for (const observer of ThresholdObserver.all) observer.scroll(passage, Math.min(visible, height), height, 600);
    }
  });
}

function sentEntries() {
  return api.readerCueImpressions.mock.calls.flatMap((call) => call[0].entries);
}

it("F14 verify: a passage reflowed from 2,000 to 6,000 px at the same window height is still recorded", async () => {
  vi.useFakeTimers();
  ThresholdObserver.all = [];
  FakeResizeObserver.all = [];
  vi.stubGlobal("IntersectionObserver", ThresholdObserver);
  vi.stubGlobal("ResizeObserver", FakeResizeObserver);
  vi.stubGlobal("innerHeight", 600);
  const shown = discovered("tall", 0);
  const placement: CuePlacement = { shown: [shown], suppressed: [], heldOutPlaced: [], heldOutSuppressed: [] };
  const ref = body(["tall"]);
  const height = { value: 2000 };
  const passage = sizedPassage(ref, "tall", height);
  renderHook(() => useCueImpressions({ extractionId: "A", cues: cues([shown]), placement, surface: "text",
    bodyRef: ref, visitId: () => "visit_A" }));
  // Mounted offscreen: the observer's first notification, nothing in view.
  act(() => { for (const observer of ThresholdObserver.all) observer.scroll(passage, 0, 2000, 600); });
  height.value = 6000;
  await reflow();
  // Now at most 600 / 6000 = 0.10 of it can be in view; it fills half the area at 0.05.
  scrollThrough(passage, 6000);
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  expect(api.readerCueImpressions).toHaveBeenCalledTimes(1);
  expect(sentEntries()).toEqual([{ cueId: "dcue_tall", shown: true }]);
});

it("F14 verify control: a 4,000 px passage that keeps its size is recorded once, its observer kept", async () => {
  vi.useFakeTimers();
  ThresholdObserver.all = [];
  FakeResizeObserver.all = [];
  vi.stubGlobal("IntersectionObserver", ThresholdObserver);
  vi.stubGlobal("ResizeObserver", FakeResizeObserver);
  vi.stubGlobal("innerHeight", 600);
  const shown = discovered("tall", 0);
  const placement: CuePlacement = { shown: [shown], suppressed: [], heldOutPlaced: [], heldOutSuppressed: [] };
  const ref = body(["tall"]);
  const passage = sizedPassage(ref, "tall", { value: 4000 });
  renderHook(() => useCueImpressions({ extractionId: "A", cues: cues([shown]), placement, surface: "text",
    bodyRef: ref, visitId: () => "visit_A" }));
  const before = ThresholdObserver.all.length;
  // A size notification that changes nothing does not rebuild the observer.
  await reflow();
  expect(ThresholdObserver.all).toHaveLength(before);
  scrollThrough(passage, 4000);
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  expect(api.readerCueImpressions).toHaveBeenCalledTimes(1);
  expect(sentEntries()).toEqual([{ cueId: "dcue_tall", shown: true }]);
});

it("F14 verify: repeated reflows never log a passage twice in one visit", async () => {
  vi.useFakeTimers();
  ThresholdObserver.all = [];
  FakeResizeObserver.all = [];
  vi.stubGlobal("IntersectionObserver", ThresholdObserver);
  vi.stubGlobal("ResizeObserver", FakeResizeObserver);
  vi.stubGlobal("innerHeight", 600);
  const first = discovered("p1", 0);
  const second = discovered("p2", 1);
  const placement: CuePlacement = { shown: [first], suppressed: [], heldOutPlaced: [second], heldOutSuppressed: [] };
  const ref = body(["p1", "p2"]);
  const firstHeight = { value: 2000 };
  const secondHeight = { value: 2000 };
  const p1 = sizedPassage(ref, "p1", firstHeight);
  const p2 = sizedPassage(ref, "p2", secondHeight);
  renderHook(() => useCueImpressions({ extractionId: "A", cues: cues([first], [second]), placement, surface: "text",
    bodyRef: ref, visitId: () => "visit_A" }));
  // p1 is read; its receipt is sent.
  scrollThrough(p1, firstHeight.value);
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  // The window narrows and widens again and again: both passages reflow, the
  // observers are rebuilt, and p1 is scrolled through again after each one.
  for (const [h1, h2] of [[6000, 5000], [3000, 2500], [6000, 7000], [2000, 2000]]) {
    firstHeight.value = h1;
    secondHeight.value = h2;
    await reflow();
    scrollThrough(p1, h1);
    await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  }
  expect(ThresholdObserver.all.length).toBeGreaterThan(1);
  // p2, read only now, is recorded once too; p1 is not again.
  scrollThrough(p2, secondHeight.value);
  await reflow();
  scrollThrough(p2, secondHeight.value);
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  expect(sentEntries()).toEqual([{ cueId: "dcue_p1", shown: true }, { cueId: "dcue_p2", shown: false }]);
});

// -- F6 ---------------------------------------------------------------------------------------

it("F6: opening another book sends the first book's queued receipts to it, with its visit", async () => {
  vi.useFakeTimers();
  const guideMark = cue("a1", 0);
  const { result, rerender } = renderHook(({ extraction }: { extraction: string }) => useCueImpressions({
    extractionId: extraction, cues: cues([guideMark]), placement: EMPTY, surface: "pdf", bodyRef: body([]),
    visitId: () => `visit_${extraction}`,
  }), { initialProps: { extraction: "A" } });
  act(() => result.current.noteShown(guideMark));
  rerender({ extraction: "B" });  // before the flush
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  expect(api.readerCueImpressions).toHaveBeenCalledTimes(1);
  expect(api.readerCueImpressions).toHaveBeenCalledWith({ extractionId: "A", visitId: "visit_A", planId: "cplan_1",
    entries: [{ cueId: "cue_a1", shown: true }] });
});

it("F6: a batch the sidecar did not take is sent again once", async () => {
  vi.useFakeTimers();
  api.readerCueImpressions.mockRejectedValueOnce(new Error("busy")).mockResolvedValue({ recorded: [] });
  const guideMark = cue("a1", 0);
  const { result } = renderHook(() => useCueImpressions({ extractionId: "A", cues: cues([guideMark]),
    placement: EMPTY, surface: "pdf", bodyRef: body([]), visitId: () => "visit_A" }));
  act(() => result.current.noteShown(guideMark));
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_RETRY_MS + 10); });
  expect(api.readerCueImpressions).toHaveBeenCalledTimes(2);
  expect(api.readerCueImpressions.mock.calls[1][0]).toEqual({ extractionId: "A", visitId: "visit_A", planId: "cplan_1",
    entries: [{ cueId: "cue_a1", shown: true }] });
});

// -- F7 ---------------------------------------------------------------------------------------

it("F7: a search that answered for older targets is asked again for the current ones", async () => {
  vi.useFakeTimers();
  const reload = vi.fn().mockResolvedValue(undefined);
  // The first ask starts K1's job; the second (K2) joins it; K1's job then answers for K1.
  api.readerCueDiscovery
    .mockResolvedValueOnce({ jobId: "j1", extractionId: "A", state: "pending", result: null })
    .mockResolvedValueOnce({ jobId: "j1", extractionId: "A", state: "pending", result: null })
    .mockResolvedValueOnce({ jobId: "j2", extractionId: "A", state: "done",
      result: { status: "done", targetsKey: "K2", calls: 1, links: 1 } });
  api.readerCueDiscoveryJob.mockResolvedValue({ jobId: "j1", extractionId: "A", state: "done",
    result: { status: "done", targetsKey: "K1", calls: 1, links: 0 } });
  const discovery = (key: string) => cues([], [], key).discovery ?? null;
  const { rerender } = renderHook(({ key }: { key: string }) => useCueDiscovery({ extractionId: "A",
    discovery: discovery(key), offline: false, reloadGuidePlan: reload }), { initialProps: { key: "K1" } });
  await act(async () => { await Promise.resolve(); });
  rerender({ key: "K2" });
  await act(async () => { await Promise.resolve(); });
  await act(async () => { vi.advanceTimersByTime(DISCOVERY_POLL_MS[0] + 10); });
  await act(async () => { await Promise.resolve(); await Promise.resolve(); });
  expect(api.readerCueDiscovery).toHaveBeenCalledTimes(3);
  // The answer for K2 found links: the plan is re-read.
  expect(reload).toHaveBeenCalled();
});

it("F7: a search answered for the targets asked is not asked again", async () => {
  api.readerCueDiscovery.mockResolvedValue({ jobId: "j1", extractionId: "A", state: "done",
    result: { status: "done", targetsKey: "K1", calls: 0, links: 0 } });
  const reload = vi.fn().mockResolvedValue(undefined);
  renderHook(() => useCueDiscovery({ extractionId: "A", discovery: cues([], [], "K1").discovery ?? null,
    offline: false, reloadGuidePlan: reload }));
  await act(async () => { await Promise.resolve(); await Promise.resolve(); });
  expect(api.readerCueDiscovery).toHaveBeenCalledTimes(1);
  expect(reload).not.toHaveBeenCalled();
});

// -- Fix round 4 (whole-stage verify) ---------------------------------------------------------------

it("F14 round 4: a 24,100 px passage is recorded at the exact half-area crossing (no rounded threshold)", async () => {
  vi.useFakeTimers();
  ThresholdObserver.all = [];
  FakeResizeObserver.all = [];
  vi.stubGlobal("IntersectionObserver", ThresholdObserver);
  vi.stubGlobal("ResizeObserver", FakeResizeObserver);
  vi.stubGlobal("innerHeight", 600);
  const shown = discovered("tall", 0);
  const placement: CuePlacement = { shown: [shown], suppressed: [], heldOutPlaced: [], heldOutSuppressed: [] };
  const ref = body(["tall"]);
  const passage = sizedPassage(ref, "tall", { value: 24_100 });
  renderHook(() => useCueImpressions({ extractionId: "A", cues: cues([shown]), placement, surface: "text",
    bodyRef: ref, visitId: () => "visit_A" }));
  // Half the area is 300 px, a ratio of 300 / 24,100 = 0.012448...; rounded to 0.0124 it fired at 298.9 px.
  act(() => {
    for (const visible of [0, 120.5, 298.9, 299.5, 299.95, 300.2, 301.7, 450.25, 600]) {
      for (const observer of ThresholdObserver.all) observer.scroll(passage, visible, 24_100, 600);
    }
  });
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  expect(sentEntries()).toEqual([{ cueId: "dcue_tall", shown: true }]);
});

it("F14 round 4: the half-area threshold is the exact ratio, kept within (0, 1]", () => {
  expect(passageThresholds(24_100, 600)).toContain(300 / 24_100);
  expect(passageThresholds(4_000, 600)).toContain(0.075);
  for (const threshold of passageThresholds(1e12, 600)) expect(threshold >= 0 && threshold <= 1).toBe(true);
  expect(passageThresholds(1e12, 600).filter((threshold) => threshold > 0 && threshold < 0.25)).toHaveLength(1);
  expect(passageThresholds(500, 600)).toEqual([0, 0.25, 0.5, 0.75, 1]);
});

it("F17: each queued impression carries the plan it was seen on, and a later plan's batch is sent apart", async () => {
  vi.useFakeTimers();
  const first = cue("a1", 0);
  const second = cue("a2", 1);
  const { result, rerender } = renderHook(({ plan }: { plan: string }) => useCueImpressions({
    extractionId: "A", cues: cues([first, second], [], "tk1", plan), placement: EMPTY, surface: "pdf",
    bodyRef: body([]), visitId: () => "visit_A",
  }), { initialProps: { plan: "cplan_old" } });
  act(() => result.current.noteShown(first));
  // The plan is re-read before the flush (a density change): a new plan id.
  rerender({ plan: "cplan_new" });
  act(() => result.current.noteShown(second));
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  const sent = api.readerCueImpressions.mock.calls.map((call) => call[0]);
  expect(sent).toHaveLength(2);
  expect(sent).toContainEqual({ extractionId: "A", visitId: "visit_A", planId: "cplan_old",
    entries: [{ cueId: "cue_a1", shown: true }] });
  expect(sent).toContainEqual({ extractionId: "A", visitId: "visit_A", planId: "cplan_new",
    entries: [{ cueId: "cue_a2", shown: true }] });
});

it("F16: every discovery ask of one source open names the same open; the next source is a new open", async () => {
  api.readerCueDiscovery.mockImplementation(({ extractionId }: { extractionId: string }) => Promise.resolve({
    jobId: "j", extractionId, state: "done", result: { status: "done", targetsKey: null, calls: 0, links: 0 } }));
  const reload = vi.fn().mockResolvedValue(undefined);
  const { rerender } = renderHook(({ extraction, key }: { extraction: string; key: string }) => useCueDiscovery({
    extractionId: extraction, discovery: cues([], [], key).discovery ?? null, offline: false, reloadGuidePlan: reload,
  }), { initialProps: { extraction: "A", key: "K1" } });
  await act(async () => { await Promise.resolve(); });
  // A new target mid-open: asked again, within the same open.
  rerender({ extraction: "A", key: "K2" });
  await act(async () => { await Promise.resolve(); });
  rerender({ extraction: "B", key: "K2" });
  await act(async () => { await Promise.resolve(); });
  const asks = api.readerCueDiscovery.mock.calls.map((call) => call[0] as { extractionId: string; sourceOpenId?: string });
  expect(asks.map((ask) => ask.extractionId)).toEqual(["A", "A", "B"]);
  expect(asks[0].sourceOpenId).toMatch(/^copen_/);
  expect(asks[1].sourceOpenId).toBe(asks[0].sourceOpenId);
  expect(asks[2].sourceOpenId).toMatch(/^copen_/);
  expect(asks[2].sourceOpenId).not.toBe(asks[0].sourceOpenId);
});

// -- Fix round 5 (verify) ------------------------------------------------------------------------

it("F20: a new plan with the same placement and targets rebinds the observers; a passage first seen under B sends plan_B", async () => {
  vi.useFakeTimers();
  ThresholdObserver.all = [];
  FakeResizeObserver.all = [];
  vi.stubGlobal("IntersectionObserver", ThresholdObserver);
  vi.stubGlobal("ResizeObserver", FakeResizeObserver);
  vi.stubGlobal("innerHeight", 600);
  const first = discovered("p1", 0);
  const second = discovered("p2", 1);
  // One placement object for both plans: plan B moves no mark and keeps the targets.
  const placement: CuePlacement = { shown: [first, second], suppressed: [], heldOutPlaced: [], heldOutSuppressed: [] };
  const ref = body(["p1", "p2"]);
  const p1 = sizedPassage(ref, "p1", { value: 400 });
  const p2 = sizedPassage(ref, "p2", { value: 400 });
  const { rerender } = renderHook(({ plan }: { plan: string }) => useCueImpressions({
    extractionId: "A", cues: cues([first, second], [], "tk1", plan), placement, surface: "text", bodyRef: ref,
    visitId: () => "visit_A" }), { initialProps: { plan: "plan_A" } });
  // p1 is seen under A (queued, not yet sent); p2 is still offscreen.
  act(() => {
    for (const observer of ThresholdObserver.all) observer.scroll(p2, 0, 400, 600);
    for (const observer of ThresholdObserver.all) observer.scroll(p1, 400, 400, 600);
  });
  rerender({ plan: "plan_B" });
  // p2 comes into view only now, under B.
  act(() => {
    for (const observer of ThresholdObserver.all) observer.scroll(p2, 0, 400, 600);
    for (const observer of ThresholdObserver.all) observer.scroll(p2, 400, 400, 600);
  });
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  const sent = api.readerCueImpressions.mock.calls.map((call) => call[0]);
  expect(sent).toContainEqual({ extractionId: "A", visitId: "visit_A", planId: "plan_B",
    entries: [{ cueId: "dcue_p2", shown: true }] });
  // The receipt queued under A keeps A.
  expect(sent).toContainEqual({ extractionId: "A", visitId: "visit_A", planId: "plan_A",
    entries: [{ cueId: "dcue_p1", shown: true }] });
  expect(sent.flatMap((batch) => batch.entries)).toHaveLength(2);
});

it("F17 round 5: a tap names the plan its cue was first seen on this visit, else the plan served now", () => {
  const seen = cue("a1", 0);
  const unseen = cue("a2", 1);
  const { result, rerender } = renderHook(({ plan }: { plan: string }) => useCueImpressions({
    extractionId: "A", cues: cues([seen, unseen], [], "tk1", plan), placement: EMPTY, surface: "pdf",
    bodyRef: body([]), visitId: () => "visit_A",
  }), { initialProps: { plan: "plan_A" } });
  act(() => result.current.noteShown(seen));
  rerender({ plan: "plan_B" });
  expect(result.current.planFor(seen)).toBe("plan_A");
  expect(result.current.planFor(unseen)).toBe("plan_B");
});

// -- Fix round 6 (verify) ------------------------------------------------------------------------

it("F21: a disconnected generation's delayed callback is discarded; measured again under B, the passage is sent once as plan_B", async () => {
  vi.useFakeTimers();
  ThresholdObserver.all = [];
  FakeResizeObserver.all = [];
  vi.stubGlobal("IntersectionObserver", ThresholdObserver);
  vi.stubGlobal("ResizeObserver", FakeResizeObserver);
  vi.stubGlobal("innerHeight", 600);
  const shown = discovered("p1", 0);
  const placement: CuePlacement = { shown: [shown], suppressed: [], heldOutPlaced: [], heldOutSuppressed: [] };
  const ref = body(["p1"]);
  const p1 = sizedPassage(ref, "p1", { value: 400 });
  const { rerender } = renderHook(({ plan }: { plan: string }) => useCueImpressions({
    extractionId: "A", cues: cues([shown], [], "tk1", plan), placement, surface: "text", bodyRef: ref,
    visitId: () => "visit_A" }), { initialProps: { plan: "plan_A" } });
  const generationA = ThresholdObserver.all.find((observer) => observer.targets.includes(p1))!;
  expect(generationA).toBeDefined();
  // The browser samples p1 in view under A, but plan B renders before the callback runs.
  rerender({ plan: "plan_B" });
  act(() => {
    generationA.callback([{ isIntersecting: true, intersectionRatio: 1, target: p1, intersectionRect: { height: 400 },
      rootBounds: { height: 600 } }] as unknown as IntersectionObserverEntry[],
    generationA as unknown as IntersectionObserver);
  });
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  // The A observation is never sent, under either plan's id.
  expect(api.readerCueImpressions).not.toHaveBeenCalled();
  // B's own observer measures p1 again: sent once, as plan_B.
  act(() => {
    for (const observer of ThresholdObserver.all) observer.scroll(p1, 0, 400, 600);
    for (const observer of ThresholdObserver.all) observer.scroll(p1, 400, 400, 600);
  });
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  expect(api.readerCueImpressions.mock.calls.map((call) => call[0])).toEqual([
    { extractionId: "A", visitId: "visit_A", planId: "plan_B", entries: [{ cueId: "dcue_p1", shown: true }] }]);
});

// -- Fix round 7 (verify) ------------------------------------------------------------------------

/** An observer whose callbacks the test delivers; it remembers being disconnected. */
class MarkObserver {
  static all: MarkObserver[] = [];
  callback: IntersectionObserverCallback;
  targets: Element[] = [];
  connected = true;
  constructor(callback: IntersectionObserverCallback) {
    this.callback = callback;
    MarkObserver.all.push(this);
  }
  observe(target: Element) { this.targets.push(target); }
  unobserve() {}
  disconnect() { this.connected = false; }
  deliver(target: Element) {
    this.callback([{ isIntersecting: true, intersectionRatio: 1, target }] as unknown as IntersectionObserverEntry[],
      this as unknown as IntersectionObserver);
  }
}

function GuideMarkHarness({ plan, mark }: { plan: string; mark: ReaderCueDto }) {
  const served = cues([mark], [], "tk1", plan);
  const ref = useRef(document.createElement("div") as HTMLDivElement);
  const impressions = useCueImpressions({ extractionId: "A", cues: served, placement: EMPTY, surface: "pdf",
    bodyRef: ref, visitId: () => "visit_A" });
  const noop = () => undefined;
  return (
    <MarginMark cue={mark} open={false} onOpenChange={noop} surface="text" canCheckMe={false} checkPhase="idle"
      onOpenEarlier={noop} onCheckMe={noop} onNotRelevant={noop} onFewer={noop} onOffBook={noop}
      onOffEverywhere={noop} onSeen={(seenOn) => impressions.noteShown(mark, seenOn)} planId={plan} />
  );
}

it("F22: a Guide mark's delayed callback from plan A is discarded; measured again under B, it is sent once as plan_B", async () => {
  vi.useFakeTimers();
  MarkObserver.all = [];
  vi.stubGlobal("IntersectionObserver", MarkObserver);
  const mark = cue("g1", 0);
  const view = render(<GuideMarkHarness plan="plan_A" mark={mark} />);
  const node = view.container.querySelector(`[data-cue-mark="${mark.cueId}"]`)!;
  const generationA = MarkObserver.all.find((observer) => observer.targets.includes(node))!;
  expect(generationA).toBeDefined();
  // The browser samples the mark in view under A; plan B renders before the callback runs.
  view.rerender(<GuideMarkHarness plan="plan_B" mark={mark} />);
  act(() => generationA.deliver(node));
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  // The A sighting is never sent, under either plan's id.
  expect(api.readerCueImpressions).not.toHaveBeenCalled();
  // B's own observer measures the mark again: sent once, as plan_B.
  const generationB = MarkObserver.all.filter((observer) => observer.connected && observer.targets.includes(node));
  expect(generationB).toHaveLength(1);
  act(() => generationB[0].deliver(node));
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  expect(api.readerCueImpressions.mock.calls.map((call) => call[0])).toEqual([
    { extractionId: "A", visitId: "visit_A", planId: "plan_B", entries: [{ cueId: "cue_g1", shown: true }] }]);
});

// -- Fix round 8 (verify) ------------------------------------------------------------------------

it("F24: 'fewer' goes to the plan the cue was first seen on, after its first receipt failed and the plan changed", async () => {
  vi.useFakeTimers();
  api.readerCueImpressions.mockRejectedValueOnce(new Error("busy")).mockRejectedValueOnce(new Error("busy"))
    .mockResolvedValue({ recorded: [] });
  const guideMark = cue("a1", 0);
  const { result, rerender } = renderHook(({ plan }: { plan: string }) => useCueImpressions({
    extractionId: "A", cues: cues([guideMark], [], "tk1", plan), placement: EMPTY, surface: "pdf",
    bodyRef: body([]), visitId: () => "visit_A",
  }), { initialProps: { plan: "plan_A" } });
  act(() => result.current.noteShown(guideMark, "plan_A"));
  // The receipt and its one retry both fail: nothing is stored.
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_RETRY_MS + 10); });
  expect(api.readerCueImpressions).toHaveBeenCalledTimes(2);
  rerender({ plan: "plan_B" });
  act(() => result.current.noteFewer(guideMark));
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  expect(api.readerCueImpressions.mock.calls[2][0]).toEqual({ extractionId: "A", visitId: "visit_A", planId: "plan_A",
    entries: [{ cueId: "cue_a1", response: "fewer" }] });
});

let exposedImpressions: ReturnType<typeof useCueImpressions> | null = null;

function DiscoveredMarkHarness({ plan, mark, surface }: { plan: string; mark: ReaderCueDto; surface: "pdf" | "text" }) {
  const served = cues([mark], [], "tk1", plan);
  const ref = useRef(Object.assign(document.createElement("div"), { innerHTML: `<p data-span-id="${mark.spanId}"></p>` }) as HTMLDivElement);
  const placement = useRef<CuePlacement>({ shown: [mark], suppressed: [], heldOutPlaced: [], heldOutSuppressed: [] });
  const impressions = useCueImpressions({ extractionId: "A", cues: served, placement: placement.current, surface,
    bodyRef: ref, visitId: () => "visit_A" });
  exposedImpressions = impressions;
  const noop = () => undefined;
  return (
    <MarginMark cue={mark} open={false} onOpenChange={noop} surface={surface} canCheckMe={false} checkPhase="idle"
      onOpenEarlier={noop} onCheckMe={noop} onNotRelevant={noop} onFewer={noop} onOffBook={noop}
      onOffEverywhere={noop} onSeen={(seenOn) => impressions.noteShown(mark, seenOn)} planId={plan} />
  );
}

for (const surface of ["pdf", "text"] as const) {
  for (const how of ["observed", "hovered", "focused", "clicked"] as const) {
    it(`F25: a discovered mark ${how} on the ${surface} under plan A keeps plan A for its taps after plan B`, async () => {
      vi.useFakeTimers();
      MarkObserver.all = [];
      vi.stubGlobal("IntersectionObserver", MarkObserver);
      const mark = discovered("d1", 0);
      const view = render(<DiscoveredMarkHarness plan="plan_A" mark={mark} surface={surface} />);
      const node = view.container.querySelector(`[data-cue-mark="${mark.cueId}"]`) as HTMLButtonElement;
      if (how === "observed") {
        const live = MarkObserver.all.filter((observer) => observer.connected && observer.targets.includes(node));
        act(() => live[0].deliver(node));
      } else if (how === "hovered") {
        fireEvent.mouseEnter(node);
      } else if (how === "focused") {
        fireEvent.focus(node);
      } else {
        fireEvent.click(node);
      }
      view.rerender(<DiscoveredMarkHarness plan="plan_B" mark={mark} surface={surface} />);
      expect(exposedImpressions!.planFor(mark)).toBe("plan_A");
      // The PDF measurement policy is unchanged: a discovered mark's own sighting is no receipt.
      await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
      expect(api.readerCueImpressions).not.toHaveBeenCalled();
    });
  }
}

// -- Fix round 9 (verify) ------------------------------------------------------------------------

it("F26: a discovered mark seen under A before its passage counted is recorded under A when the passage counts under B", async () => {
  vi.useFakeTimers();
  MarkObserver.all = [];
  vi.stubGlobal("IntersectionObserver", MarkObserver);
  const mark = discovered("d1", 0);
  const view = render(<DiscoveredMarkHarness plan="plan_A" mark={mark} surface="text" />);
  const node = view.container.querySelector(`[data-cue-mark="${mark.cueId}"]`) as HTMLButtonElement;
  // The mark is in view under A; its passage has not met the criterion yet.
  const markObserver = MarkObserver.all.find((observer) => observer.connected && observer.targets.includes(node))!;
  act(() => markObserver.deliver(node));
  view.rerender(<DiscoveredMarkHarness plan="plan_B" mark={mark} surface="text" />);
  // Under B the passage's (new generation's) observer sees it qualify.
  const passageObservers = MarkObserver.all.filter((observer) => observer.connected
    && observer.targets.some((target) => target.getAttribute("data-span-id") === mark.spanId));
  expect(passageObservers).toHaveLength(1);
  const passage = passageObservers[0].targets.find((target) => target.getAttribute("data-span-id") === mark.spanId)!;
  act(() => passageObservers[0].deliver(passage));
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  expect(api.readerCueImpressions.mock.calls.map((call) => call[0])).toEqual([
    { extractionId: "A", visitId: "visit_A", planId: "plan_A", entries: [{ cueId: "dcue_d1", shown: true }] }]);
});

it("F26: a Guide mark whose receipt failed twice under A is recorded under A when it is observed again under B", async () => {
  vi.useFakeTimers();
  api.readerCueImpressions.mockRejectedValueOnce(new Error("busy")).mockRejectedValueOnce(new Error("busy"))
    .mockResolvedValue({ recorded: [] });
  MarkObserver.all = [];
  vi.stubGlobal("IntersectionObserver", MarkObserver);
  const mark = cue("g1", 0);
  const view = render(<GuideMarkHarness plan="plan_A" mark={mark} />);
  const node = view.container.querySelector(`[data-cue-mark="${mark.cueId}"]`)!;
  const live = () => MarkObserver.all.filter((observer) => observer.connected && observer.targets.includes(node));
  act(() => live()[0].deliver(node));
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_RETRY_MS + 10); });
  expect(api.readerCueImpressions).toHaveBeenCalledTimes(2);
  view.rerender(<GuideMarkHarness plan="plan_B" mark={mark} />);
  act(() => live()[0].deliver(node));
  await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
  expect(api.readerCueImpressions).toHaveBeenCalledTimes(3);
  expect(api.readerCueImpressions.mock.calls[2][0]).toEqual({ extractionId: "A", visitId: "visit_A", planId: "plan_A",
    entries: [{ cueId: "cue_g1", shown: true }] });
});

// -- Fix round 10 (verify) -----------------------------------------------------------------------

for (const away of [null, "B"] as const) {
  it(`F27: with no funnel visit, A → ${away === null ? "Library" : "an unseen B"} → A is a new visit with its own plan and a fresh receipt`, async () => {
    vi.useFakeTimers();
    const guideMark = cue("a1", 0);
    const found = discovered("a2", 1);
    const { result, rerender } = renderHook(({ extraction, plan }: { extraction: string | null; plan: string }) =>
      useCueImpressions({ extractionId: extraction, cues: cues([guideMark, found], [], "tk1", plan), placement: EMPTY,
        surface: "pdf", bodyRef: body([]), visitId: () => null }),
    { initialProps: { extraction: "A" as string | null, plan: "plan_A" } });
    act(() => {
      result.current.noteShown(guideMark, "plan_A");
      result.current.noteShown(found, "plan_A");  // remembered, no receipt (PDF)
    });
    await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
    const first = api.readerCueImpressions.mock.calls[0][0] as { visitId: string; planId: string };
    expect(first.planId).toBe("plan_A");
    const firstVisit = result.current.visitId();
    expect(firstVisit).toBe(first.visitId);
    // Away (nothing there asks for a visit), then back to A under a new plan.
    rerender({ extraction: away, plan: "plan_X" });
    rerender({ extraction: "A", plan: "plan_B" });
    act(() => {
      result.current.noteShown(guideMark, "plan_B");
      result.current.noteShown(found, "plan_B");
    });
    const secondVisit = result.current.visitId();
    expect(secondVisit).toMatch(/^cues_/);
    expect(secondVisit).not.toBe(firstVisit);
    expect(result.current.planFor(found)).toBe("plan_B");
    expect(result.current.planFor(guideMark)).toBe("plan_B");
    await act(async () => { vi.advanceTimersByTime(IMPRESSION_FLUSH_MS + 10); });
    // A fresh receipt in the new visit, under the new plan.
    expect(api.readerCueImpressions.mock.calls.map((call) => call[0])).toEqual([
      { extractionId: "A", visitId: firstVisit, planId: "plan_A", entries: [{ cueId: "cue_a1", shown: true }] },
      { extractionId: "A", visitId: secondVisit, planId: "plan_B", entries: [{ cueId: "cue_a1", shown: true }] },
    ]);
  });
}
