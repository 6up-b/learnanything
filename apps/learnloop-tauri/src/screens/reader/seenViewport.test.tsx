// Every readable passage SHOWN in the Reader's viewport during the learner's own movement is observed, not only the
// one under the reading marker: what was on screen when their hand started the movement, and what each frame of the
// movement displayed, so a screenful-at-a-time read covers the whole range it read and a continuous scroll covers what
// crossed the view. A restore, a placement, a Contents jump, a seek or a completion observes nothing until the learner
// moves again. A step that displays nothing in between (the End key, a scrollbar jump) observes its two ends only. A
// page-only PDF observes the passages whose share of a page was shown; a video observes the cues played.
//
// The page is faked: the reading area is 600 px tall at the window's top, and each passage (or page) has a fixed place
// in the scrolled content; `scrollY` is how far the content is scrolled.
import { act, cleanup, renderHook } from "@testing-library/react";
import { createRef, useState } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type {
  ReaderGuidePlanDto, ReaderGuideSectionDto, ReaderPdfViewDto, ReaderRenderViewDto, ReaderWatchPlanDto,
} from "../../api/dto";
import { readerRenderViewFixture } from "../../fixtures/readerRenderView";
import { passagesInView } from "./readingPosition";
import { SEEN_REPORT_MS, useReadingProgress, type ReadingProgressInput } from "./useReadingProgress";

const api = vi.hoisted(() => ({
  readerLogActivity: vi.fn(), readerNoteReadingProgress: vi.fn(), readerAuthorSectionQuestion: vi.fn(),
  readerGuidePlan: vi.fn(), readerMarkSectionProgress: vi.fn(), readerSavedPlace: vi.fn(),
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("./guidePlan", () => ({ useGuideDiagnosisRefresh: () => undefined }));

const VIEW = 600;
const PASSAGE = 60;
let scrollY = 0;
const layout = new Map<Element, { top: number; height: number }>();

function box(top: number, height: number, width = 400): DOMRect {
  return { top, bottom: top + height, left: 0, right: width, width, height, x: 0, y: top, toJSON: () => ({}) } as DOMRect;
}

const ids = (prefix: string, from: number, to: number) => Array.from({ length: to - from }, (_, i) => `${prefix}${from + i}`);

function section(id: string, spanIds: string[]): ReaderGuideSectionDto {
  return {
    id, label: `Section ${id}`, startSpanId: spanIds[0], endSpanId: spanIds[spanIds.length - 1], spanIds,
    question: null, suggestedPassages: [],
  } as unknown as ReaderGuideSectionDto;
}

function viewOf(spanIds: string[]): ReaderRenderViewDto {
  return {
    ...readerRenderViewFixture,
    blocks: spanIds.map((spanId) => ({ ...readerRenderViewFixture.blocks[1], spanId, displayNodeId: `node-${spanId}`, markdown: `Passage ${spanId}.` })),
  };
}

function planOf(view: ReaderRenderViewDto, sections: ReaderGuideSectionDto[]): ReaderGuidePlanDto {
  return {
    version: 1, sourceId: view.sourceId, extractionId: view.extractionId, personalized: false, selectionBasis: "",
    goalContext: null, sections,
  };
}

/** The text view: one box per passage, stacked `PASSAGE` px apart from the content's top. */
function textBody(spanIds: string[], extra: (node: HTMLElement, spanId: string) => void = () => undefined): HTMLDivElement {
  const body = document.createElement("div");
  spanIds.forEach((spanId, index) => {
    const node = document.createElement("div");
    node.dataset.spanId = spanId;
    extra(node, spanId);
    body.appendChild(node);
    layout.set(node, { top: index * PASSAGE, height: PASSAGE });
  });
  document.body.appendChild(body);
  return body;
}

/** The original PDF without boxes: pages `height` px tall, one after another. */
function pagesBody(pages: number, height: number): HTMLDivElement {
  const body = document.createElement("div");
  for (let page = 0; page < pages; page += 1) {
    const node = document.createElement("div");
    node.dataset.pdfPage = String(page);
    body.appendChild(node);
    layout.set(node, { top: page * height, height });
  }
  document.body.appendChild(body);
  return body;
}

let body: HTMLDivElement | null = null;

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "requestAnimationFrame", "cancelAnimationFrame", "Date"] });
  for (const fn of Object.values(api)) fn.mockReset();
  api.readerNoteReadingProgress.mockResolvedValue({});
  api.readerMarkSectionProgress.mockResolvedValue({});
  scrollY = 0;
  layout.clear();
  vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(function (this: Element) {
    if (this === body) return box(0, VIEW);
    const place = layout.get(this);
    return place ? box(place.top - scrollY, place.height) : box(0, 0, 0);
  });
});
afterEach(() => {
  cleanup();
  body?.remove();
  body = null;
  vi.restoreAllMocks();
  vi.useRealTimers();
});

