// @vitest-environment node
// Performance of the PDF selection model on a long book (reader-pdf-selection):
// a 600-page synthetic PDF, written here and parsed by the real pdf.js, two
// columns of prose per page, a display formula on every third page, and the
// second half scanned (no text layer: words placed by estimate in its boxes).
//
// What must stay smooth at 60 fps (16.7 ms a frame): one drag frame is a
// hit-test and the selection's boxes on the pages near the view (the pane
// draws only those). Placing a page's words happens once, when the page comes
// near the view. The hand-over (the selection's nodes and text) happens once,
// 150 ms after the mouse is released. Budgets are generous on purpose (the
// suite runs on a shared, busy machine) and the measured numbers are printed
// for the review file. Rerun this file alone before reading a failure as a
// regression.
import { describe, expect, it } from "vitest";
import type { ReaderPdfBlockDto } from "../../api/dto";
import { hitTest, rangeRects, selectionPayload, SelectionModel, type Pos, type SelRange } from "./model";
import { buildPdf, readPdf, type PdfPageSpec, type PdfText } from "./testing/syntheticPdf";

const PAGES = 600;
const SCANNED_FROM = 300;
const WORDS = "the a of and vector space linear map basis kernel image rank field scalar sum product matrix row column entry".split(" ");

function line(seed: number): string {
  const out: string[] = [];
  let length = 0;
  for (let i = 0; length < 40; i++) {
    const word = WORDS[(seed * 7 + i * 13) % WORDS.length];
    out.push(word);
    length += word.length + 1;
  }
  return out.join(" ");
}

interface Para {
  spanId: string;
  blockType: string;
  x: number;
  y: number;
  lines: string[];
  text?: string;
}

function pageParas(page: number): Para[] {
  const paras: Para[] = [];
  for (let column = 0; column < 2; column++) {
    for (let index = 0; index < 4; index++) {
      const lines = Array.from({ length: 6 }, (_, n) => line(page * 100 + column * 30 + index * 7 + n));
      paras.push({ spanId: `p${page}c${column}i${index}`, blockType: "Text", x: column ? 320 : 72, y: 80 + index * 160, lines });
    }
  }
  if (page % 3 === 0) {
    paras.push({ spanId: `p${page}eq`, blockType: "Equation", x: 250, y: 730, lines: ["Ax = b"], text: "$$\nA x = b\n$$" });
  }
  return paras;
}

function texts(paras: Para[]): PdfText[] {
  return paras.flatMap((para) => para.lines.map((text, n) => ({ x: para.x, y: para.y + n * 14, size: 10, text })));
}

function blocks(page: number, paras: Para[]): ReaderPdfBlockDto[] {
  return paras.map((para) => ({
    spanId: para.spanId,
    page,
    bbox: [para.x - 1, para.y - 9, para.x + 220, para.y + (para.lines.length - 1) * 14 + 3],
    blockType: para.blockType,
    text: para.text ?? para.lines.join(" "),
  }));
}

function percentile(values: number[], p: number): number {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.min(sorted.length - 1, Math.floor((p / 100) * sorted.length))];
}

describe("a 600-page book", () => {
  it("stays within a 60 fps frame: drags, page arrival and the hand-over", async () => {
    const specs: PdfPageSpec[] = [];
    const book: ReaderPdfBlockDto[] = [];
    for (let page = 0; page < PAGES; page++) {
      const paras = pageParas(page);
      specs.push(page < SCANNED_FROM ? { texts: texts(paras) } : { scanned: true });
      book.push(...blocks(page, paras));
    }
    const parsed = await readPdf(buildPdf(specs));
    expect(parsed).toHaveLength(PAGES);

    let t = performance.now();
    const model = new SelectionModel(book);
    const constructMs = performance.now() - t;

    // Each page's words placed as it comes near the view.
    const placeMs: number[] = [];
    for (const page of parsed) {
      t = performance.now();
      model.setPageText(page.page, page.items, page.transform);
      placeMs.push(performance.now() - t);
    }

    // Drag frames: a drag from page 120 down to page 124 (text layer) and
    // from 420 to 424 (scanned), the pointer moving 2 points a frame; each
    // frame hit-tests and repaints the three pages near the pointer.
    const frameMs: number[] = [];
    const dragAcross = (fromPage: number) => {
      const anchor = hitTest(model, fromPage, 100, 100) as Pos;
      let ranges: SelRange[] = [];
      for (let page = fromPage; page < fromPage + 4; page++) {
        for (let y = 80; y < 760; y += 2) {
          const start = performance.now();
          const head = hitTest(model, page, 150 + ((y * 3) % 300), y);
          if (head) ranges = [{ anchor, head }];
          for (const near of [page - 1, page, page + 1]) rangeRects(model, ranges, near);
          frameMs.push(performance.now() - start);
        }
      }
      return ranges;
    };
    dragAcross(120);
    dragAcross(420);

    // The hand-over of a selection across half the book.
    const wide: SelRange[] = [{ anchor: hitTest(model, 10, 100, 100) as Pos, head: hitTest(model, 310, 400, 600) as Pos }];
    t = performance.now();
    const payload = selectionPayload(model, wide);
    const handOverMs = performance.now() - t;
    expect(payload?.nodes.length).toBeGreaterThan(2500);

    const report = {
      pages: PAGES,
      blocks: model.blocks.length,
      constructMs: +constructMs.toFixed(1),
      placePageMs: { mean: +(placeMs.reduce((a, b) => a + b, 0) / placeMs.length).toFixed(2), p95: +percentile(placeMs, 95).toFixed(2), max: +Math.max(...placeMs).toFixed(2) },
      dragFrameMs: { frames: frameMs.length, mean: +(frameMs.reduce((a, b) => a + b, 0) / frameMs.length).toFixed(3), p95: +percentile(frameMs, 95).toFixed(3), max: +Math.max(...frameMs).toFixed(2) },
      handOverMs: +handOverMs.toFixed(1),
    };
    console.log(`pdf-selection perf ${JSON.stringify(report)}`);

    expect(constructMs).toBeLessThan(500);
    expect(report.placePageMs.mean).toBeLessThan(8);
    // A drag frame leaves most of the 16.7 ms frame for the browser.
    expect(report.dragFrameMs.p95).toBeLessThan(4);
    expect(report.dragFrameMs.mean).toBeLessThan(2);
    expect(handOverMs).toBeLessThan(400);
  }, 180_000);
});
