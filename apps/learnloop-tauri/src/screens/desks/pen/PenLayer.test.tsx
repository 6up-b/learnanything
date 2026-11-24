// The pen layer on a source window (spec §10.10): strokes drawn with pen pointer events on a laid-out page (jsdom
// lays nothing out, so the page's geometry is stubbed: one line of text per passage), each recognition becoming
// the annotation the spec names with its ink saved through the one write sequence; touch, a paused window and an
// unrecognized stroke keep nothing.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { InkTranscribeJobDto } from "../../../api/dto";
import { Poller } from "../../../api/poller";
import type { PenSurface } from "../source/types";
import { WindowLifecycleContext, type WindowState } from "../lifecycle";
import { PenHostContext, type PenApi, type PenHost } from "./host";
import { InkCache } from "./inkCache";
import { PenLayer, STRIKE_WORDS } from "./PenLayer";

// Each passage is one line: left 100, 8 px a character, 24 px tall, the first at y 100, then every 30 px.
const LEFT = 100;
const CHAR = 8;
const LINE = 24;
const TEXTS = ["the quick brown fox jumps over the lazy dog", "a second passage of plain words to mark"];

let body: HTMLElement;
let paragraphs: HTMLElement[];

function lineOf(index: number) {
  return { top: 100 + index * 30, height: LINE };
}

function rect(left: number, top: number, width: number, height: number): DOMRect {
  return { left, top, width, height, right: left + width, bottom: top + height, x: left, y: top, toJSON: () => ({}) } as DOMRect;
}

function paragraphIndex(node: Node): number {
  return paragraphs.findIndex((p) => p.contains(node));
}

function rangeRects(range: Range): DOMRect[] {
  const s = paragraphIndex(range.startContainer);
  const e = paragraphIndex(range.endContainer);
  if (s < 0 || e < 0) return [];
  const out: DOMRect[] = [];
  for (let i = s; i <= e; i += 1) {
    const text = TEXTS[i];
    const from = i === s ? range.startOffset : 0;
    const to = i === e ? range.endOffset : text.length;
    const { top, height } = lineOf(i);
    out.push(rect(LEFT + from * CHAR, top, Math.max(0, to - from) * CHAR, height));
  }
  return out;
}

beforeEach(() => {
  body = document.createElement("div");
  paragraphs = TEXTS.map((text, i) => {
    const p = document.createElement("p");
    p.dataset.spanId = `s${i + 1}`;
    p.textContent = text;
    p.getBoundingClientRect = () => rect(LEFT, lineOf(i).top, 400, LINE);
    body.appendChild(p);
    return p;
  });
  body.getBoundingClientRect = () => rect(0, 0, 900, 600);
  document.body.appendChild(body);
  (document as unknown as { caretRangeFromPoint: (x: number, y: number) => Range | null }).caretRangeFromPoint = (x, y) => {
    const i = paragraphs.findIndex((_p, k) => y >= lineOf(k).top && y < lineOf(k).top + LINE);
    if (i < 0 || x < LEFT || x > LEFT + 400) return null;
    const node = paragraphs[i].firstChild!;
    const range = document.createRange();
    range.setStart(node, Math.max(0, Math.min(TEXTS[i].length, Math.round((x - LEFT) / CHAR))));
    return range;
  };
  Range.prototype.getClientRects = function getClientRects(this: Range) {
    const rects = rangeRects(this);
    return Object.assign(rects, { item: (k: number) => rects[k] }) as unknown as DOMRectList;
  };
  Range.prototype.getBoundingClientRect = function getBoundingClientRect(this: Range) {
    const rects = rangeRects(this);
    if (!rects.length) return rect(0, 0, 0, 0);
    const left = Math.min(...rects.map((r) => r.left));
    const top = Math.min(...rects.map((r) => r.top));
    return rect(left, top, Math.max(...rects.map((r) => r.right)) - left, Math.max(...rects.map((r) => r.bottom)) - top);
  };
});

afterEach(() => {
  cleanup();
  body.remove();
});

