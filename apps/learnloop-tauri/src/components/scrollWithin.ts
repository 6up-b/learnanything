// Bring an element into view by scrolling only the boxes the learner can
// scroll themselves (overflow auto or scroll), never the page.
//
// The native `scrollIntoView` scrolls every scrolling box between the element
// and the window, and a box with `overflow: hidden` is one: the shell's frame,
// `#root`, `body`. A Reader pane asking for its own passage therefore moved
// the whole application up, the top bar and the place tabs left the window,
// and nothing the learner could do (wheel, Escape) scrolled a hidden box back.
//
// A scroller's own sticky bars (the Reader rail's tabs) are kept clear: the
// element lands beside them, never under them.

export type ScrollBlock = "start" | "center" | "end" | "nearest";

export interface ScrollWithinOptions {
  block?: ScrollBlock;
  behavior?: ScrollBehavior;
}

const USER_SCROLLABLE = /^(auto|scroll|overlay)$/;

function isUserScrollable(element: Element): boolean {
  const view = element.ownerDocument.defaultView;
  if (!view) return false;
  return USER_SCROLLABLE.test(view.getComputedStyle(element).overflowY);
}

function pixels(value: string | null | undefined): number {
  const parsed = Number.parseFloat(value ?? "");
  return Number.isFinite(parsed) ? parsed : 0;
}

/** How far the scroller's own sticky children, once stuck, cover its view
 *  from the top and from the bottom (the Reader rail's tab bar). A target put
 *  at the scroller's edge sits under them, and the first click on it lands on
 *  the bar instead. A sticky child that holds the target covers nothing of it. */
function stickyCover(container: HTMLElement, target: Element): { top: number; bottom: number } {
  const view = container.ownerDocument.defaultView;
  if (!view) return { top: 0, bottom: 0 };
  const own = view.getComputedStyle(container);
  let top = 0;
  let bottom = 0;
  for (const child of Array.from(container.children)) {
    if (child.contains(target)) continue;
    const style = view.getComputedStyle(child);
    if (style.position !== "sticky") continue;
    const height = child.getBoundingClientRect().height;
    // A sticky offset is measured from inside the scroller's padding.
    if (style.top && style.top !== "auto") top = Math.max(top, pixels(own.paddingTop) + pixels(style.top) + height);
    else if (style.bottom && style.bottom !== "auto") bottom = Math.max(bottom, pixels(own.paddingBottom) + pixels(style.bottom) + height);
  }
  return { top: Math.max(0, top), bottom: Math.max(0, bottom) };
}

/** Where `scrollTop` should go so the element sits as `block` asks inside
 *  the part of `container` its sticky children leave clear. `top` and
 *  `height` are the element's box in the viewport. */
function targetScrollTop(container: HTMLElement, top: number, height: number, block: ScrollBlock, marginTop: number,
                         cover: { top: number; bottom: number }): number {
  const box = container.getBoundingClientRect();
  const view = container.clientHeight;
  const clear = Math.max(0, view - cover.top - cover.bottom);
  const offset = container.scrollTop + (top - box.top - container.clientTop);
  switch (block) {
    case "start":
      return offset - marginTop - cover.top;
    case "end":
      return offset + height - view + cover.bottom;
    case "center":
      return offset + height / 2 - cover.top - clear / 2;
    case "nearest": {
      const visibleTop = container.scrollTop + cover.top;
      const visibleBottom = container.scrollTop + view - cover.bottom;
      if (offset - marginTop < visibleTop || height > clear) return offset - marginTop - cover.top;
      if (offset + height > visibleBottom) return offset + height - view + cover.bottom;
      return container.scrollTop;
    }
  }
}

function clampScrollTop(container: HTMLElement, value: number): number {
  const max = container.scrollHeight - container.clientHeight;
  return Math.max(0, max > 0 ? Math.min(value, max) : value);
}

/** Scroll `target` into view inside its scrollable ancestors only. Boxes with
 *  hidden or clipped overflow, `body` and the document are never moved. */
export function scrollIntoViewWithin(target: Element | null | undefined, options: ScrollWithinOptions = {}): void {
  if (!target) return;
  const block = options.block ?? "start";
  const behavior = options.behavior ?? "auto";
  const doc = target.ownerDocument;
  const view = doc.defaultView;
  const marginTop = view ? pixels(view.getComputedStyle(target).scrollMarginTop) : 0;
  const rect = target.getBoundingClientRect();
  // What the inner boxes' moves will do to the element's place once they land
  // (a smooth move has not landed when the outer box is measured).
  let shift = 0;
  for (let node = target.parentElement; node && node !== doc.body && node !== doc.documentElement; node = node.parentElement) {
    if (!isUserScrollable(node)) continue;
    const current = node.scrollTop;
    const next = clampScrollTop(node, targetScrollTop(node, rect.top - shift, rect.height, block, marginTop, stickyCover(node, target)));
    if (Math.abs(next - current) < 0.5) continue;
    if (typeof node.scrollTo === "function") node.scrollTo({ top: next, behavior });
    else node.scrollTop = next;
    shift += next - current;
  }
}
