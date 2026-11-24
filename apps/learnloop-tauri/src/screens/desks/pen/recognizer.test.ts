import { describe, expect, it } from "vitest";
import { RECOGNIZER, boxOf, inMargin, isClosedLoop, recognize, throughTheMiddle, type LineBox, type Point, type RecognizerPage } from "./recognizer";

// A page with one text column from x 100 to 500 and lines 24 px tall starting at y 100 (glyphs fill each line).
const COLUMN = { left: 100, right: 500 };
const LINE = 24;
function page(column: { left: number; right: number } | null = COLUMN): RecognizerPage {
  return {
    textColumn: () => column,
    lineAt: (x: number, y: number): LineBox | null => {
      if (!column || x < column.left || x > column.right || y < 100 || y >= 100 + 10 * LINE) return null;
      const top = 100 + Math.floor((y - 100) / LINE) * LINE;
      return { top, bottom: top + LINE, height: LINE };
    },
  };
}

const line = (x0: number, x1: number, y: number, step = 6): Point[] => {
  const out: Point[] = [];
  for (let x = x0; x <= x1; x += step) out.push({ x, y: y + Math.sin(x) * 1.2 });
  return out;
};
const vertical = (x: number, y0: number, y1: number): Point[] => {
  const out: Point[] = [{ x: x + 10, y: y0 }];
  for (let y = y0; y <= y1; y += 8) out.push({ x, y });
  out.push({ x: x + 10, y: y1 });
  return out;
};
const loop = (cx: number, cy: number, rx: number, ry: number, gap = 0.2): Point[] => {
  const out: Point[] = [];
  for (let a = 0; a <= Math.PI * 2 - gap; a += 0.2) out.push({ x: cx + rx * Math.cos(a), y: cy + ry * Math.sin(a) });
  return out;
};
const scribble = (x: number, y: number, w: number): Point[] => {
  const out: Point[] = [];
  for (let t = 0; t < 1; t += 0.006) out.push({ x: x + t * w, y: y + Math.sin(t * 60) * 7 + Math.sin(t * 13) * 3 });
  return out;
};

describe("the recognizer (spec §10.10's table, the mockup's geometry)", () => {
  it.each([
    ["an underline under a line's words", line(150, 300, 100 + LINE + 2), "underline"],
    ["a strike through a line's middle", line(150, 300, 100 + LINE * 0.55), "strike"],
    ["a closed loop round words", loop(250, 160, 80, 20), "lasso"],
    ["a tall narrow bracket left of the column", vertical(80, 110, 200), "bracket"],
    ["a scribble right of the column", scribble(528, 140, 170), "note"],
    ["a scribble left of the column", scribble(-120, 140, 100), "note"],
    ["a short flat stroke (not wider than 40 px)", line(150, 186, 130), "ink"],
    ["a tall stroke inside the column", vertical(200, 110, 200), "ink"],
    ["a big zigzag over the text", [{ x: 150, y: 110 }, { x: 250, y: 170 }, { x: 300, y: 120 }, { x: 420, y: 190 }], "ink"],
    ["a loop whose ends are 30 px apart or more", loop(250, 160, 80, 40, 0.8), "ink"],
  ])("%s → %s", (_name, points, kind) => {
    expect(recognize(points, page())?.kind).toBe(kind);
  });

  it("a tap (three points or fewer) is not recognized", () => {
    expect(recognize([{ x: 1, y: 1 }, { x: 2, y: 2 }, { x: 3, y: 3 }], page())).toBeNull();
    expect(RECOGNIZER.minPoints).toBe(3);
  });

  it("the thresholds are the spec's: a loop needs w > 30 and h > 16, a bracket h > 40 and w < 26, flat h < 22 and w > 40", () => {
    expect(isClosedLoop(loop(200, 200, 15, 10))).toBe(false); // 30 wide: not more than 30
    expect(isClosedLoop(loop(200, 200, 16, 9))).toBe(true);
    expect(isClosedLoop(loop(200, 200, 30, 8))).toBe(false); // 16 tall: not more than 16
    expect(recognize(vertical(80, 110, 150), page())?.kind).toBe("note"); // 40 tall: not a bracket
    expect(recognize(vertical(80, 110, 151), page())?.kind).toBe("bracket");
    expect(recognize([{ x: 30, y: 110 }, ...vertical(60, 112, 200)], page())?.kind).toBe("note"); // 26 wide or more
    expect(recognize(line(150, 190, 130), page())?.kind).toBe("ink"); // 40 wide: not flat-and-wide
  });

  it("the margin is beyond 4 px past the column; with no text column nothing is in the margin", () => {
    expect(inMargin(boxOf([{ x: 505, y: 0 }, { x: 600, y: 0 }]), COLUMN)).toBe(true);
    expect(inMargin(boxOf([{ x: 504, y: 0 }, { x: 600, y: 0 }]), COLUMN)).toBe(false);
    expect(inMargin(boxOf([{ x: 0, y: 0 }, { x: 95, y: 0 }]), COLUMN)).toBe(true);
    expect(inMargin(boxOf([{ x: 0, y: 0 }, { x: 96, y: 0 }]), COLUMN)).toBe(false);
    expect(recognize(vertical(600, 110, 200), page(null))?.kind).toBe("ink");
  });

  it("through the middle: the line 9 px above holds the middle between 30 % from its top and 25 % from its bottom", () => {
    // The line 100..124: the middle must fall within 107.2..118, and 9 px above it must still be that line.
    expect(throughTheMiddle(boxOf(line(150, 300, 110)), page())).toBe(true);
    expect(throughTheMiddle(boxOf(line(150, 300, 117)), page())).toBe(true);
    expect(throughTheMiddle(boxOf(line(150, 300, 106)), page())).toBe(false); // the line probed above is another
    expect(throughTheMiddle(boxOf(line(150, 300, 126)), page())).toBe(false); // below the line: an underline
  });

  it("an underline's words are on the line 10 px above its middle; a strike's at its middle", () => {
    const under = recognize(line(150, 300, 126), page());
    expect(under?.kind).toBe("underline");
    expect(under?.lineY).toBeCloseTo((under!.box.y0 + under!.box.y1) / 2 - 10);
    const strike = recognize(line(150, 300, 112), page());
    expect(strike?.kind).toBe("strike");
    expect(strike?.lineY).toBeCloseTo((strike!.box.y0 + strike!.box.y1) / 2);
  });

  it("ambiguous strokes resolve by the table's order: a loop first, then the margin, then flat strokes", () => {
    // A closed loop drawn in the margin is a selection attempt, not a note.
    expect(recognize(loop(600, 160, 40, 20), page())?.kind).toBe("lasso");
    // A flat wide stroke in the margin is a note, not an underline.
    expect(recognize(line(520, 640, 130), page())?.kind).toBe("note");
    // A flat stroke over no text line is an underline candidate (its words are looked for by the layer).
    expect(recognize(line(150, 300, 400), page())?.kind).toBe("underline");
  });
});