function fakeApi(job: Partial<InkTranscribeJobDto> = {}): PenApi {
  let annotation = 0;
  return {
    readerCapture: vi.fn(async () => ({ annotationId: `ann_${++annotation}`, outboxId: "o", interactionEventId: "e", anchorStatus: "exact" as const, captureKind: "annotation", deduplicated: false, receipt: "r" })),
    readerDeleteIntentAnnotation: vi.fn(async () => ({ eventId: "del" })),
    readerEditAnnotation: vi.fn(async () => ({ annotationId: "ann_1", status: "exact" as const })),
    readerSourceAnnotations: vi.fn(async () => ({ annotations: [] })),
    inkList: vi.fn(async () => ({ version: 1, padId: null, sourceId: "src", owners: [] })),
    inkTranscribe: vi.fn(async () => ({ version: 1, jobId: null, status: "failed" as const, done: true, result: null,
      error: { code: "unavailable", message: "text recognition isn't set up", retryable: true, details: null }, ...job })),
    inkTranscribeJob: vi.fn(),
    inkTranscribeCancel: vi.fn(),
  };
}

function setup({ state = "active" as WindowState, on = true, api = fakeApi() } = {}) {
  let n = 0;
  const host: PenHost = {
    on,
    simulate: false,
    setOn: vi.fn(),
    saveInk: vi.fn(),
    eraseInk: vi.fn(),
    settled: vi.fn(async () => "saved" as const),
    mintId: (prefix) => `${prefix}_${++n}`,
    api,
    poller: new Poller({ setInterval: () => 1, clearInterval: () => undefined }),
    askCompanion: vi.fn(),
    ink: undefined as unknown as InkCache,
  };
  host.ink = new InkCache({ api, poller: host.poller, settled: host.settled, refreshPad: async () => undefined });
  const surface: PenSurface = {
    body,
    identity: { sourceId: "src", revisionId: "rev", extractionId: "ext", renderViewId: "rv" },
    nodesFor: vi.fn((range: Range) => [{ spanId: "s1", quote: range.toString() }]),
  };
  const ui = (value: PenHost) => (
    <WindowLifecycleContext.Provider value={{ windowId: "w1", state }}>
      <PenHostContext.Provider value={value}>
        <PenLayer surface={surface} />
      </PenHostContext.Provider>
    </WindowLifecycleContext.Provider>
  );
  const view = render(ui(host));
  return { host, surface, api, rerenderOn: (now: boolean) => view.rerender(ui({ ...host, on: now })) };
}

function pointer(type: string, x: number, y: number, over: Record<string, unknown> = {}) {
  const { button = 0, buttons = 1, ...rest } = over as { button?: number; buttons?: number };
  const event = new MouseEvent(type, { bubbles: true, cancelable: true, clientX: x, clientY: y, button, buttons });
  Object.assign(event, { pointerId: 1, pointerType: "pen", pressure: 0.5, tiltX: 0, tiltY: 0, ...rest });
  return event;
}

function draw(points: Array<[number, number]>, over: Record<string, unknown> = {}) {
  const target = paragraphs[0];
  act(() => {
    target.dispatchEvent(pointer("pointerdown", points[0][0], points[0][1], over));
    for (const [x, y] of points.slice(1)) target.dispatchEvent(pointer("pointermove", x, y, over));
    target.dispatchEvent(pointer("pointerup", points[points.length - 1][0], points[points.length - 1][1], over));
  });
}

const flat = (x0: number, x1: number, y: number): Array<[number, number]> => {
  const out: Array<[number, number]> = [];
  for (let x = x0; x <= x1; x += 6) out.push([x, y]);
  return out;
};

/** ↵ outside a text field: the margin note being written ends (it is kept and read then). */
function endNote() {
  act(() => {
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  });
}

async function settle() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

