// Reading-view geometry (spec §4.3, §5.2): uniform slots, the camera that keeps the focus in view, the
// slivers, the soft crop, focus mode's full screen, and the document zoom's range.
import { describe, expect, it } from "vitest";
import {
  DESK_SIZES,
  ensureVisible,
  focusRect,
  paneRects,
  rowTop,
  sliverSlots,
  slotRects,
  slotVisibility,
  slotWidth,
  slotsInView,
  softCropMask,
  stageFor,
  stepZoom,
  stripWidth,
} from "./geometry";

const stage = { width: 1364, height: 896 };

describe("slots", () => {
  it("two uniform slots and their gap fill the stage inside the side margins", () => {
    const w = slotWidth(stage);
    expect(2 * w + DESK_SIZES.gap + 2 * DESK_SIZES.side).toBe(stage.width);
    const rects = slotRects(3, stage);
    expect(rects[0]).toEqual({ x: 34, y: 8, w, h: stage.height - 16 });
    expect(rects[1].x - (rects[0].x + rects[0].w)).toBe(DESK_SIZES.gap);
    expect(stripWidth(3, stage)).toBe(rects[2].x + rects[2].w + DESK_SIZES.side);
  });

  it("every window fills its slot's full height; a pair splits it top and bottom with a 6 px divider", () => {
    const [slot] = slotRects(1, stage);
    expect(slot.h).toBe(stage.height - 2 * DESK_SIZES.inset);
    const [top, bottom] = paneRects(slot, 2);
    expect(top.h).toBe(bottom.h);
    expect(top.h + bottom.h + DESK_SIZES.pairDivider).toBe(slot.h);
    expect(bottom.y).toBe(top.y + top.h + DESK_SIZES.pairDivider);
    expect(paneRects(slot, 1)).toEqual([slot]);
  });

  it("desk rows stack like workspaces", () => {
    expect(rowTop(0, stage)).toBe(0);
    expect(rowTop(2, stage)).toBe(2 * (stage.height + DESK_SIZES.rowGap));
  });
});

describe("the camera", () => {
  it("moves only as far as it must to bring the focus in view, and never past the strip's ends", () => {
    expect(ensureVisible(0, 0, 5, stage)).toBe(0);
    expect(ensureVisible(0, 1, 5, stage)).toBe(0);
    const third = ensureVisible(0, 2, 5, stage);
    expect(slotsInView(third, 5, stage)).toEqual([1, 2]);
    // Back to the first: the camera returns to 0, not past it.
    expect(ensureVisible(third, 0, 5, stage)).toBe(0);
    // The last slot: the camera stops at the strip's end.
    const last = ensureVisible(0, 4, 5, stage);
    expect(last).toBe(stripWidth(5, stage) - stage.width);
  });

  it("opening beside keeps the previous focus in view", () => {
    const cam = ensureVisible(0, 3, 5, stage, true);
    expect(slotsInView(cam, 5, stage)).toEqual([2, 3]);
  });
});

describe("slivers and soft crop", () => {
  it("the off-screen neighbours each side are the slivers", () => {
    expect(sliverSlots(0, 1, stage)).toEqual({ left: null, right: null });
    expect(sliverSlots(0, 4, stage)).toEqual({ left: null, right: 2 });
    const cam = ensureVisible(0, 2, 4, stage);
    expect(sliverSlots(cam, 4, stage)).toEqual({ left: 0, right: 3 });
  });

  it("a window cut by the stage edge fades over its last 36 px to 55 %; one fully shown has no mask", () => {
    const [shown] = slotVisibility(0, 3, stage);
    expect(softCropMask(shown, slotWidth(stage))).toBeNull();
    const cut = slotVisibility(200, 3, stage)[0];
    expect(cut.cutLeft).toBe(200 - 34);
    const mask = softCropMask(cut, slotWidth(stage))!;
    expect(mask).toContain("rgba(0,0,0,0.55) 166px");
    expect(mask).toContain("#000 202px");
  });
});

describe("focus mode", () => {
  it("is the whole viewport, and the document zoom runs 0.6 to 2.2 in steps of 0.1", () => {
    expect(focusRect({ width: 1600, height: 960 })).toEqual({ x: 0, y: 0, w: 1600, h: 960 });
    expect(stepZoom(1, 1)).toBe(1.1);
    expect(stepZoom(2.2, 1)).toBe(2.2);
    expect(stepZoom(0.6, -1)).toBe(0.6);
    expect(stepZoom(1.7, 0)).toBe(1);
  });

  it("the stage leaves the top bar, the footer and the shelf (its rail below 1400 px)", () => {
    expect(stageFor({ width: 1600, height: 960 })).toEqual({ width: 1600 - 236, height: 960 - 38 - 26 });
    expect(stageFor({ width: 1280, height: 800 })).toEqual({ width: 1280 - 44, height: 800 - 64 });
  });
});
