// Reader workbench RW3a on the original PDF: a margin mark is drawn in an
// overlay gutter at the left of its passage's box, once the passage's page is
// drawn, and only for passages with a box. The pane reports its pages' own
// sizes, loaded with the document and not from drawing, so the Reader's
// one-mark-per-screenful spacing follows landscape and mixed-size pages
// (review F5), and an undrawn page already has its own height.
import { act, cleanup, fireEvent, render } from "@testing-library/react";
import { createRef, type ReactNode } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReaderPdfBlockDto } from "../api/dto";
import type { PdfPageLayout } from "../screens/reader/cues";
import { PdfReaderPane, type PdfReaderPaneHandle } from "./PdfReaderPane";

const { acquirePdfDocument } = vi.hoisted(() => ({ acquirePdfDocument: vi.fn() }));
vi.mock("./pdfDocumentCache", () => ({ acquirePdfDocument }));
vi.mock("pdfjs-dist", () => ({
  GlobalWorkerOptions: {},
  TextLayer: class {
    render() {
      return Promise.resolve();
    }
  }
}));
vi.mock("pdfjs-dist/build/pdf.worker.min.mjs?url", () => ({ default: "pdf.worker.js" }));
vi.mock("pdfjs-dist/web/pdf_viewer.css", () => ({}));

// Five pages, a passage with a box on each.
const BLOCKS: ReaderPdfBlockDto[] = [0, 1, 2, 3, 4].map((page) => ({
  spanId: `s${page}`,
  page,
  bbox: [50, 300, 550, 400],
  blockType: "Text",
  text: `Passage on page ${page}.`
}));

const PAGE_HEIGHT = 400;
const layout = { ready: false };
// Every scroll the pane makes, in order: a centred passage or a page put at the top.
const scrolls: string[] = [];
const observed: Array<{ callback: IntersectionObserverCallback; node: Element }> = [];

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((yes) => {
    resolve = yes;
  });
  return { promise, resolve };
}

// Letter pages, but page 2 is landscape.
const SIZES = [[612, 792], [612, 792], [792, 612], [612, 792], [612, 792]];
const fakeDoc = {
  numPages: 5,
  getPage: async (pageNumber: number) => ({
    getViewport: ({ scale }: { scale: number }) => ({ width: SIZES[pageNumber - 1][0] * scale, height: SIZES[pageNumber - 1][1] * scale }),
    render: () => ({ promise: Promise.resolve() }),
    streamTextContent: () => ({})
  })
};

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "requestAnimationFrame", "cancelAnimationFrame"] });
  layout.ready = false;
  scrolls.length = 0;
  observed.length = 0;
  vi.stubGlobal("ResizeObserver", class {
    observe() {}
    disconnect() {}
  });
  // Pages are drawn once they come near the view (the pane's lazy rendering).
  vi.stubGlobal("IntersectionObserver", class {
    constructor(private callback: IntersectionObserverCallback) {}
    observe(node: Element) {
      observed.push({ callback: this.callback, node });
    }
    disconnect() {}
  });
  HTMLCanvasElement.prototype.getContext = vi.fn(() => ({})) as unknown as typeof HTMLCanvasElement.prototype.getContext;
  Element.prototype.scrollIntoView = vi.fn(function (this: Element, options?: boolean | ScrollIntoViewOptions) {
    const element = this as HTMLElement;
    const where = typeof options === "object" ? options.block : "start";
    scrolls.push(element.dataset.spanId ? `${where}:${element.dataset.spanId}` : `${where}:page${element.dataset.pdfPage}`);
  });
  vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(function (this: Element) {
    const page = (this as HTMLElement).dataset?.pdfPage;
    const height = page !== undefined && layout.ready ? PAGE_HEIGHT : 0;
    const top = page !== undefined && layout.ready ? Number(page) * PAGE_HEIGHT : 0;
    return { top, bottom: top + height, height, width: 320, left: 0, right: 320, x: 0, y: top, toJSON: () => ({}) } as DOMRect;
  });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

async function flush(ms = 0) {
  for (let i = 0; i < 6; i += 1) {
    await act(async () => {
      await vi.advanceTimersByTimeAsync(i === 0 ? ms : 50);
    });
  }
}

