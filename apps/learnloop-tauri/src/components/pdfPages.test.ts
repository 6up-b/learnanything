// UX Phase 1 (docs/specs/ux_learnloop_v1.md §6.3): the original PDF is readable
// before the book's text is ready. With no block geometry (a book still being
// prepared, or a text-only extraction) the Reader shows every page of the
// original instead of none.
import { describe, expect, it } from "vitest";
import { findJargon } from "../copy/denyList";
import { pagesLeftOutLabel, pagesShownLabel, pagesToShow } from "./pdfPages";

describe("pagesToShow", () => {
  it("shows the pages the extraction covers", () => {
    expect(pagesToShow([{ page: 4 }, { page: 2 }, { page: 4 }], 10)).toEqual([2, 4]);
  });

  it("shows every page when there is no geometry yet", () => {
    expect(pagesToShow([], 3)).toEqual([0, 1, 2]);
  });

  it("shows nothing until the document is loaded", () => {
    expect(pagesToShow([], null)).toEqual([]);
  });
});

// UX Phase 1 re-test (#3): "original pdf · 26 ingested pages" on a 404-page
// book. The header says nothing when every page is here, and how many of the
// book's pages are here, plainly, when only some are.
describe("what the header says about the pages shown", () => {
  it("says nothing more when every page is shown", () => {
    expect(pagesShownLabel(404, 404)).toBe("original pdf");
    expect(pagesShownLabel(3, null)).toBe("original pdf");
  });

  it("says how many of the book's pages are here when only some are", () => {
    expect(pagesShownLabel(26, 404)).toBe("original pdf · showing 26 of its 404 pages");
  });

  it("marks the pages left out between two shown ones in plain words", () => {
    expect(pagesLeftOutLabel(27, 30)).toBe("⋯ pages 27–30 of the original weren't added to LearnLoop");
    expect(pagesLeftOutLabel(5, 5)).toBe("⋯ page 5 of the original wasn't added to LearnLoop");
  });

  it.each([
    pagesShownLabel(26, 404),
    pagesLeftOutLabel(27, 30),
  ])("uses no internal words: %s", (label) => {
    expect(findJargon(label)).toEqual([]);
  });
});
