// Selecting and highlighting on the original PDF (reader-pdf-selection): the
// pane with the selection model, driven like a learner drives it. The pages
// are the synthetic book (two columns with a footnote drawn between them, a
// word hyphenated over a line break, a display formula, a table, inline
// maths, a page break, and a scanned page with no text layer), with the text
// content pdf.js reads from it (recorded and checked by model.test.ts).
// Pages are drawn at 100 % (612 px wide, one PDF point per pixel), stacked
// with the pane's 14 px gap.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useEffect, useState, type ComponentProps } from "react";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PdfReaderPane } from "./PdfReaderPane";
import type { PdfHighlight } from "./pdfSelection/highlights";
import { SelectionModel, type Pos } from "./pdfSelection/model";
import { SELECTION_SETTLE_MS } from "./pdfSelection/usePdfSelection";
import { SYNTHETIC_BLOCKS } from "./pdfSelection/testing/syntheticBook";
import type { ParsedPage } from "./pdfSelection/testing/syntheticPdf";

const { acquirePdfDocument, OPS } = vi.hoisted(() => ({
  acquirePdfDocument: vi.fn(),
  // pdf.js's operator ids for what a page's text draws with.
  OPS: { save: 10, restore: 11, transform: 12, beginText: 31, endText: 32, setFont: 37, moveText: 40, setTextMatrix: 42, showText: 44 },
}));
vi.mock("./pdfDocumentCache", () => ({ acquirePdfDocument }));
vi.mock("pdfjs-dist", () => ({
  GlobalWorkerOptions: {},
  OPS,
  AnnotationMode: { DISABLE: 0, ENABLE: 1 },
  TextLayer: class {
    render() {
      return Promise.resolve();
    }
  },
}));
vi.mock("pdfjs-dist/build/pdf.worker.min.mjs?url", () => ({ default: "pdf.worker.js" }));
vi.mock("pdfjs-dist/web/pdf_viewer.css", () => ({}));

const TEXT = (JSON.parse(readFileSync(join(__dirname, "pdfSelection", "fixtures", "synthetic_text_content.json"), "utf8")) as {
  pages: ParsedPage[];
}).pages;

const PAGE_W = 612;
const PAGE_H = 792;
const GAP = 14;
const pageTop = (page: number) => page * (PAGE_H + GAP);

const renders: number[] = [];
const cleanups: number[] = [];
const fakeDoc = {
  numPages: 3,
  getPage: async (pageNumber: number) => ({
    getViewport: ({ scale }: { scale: number }) => ({
      width: PAGE_W * scale,
      height: PAGE_H * scale,
      transform: [scale, 0, 0, -scale, 0, PAGE_H * scale],
    }),
    getTextContent: async () => ({ items: TEXT[pageNumber - 1].items, styles: TEXT[pageNumber - 1].styles }),
    render: () => {
      renders.push(pageNumber - 1);
      return { promise: Promise.resolve(), cancel() {} };
    },
    streamTextContent: () => ({}),
    cleanup: () => cleanups.push(pageNumber - 1),
  }),
};

// The model the pane builds, built here the same way, to find where words are.
const model = new SelectionModel(SYNTHETIC_BLOCKS);
for (const page of TEXT) model.setPageText(page.page, page.items, page.transform, page.styles);

function find(spanId: string, text: string, nth = 0): Pos {
  const block = model.blockIndex(spanId) as number;
  const source = model.blocks[block].text;
  const hits = model.units(block).flatMap((unit, index) => (source.slice(unit.start, unit.end) === text ? [index] : []));
  if (hits[nth] === undefined) throw new Error(`no ${text} in ${spanId}`);
  return { block, unit: hits[nth] };
}

/** The client point at the centre of a word (or of a formula's box). */
function at(spanId: string, text: string | null = null, piece = 0): { clientX: number; clientY: number } {
  const block = model.blockIndex(spanId) as number;
  const pos = text === null ? { block, unit: 0 } : find(spanId, text);
  const box = model.geometry(pos.block).boxes[pos.unit][piece];
  return { clientX: (box[0] + box[2]) / 2, clientY: pageTop(model.blocks[block].page) + (box[1] + box[3]) / 2 };
}

