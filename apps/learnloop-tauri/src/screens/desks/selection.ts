// What the learner has selected in a desk window (spec §8.3, §8.6): the passages it touches, its text and
// where it shows on the stage, read from the DOM selection. The companion anchors at it and asks about it;
// the avoid rule keeps it uncovered.
import type { Rect } from "./geometry";
import { selectionQuote } from "../../render/mathSnippet";
import { WINDOW_ATTRIBUTE } from "./keys/listeners";

export interface WindowSelection {
  windowId: string;
  spanIds: string[];
  quote: string;
  /** The selection's line boxes in stage coordinates. */
  rects: Rect[];
  /** Their union. */
  bounds: Rect;
}

const SPAN_SELECTOR = "[data-span-id], [data-transcript-span]";

function spanOf(element: Element): string | null {
  return element.getAttribute("data-span-id") ?? element.getAttribute("data-transcript-span");
}

/** The selection's text as the learner reads it: rendered math by its TeX source, through the Reader's own
 * `selectionQuote` (a formula the selection starts or ends inside is taken whole, a displayed one keeps its
 * display delimiters; KaTeX's drawn and MathML copies would otherwise repeat or flatten every symbol). */
export function quoteOf(range: Range): string {
  return selectionQuote(range, range.toString()).replace(/\s+/g, " ").trim();
}

/** A quote cut to `max` characters, never inside a formula: a cut that would fall inside one ends before it. */
export function clipQuote(quote: string, max: number): string {
  if (quote.length <= max) return quote;
  let cut = max;
  // Each formula's span, $$…$$ tried before $…$: a cut inside one moves to the formula's start.
  for (const match of quote.matchAll(/\$\$[\s\S]+?\$\$|\$[^$]+?\$/g)) {
    const start = match.index ?? 0;
    const end = start + match[0].length;
    if (start < cut && end > cut) {
      cut = start;
      break;
    }
  }
  return quote.slice(0, cut).trimEnd();
}

/** The current DOM selection inside the window `windowId`, or null when there is none there. */
export function readWindowSelection(windowId: string, stage: Element | null, doc: Document = document): WindowSelection | null {
  const selection = doc.getSelection?.();
  if (!selection || selection.isCollapsed || selection.rangeCount === 0) return null;
  const range = selection.getRangeAt(0);
  const host = doc.querySelector(`[${WINDOW_ATTRIBUTE}="${windowId}"]`);
  if (!host || !host.contains(range.commonAncestorContainer)) return null;
  const quote = quoteOf(range);
  if (!quote) return null;
  const spanIds: string[] = [];
  const start = range.startContainer instanceof Element ? range.startContainer : range.startContainer.parentElement;
  const first = start?.closest(SPAN_SELECTOR);
  if (first) {
    const id = spanOf(first);
    if (id) spanIds.push(id);
  }
  for (const element of host.querySelectorAll(SPAN_SELECTOR)) {
    const id = spanOf(element);
    if (id && !spanIds.includes(id) && range.intersectsNode(element)) spanIds.push(id);
  }
  const origin = stage?.getBoundingClientRect() ?? { left: 0, top: 0 };
  const rects = [...(range.getClientRects?.() ?? [])]
    .filter((rect) => rect.width > 0 && rect.height > 0)
    .map((rect) => ({ x: rect.left - origin.left, y: rect.top - origin.top, w: rect.width, h: rect.height }));
  const box = range.getBoundingClientRect?.();
  const bounds = box && box.width + box.height > 0
    ? { x: box.left - origin.left, y: box.top - origin.top, w: box.width, h: box.height }
    : rects[0] ?? { x: 0, y: 0, w: 0, h: 0 };
  return { windowId, spanIds, quote, rects: rects.length ? rects : [bounds], bounds };
}
