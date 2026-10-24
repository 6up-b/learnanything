// Reader workbench RW5b: the trusted renderer's heat maps, vector fields,
// trajectories and iterated maps (spec §8.7; UX §4.7, §7.2).
//
// Draws only what evaluateFigure computed (figureSpec.ts): a heat map is one
// hue whose opacity rises with the value (readable in greyscale), with its
// contour lines traced by marching squares over the computed grid; a vector
// field's arrows are scaled by the longest one, over its heat map when it has
// one; a trajectory or an iterated map is its computed points joined, from a
// marked start, and when the path stopped (it left the plot, or a value was
// not finite) the panel says so in words: nothing past that point is drawn.
// Every panel has a values table (the `t` toggle), sampled to at most about a
// dozen rows and columns so a screen reader can use it. Nothing here animates.
import type { CSSProperties } from "react";
import { COLOR, FONT_MONO } from "../../../components/term";
import { ESCAPE_MARGIN, type HeatmapGridData, type IterateData, type TrajectoryData, type VectorFieldData } from "./figureSpec";
import { formatValue } from "./FigurePanels";

const W = 600;
const H = 300;
const PAD = { left: 44, right: 12, top: 10, bottom: 26 };
const TABLE_SIDE = 12;

const svgStyle: CSSProperties = { width: "100%", height: "auto", display: "block", fontFamily: FONT_MONO, fontSize: 10 };
const tableStyle: CSSProperties = { borderCollapse: "collapse", fontFamily: FONT_MONO, fontSize: 10, color: COLOR.text };
const cellStyle: CSSProperties = { border: `1px solid ${COLOR.border}`, padding: "1px 6px", textAlign: "right" };
const noteStyle: CSSProperties = { fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim };

export const ADVANCED_COPY = {
  leftPlot: "the path leaves the plot here; nothing past it is drawn",
  notFinite: "a value stopped being a number here; nothing past it is drawn",
  startsOutside: "the path starts outside the plot, so nothing is drawn",
  start: "start",
} as const;

function scaler(domain: [number, number], range: [number, number]): (value: number) => number {
  const [d0, d1] = domain;
  const [r0, r1] = range;
  const span = d1 - d0 || 1;
  return (value: number) => r0 + ((value - d0) / span) * (r1 - r0);
}

function finiteRange(values: Array<number | null>): [number, number] | null {
  let low = Infinity;
  let high = -Infinity;
  for (const value of values) {
    if (value === null || !Number.isFinite(value)) continue;
    if (value < low) low = value;
    if (value > high) high = value;
  }
  return low <= high ? [low, high] : null;
}

/** Every `step`-th index, the last one always included. */
function sampled(length: number, side = TABLE_SIDE): number[] {
  if (length <= 0) return [];
  const step = Math.max(1, Math.ceil(length / side));
  const out: number[] = [];
  for (let index = 0; index < length; index += step) out.push(index);
  if (out[out.length - 1] !== length - 1) out.push(length - 1);
  return out;
}

function GridAxes({ x, y, xDomain, yDomain }: { x: (v: number) => number; y: (v: number) => number; xDomain: [number, number]; yDomain: [number, number] }) {
  return (
    <g stroke={COLOR.borderStrong} fill={COLOR.textDim}>
      <rect x={x(xDomain[0])} y={y(yDomain[1])} width={x(xDomain[1]) - x(xDomain[0])} height={y(yDomain[0]) - y(yDomain[1])} fill="none" />
      {[xDomain[0], (xDomain[0] + xDomain[1]) / 2, xDomain[1]].map((tick) => (
        <text key={`x${tick}`} x={x(tick)} y={H - 8} textAnchor="middle" stroke="none">{formatValue(tick)}</text>
      ))}
      {[yDomain[0], (yDomain[0] + yDomain[1]) / 2, yDomain[1]].map((tick) => (
        <text key={`y${tick}`} x={PAD.left - 4} y={y(tick) + 3} textAnchor="end" stroke="none">{formatValue(tick)}</text>
      ))}
    </g>
  );
}

/** The plot square for a grid: x across, y up. */
function frame(xs: number[], ys: number[]) {
  const xDomain: [number, number] = [xs[0], xs[xs.length - 1]];
  const yDomain: [number, number] = [ys[0], ys[ys.length - 1]];
  return { xDomain, yDomain, x: scaler(xDomain, [PAD.left, W - PAD.right]), y: scaler(yDomain, [H - PAD.bottom, PAD.top]) };
}