const observed: Array<{ callback: IntersectionObserverCallback; node: Element }> = [];

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "requestAnimationFrame", "cancelAnimationFrame"] });
  observed.length = 0;
  renders.length = 0;
  cleanups.length = 0;
  acquirePdfDocument.mockResolvedValue({ doc: fakeDoc, pageTexts: new Map() });
  vi.stubGlobal("ResizeObserver", class {
    observe() {}
    disconnect() {}
  });
  vi.stubGlobal("IntersectionObserver", class {
    constructor(private callback: IntersectionObserverCallback) {}
    observe(node: Element) {
      observed.push({ callback: this.callback, node });
    }
    disconnect() {}
  });
  HTMLCanvasElement.prototype.getContext = vi.fn(() => ({})) as unknown as typeof HTMLCanvasElement.prototype.getContext;
  Element.prototype.scrollIntoView = vi.fn();
  Object.defineProperty(HTMLElement.prototype, "clientWidth", { configurable: true, get: () => PAGE_W + 2 });
  vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(function (this: Element) {
    const page = (this as HTMLElement).dataset?.pdfPage;
    if (page === undefined) return { top: 0, bottom: 0, height: 0, width: 0, left: 0, right: 0, x: 0, y: 0, toJSON: () => ({}) } as DOMRect;
    const width = Number((this as HTMLElement).style.width.replace("px", "")) || PAGE_W;
    const height = Number((this as HTMLElement).style.height.replace("px", "")) || PAGE_H;
    const top = Number(page) * (height + GAP);
    return { top, bottom: top + height, height, width, left: 0, right: width, x: 0, y: top, toJSON: () => ({}) } as DOMRect;
  });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
  // @ts-expect-error -- restore jsdom's own (prototype chain) getter
  delete HTMLElement.prototype.clientWidth;
});

async function flush(ms = 0) {
  for (let i = 0; i < 6; i += 1) {
    await act(async () => {
      await vi.advanceTimersByTimeAsync(i === 0 ? ms : 20);
    });
  }
}

/** Every page comes near the view: drawn, its words placed. */
async function drawPages() {
  for (const { callback, node } of observed) {
    callback([{ isIntersecting: true, target: node } as unknown as IntersectionObserverEntry], {} as IntersectionObserver);
  }
  await flush(50);
}

function pageEl(page: number): HTMLElement {
  return document.querySelector(`[data-pdf-page="${page}"]`) as HTMLElement;
}

type PaneProps = Partial<ComponentProps<typeof PdfReaderPane>>;
type FullProps = ComponentProps<typeof PdfReaderPane>;

/** The Reader's part: it keeps the settled selection as its capture (and
 *  hands it back to the pane), clears it on Esc, restores one when asked. */
function Reader({ restored = null, ...props }: FullProps & { restored?: FullProps["selection"] }) {
  const [selection, setSelection] = useState<FullProps["selection"]>(restored);
  useEffect(() => {
    if (restored) setSelection(restored);
  }, [restored]);
  return (
    <div style={{ overflowY: "auto" }}>
      <PdfReaderPane
        {...props}
        selection={selection}
        onTextSelection={(next) => {
          props.onTextSelection(next);
          setSelection(next);
        }}
        onSelectionCleared={() => {
          props.onSelectionCleared?.();
          setSelection(null);
        }}
      />
    </div>
  );
}

async function open(extra: PaneProps = {}) {
  const onTextSelection = vi.fn();
  const onTagMenu = vi.fn();
  const onHighlightRemove = vi.fn();
  const onHighlightOpen = vi.fn();
  const onSelectionCleared = vi.fn();
  const props = {
    fileUrl: "llpdf://sha256-synthetic",
    blocks: SYNTHETIC_BLOCKS,
    guidanceSpans: new Set<string>(),
    activeSpan: null,
    onTextSelection,
    onTagMenu,
    onError: () => undefined,
    onHighlightRemove,
    onHighlightOpen,
    onSelectionCleared,
    ...extra,
  };
  const { selection, ...rest } = props as PaneProps & typeof props;
  const view = render(<Reader {...(rest as FullProps)} restored={selection ?? null} />);
  await flush();
  await drawPages();
  return { ...view, props, onTextSelection, onTagMenu, onHighlightRemove, onHighlightOpen, onSelectionCleared };
}

/** A learner's drag: press, move in steps (one frame each), release. */
async function drag(from: { clientX: number; clientY: number }, to: { clientX: number; clientY: number }, page = 0) {
  fireEvent.mouseDown(pageEl(page), { ...from, button: 0, detail: 1 });
  for (let step = 1; step <= 4; step++) {
    fireEvent.mouseMove(window, {
      clientX: from.clientX + ((to.clientX - from.clientX) * step) / 4,
      clientY: from.clientY + ((to.clientY - from.clientY) * step) / 4,
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(16);
    });
  }
  fireEvent.mouseUp(window, to);
}

function lastSelection(spy: ReturnType<typeof vi.fn>) {
  return spy.mock.calls[spy.mock.calls.length - 1][0] as { spanId: string; quote: string; text: string; nodes: Array<{ spanId: string; quote: string; start: number; end: number }> };
}