function renderPane(extra: { marks?: ReadonlyMap<string, ReactNode>; onPageLayout?: (layout: PdfPageLayout) => void } = {}) {
  const handle = createRef<PdfReaderPaneHandle>();
  const view = render(
    <div data-testid="scroller" style={{ overflowY: "auto" }}>
      <PdfReaderPane
        ref={handle}
        fileUrl="llpdf://sha256-book"
        blocks={BLOCKS}
        guidanceSpans={new Set()}
        activeSpan={null}
        onTextSelection={() => undefined}
        onTagMenu={() => undefined}
        onError={() => undefined}
        marks={extra.marks}
        onPageLayout={extra.onPageLayout}
      />
    </div>
  );
  const scroller = view.getByTestId("scroller");
  let top = 0;
  Object.defineProperty(scroller, "scrollTop", {
    configurable: true,
    get: () => top,
    set: (value: number) => {
      top = value;
      scrolls.push(`top:${value}`);
    }
  });
  return { handle, scroller };
}

/** Pages near the view are drawn: each gets its size and its passage boxes. */
async function drawPages() {
  for (const { callback, node } of observed) {
    callback([{ isIntersecting: true, target: node } as unknown as IntersectionObserverEntry], {} as IntersectionObserver);
  }
  await flush(200);
}

it("a mark is drawn at the left of its passage's box once the page is drawn", async () => {
  acquirePdfDocument.mockResolvedValue({ doc: fakeDoc, pageTexts: new Map() });
  const marks = new Map<string, ReactNode>([["s2", <button key="m" type="button" data-cue-mark="cue_s2">mark</button>]]);
  Object.defineProperty(HTMLElement.prototype, "clientWidth", { configurable: true, get: () => 642 });
  renderPane({ marks });
  await flush();
  layout.ready = true;
  await flush(200);
  expect(document.querySelector("[data-cue-mark]")).toBeNull(); // its page is not drawn yet
  await drawPages();
  const gutter = document.querySelector<HTMLElement>("[data-cue-gutter='s2']");
  expect(gutter).not.toBeNull();
  expect(gutter!.closest("[data-pdf-page]")?.getAttribute("data-pdf-page")).toBe("2");
  expect(gutter!.querySelector("[data-cue-mark='cue_s2']")).not.toBeNull();
  // Just left of the box (bbox x0 = 50 points), at its top (y0 = 300 points).
  expect(parseFloat(gutter!.style.left)).toBeLessThan(50);
  expect(parseFloat(gutter!.style.top)).toBeGreaterThan(0);
  expect(document.querySelectorAll("[data-cue-gutter]")).toHaveLength(1);
  // @ts-expect-error -- restore jsdom's own (prototype chain) getter
  delete HTMLElement.prototype.clientWidth;
});

it("the pane reports each page's own size before any page is drawn, and an undrawn page has its own height", async () => {
  acquirePdfDocument.mockResolvedValue({ doc: fakeDoc, pageTexts: new Map() });
  const onPageLayout = vi.fn();
  Object.defineProperty(HTMLElement.prototype, "clientWidth", { configurable: true, get: () => 642 });
  renderPane({ onPageLayout });
  await flush();
  // Nothing is drawn (no page came near the view), yet the sizes are known:
  // the Reader's spacing model reads them at the pages' width (642 - 2 at 100 %).
  expect(onPageLayout).toHaveBeenLastCalledWith({
    widthPx: 640,
    pages: SIZES.map(([widthPoints, heightPoints], page) => ({ page, widthPoints, heightPoints, leftOutBefore: false })),
  });
  // The landscape page's placeholder is already landscape, so the layout the
  // model assumes is the layout on screen while the learner scrolls.
  const landscape = document.querySelector<HTMLElement>("[data-pdf-page='2']");
  expect(parseFloat(landscape!.style.height)).toBeCloseTo(640 * (612 / 792), 3);
  const portrait = document.querySelector<HTMLElement>("[data-pdf-page='1']");
  expect(parseFloat(portrait!.style.height)).toBeCloseTo(640 * (792 / 612), 3);
  // @ts-expect-error -- restore jsdom's own (prototype chain) getter
  delete HTMLElement.prototype.clientWidth;
});

it("without marks the pages carry no gutter", async () => {
  acquirePdfDocument.mockResolvedValue({ doc: fakeDoc, pageTexts: new Map() });
  renderPane();
  await flush();
  layout.ready = true;
  await drawPages();
  expect(document.querySelector("[data-cue-gutter]")).toBeNull();
});
