import { describe, expect, it } from "vitest";
import { PenInput, type PointerLike } from "./input";

function ev(over: Partial<PointerLike> = {}): PointerLike {
  return { pointerId: 1, pointerType: "pen", button: 0, buttons: 1, clientX: 10, clientY: 20, pressure: 0.4, tiltX: 12, tiltY: -7, timeStamp: 1000, ...over };
}

describe("pen input (spec §10.10's input rules)", () => {
  it("a pen draws, and its first touch with pen mode off turns pen mode on and already draws", () => {
    const input = new PenInput();
    expect(input.down(ev(), false)).toEqual({ kind: "draw", turnOn: true });
    input.move(ev({ clientX: 14, clientY: 22, timeStamp: 1008, pressure: 0.6 }));
    const stroke = input.up(ev({ timeStamp: 1010 }));
    expect(stroke?.pointerType).toBe("pen");
    expect(stroke?.samples).toEqual([
      { x: 10, y: 20, t: 0, pressure: 0.4, tiltX: 12, tiltY: -7 },
      { x: 14, y: 22, t: 8, pressure: 0.6, tiltX: 12, tiltY: -7 },
    ]);
  });

  it("touch never draws (palm rejection), nor does a second pointer while a stroke is drawn", () => {
    const input = new PenInput();
    expect(input.down(ev({ pointerType: "touch" }), true)).toEqual({ kind: "pass" });
    input.down(ev(), true);
    expect(input.down(ev({ pointerId: 2, pointerType: "touch" }), true)).toEqual({ kind: "pass" });
    expect(input.down(ev({ pointerId: 3 }), true)).toEqual({ kind: "pass" });
    expect(input.move(ev({ pointerId: 2, clientX: 99 }))).toEqual([]);
    expect(input.up(ev({ pointerId: 2 }))).toBeNull();
    expect(input.up(ev())?.samples).toHaveLength(1);
  });

  it("the mouse draws only with simulate pen on and in pen mode, at the Pointer Events mouse pressure", () => {
    let simulate = false;
    const input = new PenInput(() => simulate);
    expect(input.down(ev({ pointerType: "mouse", pressure: 0 }), true)).toEqual({ kind: "pass" });
    simulate = true;
    expect(input.down(ev({ pointerType: "mouse", pressure: 0 }), false)).toEqual({ kind: "pass" });
    expect(input.down(ev({ pointerType: "mouse", pressure: 0, tiltX: undefined, tiltY: undefined }), true)).toEqual({ kind: "draw", turnOn: false });
    expect(input.up(ev({ pointerType: "mouse" }))?.samples[0]).toMatchObject({ pressure: 0.5, tiltX: 0, tiltY: 0 });
  });

  it("the barrel button (2 or 5) or the eraser end erases and keeps no stroke", () => {
    for (const over of [{ button: 2 }, { button: 5 }, { buttons: 32 }]) {
      const input = new PenInput();
      expect(input.down(ev(over), true).kind).toBe("erase");
      expect(input.erasing).toBe(true);
      expect(input.move(ev({ clientX: 30 }))).toHaveLength(1);
      expect(input.up(ev())).toBeNull();
    }
  });

  it("coalesced events are kept, values are clamped to the Pointer Events ranges, a cancel keeps nothing", () => {
    const input = new PenInput();
    input.down(ev(), true);
    const samples = input.move(ev({ getCoalescedEvents: () => [ev({ clientX: 11, timeStamp: 1002 }), ev({ clientX: 12, timeStamp: 1004, pressure: 3, tiltX: 140 })] }));
    expect(samples.map((s) => s.x)).toEqual([11, 12]);
    expect(samples[1]).toMatchObject({ pressure: 1, tiltX: 90, t: 4 });
    input.cancel();
    expect(input.drawing).toBe(false);
    expect(input.up(ev())).toBeNull();
  });
});
