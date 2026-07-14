// Two time-aligned lanes for the "Will I be ready?" hero (spec §4.1). Demonstrated
// coverage and predicted recall are different quantities and NEVER share an axis:
//
//   Demonstrated lane (top): a step line of capability-matched certification counts
//   (demonstratedCount / total). Non-monotone — corrections render as visible steps
//   down, annotated with a ▽ glyph so the drop is not carried by color alone.
//
//   Ready lane (bottom): the historical predicted-recall estimate (readyMean) plus the
//   dotted do-nothing decay line (projectedReadyMean over projection points — FSRS
//   retrievability decayed to the due date). Target-recall reference line and due-date
//   tick live in THIS lane only; the target has no meaning for the Demonstrated lane.
//
// No trailing-window least-squares extrapolation — four noisy points fit linearly is a
// fabricated trend. The projection comes entirely from the backend do-nothing series,
// and is withheld outright when no facet carries FSRS decay information (decayEstimated
// == 0): "no decay information is not the same as no decay."

import type { GoalSeriesPointDto } from "../api/dto";
import { COLOR, FONT_MONO } from "./term";

const pctText = (v: number | null | undefined): string =>
  v == null ? "—" : `${Math.round(v * 100)}%`;

function daysBetween(fromMs: number, toMs: number): number {
  return Math.round((toMs - fromMs) / 86_400_000);
}

// One-sentence text equivalent of the hero for screen readers (spec §4.13).
export function trajectorySummary(
  series: GoalSeriesPointDto[],
  dueAt: string | null,
  targetRecall?: number
): string {
  const valid = series.filter((p) => !Number.isNaN(Date.parse(p.at)));
  if (valid.length === 0) return "Not enough history yet to draw a trajectory.";
  const hist = valid.filter((p) => !p.projection);
  const last = hist[hist.length - 1] ?? valid[valid.length - 1];
  const parts: string[] = [];
  if (last?.demonstratedCount != null && last.total != null) {
    parts.push(`Demonstrated ${last.demonstratedCount} of ${last.total} facets`);
  }
  if (last?.readyMean != null) {
    let ready = `predicted recall now ${pctText(last.readyMean)}`;
    if (targetRecall != null) ready += `, target ${pctText(targetRecall)}`;
    parts.push(ready);
  }
  const decayPts = valid.filter((p) => p.projection && p.projectedReadyMean != null);
  const anyDecay = valid.some((p) => (p.decayEstimated ?? 0) > 0);
  const dueT = dueAt && !Number.isNaN(Date.parse(dueAt)) ? Date.parse(dueAt) : null;
  if (anyDecay && decayPts.length > 0) {
    const end = decayPts[decayPts.length - 1];
    let s = `if nothing is practiced, decay projects ${pctText(end.projectedReadyMean)}`;
    if (dueT != null) s += ` by the due date in ${Math.max(0, daysBetween(Date.now(), dueT))} days`;
    parts.push(s);
  } else {
    parts.push("no decay projection — not enough retrievability history");
  }
  return parts.join("; ") + ".";
}

