// What the learner has selected in a desk window (spec §8.3, §8.6): the passages it touches, its text and
// where it shows on the stage, read from the DOM selection. The companion anchors at it and asks about it;
// the avoid rule keeps it uncovered.
import type { Rect } from "./geometry";
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

/** The current DOM selection inside the window `windowId`, or null when there is none there. */
export function readWindowSelection(windowId: string, stage: Element | null, doc: Document = document): WindowSelection | null {
  const selection = doc.getSelection?.();
  if (!selection || selection.isCollapsed || selection.rangeCount === 0) return null;
  const range = selection.getRangeAt(0);
  const host = doc.querySelector(`[${WINDOW_ATTRIBUTE}="${windowId}"]`);
  if (!host || !host.contains(range.commonAncestorContainer)) return null;
  const quote = selection.toString().replace(/\s+/g, " ").trim();
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
