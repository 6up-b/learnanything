import { useMemo, useRef, useState } from "react";
import type { KnowledgeMapHistory, KnowledgeMapPoint } from "../api/dto";
import { COLOR, Faint, FONT_MONO } from "../components/term";
import { masteryTone } from "../app/algoConfig";

// Strata view — the chronicle's replacement. The latent learner state is a
// belief (mastery mean per learning object) evolving in time, so draw exactly
// that: one row per LO, x = time, and inside each row the mastery step-series
// as a micro line+area whose height and color are the belief at that instant.
// Rows are ordered by projecting each LO's embedding centroid onto the
// principal axis of the map, grouped under their concept — latent-space
// neighbors sit on adjacent rows, so the amber frontier crossings (dots where
// a trajectory first clears FRONTIER_LEVEL) trace the mastery wavefront
// diagonally across the whole image instead of hiding behind a scrubber.
//
// Attempts are ticks on the row baseline colored by correctness (diamonds for
// probes); rows with no belief yet render as a dashed void — visible
// unexplored territory, not absence. A stacked band up top aggregates the
// portfolio: how many LOs sat in each mastery band (or untried) at every
// moment. All of time is visible at once; a crosshair gives exact dates.

const DEFAULT_W = 860;
const LABEL_W = 168;
const STAT_W = 84;
const PLOT_X = LABEL_W;
const AGG_H = 64;
const AXIS_H = 18;
const ROW_H = 20;
const CONCEPT_H = 18;
const FRONTIER_LEVEL = 0.7;
const AGG_SAMPLES = 140;

const dateLabel = (tMs: number) => new Date(tMs).toISOString().slice(0, 10);

function correctnessTone(correctness: number | null): string {
  if (correctness == null) return COLOR.textFaint;
  if (correctness >= 0.75) return COLOR.green;
  if (correctness >= 0.35) return COLOR.amber;
  return COLOR.red;
}

interface LoRow {
  loId: string;
  conceptId: string | null;
  points: KnowledgeMapPoint[];
  /** step series of belief updates, time-sorted */
  series: Array<{ tMs: number; mastery: number }>;
  attempts: Array<{ itemId: string; tMs: number; correctness: number | null; isProbe: boolean; type: string; hints: number }>;
  /** representative practice item for row-level hover/select */
  repItemId: string;
  currentMastery: number | null;
  currentVariance: number | null;
  proj: number;
}

interface StrataData {
  rows: LoRow[];
  /** concept groups in render order: label + member rows */
  groups: Array<{ conceptId: string | null; rows: LoRow[] }>;
  startMs: number;
  endMs: number;
  spanMs: number;
  hasHistory: boolean;
}

