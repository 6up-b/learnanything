// The page side of pen marks on a source (spec §10.10): the probes the recognizer reads, and the ranges and boxes
// a recognized stroke marks. Reads the DOM's layout (caret ranges and client rects), so it runs in the real
// webview; the rules it feeds are in `recognizer.ts`.
import type { Box, LineBox, Point, RecognizerPage } from "./recognizer";
import { RECOGNIZER } from "./recognizer";

export const PASSAGE = "[data-span-id]";

export interface LocalRect {
  x: number;
  y: number;
  w: number;
  h: number;
}

type CaretDoc = Document & {
  caretRangeFromPoint?: (x: number, y: number) => Range | null;
  caretPositionFromPoint?: (x: number, y: number) => { offsetNode: Node; offset: number } | null;
};

/** A collapsed range at a point, inside `host`, or null. */
export function caretAt(host: HTMLElement, x: number, y: number, doc: Document = host.ownerDocument): Range | null {
  const caretDoc = doc as CaretDoc;
  let range: Range | null = null;
  if (caretDoc.caretRangeFromPoint) {
    range = caretDoc.caretRangeFromPoint(x, y);
  } else if (caretDoc.caretPositionFromPoint) {
    const position = caretDoc.caretPositionFromPoint(x, y);
    if (position) {
      range = doc.createRange();
      range.setStart(position.offsetNode, position.offset);
    }
  }
  if (!range || !host.contains(range.startContainer)) return null;
  const passage = (range.startContainer instanceof Element ? range.startContainer : range.startContainer.parentElement)?.closest(PASSAGE);
  return passage && host.contains(passage) ? range : null;
}

function caretLine(range: Range): LineBox | null {
  const rect = range.getClientRects?.()[0] ?? range.getBoundingClientRect?.();
  if (!rect || !rect.height) return null;
  return { top: rect.top, bottom: rect.bottom, height: rect.height };
}

export function passages(host: HTMLElement): HTMLElement[] {
  return Array.from(host.querySelectorAll<HTMLElement>(PASSAGE));
}

export function pageOf(host: HTMLElement): RecognizerPage {
  return {
    textColumn: () => {
      const column = passages(host).map((element) => element.getBoundingClientRect()).find((rect) => rect.width > RECOGNIZER.columnMinWidth);
      return column ? { left: column.left, right: column.right } : null;
    },
    lineAt: (x, y) => {
      const range = caretAt(host, x, y);
      return range ? caretLine(range) : null;
    },
  };
}

/** The text between two points on one line (an underline's or a strike's words), or null. */
export function rangeBetween(host: HTMLElement, a: Point, b: Point): Range | null {
  const start = caretAt(host, a.x, a.y);
  const end = caretAt(host, b.x, b.y);
  if (!start || !end) return null;
  const range = host.ownerDocument.createRange();
  try {
    range.setStart(start.startContainer, start.startOffset);
    range.setEnd(end.startContainer, end.startOffset);
  } catch {
    return null;
  }
  return range.collapsed ? null : range;
}

export function inPolygon(x: number, y: number, polygon: readonly Point[]): boolean {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const a = polygon[i];
    const b = polygon[j];
    if ((a.y > y) !== (b.y > y) && x < ((b.x - a.x) * (y - a.y)) / (b.y - a.y) + a.x) inside = !inside;
  }
  return inside;
}

/** The words whose centres lie inside a closed loop, as one range from the first to the last, or null. */
export function wordsInLoop(host: HTMLElement, loop: readonly Point[]): Range | null {
  let first: [Node, number] | null = null;
  let last: [Node, number] | null = null;
  const doc = host.ownerDocument;
  for (const passage of passages(host)) {
    const walker = doc.createTreeWalker(passage, NodeFilter.SHOW_TEXT);
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      const text = (node as Text).data;
      for (const match of text.matchAll(/\S+/g)) {
        const at = match.index ?? 0;
        const word = doc.createRange();
        word.setStart(node, at);
        word.setEnd(node, at + match[0].length);
        const rect = word.getBoundingClientRect();
        if (rect.width && inPolygon(rect.left + rect.width / 2, rect.top + rect.height / 2, loop)) {
          if (!first) first = [node, at];
          last = [node, at + match[0].length];
        }
      }
    }
  }
  if (!first || !last) return null;
  const range = doc.createRange();
  range.setStart(first[0], first[1]);
  range.setEnd(last[0], last[1]);
  return range;
}

/** The passages a bracket spans: those overlapping the stroke by more than 6 px at each end (the mockup's rule). */
export function passagesSpanned(host: HTMLElement, box: Box): HTMLElement[] {
  return passages(host).filter((element) => {
    const rect = element.getBoundingClientRect();
    return rect.bottom > box.y0 + 6 && rect.top < box.y1 - 6;
  });
}

/** The passage a margin note sits beside: one it overlaps vertically, else the nearest. */
export function passageBeside(host: HTMLElement, box: Box): HTMLElement | null {
  const all = passages(host).filter((element) => element.getBoundingClientRect().height > 0);
  const overlapping = all.find((element) => {
    const rect = element.getBoundingClientRect();
    return rect.bottom > box.y0 && rect.top < box.y1;
  });
  if (overlapping) return overlapping;
  const middle = (box.y0 + box.y1) / 2;
  let best: HTMLElement | null = null;
  let distance = Infinity;
  for (const element of all) {
    const rect = element.getBoundingClientRect();
    const d = middle < rect.top ? rect.top - middle : middle > rect.bottom ? middle - rect.bottom : 0;
    if (d < distance) {
      distance = d;
      best = element;
    }
  }
  return best;
}

/** Client coordinates to the host's own (the ink layer's: they scroll with the text). */
export function toLocal(host: HTMLElement, x: number, y: number): Point {
  const rect = host.getBoundingClientRect();
  return { x: x - rect.left + host.scrollLeft, y: y - rect.top + host.scrollTop };
}

export function toClient(host: HTMLElement, x: number, y: number): Point {
  const rect = host.getBoundingClientRect();
  return { x: x + rect.left - host.scrollLeft, y: y + rect.top - host.scrollTop };
}

export function localRects(host: HTMLElement, rects: Iterable<DOMRect>): LocalRect[] {
  const out: LocalRect[] = [];
  for (const rect of rects) {
    if (!rect.width || !rect.height) continue;
    const at = toLocal(host, rect.left, rect.top);
    out.push({ x: at.x, y: at.y, w: rect.width, h: rect.height });
  }
  return out;
}

/** The distance from a point to a polyline. */
export function distanceToPolyline(p: Point, line: readonly Point[]): number {
  if (line.length === 1) return Math.hypot(p.x - line[0].x, p.y - line[0].y);
  let best = Infinity;
  for (let i = 1; i < line.length; i += 1) {
    const a = line[i - 1];
    const b = line[i];
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const length = dx * dx + dy * dy;
    const t = length ? Math.max(0, Math.min(1, ((p.x - a.x) * dx + (p.y - a.y) * dy) / length)) : 0;
    best = Math.min(best, Math.hypot(p.x - (a.x + t * dx), p.y - (a.y + t * dy)));
  }
  return best;
}