describe("selecting on the page", () => {
  it("a drag across two columns follows the reading order and settles 150 ms after the mouse is released", async () => {
    const { onTextSelection } = await open();
    await drag(at("s2", "quietly."), at("s3", "begins"));
    // Painted at once, word by word, while nothing is handed over yet.
    expect(document.querySelectorAll("[data-pdf-page='0'] [data-pdf-selection-rect]").length).toBeGreaterThan(0);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(SELECTION_SETTLE_MS - 20);
    });
    expect(onTextSelection).not.toHaveBeenCalled();
    await flush(30);
    expect(onTextSelection).toHaveBeenCalledTimes(1);
    const selection = lastSelection(onTextSelection);
    expect(selection.nodes.map((node) => [node.spanId, node.quote])).toEqual([
      ["s2", "quietly."],
      ["s3", "Right column begins"],
    ]);
    // Exact slices with code-point offsets: the sidecar anchors them exactly.
    const s3 = SYNTHETIC_BLOCKS.find((block) => block.spanId === "s3")!.text!;
    expect(Array.from(s3).slice(selection.nodes[1].start, selection.nodes[1].end).join("")).toBe("Right column begins");
    expect(selection.text).toBe("quietly.\n\nRight column begins");
  });

  it("a drag over a page break takes the page's footnote after its body", async () => {
    const { onTextSelection } = await open();
    await drag(at("s3", "column."), at("s5", "on"));
    await flush(SELECTION_SETTLE_MS);
    expect(lastSelection(onTextSelection).nodes.map((node) => node.spanId)).toEqual(["s3", "s4", "s5"]);
    // Painted on both pages.
    expect(document.querySelectorAll("[data-pdf-page='0'] [data-pdf-selection-rect]").length).toBeGreaterThan(0);
    expect(document.querySelectorAll("[data-pdf-page='1'] [data-pdf-selection-rect]").length).toBeGreaterThan(0);
  });

  it("a click on a display formula takes it whole, its LaTeX the selected text", async () => {
    const { onTextSelection } = await open();
    const point = at("s6");
    fireEvent.mouseDown(pageEl(1), { ...point, button: 0, detail: 1 });
    fireEvent.mouseUp(window, point);
    await flush(SELECTION_SETTLE_MS);
    const selection = lastSelection(onTextSelection);
    expect(selection.nodes).toEqual([{ spanId: "s6", quote: "$$\nx^{2} + y^{2} = 1\n$$", start: 0, end: 23 }]);
    expect(selection.text).toBe("$$\nx^{2} + y^{2} = 1\n$$");
    // One box: the formula's own.
    const rects = document.querySelectorAll<HTMLElement>("[data-pdf-page='1'] [data-pdf-selection-rect]");
    expect(rects).toHaveLength(1);
  });

  it("a drag on a scanned page (no text layer, layout boxes only) snaps to words", async () => {
    const { onTextSelection } = await open();
    await drag({ clientX: 75, clientY: pageTop(2) + 115 }, { clientX: 160, clientY: pageTop(2) + 140 }, 2);
    await flush(SELECTION_SETTLE_MS);
    const [node] = lastSelection(onTextSelection).nodes;
    expect(node.spanId).toBe("s11");
    expect(node.quote.startsWith("A scanned page")).toBe(true);
    expect(node.start).toBe(0);
  });

  it("double then triple click within the settle time hands over one selection, the passage", async () => {
    const { onTextSelection } = await open();
    const point = at("s2", "lazy");
    fireEvent.mouseDown(pageEl(0), { ...point, button: 0, detail: 2 });
    fireEvent.mouseUp(window, point);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(60);
    });
    fireEvent.mouseDown(pageEl(0), { ...point, button: 0, detail: 3 });
    fireEvent.mouseUp(window, point);
    await flush(SELECTION_SETTLE_MS);
    expect(onTextSelection).toHaveBeenCalledTimes(1);
    expect(lastSelection(onTextSelection).nodes[0].quote).toBe(SYNTHETIC_BLOCKS.find((block) => block.spanId === "s2")!.text);
  });

  it("Shift+arrows extend from the caret by a word and by a line, and the selection is read out", async () => {
    const { onTextSelection, container } = await open();
    const pane = container.querySelector<HTMLElement>("[role='document']")!;
    const point = at("s2", "quick");
    fireEvent.mouseDown(pageEl(0), { ...point, button: 0, detail: 1 });
    fireEvent.mouseUp(window, point);
    await flush();
    expect(document.activeElement).toBe(pane);
    expect(document.querySelector("[data-pdf-caret]")).not.toBeNull();
    fireEvent.keyDown(pane, { key: "ArrowRight", shiftKey: true });
    fireEvent.keyDown(pane, { key: "ArrowRight", shiftKey: true });
    await flush(SELECTION_SETTLE_MS);
    expect(lastSelection(onTextSelection).nodes[0].quote).toBe("quick brown");
    fireEvent.keyDown(pane, { key: "ArrowDown", shiftKey: true });
    await flush(SELECTION_SETTLE_MS);
    expect(lastSelection(onTextSelection).nodes[0].quote.startsWith("quick brown fox jumps over the")).toBe(true);
    expect(container.querySelector("[aria-live='polite']")?.textContent).toMatch(/^Selected: quick brown fox/);
  });

  it("Ctrl+C copies the extraction's clean text, maths as LaTeX", async () => {
    const { onTextSelection } = await open();
    await drag(at("s9", "positive;"), at("s9", "holds"), 1);
    await flush(SELECTION_SETTLE_MS);
    expect(onTextSelection).toHaveBeenCalled();
    const setData = vi.fn();
    const copy = new Event("copy", { bubbles: true, cancelable: true });
    Object.defineProperty(copy, "clipboardData", { value: { setData } });
    document.dispatchEvent(copy);
    expect(setData).toHaveBeenCalledWith("text/plain", "positive; then $x^{2} > 0$ holds");
    expect(copy.defaultPrevented).toBe(true);
  });

  it("a right-click on the selection tags it with its exact nodes; elsewhere on a passage, the passage", async () => {
    const { onTagMenu } = await open();
    await drag(at("s2", "lazy"), at("s2", "dog"));
    await flush(SELECTION_SETTLE_MS);
    fireEvent.contextMenu(pageEl(0), at("s2", "lazy"));
    const request = onTagMenu.mock.calls[0][0];
    expect(request.nodes).toEqual([expect.objectContaining({ spanId: "s2", quote: "lazy dog" })]);
    expect(typeof request.nodes[0].start).toBe("number");
    fireEvent.contextMenu(pageEl(0), at("s3", "begins"));
    expect(onTagMenu.mock.calls[1][0]).toMatchObject({ spanId: "s3", quote: null });
  });

  it("a click on text keeps the Reader's capture; Esc clears it", async () => {
    const s2 = SYNTHETIC_BLOCKS.find((block) => block.spanId === "s2")!.text!;
    const start = s2.indexOf("lazy dog");
    const selection = { spanId: "s2", quote: "lazy dog", nodes: [{ spanId: "s2", quote: "lazy dog", start, end: start + 8 }] };
    const { onSelectionCleared, container } = await open({ selection });
    expect(document.querySelectorAll("[data-pdf-page='0'] [data-pdf-selection-rect]")).toHaveLength(1);
    const point = at("s3", "begins");
    fireEvent.mouseDown(pageEl(0), { ...point, button: 0, detail: 1 });
    fireEvent.mouseUp(window, point);
    await flush(SELECTION_SETTLE_MS);
    expect(document.querySelectorAll("[data-pdf-page='0'] [data-pdf-selection-rect]")).toHaveLength(1);
    expect(onSelectionCleared).not.toHaveBeenCalled();
    fireEvent.keyDown(container.querySelector("[role='document']")!, { key: "Escape" });
    expect(onSelectionCleared).toHaveBeenCalledTimes(1);
  });

  it("after a click elsewhere, Shift+arrows start at the click, not at the capture it kept", async () => {
    const { onTextSelection, container } = await open();
    await drag(at("s2", "lazy"), at("s2", "dog"));
    await flush(SELECTION_SETTLE_MS);
    const point = at("s3", "second");
    fireEvent.mouseDown(pageEl(0), { ...point, button: 0, detail: 1 });
    fireEvent.mouseUp(window, point);
    await flush();
    const pane = container.querySelector<HTMLElement>("[role='document']")!;
    fireEvent.keyDown(pane, { key: "ArrowRight", shiftKey: true });
    fireEvent.keyDown(pane, { key: "ArrowRight", shiftKey: true });
    await flush(SELECTION_SETTLE_MS);
    expect(lastSelection(onTextSelection).nodes.map((node) => [node.spanId, node.quote])).toEqual([["s3", "second paragraph"]]);
    // Shift+click extends from the new selection's start.
    const end = at("s3", "page,");
    fireEvent.mouseDown(pageEl(0), { ...end, button: 0, detail: 1, shiftKey: true });
    fireEvent.mouseUp(window, end);
    await flush(SELECTION_SETTLE_MS);
    expect(lastSelection(onTextSelection).nodes[0].quote).toBe("second paragraph of this page,");
  });

  it("a capture restored by the Reader paints its words and never moves the keyboard", async () => {
    const elsewhere = document.createElement("textarea");
    document.body.appendChild(elsewhere);
    elsewhere.focus();
    const view = await open();
    const s7 = SYNTHETIC_BLOCKS.find((block) => block.spanId === "s7")!.text!;
    const selection = { spanId: "s7", quote: "two values", nodes: [{ spanId: "s7", quote: "two values", start: s7.indexOf("two"), end: s7.indexOf("two") + 10 }] };
    view.rerender(<Reader {...(view.props as FullProps)} restored={selection} />);
    await flush(SELECTION_SETTLE_MS);
    expect(document.querySelectorAll("[data-pdf-page='1'] [data-pdf-selection-rect]")).toHaveLength(1);
    expect(document.activeElement).toBe(elsewhere);
    elsewhere.remove();
  });
});

