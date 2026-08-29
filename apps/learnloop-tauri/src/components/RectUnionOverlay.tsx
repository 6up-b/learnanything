import { useMemo } from "react";

interface RectUnionPaths {
  fill: string;
  outline: string;
}

function normalizedRects(rects: number[][]): number[][] {
  return rects
    .filter((rect) => rect.length === 4)
    .map((rect) => [
      Math.min(rect[0], rect[2]),
      Math.min(rect[1], rect[3]),
      Math.max(rect[0], rect[2]),
      Math.max(rect[1], rect[3]),
    ])
    .filter((rect) => rect[2] > rect[0] && rect[3] > rect[1]);
}

/** Convert overlapping axis-aligned rectangles into one fill path plus only
 * the exterior union boundary. The fill remains a single SVG paint operation,
 * so overlaps never accumulate opacity. */
export function rectUnionPaths(rects: number[][]): RectUnionPaths | null {
  const normalized = normalizedRects(rects);
  if (!normalized.length) return null;
  const xs = [...new Set(normalized.flatMap((rect) => [rect[0], rect[2]]))].sort((a, b) => a - b);
  const ys = [...new Set(normalized.flatMap((rect) => [rect[1], rect[3]]))].sort((a, b) => a - b);
  const occupied = Array.from({ length: ys.length - 1 }, (_, row) =>
    Array.from({ length: xs.length - 1 }, (_, column) => {
      const cx = (xs[column] + xs[column + 1]) / 2;
      const cy = (ys[row] + ys[row + 1]) / 2;
      return normalized.some(
        (rect) => cx >= rect[0] && cx <= rect[2] && cy >= rect[1] && cy <= rect[3],
      );
    }),
  );
  const outline: string[] = [];
  for (let row = 0; row < occupied.length; row += 1) {
    for (let column = 0; column < occupied[row].length; column += 1) {
      if (!occupied[row][column]) continue;
      const x0 = xs[column];
      const x1 = xs[column + 1];
      const y0 = ys[row];
      const y1 = ys[row + 1];
      if (row === 0 || !occupied[row - 1][column]) outline.push(`M${x0} ${y0}H${x1}`);
      if (column + 1 === occupied[row].length || !occupied[row][column + 1]) outline.push(`M${x1} ${y0}V${y1}`);
      if (row + 1 === occupied.length || !occupied[row + 1][column]) outline.push(`M${x1} ${y1}H${x0}`);
      if (column === 0 || !occupied[row][column - 1]) outline.push(`M${x0} ${y1}V${y0}`);
    }
  }
  return {
    // One path element paints all subpaths as a single geometry. Nonzero fill
    // makes overlapping same-winding rectangles part of one opaque union.
    fill: normalized.map((rect) => `M${rect[0]} ${rect[1]}H${rect[2]}V${rect[3]}H${rect[0]}Z`).join(""),
    outline: outline.join(""),
  };
}

export function RectUnionOverlay({ rects, scale = 1 }: { rects: number[][]; scale?: number }) {
  const paths = useMemo(() => rectUnionPaths(rects), [rects]);
  if (!paths) return null;
  return (
    <svg
      aria-hidden="true"
      width="1"
      height="1"
      style={{
        position: "absolute",
        left: 0,
        top: 0,
        overflow: "visible",
        pointerEvents: "none",
        mixBlendMode: "multiply",
      }}
    >
      <g transform={`scale(${scale})`}>
        <path d={paths.fill} fill="rgba(245, 166, 35, 0.18)" fillRule="nonzero" />
        <path
          d={paths.outline}
          fill="none"
          stroke="rgba(215, 135, 15, 0.9)"
          strokeWidth="1.5"
          vectorEffect="non-scaling-stroke"
        />
      </g>
    </svg>
  );
}
