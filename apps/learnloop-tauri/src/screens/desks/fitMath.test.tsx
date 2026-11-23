// Display math is never clipped (spec §13.4, an owner rule): a wide equation is scaled to its column down to
// 0.75, below that it scrolls (with its full height) instead of shrinking further, and a narrow one is left.
// jsdom lays nothing out, so the widths are given; the real webview fixture measures the ink.
import { describe, expect, it } from "vitest";
import { MIN_MATH_SCALE, fitDisplayMath } from "./fitMath";

function display(column: number, natural: number): HTMLElement {
  const root = document.createElement("div");
  root.innerHTML = '<span class="katex-display"><span class="katex">x</span></span>';
  const box = root.querySelector(".katex-display") as HTMLElement;
  const math = root.querySelector(".katex") as HTMLElement;
  Object.defineProperty(box, "clientWidth", { value: column });
  Object.defineProperty(math, "scrollWidth", { value: natural });
  return root;
}

describe("fitting display math", () => {
  it("leaves an equation that fits", () => {
    const root = display(400, 300);
    expect(fitDisplayMath(root)).toEqual(["fits"]);
    expect((root.querySelector(".katex") as HTMLElement).style.fontSize).toBe("");
  });

  it("scales a wide one by the font size (so its height follows), never below 0.75", () => {
    const root = display(400, 500);
    expect(fitDisplayMath(root)).toEqual(["scaled"]);
    expect(parseFloat((root.querySelector(".katex") as HTMLElement).style.fontSize)).toBeCloseTo(1.21 * 0.8, 4);
    expect(MIN_MATH_SCALE).toBe(0.75);
  });

  it("gives one that would go below 0.75 a horizontal scroller instead, at full size", () => {
    const root = display(300, 500);
    expect(fitDisplayMath(root)).toEqual(["scrolls"]);
    expect(root.querySelector(".katex-display")?.classList.contains("desk-math-scroll")).toBe(true);
    expect((root.querySelector(".katex") as HTMLElement).style.fontSize).toBe("");
  });
});