describe("highlights drawn from their anchors", () => {
  const s2 = SYNTHETIC_BLOCKS.find((block) => block.spanId === "s2")!.text!;
  const s3 = SYNTHETIC_BLOCKS.find((block) => block.spanId === "s3")!.text!;
  const HIGHLIGHTS: PdfHighlight[] = [
    {
      id: "a1",
      kind: "highlight",
      state: "here",
      segments: [{ spanId: "s2", start: s2.indexOf("long"), end: s2.indexOf("integral") + 8 }],
      flagSpanId: null,
      quote: "long computation of the integral",
      note: "",
    },
    {
      id: "a2",
      kind: "question",
      state: "moved",
      segments: [{ spanId: "s3", start: s3.indexOf("careful"), end: s3.indexOf("reader") + 6 }],
      flagSpanId: null,
      quote: "careful reader",
      note: "why careful?",
    },
    { id: "a3", kind: "highlight", state: "flagged", segments: [], flagSpanId: "s7", quote: "two old values", note: "" },
  ];

  it("draws each on its words (one box per line), moved ones labelled, changed ones outlined", async () => {
    await open({ highlights: HIGHLIGHTS });
    // "long computation of the integral" runs over two lines (the hyphen).
    expect(document.querySelectorAll("[data-pdf-highlight='a1']")).toHaveLength(2);
    const moved = document.querySelectorAll<HTMLElement>("[data-pdf-highlight='a2']");
    expect(moved.length).toBeGreaterThan(0);
    expect(moved[0].dataset.highlightState).toBe("moved");
    const stop = document.querySelector<HTMLElement>("[data-highlight-stop='a2']")!;
    expect(stop.getAttribute("aria-label")).toContain("moved here when the book was read again");
    expect(stop.getAttribute("aria-label")).toContain("note: why careful?");
    const flagged = document.querySelector<HTMLElement>("[data-pdf-highlight='a3']")!;
    expect(flagged.dataset.highlightState).toBe("flagged");
    expect(flagged.closest("[data-pdf-page]")?.getAttribute("data-pdf-page")).toBe("1");
  });

  it("follows zoom: the same words, at the new scale (never stored screen boxes)", async () => {
    const { getByText } = await open({ highlights: HIGHLIGHTS });
    const before = document.querySelector<HTMLElement>("[data-pdf-highlight='a1']")!;
    const left = parseFloat(before.style.left);
    const width = parseFloat(before.style.width);
    fireEvent.click(getByText("+"));
    await flush(50);
    const after = document.querySelector<HTMLElement>("[data-pdf-highlight='a1']")!;
    // 115 %: every box scales by the page's width.
    expect(parseFloat(after.style.left) + 1).toBeCloseTo((left + 1) * 1.15, 1);
    expect(parseFloat(after.style.width) - 2).toBeCloseTo((width - 2) * 1.15, 1);
  });

  it("a click opens it (its chip says what it is); remove, and Delete on its keyboard stop, remove it", async () => {
    const { onHighlightRemove, onHighlightOpen, getByText } = await open({ highlights: HIGHLIGHTS });
    const point = at("s3", "careful");
    fireEvent.mouseDown(pageEl(0), { ...point, button: 0, detail: 1 });
    fireEvent.mouseUp(window, point);
    await flush();
    const chip = document.querySelector<HTMLElement>("[data-highlight-chip='a2']")!;
    expect(chip.textContent).toContain("Question");
    expect(chip.textContent).toContain("moved here when the book was read again");
    fireEvent.click(getByText("open note"));
    expect(onHighlightOpen).toHaveBeenCalledWith("a2");
    fireEvent.click(getByText("remove"));
    expect(onHighlightRemove).toHaveBeenCalledWith("a2");
    const stop = document.querySelector<HTMLElement>("[data-highlight-stop='a1']")!;
    act(() => stop.focus());
    fireEvent.keyDown(stop, { key: "Delete" });
    expect(onHighlightRemove).toHaveBeenLastCalledWith("a1");
  });

  it("a drag starting on a highlight selects words; it does not open the highlight", async () => {
    const { onTextSelection } = await open({ highlights: HIGHLIGHTS });
    await drag(at("s2", "long"), at("s2", "integral"));
    await flush(SELECTION_SETTLE_MS);
    expect(lastSelection(onTextSelection).text).toBe("long computation of the integral");
    expect(document.querySelector("[data-highlight-chip]")).toBeNull();
  });
});