describe("the pen layer", () => {
  it("an underline becomes a highlight snapped to the words, with its ink saved in the one write sequence", async () => {
    const { host, api, surface } = setup();
    draw(flat(140, 300, 100 + LINE + 2)); // under the first line
    await settle();
    expect(api.readerCapture).toHaveBeenCalledTimes(1);
    const capture = vi.mocked(api.readerCapture).mock.calls[0][0];
    expect(capture).toMatchObject({ sourceId: "src", revisionId: "rev", extractionId: "ext", renderViewId: "rv", action: "highlight", learnerText: "" });
    expect(surface.nodesFor).toHaveBeenCalled();
    // x 142..294 at 8 px a character ends inside "quick" and "jumps": the highlight takes both words whole.
    expect(vi.mocked(surface.nodesFor).mock.calls[0][0].toString()).toBe("quick brown fox jumps");
    expect(host.saveInk).toHaveBeenCalledTimes(1);
    const ink = vi.mocked(host.saveInk).mock.calls[0][0];
    expect(ink.owner).toEqual({ annotationId: "ann_1" });
    expect(ink.pointerMeta.pointerType).toBe("pen");
    expect(ink.strokes).toHaveLength(1);
    expect(ink.strokes[0].points[0]).toEqual([140, 126, 0, 0.5, 0, 0]);
    expect(screen.getByText("underline → highlight")).toBeTruthy();
    expect(body.querySelector('[data-pen-mark="underline"]')).not.toBeNull();
    expect(body.querySelector('path[data-pen-stroke="underline"]')).not.toBeNull();
  });

  it("a strike becomes the disposition the spec names", async () => {
    const { api } = setup();
    draw(flat(140, 300, 100 + LINE * 0.55));
    await settle();
    expect(vi.mocked(api.readerCapture).mock.calls[0][0]).toMatchObject({ action: "disposition", learnerText: STRIKE_WORDS });
    expect(body.querySelector(".desk-pen-strike")).not.toBeNull();
  });

  it("a bracket in the margin highlights the paragraphs it spans, each anchored whole", async () => {
    const { api } = setup();
    const points: Array<[number, number]> = [[88, 100]];
    for (let y = 100; y <= 150; y += 8) points.push([80, y]);
    points.push([88, 150]);
    draw(points);
    await settle();
    expect(vi.mocked(api.readerCapture).mock.calls[0][0]).toMatchObject({
      action: "highlight", rawSelection: { extractionId: "ext", nodes: [{ spanId: "s1", start: 0, end: 1_000_000 }, { spanId: "s2", start: 0, end: 1_000_000 }] },
    });
    expect(body.querySelectorAll('[data-pen-mark="bracket"]')).toHaveLength(2);
  });

  it("a margin note is an interpretation holding the ink; unreadable handwriting is said plainly and the learner's words are kept", async () => {
    const { api, host } = setup();
    const points: Array<[number, number]> = [];
    for (let t = 0; t < 1; t += 0.02) points.push([530 + t * 150, 110 + Math.sin(t * 60) * 7]);
    draw(points);
    endNote();
    await settle();
    await settle();
    expect(vi.mocked(api.readerCapture).mock.calls[0][0]).toMatchObject({ action: "interpretation", rawSelection: { nodes: [{ spanId: "s1", start: 0, end: 1_000_000 }] } });
    const inkId = vi.mocked(host.saveInk).mock.calls[0][0].inkId;
    expect(api.inkTranscribe).toHaveBeenCalledWith({ inkId });
    expect(screen.getByText("handwriting can't be read yet: text recognition isn't set up · to add it, paste a z.ai API key in Settings, under Ingestion, or run a local GLM-OCR server · your ink is kept")).toBeTruthy();
    const field = screen.getByLabelText("your note's words");
    fireEvent.change(field, { target: { value: "does the log cancel the exp?" } });
    fireEvent.keyDown(field, { key: "Enter" });
    expect(api.readerEditAnnotation).toHaveBeenCalledWith({ annotationId: "ann_1", learnerText: "does the log cancel the exp?" });
  });

  it("a reading is shown as may be wrong and is never stored as the learner's words until they keep it", async () => {
    const api = fakeApi({ status: "done", error: null, result: { transcriptionId: "it_1", ownerKind: "annotation", ownerId: "ann_1", contentHash: "h", latexMd: "does $e^x$ cancel?", confidenceLabel: "may_be_wrong", model: "m", createdAt: "t", applied: false, reason: null, headVersionId: null } });
    setup({ api });
    const points: Array<[number, number]> = [];
    for (let t = 0; t < 1; t += 0.02) points.push([530 + t * 150, 110 + Math.sin(t * 60) * 7]);
    draw(points);
    endNote();
    await settle();
    await settle();
    const field = screen.getByLabelText("your note's words") as HTMLTextAreaElement;
    expect(field.value).toBe("does $e^x$ cancel?");
    expect(screen.getByText("transcribed · may be wrong · fix it")).toBeTruthy();
    fireEvent.blur(field);
    expect(api.readerEditAnnotation).not.toHaveBeenCalled();
  });

  it("a closed loop selects the words inside and offers the companion; nothing is stored", async () => {
    const { api, host } = setup();
    const points: Array<[number, number]> = [];
    for (let a = 0; a <= Math.PI * 2 - 0.2; a += 0.2) points.push([200 + 70 * Math.cos(a), 112 + 14 * Math.sin(a)]);
    draw(points);
    await settle();
    expect(document.getSelection()?.toString()).toContain("brown");
    expect(api.readerCapture).not.toHaveBeenCalled();
    expect(host.saveInk).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("ask in the companion · c"));
    expect(host.askCompanion).toHaveBeenCalled();
  });

  it("undo takes the mark back: its annotation's delete intent, its marks and ink gone", async () => {
    const { api } = setup();
    draw(flat(140, 300, 100 + LINE + 2));
    await settle();
    fireEvent.click(screen.getByText("undo"));
    expect(api.readerDeleteIntentAnnotation).toHaveBeenCalledWith({ annotationId: "ann_1", reason: "pen undo" });
    expect(body.querySelector('[data-pen-mark="underline"]')).toBeNull();
    expect(body.querySelector('path[data-pen-stroke="underline"]')).toBeNull();
  });

  it("the barrel button erases a mark's ink, taking the mark back", async () => {
    const { api } = setup();
    draw(flat(140, 300, 100 + LINE + 2));
    await settle();
    draw([[200, 126], [205, 126], [210, 126]], { button: 2 });
    expect(api.readerDeleteIntentAnnotation).toHaveBeenCalledWith({ annotationId: "ann_1", reason: "pen undo" });
  });

  it("a stroke it cannot place stays on the page as plain ink, kept for the reading, never a mark", async () => {
    const { api, host } = setup();
    draw([[150, 105], [250, 160], [300, 110], [420, 170]]);
    await settle();
    expect(screen.getByText("Ink on the page. Draw over or beside text to make a mark.")).toBeTruthy();
    expect(api.readerCapture).not.toHaveBeenCalled();
    expect(host.saveInk).toHaveBeenCalledTimes(1);
    expect(vi.mocked(host.saveInk).mock.calls[0][0].owner).toEqual({ extractionId: "ext" });
    expect(body.querySelector('path[data-pen-stroke="ink"]')).not.toBeNull();
    // Its undo erases it (an ink.erase of its strokes); nothing asks to read it.
    fireEvent.click(screen.getByText("undo"));
    expect(host.eraseInk).toHaveBeenCalledWith({ owner: { extractionId: "ext" }, eraseId: expect.any(String), strokeIds: [vi.mocked(host.saveInk).mock.calls[0][0].strokes[0].strokeId] });
    expect(body.querySelector('path[data-pen-stroke="ink"]')).toBeNull();
    expect(api.inkTranscribe).not.toHaveBeenCalled();
  });

  it("the barrel erases plain page ink stroke by stroke", async () => {
    const { host } = setup();
    draw([[150, 105], [250, 160], [300, 110], [420, 170]]);
    await settle();
    draw([[250, 160], [252, 161], [254, 162]], { button: 2 });
    expect(host.eraseInk).toHaveBeenCalledTimes(1);
    expect(body.querySelector('path[data-pen-stroke="ink"]')).toBeNull();
  });

  it("touch never draws; a paused window draws and saves nothing; a pen's first touch turns pen mode on", async () => {
    const first = setup();
    draw(flat(140, 300, 126), { pointerType: "touch" });
    await settle();
    expect(first.api.readerCapture).not.toHaveBeenCalled();
    cleanup();
    const paused = setup({ state: "offscreen" });
    draw(flat(140, 300, 126));
    await settle();
    expect(paused.api.readerCapture).not.toHaveBeenCalled();
    expect(body.querySelector("path")).toBeNull();
    cleanup();
    const off = setup({ on: false });
    draw(flat(140, 300, 126));
    await settle();
    expect(off.host.setOn).toHaveBeenCalledWith(true);
    expect(off.api.readerCapture).toHaveBeenCalled();
  });
});

