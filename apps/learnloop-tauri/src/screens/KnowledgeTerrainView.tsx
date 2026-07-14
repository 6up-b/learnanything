import { useMemo } from "react";
import type {
  CapabilityArcStatus,
  KnowledgeFacetField,
  KnowledgeFacetPoint
} from "../api/dto";
import { COLOR, FONT_MONO } from "../components/term";
import { depthFade, project, useOrbitCamera } from "./wire3d";

// A graph-honest dual manifold. Demonstrated evidence is the solid lower
// gravity sheet; Ready is the vaporous prediction sheet above it. Node masses
// diffuse through the BlueprintRecipe Laplacian before they reach the mesh, so
// screen-space proximity alone cannot make two facets share a basin.

const W = 860;
const H = 600;
const CX = W / 2;
const CY = H / 2 + 42;
const SCALE = 238;
const GX = 38;
const GY = 27;
const TAU = 0.72;
const DEMO_DEPTH = 0.56;
const READY_OFFSET = 0.3;
const READY_DEPTH = 0.24;

type MassKey = "demonstratedMass" | "ready";

interface Cell {
  demo: number;
  ready: number;
  readyConfidence: number;
  presence: number;
}

interface Segment {
  ax: number;
  ay: number;
  az: number;
  bx: number;
  by: number;
  bz: number;
  confidence: number;
}

const clamp01 = (value: number) => Math.max(0, Math.min(1, value));

function diffuse(field: KnowledgeFacetField, key: MassKey): Map<string, number> {
  const pointById = new Map(field.points.map((point) => [point.id, point] as const));
  const neighbors = new Map<string, Array<{ id: string; weight: number }>>();
  for (const node of field.graphNodes) neighbors.set(node, []);
  for (const edge of field.edges) {
    neighbors.get(edge.source)?.push({ id: edge.target, weight: edge.weight });
    neighbors.get(edge.target)?.push({ id: edge.source, weight: edge.weight });
  }
  const mass = new Map<string, number>();
  for (const node of field.graphNodes) {
    const point = pointById.get(node);
    mass.set(node, point?.hasBlueprints ? point[key] : 0);
  }
  let values = new Map(mass);
  // Stable Jacobi solve of (I + τL)x = m: a normalized graph potential.
  for (let iteration = 0; iteration < 36; iteration += 1) {
    const next = new Map<string, number>();
    for (const node of field.graphNodes) {
      const links = neighbors.get(node) ?? [];
      const degree = links.reduce((sum, link) => sum + link.weight, 0);
      const neighborMass = links.reduce(
        (sum, link) => sum + link.weight * (values.get(link.id) ?? 0),
        0
      );
      next.set(node, ((mass.get(node) ?? 0) + TAU * neighborMass) / (1 + TAU * degree));
    }
    values = next;
  }
  return values;
}

function buildCells(field: KnowledgeFacetField): Cell[][] {
  const visible = field.points.filter((point) => point.hasBlueprints);
  const demoPotential = diffuse(field, "demonstratedMass");
  const readyPotential = diffuse(field, "ready");
  const rows: Cell[][] = [];
  let maxDemo = 0;
  let maxReady = 0;
  for (let gy = 0; gy <= GY; gy += 1) {
    const y = -1 + (2 * gy) / GY;
    const row: Cell[] = [];
    for (let gx = 0; gx <= GX; gx += 1) {
      const x = -1 + (2 * gx) / GX;
      let demo = 0;
      let ready = 0;
      let confidenceWeight = 0;
      let confidence = 0;
      let nearest = Number.POSITIVE_INFINITY;
      for (const point of visible) {
        const d2 = (point.x - x) ** 2 + (point.y - y) ** 2;
        nearest = Math.min(nearest, d2);
        // The surface is a genuine summed potential: nearby demonstrated mass
        // adds, so adjacent wells deepen into one basin rather than averaging
        // each other away. Epsilon bounds the node singularity.
        const distance = Math.sqrt(d2);
        const weight = 1 / (distance + 0.075);
        const evidenceConfidence =
          (point.evidenceMass / (point.evidenceMass + 1)) *
          (1 / (1 + 18 * point.readyVariance));
        demo += weight * (demoPotential.get(point.id) ?? 0);
        ready += weight * (readyPotential.get(point.id) ?? 0);
        confidence += weight * evidenceConfidence;
        confidenceWeight += weight;
      }
      maxDemo = Math.max(maxDemo, demo);
      maxReady = Math.max(maxReady, ready);
      const presence = visible.length ? clamp01(1 - Math.sqrt(nearest) / 1.15) : 0;
      row.push({
        demo,
        ready,
        readyConfidence: confidenceWeight ? confidence / confidenceWeight : 0,
        presence
      });
    }
    rows.push(row);
  }
  // One common scale preserves both additive basin ordering and the magnitude
  // of the Ready↔Demonstrated void. Per-sheet normalization would falsely make
  // a trace of demonstrated evidence look as massive as a strong prediction.
  const maxPotential = Math.max(maxDemo, maxReady);
  for (const row of rows) {
    for (const cell of row) {
      cell.demo = maxPotential > 0 ? cell.demo / maxPotential : 0;
      cell.ready = maxPotential > 0 ? cell.ready / maxPotential : 0;
    }
  }
  return rows;
}

