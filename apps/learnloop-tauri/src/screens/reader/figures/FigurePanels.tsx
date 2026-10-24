// Reader workbench RW5a: the trusted renderer's panels (spec §8.2; UX §4.7, §7.2).
//
// Draws what evaluateFigure computed (figureSpec.ts) as SVG: function plots
// with their shaded areas and markers, PMF bars with a highlighted range, the
// unit square under a 2x2 linear map, and readouts. Every panel has a values
// table, its data-table equivalent for screen readers (the `t` toggle). Series
// and areas differ by line style and pattern as well as colour, so they
// survive greyscale. Nothing here animates: motion is only ever a parameter
// the learner set or played (FigureInline). RW5b's heat maps, vector fields,
// trajectories and iterated maps are drawn by AdvancedPanels.tsx.
import type { CSSProperties } from "react";
import { COLOR, FONT_MONO } from "../../../components/term";
import { HeatmapPanelView, PathPanelView, VectorFieldPanelView } from "./AdvancedPanels";
import type { FigurePanel as FigurePanelModel, FunctionPlotData, LinearMapData, PanelData, PmfBarsData, ReadoutData } from "./figureSpec";

const W = 600;
const H = 220;
const PAD = { left: 44, right: 12, top: 10, bottom: 26 };
const DASHES = ["", "6 4", "2 3", "10 3 2 3"];
const SHADE_FILLS = ["var(--wash-amber)", "var(--wash-cyan)", "var(--wash-purple)", "var(--wash-green)"];

export function formatValue(value: number | null, format: "number" | "percent" = "number"): string {
  if (value === null || !Number.isFinite(value)) return "—";
  if (format === "percent") {
    // The scaled number is what is shown: guard it too (fix round 5; 1e307 as a percent overflows).
    const scaled = value * 100;
    return Number.isFinite(scaled) ? `${scaled.toFixed(1)}%` : "—";
  }
  if (value !== 0 && (Math.abs(value) >= 1e5 || Math.abs(value) < 1e-3)) return value.toExponential(3);
  return String(Number(value.toPrecision(5)));
}

function extent(values: Array<number | null>, include: number[] = []): [number, number] {
  const finite = [...values.filter((value): value is number => value !== null && Number.isFinite(value)), ...include];
  if (!finite.length) return [0, 1];
  let low = Math.min(...finite);
  let high = Math.max(...finite);
  if (low === high) {
    low -= 1;
    high += 1;
  }
  const pad = (high - low) * 0.05;
  return [low - (low === 0 ? 0 : pad), high + pad];
}

function scaler(domain: [number, number], range: [number, number]): (value: number) => number {
  const [d0, d1] = domain;
  const [r0, r1] = range;
  return (value: number) => r0 + ((value - d0) / (d1 - d0)) * (r1 - r0);
}

const svgStyle: CSSProperties = { width: "100%", height: "auto", display: "block", fontFamily: FONT_MONO, fontSize: 10 };
const tableStyle: CSSProperties = { borderCollapse: "collapse", fontFamily: FONT_MONO, fontSize: 10, color: COLOR.text };
const cellStyle: CSSProperties = { border: `1px solid ${COLOR.border}`, padding: "1px 6px", textAlign: "right" };

function Axes({ x, y, xDomain, yDomain }: { x: (v: number) => number; y: (v: number) => number; xDomain: [number, number]; yDomain: [number, number] }) {
  const zeroY = yDomain[0] <= 0 && yDomain[1] >= 0 ? y(0) : H - PAD.bottom;
  return (
    <g stroke={COLOR.borderStrong} fill={COLOR.textDim}>
      <line x1={PAD.left} x2={W - PAD.right} y1={zeroY} y2={zeroY} />
      <line x1={PAD.left} x2={PAD.left} y1={PAD.top} y2={H - PAD.bottom} />
      {[xDomain[0], (xDomain[0] + xDomain[1]) / 2, xDomain[1]].map((tick) => (
        <text key={`x${tick}`} x={x(tick)} y={H - 8} textAnchor="middle" stroke="none">{formatValue(tick)}</text>
      ))}
      {[yDomain[0], yDomain[1]].map((tick) => (
        <text key={`y${tick}`} x={PAD.left - 4} y={y(tick) + 3} textAnchor="end" stroke="none">{formatValue(tick)}</text>
      ))}
    </g>
  );
}

