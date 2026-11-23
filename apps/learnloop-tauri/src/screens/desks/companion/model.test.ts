// The companion's geometry and state machine (spec §8.2, §8.3, §4.3).
import { describe, expect, it } from "vitest";
import { HIDDEN, anchoredRect, avoidOffset, companionStep, dockRect, nearestDock, pillRect, type CompanionState } from "./model";

const stage = { width: 1330, height: 896 };

describe("docks", () => {
  it("br, bl and cb are 400 wide and 52 % high, 14 px in; right is the stage's height", () => {
    expect(dockRect("br", stage)).toEqual({ x: 1330 - 400 - 14, y: 896 - 466 - 14, w: 400, h: 466 });
    expect(dockRect("bl", stage)).toEqual({ x: 14, y: 416, w: 400, h: 466 });
    expect(dockRect("cb", stage).x).toBe(465);
    const right = dockRect("right", stage);
    expect(right.w).toBeCloseTo(Math.min(420, 1330 * 0.34));
    expect(right.h).toBe(896 - 28);
  });

  it("a drop snaps to the nearest dock", () => {
    expect(nearestDock({ x: 100, y: 800 }, stage)).toBe("bl");
    expect(nearestDock({ x: 1300, y: 100 }, stage)).toBe("right");
    expect(nearestDock({ x: 660, y: 850 }, stage)).toBe("cb");
    expect(nearestDock({ x: 1150, y: 860 }, stage)).toBe("br");
  });

  it("the pill sits at the bottom right", () => {
    expect(pillRect(stage)).toEqual({ x: 1330 - 300 - 16, y: 896 - 38 - 14, w: 300, h: 38 });
  });
});

describe("anchored summon", () => {
  it("lands 10 px below the anchor when it fits, above when it does not, clamped to the stage", () => {
    const below = anchoredRect({ x: 300, y: 100, w: 200, h: 40 }, stage);
    expect(below).toEqual({ x: 300, y: 150, w: 400, h: 440 });
    const above = anchoredRect({ x: 1200, y: 700, w: 100, h: 20 }, stage);
    expect(above.y).toBe(700 - 10 - 440);
    expect(above.x).toBe(1330 - 400 - 8);
  });

  it("is 360 wide on a stage under 1240 px", () => {
    expect(anchoredRect({ x: 10, y: 10, w: 10, h: 10 }, { width: 1100, height: 700 }).w).toBe(360);
  });
});

describe("avoid", () => {
  const panel = { x: 900, y: 400, w: 400, h: 466 };
  it("slides the shorter way that clears what it covers, never more than 600 px", () => {
    expect(avoidOffset(panel, [{ x: 1000, y: 500, w: 100, h: 30 }], stage)).toBe(1000 - 12 - 1300);
    expect(avoidOffset(panel, [{ x: 200, y: 500, w: 100, h: 30 }], stage)).toBe(0);
  });
  it("does not slide off the stage or past its limit", () => {
    expect(avoidOffset(panel, [{ x: 100, y: 500, w: 1150, h: 30 }], stage)).toBe(0);
  });
});

describe("the state machine (§8.3)", () => {
  const anchor = { x: 300, y: 100, w: 200, h: 40 };
  it("c with nothing showing opens at the cursor; c again dissolves it in place, never via the dock", () => {
    const open = companionStep(HIDDEN, { kind: "c", anchor, stage });
    expect(open).toMatchObject({ mode: "anchored", origin: "cursor", last: "summon" });
    const gone = companionStep(open, { kind: "c", anchor, stage });
    expect(gone).toMatchObject({ mode: "hidden", last: "dissolve" });
  });

  it("summoned from the drawer, c sends it back to the drawer", () => {
    const docked = companionStep(HIDDEN, { kind: "dock" });
    expect(docked).toMatchObject({ mode: "docked", origin: "drawer", last: "show" });
    expect(companionStep(docked, { kind: "c", anchor, stage })).toMatchObject({ mode: "hidden", last: "hide" });
  });

  it("shift+c and the hand-off triggers move an anchored companion to its dock", () => {
    const open = companionStep(HIDDEN, { kind: "c", anchor, stage });
    expect(companionStep(open, { kind: "dock" })).toMatchObject({ mode: "docked", last: "hand-off" });
    expect(companionStep(open, { kind: "hand-off" })).toMatchObject({ mode: "docked", last: "hand-off" });
  });

  it("a hand-off leaves a docked or hidden companion where it is", () => {
    const docked: CompanionState = { mode: "docked", origin: "drawer", anchored: null, last: "show" };
    expect(companionStep(docked, { kind: "hand-off" })).toBe(docked);
    expect(companionStep(HIDDEN, { kind: "hand-off" })).toBe(HIDDEN);
  });
});