export function GoalTrajectoryChart({
  series,
  dueAt,
  targetRecall,
  width = 340
}: {
  series: GoalSeriesPointDto[];
  dueAt: string | null;
  targetRecall?: number;
  width?: number;
  height?: number;
}) {
  const valid = series.filter((p) => !Number.isNaN(Date.parse(p.at)));
  const hist = valid
    .filter((p) => !p.projection)
    .map((p) => ({
      t: Date.parse(p.at),
      demonstrated: p.demonstratedCount ?? 0,
      total: p.total ?? 0,
      ready: p.readyMean
    }));

  if (hist.length < 2) {
    return (
      <div style={{ fontSize: 11, color: COLOR.textFaint, fontFamily: FONT_MONO, padding: "8px 0" }}>
        not enough history yet — trajectory appears after a couple of sessions
      </div>
    );
  }

  const decay = valid
    .filter((p) => p.projection && p.projectedReadyMean != null)
    .map((p) => ({ t: Date.parse(p.at), ready: p.projectedReadyMean as number }));

  // Model coverage (carried per point; identical across projection points). Read the
  // last valid point so the disclosure matches whatever the projection was built from.
  const lastValid = valid[valid.length - 1];
  const decayEstimated = lastValid?.decayEstimated ?? 0;
  const heldFlat = lastValid?.heldFlat ?? 0;
  const showProjection = decayEstimated > 0 && decay.length > 0;

  // ── layout ──
  const padL = 4;
  const padR = 52; // room for the ready-lane forecast label
  const demoLaneH = 40;
  const laneGap = 20;
  const readyLaneH = 52;
  const padT = 6;
  const padB = 14;
  const height = padT + demoLaneH + laneGap + readyLaneH + padB;
  const plotW = width - padL - padR;

  // ── shared time axis ──
  const firstT = hist[0].t;
  const dueT = dueAt && !Number.isNaN(Date.parse(dueAt)) ? Date.parse(dueAt) : null;
  const lastT = Math.max(
    hist[hist.length - 1].t,
    decay.length ? decay[decay.length - 1].t : 0,
    dueT ?? 0
  );
  const spanT = Math.max(1, lastT - firstT);
  const xOf = (t: number) => padL + ((t - firstT) / spanT) * plotW;

  // ── demonstrated lane (top) ──
  const demoTop = padT;
  const demoBot = padT + demoLaneH;
  const totalMax = Math.max(1, ...hist.map((p) => p.total), ...hist.map((p) => p.demonstrated));
  const demoY = (count: number) => demoBot - (Math.max(0, Math.min(totalMax, count)) / totalMax) * demoLaneH;

  // step-after path: hold each level until the next checkpoint, then step.
  const demoPath = hist
    .map((p, i) => {
      const x = xOf(p.t);
      const y = demoY(p.demonstrated);
      if (i === 0) return `M ${x.toFixed(1)} ${y.toFixed(1)}`;
      const prevY = demoY(hist[i - 1].demonstrated);
      return `L ${x.toFixed(1)} ${prevY.toFixed(1)} L ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");
  const demoLast = hist[hist.length - 1];

  // ── ready lane (bottom) ──
  const readyTop = demoBot + laneGap;
  const readyBot = readyTop + readyLaneH;
  const readyY = (frac: number) => readyBot - Math.max(0, Math.min(1, frac)) * readyLaneH;

  const readyHist = hist.filter((p) => p.ready != null) as Array<{ t: number; ready: number }>;
  const readyPath = readyHist
    .map((p, i) => `${i === 0 ? "M" : "L"} ${xOf(p.t).toFixed(1)} ${readyY(p.ready).toFixed(1)}`)
    .join(" ");

  // decay line: anchor on the last historical ready point for visual continuity.
  const decayAnchor = readyHist.length ? readyHist[readyHist.length - 1] : null;
  const decaySeq = decayAnchor ? [decayAnchor, ...decay] : decay;
  const decayPath = decaySeq
    .map((p, i) => `${i === 0 ? "M" : "L"} ${xOf(p.t).toFixed(1)} ${readyY(p.ready).toFixed(1)}`)
    .join(" ");
  const decayEnd = decay.length ? decay[decay.length - 1] : null;

  const summary = trajectorySummary(series, dueAt, targetRecall);

  return (
    <div>
      <svg width={width} height={height} style={{ display: "block", overflow: "visible" }} role="img" aria-label={summary}>
        <title>{summary}</title>

        {/* ── demonstrated lane ── */}
        <text x={padL} y={demoTop - 0} dominantBaseline="hanging" fill={COLOR.textFaint} fontFamily={FONT_MONO} fontSize={9} letterSpacing={0.5}>
          DEMONSTRATED
        </text>
        <line x1={padL} y1={demoBot} x2={padL + plotW} y2={demoBot} stroke={COLOR.border} strokeWidth={1} />
        <path d={demoPath} fill="none" stroke={COLOR.green} strokeWidth={1.5} />
        {hist.map((p, i) => {
          const stepDown = i > 0 && p.demonstrated < hist[i - 1].demonstrated;
          const x = xOf(p.t);
          const y = demoY(p.demonstrated);
          return (
            <g key={`d${i}`}>
              <circle cx={x} cy={y} r={2} fill={COLOR.green} />
              {stepDown ? (
                // ▽ glyph marks a correction (a step down) — not color alone.
                <path d={`M ${x - 3.5} ${y - 8} L ${x + 3.5} ${y - 8} L ${x} ${y - 2.5} Z`} fill={COLOR.pink} stroke={COLOR.pink} strokeWidth={0.5}>
                  <title>correction — demonstrated count dropped to {p.demonstrated}</title>
                </path>
              ) : null}
            </g>
          );
        })}
        <text x={xOf(demoLast.t) + 5} y={demoY(demoLast.demonstrated) + 3} fill={COLOR.green} fontFamily={FONT_MONO} fontSize={10}>
          {demoLast.demonstrated}/{demoLast.total}
        </text>

        {/* ── ready lane ── */}
        <text x={padL} y={readyTop - 10} fill={COLOR.textFaint} fontFamily={FONT_MONO} fontSize={9} letterSpacing={0.5}>
          READY (predicted recall)
        </text>
        <line x1={padL} y1={readyBot} x2={padL + plotW} y2={readyBot} stroke={COLOR.border} strokeWidth={1} />

        {/* target-recall reference line — ready lane only */}
        {targetRecall != null ? (
          <>
            <line x1={padL} y1={readyY(targetRecall)} x2={padL + plotW} y2={readyY(targetRecall)} stroke={COLOR.greenSoft} strokeWidth={1} strokeDasharray="2 3" opacity={0.6} />
            <text x={padL + plotW + 3} y={readyY(targetRecall) + 3} fill={COLOR.greenSoft} fontFamily={FONT_MONO} fontSize={9}>
              tgt {pctText(targetRecall)}
            </text>
          </>
        ) : null}

        {/* due-date vertical tick — ready lane only */}
        {dueT != null ? (
          <>
            <line x1={xOf(dueT)} y1={readyTop} x2={xOf(dueT)} y2={readyBot} stroke={COLOR.borderStrong} strokeWidth={1} strokeDasharray="2 3" />
            <text x={xOf(dueT)} y={readyBot + 11} fill={COLOR.textFaint} fontFamily={FONT_MONO} fontSize={9} textAnchor="middle">
              due
            </text>
          </>
        ) : null}

        {/* do-nothing decay projection (dotted) — only when a facet carries decay info */}
        {showProjection && decayEnd ? (
          <>
            <path d={decayPath} fill="none" stroke={COLOR.textDim} strokeWidth={1.25} strokeDasharray="2 3" />
            <circle cx={xOf(decayEnd.t)} cy={readyY(decayEnd.ready)} r={2.2} fill={COLOR.textDim} />
            <text x={xOf(decayEnd.t) + 5} y={readyY(decayEnd.ready) + 3} fill={COLOR.textDim} fontFamily={FONT_MONO} fontSize={10}>
              {pctText(decayEnd.ready)}
            </text>
          </>
        ) : null}

        {/* historical ready line */}
        <path d={readyPath} fill="none" stroke={COLOR.amber} strokeWidth={1.5} />
        {readyHist.map((p, i) => (
          <circle key={`r${i}`} cx={xOf(p.t)} cy={readyY(p.ready)} r={2.2} fill={COLOR.amber} />
        ))}
      </svg>

      {/* model-coverage disclosure caption */}
      <div style={{ marginTop: 4, fontSize: 10, color: COLOR.textFaint, fontFamily: FONT_MONO, lineHeight: 1.5 }}>
        {showProjection
          ? `dotted line: do-nothing decay · estimated from ${decayEstimated} of ${decayEstimated + heldFlat} facets; ${heldFlat} held flat — not enough history.`
          : heldFlat > 0
            ? `no decay projection — ${heldFlat} facets held flat, not enough retrievability history yet.`
            : "no decay projection yet."}
      </div>

      {/* text equivalent for screen readers (spec §4.13) */}
      <span style={{ position: "absolute", width: 1, height: 1, overflow: "hidden", clip: "rect(0 0 0 0)" }}>{summary}</span>
    </div>
  );
}
