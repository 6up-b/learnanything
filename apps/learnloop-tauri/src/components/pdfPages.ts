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
