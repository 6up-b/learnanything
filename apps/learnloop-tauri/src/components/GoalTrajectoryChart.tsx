// Inline-SVG week-by-week goal trajectory, with a dotted linear forecast to the
// due date. Plots predicted recall (continuous, comparable to the targetRecall
// reference line); falls back to the legacy on-track fraction when the sidecar
// predates the dual-axis report. Green rings mark milestone weeks where the
// certified-facet count increased. No chart libs — terminal-styled: amber
// achieved series, dimmed dashed forecast, a vertical tick at the due date.
// Y domain is a fixed 0–100%. Honest by construction: fewer than two real
// points renders a "not enough history yet" note instead of a fabricated line.

import type { GoalSeriesPointDto } from "../api/dto";
import { COLOR, FONT_MONO } from "./term";

interface FitPoint {
  t: number;
  frac: number;
}

// Least-squares slope/intercept over the trailing window (t in ms, frac 0–1).
function linearFit(points: FitPoint[]): { m: number; b: number } | null {
  const n = points.length;
  if (n < 2) return null;
  const t0 = points[0].t; // shift for numerical stability
  let sx = 0;
  let sy = 0;
  let sxx = 0;
  let sxy = 0;
  for (const p of points) {
    const x = (p.t - t0) / 86_400_000; // days since first
    sx += x;
    sy += p.frac;
    sxx += x * x;
    sxy += x * p.frac;
  }
  const denom = n * sxx - sx * sx;
  if (Math.abs(denom) < 1e-9) return null;
  const m = (n * sxy - sx * sy) / denom;
  const b = (sy - m * sx) / n;
  return { m, b };
}

export function GoalTrajectoryChart({
  series,
  dueAt,
  targetRecall,
  width = 340,
  height = 96
}: {
  series: GoalSeriesPointDto[];
  dueAt: string | null;
  targetRecall?: number;
  width?: number;
  height?: number;
}) {
  const metricOf = (p: GoalSeriesPointDto): number | null =>
    p.predictedRecallMean ?? p.onTrackFraction ?? null;
  const pts: Array<{ t: number; frac: number; certified: number }> = series
    .filter((p) => metricOf(p) != null && !Number.isNaN(Date.parse(p.at)))
    .map((p) => ({ t: Date.parse(p.at), frac: metricOf(p) as number, certified: p.certifiedCount ?? 0 }));

  if (pts.length < 2) {
    return (
      <div style={{ fontSize: 11, color: COLOR.textFaint, fontFamily: FONT_MONO, padding: "8px 0" }}>
        not enough history yet — trajectory appears after a couple of sessions
      </div>
    );
  }

  const padL = 4;
  const padR = 52; // room for the forecast label
  const padT = 8;
  const padB = 14;
  const plotW = width - padL - padR;
  const plotH = height - padT - padB;

  const firstT = pts[0].t;
  const lastT = pts[pts.length - 1].t;
  const dueT = dueAt && !Number.isNaN(Date.parse(dueAt)) ? Date.parse(dueAt) : null;
  const maxT = Math.max(lastT, dueT ?? lastT);
  const spanT = Math.max(1, maxT - firstT);

  const xOf = (t: number) => padL + ((t - firstT) / spanT) * plotW;
  const yOf = (frac: number) => padT + (1 - Math.max(0, Math.min(1, frac))) * plotH;

  const linePath = pts.map((p, i) => `${i === 0 ? "M" : "L"} ${xOf(p.t).toFixed(1)} ${yOf(p.frac).toFixed(1)}`).join(" ");

  // Forecast from the trailing window (last up-to-4 points) to the due date.
  const window = pts.slice(Math.max(0, pts.length - 4));
  const fit = linearFit(window);
  let forecast: { x: number; y: number; frac: number } | null = null;
  if (fit && dueT && dueT > lastT) {
    const days = (dueT - firstT) / 86_400_000;
    const projFrac = Math.max(0, Math.min(1, fit.m * days + fit.b));
    forecast = { x: xOf(dueT), y: yOf(projFrac), frac: projFrac };
  }

  const targetY = targetRecall != null ? yOf(targetRecall) : null;

  return (
    <svg width={width} height={height} style={{ display: "block", overflow: "visible" }}>
      {/* baseline + top gridlines */}
      <line x1={padL} y1={yOf(0)} x2={padL + plotW} y2={yOf(0)} stroke={COLOR.border} strokeWidth={1} />
      <line x1={padL} y1={yOf(1)} x2={padL + plotW} y2={yOf(1)} stroke={COLOR.border} strokeWidth={1} strokeDasharray="1 4" opacity={0.5} />

      {/* target recall reference line */}
      {targetY != null ? (
        <line x1={padL} y1={targetY} x2={padL + plotW} y2={targetY} stroke={COLOR.greenSoft} strokeWidth={1} strokeDasharray="2 3" opacity={0.55} />
      ) : null}

      {/* due-date vertical tick */}
      {dueT != null ? (
        <line x1={xOf(dueT)} y1={padT} x2={xOf(dueT)} y2={padT + plotH} stroke={COLOR.borderStrong} strokeWidth={1} strokeDasharray="2 3" />
      ) : null}

      {/* forecast (dotted) */}
      {forecast ? (
        <>
          <line
            x1={xOf(lastT)}
            y1={yOf(pts[pts.length - 1].frac)}
            x2={forecast.x}
            y2={forecast.y}
            stroke={COLOR.textDim}
            strokeWidth={1.25}
            strokeDasharray="3 3"
          />
          <path d={`M ${forecast.x - 4} ${forecast.y} L ${forecast.x} ${forecast.y - 4} L ${forecast.x + 4} ${forecast.y} L ${forecast.x} ${forecast.y + 4} Z`} fill={COLOR.textDim} />
          <text x={forecast.x + 6} y={forecast.y + 3} fill={COLOR.textDim} fontFamily={FONT_MONO} fontSize={10}>
            {Math.round(forecast.frac * 100)}%
          </text>
        </>
      ) : null}

      {/* achieved series */}
      <path d={linePath} fill="none" stroke={COLOR.amber} strokeWidth={1.5} />
      {pts.map((p, i) => (
        <circle key={i} cx={xOf(p.t)} cy={yOf(p.frac)} r={2.4} fill={COLOR.amber} />
      ))}

      {/* milestone rings: weeks where the certified-facet count grew */}
      {pts.map((p, i) =>
        i > 0 && p.certified > pts[i - 1].certified ? (
          <circle key={`m${i}`} cx={xOf(p.t)} cy={yOf(p.frac)} r={4.2} fill="none" stroke={COLOR.green} strokeWidth={1.4} />
        ) : null
      )}
    </svg>
  );
}