function useHarness(input: Partial<ReadingProgressInput>) {
  const [activeSpan, setActiveSpan] = useState<string | null>(null);
  return useReadingProgress({
    render: null, offline: false, blocks: [], guidePlan: null, setGuidePlan: vi.fn(), guideLoading: false,
    pdfView: null, pdfViewPending: false, surface: "text", watch: null, watchLoading: false, mode: "skim",
    inquiry: true, muted: false, activeSpan, setActiveSpan, bodyRef: { current: body },
    railRef: createRef<HTMLDivElement>(), paneRef: createRef(), watchRef: createRef(), noteProactive: vi.fn(() => true),
    showGuideRail: vi.fn(), ...input,
  });
}

type Harness = { current: ReturnType<typeof useReadingProgress> };
type Report = { sectionId: string; spansSeen?: number; seenSpanIds?: string[]; reachedEnd?: boolean };
const reports = () => api.readerNoteReadingProgress.mock.calls.map(([input]) => input as Report);
const passagesSent = (sectionId?: string) =>
  reports().filter((one) => sectionId === undefined || one.sectionId === sectionId).flatMap((one) => one.seenSpanIds ?? []);
const sorted = (list: string[]) => [...list].sort();

async function wait(ms: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

/** The learner's own movement: their hand on the page (wheel, touch, the scrollbar) and then the frames it scrolls
 *  through, one scroll event and one frame each. One frame is a step that displays nothing in between. */
async function moveByHand(result: Harness, frames: number[]) {
  await act(async () => {
    result.current.noteUserScroll();
    for (const y of frames) {
      scrollY = y;
      result.current.onReadingScroll();
      await vi.advanceTimersByTimeAsync(17);
    }
  });
}

/** The same with a scroll key: the keydown the Reader listens for on the window, then the frames. */
async function moveByKey(result: Harness, key: string, frames: number[]) {
  await act(async () => {
    window.dispatchEvent(new KeyboardEvent("keydown", { key }));
    for (const y of frames) {
      scrollY = y;
      result.current.onReadingScroll();
      await vi.advanceTimersByTimeAsync(17);
    }
  });
}

/** The page moving without the learner (a restore landing, layout settling, a jump's scroll). */
async function moveByItself(result: Harness, y: number) {
  await act(async () => {
    scrollY = y;
    result.current.onReadingScroll();
    await vi.advanceTimersByTimeAsync(17);
  });
}

async function saved() {
  await wait(SEEN_REPORT_MS + 50);
}

// The live walk's shape: one section of 135 passages (a web-page chapter), read a screenful at a time.
const CHAPTER = ids("w", 0, 135);

function openChapter() {
  body = textBody(CHAPTER);
  const view = viewOf(CHAPTER);
  const plan = planOf(view, [section("ch", CHAPTER)]);
  return renderHook(() => useHarness({ render: view, blocks: view.blocks, guidePlan: plan }));
}

it("a screenful-at-a-time read of a long section observes every passage that was on screen at each stop: the read range, whole", async () => {
  const { result } = openChapter();
  await wait(2000);
  // Ten stops a screenful apart (each step one frame, as a scripted scroll makes it), down to the 100th passage.
  for (let stop = 1; stop <= 9; stop += 1) {
    await moveByHand(result, [stop * VIEW]);
    await wait(3000);
  }
  await saved();
  // Shown during the learner's movement: the first screen (on screen when their hand moved it) to the last stop's
  // bottom edge, 6,000 px down: w0-w99. Nothing below it.
  expect(sorted(passagesSent("ch"))).toEqual(sorted(ids("w", 0, 100)));
  // Each passage goes once.
  expect(passagesSent("ch")).toHaveLength(100);
  // The count is still the marker's position (unchanged): 70% down the last screen, the marker is at w96's foot.
  expect(Math.max(...reports().map((one) => one.spansSeen ?? 0))).toBe(97);
  expect(reports().some((one) => one.reachedEnd)).toBe(false);
});

it("a single continuous scroll observes every passage that crossed the view, the first screen included", async () => {
  const { result } = openChapter();
  await wait(2000);
  // A wheel's movement: 40 px a frame, from the top to 3,000 px.
  await moveByHand(result, Array.from({ length: 75 }, (_, i) => (i + 1) * 40));
  await saved();
  expect(sorted(passagesSent("ch"))).toEqual(sorted(ids("w", 0, 60)));
});

it("Page Down observes each screen it shows, and the one it started from", async () => {
  const { result } = openChapter();
  await wait(2000);
  for (const y of [540, 1080, 1620]) await moveByKey(result, "PageDown", [y]);
  await saved();
  // 1,620 + 600 = 2,220 px: w0-w36 were on screen.
  expect(sorted(passagesSent("ch"))).toEqual(sorted(ids("w", 0, 37)));
});

it("the End key observes the screen it left and the screen it lands on: the passages in between were never displayed", async () => {
  const { result } = openChapter();
  await wait(2000);
  await moveByKey(result, "End", [CHAPTER.length * PASSAGE - VIEW]);
  await saved();
  expect(sorted(passagesSent("ch"))).toEqual(sorted([...ids("w", 0, 10), ...ids("w", 125, 135)]));
  // The bottom reached by the learner's own key is the section's end.
  expect(reports().filter((one) => one.reachedEnd).map((one) => one.sectionId)).toEqual(["ch"]);
});

it("a restore observes nothing, nor the page settling after it; the learner's own movement then observes the view", async () => {
  const { result } = openChapter();
  act(() => result.current.placeAtOpen(readerRenderViewFixture.sourceId, "w60", null));
  // The restore's own scroll (w60 centred) and a later settling scroll with no hand on the page.
  await moveByItself(result, 60 * PASSAGE - 270);
  await wait(2000);
  await moveByItself(result, 60 * PASSAGE - 300);
  await wait(4000);
  expect(reports()).toEqual([]);
  // The learner scrolls on 120 px: what was on screen when they did (w55-w64) and what came into view (to w66).
  await moveByHand(result, [3340, 3380, 3420]);
  await saved();
  expect(sorted(passagesSent("ch"))).toEqual(sorted(ids("w", 55, 67)));
});

it("a Contents jump observes nothing where it lands, not even with a hand on the page while it settles; moving on after it does", async () => {
  const { result } = openChapter();
  await wait(2000);
  await moveByHand(result, [40]);
  await saved();
  expect(sorted(passagesSent("ch"))).toEqual(sorted(ids("w", 0, 11)));
  act(() => result.current.jumpToSpan("w100"));
  await moveByItself(result, 100 * PASSAGE - 270);
  // A wheel while the jump is still settling is not reading yet.
  await moveByHand(result, [100 * PASSAGE - 260]);
  await wait(2000);
  await saved();
  expect(passagesSent("ch")).toHaveLength(11);
  // After it settled, the learner's own scroll: the screen they moved from (w95-w105) and the frame's (to w106).
  await moveByHand(result, [100 * PASSAGE - 220]);
  await saved();
  expect(sorted(passagesSent("ch"))).toEqual(sorted([...ids("w", 0, 11), ...ids("w", 95, 107)]));
});

it("a short section's last passage and the book's last passage are observed once shown, and each end is reported", async () => {
  // A short section that fits the window, a long one, and the book's last section (three passages at its bottom).
  const spans = ids("x", 0, 26);
  body = textBody(spans);
  const view = viewOf(spans);
  const plan = planOf(view, [section("a", spans.slice(0, 3)), section("b", spans.slice(3, 23)), section("c", spans.slice(23))]);
  const { result } = renderHook(() => useHarness({ render: view, blocks: view.blocks, guidePlan: plan }));
  await wait(2000);
  // A small scroll: section a's last passage (x2) was on screen; it never comes under the marker 70% down.
  await moveByHand(result, [50, 100]);
  await saved();
  expect(reports().filter((one) => one.reachedEnd).map((one) => one.sectionId)).toEqual(["a"]);
  // Down to the bottom of the book: its last passage (x25) sits at the bottom of the view, below the marker.
  await moveByHand(result, Array.from({ length: 22 }, (_, i) => 100 + (i + 1) * 40).filter((y) => y <= 960).concat([960]));
  await saved();
  // Section b's end (x22) was shown along the way too.
  expect(sorted(reports().filter((one) => one.reachedEnd).map((one) => one.sectionId))).toEqual(["a", "b", "c"]);
  expect(sorted(passagesSent("c"))).toEqual(["x23", "x24", "x25"]);
  expect(reports().find((one) => one.sectionId === "c" && one.reachedEnd)?.seenSpanIds).toContain("x25");
});

it("a long first report goes whole, is sent again whole after a failed save, and once acknowledged never again", async () => {
  api.readerNoteReadingProgress.mockRejectedValueOnce({ code: "database_busy", message: "busy", retryable: true });
  const { result } = openChapter();
  await wait(2000);
  // Nine quick stops, inside one report's gathering: the first report carries 100 passages.
  for (let stop = 1; stop <= 9; stop += 1) await moveByHand(result, [stop * VIEW]);
  await saved();
  expect(reports()).toHaveLength(1);
  expect(sorted(reports()[0].seenSpanIds ?? [])).toEqual(sorted(ids("w", 0, 100)));
  await wait(SEEN_REPORT_MS * 2 + 50);
  expect(reports()).toHaveLength(2);
  expect(reports()[1].seenSpanIds).toEqual(reports()[0].seenSpanIds);
  // Back up over what was read: everything is acknowledged, so nothing goes again.
  await moveByHand(result, [3000, 1200]);
  await saved();
  await wait(SEEN_REPORT_MS * 8);
  expect(reports()).toHaveLength(2);
});

it("a folded passage (covered while the learner tries the next step) is not shown, so not observed", async () => {
  body = textBody(CHAPTER, (node, spanId) => {
    if (spanId === "w3" || spanId === "w4") node.dataset.folded = "";
  });
  const view = viewOf(CHAPTER);
  const plan = planOf(view, [section("ch", CHAPTER)]);
  const { result } = renderHook(() => useHarness({ render: view, blocks: view.blocks, guidePlan: plan }));
  await wait(2000);
  await moveByHand(result, [40]);
  await saved();
  expect(sorted(passagesSent("ch"))).toEqual(sorted(ids("w", 0, 11).filter((id) => id !== "w3" && id !== "w4")));
});

it("a page-only PDF observes the passages whose share of a page was shown during the learner's movement", async () => {
  // Four pages 1,000 px tall, three passages each: a passage is a third of its page, in order.
  const pageSpans = [0, 1, 2, 3].flatMap((page) => ["a", "b", "c"].map((part) => ({ spanId: `p${page}${part}`, page })));
  const spans = pageSpans.map((entry) => entry.spanId);
  body = pagesBody(4, 1000);
  const view = viewOf(spans);
  const plan = planOf(view, [section("one", spans.slice(0, 6)), section("two", spans.slice(6))]);
  const pdfView = {
    available: true, fileName: "book.pdf", extractionId: view.extractionId, sourceId: view.sourceId, revisionId: null,
    blocks: [], pageSpans,
  } as ReaderPdfViewDto;
  const { result } = renderHook(() => useHarness({ render: view, blocks: view.blocks, guidePlan: plan, pdfView, surface: "pdf" }));
  await wait(2000);
  // From the top (page 0's first 60% on screen: p0a, p0b) through 350 and 700 to 1,050 (page 1 from 5% to 65%).
  await moveByHand(result, [350, 700, 1050]);
  await saved();
  expect(sorted(passagesSent())).toEqual(["p0a", "p0b", "p0c", "p1a", "p1b"]);
  // An instant step from there to page 3 displays page 2 in no frame: its passages are not observed.
  await moveByHand(result, [3050]);
  await saved();
  expect(sorted(passagesSent())).toEqual(["p0a", "p0b", "p0c", "p1a", "p1b", "p3a", "p3b"]);
});

it("a video observes the cues played: the one a seek started from once playback moves on, never a seek's or a pause's", async () => {
  const cues = ids("c", 0, 10);
  const view = viewOf(cues);
  const plan = planOf(view, [section("v", cues)]);
  const watch = { sourceId: view.sourceId, videoId: "vid", embedUrl: "", pausePoints: [] } as unknown as ReaderWatchPlanDto;
  const { result } = renderHook(() => useHarness({ render: view, blocks: view.blocks, guidePlan: plan, watch }));
  act(() => result.current.onPlaybackSeek("c1"));
  await wait(2000);
  await saved();
  expect(reports()).toEqual([]);
  // Playback goes on from c1: c1 was played, and c2, c3 as they play.
  for (const cue of ["c2", "c3"]) {
    act(() => result.current.onPlaybackSpan(cue, true));
    await wait(1000);
  }
  await saved();
  expect(passagesSent("v")).toEqual(expect.arrayContaining(["c1", "c2", "c3"]));
  expect(passagesSent("v")).toHaveLength(3);
  // A seek to c6 and a cue change while paused observe nothing.
  act(() => result.current.onPlaybackSeek("c6"));
  await wait(2000);
  act(() => result.current.onPlaybackSpan("c7", false));
  await wait(2000);
  await saved();
  expect(passagesSent("v")).toHaveLength(3);
  // Playing on from c7: c7 was played, and c8.
  act(() => result.current.onPlaybackSpan("c8", true));
  await wait(1000);
  await saved();
  expect(sorted(passagesSent("v"))).toEqual(["c1", "c2", "c3", "c7", "c8"]);
});

it("passagesInView: a passage is shown when part of it lies inside the reading area; on a page-only PDF, its share of the page", () => {
  body = textBody(["t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8", "t9", "t10", "t11"]);
  // The area is 0-600; at 30 px t0 is 30 px above it, half of it shown; t10 starts at 570, 30 px of it shown.
  scrollY = 30;
  expect(passagesInView(body, null)).toEqual(["t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8", "t9", "t10"]);
  // At 60 px t0's bottom touches the area's top edge (no part of it inside), and t10 ends exactly at its bottom.
  scrollY = 60;
  expect(passagesInView(body, null)).toEqual(["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8", "t9", "t10"]);
  body.remove();
  layout.clear();
  body = pagesBody(2, 1000);
  const pages = [{ spanId: "a", page: 0 }, { spanId: "b", page: 0 }, { spanId: "c", page: 1 }];
  // Page 0 from 50% to 100% on screen (b's half), page 1's first 10% (c).
  scrollY = 500;
  expect(passagesInView(body, pages)).toEqual(["b", "c"]);
  // Page 0 from 40%: the last tenth of a's half.
  scrollY = 400;
  expect(passagesInView(body, pages)).toEqual(["a", "b"]);
});
