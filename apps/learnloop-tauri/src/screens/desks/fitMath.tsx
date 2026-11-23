// Display math that is never clipped (spec §13.4, an owner rule): room above and below inside the equation's
// own box, no clipping box between it and the window's scroller, and a wide equation fitted to its column
// (scaled down to at least 0.75) or, below that, given a horizontal scroller with a visible bar that keeps
// its full height. Measured after KaTeX renders and after the web fonts load, and again on resize.
import { useLayoutEffect, useRef, type ReactNode } from "react";

/** The least scale a wide equation is fitted to before it scrolls instead (§13.4 rule 2). */
export const MIN_MATH_SCALE = 0.75;

/** Fit every display equation inside `root` to its column. Returns how each one was handled (for tests). */
export function fitDisplayMath(root: HTMLElement): Array<"fits" | "scaled" | "scrolls"> {
  const out: Array<"fits" | "scaled" | "scrolls"> = [];
  for (const display of root.querySelectorAll<HTMLElement>(".katex-display")) {
    const math = display.querySelector<HTMLElement>(":scope > .katex");
    if (!math) continue;
    // Measure at the natural size.
    math.style.fontSize = "";
    display.classList.remove("desk-math-scroll");
    const column = display.clientWidth;
    const natural = math.scrollWidth;
    if (!column || natural <= column + 0.5) {
      out.push("fits");
      continue;
    }
    const scale = column / natural;
    if (scale >= MIN_MATH_SCALE) {
      // KaTeX sizes everything in em from `.katex`'s font size (1.21em by default): scaling it scales the
      // whole equation and its line box, so the height follows (a transform would leave the old height).
      math.style.fontSize = `${(1.21 * scale).toFixed(4)}em`;
      out.push("scaled");
    } else {
      display.classList.add("desk-math-scroll");
      out.push("scrolls");
    }
  }
  return out;
}

/** A container whose display math is fitted: on render, when the web fonts are ready and on resize. */
export function FitMath({ children, className, as: Tag = "div" }: { children: ReactNode; className?: string; as?: "div" | "span" }) {
  const ref = useRef<HTMLElement | null>(null);
  useLayoutEffect(() => {
    const node = ref.current;
    if (!node) return;
    let live = true;
    const fit = () => {
      if (live && ref.current) fitDisplayMath(ref.current);
    };
    fit();
    const fonts = typeof document !== "undefined" ? (document as Document & { fonts?: { ready?: Promise<unknown> } }).fonts : undefined;
    void fonts?.ready?.then(fit);
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(fit);
    observer?.observe(node);
    // KaTeX output can land after this render (a lazy MarkdownMath): watch for it.
    const mutations = typeof MutationObserver === "undefined" ? null : new MutationObserver(fit);
    mutations?.observe(node, { childList: true, subtree: true });
    return () => {
      live = false;
      observer?.disconnect();
      mutations?.disconnect();
    };
  });
  return <Tag ref={ref as never} className={`desk-math${className ? ` ${className}` : ""}`}>{children}</Tag>;
}