function sample(cells: Cell[][], x: number, y: number): Cell {
  const fx = clamp01((x + 1) / 2) * GX;
  const fy = clamp01((y + 1) / 2) * GY;
  const gx = Math.min(GX - 1, Math.floor(fx));
  const gy = Math.min(GY - 1, Math.floor(fy));
  const tx = fx - gx;
  const ty = fy - gy;
  const mix = (key: keyof Cell) => {
    const top = cells[gy][gx][key] * (1 - tx) + cells[gy][gx + 1][key] * tx;
    const bottom = cells[gy + 1][gx][key] * (1 - tx) + cells[gy + 1][gx + 1][key] * tx;
    return top * (1 - ty) + bottom * ty;
  };
  return { demo: mix("demo"), ready: mix("ready"), readyConfidence: mix("readyConfidence"), presence: mix("presence") };
}

function sheetZ(cell: Cell) {
  const demo = -DEMO_DEPTH * cell.demo;
  const predicted = READY_OFFSET - READY_DEPTH * cell.ready;
  return { demo, ready: Math.max(predicted, demo + 0.13) };
}

function meshSegments(cells: Cell[][], sheet: "demo" | "ready"): Segment[] {
  const out: Segment[] = [];
  const world = (gx: number, gy: number) => ({ x: -1 + (2 * gx) / GX, y: -1 + (2 * gy) / GY });
  const push = (ax: number, ay: number, bx: number, by: number) => {
    const a = cells[ay][ax];
    const b = cells[by][bx];
    if (Math.min(a.presence, b.presence) < 0.035) return;
    const pa = world(ax, ay);
    const pb = world(bx, by);
    out.push({
      ax: pa.x,
      ay: pa.y,
      az: sheetZ(a)[sheet],
      bx: pb.x,
      by: pb.y,
      bz: sheetZ(b)[sheet],
      confidence: (a.readyConfidence + b.readyConfidence) / 2
    });
  };
  for (let y = 0; y <= GY; y += 1) for (let x = 0; x < GX; x += 1) push(x, y, x + 1, y);
  for (let x = 0; x <= GX; x += 1) for (let y = 0; y < GY; y += 1) push(x, y, x, y + 1);
  return out;
}

function arcPath(cx: number, cy: number, radius: number, index: number): string {
  const start = -Math.PI / 2 + (index * Math.PI * 2) / 5 + 0.08;
  const end = -Math.PI / 2 + ((index + 1) * Math.PI * 2) / 5 - 0.08;
  return `M ${(cx + Math.cos(start) * radius).toFixed(1)} ${(cy + Math.sin(start) * radius).toFixed(1)} A ${radius} ${radius} 0 0 1 ${(cx + Math.cos(end) * radius).toFixed(1)} ${(cy + Math.sin(end) * radius).toFixed(1)}`;
}

function arcStyle(status: CapabilityArcStatus): { stroke: string; dash?: string; opacity: number } {
  if (status === "demonstrated") return { stroke: COLOR.green, opacity: 0.95 };
  if (status === "required") return { stroke: COLOR.textDim, dash: "2 2", opacity: 0.8 };
  return { stroke: "transparent", opacity: 0 };
}