describe("Esc and Shift+Home/End (Codex review F6, F7)", () => {
  it("Esc in the middle of a drag ends it: the release selects nothing, after a frame was drawn or before", async () => {
    const { onTextSelection } = await open();
    const from = at("s2", "quick");
    const to = at("s2", "lazy");
    // After a frame was drawn: the drag is painted, then Esc.
    fireEvent.mouseDown(pageEl(0), { ...from, button: 0, detail: 1 });
    fireEvent.mouseMove(window, { clientX: to.clientX, clientY: to.clientY });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(16);
    });
    expect(document.querySelectorAll("[data-pdf-page='0'] [data-pdf-selection-rect]").length).toBeGreaterThan(0);
    fireEvent.keyDown(document.activeElement ?? window, { key: "Escape" });
    await flush();
    expect(document.querySelectorAll("[data-pdf-selection-rect]")).toHaveLength(0);
    fireEvent.mouseMove(window, { clientX: to.clientX + 40, clientY: to.clientY });
    fireEvent.mouseUp(window, to);
    await flush(SELECTION_SETTLE_MS * 2);
    expect(onTextSelection).not.toHaveBeenCalled();
    expect(document.querySelectorAll("[data-pdf-selection-rect]")).toHaveLength(0);
    // Before the first frame: Esc while the first move's frame is still pending.
    fireEvent.mouseDown(pageEl(0), { ...from, button: 0, detail: 1 });
    fireEvent.mouseMove(window, { clientX: to.clientX, clientY: to.clientY });
    fireEvent.keyDown(document.activeElement ?? window, { key: "Escape" });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(16);
    });
    fireEvent.mouseUp(window, to);
    await flush(SELECTION_SETTLE_MS * 2);
    expect(onTextSelection).not.toHaveBeenCalled();
    expect(document.querySelectorAll("[data-pdf-selection-rect]")).toHaveLength(0);
    // The pages still select afterwards.
    await drag(from, to);
    await flush(SELECTION_SETTLE_MS);
    expect(lastSelection(onTextSelection).nodes[0].quote).toBe("quick brown fox jumps over the lazy");
  });

  it("Esc in the middle of an Alt sweep ends it, wherever the keyboard is", async () => {
    const { onTextSelection } = await open();
    const from = at("s2", "quick");
    fireEvent.mouseDown(pageEl(0), { ...from, button: 0, detail: 1, altKey: true });
    fireEvent.mouseMove(window, at("s3", "begins"));
    await flush();
    expect(document.querySelectorAll("[data-pdf-selection-rect]").length).toBeGreaterThan(0);
    fireEvent.keyDown(document.body, { key: "Escape" });
    await flush();
    fireEvent.mouseUp(window, at("s3", "begins"));
    await flush(SELECTION_SETTLE_MS * 2);
    expect(onTextSelection).not.toHaveBeenCalled();
    expect(document.querySelectorAll("[data-pdf-selection-rect]")).toHaveLength(0);
  });

  it("from a click on a word, the first Shift+Home selects to the line's start and Shift+End to its end", async () => {
    const { onTextSelection, container } = await open();
    const pane = container.querySelector<HTMLElement>("[role='document']")!;
    // "The quick brown fox jumps over" is the first line of s2.
    const point = at("s2", "fox");
    fireEvent.mouseDown(pageEl(0), { ...point, button: 0, detail: 1 });
    fireEvent.mouseUp(window, point);
    await flush();
    fireEvent.keyDown(pane, { key: "Home", shiftKey: true });
    await flush(SELECTION_SETTLE_MS);
    expect(lastSelection(onTextSelection).nodes[0].quote).toBe("The quick brown fox");
    fireEvent.mouseDown(pageEl(0), { ...point, button: 0, detail: 1 });
    fireEvent.mouseUp(window, point);
    await flush();
    fireEvent.keyDown(pane, { key: "End", shiftKey: true });
    await flush(SELECTION_SETTLE_MS);
    expect(lastSelection(onTextSelection).nodes[0].quote).toBe("fox jumps over");
    // Shift+Right from a caret still takes the word at it first.
    fireEvent.mouseDown(pageEl(0), { ...point, button: 0, detail: 1 });
    fireEvent.mouseUp(window, point);
    await flush();
    fireEvent.keyDown(pane, { key: "ArrowRight", shiftKey: true });
    await flush(SELECTION_SETTLE_MS);
    expect(lastSelection(onTextSelection).nodes[0].quote).toBe("fox");
  });
});

