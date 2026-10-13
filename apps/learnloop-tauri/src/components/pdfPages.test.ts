// UX Phase 1 (docs/specs/ux_learnloop_v1.md §6.3): the original PDF is readable
// before the book's text is ready. With no block geometry (a book still being
// prepared, or a text-only extraction) the Reader shows every page of the
// original instead of none.
import { describe, expect, it } from "vitest";
import { pagesToShow } from "./pdfPages";

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