function FunctionPlot({ data, showTable }: { data: FunctionPlotData; showTable: boolean }) {
  const xDomain: [number, number] = [data.x[0], data.x[data.x.length - 1]];
  const yDomain = extent(data.series.flatMap((series) => series.y), [0]);
  const x = scaler(xDomain, [PAD.left, W - PAD.right]);
  const y = scaler(yDomain, [H - PAD.bottom, PAD.top]);
  const path = (ys: Array<number | null>) => {
    let d = "";
    let pen = false;
    ys.forEach((value, index) => {
      if (value === null) {
        pen = false;
        return;
      }
      d += `${pen ? "L" : "M"}${x(data.x[index]).toFixed(1)},${y(value).toFixed(1)}`;
      pen = true;
    });
    return d;
  };
  const shadePath = (shade: FunctionPlotData["shades"][number]) => {
    const series = data.series.find((item) => item.label === shade.series);
    if (!series || shade.from === null || shade.to === null) return "";
    const [low, high] = shade.from <= shade.to ? [shade.from, shade.to] : [shade.to, shade.from];
    const points: Array<[number, number]> = [];
    data.x.forEach((xv, index) => {
      const yv = series.y[index];
      if (xv >= low && xv <= high && yv !== null) points.push([xv, yv]);
    });
    if (!points.length) return "";
    const base = y(Math.max(yDomain[0], Math.min(0, yDomain[1])));
    return `M${x(points[0][0]).toFixed(1)},${base.toFixed(1)}`
      + points.map(([xv, yv]) => `L${x(xv).toFixed(1)},${y(yv).toFixed(1)}`).join("")
      + `L${x(points[points.length - 1][0]).toFixed(1)},${base.toFixed(1)}Z`;
  };
  return (
    <div data-figure-panel="function_plot">
      <svg viewBox={`0 0 ${W} ${H}`} style={svgStyle} role="img"
        aria-label={`plot of ${data.series.map((series) => series.label).join(", ")}${data.shades.length ? `; shaded: ${data.shades.map((shade) => `${shade.label} ${formatValue(shade.value)}`).join(", ")}` : ""}`}>
        <defs>
          <pattern id="figure-hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <line x1="0" y1="0" x2="0" y2="6" stroke={COLOR.textDim} strokeWidth="1" />
          </pattern>
        </defs>
        {data.shades.map((shade, index) => (
          <path key={`shade-${shade.label}`} d={shadePath(shade)} data-figure-shade={shade.label}
            fill={index % 2 === 1 ? "url(#figure-hatch)" : SHADE_FILLS[index % SHADE_FILLS.length]} stroke="none" opacity={0.9} />
        ))}
        <Axes x={x} y={y} xDomain={xDomain} yDomain={yDomain} />
        {data.markers.map((marker) => marker.x === null ? null : (
          <g key={`marker-${marker.label}`}>
            <line x1={x(marker.x)} x2={x(marker.x)} y1={PAD.top} y2={H - PAD.bottom} stroke={COLOR.textDim} strokeDasharray="2 3" />
            <text x={x(marker.x) + 3} y={PAD.top + 9} fill={COLOR.textDim}>{marker.label}</text>
          </g>
        ))}
        {data.series.map((series, index) => (
          <path key={`series-${series.label}`} d={path(series.y)} fill="none" stroke={index === 0 ? COLOR.amber : COLOR.cyan}
            strokeWidth={1.6} strokeDasharray={DASHES[index % DASHES.length]} data-figure-series={series.label} />
        ))}
      </svg>
      <div style={{ display: "flex", gap: 14, flexWrap: "wrap", fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim }}>
        {data.series.map((series, index) => (
          <span key={series.label}>{["──", "- -", "···", "-·-"][index % 4]} {series.label}</span>
        ))}
        {data.shades.map((shade) => (
          <span key={shade.label} data-figure-readout={shade.label} style={{ color: COLOR.text }}>
            {shade.label}: {formatValue(shade.value)}
          </span>
        ))}
      </div>
      {showTable ? <FunctionTable data={data} /> : null}
    </div>
  );
}

