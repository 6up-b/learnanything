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

/** The page under a reading marker ``fraction`` of the way down ``scroller``'s
 * viewport, and how far into that page the marker is (usability round 1, U2:
 * the original PDF follows the learner without block geometry). */
export function pagePositionAt(scroller: HTMLElement | null, fraction: number): ReadingPosition | null {
  if (!scroller) return null;
  const box = scroller.getBoundingClientRect();
  const marker = box.top + box.height * fraction;
  const pages = Array.from(scroller.querySelectorAll<HTMLElement>("[data-pdf-page]"));
  let last: ReadingPosition | null = null;
  for (const pageEl of pages) {
    const rect = pageEl.getBoundingClientRect();
    const page = Number(pageEl.dataset.pdfPage);
    if (rect.height <= 0 || !Number.isFinite(page)) continue;
    if (rect.top > marker) break;
    last = { page, offset: Math.min(Math.max((marker - rect.top) / rect.height, 0), 1) };
    if (rect.bottom >= marker) return last;
  }
  return last;
}

/** The passage a page position lands on when passages only know their page
 * (a text-only extraction): the page's passages split it evenly; a page with
 * none (a figure, a blank page) belongs to the last passage before it. */
export function spanOnPage(
  pageSpans: ReadonlyArray<{ spanId: string; page: number }>,
  position: ReadingPosition
): string | null {
  const onPage = pageSpans.filter((entry) => entry.page === position.page);
  if (onPage.length > 0) {
    const index = Math.min(onPage.length - 1, Math.floor(position.offset * onPage.length));
    return onPage[index].spanId;
  }
  const before = pageSpans.filter((entry) => entry.page < position.page);
  return before.length > 0 ? before[before.length - 1].spanId : (pageSpans[0]?.spanId ?? null);
}