describe("a highlight running over a page break (Codex review F5)", () => {
  const s3 = SYNTHETIC_BLOCKS.find((block) => block.spanId === "s3")!.text!;
  const s5 = SYNTHETIC_BLOCKS.find((block) => block.spanId === "s5")!.text!;
  const ACROSS: PdfHighlight[] = [
    {
      id: "over",
      kind: "question",
      state: "here",
      segments: [
        { spanId: "s3", start: s3.indexOf("careful"), end: s3.length },
        { spanId: "s5", start: 0, end: s5.indexOf("page,") + 5 },
      ],
      flagSpanId: null,
      quote: "careful reader reads after the whole left column. Continuing on the next page,",
      note: "",
    },
  ];

  it("a click on its part on the next page opens its chip there, above that part", async () => {
    const { onHighlightOpen, onHighlightRemove, getByText } = await open({ highlights: ACROSS });
    const point = at("s5", "next");
    fireEvent.mouseDown(pageEl(1), { ...point, button: 0, detail: 1 });
    fireEvent.mouseUp(window, point);
    await flush();
    const chip = document.querySelector<HTMLElement>("[data-pdf-page='1'] [data-highlight-chip='over']");
    expect(chip).not.toBeNull();
    expect(document.querySelector("[data-pdf-page='0'] [data-highlight-chip]")).toBeNull();
    // Above the clicked line, on page 1.
    const part = document.querySelector<HTMLElement>("[data-pdf-page='1'] [data-pdf-highlight='over']")!;
    expect(parseFloat(chip!.style.top)).toBeLessThanOrEqual(parseFloat(part.style.top) + 1);
    fireEvent.click(getByText("open note"));
    expect(onHighlightOpen).toHaveBeenCalledWith("over");
    fireEvent.click(getByText("remove"));
    expect(onHighlightRemove).toHaveBeenCalledWith("over");
  });

  it("each page it is drawn on has its keyboard stop: Tab reaches the part in view, Enter and Delete act on it", async () => {
    const { onHighlightOpen, onHighlightRemove } = await open({ highlights: ACROSS });
    const first = document.querySelector<HTMLElement>("[data-pdf-page='0'] [data-highlight-stop='over']")!;
    const next = document.querySelector<HTMLElement>("[data-pdf-page='1'] [data-highlight-stop='over']")!;
    expect(first).not.toBeNull();
    expect(next).not.toBeNull();
    expect(first.hasAttribute("data-highlight-continued")).toBe(false);
    expect(next.hasAttribute("data-highlight-continued")).toBe(true);
    expect(next.getAttribute("aria-label")).toContain("continued from the page before");
    // Page 0 leaves the view: page 1's stop is still there.
    const page0 = observed.find((entry) => entry.node === pageEl(0))!;
    page0.callback([{ isIntersecting: false, target: page0.node } as unknown as IntersectionObserverEntry], {} as IntersectionObserver);
    await flush();
    const stop = document.querySelector<HTMLElement>("[data-pdf-page='1'] [data-highlight-stop='over']")!;
    act(() => stop.focus());
    await flush();
    expect(document.querySelector("[data-pdf-page='1'] [data-highlight-chip='over']")).not.toBeNull();
    fireEvent.keyDown(stop, { key: "Enter" });
    expect(onHighlightOpen).toHaveBeenCalledWith("over");
    fireEvent.keyDown(stop, { key: "Delete" });
    expect(onHighlightRemove).toHaveBeenCalledWith("over");
  });
});

