// Where the learner is in an original PDF, so the hand-over from the preparing
// view to the full Reader keeps their place (UX Phase 1 review F8): the page
// at the top of the viewport and how far down it the viewport starts.
import type { ReaderPdfBlockDto } from "../../api/dto";

export interface ReadingPosition {
  /** 0-based page index, as `data-pdf-page` and `ReaderPdfBlockDto.page`. */
  page: number;
  /** How far down that page the viewport's top edge is, 0..1. */
  offset: number;
  /** The page's height in PDF points, when the page is laid out. */
  pageHeightPoints?: number | null;
}

/** The page at the top of ``scroller``'s viewport and the offset into it. */
export function readingPositionIn(scroller: HTMLElement | null): ReadingPosition | null {
  if (!scroller) return null;
  const top = scroller.getBoundingClientRect().top;
  const pages = Array.from(scroller.querySelectorAll<HTMLElement>("[data-pdf-page]"));
  for (const pageEl of pages) {
    const rect = pageEl.getBoundingClientRect();
    if (rect.height <= 0 || rect.bottom <= top + 1) continue;
    const page = Number(pageEl.dataset.pdfPage);
    if (!Number.isFinite(page)) continue;
    const widthPoints = Number(pageEl.dataset.widthPoints);
    const scale = widthPoints > 0 && rect.width > 0 ? rect.width / widthPoints : 0;
    return {
      page,
      offset: Math.min(Math.max((top - rect.top) / rect.height, 0), 1),
      pageHeightPoints: scale > 0 ? rect.height / scale : null
    };
  }
  return null;
}

/** The first passage the learner had in view: the first block on that page at
 * or below the viewport's top edge (else the page's last block above it). */
export function spanAtPosition(blocks: ReaderPdfBlockDto[], position: ReadingPosition): string | null {
  const onPage = blocks
    .filter((block) => block.page === position.page && block.bbox.length >= 4)
    .sort((a, b) => a.bbox[1] - b.bbox[1]);
  if (onPage.length === 0) return null;
  const height = position.pageHeightPoints ?? Math.max(...onPage.map((block) => block.bbox[3]));
  const edge = position.offset * height;
  const below = onPage.find((block) => block.bbox[3] > edge);
  return (below ?? onPage[onPage.length - 1]).spanId;
}