function gapGlyph(kind: NonNullable<KnowledgeFacetField["nextGap"]>["kind"], x: number, y: number) {
  if (kind === "integration_gap") return `M ${x - 7} ${y} Q ${x} ${y - 9} ${x + 7} ${y}`;
  if (kind === "retrievability") return `M ${x - 6} ${y} A 6 3 0 1 0 ${x + 6} ${y}`;
  if (kind === "unresolved_diagnostic") return `M ${x - 6} ${y - 4} L ${x} ${y + 5} L ${x + 6} ${y - 4}`;
  return `M ${x - 6} ${y + 5} L ${x} ${y - 6} L ${x + 6} ${y + 5} Z`;
}

function FlatTopology({ field, selected, onSelect, onInspect }: {
  field: KnowledgeFacetField;
  selected: string | null;
  onSelect: (id: string) => void;
  onInspect: (id: string) => void;
}) {
  const byId = new Map(field.points.map((point) => [point.id, point] as const));
  const sx = (x: number) => CX + x * SCALE;
  const sy = (y: number) => H / 2 + y * SCALE;
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ maxWidth: "100%", fontFamily: FONT_MONO }}>
      <text x={24} y={28} fill={COLOR.amber} fontSize={11}>{field.layoutWarning ?? "flat recipe topology"}</text>
      {field.edges.map((edge) => {
        const a = byId.get(edge.source);
        const b = byId.get(edge.target);
        return a && b ? <line key={`${edge.source}:${edge.target}`} x1={sx(a.x)} y1={sy(a.y)} x2={sx(b.x)} y2={sy(b.y)} stroke={COLOR.borderStrong} strokeWidth={Math.min(2.5, 0.6 + edge.weight)} /> : null;
      })}
      {field.points.map((point) => (
        <g key={point.id} style={{ cursor: point.learningObjectIds.length ? "pointer" : "default" }} onMouseEnter={() => onSelect(point.id)} onClick={() => point.learningObjectIds[0] && onInspect(point.learningObjectIds[0])}>
          <circle cx={sx(point.x)} cy={sy(point.y)} r={point.id === selected ? 7 : 5} fill={point.hasBlueprints ? COLOR.green : COLOR.bg} stroke={point.hasBlueprints ? COLOR.green : COLOR.textFaint} />
          <text x={sx(point.x) + 8} y={sy(point.y) - 7} fill={point.id === selected ? COLOR.amber : COLOR.textDim} fontSize={9}>{point.title}</text>
        </g>
      ))}
    </svg>
  );
}

