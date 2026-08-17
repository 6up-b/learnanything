import { useMemo } from "react";
import type { DecayPressureDto, KnowledgeFacetField, KnowledgeFacetPoint } from "../api/dto";
import { COLOR, FONT_MONO } from "../components/term";
import { useScrollZoom } from "./scrollZoom";
import { depthFade, polyPath, project, useOrbitCamera, type Projected } from "./wire3d";

// KnowledgeWellView — a spacetime-curvature wireframe where settled knowledge
// is mass that bends the fabric. Unlike the legacy per-facet "mastery" well,
// exactly ONE continuous quantity owns the geometry:
//
//   wellDepth(facet) = ready · visibility(evidenceMass)
//
// i.e. a facet the model predicts you'll recall AND that has real evidence
// behind it pulls a deep well; high prediction with no evidence barely dimples
// the sheet; no evidence at all leaves the fabric flat — that flat plain is the
// frontier, where the equipotential contours bunch. This is an ambient surface,
// so leading with Ready is spec-legal (§1.1). Demonstrated is NEVER a second
// depth — it renders as a DISCRETE marker channel (a filled anchor bead vs a
// hollow ring) at each well bottom, so the two independent axes never share a
// continuous scale (§1.1). Decay honesty (§1.4/§1.6): a facet the FSRS model
// holds flat for lack of history is NOT given confident geometry — its sector
// is drawn with a dashed spoke and a hollow diamond, visibly distinct from an
// unexplored-but-solid frontier; and a still-relaxing well shows a faint ghost
// ring at its pre-decay (readyGhost) depth. No number is drawn on the fabric
// that isn't straight from the DTO; exact values live in the side panel.

// The view fills whatever box it is given; the viewBox is 1:1 with CSS pixels
// so labels and stroke weights keep their designed size as the well grows. The
// coefficients below reproduce the original 860×640 framing exactly, and the
// vertical term keeps the scene from outgrowing a short, wide pane.
const DEFAULT_W = 860;
const DEFAULT_H = 640;
const CENTER_LIFT = 0.047; // scene centre sits above the box centre (label room)
const SCALE_W = 0.273;
const SCALE_H = 0.42;

const DEPTH = 0.9;
const CENTER_BLEND = 0.28;
const PROFILE_POW = 1.55;
const EVIDENCE_K = 1.2; // evidenceMass at which visibility ≈ 0.5
const DEMO_THRESHOLD = 0.5; // demonstratedMass ≥ this ⇒ filled anchor bead
const DEEP_LEVEL = 0.4; // wellDepth ≥ this ⇒ "deep well" in the scene summary
const SHALLOW_LEVEL = 0.12; // below this ⇒ "flat frontier"
const BEAD_R = 0.52; // radius along each spoke where the anchor bead sits
const RING_RS = [0.14, 0.28, 0.42, 0.56, 0.7, 0.84, 1];
const CONTOUR_QS = [0.12, 0.24, 0.36, 0.48, 0.6, 0.72]; // fractions of DEPTH
const SPOKE_STEPS = 26;
const EASE = "stroke 0.22s ease, fill 0.22s ease, opacity 0.22s ease, stroke-width 0.22s ease";

const clamp01 = (value: number) => Math.max(0, Math.min(1, value));
const smooth = (t: number) => t * t * (3 - 2 * t);
const visibility = (evidenceMass: number) => evidenceMass / (evidenceMass + EVIDENCE_K);

type V3 = { x: number; y: number; z: number };

// Underscore-aware line wrapping for facet-id labels (kept from the old well).
function labelLines(facetId: string, maxChars = 20): string[] {
  const words = facetId.split("_");
  const lines: string[] = [];
  let current = "";
  for (const word of words) {
    const candidate = current ? `${current}_${word}` : word;
    if (candidate.length > maxChars && current) {
      lines.push(`${current}_`);
      current = word;
    } else {
      current = candidate;
    }
  }
  if (current) lines.push(current);
  return lines;
}

