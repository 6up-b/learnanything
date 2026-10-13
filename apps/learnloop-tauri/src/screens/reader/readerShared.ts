// Shared helpers for the Reader screen and its rail components (RW1a split).

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
}

export interface MarginAnnotation {
  annotationId: string | null;
  quote: string;
  status: string | null;
  learnerText: string;
  kind: string;
  segments: AnnotationSegment[];
}
