// Bring an element into view by scrolling only the boxes the learner can
// scroll themselves (overflow auto or scroll), never the page.
//
// The native `scrollIntoView` scrolls every scrolling box between the element
// and the window, and a box with `overflow: hidden` is one: the shell's frame,
// `#root`, `body`. A Reader pane asking for its own passage therefore moved
// the whole application up, the top bar and the place tabs left the window,
// and nothing the learner could do (wheel, Escape) scrolled a hidden box back.

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

/** Where `scrollTop` should go so the element sits as `block` asks inside
 *  `container`. `top` and `height` are the element's box in the viewport. */
function targetScrollTop(container: HTMLElement, top: number, height: number, block: ScrollBlock, marginTop: number): number {
  const box = container.getBoundingClientRect();
  const view = container.clientHeight;
  const offset = container.scrollTop + (top - box.top - container.clientTop);
  switch (block) {
    case "start":
      return offset - marginTop;
    case "end":
      return offset + height - view;
    case "center":
      return offset + height / 2 - view / 2;
    case "nearest": {
      const visibleTop = container.scrollTop;
      const visibleBottom = visibleTop + view;
      if (offset - marginTop < visibleTop || height > view) return offset - marginTop;
      if (offset + height > visibleBottom) return offset + height - view;
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
    const next = clampScrollTop(node, targetScrollTop(node, rect.top - shift, rect.height, block, marginTop));
    if (Math.abs(next - current) < 0.5) continue;
    if (typeof node.scrollTo === "function") node.scrollTo({ top: next, behavior });
    else node.scrollTop = next;
    shift += next - current;
  }
}