describe("ink already saved", () => {
  it("is drawn again where it was written, with its mark and its note's words", async () => {
    const api = fakeApi();
    vi.mocked(api.inkList).mockResolvedValue({ version: 1, padId: null, sourceId: "src", owners: [
      { ownerKind: "annotation", ownerId: "ann_u", contentHash: "h1", devicePixelRatio: 1, transcription: null,
        strokes: [{ strokeId: "s1", inkId: "ink_u", points: flat(140, 300, 126).map(([x, y]) => [x, y, 0, 0.5, 0, 0] as [number, number, number, number, number, number]) }] },
      { ownerKind: "annotation", ownerId: "ann_n", contentHash: "h2", devicePixelRatio: 1, transcription: null,
        strokes: [{ strokeId: "s2", inkId: "ink_n", points: [[530, 110, 0, 0.5, 0, 0], [560, 118, 8, 0.5, 0, 0], [600, 104, 16, 0.5, 0, 0], [640, 112, 24, 0.5, 0, 0]] }] },
    ] });
    vi.mocked(api.readerSourceAnnotations).mockResolvedValue({ annotations: [
      { annotation: { id: "ann_u" }, version: { annotationType: "highlight", learnerText: "" }, segments: [{ spanId: "s1", exactQuote: "quick brown fox jumps" }] },
      { annotation: { id: "ann_n" }, version: { annotationType: "interpretation", learnerText: "my words" }, segments: [{ spanId: "s1", exactQuote: "the quick" }] },
    ] });
    setup({ api });
    await settle();
    expect(api.inkList).toHaveBeenCalledWith({ sourceId: "src" });
    expect(api.readerSourceAnnotations).toHaveBeenCalledWith({ sourceId: "src", extractionId: "ext" });
    expect(body.querySelector('path[data-pen-stroke="underline"]')).not.toBeNull();
    expect(body.querySelector('[data-pen-mark="underline"]')).not.toBeNull();
    expect((screen.getByLabelText("your note's words") as HTMLTextAreaElement).value).toBe("my words");
  });

  it("plain ink on this reading's page is drawn again; another reading's is not", async () => {
    const api = fakeApi();
    const page = (ownerId: string) => ({ ownerKind: "source" as const, ownerId, contentHash: "hp", devicePixelRatio: 1, transcription: null,
      strokes: [{ strokeId: `p_${ownerId}`, inkId: `ink_${ownerId}`, points: [[150, 105, 0, 0.5, 0, 0], [250, 160, 8, 0.5, 0, 0]] as Array<[number, number, number, number, number, number]> }] });
    vi.mocked(api.inkList).mockResolvedValue({ version: 1, padId: null, sourceId: "src", owners: [page("ext"), page("ext_other")] });
    setup({ api });
    await settle();
    expect(body.querySelectorAll('path[data-pen-stroke="ink"]')).toHaveLength(1);
  });

  it("a mark is drawn from its annotation's anchor: at another width its ink moves beside the words it marks", async () => {
    const api = fakeApi();
    // Written under the first line at another width; the disagreement belongs to the second passage's words.
    vi.mocked(api.inkList).mockResolvedValue({ version: 1, padId: null, sourceId: "src", owners: [
      { ownerKind: "annotation", ownerId: "ann_s", contentHash: "h1", devicePixelRatio: 1, transcription: null,
        strokes: [{ strokeId: "s1", inkId: "ink_s", points: flat(140, 300, 112).map(([x, y]) => [x, y, 0, 0.5, 0, 0] as [number, number, number, number, number, number]) }] },
    ] });
    vi.mocked(api.readerSourceAnnotations).mockResolvedValue({ annotations: [
      { annotation: { id: "ann_s" }, version: { annotationType: "disposition", learnerText: "" }, segments: [{ spanId: "s2", exactQuote: "second passage" }] },
    ] });
    setup({ api });
    await settle();
    const mark = body.querySelector('[data-pen-mark="strike"]') as HTMLElement;
    expect(mark).not.toBeNull();
    // "second passage" starts at the 3rd character of the second line (top 130).
    expect([mark.style.left, mark.style.top, mark.style.width]).toEqual([`${LEFT + 2 * CHAR}px`, "130px", `${14 * CHAR}px`]);
    const ink = body.querySelector('path[data-pen-stroke="strike"]')!.getAttribute("d")!;
    expect(ink.startsWith(`M${(LEFT + 2 * CHAR).toFixed(1)} ${(130 + LINE / 2).toFixed(1)}`)).toBe(true);
  });

  it("a mark whose anchor can no longer be vouched for paints no words", async () => {
    const api = fakeApi();
    vi.mocked(api.inkList).mockResolvedValue({ version: 1, padId: null, sourceId: "src", owners: [
      { ownerKind: "annotation", ownerId: "ann_u", contentHash: "h1", devicePixelRatio: 1, transcription: null,
        strokes: [{ strokeId: "s1", inkId: "ink_u", points: flat(140, 300, 126).map(([x, y]) => [x, y, 0, 0.5, 0, 0] as [number, number, number, number, number, number]) }] },
    ] });
    vi.mocked(api.readerSourceAnnotations).mockResolvedValue({ annotations: [
      { annotation: { id: "ann_u" }, version: { annotationType: "highlight", learnerText: "" }, segments: [{ spanId: "s1", exactQuote: "quick brown fox jumps" }],
        placement: { state: "flagged", segments: [], flagSpanId: "s1" } },
    ] });
    setup({ api });
    await settle();
    expect(body.querySelector('path[data-pen-stroke="underline"]')).not.toBeNull();
    expect(body.querySelector('[data-pen-mark="underline"]')).toBeNull();
  });
});

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((done, fail) => {
    resolve = done;
    reject = fail;
  });
  return { promise, resolve, reject };
}

