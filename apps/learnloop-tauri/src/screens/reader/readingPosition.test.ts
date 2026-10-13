// The preparing view's hand-over keeps the learner's place (UX Phase 1 review F8).
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ReaderPdfBlockDto } from "../../api/dto";
import { readingPositionIn, resumeSpanFromHistory, spanAtPosition } from "./readingPosition";

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

  // Usability round 2: a hand-over read while the first pages were still
  // unmeasured named a later page (the Contents), and the Reader opened there.
  it("is nothing while a page before the view's top is not laid out yet", () => {
    const scroller = document.createElement("div");
    scroller.innerHTML = [0, 1, 2]
      .map((page) => `<div data-pdf-page="${page}" data-width-points="612"></div>`)
      .join("");
    document.body.appendChild(scroller);
    const rects: Record<string, DOMRect> = { "0": rect(0, 0), "1": rect(0, 0), "2": rect(0, 800) };
    vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(function (this: Element) {
      const page = (this as HTMLElement).dataset?.pdfPage;
      return page !== undefined ? rects[page] : rect(0, 700);
    });
    expect(readingPositionIn(scroller)).toBeNull();
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

// UX Phase 1 usability round 2: a book read before the Reader saved places
// (months of history, Axler in the three-month persona's library) reopened at
// its first page while Contents ticked sections deep into the book.
describe("resumeSpanFromHistory", () => {
  const sections = [
    { id: "u1", spanIds: ["s1"] },
    { id: "u2", spanIds: ["s2", "s3"] },
    { id: "u3", spanIds: ["s4", "s5", "s6"] },
    { id: "u4", spanIds: ["s7"] }
  ];
  const row = (sectionId: string, fields: Partial<{ spansSeen: number; completedAt: string | null; revealedAt: string | null }>) => ({
    sectionId, spansSeen: 0, completedAt: null, revealedAt: null, ...fields
  });

  it("has nothing to say for a book never read", () => {
    expect(resumeSpanFromHistory(sections, [])).toBeNull();
  });

  it("continues after the furthest section finished, not at a section skipped on the way", () => {
    expect(resumeSpanFromHistory(sections, [row("u1", { completedAt: "t" }), row("u3", { completedAt: "t" })])).toBe("s7");
  });

  it("continues inside a section read part of the way, at its first unread passage", () => {
    expect(resumeSpanFromHistory(sections, [row("u2", { completedAt: "t" }), row("u3", { spansSeen: 1 })])).toBe("s5");
  });

  it("treats a section read through as finished", () => {
    expect(resumeSpanFromHistory(sections, [row("u2", { spansSeen: 2 })])).toBe("s4");
  });

  it("starts a section whose check was only looked at", () => {
    expect(resumeSpanFromHistory(sections, [row("u3", { revealedAt: "t" })])).toBe("s4");
  });

  it("stays in the last section when the whole book was read", () => {
    expect(resumeSpanFromHistory(sections, [row("u4", { completedAt: "t" })])).toBe("s7");
  });
});