// Per-facet derived state that drives every visual channel. Computed once so
// the geometry and the markers agree and the scene summary is exact.
interface FacetState {
  point: KnowledgeFacetPoint;
  angle: number;
  vis: number;
  wellDepth: number; // ready · vis — the ONE quantity that bends the fabric
  ghostDepth: number; // readyGhost · vis — pre-decay depth (for the relax ghost)
  effectiveDepth: number; // geometry input: 0 when absent or held-flat
  demonstrated: boolean;
  // Instructed but not yet verified: a repair here was done with assistance and
  // the unassisted check it scheduled has not been answered. A THIRD marker
  // state between predicted and demonstrated — never counted as either, because
  // instructed work is not evidence and the whole point of the pending check is
  // that we do not yet know whether it stuck.
  instructed: boolean;
  absent: boolean; // no blueprint ⇒ content debt, not a learner gap (§1.7)
  noHistory: boolean; // FSRS-held-flat ⇒ must not get confident geometry (§1.4)
  crossesInDays: number | null;
  showGhost: boolean;
}

// Aggregate the per-(LO,facet) decay rows down to one verdict per facet.
function decayByFacet(decay: DecayPressureDto | null | undefined): Map<string, { hasHistory: boolean; crossesInDays: number | null }> {
  const out = new Map<string, { hasHistory: boolean; crossesInDays: number | null }>();
  for (const row of decay?.facets ?? []) {
    const prev = out.get(row.facetId);
    const crosses = [prev?.crossesInDays, row.crossesInDays].filter((v): v is number => v != null);
    out.set(row.facetId, {
      hasHistory: (prev?.hasHistory ?? false) || row.hasHistory,
      crossesInDays: crosses.length ? Math.min(...crosses) : null
    });
  }
  return out;
}

function buildStates(field: KnowledgeFacetField, decay: DecayPressureDto | null | undefined): FacetState[] {
  // Deterministic angular placement: sort by id so the well never reshuffles
  // between visits.
  const points = [...field.points].sort((a, b) => a.id.localeCompare(b.id));
  const N = points.length;
  const decayMap = decayByFacet(decay);
  return points.map((point, i) => {
    const vis = visibility(point.evidenceMass);
    const wellDepth = clamp01(point.ready) * vis;
    const ghostDepth = clamp01(point.readyGhost) * vis;
    const absent = !point.hasBlueprints;
    const entry = decayMap.get(point.id);
    // "Held flat for lack of history" only when the model actually saw this
    // facet and had no FSRS history to lean on. Facets absent from the decay
    // feed are treated as normal (the feed may be empty when unavailable).
    const noHistory = entry != null && !entry.hasHistory;
    const demonstrated = point.demonstratedMass >= DEMO_THRESHOLD;
    return {
      point,
      angle: -Math.PI / 2 + (i * 2 * Math.PI) / N,
      vis,
      wellDepth,
      ghostDepth,
      // Neither content debt nor an unbacked FSRS hold earns confident depth.
      effectiveDepth: absent || noHistory ? 0 : wellDepth,
      demonstrated,
      // Ranked BELOW demonstrated: a facet already carrying demonstrated credit
      // keeps its filled bead, and the pending check only ever adds a state to a
      // facet that has none — it can never take one away or add one.
      instructed: (point.coldCheckPending ?? false) && !demonstrated && !absent && !noHistory,
      absent,
      noHistory,
      crossesInDays: entry?.crossesInDays ?? null,
      showGhost: !absent && !noHistory && ghostDepth - wellDepth >= 0.01
    };
  });
}

interface WellGeometry {
  rings: V3[][];
  spokes: V3[][]; // one per facet, index-aligned with states
  contours: V3[][][]; // per level, list of contiguous runs
  beads: V3[];
  ghosts: Array<V3 | null>;
  labels: V3[];
}