const scribble = (): Array<[number, number]> => {
  const points: Array<[number, number]> = [];
  for (let t = 0; t < 1; t += 0.02) points.push([530 + t * 150, 110 + Math.sin(t * 60) * 7]);
  return points;
};

describe("marks taken back and readings stopped", () => {
  it("undo while the annotation is being made removes it once made, and its ink is never saved", async () => {
    const api = fakeApi();
    const capture = deferred<Awaited<ReturnType<PenApi["readerCapture"]>>>();
    vi.mocked(api.readerCapture).mockReturnValue(capture.promise);
    const { host } = setup({ api });
    draw(flat(140, 300, 100 + LINE + 2));
    await settle();
    fireEvent.click(screen.getByText("undo"));
    expect(api.readerDeleteIntentAnnotation).not.toHaveBeenCalled();
    capture.resolve({ annotationId: "ann_late", outboxId: "o", interactionEventId: "e", anchorStatus: "exact", captureKind: "annotation", deduplicated: false, receipt: "r" });
    await settle();
    expect(api.readerDeleteIntentAnnotation).toHaveBeenCalledWith({ annotationId: "ann_late", reason: "pen undo" });
    expect(host.saveInk).not.toHaveBeenCalled();
    expect(body.querySelector('[data-pen-mark="underline"]')).toBeNull();
  });

  it("a removal that fails puts the mark back, saying so, and undo tries again", async () => {
    const api = fakeApi();
    vi.mocked(api.readerDeleteIntentAnnotation).mockRejectedValueOnce(new Error("offline"));
    setup({ api });
    draw(flat(140, 300, 100 + LINE + 2));
    await settle();
    fireEvent.click(screen.getByText("undo"));
    await settle();
    expect(screen.getByText("couldn't take this mark back · undo to try again")).toBeTruthy();
    expect(body.querySelector('[data-pen-mark="underline"]')).not.toBeNull();
    fireEvent.click(screen.getByText("undo"));
    await settle();
    expect(api.readerDeleteIntentAnnotation).toHaveBeenCalledTimes(2);
    expect(body.querySelector('[data-pen-mark="underline"]')).toBeNull();
  });

  it("a note taken back before its reading's start answered stops that reading on the server", async () => {
    const api = fakeApi();
    const start = deferred<InkTranscribeJobDto>();
    vi.mocked(api.inkTranscribe).mockReturnValue(start.promise);
    vi.mocked(api.inkTranscribeCancel).mockResolvedValue({ version: 1, jobId: "job_late", status: "cancelled", done: false, result: null, error: null });
    const { host } = setup({ api });
    draw(scribble());
    endNote();
    await settle();
    await settle();
    expect(api.inkTranscribe).toHaveBeenCalled();
    fireEvent.click(screen.getByText("undo"));
    start.resolve({ version: 1, jobId: "job_late", status: "running", done: false, result: null, error: null });
    await settle();
    expect(api.inkTranscribeCancel).toHaveBeenCalledWith({ jobId: "job_late" });
    expect(host.poller.size).toBe(0);
  });

  it("closing the window stops a note's reading on the server", async () => {
    const api = fakeApi({ jobId: "job_1", status: "running", done: false, error: null });
    vi.mocked(api.inkTranscribeCancel).mockResolvedValue({ version: 1, jobId: "job_1", status: "cancelled", done: false, result: null, error: null });
    const { host } = setup({ api });
    draw(scribble());
    endNote();
    await settle();
    await settle();
    expect(host.poller.size).toBe(1);
    cleanup();
    expect(api.inkTranscribeCancel).toHaveBeenCalledWith({ jobId: "job_1" });
    expect(host.poller.size).toBe(0);
  });

  it("a reading arriving while the learner types is offered beside the draft, never written over it", async () => {
    const api = fakeApi();
    const start = deferred<InkTranscribeJobDto>();
    vi.mocked(api.inkTranscribe).mockReturnValue(start.promise);
    setup({ api });
    draw(scribble());
    endNote();
    await settle();
    await settle();
    const field = screen.getByLabelText("your note's words") as HTMLTextAreaElement;
    fireEvent.change(field, { target: { value: "my own draf" } });
    start.resolve({ version: 1, jobId: null, status: "done", done: true, error: null, result: { transcriptionId: "it_1", ownerKind: "annotation", ownerId: "ann_1", contentHash: "h", latexMd: "does $e^x$ cancel?", confidenceLabel: "may_be_wrong", model: "m", createdAt: "t", applied: false, reason: null, headVersionId: null } });
    await settle();
    expect(field.value).toBe("my own draf");
    expect(screen.getByText(/LearnLoop reads: does \$e\^x\$ cancel\?/)).toBeTruthy();
    expect(api.readerEditAnnotation).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("use it"));
    expect(api.readerEditAnnotation).toHaveBeenCalledWith({ annotationId: "ann_1", learnerText: "does $e^x$ cancel?" });
  });
});

