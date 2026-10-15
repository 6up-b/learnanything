// Codex review of UX Phase 1 usability round 2, F4: a resume at a passage
// with boxes, asked for before the original PDF's page exists, must end
// centred on that passage once the page is laid out and drawn. The pane
// queued only a delayed page-top scroll; the passage request returned with
// nothing kept, so the learner landed on the top of the page.
import { act, cleanup, fireEvent, render } from "@testing-library/react";
import { createRef } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReaderPdfBlockDto } from "../api/dto";
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

const fakeDoc = {
  numPages: 5,
  getPage: async () => ({
    getViewport: ({ scale }: { scale: number }) => ({ width: 612 * scale, height: 792 * scale }),
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

function renderPane() {
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

it("a resume asked for before the PDF is laid out ends centred on the passage, not the page top", async () => {
  const loading = deferred<{ doc: typeof fakeDoc; pageTexts: Map<number, string> }>();
  acquirePdfDocument.mockReturnValue(loading.promise);
  const { handle } = renderPane();

  // The Reader's resume: the passage's page, then the passage itself.
  handle.current!.scrollToPage(3, 0);
  handle.current!.scrollToSegment(3, "s3");

  loading.resolve({ doc: fakeDoc, pageTexts: new Map() });
  await flush();
  layout.ready = true;
  await flush(200);
  await drawPages();

  expect(scrolls).toContain("center:s3");
  // Nothing moved the view off the passage afterwards.
  expect(scrolls[scrolls.length - 1]).toBe("center:s3");
});

it("a passage asked for alone, before its page is drawn, is centred once it is", async () => {
  acquirePdfDocument.mockResolvedValue({ doc: fakeDoc, pageTexts: new Map() });
  const { handle } = renderPane();
  await flush();
  layout.ready = true;

  handle.current!.scrollToSegment(2, "s2");
  await flush(200);
  await drawPages();

  expect(scrolls[scrolls.length - 1]).toBe("center:s2");
});

it("the learner's own wheel drops a place still waiting for its page", async () => {
  const loading = deferred<{ doc: typeof fakeDoc; pageTexts: Map<number, string> }>();
  acquirePdfDocument.mockReturnValue(loading.promise);
  const { handle, scroller } = renderPane();
  handle.current!.scrollToSegment(3, "s3");
  loading.resolve({ doc: fakeDoc, pageTexts: new Map() });
  await flush();

  fireEvent.wheel(scroller.firstElementChild!, { deltaY: 120 });
  layout.ready = true;
  await flush(200);
  await drawPages();

  expect(scrolls).toEqual([]);
});