function buildStrata(points: KnowledgeMapPoint[], history: KnowledgeMapHistory, nowMs: number): StrataData {
  const pointById = new Map(points.map((p) => [p.id, p] as const));

  // Group practice items into LO rows.
  const rowByLo = new Map<string, LoRow>();
  for (const point of points) {
    let row = rowByLo.get(point.learningObjectId);
    if (!row) {
      row = {
        loId: point.learningObjectId,
        conceptId: point.conceptId,
        points: [],
        series: [],
        attempts: [],
        repItemId: point.id,
        currentMastery: null,
        currentVariance: null,
        proj: 0
      };
      rowByLo.set(point.learningObjectId, row);
    }
    row.points.push(point);
    if (row.conceptId == null) row.conceptId = point.conceptId;
    if (row.currentMastery == null) row.currentMastery = point.mastery;
    if (row.currentVariance == null) row.currentVariance = point.variance;
  }

  for (const lo of history.learningObjects) {
    const row = rowByLo.get(lo.id);
    if (!row) continue;
    row.series = lo.series
      .map((s) => ({ tMs: Date.parse(s.t), mastery: s.mastery }))
      .filter((s) => Number.isFinite(s.tMs))
      .sort((a, b) => a.tMs - b.tMs);
  }

  const attemptCount = new Map<string, number>();
  for (const attempt of history.attempts) {
    const tMs = Date.parse(attempt.t);
    if (!Number.isFinite(tMs)) continue;
    const row = rowByLo.get(attempt.learningObjectId);
    if (!row) continue;
    const point = pointById.get(attempt.practiceItemId);
    row.attempts.push({
      itemId: attempt.practiceItemId,
      tMs,
      correctness: attempt.correctness,
      isProbe: point?.isProbe ?? false,
      type: attempt.attemptType,
      hints: attempt.hintsUsed
    });
    attemptCount.set(attempt.practiceItemId, (attemptCount.get(attempt.practiceItemId) ?? 0) + 1);
  }

  const rows = [...rowByLo.values()];
  for (const row of rows) {
    row.attempts.sort((a, b) => a.tMs - b.tMs);
    // Representative item = the one practiced most (its detail panel is the
    // most informative stand-in for the whole row).
    let best = row.points[0];
    for (const p of row.points) {
      if ((attemptCount.get(p.id) ?? 0) > (attemptCount.get(best.id) ?? 0)) best = p;
    }
    row.repItemId = best.id;
  }

  // Order rows by the principal axis of the LO centroids in the 2D embedding —
  // a 1D seriation that keeps latent-space neighbors on adjacent rows.
  const centroids = rows.map((row) => {
    const cx = row.points.reduce((s, p) => s + p.x, 0) / row.points.length;
    const cy = row.points.reduce((s, p) => s + p.y, 0) / row.points.length;
    return { row, cx, cy };
  });
  const mx = centroids.reduce((s, c) => s + c.cx, 0) / Math.max(centroids.length, 1);
  const my = centroids.reduce((s, c) => s + c.cy, 0) / Math.max(centroids.length, 1);
  let cxx = 0;
  let cyy = 0;
  let cxy = 0;
  for (const c of centroids) {
    cxx += (c.cx - mx) ** 2;
    cyy += (c.cy - my) ** 2;
    cxy += (c.cx - mx) * (c.cy - my);
  }
  const angle = 0.5 * Math.atan2(2 * cxy, cxx - cyy);
  const ux = Math.cos(angle);
  const uy = Math.sin(angle);
  for (const c of centroids) c.row.proj = (c.cx - mx) * ux + (c.cy - my) * uy;

  // Group by concept; concepts ordered by their mean projection, rows within
  // a concept by projection.
  const byConcept = new Map<string | null, LoRow[]>();
  for (const row of rows) {
    const bucket = byConcept.get(row.conceptId) ?? [];
    bucket.push(row);
    byConcept.set(row.conceptId, bucket);
  }
  const groups = [...byConcept.entries()].map(([conceptId, members]) => {
    members.sort((a, b) => a.proj - b.proj);
    const mean = members.reduce((s, r) => s + r.proj, 0) / members.length;
    return { conceptId, rows: members, mean };
  });
  groups.sort((a, b) => a.mean - b.mean);

  const times: number[] = [];
  for (const row of rows) {
    for (const s of row.series) times.push(s.tMs);
    for (const a of row.attempts) times.push(a.tMs);
  }
  const hasHistory = times.length > 0;
  const startMs = hasHistory ? Math.min(...times) : nowMs - 24 * 3600 * 1000;
  const endMs = Math.max(nowMs, hasHistory ? Math.max(...times) : nowMs);
  const spanMs = Math.max(endMs - startMs, 60 * 60 * 1000);

  return {
    rows,
    groups: groups.map(({ conceptId, rows: members }) => ({ conceptId, rows: members })),
    startMs,
    endMs,
    spanMs,
    hasHistory
  };
}

/** Step-function belief at time t; null before the first update. */
function masteryAt(series: LoRow["series"], tMs: number): number | null {
  if (series.length === 0 || series[0].tMs > tMs) return null;
  let value = series[0].mastery;
  for (const s of series) {
    if (s.tMs > tMs) break;
    value = s.mastery;
  }
  return value;
}

function shortenId(id: string, max: number): string {
  return id.length <= max ? id : `…${id.slice(id.length - max + 1)}`;
}