function buildGeometry(states: FacetState[]): WellGeometry {
  const N = states.length;
  const meanDepth = states.reduce((sum, s) => sum + s.effectiveDepth, 0) / N;

  // Angular depth field: cosine interpolation of effectiveDepth between the
  // radially-placed facets, so the sheet is a smooth summed potential.
  const depthAtAngle = (theta: number): number => {
    const u = (((theta + Math.PI / 2) / (2 * Math.PI)) * N) % N;
    const uu = u < 0 ? u + N : u;
    const i0 = Math.floor(uu) % N;
    const t = uu - Math.floor(uu);
    const d0 = states[i0].effectiveDepth;
    const d1 = states[(i0 + 1) % N].effectiveDepth;
    const s = (1 - Math.cos(t * Math.PI)) / 2;
    return d0 + (d1 - d0) * s;
  };

  const surfaceZ = (theta: number, r: number): number => {
    const blend = smooth(clamp01(r / CENTER_BLEND));
    const d = meanDepth + (depthAtAngle(theta) - meanDepth) * blend;
    return -DEPTH * d * Math.pow(1 - clamp01(r), PROFILE_POW);
  };

  const polar = (theta: number, r: number, lift = 0): V3 => ({
    x: r * Math.cos(theta),
    y: r * Math.sin(theta),
    z: surfaceZ(theta, r) + lift
  });

  const ASAMP = Math.max(96, Math.min(168, N * 12));
  const thetaAt = (s: number) => -Math.PI / 2 + (s * 2 * Math.PI) / ASAMP;

  const rings = RING_RS.map((r) => {
    const pts: V3[] = [];
    for (let s = 0; s <= ASAMP; s += 1) pts.push(polar(thetaAt(s), r));
    return pts;
  });

  const spokeAt = (theta: number): V3[] => {
    const pts: V3[] = [];
    for (let s = 0; s <= SPOKE_STEPS; s += 1) pts.push(polar(theta, 0.02 + (s / SPOKE_STEPS) * 0.98));
    return pts;
  };
  const spokes = states.map((s) => spokeAt(s.angle));

  // Equipotential contours: scan each angular sample inward for the outermost
  // iso-depth crossing. Sectors shallower than a level produce pen-up gaps, so
  // the rings bunch tightly at the wall between a deep well and flat frontier.
  const RFINE = 110;
  const contours = CONTOUR_QS.map((q) => {
    const zL = -DEPTH * q;
    const runs: V3[][] = [];
    let run: V3[] = [];
    for (let s = 0; s <= ASAMP; s += 1) {
      const theta = thetaAt(s);
      let hit: number | null = null;
      let prevR = 1;
      let prevZ = surfaceZ(theta, 1);
      for (let f = 1; f <= RFINE; f += 1) {
        const r = 1 - f / RFINE;
        const z = surfaceZ(theta, r);
        if (z <= zL) {
          const t = prevZ === z ? 0.5 : (zL - prevZ) / (z - prevZ);
          hit = prevR + (r - prevR) * t;
          break;
        }
        prevR = r;
        prevZ = z;
      }
      if (hit == null) {
        if (run.length > 1) runs.push(run);
        run = [];
      } else {
        run.push({ x: hit * Math.cos(theta), y: hit * Math.sin(theta), z: zL });
      }
    }
    if (run.length > 1) runs.push(run);
    return runs;
  });

  const beads = states.map((s) => polar(s.angle, BEAD_R, 0.012));
  const ghosts = states.map((s) =>
    s.showGhost
      ? {
          x: BEAD_R * Math.cos(s.angle),
          y: BEAD_R * Math.sin(s.angle),
          // Lift the ghost to the pre-decay surface height at r = BEAD_R.
          z: -DEPTH * (meanDepth + (s.ghostDepth - meanDepth) * smooth(clamp01(BEAD_R / CENTER_BLEND))) * Math.pow(1 - BEAD_R, PROFILE_POW) + 0.012
        }
      : null
  );
  const labels = states.map((s) => polar(s.angle, 1.16));

  return { rings, spokes, contours, beads, ghosts, labels };
}

