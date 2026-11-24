// The pen recognizer on sources (spec §10.10): one finished stroke, classified by its shape and where it sits
// against the text. Pure: the page is reached only through the probes in `RecognizerPage`, so the rules are
// table-tested on synthetic strokes.
//
// The rules and their numbers are the spec's recognizer geometry (§10.10's table), taken from the mockup's
// recognizer with the details the table leaves out:
// - closed loop: the ends within 30 px, wider than 30 px and taller than 16 px → a selection (lasso);
// - tall and narrow in the margin (taller than 40 px, narrower than 26 px) → a bracket;
// - any other stroke in the margin → a handwritten note;
// - flat (shorter than 22 px) and wider than 40 px: through the middle of a text line → a strike, under it →
//   an underline. "Through the middle" is the mockup's test: the text line found 9 px above the stroke's middle
//   holds the middle between 30 % of its height from its top and 25 % from its bottom, and the line found at
//   the middle itself is that same line;
// - "in the margin": the stroke lies more than 4 px beyond the text column's left or right edge, the column
//   being the first passage wider than 100 px;
// - a stroke of 3 points or fewer is not recognized (a tap).
// Anything else stays plain ink: never a guess shown as certain.

export interface Point {
  x: number;
  y: number;
}

export interface Box {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  w: number;
  h: number;
}

/** A text line's box at a point (the caret's line), or null where no text is. */
export interface LineBox {
  top: number;
  bottom: number;
  height: number;
}

export interface RecognizerPage {
  /** The text column's left and right edges (client coordinates), or null when the window shows no text. */
  textColumn(): { left: number; right: number } | null;
  /** The text line at a point (client coordinates). */
  lineAt(x: number, y: number): LineBox | null;
}

export type StrokeKind = "lasso" | "bracket" | "note" | "strike" | "underline" | "ink";

export interface Recognition {
  kind: StrokeKind;
  box: Box;
  /** For a strike or an underline: the y (client) of the text line the mark goes on. */
  lineY?: number;
}

export const RECOGNIZER = {
  /** A stroke needs more points than this to be recognized. */
  minPoints: 3,
  loop: { endsWithin: 30, minWidth: 30, minHeight: 16 },
  bracket: { minHeight: 40, maxWidth: 26 },
  flat: { maxHeight: 22, minWidth: 40 },
  /** The text line probed this far above a flat stroke's middle. */
  lineProbeAbove: 9,
  /** An underline's text line sits this far above the stroke's middle. */
  underlineAbove: 10,
  /** Through the middle: between these fractions of the line's height from its top and its bottom. */
  strikeFromTop: 0.3,
  strikeFromBottom: 0.25,
  marginBeyond: 4,
  columnMinWidth: 100,
} as const;

export function boxOf(points: readonly Point[]): Box {
  const xs = points.map((p) => p.x);
  const ys = points.map((p) => p.y);
  const x0 = Math.min(...xs);
  const x1 = Math.max(...xs);
  const y0 = Math.min(...ys);
  const y1 = Math.max(...ys);
  return { x0, y0, x1, y1, w: x1 - x0, h: y1 - y0 };
}

export function isClosedLoop(points: readonly Point[], box: Box = boxOf(points)): boolean {
  const first = points[0];
  const last = points[points.length - 1];
  const { endsWithin, minWidth, minHeight } = RECOGNIZER.loop;
  return Math.hypot(first.x - last.x, first.y - last.y) < endsWithin && box.w > minWidth && box.h > minHeight;
}

export function inMargin(box: Box, column: { left: number; right: number } | null): boolean {
  if (!column) return false;
  return box.x0 > column.right + RECOGNIZER.marginBeyond || box.x1 < column.left - RECOGNIZER.marginBeyond;
}

/** Whether a flat stroke runs through the middle of the text line it sits on (else it is under one). */
export function throughTheMiddle(box: Box, page: RecognizerPage): boolean {
  const mid = (box.y0 + box.y1) / 2;
  const cx = box.x0 + box.w / 2;
  const above = page.lineAt(cx, mid - RECOGNIZER.lineProbeAbove);
  if (!above || !above.height) return false;
  if (!(mid > above.top + above.height * RECOGNIZER.strikeFromTop && mid < above.bottom - above.height * RECOGNIZER.strikeFromBottom)) return false;
  const at = page.lineAt(cx, mid);
  return !!at && at.top === above.top;
}

export function recognize(points: readonly Point[], page: RecognizerPage): Recognition | null {
  if (points.length <= RECOGNIZER.minPoints) return null;
  const box = boxOf(points);
  if (isClosedLoop(points, box)) return { kind: "lasso", box };
  const margin = inMargin(box, page.textColumn());
  if (box.h > RECOGNIZER.bracket.minHeight && box.w < RECOGNIZER.bracket.maxWidth && margin) return { kind: "bracket", box };
  if (margin) return { kind: "note", box };
  if (box.h < RECOGNIZER.flat.maxHeight && box.w > RECOGNIZER.flat.minWidth) {
    const mid = (box.y0 + box.y1) / 2;
    if (throughTheMiddle(box, page)) return { kind: "strike", box, lineY: mid };
    return { kind: "underline", box, lineY: mid - RECOGNIZER.underlineAbove };
  }
  return { kind: "ink", box };
}

/** What each recognition becomes, as its chip says it ("X → Y"). */
export const RECOGNIZED_AS: Record<Exclude<StrokeKind, "ink">, string> = {
  lasso: "circle → selection",
  bracket: "bracket → paragraph highlighted",
  note: "margin → handwritten note",
  strike: "strike → “I disagree / doesn't make sense” · the tutor can pick it up",
  underline: "underline → highlight",
};
