// Live miniatures (spec §6.1): a card's picture of its window, a static clone of what the window shows,
// built when idle and rebuilt only once the window has changed. A clone carries no listeners, no timers
// and no player: it can log no reading activity (§3.6), and an iframe becomes a placeholder.

/** Clone `source` (a window's content) for a card: no ids, no window marks, no frames, nothing focusable,
 * inert. Scrolled parts keep their scroll once the clone is in the page (`restoreScroll`). */
export function cloneForMiniature(source: HTMLElement): { node: HTMLElement; restoreScroll: () => void } {
  const scrolls: Array<{ path: number[]; top: number; left: number }> = [];
  const walk = (element: Element, path: number[]) => {
    if (element instanceof HTMLElement && (element.scrollTop > 0 || element.scrollLeft > 0)) {
      scrolls.push({ path, top: element.scrollTop, left: element.scrollLeft });
    }
    Array.from(element.children).forEach((child, index) => walk(child, [...path, index]));
  };
  walk(source, []);
  const node = source.cloneNode(true) as HTMLElement;
  node.removeAttribute("id");
  // A clone marked as a window would take its clicks for that window (the listener router reads the mark).
  node.removeAttribute("data-desk-window");
  for (const element of Array.from(node.querySelectorAll("[id]"))) element.removeAttribute("id");
  for (const element of Array.from(node.querySelectorAll("[data-desk-window]"))) element.removeAttribute("data-desk-window");
  for (const frame of Array.from(node.querySelectorAll("iframe, video, audio, canvas, object, embed"))) {
    const placeholder = document.createElement("div");
    placeholder.className = "desk-mini-frame";
    placeholder.textContent = frame.tagName === "IFRAME" || frame.tagName === "VIDEO" ? "▶" : "";
    const box = (frame as HTMLElement).getBoundingClientRect?.();
    if (box && box.height > 0) placeholder.style.height = `${box.height}px`;
    frame.replaceWith(placeholder);
  }
  for (const element of Array.from(node.querySelectorAll("input, textarea, select, button, a[href], [tabindex], [contenteditable]"))) {
    element.setAttribute("tabindex", "-1");
    element.removeAttribute("contenteditable");
  }
  node.setAttribute("inert", "");
  node.setAttribute("aria-hidden", "true");
  const restoreScroll = () => {
    for (const { path, top, left } of scrolls) {
      let element: Element | undefined = node;
      for (const index of path) element = element?.children[index];
      if (element instanceof HTMLElement) {
        element.scrollTop = top;
        element.scrollLeft = left;
      }
    }
  };
  return { node, restoreScroll };
}

/** Which windows' miniatures are stale: a window is marked when it changes and cleared when its
 * miniature is rebuilt. */
export class MiniatureBook {
  private built = new Map<string, HTMLElement>();
  private dirty = new Set<string>();

  invalidate(windowId: string): void {
    this.dirty.add(windowId);
  }

  needs(windowId: string): boolean {
    return !this.built.has(windowId) || this.dirty.has(windowId);
  }

  store(windowId: string, node: HTMLElement): void {
    this.built.set(windowId, node);
    this.dirty.delete(windowId);
  }

  get(windowId: string): HTMLElement | null {
    return this.built.get(windowId) ?? null;
  }

  forget(windowId: string): void {
    this.built.delete(windowId);
    this.dirty.delete(windowId);
  }
}