// Split a projected polyline into depth buckets so far fabric fades and near
// fabric stays bright (SVG stroke opacity can't vary along one path).
function depthRuns(points: Projected[]): Array<{ d: string; opacity: number }> {
  const bucketOf = (depth: number) => Math.max(0, Math.min(2, Math.floor(depthFade(depth, 0, 1) * 3)));
  const runs: Array<{ d: string; opacity: number }> = [];
  let start = 0;
  let bucket = points.length > 1 ? bucketOf((points[0].depth + points[1].depth) / 2) : 0;
  for (let i = 1; i < points.length; i += 1) {
    const b = i + 1 < points.length ? bucketOf((points[i].depth + points[i + 1].depth) / 2) : bucket;
    if (b !== bucket || i === points.length - 1) {
      runs.push({ d: polyPath(points.slice(start, i + 1)), opacity: 0.35 + 0.28 * bucket });
      start = i;
      bucket = b;
    }
  }
  return runs;
}

export function KnowledgeWellView({
  field,
  decay,
  selected,
  onSelect,
  onPin,
  onInspect,
  width,
  height
}: {
  field: KnowledgeFacetField;
  decay?: DecayPressureDto | null;
  selected: string | null;
  /** Hover select. The owner may ignore this while a pick is pinned. */
  onSelect: (id: string) => void;
  /** Explicit select (click / arrow key). Always honoured, and hard-selects. */
  onPin?: (id: string) => void;
  onInspect: (id: string) => void;
  /** Pane size in CSS pixels; omitted falls back to the design framing. */
  width?: number;
  height?: number;
}) {
  const W = width && width > 0 ? width : DEFAULT_W;
  const H = height && height > 0 ? height : DEFAULT_H;
  const CX = W / 2;
  const CY = H / 2 - H * CENTER_LIFT;
  const SCALE = Math.min(W * SCALE_W, H * SCALE_H);

  const { cam, onMouseDown, pauseDrift, dragging } = useOrbitCamera({ yaw: -0.5, pitch: 1.0 });
  // Scroll-wheel zoom (see scrollZoom.ts — SCROLL_ZOOM.enabled = false, or
  // deleting this line, the svg's ref/onDoubleClick and the `zoom.*` reads
  // below, removes the behaviour wholesale).
  const zoom = useScrollZoom({ viewWidth: W, centerX: CX, centerY: CY, contentRadius: SCALE, onInteract: pauseDrift });
  const states = useMemo(() => buildStates(field, decay), [field, decay]);
  const geometry = useMemo(() => buildGeometry(states), [states]);

  const view = { cx: CX + zoom.panX, cy: CY + zoom.panY, scale: SCALE * zoom.k, persp: 5.4 };
  const proj = (p: V3) => project(p.x, p.y, p.z, cam, view);

  // Painter order for the anchor beads (far first). View depth is independent
  // of zoom/pan, so this only re-sorts when the camera or geometry moves; the
  // screen positions are projected at draw time.
  const beadOrder = useMemo(() => {
    return geometry.beads
      .map((pos, i) => ({ i, depth: project(pos.x, pos.y, pos.z, cam, view).depth }))
      .sort((a, b) => a.depth - b.depth)
      .map((entry) => entry.i);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [geometry, cam.yaw, cam.pitch]);

  // Exact scene summary for the aria-label and the always-visible caption.
  const summary = useMemo(() => {
    let deep = 0;
    let anchored = 0;
    let shallow = 0;
    let flat = 0;
    let held = 0;
    let debt = 0;
    let instructed = 0;
    for (const s of states) {
      // Counted alongside the depth bands, never inside `anchored`: an
      // instructed facet has no demonstrated credit to anchor with yet.
      if (s.instructed) instructed += 1;
      if (s.absent) debt += 1;
      else if (s.noHistory) held += 1;
      else if (s.wellDepth >= DEEP_LEVEL) {
        deep += 1;
        if (s.demonstrated) anchored += 1;
      } else if (s.wellDepth >= SHALLOW_LEVEL) shallow += 1;
      else flat += 1;
    }
    return { deep, anchored, shallow, flat, held, debt, instructed };
  }, [states]);

  const ariaLabel =
    `Knowledge well, ${states.length} facets: ` +
    `${summary.deep} deep well${summary.deep === 1 ? "" : "s"} (${summary.anchored} anchored / demonstrated), ` +
    `${summary.shallow} shallow, ${summary.flat} flat frontier` +
    (summary.held ? `, ${summary.held} held flat for insufficient history` : "") +
    (summary.instructed
      ? `, ${summary.instructed} instructed with a cold check pending (not demonstrated)`
      : "") +
    (summary.debt ? `, ${summary.debt} absent (content debt)` : "") +
    ". Deep = likely recall, filled bead = demonstrated, flat = unexplored." +
    " Scroll or press plus and minus to zoom; 0 restores the default framing.";

  const sortedIds = states.map((s) => s.point.id);

  // Explicit picks (click, arrow keys) go through `pin` so the owner can latch
  // the selection; hover keeps calling `onSelect`, which the owner may ignore
  // while that latch is held. Falling back to onSelect keeps the component
  // usable standalone, where nothing is latched and the two are the same act.
  const pin = onPin ?? onSelect;

  // Keyboard navigation: arrows cycle the selected facet through the stable id
  // order; Enter opens the facet's first learning object in the inspector.
  const onKeyDown = (event: React.KeyboardEvent<SVGSVGElement>) => {
    if (sortedIds.length === 0) return;
    const idx = selected ? sortedIds.indexOf(selected) : -1;
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      event.preventDefault();
      pin(sortedIds[(idx + 1 + sortedIds.length) % sortedIds.length]);
      pauseDrift();
    } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      event.preventDefault();
      pin(sortedIds[(idx - 1 + sortedIds.length) % sortedIds.length]);
      pauseDrift();
    } else if (event.key === "+" || event.key === "=" || event.key === "-" || event.key === "_") {
      // Keyboard peer for the scroll gesture, so zoom isn't pointer-only.
      event.preventDefault();
      zoom.zoomBy(event.key === "-" || event.key === "_" ? 1 / 1.35 : 1.35);
    } else if (event.key === "0") {
      event.preventDefault();
      zoom.reset();
    } else if ((event.key === "Enter" || event.key === " ") && idx >= 0) {
      event.preventDefault();
      const lo = states[idx].point.learningObjectIds[0];
      if (lo) onInspect(lo);
    }
  };

  if (states.length === 0) {
    return (
      <div style={{ padding: 40, color: COLOR.textFaint, fontSize: 13, fontFamily: FONT_MONO }}>
        no facet field yet — the fabric is flat until evidence gives it mass
      </div>
    );
  }

  return (
    <svg
      ref={zoom.ref}
      className="noselect-canvas"
      width={W}
      height={H}
      viewBox={`0 0 ${W} ${H}`}
      role="img"
      tabIndex={0}
      aria-label={ariaLabel}
      onMouseDown={onMouseDown}
      onDoubleClick={zoom.reset}
      onKeyDown={onKeyDown}
      style={{
        fontFamily: FONT_MONO,
        display: "block",
        // The svg now spans the whole pane, so its box is the frame: spilling
        // rim labels would run under the side panel (and add scrollbars).
        overflow: "hidden",
        cursor: dragging ? "grabbing" : "grab",
        userSelect: "none",
        WebkitUserSelect: "none",
        outline: "none"
      }}
    >
      {/* Always-visible caption — the interpretability contract. */}
      <text x={18} y={22} fill={COLOR.textDim} fontSize={11}>
        deep = likely recall (weighted by evidence) · filled bead = demonstrated · flat = unexplored frontier
      </text>
      {/* Third legend line, present only when the state is: an amber dashed
          bead is a claim the system has NOT earned yet, and a legend that
          named it on every visit would imply it is a normal resting state. */}
      {summary.instructed ? (
        <text x={18} y={37} fill={COLOR.amber} fontSize={11}>
          ◌ dashed amber bead = instructed — cold check pending (not demonstrated)
        </text>
      ) : null}

      {/* Equipotential contours (iso-depth) — bunch where the well wall is
          steep, i.e. at the frontier between settled and unexplored sectors. */}
      {geometry.contours.map((runs, level) =>
        runs.map((run, ri) => (
          <path
            key={`contour-${level}-${ri}`}
            d={polyPath(run.map(proj))}
            fill="none"
            stroke={COLOR.amber}
            strokeWidth={0.7}
            strokeDasharray="3 3"
            opacity={0.28}
          />
        ))
      )}

      {/* Geodesic mesh: distorted rings, depth-faded per run. */}
      {geometry.rings.map((ring, ri) => {
        const isRim = RING_RS[ri] === 1;
        return depthRuns(ring.map(proj)).map((run, si) => (
          <path
            key={`ring-${ri}-${si}`}
            d={run.d}
            fill="none"
            stroke={isRim ? COLOR.borderStrong : COLOR.border}
            strokeWidth={isRim ? 1.2 : 0.8}
            opacity={run.opacity * (isRim ? 1.5 : 1)}
          />
        ));
      })}

      {/* Facet spokes. A held-flat (no-history) sector is dashed so its flat
          fabric reads as "not enough history", distinct from a solid flat
          frontier that is genuinely unexplored (§1.4). */}
      {geometry.spokes.map((spoke, i) => {
        const s = states[i];
        const isActive = s.point.id === selected;
        return (
          <g key={`spoke-${s.point.id}`}>
            <path
              d={polyPath(spoke.map(proj))}
              fill="none"
              stroke={isActive ? COLOR.amber : COLOR.borderStrong}
              strokeWidth={isActive ? 1.4 : 0.85}
              strokeDasharray={s.noHistory ? "3 4" : undefined}
              opacity={isActive ? 0.95 : s.noHistory ? 0.5 : 0.68}
              style={{ transition: EASE }}
            />
            {/* Wide invisible hit path so the whole wire selects the facet. */}
            <path
              d={polyPath(spoke.map(proj))}
              fill="none"
              stroke="transparent"
              strokeWidth={16}
              style={{ cursor: "pointer" }}
              onMouseEnter={() => {
                onSelect(s.point.id);
                pauseDrift();
              }}
              onClick={() => pin(s.point.id)}
            />
          </g>
        );
      })}

      {/* Ghost rings at the pre-decay (readyGhost) depth: the well was here
          before decay pulled it toward flat. Cyan = the Ready channel. */}
      {geometry.ghosts.map((ghost, i) =>
        ghost ? (
          <circle
            key={`ghost-${states[i].point.id}`}
            cx={proj(ghost).x}
            cy={proj(ghost).y}
            r={4.5 * proj(ghost).k}
            fill="none"
            stroke={COLOR.cyan}
            strokeWidth={0.9}
            strokeDasharray="4 3"
            opacity={0.5}
          >
            <title>{`${states[i].point.title}\nrelaxing toward flat — was ${Math.round(states[i].point.readyGhost * 100)}%, now Ready ${Math.round(states[i].point.ready * 100)}%`}</title>
          </circle>
        ) : null
      )}

      {/* Anchor beads at the well bottoms — the DISCRETE Demonstrated channel.
          Filled green bead = demonstrated; hollow cyan ring = predicted but not
          yet demonstrated; hollow amber bead inside a segmented amber ring =
          instructed, cold check pending (repaired with help, unverified);
          × = absent (no blueprint, content debt); hollow diamond = held flat for
          insufficient history. Never a second depth. */}
      {beadOrder.map((i) => {
        const s = states[i];
        const p = proj(geometry.beads[i]);
        const isActive = s.point.id === selected;
        const fade = depthFade(p.depth, 0.6, 1);
        const size = (isActive ? 5 : 3.8) * p.k * zoom.markerScale;
        const hit = 11 * zoom.markerScale;
        const tooltip =
          `${s.point.title}\n` +
          `Ready ${Math.round(s.point.ready * 100)}% · Demonstrated ${Math.round(s.point.demonstratedMass * 100)}% · evidence ${s.point.evidenceMass.toFixed(2)}` +
          (s.absent ? "\nabsent: no blueprint (content debt)" : "") +
          (s.noHistory ? "\nheld flat: not enough history" : "") +
          (s.instructed
            ? "\ninstructed — cold check pending: this was repaired with assistance," +
              "\nand an unassisted check is scheduled. The bead fills only if it passes."
            : "") +
          (s.crossesInDays != null ? `\ncrosses target in ~${Math.round(s.crossesInDays)}d` : "");
        const onEnter = () => {
          onSelect(s.point.id);
          pauseDrift();
        };
        const onClick = (event: React.MouseEvent) => {
          event.stopPropagation();
          // Hard-select first either way, so the pick survives the pointer
          // moving off the bead (and stays put behind the LO overlay).
          pin(s.point.id);
          const lo = s.point.learningObjectIds[0];
          if (lo) onInspect(lo);
        };
        // Absent — content debt, not a learner gap (§1.7): a faint ×, no well.
        if (s.absent) {
          return (
            <g key={`bead-${s.point.id}`} opacity={isActive ? 1 : fade} style={{ cursor: "pointer" }} onMouseEnter={onEnter} onClick={onClick}>
              <line x1={p.x - size} y1={p.y - size} x2={p.x + size} y2={p.y + size} stroke={COLOR.textFaint} strokeWidth={1.1} />
              <line x1={p.x + size} y1={p.y - size} x2={p.x - size} y2={p.y + size} stroke={COLOR.textFaint} strokeWidth={1.1} />
              <circle cx={p.x} cy={p.y} r={hit} fill="transparent" />
              <title>{tooltip}</title>
            </g>
          );
        }
        // Held flat for insufficient history: a hollow diamond — no confident
        // geometry, and shape (not colour) carries the caveat.
        if (s.noHistory) {
          const d = size + 1.2;
          return (
            <g key={`bead-${s.point.id}`} opacity={isActive ? 1 : fade} style={{ cursor: "pointer" }} onMouseEnter={onEnter} onClick={onClick}>
              <path
                d={`M ${p.x} ${p.y - d} L ${p.x + d} ${p.y} L ${p.x} ${p.y + d} L ${p.x - d} ${p.y} Z`}
                fill="none"
                stroke={isActive ? COLOR.amber : COLOR.textDim}
                strokeWidth={1.1}
                strokeDasharray="2 2"
              />
              <circle cx={p.x} cy={p.y} r={hit} fill="transparent" />
              <title>{tooltip}</title>
            </g>
          );
        }
        return (
          <g key={`bead-${s.point.id}`} opacity={isActive ? 1 : fade} style={{ cursor: "pointer", transition: EASE }} onMouseEnter={onEnter} onClick={onClick}>
            {/* Locked facets get a subtle padlock ring, per the terrain view. */}
            {s.point.locked ? (
              <circle cx={p.x} cy={p.y} r={size + 3.5} fill="none" stroke={COLOR.amber} strokeWidth={0.8} strokeDasharray="2 2" opacity={0.7} />
            ) : null}
            {s.demonstrated ? (
              <circle
                cx={p.x}
                cy={p.y}
                r={size}
                fill={COLOR.green}
                stroke={isActive ? COLOR.text : COLOR.bg}
                strokeWidth={1}
              />
            ) : s.instructed ? (
              // Hollow (nothing demonstrated) inside a SEGMENTED ring: the
              // broken ring is the pending measurement, and the bead stays
              // unfilled until an unassisted answer fills it.
              <>
                <circle
                  cx={p.x}
                  cy={p.y}
                  r={size + 2.6}
                  fill="none"
                  stroke={COLOR.amber}
                  strokeWidth={1.1}
                  strokeDasharray="3 3"
                  opacity={0.85}
                />
                <circle
                  cx={p.x}
                  cy={p.y}
                  r={size}
                  fill={COLOR.bg}
                  stroke={COLOR.amber}
                  strokeWidth={1.4}
                />
              </>
            ) : (
              <circle
                cx={p.x}
                cy={p.y}
                r={size}
                fill={COLOR.bg}
                stroke={isActive ? COLOR.amber : COLOR.cyan}
                strokeWidth={1.4}
              />
            )}
            <circle cx={p.x} cy={p.y} r={hit} fill="transparent" />
            <title>{tooltip}</title>
          </g>
        );
      })}

      {/* Rim labels — all facets stay visible; selection only changes emphasis. */}
      {geometry.labels.map((pos, i) => {
        const s = states[i];
        const p = proj(pos);
        const isActive = s.point.id === selected;
        const anchor = Math.abs(p.x - CX) < 14 ? "middle" : p.x > CX ? "start" : "end";
        const lines = labelLines(s.point.id);
        const LINE_H = 12;
        const blockShift = p.y > CY + 10 ? 4 : -((lines.length - 1) * LINE_H) / 2;
        const fade = depthFade(p.depth, 0.55, 1);
        return (
          <g
            key={`label-${s.point.id}`}
            style={{ cursor: "pointer" }}
            opacity={fade}
            onMouseEnter={() => {
              onSelect(s.point.id);
              pauseDrift();
            }}
            onClick={() => pin(s.point.id)}
          >
            <text
              x={p.x}
              y={p.y + blockShift}
              textAnchor={anchor}
              dominantBaseline="middle"
              fontSize={10.5}
              fill={isActive ? COLOR.amber : s.absent ? COLOR.textFaint : COLOR.textDim}
              style={{ transition: EASE }}
            >
              {lines.map((line, lineIndex) => (
                <tspan key={lineIndex} x={p.x} dy={lineIndex === 0 ? 0 : LINE_H}>
                  {line}
                </tspan>
              ))}
            </text>
            {isActive ? (
              <text
                x={p.x}
                y={p.y + blockShift + lines.length * LINE_H}
                textAnchor={anchor}
                dominantBaseline="middle"
                fontSize={9.5}
                fill={COLOR.cyan}
                style={{ transition: EASE }}
              >
                {`Ready ${Math.round(s.point.ready * 100)}%`}
              </text>
            ) : null}
          </g>
        );
      })}

      {/* Zoom readout — bright on the notch, then settles to a faint reminder
          that the framing is no longer the resting one. Corner ticks mark the
          clipped viewport. Both fade to nothing at ×1. */}
      {zoom.readout > 0 ? (
        <g opacity={zoom.readout} pointerEvents="none">
          {[
            [1, 1],
            [-1, 1],
            [1, -1],
            [-1, -1]
          ].map(([sx, sy], i) => {
            const x = sx > 0 ? W - 10 : 10;
            const y = sy > 0 ? H - 10 : 10;
            return (
              <path
                key={`tick-${i}`}
                d={`M ${x - sx * 14} ${y} L ${x} ${y} L ${x} ${y - sy * 14}`}
                fill="none"
                stroke={COLOR.amber}
                strokeWidth={0.9}
                opacity={0.55}
              />
            );
          })}
          <text x={18} y={H - 18} fill={COLOR.amber} fontSize={11}>
            {`×${zoom.k.toFixed(2)}`}
            <tspan fill={COLOR.textFaint}>{"  scroll to zoom · double-click to reset"}</tspan>
          </text>
        </g>
      ) : null}
    </svg>
  );
}