/** Contour segments at `level` by marching squares over the computed grid (display only). */
export function contourSegments(grid: HeatmapGridData, level: number): Array<[[number, number], [number, number]]> {
  const segments: Array<[[number, number], [number, number]]> = [];
  const { x: xs, y: ys, z } = grid;
  const cross = (x0: number, y0: number, v0: number, x1: number, y1: number, v1: number): [number, number] => {
    const t = v1 === v0 ? 0.5 : (level - v0) / (v1 - v0);
    return [x0 + (x1 - x0) * t, y0 + (y1 - y0) * t];
  };
  for (let j = 0; j + 1 < ys.length; j += 1) {
    for (let i = 0; i + 1 < xs.length; i += 1) {
      const corners = [z[j][i], z[j][i + 1], z[j + 1][i + 1], z[j + 1][i]];
      if (corners.some((value) => value === null)) continue;
      const [a, b, c, d] = corners as number[];
      const points: Array<[number, number]> = [];
      const edges: Array<[number, number, number, number, number, number]> = [
        [xs[i], ys[j], a, xs[i + 1], ys[j], b],
        [xs[i + 1], ys[j], b, xs[i + 1], ys[j + 1], c],
        [xs[i + 1], ys[j + 1], c, xs[i], ys[j + 1], d],
        [xs[i], ys[j + 1], d, xs[i], ys[j], a],
      ];
      for (const [x0, y0, v0, x1, y1, v1] of edges) {
        if ((v0 < level) !== (v1 < level)) points.push(cross(x0, y0, v0, x1, y1, v1));
      }
      if (points.length === 2) segments.push([points[0], points[1]]);
      else if (points.length === 4) segments.push([points[0], points[1]], [points[2], points[3]]);
    }
  }
  return segments;
}

function HeatCells({ grid, x, y }: { grid: HeatmapGridData; x: (v: number) => number; y: (v: number) => number }) {
  const range = finiteRange(grid.z.flat());
  if (!range) return null;
  const [low, high] = range;
  const span = high - low || 1;
  const halfX = (index: number) => (index + 1 < grid.x.length ? (grid.x[index + 1] - grid.x[index]) / 2 : (grid.x[index] - grid.x[index - 1]) / 2);
  const halfY = (index: number) => (index + 1 < grid.y.length ? (grid.y[index + 1] - grid.y[index]) / 2 : (grid.y[index] - grid.y[index - 1]) / 2);
  return (
    <g data-figure-heat="">
      {grid.z.map((row, j) => row.map((value, i) => {
        if (value === null) return null;
        const left = x(Math.max(grid.x[0], grid.x[i] - halfX(i)));
        const right = x(Math.min(grid.x[grid.x.length - 1], grid.x[i] + halfX(i)));
        const top = y(Math.min(grid.y[grid.y.length - 1], grid.y[j] + halfY(j)));
        const bottom = y(Math.max(grid.y[0], grid.y[j] - halfY(j)));
        return (
          <rect key={`${i}-${j}`} x={left} y={top} width={Math.max(0.5, right - left)} height={Math.max(0.5, bottom - top)}
            fill={COLOR.amber} fillOpacity={0.06 + 0.84 * ((value - low) / span)} stroke="none" />
        );
      }))}
      {grid.contours.map((contour, index) => contour.level === null ? null : (
        <path key={`c${index}`} data-figure-contour={contour.level} fill="none" stroke={COLOR.text} strokeWidth={1} strokeDasharray={index % 2 ? "3 2" : ""}
          d={contourSegments(grid, contour.level).map(([[x0, y0], [x1, y1]]) => `M${x(x0).toFixed(1)},${y(y0).toFixed(1)}L${x(x1).toFixed(1)},${y(y1).toFixed(1)}`).join("")} />
      ))}
    </g>
  );
}

function HeatLegend({ grid }: { grid: HeatmapGridData }) {
  const range = finiteRange(grid.z.flat());
  return (
    <div style={{ ...noteStyle, display: "flex", gap: 14, flexWrap: "wrap" }}>
      {grid.label ? <span style={{ color: COLOR.text }}>{grid.label}</span> : null}
      {range ? <span>lighter {formatValue(range[0])} → darker {formatValue(range[1])}</span> : null}
      {grid.contours.length ? <span>contours at {grid.contours.map((contour) => formatValue(contour.level)).join(", ")}</span> : null}
    </div>
  );
}