/** One pen stroke along a polyline, sampled every few pixels (a recognizer needs more than three points). */
function along(points: Array<[number, number]>): Array<[number, number]> {
  const out: Array<[number, number]> = [];
  for (let i = 1; i < points.length; i += 1) {
    const [x0, y0] = points[i - 1];
    const [x1, y1] = points[i];
    for (let k = 0; k < 6; k += 1) out.push([x0 + ((x1 - x0) * k) / 6, y0 + ((y1 - y0) * k) / 6]);
  }
  out.push(points[points.length - 1]);
  return out;
}

describe("a handwritten margin note", () => {
  it("a two-stroke x is one note: one annotation holding both strokes and one reading, made when the note ends", async () => {
    const { api, host } = setup();
    draw(along([[540, 104], [552, 110], [566, 122]]));
    await settle();
    draw(along([[566, 104], [552, 112], [540, 122]]));
    await settle();
    expect(api.readerCapture).not.toHaveBeenCalled();
    expect(body.querySelectorAll("[data-pen-note]")).toHaveLength(1);
    endNote();
    await settle();
    await settle();
    expect(api.readerCapture).toHaveBeenCalledTimes(1);
    expect(vi.mocked(api.readerCapture).mock.calls[0][0]).toMatchObject({ action: "interpretation", rawSelection: { nodes: [{ spanId: "s1" }] } });
    expect(host.saveInk).toHaveBeenCalledTimes(1);
    expect(vi.mocked(host.saveInk).mock.calls[0][0].strokes).toHaveLength(2);
    expect(api.inkTranscribe).toHaveBeenCalledTimes(1);
  });

  it("two notes beside different passages stay two", async () => {
    const { api, host } = setup();
    draw(along([[540, 104], [552, 110], [566, 122]]));
    await settle();
    // Close enough to overlap the first note grown by a line, but beside the second passage: a note of its own.
    draw(along([[540, 132], [552, 140], [566, 150]]));
    await settle();
    endNote();
    await settle();
    await settle();
    expect(api.readerCapture).toHaveBeenCalledTimes(2);
    expect(vi.mocked(api.readerCapture).mock.calls.map((call) => call[0].rawSelection?.nodes[0]?.spanId)).toEqual(["s1", "s2"]);
    expect(vi.mocked(host.saveInk).mock.calls.map((call) => call[0].strokes.length)).toEqual([1, 1]);
    expect(api.inkTranscribe).toHaveBeenCalledTimes(2);
  });

  it("a stroke far from the open note, or a stroke that is not a margin note, ends it", async () => {
    const { api } = setup();
    draw(along([[540, 104], [552, 110], [566, 122]]));
    await settle();
    draw(along([[760, 104], [772, 110], [786, 122]])); // beside the same passage, beyond a line from the note
    await settle();
    expect(api.readerCapture).toHaveBeenCalledTimes(1);
    draw(flat(140, 300, 100 + 30 + LINE + 2)); // an underline of the second passage
    await settle();
    await settle();
    expect(vi.mocked(api.readerCapture).mock.calls.map((call) => call[0].action)).toEqual(["interpretation", "interpretation", "highlight"]);
  });

  it("undo takes the open note's last stroke back, and the note with its only one; nothing was kept", async () => {
    const { api } = setup();
    draw(along([[540, 104], [552, 110], [566, 122]]));
    await settle();
    draw(along([[566, 104], [552, 112], [540, 122]]));
    await settle();
    expect(body.querySelectorAll('path[data-pen-stroke="note"]')).toHaveLength(2);
    fireEvent.click(screen.getByText("undo"));
    expect(body.querySelectorAll('path[data-pen-stroke="note"]')).toHaveLength(1);
    fireEvent.click(screen.getByText("undo"));
    expect(body.querySelectorAll('path[data-pen-stroke="note"]')).toHaveLength(0);
    expect(body.querySelector("[data-pen-note]")).toBeNull();
    endNote();
    await settle();
    expect(api.readerCapture).not.toHaveBeenCalled();
  });

  it("leaving pen mode ends the open note", async () => {
    const { api, rerenderOn } = setup();
    draw(along([[540, 104], [552, 110], [566, 122]]));
    await settle();
    rerenderOn(false);
    await settle();
    expect(api.readerCapture).toHaveBeenCalledTimes(1);
  });
});
