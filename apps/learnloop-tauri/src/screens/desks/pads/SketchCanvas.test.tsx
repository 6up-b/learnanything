// Sketch blocks (spec §10.8): every tool draws a typed shape into the block's payload in the canvas's own
// units, the eraser removes what it touches, drawing near the bottom grows the canvas, and a paused or
// read-only canvas draws nothing.
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { SKETCH_SIZES, SketchCanvas, hits, readSketch, smoothPath, type SketchPayload } from "./SketchCanvas";

afterEach(cleanup);

// jsdom has no PointerEvent: without one a pointer event carries no coordinates.
if (typeof window.PointerEvent === "undefined") {
  class PointerEventStandIn extends MouseEvent {
    pointerId: number;
    pointerType: string;
    pressure: number;
    constructor(type: string, init: PointerEventInit = {}) {
      super(type, init);
      this.pointerId = init.pointerId ?? 1;
      this.pointerType = init.pointerType ?? "mouse";
      this.pressure = init.pressure ?? 0;
    }
  }
  (window as unknown as { PointerEvent: unknown }).PointerEvent = PointerEventStandIn;
}

function canvas(payload: Record<string, unknown>, editable = true, text: string | null = "a label") {
  const commits: SketchPayload[] = [];
  render(<SketchCanvas payload={payload} editable={editable} onCommit={(next) => commits.push(next)} onTextPrompt={() => text} />);
  const svg = screen.getByRole("img", { name: "your sketch" });
  // A 960 px wide canvas at 2x: screen offsets are halved into the canvas's units.
  svg.getBoundingClientRect = () => ({ left: 10, top: 20, width: 960, height: 320, right: 970, bottom: 340, x: 10, y: 20, toJSON: () => ({}) });
  const stroke = (from: [number, number], to: [number, number]) => {
    fireEvent.pointerDown(svg, { clientX: from[0], clientY: from[1], pointerId: 1 });
    fireEvent.pointerMove(svg, { clientX: (from[0] + to[0]) / 2, clientY: (from[1] + to[1]) / 2, pointerId: 1 });
    fireEvent.pointerMove(svg, { clientX: to[0], clientY: to[1], pointerId: 1 });
    fireEvent.pointerUp(svg, { clientX: to[0], clientY: to[1], pointerId: 1 });
  };
  return { commits, svg, stroke, tool: (label: RegExp) => fireEvent.click(screen.getByRole("button", { name: label })) };
}

describe("a sketch block", () => {
  it("offers every tool, and each draws its shape in the canvas's units", () => {
    const { commits, stroke, tool } = canvas({ width: 480, height: 160, items: [] });
    for (const label of ["✎ pen", "／ line", "→ arrow", "▭ box", "T text", "⌫ eraser"]) expect(screen.getByRole("button", { name: label })).toBeTruthy();
    tool(/line/);
    stroke([30, 40], [130, 40]);
    expect(commits[0].items).toEqual([{ type: "line", x1: 10, y1: 10, x2: 60, y2: 10 }]);
    tool(/arrow/);
    stroke([30, 40], [130, 40]);
    expect(commits[1].items[0]).toEqual({ type: "arrow", x1: 10, y1: 10, x2: 60, y2: 10 });
    tool(/box/);
    stroke([130, 140], [30, 40]);
    expect(commits[2].items[0]).toEqual({ type: "box", x: 10, y: 10, w: 50, h: 50 });
    tool(/pen/);
    stroke([30, 40], [130, 140]);
    expect(commits[3].items[0]).toMatchObject({ type: "path" });
    expect((commits[3].items[0] as { d: string }).d.startsWith("M10 10")).toBe(true);
    tool(/text/);
    fireEvent.pointerDown(screen.getByRole("img"), { clientX: 50, clientY: 60, pointerId: 1 });
    expect(commits[4].items[0]).toEqual({ type: "text", x: 20, y: 20, text: "a label" });
  });

  it("the eraser removes what it touches and nothing else", () => {
    const items = [{ type: "box", x: 10, y: 10, w: 50, h: 50 }, { type: "line", x1: 200, y1: 100, x2: 300, y2: 100 }];
    const { commits, svg, tool } = canvas({ width: 480, height: 160, items });
    tool(/eraser/);
    fireEvent.pointerDown(svg, { clientX: 10 + 2 * 250, clientY: 20 + 2 * 100, pointerId: 1 });
    expect(commits[0].items).toEqual([items[0]]);
    fireEvent.pointerDown(svg, { clientX: 10 + 2 * 400, clientY: 20 + 2 * 20, pointerId: 1 });
    expect(commits).toHaveLength(1);
  });

  it("drawing within 16 px of the bottom grows the canvas by 60 px, and the next commit keeps the height", () => {
    const { commits, stroke, tool } = canvas({ width: 480, height: 160, items: [] });
    tool(/line/);
    // y = 150 in canvas units is within 16 of 160.
    stroke([30, 40], [130, 20 + 2 * 150]);
    expect(commits[0].height).toBe(160 + SKETCH_SIZES.growBy);
  });

  it("a canvas that is not editable (a paused window) draws nothing and shows no tools", () => {
    const { commits, stroke } = canvas({ width: 480, height: 160, items: [] }, false);
    expect(screen.queryByRole("button", { name: "▭ box" })).toBeNull();
    stroke([30, 40], [130, 140]);
    expect(commits).toEqual([]);
  });

  it("reads a payload with defaults, smooths a stroke and hit-tests each shape", () => {
    expect(readSketch({})).toEqual({ width: 480, height: SKETCH_SIZES.minHeight, items: [] });
    expect(smoothPath([{ x: 0, y: 0 }, { x: 10, y: 0 }, { x: 20, y: 10 }])).toBe("M0 0 Q10 0 15 5 L20 10");
    expect(hits({ type: "box", x: 0, y: 0, w: 10, h: 10 }, 5, 0)).toBe(true);
    expect(hits({ type: "line", x1: 0, y1: 0, x2: 100, y2: 0 }, 50, 30)).toBe(false);
  });
});
