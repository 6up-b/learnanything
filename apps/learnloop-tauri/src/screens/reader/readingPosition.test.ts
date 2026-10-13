// The preparing view's hand-over keeps the learner's place (UX Phase 1 review F8).
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ReaderPdfBlockDto } from "../../api/dto";
import { readingPositionIn, spanAtPosition } from "./readingPosition";

function rect(top: number, height: number, width = 600): DOMRect {
  return { top, bottom: top + height, height, width, left: 0, right: width, x: 0, y: top, toJSON: () => ({}) } as DOMRect;
}

afterEach(() => {
  vi.restoreAllMocks();
  document.body.innerHTML = "";
});

describe("readingPositionIn", () => {
  it("is the page at the top of the view and how far down it the view starts", () => {
    const scroller = document.createElement("div");
    scroller.innerHTML = [0, 1, 2]
      .map((page) => `<div data-pdf-page="${page}" data-width-points="612"></div>`)
      .join("");
    document.body.appendChild(scroller);
    const rects: Record<string, DOMRect> = { "0": rect(-1700, 800), "1": rect(-860, 800), "2": rect(-40, 800) };
    vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(function (this: Element) {
      const page = (this as HTMLElement).dataset?.pdfPage;
      return page !== undefined ? rects[page] : rect(0, 700);
    });
    const position = readingPositionIn(scroller);
    expect(position?.page).toBe(2);
    expect(position?.offset).toBeCloseTo(0.05);
    expect(position?.pageHeightPoints).toBeCloseTo((800 * 612) / 600);
  });

  it("is nothing while no page is laid out", () => {
    const scroller = document.createElement("div");
    expect(readingPositionIn(scroller)).toBeNull();
    expect(readingPositionIn(null)).toBeNull();
  });
});

describe("spanAtPosition", () => {
  const block = (spanId: string, page: number, y0: number, y1: number): ReaderPdfBlockDto => ({
    spanId,
    page,
    bbox: [50, y0, 550, y1],
    blockType: "text"
  });
  const blocks = [block("s1", 4, 60, 120), block("s2", 4, 130, 400), block("s3", 4, 410, 700), block("s9", 5, 60, 90)];

  it("is the first passage at or below the top of the view on that page", () => {
    expect(spanAtPosition(blocks, { page: 4, offset: 0.25, pageHeightPoints: 800 })).toBe("s2");
    expect(spanAtPosition(blocks, { page: 4, offset: 0, pageHeightPoints: 800 })).toBe("s1");
    expect(spanAtPosition(blocks, { page: 4, offset: 0.95, pageHeightPoints: 800 })).toBe("s3");
  });

  it("is nothing for a page without passages", () => {
    expect(spanAtPosition(blocks, { page: 7, offset: 0.5 })).toBeNull();
  });
});