export function KnowledgeTerrainView({
  field,
  selected,
  onSelect,
  onInspect
}: {
  field: KnowledgeFacetField;
  selected: string | null;
  onSelect: (id: string) => void;
  onInspect: (id: string) => void;
}) {
  const { cam, onMouseDown, pauseDrift, dragging } = useOrbitCamera({ yaw: -0.62, pitch: 1.02 });
  const cells = useMemo(() => buildCells(field), [field]);
  const demo = useMemo(() => meshSegments(cells, "demo"), [cells]);
  const ready = useMemo(() => meshSegments(cells, "ready"), [cells]);
  const view = { cx: CX, cy: CY, scale: SCALE, persp: 5.6 };
  const proj = (x: number, y: number, z: number) => project(x, y, z, cam, view);

  const groupSheet = (segments: Segment[], prediction: boolean) => {
    const groups = new Map<string, { d: string[]; opacity: number }>();
    for (const segment of segments) {
      const a = proj(segment.ax, segment.ay, segment.az);
      const b = proj(segment.bx, segment.by, segment.bz);
      const depth = Math.max(0, Math.min(2, Math.floor(depthFade((a.depth + b.depth) / 2, 0, 1) * 3)));
      const certainty = prediction ? Math.max(0, Math.min(3, Math.floor(segment.confidence * 4))) : 3;
      const key = `${depth}:${certainty}`;
      const opacity = prediction
        ? (0.08 + certainty * 0.08) * (0.7 + depth * 0.13)
        : 0.34 * (0.72 + depth * 0.14);
      const group = groups.get(key) ?? { d: [], opacity };
      group.d.push(`M ${a.x.toFixed(1)} ${a.y.toFixed(1)} L ${b.x.toFixed(1)} ${b.y.toFixed(1)}`);
      groups.set(key, group);
    }
    return [...groups.entries()].map(([key, group]) => ({ key, opacity: group.opacity, d: group.d.join(" ") }));
  };

  const demoGroups = groupSheet(demo, false);
  const readyGroups = groupSheet(ready, true);
  const pointById = new Map(field.points.map((point) => [point.id, point] as const));
  const pins = field.points
    .map((point) => {
      const z = sheetZ(sample(cells, point.x, point.y));
      return { point, demo: proj(point.x, point.y, z.demo), ready: proj(point.x, point.y, z.ready) };
    })
    .sort((a, b) => a.demo.depth - b.demo.depth);

  const pathPoints = (field.nextGap?.pathFacetIds ?? [])
    .map((id) => pointById.get(id))
    .filter((point): point is KnowledgeFacetPoint => point != null)
    .map((point) => {
      const z = sheetZ(sample(cells, point.x, point.y)).demo - 0.008;
      return proj(point.x, point.y, z);
    });
  const pathD = pathPoints.length > 1
    ? `M ${pathPoints.map((point) => `${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(" L ")}`
    : "";

  const floor = [proj(-1, -1, 0), proj(1, -1, 0), proj(1, 1, 0), proj(-1, 1, 0)];
  const floorD = `M ${floor.map((point) => `${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(" L ")} Z`;

  if (!field.layoutValid) {
    return <FlatTopology field={field} selected={selected} onSelect={onSelect} onInspect={onInspect} />;
  }

  return (
    <svg
      className="noselect-canvas"
      width={W}
      height={H}
      viewBox={`0 0 ${W} ${H}`}
      onMouseDown={onMouseDown}
      style={{
        fontFamily: FONT_MONO,
        maxWidth: "100%",
        height: "auto",
        overflow: "visible",
        cursor: dragging ? "grabbing" : "grab",
        userSelect: "none"
      }}
    >
      <path d={floorD} fill="none" stroke={COLOR.borderStrong} strokeWidth={1} strokeDasharray="2 5" opacity={0.45} />

      {/* Demonstrated: stable, solid, lit. It never fogs. */}
      {demoGroups.map((group) => (
        <path key={`demo:${group.key}`} d={group.d} fill="none" stroke={COLOR.green} strokeWidth={0.9} opacity={group.opacity} />
      ))}

      {/* Ready: deliberately distinct wire/vapor material; only it fogs. */}
      {readyGroups.map((group) => (
        <path key={`ready:${group.key}`} d={group.d} fill="none" stroke={COLOR.cyan} strokeWidth={0.72} strokeDasharray="3 2" opacity={group.opacity} />
      ))}

      {pathD ? <path d={pathD} fill="none" stroke={COLOR.amber} strokeWidth={2} strokeDasharray="6 3" opacity={0.95} /> : null}

      {pins.map(({ point, demo: demoPoint, ready: readyPoint }) => {
        const active = point.id === selected;
        const fade = depthFade(demoPoint.depth, 0.58, 1);
        const radius = active ? 10 : 8;
        const tooltip = `${point.title}\nDemonstrated ${Math.round(point.demonstratedMass * 100)}%\nReady ${Math.round(point.ready * 100)}%`;
        if (!point.hasBlueprints) {
          return (
            <g
              key={point.id}
              opacity={active ? 1 : fade}
              style={{ cursor: "pointer" }}
              onMouseEnter={() => { onSelect(point.id); pauseDrift(); }}
              onClick={(event) => { event.stopPropagation(); if (point.learningObjectIds[0]) onInspect(point.learningObjectIds[0]); }}
            >
              <line x1={demoPoint.x - 5} y1={demoPoint.y - 5} x2={demoPoint.x + 5} y2={demoPoint.y + 5} stroke={COLOR.textFaint} />
              <line x1={demoPoint.x + 5} y1={demoPoint.y - 5} x2={demoPoint.x - 5} y2={demoPoint.y + 5} stroke={COLOR.textFaint} />
              <circle cx={demoPoint.x} cy={demoPoint.y} r={12} fill="transparent" />
              <title>{`${point.title}\nAbsent: no blueprint requirements`}</title>
            </g>
          );
        }
        return (
          <g
            key={point.id}
            opacity={active ? 1 : fade}
            style={{ cursor: "pointer" }}
            onMouseEnter={() => { onSelect(point.id); pauseDrift(); }}
            onClick={(event) => { event.stopPropagation(); if (point.learningObjectIds[0]) onInspect(point.learningObjectIds[0]); }}
          >
            <line x1={demoPoint.x} y1={demoPoint.y} x2={readyPoint.x} y2={readyPoint.y} stroke={COLOR.textFaint} strokeWidth={0.65} opacity={0.38} />
            <circle cx={readyPoint.x} cy={readyPoint.y} r={3.2} fill="none" stroke={COLOR.cyan} strokeWidth={0.8} opacity={0.62} />
            <circle cx={demoPoint.x} cy={demoPoint.y} r={active ? 3.8 : 2.8} fill={COLOR.green} stroke={active ? COLOR.text : COLOR.bg} strokeWidth={1} />
            {point.capabilityArcs.map((arc, index) => {
              const style = arcStyle(arc.status);
              return (
                <path
                  key={arc.capability}
                  d={arcPath(demoPoint.x, demoPoint.y, radius, index)}
                  fill="none"
                  stroke={style.stroke}
                  strokeWidth={arc.status === "demonstrated" ? 2 : 1.15}
                  strokeDasharray={style.dash}
                  opacity={style.opacity}
                />
              );
            })}
            {point.ambiguityCandidates.map((candidate, index) => {
              const candidatePoint = pointById.get(candidate);
              if (!candidatePoint) return null;
              const candidateZ = sheetZ(sample(cells, candidatePoint.x, candidatePoint.y)).demo;
              const ghost = proj(candidatePoint.x, candidatePoint.y, candidateZ - 0.012 - index * 0.002);
              return (
                <g key={candidate}>
                  <line x1={demoPoint.x} y1={demoPoint.y} x2={ghost.x} y2={ghost.y} stroke={COLOR.red} strokeWidth={0.7} strokeDasharray="2 3" opacity={0.4} />
                  <circle cx={ghost.x} cy={ghost.y} r={3} fill="none" stroke={COLOR.red} opacity={0.62} />
                </g>
              );
            })}
            {point.correction ? (
              <>
                <circle cx={demoPoint.x} cy={demoPoint.y} r={radius + 3} fill="none" stroke={COLOR.amber} strokeWidth={1} strokeDasharray="2 3" opacity={0.78} />
                <text x={demoPoint.x + radius + 5} y={demoPoint.y - radius} fill={COLOR.amber} fontSize={8}>correction</text>
              </>
            ) : null}
            {field.nextGap?.kind === "retrievability" && field.nextGap.facetId === point.id ? (() => {
              const ghost = proj(point.x, point.y, READY_OFFSET - READY_DEPTH * point.readyGhost);
              return (
                <>
                  <circle cx={ghost.x} cy={ghost.y} r={radius + 3} fill="none" stroke={COLOR.cyan} strokeWidth={1.2} strokeDasharray="5 3" opacity={0.72} />
                  <line x1={ghost.x} y1={ghost.y} x2={readyPoint.x} y2={readyPoint.y} stroke={COLOR.cyan} strokeWidth={0.7} strokeDasharray="2 3" opacity={0.5} />
                </>
              );
            })() : null}
            <circle cx={demoPoint.x} cy={demoPoint.y} r={14} fill="transparent" />
            <title>{tooltip}</title>
          </g>
        );
      })}

      {field.nextGap ? (() => {
        const point = pointById.get(field.nextGap.facetId);
        if (!point) return null;
        const base = proj(point.x, point.y, sheetZ(sample(cells, point.x, point.y)).demo - 0.035);
        return (
          <g
            style={{ cursor: "pointer" }}
            onMouseEnter={() => { onSelect(point.id); pauseDrift(); }}
            onClick={(event) => { event.stopPropagation(); onInspect(field.nextGap!.targetId); }}
          >
            <path d={gapGlyph(field.nextGap.kind, base.x, base.y - 12)} fill="none" stroke={COLOR.amber} strokeWidth={2.2} />
            <line x1={base.x} y1={base.y - 6} x2={base.x} y2={base.y} stroke={COLOR.amber} strokeWidth={1.4} />
            <circle cx={base.x} cy={base.y - 12} r={14} fill="transparent" />
            <title>{`Next · ${field.nextGap.label}`}</title>
          </g>
        );
      })() : null}
    </svg>
  );
}