function ValuesGrid({ xs, ys, cell, label }: { xs: number[]; ys: number[]; cell: (j: number, i: number) => string; label: string }) {
  const columns = sampled(xs.length);
  const rows = sampled(ys.length);
  return (
    <table style={tableStyle} aria-label={label}>
      <thead>
        <tr><th style={cellStyle}>y \ x</th>{columns.map((i) => <th key={i} style={cellStyle}>{formatValue(xs[i])}</th>)}</tr>
      </thead>
      <tbody>
        {[...rows].reverse().map((j) => (
          <tr key={j}><th style={cellStyle}>{formatValue(ys[j])}</th>{columns.map((i) => <td key={i} style={cellStyle}>{cell(j, i)}</td>)}</tr>
        ))}
      </tbody>
    </table>
  );
}

export function HeatmapPanelView({ data, showTable }: { data: HeatmapGridData & { kind: "heatmap_2d" }; showTable: boolean }) {
  const { x, y, xDomain, yDomain } = frame(data.x, data.y);
  return (
    <div data-figure-panel="heatmap_2d">
      <svg viewBox={`0 0 ${W} ${H}`} style={svgStyle} role="img" aria-label={`heat map${data.label ? ` of ${data.label}` : ""}${data.contours.length ? ` with ${data.contours.length} contour lines` : ""}`}>
        <HeatCells grid={data} x={x} y={y} />
        <GridAxes x={x} y={y} xDomain={xDomain} yDomain={yDomain} />
      </svg>
      <HeatLegend grid={data} />
      {showTable ? <ValuesGrid xs={data.x} ys={data.y} label="values as a table" cell={(j, i) => formatValue(data.z[j][i])} /> : null}
    </div>
  );
}

export function VectorFieldPanelView({ data, showTable }: { data: VectorFieldData; showTable: boolean }) {
  const { x, y, xDomain, yDomain } = frame(data.x, data.y);
  let longest = 0;
  data.u.forEach((row, j) => row.forEach((u, i) => {
    const v = data.v[j][i];
    if (u !== null && v !== null) longest = Math.max(longest, Math.hypot(u, v));
  }));
  const stepX = data.x.length > 1 ? Math.abs(x(data.x[1]) - x(data.x[0])) : W;
  const stepY = data.y.length > 1 ? Math.abs(y(data.y[1]) - y(data.y[0])) : H;
  const reach = 0.85 * Math.min(stepX, stepY);
  return (
    <div data-figure-panel="vector_field_2d">
      <svg viewBox={`0 0 ${W} ${H}`} style={svgStyle} role="img" aria-label={`vector field${data.label ? ` of ${data.label}` : ""}${data.heatmap ? `, over a heat map${data.heatmap.label ? ` of ${data.heatmap.label}` : ""}` : ""}`}>
        <defs>
          <marker id="figure-arrow" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="5" markerHeight="5" orient="auto">
            <path d="M0,0L6,3L0,6Z" fill={COLOR.cyan} />
          </marker>
        </defs>
        {data.heatmap ? <HeatCells grid={data.heatmap} x={x} y={y} /> : null}
        <GridAxes x={x} y={y} xDomain={xDomain} yDomain={yDomain} />
        <g data-figure-arrows="">
          {data.u.map((row, j) => row.map((u, i) => {
            const v = data.v[j][i];
            if (u === null || v === null || longest === 0) return null;
            const scale = reach / longest;
            const x0 = x(data.x[i]);
            const y0 = y(data.y[j]);
            const dx = u * scale;
            const dy = -v * scale;
            if (Math.hypot(dx, dy) < 0.5) return <circle key={`${i}-${j}`} cx={x0} cy={y0} r={1} fill={COLOR.cyan} />;
            return <line key={`${i}-${j}`} x1={x0 - dx / 2} y1={y0 - dy / 2} x2={x0 + dx / 2} y2={y0 + dy / 2} stroke={COLOR.cyan} strokeWidth={1.2} markerEnd="url(#figure-arrow)" />;
          }))}
        </g>
      </svg>
      <div style={noteStyle}>{data.label ? `${data.label} · ` : ""}arrows scaled to the longest ({formatValue(longest)})</div>
      {data.heatmap ? <HeatLegend grid={data.heatmap} /> : null}
      {showTable ? (
        <ValuesGrid xs={data.x} ys={data.y} label="values as a table"
          cell={(j, i) => `(${formatValue(data.u[j][i])}, ${formatValue(data.v[j][i])})`} />
      ) : null}
    </div>
  );
}