export function KnowledgeStrataView({
  points,
  history,
  selected,
  onSelect,
  onInspect,
  width
}: {
  points: KnowledgeMapPoint[];
  history: KnowledgeMapHistory;
  selected: string | null;
  onSelect: (id: string) => void;
  onInspect: (id: string) => void;
  /** Pane width in CSS pixels; the timeline stretches to fill it. */
  width?: number;
}) {
  // Width follows the pane (the plot band absorbs the slack); height stays
  // content-driven — the strata are a list, so they scroll rather than squash.
  const W = width && width > 0 ? width : DEFAULT_W;
  const PLOT_W = W - LABEL_W - STAT_W;
  const nowMs = useMemo(() => Date.now(), []);
  const data = useMemo(() => buildStrata(points, history, nowMs), [points, history, nowMs]);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [hoverT, setHoverT] = useState<number | null>(null);

  const tx = (tMs: number) => PLOT_X + ((tMs - data.startMs) / data.spanMs) * PLOT_W;

  // Layout: aggregate band, axis, then concept groups (header + member rows).
  const layout = useMemo(() => {
    let y = AGG_H + 12 + AXIS_H;
    const headers: Array<{ y: number; conceptId: string | null; count: number }> = [];
    const rowY = new Map<string, number>();
    for (const group of data.groups) {
      headers.push({ y, conceptId: group.conceptId, count: group.rows.length });
      y += CONCEPT_H;
      for (const row of group.rows) {
        rowY.set(row.loId, y);
        y += ROW_H;
      }
      y += 6;
    }
    return { headers, rowY, height: y + 6 };
  }, [data]);

  // Aggregate portfolio drift: at each sample time, how many LOs sit in each
  // band (or have no belief yet). Stacked bottom-up: strong, developing, weak,
  // untried — so "solid ground" accumulates from the floor.
  const aggregate = useMemo(() => {
    const total = data.rows.length;
    if (total === 0) return null;
    const stacks: number[][] = [];
    for (let i = 0; i <= AGG_SAMPLES; i += 1) {
      const t = data.startMs + (i / AGG_SAMPLES) * data.spanMs;
      let strong = 0;
      let developing = 0;
      let weak = 0;
      for (const row of data.rows) {
        const m = masteryAt(row.series, t);
        if (m == null) continue;
        if (m >= FRONTIER_LEVEL) strong += 1;
        else if (m >= 0.4) developing += 1;
        else weak += 1;
      }
      stacks.push([strong, developing, weak, total - strong - developing - weak]);
    }
    const yTop = 8;
    const yOf = (count: number) => yTop + AGG_H - (count / total) * AGG_H;
    const bands = ["strong", "developing", "weak", "untried"] as const;
    const paths: Record<(typeof bands)[number], string> = { strong: "", developing: "", weak: "", untried: "" };
    bands.forEach((band, bi) => {
      const lower: string[] = [];
      const upper: string[] = [];
      for (let i = 0; i <= AGG_SAMPLES; i += 1) {
        const x = PLOT_X + (i / AGG_SAMPLES) * PLOT_W;
        const below = stacks[i].slice(0, bi).reduce((s, v) => s + v, 0);
        lower.push(`${x.toFixed(1)} ${yOf(below).toFixed(1)}`);
        upper.push(`${x.toFixed(1)} ${yOf(below + stacks[i][bi]).toFixed(1)}`);
      }
      paths[band] = `M ${lower.join(" L ")} L ${upper.reverse().join(" L ")} Z`;
    });
    return { paths, yTop, total };
  }, [data]);

  const gridTimes = useMemo(() => {
    const ticks: number[] = [];
    const n = 5;
    for (let i = 0; i <= n; i += 1) ticks.push(data.startMs + (i / n) * data.spanMs);
    return ticks;
  }, [data]);

  const selectedLo = selected ? points.find((p) => p.id === selected)?.learningObjectId ?? null : null;

  const onMove = (event: React.MouseEvent<SVGSVGElement>) => {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = ((event.clientX - rect.left) / rect.width) * W;
    if (x < PLOT_X || x > PLOT_X + PLOT_W) {
      setHoverT(null);
      return;
    }
    setHoverT(data.startMs + ((x - PLOT_X) / PLOT_W) * data.spanMs);
  };

  const height = layout.height;
  const axisY = AGG_H + 12 + AXIS_H - 6;

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
      <svg
        ref={svgRef}
        className="noselect-canvas"
        width={W}
        height={height}
        viewBox={`0 0 ${W} ${height}`}
        onMouseMove={onMove}
        onMouseLeave={() => setHoverT(null)}
        style={{ fontFamily: FONT_MONO, maxWidth: "100%", height: "auto", userSelect: "none", WebkitUserSelect: "none" }}
      >
        {/* ── aggregate portfolio band ─────────────────────────────────── */}
        {aggregate ? (
          <g>
            <text x={PLOT_X - 10} y={aggregate.yTop + 10} textAnchor="end" fontSize={10} fill={COLOR.textDim}>
              portfolio
            </text>
            <text x={PLOT_X - 10} y={aggregate.yTop + 24} textAnchor="end" fontSize={9} fill={COLOR.textFaint}>
              {aggregate.total} LOs
            </text>
            <path d={aggregate.paths.untried} fill={COLOR.borderStrong} opacity={0.25} />
            <path d={aggregate.paths.weak} fill={COLOR.red} opacity={0.3} />
            <path d={aggregate.paths.developing} fill={COLOR.amber} opacity={0.32} />
            <path d={aggregate.paths.strong} fill={COLOR.green} opacity={0.38} />
            <rect x={PLOT_X} y={aggregate.yTop} width={PLOT_W} height={AGG_H} fill="none" stroke={COLOR.border} strokeWidth={1} />
          </g>
        ) : null}

        {/* ── time axis + gridlines ────────────────────────────────────── */}
        {gridTimes.map((t, i) => {
          const x = tx(t);
          return (
            <g key={`grid-${i}`}>
              <line x1={x} y1={axisY} x2={x} y2={height - 8} stroke={COLOR.border} strokeWidth={1} opacity={0.35} />
              <text
                x={x}
                y={axisY - 4}
                textAnchor={i === 0 ? "start" : i === gridTimes.length - 1 ? "end" : "middle"}
                fontSize={9}
                fill={COLOR.textFaint}
              >
                {i === gridTimes.length - 1 ? "now" : dateLabel(t)}
              </text>
            </g>
          );
        })}

        {/* ── concept groups + LO strata ───────────────────────────────── */}
        {layout.headers.map((header) => (
          <g key={`concept-${header.conceptId ?? "none"}`}>
            <text x={8} y={header.y + CONCEPT_H - 6} fontSize={10} fill={COLOR.textDim}>
              {header.conceptId ? shortenId(header.conceptId, 30) : "unassigned"}
            </text>
            <line
              x1={8}
              y1={header.y + CONCEPT_H - 2}
              x2={W - 8}
              y2={header.y + CONCEPT_H - 2}
              stroke={COLOR.border}
              strokeWidth={1}
              opacity={0.6}
            />
          </g>
        ))}

        {data.rows.map((row) => {
          const y = layout.rowY.get(row.loId);
          if (y == null) return null;
          const baseY = y + ROW_H - 4;
          const topPad = 3;
          const mY = (m: number) => baseY - m * (ROW_H - 4 - topPad);
          const isSelectedRow = selectedLo === row.loId;
          const untried = row.series.length === 0;

          // Belief trajectory as a step path; area fill segments per step so
          // each stretch carries its own band color.
          const stepSegs: Array<{ x0: number; x1: number; m: number }> = [];
          for (let i = 0; i < row.series.length; i += 1) {
            const s = row.series[i];
            const next = row.series[i + 1];
            stepSegs.push({ x0: tx(s.tMs), x1: next ? tx(next.tMs) : tx(data.endMs), m: s.mastery });
          }

          // Frontier crossings (upward) → amber wavefront dots.
          const crossings: number[] = [];
          for (let i = 0; i < row.series.length; i += 1) {
            const prev = i === 0 ? 0 : row.series[i - 1].mastery;
            if (prev < FRONTIER_LEVEL && row.series[i].mastery >= FRONTIER_LEVEL) crossings.push(row.series[i].tMs);
          }

          const tone = row.currentMastery != null ? masteryTone(row.currentMastery, COLOR) : COLOR.textFaint;
          const hoverM = hoverT != null ? masteryAt(row.series, hoverT) : null;

          return (
            <g
              key={row.loId}
              onMouseEnter={() => onSelect(row.repItemId)}
              style={{ cursor: "pointer" }}
            >
              {/* hit area + row hover/selection wash */}
              <rect
                x={0}
                y={y}
                width={W}
                height={ROW_H}
                fill={isSelectedRow ? COLOR.bgElev : "transparent"}
                opacity={isSelectedRow ? 0.7 : 1}
                onClick={() => onInspect(row.loId)}
              />
              <text
                x={LABEL_W - 10}
                y={y + ROW_H / 2 + 3.5}
                textAnchor="end"
                fontSize={10}
                fill={isSelectedRow ? COLOR.amber : untried ? COLOR.textFaint : COLOR.textDim}
                style={{ pointerEvents: "none" }}
              >
                {shortenId(row.loId, 24)}
              </text>

              {/* pre-belief void: dashed baseline up to the first update */}
              <line
                x1={PLOT_X}
                y1={baseY}
                x2={untried ? PLOT_X + PLOT_W : tx(row.series[0].tMs)}
                y2={baseY}
                stroke={COLOR.borderStrong}
                strokeWidth={1}
                strokeDasharray="2 4"
                opacity={0.5}
              />
              {/* faint frontier reference inside the row */}
              {!untried ? (
                <line
                  x1={tx(row.series[0].tMs)}
                  y1={mY(FRONTIER_LEVEL)}
                  x2={PLOT_X + PLOT_W}
                  y2={mY(FRONTIER_LEVEL)}
                  stroke={COLOR.amber}
                  strokeWidth={0.6}
                  strokeDasharray="1 4"
                  opacity={0.3}
                />
              ) : null}

              {/* belief trajectory: color-banded area + step line */}
              {stepSegs.map((seg, i) => {
                const segTone = masteryTone(seg.m, COLOR);
                return (
                  <g key={`seg-${i}`} style={{ pointerEvents: "none" }}>
                    <rect
                      x={seg.x0}
                      y={mY(seg.m)}
                      width={Math.max(seg.x1 - seg.x0, 0.5)}
                      height={baseY - mY(seg.m)}
                      fill={segTone}
                      opacity={0.1 + 0.16 * seg.m}
                    />
                    <line x1={seg.x0} y1={mY(seg.m)} x2={seg.x1} y2={mY(seg.m)} stroke={segTone} strokeWidth={1.4} opacity={0.95} />
                    {i > 0 ? (
                      <line
                        x1={seg.x0}
                        y1={mY(stepSegs[i - 1].m)}
                        x2={seg.x0}
                        y2={mY(seg.m)}
                        stroke={segTone}
                        strokeWidth={1}
                        opacity={0.7}
                      />
                    ) : null}
                  </g>
                );
              })}

              {/* frontier-crossing wavefront dots */}
              {crossings.map((t, i) => (
                <circle
                  key={`cross-${i}`}
                  cx={tx(t)}
                  cy={mY(FRONTIER_LEVEL)}
                  r={2.6}
                  fill={COLOR.amber}
                  stroke={COLOR.bg}
                  strokeWidth={1}
                  style={{ pointerEvents: "none" }}
                />
              ))}

              {/* attempt ticks on the baseline (diamonds = probes) */}
              {row.attempts.map((attempt, i) => {
                const x = tx(attempt.tMs);
                const c = correctnessTone(attempt.correctness);
                return (
                  <g
                    key={`at-${i}`}
                    onMouseEnter={(event) => {
                      event.stopPropagation();
                      onSelect(attempt.itemId);
                    }}
                    onClick={(event) => {
                      event.stopPropagation();
                      onInspect(attempt.itemId);
                    }}
                    style={{ cursor: "pointer" }}
                  >
                    {attempt.isProbe ? (
                      <path
                        d={`M ${x} ${baseY - 3} L ${x + 3} ${baseY} L ${x} ${baseY + 3} L ${x - 3} ${baseY} Z`}
                        fill={c}
                        opacity={0.95}
                      />
                    ) : (
                      <line x1={x} y1={baseY - 3.5} x2={x} y2={baseY + 2.5} stroke={c} strokeWidth={1.6} opacity={0.95} />
                    )}
                    <rect x={x - 3.5} y={y} width={7} height={ROW_H} fill="transparent" />
                    <title>
                      {[
                        points.find((p) => p.id === attempt.itemId)?.title ?? attempt.itemId,
                        `${dateLabel(attempt.tMs)} · ${attempt.type}`,
                        attempt.correctness != null ? `correctness ${attempt.correctness.toFixed(2)}` : "unscored",
                        attempt.hints > 0 ? `${attempt.hints} hint${attempt.hints === 1 ? "" : "s"}` : null
                      ]
                        .filter(Boolean)
                        .join("\n")}
                    </title>
                  </g>
                );
              })}

              {/* current belief stat gutter */}
              <text
                x={W - 12}
                y={y + ROW_H / 2 + 3.5}
                textAnchor="end"
                fontSize={10}
                fill={tone}
                style={{ pointerEvents: "none" }}
              >
                {hoverT != null && hoverM != null
                  ? hoverM.toFixed(2)
                  : row.currentMastery != null
                    ? `${row.currentMastery.toFixed(2)}${row.currentVariance != null ? ` ±${Math.sqrt(row.currentVariance).toFixed(2)}` : ""}`
                    : "—"}
              </text>
            </g>
          );
        })}

        {/* ── crosshair ────────────────────────────────────────────────── */}
        {hoverT != null ? (
          <g style={{ pointerEvents: "none" }}>
            <line x1={tx(hoverT)} y1={aggregate ? aggregate.yTop : axisY} x2={tx(hoverT)} y2={height - 8} stroke={COLOR.cyan} strokeWidth={1} opacity={0.55} />
            <text
              x={Math.min(Math.max(tx(hoverT), PLOT_X + 34), PLOT_X + PLOT_W - 34)}
              y={axisY + 10}
              textAnchor="middle"
              fontSize={9}
              fill={COLOR.cyan}
            >
              {dateLabel(hoverT)}
            </text>
          </g>
        ) : null}
      </svg>

      {!data.hasHistory ? <Faint>no attempts yet — rows show the unexplored material</Faint> : null}
    </div>
  );
}
