// Shared helpers for the Reader screen and its rail components (RW1a split).
import type { ReaderAnnotationPlacementDto, ReaderProtectionDto } from "../../api/dto";

/** A section's controls and states, the same words on the desktop's guide and the phone's Reader (algorithm tag
 *  mvp-0.63: a section's end finishes it; closing a quick check does not). */
/** The learner's own way to finish a section, a short one that needs no scrolling included. */
export const SECTION_DONE = "I’ve read this section";
/** The finished state, shown only once the section's completion is the backend's (or, on the phone, durably queued). */
export const SECTION_DONE_LINE = "Section finished";
/** Navigation only: finishing has its own event. */
export const READ_NEXT_SECTION = "Read the next section";
/** At the end of the book's last section (a one-section book's only one): no next section to offer. */
export const BACK_TO_TODAY = "Back to Today";
/** Closes a quick check, keeping its answer and comparison; it finishes nothing. */
export const CHECK_DONE = "Done with this check";
/** The finished state of a section the learner's own reading finished by reaching its end (the backend's stored cause):
 *  said where "I've read this section" was, so the control vanishing is explained. */
export const SECTION_ENDED_LINE = "Section finished: you read to the end.";
/** How long after the end finishes a section, under the learner's pointer, the first press on the way on (Read the
 *  next section, Back to Today) is taken as the press meant for "I've read this section", which just went: it does
 *  nothing, instead of moving the reading on. About a hand's reaction time. */
export const END_PRESS_GUARD_MS = 1000;
/** The folded record of a closed quick check: what the learner wrote and what it was compared with, one press away. */
export function closedCheckSummary(sectionLabel: string): string {
  return `Your answer to the quick check on “${sectionWords(sectionLabel)}”`;
}

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

const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

/**
 * A section's name as the learner reads it. A web page's sections are stored under the slug of their heading
 * ("modeling-the-elevator-problem": the extraction keeps no heading text), and the part before its first
 * heading under "(intro)"; both are said in words. A book's own titles ("7.1 Symmetric matrices", "§5.A")
 * stay as they are. For showing only: what is sent or matched on is the stored label.
 */
export function sectionWords(label: string): string {
  const trimmed = label.trim();
  if (trimmed === "(intro)") return "Introduction";
  if (!SLUG.test(trimmed) || /^\d+$/.test(trimmed)) return label;
  const words = trimmed.replace(/-/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

/** A cited passage's label, "<title> · <section>", as the learner reads it:
 *  the section in words (a web page's slug, "(intro)"), and a one-section
 *  reading's "root" (the unit of a page with no sections) dropped, so the
 *  chip names the reading by its title. The label stays what the tutor was
 *  given; only what is shown changes. */
export function citationWords(label: string): string {
  const at = label.lastIndexOf(" · ");
  if (at < 0) return label;
  const title = label.slice(0, at);
  const section = label.slice(at + 3).trim();
  if (!section || section === "root") return title;
  return `${title} · ${sectionWords(section)}`;
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

/** Reader follow-ups Nov 1 (CA6b open item 1): passages as `extraction:span`
 *  keys, named by the reading they were taken in (the passage's own
 *  SourceIdentity, never the main pane's render by default). The reading-only
 *  RPCs send them beside the bare ids; the sidecar refuses a key that names
 *  another reading than the request's (span ids repeat across books), and an
 *  id sent without its key. */
export function passageKeys(reading: string, spanIds: ReadonlyArray<string | null | undefined>): string[] {
  return [...new Set(spanIds.filter((span): span is string => Boolean(span)).map((span) => `${reading}:${span}`))];
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
