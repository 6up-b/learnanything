// Reader workbench RW3a: margin cues from the Guide (spec §6.1; UX §3.4, §4.4).
//
// The sidecar sends the guide plan's own misunderstanding passages as cues,
// already within the learner's density budget (`[cues] density`). This module
// holds the Reader's own restraint rules, pure so they are tested alone:
//
// * at most one LearnLoop mark per screenful (`onePerViewport`): marks are
//   placed by rank, and a lower-ranked mark within one viewport height of a
//   higher-ranked one is not shown. Placement is computed when the text is
//   laid out, never while scrolling, so nothing appears or disappears as the
//   learner reads;
// * never on the passage the learner was restored to (it would greet them
//   with a judgement), never while skimming, never in the workbench's source
//   pane while working, never animated;
// * and the fixed copy every cue surface shows (G16: it says what connects,
//   never what the learner lacks).
import type { CueDensity, ReaderCueDto } from "../../api/dto";

export const CUE_DENSITIES: readonly CueDensity[] = ["off", "fewer", "normal", "more"];

/** Marks per section at each density (a display limit the learner owns). */
export const DENSITY_BUDGET: Readonly<Record<CueDensity, number>> = { off: 0, fewer: 1, normal: 2, more: 4 };

/** "Fewer marks like this": one notch down (more → normal → fewer → off). */
export function stepDown(density: CueDensity): CueDensity {
  const index = CUE_DENSITIES.indexOf(density);
  return CUE_DENSITIES[Math.max(0, (index < 0 ? 2 : index) - 1)];
}

/** Every fixed string the cue surfaces show (the G16 lint reads these). */
export const CUE_COPY = {
  /** RW3a's one kind: connects to something you worked on. */
  glyph: "◌┆",
  markName: "margin note",
  popoverLabel: "this margin note",
  open: "open",
  openTitle: "what you worked on",
  answeredOn: "You answered a question on this on",
  answeredUndated: "You answered a question on this earlier.",
  question: "the question",
  readingNote: "its reading of that answer",
  readingPending: "LearnLoop's model is still reading that answer.",
  checkMe: "check me",
  checkMeHint: "a short question on your own, with the book out of view",
  checkMeFinding: "◐ finding a short question…",
  checkMeNone: "Nothing in your practice fits this yet.",
  checkMeFailed: "Couldn't find a question just now.",
  tryAgain: "try again",
  notRelevant: "not relevant…",
  notRelevantWhy: "why? (optional)",
  notRelevantWhere:
    "Tells LearnLoop this mark missed, so marks like it get better. It isn't read for gaps in your understanding, and it never grades you.",
  send: "send",
  fewer: "fewer marks like this",
  offBook: "marks off for this book",
  offEverywhere: "marks off everywhere",
  footerLabel: "margin marks",
  footerLimit: "a display limit to protect your attention",
  legendToggle: "what the marks mean",
  legendRevisit: "connects to something you worked on (from the Guide's citations)",
  receiptNotRelevant: "Marked not relevant.",
  receiptBookOff: "Margin marks are off for this book.",
  receiptEverywhereOff: "Margin marks are off everywhere.",
  receiptDensity: "Margin marks:",
  bookOff: "Margin marks are off for this book.",
  turnOn: "turn back on",
  undo: "undo",
  close: "close",
} as const;

/** Why a cue the sidecar sent is not drawn (never a holdout: RW3a has none). */
export type CueSuppression = "skim" | "working" | "restored_line" | "spacing" | "no_place";

export interface CuePlacementInput {
  /** The sidecar's cues, already within the density budget. */
  marks: readonly ReaderCueDto[];
  /** Skim mode: the bare book. */
  muted: boolean;
  /** The workbench's source pane while working (RW2a): no marks. */
  working: boolean;
  /** The passage the Reader placed the learner at (a resume, a return). */
  restoredSpanId: string | null;
  /** At most one mark per screenful (`cues.one_per_viewport`). */
  onePerViewport: boolean;
  /** Where a passage sits, in pixels from one origin; null: no place to draw. */
  positionOf: (spanId: string) => number | null;
  /** The reading area's height: one screenful. */
  viewportHeight: number;
}

export interface CuePlacement {
  /** The marks to draw, in reading order. */
  shown: ReaderCueDto[];
  suppressed: Array<{ cue: ReaderCueDto; reason: CueSuppression }>;
}

/** Which of the sidecar's cues the Reader draws now (pure). */
export function placeCueMarks(input: CuePlacementInput): CuePlacement {
  const ranked = [...input.marks].sort((a, b) => a.rank - b.rank);
  if (input.muted) return { shown: [], suppressed: ranked.map((cue) => ({ cue, reason: "skim" as const })) };
  if (input.working) return { shown: [], suppressed: ranked.map((cue) => ({ cue, reason: "working" as const })) };
  const placed: Array<{ cue: ReaderCueDto; y: number }> = [];
  const suppressed: CuePlacement["suppressed"] = [];
  for (const cue of ranked) {
    if (input.restoredSpanId !== null && cue.spanId === input.restoredSpanId) {
      suppressed.push({ cue, reason: "restored_line" });
      continue;
    }
    const y = input.positionOf(cue.spanId);
    if (y === null || !Number.isFinite(y)) {
      suppressed.push({ cue, reason: "no_place" });
      continue;
    }
    if (input.onePerViewport && input.viewportHeight > 0
      && placed.some((other) => Math.abs(other.y - y) < input.viewportHeight)) {
      suppressed.push({ cue, reason: "spacing" });
      continue;
    }
    placed.push({ cue, y });
  }
  placed.sort((a, b) => a.y - b.y || a.cue.rank - b.cue.rank);
  return { shown: placed.map((entry) => entry.cue), suppressed };
}

/** The next mark in reading order after (or before) `fromIndex` (Alt+↓ / Alt+↑). */
export function stepMark(count: number, fromIndex: number, direction: 1 | -1): number | null {
  if (count === 0) return null;
  const next = fromIndex + direction;
  if (fromIndex < 0) return direction === 1 ? 0 : count - 1;
  return next >= 0 && next < count ? next : null;
}

/** US letter: the page model the original PDF's spacing assumes (points). */
export const PDF_PAGE_POINTS = { width: 612, height: 792 };
/** The pane's gap between pages, in pixels. */
export const PDF_PAGE_GAP_PX = 14;

/** Where a passage with a box sits on the original PDF, in pixels from the
 *  first page's top: a stable page model (letter pages at the pane's width),
 *  so spacing never changes as pages are drawn while the learner scrolls. */
export function pdfPassageTop(page: number, bboxTop: number, pageWidthPx: number): number {
  const scale = pageWidthPx / PDF_PAGE_POINTS.width;
  const pageHeight = PDF_PAGE_POINTS.height * scale + PDF_PAGE_GAP_PX;
  return page * pageHeight + bboxTop * scale;
}
