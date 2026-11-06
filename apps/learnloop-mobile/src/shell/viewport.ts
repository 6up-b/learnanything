// Keep the primary action above the keyboard (mobile v2 §4.3). iOS shrinks the visual viewport,
// not the layout one, when the keyboard opens; the gap between them is how far the sticky action
// area must rise. Measured on every resize and scroll of the visual viewport, never guessed.
import { useEffect } from "react";

export function keyboardInset(view: Pick<VisualViewport, "height" | "offsetTop">, layoutHeight: number): number {
  return Math.max(0, Math.round(layoutHeight - view.height - view.offsetTop));
}

export function useVisualViewportInset(root: HTMLElement = document.documentElement): void {
  useEffect(() => {
    const view = window.visualViewport;
    if (!view) return undefined;
    const update = () => root.style.setProperty("--keyboard-inset", `${keyboardInset(view, window.innerHeight)}px`);
    update();
    view.addEventListener("resize", update);
    view.addEventListener("scroll", update);
    return () => {
      view.removeEventListener("resize", update);
      view.removeEventListener("scroll", update);
      root.style.removeProperty("--keyboard-inset");
    };
  }, [root]);
}