describe("words where the page paints them (Codex review F1)", () => {
  // A line in a monospaced embedded font that pdf.js calls sans-serif (no
  // fixed-pitch flag): every glyph 600 units, 6 pt at 10 pt, so the words are
  // at 72-132, 138-198 and 204-222. Split by sans-serif widths, x = 102
  // would fall in the second word.
  const LINE = "iiiiiiiiii WWWWWWWWWW end";
  const BLOCKS = [{ spanId: "m1", page: 0, bbox: [71, 91, 300, 103], blockType: "Text", text: LINE }];
  const opCalls: unknown[] = [];
  const monoDoc = {
    numPages: 1,
    getPage: async () => ({
      getViewport: ({ scale }: { scale: number }) => ({ width: PAGE_W * scale, height: PAGE_H * scale, transform: [scale, 0, 0, -scale, 0, PAGE_H * scale] }),
      getTextContent: async () => ({
        items: [{ str: LINE, transform: [10, 0, 0, 10, 72, PAGE_H - 100], width: 150, height: 10, hasEOL: false, fontName: "g_mono" }],
        styles: { g_mono: { fontFamily: "sans-serif" } },
      }),
      getOperatorList: async (options: unknown) => {
        opCalls.push(options);
        return {
          fnArray: [OPS.beginText, OPS.setFont, OPS.moveText, OPS.showText, OPS.endText],
          argsArray: [null, ["g_mono", 10], [72, PAGE_H - 100], [Array.from(LINE, (ch) => ({ unicode: ch, width: 600, isSpace: ch === " " }))], null],
        };
      },
      commonObjs: { has: () => true, get: () => ({}) },
      render: () => ({ promise: Promise.resolve(), cancel() {} }),
      streamTextContent: () => ({}),
    }),
  };

  it("once a page is drawn, a click inside a word selects that word, whatever its font", async () => {
    opCalls.length = 0;
    acquirePdfDocument.mockResolvedValue({ doc: monoDoc, pageTexts: new Map() });
    const { onTextSelection } = await open({ blocks: BLOCKS });
    // Read once, annotations left out (their appearances are not the page's text).
    expect(opCalls).toEqual([{ annotationMode: 0 }]);
    const point = { clientX: 102, clientY: pageTop(0) + 97 };
    fireEvent.mouseDown(pageEl(0), { ...point, button: 0, detail: 2 });
    fireEvent.mouseUp(window, point);
    await flush(SELECTION_SETTLE_MS);
    expect(lastSelection(onTextSelection).nodes[0].quote).toBe("iiiiiiiiii");
    // The selection is painted on the word's own glyphs.
    const rect = document.querySelector<HTMLElement>("[data-pdf-page='0'] [data-pdf-selection-rect]")!;
    expect(parseFloat(rect.style.left) + 1).toBeCloseTo(72, 1);
    expect(parseFloat(rect.style.width) - 2).toBeCloseTo(60, 1);
    // A redraw at another zoom keeps them and does not read the list again.
    fireEvent.click(screen.getByText("+"));
    await flush(50);
    expect(opCalls).toHaveLength(1);
  });
});

