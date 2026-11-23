// The zoom engine's pure parts (spec §6.3, §18.2): the commit-identity invariant as exact geometry,
// log-scale interpolation, the fades, the chase and the spring, the release rule, the wheel's
// classification and end latch, and the overview's selection and drop rules.
import { describe, expect, it } from "vitest";
import { slotRects, slotWidth } from "../geometry";
import {
  IDENTITY,
  OVERVIEW,
  classifyWheel,
  dragProgress,
  dropTarget,
  enteringCamera,
  followSelection,
  frameAt,
  moveSelection,
  newZoomGesture,
  normalizedDelta,
  onStage,
  overviewLayout,
  release,
  settleNow,
  step,
  transformed,
  zoomWheel,
  type Motion,
  type ZoomItem,
} from "./engine";

const stage = { width: 1364, height: 896 };
const layout = overviewLayout([3, 2, 1], slotWidth(stage), stage);
const reading = slotRects(3, stage);

function items(base: 0 | 1): ZoomItem[] {
  return layout.cards[0].map((b, index) => {
    const a = reading[index];
    return { a, b, base: base === 0 ? a : b, live: index < 2, recede: index === 2 };
  });
}

function close(a: number, b: number, tolerance = 0.5) {
  expect(Math.abs(a - b), `${a} vs ${b}`).toBeLessThanOrEqual(tolerance);
}

describe("the overview's layout", () => {
  it("lays every desk out as a row of cards at least 760 wide, after the links' gutter", () => {
    expect(layout.cards.map((row) => row.length)).toEqual([3, 2, 1]);
    const [first, second] = layout.cards[0];
    expect(first.w).toBe(OVERVIEW.cardMin);
    expect(first.x).toBe(34 + OVERVIEW.gutter);
    expect(second.x - (first.x + first.w)).toBe(10);
    expect(first.h).toBe(stage.height * 0.75 - 16);
    expect(layout.cards[1][0].y - layout.cards[0][0].y).toBe(stage.height * 0.75 + OVERVIEW.rowGap);
    expect(layout.labels[1]).toEqual({ x: 34 + OVERVIEW.gutter, y: stage.height * 0.75 + OVERVIEW.rowGap - 14 });
  });

  it("enters with the selection at least 48 px inside the edges (74 from the top)", () => {
    const far = layout.cards[0][2];
    const camera = enteringCamera({ ...far, x: far.x + 4000 }, stage);
    const shown = onStage({ ...far, x: far.x + 4000 }, camera);
    expect(shown.x + shown.w).toBeLessThanOrEqual(stage.width - 48);
    const low = layout.cards[2][0];
    const down = onStage(low, followSelection(camera, low, stage));
    expect(down.y + down.h).toBeLessThanOrEqual(stage.height - 48);
    const up = onStage(layout.cards[0][0], followSelection({ x: 0, y: -900, s: OVERVIEW.scale }, layout.cards[0][0], stage));
    expect(up.y).toBeGreaterThanOrEqual(74);
  });
});