/** The window a path is drawn in: its plot range padded as the evaluator pads it (ESCAPE_MARGIN). */
function pathWindow(range: { min: number; max: number }): [number, number] {
  const pad = (range.max - range.min) * ESCAPE_MARGIN;
  return [range.min - pad, range.max + pad];
}

export function PathPanelView({ data, axes, showTable }: { data: TrajectoryData | IterateData; axes: { x: { var: string; min: number; max: number }; y: { var: string; min: number; max: number } } | null; showTable: boolean }) {
  const trajectory = data.kind === "trajectory_2d";
  const xDomain = axes ? pathWindow(axes.x) : (finiteRange(data.x) ?? [0, 1]);
  const yDomain = axes ? pathWindow(axes.y) : (finiteRange(data.y) ?? [0, 1]);
  const x = scaler(xDomain, [PAD.left, W - PAD.right]);
  const y = scaler(yDomain, [H - PAD.bottom, PAD.top]);
  const steps = trajectory ? (data as TrajectoryData).t : (data as IterateData).k;
  const d = data.x.map((xv, index) => `${index ? "L" : "M"}${x(xv).toFixed(1)},${y(data.y[index]).toFixed(1)}`).join("");
  const stoppedLine = data.stopped === "left_plot" ? ADVANCED_COPY.leftPlot
    : data.stopped === "not_finite" ? ADVANCED_COPY.notFinite
      : data.stopped === "starts_outside" ? ADVANCED_COPY.startsOutside : null;
  const last = data.x.length - 1;
  return (
    <div data-figure-panel={data.kind}>
      <svg viewBox={`0 0 ${W} ${H}`} style={svgStyle} role="img"
        aria-label={`${trajectory ? "trajectory" : "iterates"}${data.label ? ` (${data.label})` : ""}: ${data.x.length} points${stoppedLine ? `; ${stoppedLine}` : ""}`}>
        {axes ? (
          <rect x={x(axes.x.min)} y={y(axes.y.max)} width={x(axes.x.max) - x(axes.x.min)} height={y(axes.y.min) - y(axes.y.max)}
            fill="none" stroke={COLOR.border} strokeDasharray="2 3" />
        ) : null}
        <GridAxes x={x} y={y} xDomain={xDomain} yDomain={yDomain} />
        {data.x.length ? <path d={d} fill="none" stroke={COLOR.amber} strokeWidth={trajectory ? 1.6 : 0.8} data-figure-path="" /> : null}
        {!trajectory ? data.x.map((xv, index) => (
          <circle key={index} cx={x(xv)} cy={y(data.y[index])} r={1.8} fill={COLOR.amber} data-figure-iterate={index} />
        )) : null}
        {data.x.length ? (
          <g>
            <circle cx={x(data.x[0])} cy={y(data.y[0])} r={3.5} fill="none" stroke={COLOR.text} data-figure-start="" />
            <text x={x(data.x[0]) + 5} y={y(data.y[0]) - 5} fill={COLOR.textDim}>{ADVANCED_COPY.start}</text>
          </g>
        ) : null}
        {data.stopped && last >= 0 ? <circle cx={x(data.x[last])} cy={y(data.y[last])} r={3} fill={COLOR.red} data-figure-stop={data.stopped} /> : null}
      </svg>
      <div style={noteStyle}>
        {data.label ? `${data.label} · ` : ""}{trajectory ? `fixed-step RK4, t up to ${formatValue(steps[last] ?? null)}` : `${Math.max(0, last)} iterations`}
        {stoppedLine ? <span data-figure-stopped={data.stopped ?? ""} style={{ color: COLOR.text }}> · {stoppedLine}</span> : null}
      </div>
      {showTable ? (
        <table style={tableStyle} aria-label="values as a table">
          <thead><tr><th style={cellStyle}>{trajectory ? "t" : "k"}</th><th style={cellStyle}>{axes?.x.var ?? "x"}</th><th style={cellStyle}>{axes?.y.var ?? "y"}</th></tr></thead>
          <tbody>
            {sampled(data.x.length, 24).map((index) => (
              <tr key={index}><td style={cellStyle}>{formatValue(steps[index])}</td><td style={cellStyle}>{formatValue(data.x[index])}</td><td style={cellStyle}>{formatValue(data.y[index])}</td></tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </div>
  );
}
