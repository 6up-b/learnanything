// The learner's highlights and notes on the original PDF (reader-pdf-selection).
//
// A highlight is drawn from its anchor (a block of the open reading and
// code points into its text) through the selection model, never from stored
// screen or page coordinates: its boxes are the model's word boxes for those
// words, so it follows zoom, resize and reload, and a re-read moves it with
// its words. Where it lands on the open reading is the sidecar's answer
// (`reader.source_annotations` with the reading, through span_aliases):
// here, moved after a re-read (drawn, labelled), or flagged (its words
// changed: a dashed outline on the passage that took its place, never drawn
// as text).

import type { ReaderAnnotationPlacementDto } from "../../api/dto";
import { anchorRange, rangeRects, type Box, type SelRange, type SelectionModel } from "./model";

export type HighlightState = "here" | "moved" | "flagged";

export interface PdfHighlight {
  id: string;
  /** The annotation's kind (highlight, question, confusion, a preset…). */
  kind: string;
  state: HighlightState;
  /** Each part: a block of the open reading and code points into its text. */
  segments: ReadonlyArray<{ spanId: string; start: number; end: number }>;
  /** Flagged: the passage that took its place. */
  flagSpanId: string | null;
  quote: string;
  note: string;
}

export interface PlacedHighlight extends PdfHighlight {
  /** Its words in the model (empty when flagged or not on this reading). */
  ranges: SelRange[];
  /** Flagged: the block outlined. */
  flagBlock: number | null;
}

/** A highlight's segments as given by the sidecar's placement, or null when
 *  it marks nothing on the open reading (not on it at all). */
export function highlightFromPlacement(
  base: { id: string; kind: string; quote: string; note: string },
  placement: ReaderAnnotationPlacementDto,
): PdfHighlight | null {
  if (placement.state === "elsewhere") return null;
  if (placement.state === "flagged") {
    return placement.flagSpanId ? { ...base, state: "flagged", segments: [], flagSpanId: placement.flagSpanId } : null;
  }
  return {
    ...base,
    state: placement.state,
    segments: placement.segments.map((segment) => ({ spanId: segment.spanId, start: segment.codepointStart, end: segment.codepointEnd })),
    flagSpanId: null,
  };
}

/** Each highlight's words in the model. A segment whose block the model does
 *  not hold (furniture, a block with no box) draws nothing; a highlight with
 *  nothing to draw is left out. */
export function placeHighlights(model: SelectionModel, highlights: readonly PdfHighlight[]): PlacedHighlight[] {
  const placed: PlacedHighlight[] = [];
  for (const highlight of highlights) {
    if (highlight.state === "flagged") {
      const flagBlock = highlight.flagSpanId ? model.blockIndex(highlight.flagSpanId) ?? null : null;
      if (flagBlock !== null) placed.push({ ...highlight, ranges: [], flagBlock });
      continue;
    }
    const ranges = highlight.segments.flatMap((segment) => {
      const range = anchorRange(model, segment.spanId, segment.start, segment.end);
      return range ? [range] : [];
    });
    if (ranges.length) placed.push({ ...highlight, ranges, flagBlock: null });
  }
  return placed;
}

export interface HighlightOnPage {
  id: string;
  kind: string;
  state: HighlightState;
  rects: Box[];
  /** The highlight starts on this page (its label and keyboard stop go here). */
  starts: boolean;
}

/** The boxes each highlight draws on one page (PDF points), in the order
 *  they were made (a later one draws over an earlier one). */
export function highlightsOnPage(model: SelectionModel, placed: readonly PlacedHighlight[], page: number): HighlightOnPage[] {
  const out: HighlightOnPage[] = [];
  for (const highlight of placed) {
    if (highlight.flagBlock !== null) {
      const block = model.blocks[highlight.flagBlock];
      if (block.page === page) out.push({ id: highlight.id, kind: highlight.kind, state: "flagged", rects: [block.bbox], starts: true });
      continue;
    }
    const rects = rangeRects(model, highlight.ranges, page);
    if (!rects.length) continue;
    const first = highlight.ranges.reduce((lo, range) => Math.min(lo, range.anchor.block, range.head.block), Infinity);
    out.push({ id: highlight.id, kind: highlight.kind, state: highlight.state, rects, starts: model.blocks[first]?.page === page });
  }
  return out;
}

/** The highlight under a point on a page (the most recent one when several
 *  overlap), or null. */
export function highlightAt(onPage: readonly HighlightOnPage[], x: number, y: number): string | null {
  for (let index = onPage.length - 1; index >= 0; index--) {
    const entry = onPage[index];
    const tolerance = entry.state === "flagged" ? 0 : 1;
    if (entry.rects.some((r) => x >= r[0] - tolerance && x <= r[2] + tolerance && y >= r[1] - tolerance && y <= r[3] + tolerance)) {
      return entry.id;
    }
  }
  return null;
}

const KIND_LABELS: Record<string, string> = {
  highlight: "Highlight",
  question: "Question",
  confusion: "Marked confusing",
  mark_confusing: "Marked confusing",
  interpretation: "My interpretation",
  disposition: "Not worth remembering",
  not_worth_remembering: "Not worth remembering",
  test_me_later: "Test me later",
  help_me_remember: "Help me remember",
  connect_it: "Connect it",
};

/** The kind in plain words. */
export function kindLabel(kind: string): string {
  return KIND_LABELS[kind] ?? kind.replace(/_/g, " ").replace(/^./, (ch) => ch.toUpperCase());
}

/** What a moved or flagged highlight says about itself. */
export function stateLabel(state: HighlightState): string | null {
  if (state === "moved") return "moved here when the book was read again";
  if (state === "flagged") return "its words changed when the book was read again: select them again to keep it here";
  return null;
}

/** The accessible name of a highlight's keyboard stop. */
export function highlightAriaLabel(highlight: Pick<PdfHighlight, "kind" | "state" | "quote" | "note">): string {
  const quote = highlight.quote.replace(/\s+/g, " ").trim();
  const clipped = quote.length > 80 ? `${quote.slice(0, 80)}…` : quote;
  const parts = [kindLabel(highlight.kind)];
  if (clipped) parts.push(`“${clipped}”`);
  const state = stateLabel(highlight.state);
  if (state) parts.push(state);
  if (highlight.note.trim()) parts.push(`note: ${highlight.note.trim()}`);
  parts.push("Enter opens it, Delete removes it");
  return parts.join(". ");
}