describe("the frame function", () => {
  const B = enteringCamera(layout.cards[0][0], stage);

  it("entering: the last frame is exactly the overview's layout (the commit changes no pixel)", () => {
    const frame = frameAt(1, IDENTITY, B, items(0));
    expect(frame.camera).toEqual(B);
    frame.items.forEach((item, index) => {
      const shown = transformed(items(0)[index].base, item);
      const committed = layout.cards[0][index];
      close(shown.x, committed.x);
      close(shown.y, committed.y);
      close(shown.w, committed.w);
      close(shown.h, committed.h);
      expect(item.cardOpacity).toBe(1);
      expect(item.contentOpacity).toBe(0);
    });
    expect(frame.items[2].opacity).toBeCloseTo(1 - 0.62, 10);
    expect(frame.lateOpacity).toBe(1);
    expect(frame.sliverOpacity).toBe(0);
  });

  it("leaving: the last frame is exactly the reading layout, under the identity camera", () => {
    const frame = frameAt(0, IDENTITY, B, items(1));
    expect(frame.camera).toEqual(IDENTITY);
    frame.items.forEach((item, index) => {
      const shown = transformed(items(1)[index].base, item);
      close(shown.x, reading[index].x);
      close(shown.y, reading[index].y);
      close(shown.w, reading[index].w);
      close(shown.h, reading[index].h);
    });
    expect(frame.items[0].contentOpacity).toBe(1);
    expect(frame.items[2].cardOpacity).toBe(1);
  });

  it("the first frame entering is the reading layout: nothing jumps when a zoom begins", () => {
    const frame = frameAt(0, IDENTITY, B, items(0));
    frame.items.forEach((item) => {
      expect(item.tx).toBe(0);
      expect(item.ty).toBe(0);
      expect(item.sx).toBe(1);
      expect(item.sy).toBe(1);
    });
  });

  it("interpolates the camera's scale in log space and the rest by the scale's linear fraction q", () => {
    const half = frameAt(0.5, IDENTITY, B, items(0));
    expect(half.camera.s).toBeCloseTo(Math.sqrt(OVERVIEW.scale), 10);
    const q = (1 - half.camera.s) / (1 - OVERVIEW.scale);
    expect(half.q).toBeCloseTo(q, 10);
    expect(half.camera.x).toBeCloseTo(B.x * q, 10);
  });

  it("counter-scales the content so text never stretches, and fades it over q ∈ [.45, .85]", () => {
    for (const p of [0.2, 0.5, 0.8]) {
      const frame = frameAt(p, IDENTITY, B, items(0));
      for (const item of frame.items) {
        expect(item.sx * item.innerSx).toBeCloseTo(1, 10);
        expect(item.sy * item.innerSy).toBeCloseTo(1, 10);
      }
    }
    const early = frameAt(0.01, IDENTITY, B, items(0));
    expect(early.items[0].contentOpacity).toBe(1);
    // An off-screen window shows only its card throughout.
    expect(early.items[2].contentOpacity).toBe(0);
    expect(early.items[2].cardOpacity).toBe(1);
    const mid = frameAt(0.6, IDENTITY, B, items(0));
    expect(mid.items[0].contentOpacity + mid.items[0].cardOpacity).toBeCloseTo(1, 10);
  });

  it("fades the links and labels over q ∈ [.6, 1], the slivers by 1 − 3q", () => {
    const frame = frameAt(0.3, IDENTITY, B, items(0));
    expect(frame.lateOpacity).toBe(Math.max(0, Math.min(1, (frame.q - 0.6) / 0.4)));
    expect(frame.sliverOpacity).toBeCloseTo(Math.max(0, 1 - 3 * frame.q), 10);
  });
});

describe("moving p", () => {
  const motion = (patch: Partial<Motion>): Motion => ({ p: 0, v: 0, target: 0, goal: null, ...patch });

  it("chases the fingers with τ = 40 ms: one frame closes 1 − e^(−dt/τ) of the gap", () => {
    const { motion: next } = step(motion({ target: 1 }), 1 / 60);
    expect(next.p).toBeCloseTo(1 - Math.exp(-(1 / 60) / 0.04), 10);
  });

  it("settles on the goal in about 300 ms with no overshoot (critically damped, ω = 26)", () => {
    let current = motion({ goal: 1 });
    let elapsed = 0;
    let arrived = false;
    let max = 0;
    while (!arrived && elapsed < 1) {
      const result = step(current, 1 / 60);
      current = result.motion;
      arrived = result.arrived;
      max = Math.max(max, current.p);
      elapsed += 1 / 60;
    }
    expect(arrived).toBe(true);
    expect(max).toBeLessThanOrEqual(1);
    expect(elapsed).toBeGreaterThan(0.15);
    expect(elapsed).toBeLessThan(0.45);
  });

  it("releases by where the fingers were heading: 40 % in, 60 % out", () => {
    expect(release(0, 0.39, 0)).toBe(0);
    expect(release(0, 0.4, 0)).toBe(1);
    expect(release(0, 0.3, 1)).toBe(1);
    expect(release(1, 0.61, 0)).toBe(1);
    expect(release(1, 0.6, 0)).toBe(0);
    expect(release(1, 0.7, -1)).toBe(0);
    expect(settleNow(0, motion({ p: 0.5, goal: null }))).toBe(1);
    expect(settleNow(1, motion({ p: 0.7, goal: 0 }))).toBe(0);
  });
});