function FunctionTable({ data }: { data: FunctionPlotData }) {
  const rows = data.x.map((xv, index) => ({ xv, index })).filter(({ index }) => index % 10 === 0);
  return (
    <table style={tableStyle} aria-label="values as a table">
      <thead>
        <tr><th style={cellStyle}>x</th>{data.series.map((series) => <th key={series.label} style={cellStyle}>{series.label}</th>)}</tr>
      </thead>
      <tbody>
        {rows.map(({ xv, index }) => (
          <tr key={index}>
            <td style={cellStyle}>{formatValue(xv)}</td>
            {data.series.map((series) => <td key={series.label} style={cellStyle}>{formatValue(series.y[index])}</td>)}
          </tr>
        ))}
        {data.shades.map((shade) => (
          <tr key={`shade-${shade.label}`}>
            <td style={cellStyle}>{shade.label}</td>
            <td style={cellStyle} colSpan={data.series.length}>
              {formatValue(shade.value)} (from {formatValue(shade.from)} to {formatValue(shade.to)})
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function PmfBars({ data, showTable }: { data: PmfBarsData; showTable: boolean }) {
  const ks = data.k;
  const yDomain = extent(data.series.flatMap((series) => series.p), [0]);
  const x = scaler([ks[0] - 0.5, ks[ks.length - 1] + 0.5], [PAD.left, W - PAD.right]);
  const y = scaler(yDomain, [H - PAD.bottom, PAD.top]);
  const width = Math.max(1, (x(1) - x(0)) * 0.7 / Math.max(1, data.series.length));
  const inHighlight = (k: number) => data.highlight !== null && data.highlight.from !== null && data.highlight.to !== null
    && k >= data.highlight.from - 1e-9 && k <= data.highlight.to + 1e-9;
  return (
    <div data-figure-panel="pmf_bars">
      <svg viewBox={`0 0 ${W} ${H}`} style={svgStyle} role="img"
        aria-label={`bars of ${data.series.map((series) => series.label).join(", ")}${data.highlight ? `; ${data.highlight.label} ${formatValue(data.highlight.value)}` : ""}`}>
        <Axes x={x} y={y} xDomain={[ks[0], ks[ks.length - 1]]} yDomain={yDomain} />
        {data.series.map((series, s) => series.p.map((value, index) => value === null ? null : (
          <rect key={`${series.label}-${ks[index]}`} x={x(ks[index]) - (width * data.series.length) / 2 + s * width} width={width}
            y={Math.min(y(value), y(0))} height={Math.abs(y(0) - y(value))}
            fill={s === 0 && inHighlight(ks[index]) ? COLOR.amber : "none"}
            stroke={s === 0 ? COLOR.amber : COLOR.cyan} strokeDasharray={DASHES[s % DASHES.length]}
            data-figure-bar={ks[index]} data-highlighted={s === 0 && inHighlight(ks[index]) ? "" : undefined} />
        )))}
      </svg>
      {data.highlight ? (
        <div data-figure-readout={data.highlight.label} style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.text }}>
          {data.highlight.label}: {formatValue(data.highlight.value)} (filled bars)
        </div>
      ) : null}
      {showTable ? (
        <table style={tableStyle} aria-label="values as a table">
          <thead><tr><th style={cellStyle}>k</th>{data.series.map((series) => <th key={series.label} style={cellStyle}>{series.label}</th>)}</tr></thead>
          <tbody>
            {ks.map((k, index) => (
              <tr key={k}><td style={cellStyle}>{k}</td>{data.series.map((series) => <td key={series.label} style={cellStyle}>{formatValue(series.p[index])}</td>)}</tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </div>
  );
}

function LinearMap({ data, label, showTable }: { data: LinearMapData; label: string; showTable: boolean }) {
  const points = data.square.filter((point): point is [number, number] => point[0] !== null && point[1] !== null);
  const all = [...points, [0, 0], [1, 0], [1, 1], [0, 1]] as Array<[number, number]>;
  const reach = Math.max(1.2, ...all.map(([px, py]) => Math.max(Math.abs(px), Math.abs(py)))) * 1.1;
  const size = H - PAD.top - PAD.bottom;
  const left = (W - size) / 2;
  const x = scaler([-reach, reach], [left, left + size]);
  const y = scaler([-reach, reach], [H - PAD.bottom, PAD.top]);
  const polygon = (corners: Array<[number, number]>) => corners.map(([px, py]) => `${x(px).toFixed(1)},${y(py).toFixed(1)}`).join(" ");
  return (
    <div data-figure-panel="linear_map_2d">
      <svg viewBox={`0 0 ${W} ${H}`} style={svgStyle} role="img"
        aria-label={`the unit square and its image under ${label || "the matrix"}, determinant ${formatValue(data.determinant)}`}>
        <line x1={x(-reach)} x2={x(reach)} y1={y(0)} y2={y(0)} stroke={COLOR.border} />
        <line x1={x(0)} x2={x(0)} y1={y(-reach)} y2={y(reach)} stroke={COLOR.border} />
        <polygon points={polygon([[0, 0], [1, 0], [1, 1], [0, 1]])} fill="none" stroke={COLOR.textDim} strokeDasharray="2 3" />
        {points.length === 4 ? <polygon points={polygon(points)} fill="var(--wash-amber)" stroke={COLOR.amber} data-figure-image="" /> : null}
      </svg>
      <div style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.text }} data-figure-readout="determinant">
        {label ? `${label} · ` : ""}determinant {formatValue(data.determinant)} (area of the image)
      </div>
      {showTable ? (
        <table style={tableStyle} aria-label="values as a table">
          <tbody>
            {data.matrix.map((row, index) => (
              <tr key={`m${index}`}><td style={cellStyle}>row {index + 1}</td>{row.map((value, j) => <td key={j} style={cellStyle}>{formatValue(value)}</td>)}</tr>
            ))}
            {data.square.map(([px, py], index) => (
              <tr key={`c${index}`}><td style={cellStyle}>corner {index + 1}</td><td style={cellStyle}>{formatValue(px)}</td><td style={cellStyle}>{formatValue(py)}</td></tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </div>
  );
}

function Readout({ data }: { data: ReadoutData }) {
  return (
    <div data-figure-panel="readout" data-figure-readout={data.label} style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.text }}>
      {data.label}: <strong>{formatValue(data.value, data.format)}</strong>
    </div>
  );
}

export function FigurePanel({ data, label, showTable, model }: { data: PanelData; label?: string; showTable: boolean; model?: FigurePanelModel }) {
  if (data.kind === "function_plot") return <FunctionPlot data={data} showTable={showTable} />;
  if (data.kind === "pmf_bars") return <PmfBars data={data} showTable={showTable} />;
  if (data.kind === "linear_map_2d") return <LinearMap data={data} label={label ?? ""} showTable={showTable} />;
  // RW5b (AdvancedPanels.tsx).
  if (data.kind === "heatmap_2d") return <HeatmapPanelView data={data} showTable={showTable} />;
  if (data.kind === "vector_field_2d") return <VectorFieldPanelView data={data} showTable={showTable} />;
  if (data.kind === "trajectory_2d" || data.kind === "iterate_2d") {
    const axes = model && (model.kind === "trajectory_2d" || model.kind === "iterate_2d") ? { x: model.x, y: model.y } : null;
    return <PathPanelView data={data} axes={axes} showTable={showTable} />;
  }
  return <Readout data={data} />;
}