describe("only pages near the view are drawn", () => {
  it("a page leaving the view gives back its canvas, its layer and what pdf.js read to draw it; its size stays", async () => {
    await open();
    expect(document.querySelectorAll("[data-pdf-layer]")).toHaveLength(3);
    const canvas = pageEl(0).querySelector("canvas")!;
    expect(canvas.width).toBeGreaterThan(0);
    const first = observed.find((entry) => entry.node === pageEl(0))!;
    first.callback([{ isIntersecting: false, target: first.node } as unknown as IntersectionObserverEntry], {} as IntersectionObserver);
    await flush();
    expect(canvas.width).toBe(0);
    expect(pageEl(0).querySelector("[data-pdf-layer]")).toBeNull();
    expect(cleanups).toEqual([0]);
    expect(parseFloat(pageEl(0).style.height)).toBeCloseTo(PAGE_H, 3);
    // Back near the view: drawn again.
    first.callback([{ isIntersecting: true, target: first.node } as unknown as IntersectionObserverEntry], {} as IntersectionObserver);
    await flush(50);
    expect(pageEl(0).querySelector("[data-pdf-layer]")).not.toBeNull();
    expect(renders.filter((page) => page === 0)).toHaveLength(2);
  });
});

describe("a 600-page book in the pane", () => {
  it("a drag frame re-renders only what changed: far less than redrawing every page", async () => {
    const { Profiler } = await import("react");
    const PAGES = 600;
    const blocks = Array.from({ length: PAGES }, (_, page) => ({
      spanId: `b${page}`,
      page,
      bbox: [72, 100, 540, 400],
      blockType: "Text",
      text: Array.from({ length: 60 }, (_, n) => `word${(page * 7 + n) % 50}`).join(" "),
    }));
    const longDoc = {
      numPages: PAGES,
      getPage: async () => ({
        getViewport: ({ scale }: { scale: number }) => ({ width: PAGE_W * scale, height: PAGE_H * scale, transform: [scale, 0, 0, -scale, 0, PAGE_H * scale] }),
        getTextContent: async () => ({ items: [], styles: {} }),
        render: () => ({ promise: Promise.resolve(), cancel() {} }),
        streamTextContent: () => ({}),
      }),
    };
    acquirePdfDocument.mockResolvedValue({ doc: longDoc, pageTexts: new Map() });
    const commits: number[] = [];
    render(
      <Profiler id="pane" onRender={(_id, _phase, actualDuration) => commits.push(actualDuration)}>
        <Reader fileUrl="llpdf://long" blocks={blocks} guidanceSpans={new Set()} activeSpan={null} onTextSelection={() => undefined} onTagMenu={() => undefined} onError={() => undefined} />
      </Profiler>,
    );
    await flush();
    // Three pages near the view (the reader is at pages 300-302).
    for (const { callback, node } of observed) {
      const page = Number((node as HTMLElement).dataset.pdfPage);
      if (page >= 300 && page <= 302) callback([{ isIntersecting: true, target: node } as unknown as IntersectionObserverEntry], {} as IntersectionObserver);
    }
    await flush(50);
    expect(document.querySelectorAll("[data-pdf-layer]")).toHaveLength(3);
    expect(document.querySelectorAll("canvas").length).toBe(PAGES);
    expect(Array.from(document.querySelectorAll("canvas")).filter((canvas) => canvas.width > 0)).toHaveLength(3);
    commits.length = 0;
    // A drag down page 300, one frame per move.
    const top = pageTop(300);
    fireEvent.mouseDown(pageEl(300), { clientX: 100, clientY: top + 110, button: 0, detail: 1 });
    for (let y = 120; y < 390; y += 6) {
      fireEvent.mouseMove(window, { clientX: 300, clientY: top + y });
      await act(async () => {
        await vi.advanceTimersByTimeAsync(16);
      });
    }
    fireEvent.mouseUp(window, { clientX: 300, clientY: top + 390 });
    const dragCommits = [...commits];
    // Against a zoom step, which re-renders every one of the 600 pages.
    commits.length = 0;
    fireEvent.click(screen.getByText("+"));
    await flush(50);
    const fullRender = Math.max(...commits);
    const sorted = [...dragCommits].sort((a, b) => a - b);
    const p95 = sorted[Math.floor(sorted.length * 0.95)] ?? 0;
    const mean = dragCommits.reduce((a, b) => a + b, 0) / Math.max(1, dragCommits.length);
    console.log(`pdf-selection pane commits ${JSON.stringify({ frames: dragCommits.length, mean: +mean.toFixed(2), p95: +p95.toFixed(2), fullRender: +fullRender.toFixed(2) })}`);
    expect(dragCommits.length).toBeGreaterThan(10);
    // A drag frame redraws only the pages it changes: well under a full
    // re-render (a ratio, so a busy machine slows both alike; the numbers
    // printed above go to the review file).
    expect(mean).toBeLessThan(fullRender * 0.6);
  }, 60_000);
});