describe("the wheel", () => {
  const wheel = (patch: Partial<Parameters<typeof classifyWheel>[0]>) => ({ deltaX: 0, deltaY: 0, deltaMode: 0, ctrlKey: false, altKey: false, shiftKey: false, ...patch });
  const none = { alt: false, ctrl: false };

  it("normalises lines to 40 px and pages to the stage's height", () => {
    expect(normalizedDelta({ deltaX: 0, deltaY: 3, deltaMode: 1 }, 900)).toEqual({ dx: 0, dy: 120 });
    expect(normalizedDelta({ deltaX: 1, deltaY: 0, deltaMode: 2 }, 900)).toEqual({ dx: 900, dy: 0 });
  });

  it("decides the gesture by its first event: alt sideways pans, alt up or down zooms, ctrl zooms, plain scrolls", () => {
    expect(classifyWheel(wheel({ altKey: true, deltaX: 30, deltaY: 4 }), none, 900).kind).toBe("pan");
    expect(classifyWheel(wheel({ shiftKey: true, deltaY: 30 }), none, 900).kind).toBe("pan");
    expect(classifyWheel(wheel({ altKey: true, deltaY: 6 }), none, 900)).toEqual({ kind: "zoom", source: "touch" });
    expect(classifyWheel(wheel({ altKey: true, deltaY: 100 }), none, 900)).toEqual({ kind: "zoom", source: "notch" });
    expect(classifyWheel(wheel({ altKey: true, deltaY: 1, deltaMode: 1 }), none, 900)).toEqual({ kind: "zoom", source: "notch" });
    // A touchpad pinch: ctrl+wheel without the Ctrl key held.
    expect(classifyWheel(wheel({ ctrlKey: true, deltaY: 3 }), none, 900)).toEqual({ kind: "zoom", source: "pinch" });
    expect(classifyWheel(wheel({ ctrlKey: true, deltaY: 3 }), { alt: false, ctrl: true }, 900)).toEqual({ kind: "zoom", source: "touch" });
    expect(classifyWheel(wheel({ deltaY: 30 }), none, 900).kind).toBe("scroll");
    // WebKitGTK reports altKey false on touchpad scrolls: the tracked Alt still counts.
    expect(classifyWheel(wheel({ deltaY: 6 }), { alt: true, ctrl: false }, 900).kind).toBe("zoom");
  });

  it("a touch stream moves the target by dy/420 and decides at an end, then latches the rest", () => {
    let gesture = newZoomGesture("touch", 0);
    let result = zoomWheel(gesture, 42, 10, { active: false, inOverview: false, target: 0 });
    expect(result.step).toEqual({ kind: "begin-and-target", target: 0.1, armMs: 80 });
    gesture = result.gesture;
    result = zoomWheel(gesture, 420, 20, { active: true, inOverview: false, target: 0.1 });
    expect(result.step).toEqual({ kind: "goal", goal: 1, armMs: 150 });
    gesture = result.gesture;
    // Momentum the same way is swallowed; the other way turns it round.
    expect(zoomWheel(gesture, 30, 30, { active: false, inOverview: true, target: 1 }).step.kind).toBe("swallow");
    const back = zoomWheel(gesture, -42, 40, { active: false, inOverview: true, target: 1 });
    expect(back.step).toEqual({ kind: "begin-and-target", target: 0.9, armMs: 80 });
  });

  it("a notch runs the whole eased zoom; a pinch moves by dy/108; at an end already, it latches", () => {
    expect(zoomWheel(newZoomGesture("notch", 0), 120, 1, { active: false, inOverview: false, target: 0 }).step).toEqual({ kind: "goal", goal: 1, armMs: 150 });
    expect(zoomWheel(newZoomGesture("pinch", 0), 10.8, 1, { active: false, inOverview: false, target: 0 }).step).toEqual({ kind: "begin-and-target", target: 0.1, armMs: 80 });
    expect(zoomWheel(newZoomGesture("touch", 0), -20, 1, { active: false, inOverview: false, target: 0 }).step.kind).toBe("swallow");
  });

  it("ctrl+drag: 320 px of travel is the whole zoom", () => {
    expect(dragProgress(0, 160)).toBe(0.5);
    expect(dragProgress(0, 900)).toBe(1);
    expect(dragProgress(1, -320)).toBe(0);
  });
});

describe("overview navigation", () => {
  it("h/l move within a desk, j/k to the next desk's card nearest by x-centre, the ends stay", () => {
    expect(moveSelection(layout, { row: 0, slot: 1 }, "right")).toEqual({ row: 0, slot: 2 });
    expect(moveSelection(layout, { row: 0, slot: 2 }, "right")).toEqual({ row: 0, slot: 2 });
    expect(moveSelection(layout, { row: 0, slot: 2 }, "down")).toEqual({ row: 1, slot: 1 });
    expect(moveSelection(layout, { row: 1, slot: 1 }, "down")).toEqual({ row: 2, slot: 0 });
    expect(moveSelection(layout, { row: 0, slot: 0 }, "up")).toEqual({ row: 0, slot: 0 });
  });

  it("a card dropped lands on the row under it, before the card whose centre is right of it", () => {
    const second = layout.cards[1][1];
    expect(dropTarget(layout, { x: second.x + 10, y: second.y + 50 })).toEqual({ row: 1, slot: 1 });
    expect(dropTarget(layout, { x: 99_999, y: layout.cards[0][0].y + 5 })).toEqual({ row: 0, slot: 3 });
    expect(dropTarget(layout, { x: 0, y: -9_999 })).toBeNull();
  });
});
