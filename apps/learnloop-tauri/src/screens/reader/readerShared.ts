// Shared helpers for the Reader screen and its rail components (RW1a split).
import type { ReaderAnnotationPlacementDto, ReaderProtectionDto } from "../../api/dto";

export const ANSWER_MODE_OPTIONS = [
  { value: "answer_directly", label: "answer directly" },
  { value: "help_me_reason", label: "help me reason" },
  { value: "ask_me_first", label: "ask me first" },
];

/** The answer style in the learner's words, never its internal name (UX
 *  Phase 1 usability round 2). */
export function answerModeLabel(mode: string): string {
  return ANSWER_MODE_OPTIONS.find((option) => option.value === mode)?.label ?? mode.replace(/_/g, " ");
}

export function clip(text: string, max: number): string {
  return text.length > max ? `${text.slice(0, max)}…` : text;
}

// The wire nodes for a selection: one per covered block (atomic-unit captures
// also carry glyph context for backend disambiguation), falling back to the
// single primary block for selections made outside the DOM capture path.
export interface SelectionNode {
  spanId: string;
  quote: string;
  /** Code points into the block's own text, when the surface knows them
   *  (the original PDF's selection model always does; the extracted text
   *  when the quote is found once in its block). `quote` is that exact
   *  slice, so the sidecar anchors it exactly (reader-pdf-selection). */
  start?: number;
  end?: number;
  prefix?: string;
  suffix?: string;
  /** Learner edited this quote (OCR fix) — the backend prefers it over the
   *  extraction slice as the exercise surface. */
  edited?: boolean;
}

/** The learner's committed capture: one or more blocks, in reading order. */
export interface ReaderSelection {
  spanId: string;
  quote: string;
  nodes?: SelectionNode[];
  /** Learner-edited combined passage (capture editor). The nodes keep
   *  anchoring the original blocks; this overrides the exercise surface. */
  editedText?: string;
  /** Reader RW5a: a Ctrl+drag region of a figure on the original page. */
  region?: { spanId: string; page: number; bbox: number[] };
}

export function selectionNodes(sel: {
  spanId: string;
  quote: string;
  nodes?: SelectionNode[];
}): SelectionNode[] {
  return sel.nodes && sel.nodes.length ? sel.nodes : [{ spanId: sel.spanId, quote: sel.quote }];
}

export interface AnnotationSegment {
  spanId: string;
  page: number | null;
  bbox: number[] | null;
  /** Code points into the block's text (a capture made just now, before the
   *  sidecar's own placement arrives). */
  start?: number;
  end?: number;
}

export interface MarginAnnotation {
  annotationId: string | null;
  quote: string;
  status: string | null;
  learnerText: string;
  kind: string;
  segments: AnnotationSegment[];
  /** Where it lands on the open reading (span_aliases decides); absent for a
   *  capture made just now (then its segments are on the open reading). */
  placement?: ReaderAnnotationPlacementDto;
}

/** The blocks an annotation marks on the open reading: its placed segments
 *  (here or moved), or a capture made just now. Flagged and elsewhere mark
 *  nothing as text (re-read safety). */
export function placedSpanIds(annotation: MarginAnnotation): string[] {
  if (annotation.placement) {
    return annotation.placement.state === "here" || annotation.placement.state === "moved"
      ? annotation.placement.segments.map((segment) => segment.spanId)
      : [];
  }
  return annotation.status === "needs_reanchor" ? [] : annotation.segments.map((segment) => segment.spanId);
}

/** Whether an action grounded in these passages touches what the reading's
 *  protection holds out (exam_material decides): then it is not offered. A
 *  reading held back whole (rule 4) holds out every action on it, with a
 *  selection or without one (Codex review F2). */
export function groundingProtected(protection: ReaderProtectionDto | null | undefined, spanIds: readonly string[]): boolean {
  if (!protection) return false;
  if (protection.withheld) return true;
  if (!protection.heldOutSpanIds.length) return false;
  const held = new Set(protection.heldOutSpanIds);
  return spanIds.some((spanId) => held.has(spanId));
}

/** Whether a selection touches what the reading's protection holds out:
 *  then no model action is offered for it (exam_material decides). */
export function selectionProtected(
  protection: ReaderProtectionDto | null | undefined,
  selection: { spanId: string; nodes?: Array<{ spanId: string }> } | null,
): boolean {
  if (!protection || !selection) return false;
  return groundingProtected(protection, [selection.spanId, ...(selection.nodes ?? []).map((node) => node.spanId)]);
}

/** The passages an Ask sends now, as the Reader's Ask grounds it
 *  (useReaderInquiry's submitAsk): a follow-up's inherited passage, else the
 *  selection, else the active passage. */
export function askGroundingSpans(
  parent: { spanId: string; selectionSpanIds: string[] } | null,
  selection: { spanId: string; nodes?: Array<{ spanId: string }> } | null,
  activeSpan: string | null,
): string[] {
  if (parent) return [parent.spanId, ...parent.selectionSpanIds];
  if (selection) return [selection.spanId, ...(selection.nodes ?? []).map((node) => node.spanId)];
  return activeSpan ? [activeSpan] : [];
}
