// The sticky-tab stack's geometry (spec §10.1): tabs pile above and wait below, the active pad, the merge
// amount over 56 px, the three width grades and the landing point of a jump.
import { describe, expect, it } from "vitest";
import { activePad, fractionalOpen, mergeAmount, paperMinHeight, scrollTargetFor, stuckTop, tabMargin, type PadGeometry } from "./stickyTabs";

// Three pads in a 600 px scroller: each tab 30 px, each paper at least 600 − 90 = 510 px.
const viewport = 600;
const pads: PadGeometry[] = [0, 1, 2].map((i) => ({ tabTop: i * 540, paperTop: i * 540 + 30, paperBottom: i * 540 + 540 }));
const height = 3 * 540;

describe("sticky tabs", () => {
  it("each tab sticks between the pile above (i·30) and the pile below ((n−1−i)·30 from the bottom)", () => {
    expect(stuckTop(0, 3, -200, viewport)).toBe(0);
    expect(stuckTop(2, 3, 900, viewport)).toBe(viewport - 30);
    expect(stuckTop(1, 3, 250, viewport)).toBe(250);
    expect(paperMinHeight(viewport, 3)).toBe(510);
  });

  it("the active pad crosses the upper third; at the end it is the last", () => {
    expect(activePad(pads, 0, viewport, height)).toBe(0);
    expect(activePad(pads, 500, viewport, height)).toBe(1);
    expect(activePad(pads, height - viewport, viewport, height)).toBe(2);
  });

  it("the open tab merges fully with its paper; a tab waiting below shows none of its paper", () => {
    expect(mergeAmount(0, pads, 0, viewport)).toBe(1);
    expect(mergeAmount(2, pads, 0, viewport)).toBe(0);
    // Scrolled 28 px: pad 1's tab rises off the pile below and 28 px of its paper shows under it.
    expect(mergeAmount(1, pads, 28, viewport)).toBeCloseTo(0.5);
  });

  it("the three grades: flat none, order 9 px an index, distance 14 + 9 px a unit capped at four", () => {
    expect(tabMargin("flat", 3, 0)).toBe(0);
    expect(tabMargin("order", 3, 0)).toBe(27);
    expect(tabMargin("distance", 0, 0)).toBe(14);
    expect(tabMargin("distance", 2, 0.5)).toBe(14 + 9 * 1.5);
    expect(tabMargin("distance", 9, 0)).toBe(14 + 9 * 4);
  });

  it("the fractional open pad moves smoothly from one pad to the next", () => {
    const a = fractionalOpen(pads, 100, viewport, height);
    const b = fractionalOpen(pads, 300, viewport, height);
    expect(a).toBeGreaterThan(0);
    expect(b).toBeGreaterThan(a);
    expect(b).toBeLessThan(2);
  });

  it("a jump lands the pad's tab just below the pile above it", () => {
    expect(scrollTargetFor(2, pads)).toBe(2 * 540 - 60);
  });
});
