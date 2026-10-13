// Which pages of the original PDF the Reader shows (0-based).
//
// The extraction's pages when it has block geometry; every page of the
// original when it has none — a book still being prepared (UX Phase 1, §6.3)
// or a text-only (pypdf) extraction — so the original is always readable.
export function pagesToShow(blocks: ReadonlyArray<{ page: number }>, numPages: number | null): number[] {
  const covered = [...new Set(blocks.map((block) => block.page))].sort((a, b) => a - b);
  if (covered.length > 0 || numPages === null) return covered;
  return Array.from({ length: numPages }, (_, index) => index);
}

// What the pane's header says about the pages it shows (UX Phase 1 re-test
// #3: "original pdf · 26 ingested pages" on a 404-page book read as "LearnLoop
// only knows 26 pages"). Every page shown: nothing more to say. Only some: how
// many of the book's pages are here, in plain words.
export function pagesShownLabel(shown: number, numPages: number | null): string {
  if (numPages === null || shown <= 0 || shown >= numPages) return "original pdf";
  return `original pdf · showing ${shown} of its ${numPages} pages`;
}

// The marker between two shown pages with pages left out between them
// (1-based page numbers, as the learner counts them).
export function pagesLeftOutLabel(firstMissing: number, lastMissing: number): string {
  if (firstMissing === lastMissing) return `⋯ page ${firstMissing} of the original wasn't added to LearnLoop`;
  return `⋯ pages ${firstMissing}–${lastMissing} of the original weren't added to LearnLoop`;
}
