import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type {
  CommandError,
  ConceptGraphEdge,
  ConceptGraphNode,
  ConceptGraphSnapshot,
  GoalDto,
  GoalReportSnapshot
} from "../api/dto";
import { EntityLink } from "../components/ui";
import { BlockBar, COLOR, Dim, Faint, FONT_MONO, KeyBar, Meta, Pill, SectionHeader, type PillColor } from "../components/term";
import { masteryTone } from "../app/algoConfig";
import { KnowledgeMapView } from "./KnowledgeMapScreen";

const NODE_W = 200;
const NODE_H = 36;
const COL_GAP = 80;
const ROW_GAP = 24;
const PAD = 24;

type Relation = "prerequisite" | "confusable_with" | "related" | "part_of";

const RELATION_STYLE: Record<Relation, { stroke: string; dash: string; label: string; marker: string }> = {
  prerequisite: { stroke: COLOR.amber, dash: "0", label: "prereq", marker: "arrow" },
  confusable_with: { stroke: COLOR.red, dash: "4 4", label: "confusable", marker: "arrow-red" },
  related: { stroke: COLOR.cyan, dash: "1 4", label: "related", marker: "arrow-cyan" },
  part_of: { stroke: COLOR.green, dash: "8 2 1 2", label: "part_of", marker: "arrow-green" }
};

function relationStyle(relation: string) {
  return RELATION_STYLE[relation as Relation] ?? RELATION_STYLE.related;
}

function conceptPillColor(type: string): PillColor {
  return type === "misconception" ? "red" : type === "procedure" ? "green" : type === "skill" ? "amber" : "purple";
}

function masteryColor(mastery: number): string {
  return masteryTone(mastery, COLOR);
}

type Position = { x: number; y: number };

// Layered layout: column = longest prerequisite-chain depth, row = order within
// that depth. Non-prerequisite edges don't influence placement.
function layoutConcepts(concepts: ConceptGraphNode[], edges: ConceptGraphEdge[]): {
  positions: Record<string, Position>;
  width: number;
  height: number;
} {
  const depth: Record<string, number> = {};
  concepts.forEach((c) => {
    depth[c.id] = 0;
  });
  const prereq = edges.filter((edge) => edge.relationType === "prerequisite" && edge.source in depth && edge.target in depth);
  for (let iter = 0; iter < concepts.length; iter += 1) {
    let changed = false;
    for (const edge of prereq) {
      if (depth[edge.target] < depth[edge.source] + 1) {
        depth[edge.target] = depth[edge.source] + 1;
        changed = true;
      }
    }
    if (!changed) break;
  }

  const byColumn = new Map<number, ConceptGraphNode[]>();
  for (const concept of concepts) {
    const col = depth[concept.id] ?? 0;
    const bucket = byColumn.get(col) ?? [];
    bucket.push(concept);
    byColumn.set(col, bucket);
  }

  const positions: Record<string, Position> = {};
  for (const [col, bucket] of byColumn) {
    bucket.sort((a, b) => (a.title || a.id).localeCompare(b.title || b.id));
    bucket.forEach((concept, row) => {
      positions[concept.id] = {
        x: col * (NODE_W + COL_GAP),
        y: row * (NODE_H + ROW_GAP)
      };
    });
  }

  // Crop to the bounding box of the actually-placed nodes: shift the top-left
  // node to (PAD, PAD) and size width/height to wrap the nodes tightly. Depth
  // (the column index) can start above 0 — a prerequisite cycle makes the
  // longest-path layering increment every node's depth, so nothing lands in
  // column 0 — which would otherwise push the whole graph off to the right and
  // leave a wide empty band (premature horizontal scroll, graph not visible).
  const placed = Object.values(positions);
  if (placed.length === 0) {
    return { positions, width: PAD * 2, height: PAD * 2 };
  }
  const minX = Math.min(...placed.map((p) => p.x));
  const minY = Math.min(...placed.map((p) => p.y));
  let maxX = 0;
  let maxY = 0;
  for (const id of Object.keys(positions)) {
    const x = positions[id].x - minX + PAD;
    const y = positions[id].y - minY + PAD;
    positions[id] = { x, y };
    maxX = Math.max(maxX, x + NODE_W);
    maxY = Math.max(maxY, y + NODE_H);
  }

  return { positions, width: maxX + PAD, height: maxY + PAD };
}

// Orthogonal connector: exit the source's right edge, enter the target's left
// edge, with a vertical bend at the midpoint (mirrors the handoff design).
function edgePath(source: Position, target: Position): string {
  const sy = source.y + NODE_H / 2;
  const ty = target.y + NODE_H / 2;
  if (target.x < source.x) {
    const sx = source.x;
    const tx = target.x + NODE_W;
    const mid = (sx + tx) / 2;
    return `M ${sx} ${sy} L ${mid} ${sy} L ${mid} ${ty} L ${tx} ${ty}`;
  }
  const sx = source.x + NODE_W;
  const tx = target.x;
  const mid = (sx + tx) / 2;
  return `M ${sx} ${sy} L ${mid} ${sy} L ${mid} ${ty} L ${tx} ${ty}`;
}

type GraphView = "map" | "knowledge";

export function GraphScreen({ onInspect, onError }: { onInspect: (id: string) => void; onError: (message: string) => void }) {
  const [view, setView] = useState<GraphView>("map");
  const [snapshot, setSnapshot] = useState<ConceptGraphSnapshot | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [hovered, setHovered] = useState<string | null>(null);
  // Goal overlay: tint concept nodes by whether they fall in the active goal's
  // scope and are at risk. Off by default → exactly the prior rendering.
  const [goalOverlay, setGoalOverlay] = useState(false);
  const [goal, setGoal] = useState<GoalDto | null>(null);
  const [goalReport, setGoalReport] = useState<GoalReportSnapshot | null>(null);
  const [goalError, setGoalError] = useState<string | null>(null);

  // Lazily load the active goal + its at-risk report the first time the overlay
  // is switched on. Failures degrade to a dim legend note (never crash).
  useEffect(() => {
    if (!goalOverlay || goal) return;
    let cancelled = false;
    setGoalError(null);
    api
      .goalsList()
      .then((snap) => {
        if (cancelled) return null;
        const active = snap.goals.find((g) => g.status === "active") ?? snap.goals[0] ?? null;
        if (!active) {
          setGoalError("no goals defined");
          return null;
        }
        setGoal(active);
        return api.getGoalReport(active.id);
      })
      .then((report) => {
        if (!cancelled && report) setGoalReport(report);
      })
      .catch((error) => {
        if (!cancelled) setGoalError((error as CommandError).message);
      });
    return () => {
      cancelled = true;
    };
  }, [goalOverlay, goal]);

  useEffect(() => {
    let cancelled = false;
    api
      .getConceptGraph()
      .then((graph) => {
        if (cancelled) return;
        setSnapshot(graph);
        setSelected((current) => current ?? graph.concepts[0]?.id ?? null);
      })
      .catch((error) => {
        if (!cancelled) onError(error.message);
      });
    return () => {
      cancelled = true;
    };
  }, [onError]);

  const order = useMemo(() => snapshot?.concepts.map((c) => c.id) ?? [], [snapshot]);
  const layout = useMemo(
    () => (snapshot ? layoutConcepts(snapshot.concepts, snapshot.edges) : { positions: {}, width: 0, height: 0 }),
    [snapshot]
  );

  // Per-concept goal status: a concept is in-scope if it's named in the goal's
  // facet scope or owns a learning object with an at-risk facet; "at risk" if any
  // owned LO has an at-risk (non-solid) facet, else "on track". Concepts outside
  // the scope get no entry (rendered dimmed while the overlay is on).
  const goalScope = useMemo(() => {
    if (!goalOverlay || !goal || !snapshot) return null;
    const scopeConcepts = new Set(goal.facetScope.concepts);
    const atRiskLos = new Set(
      (goalReport?.report.atRisk ?? []).filter((f) => f.label !== "solid").map((f) => f.learningObjectId)
    );
    const status = new Map<string, "atRisk" | "onTrack">();
    let atRiskCount = 0;
    for (const concept of snapshot.concepts) {
      const risky = concept.learningObjects.some((lo) => atRiskLos.has(lo.id));
      const inScope = scopeConcepts.has(concept.id) || risky;
      if (!inScope) continue;
      status.set(concept.id, risky ? "atRisk" : "onTrack");
      if (risky) atRiskCount += 1;
    }
    return { status, atRiskCount, total: status.size, title: goal.title };
  }, [goalOverlay, goal, goalReport, snapshot]);

  useEffect(() => {
    if (view !== "map") return;
    const onKey = (event: KeyboardEvent) => {
      const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea") return;
      if (event.key !== "Tab" || order.length === 0) return;
      event.preventDefault();
      const index = selected ? order.indexOf(selected) : -1;
      const next = event.shiftKey ? (index - 1 + order.length) % order.length : (index + 1) % order.length;
      setSelected(order[next]);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [order, selected, view]);

  const viewToggle = (
    <div
      style={{
        display: "flex",
        gap: 4,
        padding: "8px 14px",
        borderBottom: `1px solid ${COLOR.border}`,
        background: COLOR.bg,
        flexShrink: 0,
        fontFamily: FONT_MONO,
        fontSize: 12
      }}
    >
      {(["map", "knowledge"] as const).map((id) => (
        <button
          key={id}
          type="button"
          onClick={() => setView(id)}
          style={{
            background: view === id ? "#241d12" : "transparent",
            border: `1px solid ${view === id ? COLOR.amber : COLOR.border}`,
            color: view === id ? COLOR.amber : COLOR.textDim,
            font: "inherit",
            padding: "3px 12px",
            cursor: "pointer"
          }}
        >
          {id === "map" ? "concept map" : "knowledge field"}
        </button>
      ))}
    </div>
  );

  if (view === "knowledge") {
    return (
      <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
        {viewToggle}
        <KnowledgeMapView onInspect={onInspect} onError={onError} />
      </div>
    );
  }

  if (!snapshot) {
    return (
      <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
        {viewToggle}
        <div style={{ padding: 30, color: COLOR.textFaint, fontSize: 13 }}>loading concept graph…</div>
      </div>
    );
  }

  const conceptById = new Map(snapshot.concepts.map((concept) => [concept.id, concept] as const));
  const selectedConcept = selected ? conceptById.get(selected) ?? null : null;

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      {viewToggle}
      <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
        {/* Canvas */}
        <div style={{ flex: 1, position: "relative", overflow: "hidden", background: COLOR.bg }}>
          {/* Grid lines — full canvas backdrop, independent of graph content size */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              backgroundImage: [
                `linear-gradient(to right, ${COLOR.border} 1px, transparent 1px)`,
                `linear-gradient(to bottom, ${COLOR.border} 1px, transparent 1px)`,
              ].join(", "),
              backgroundSize: "24px 24px",
              opacity: 0.22,
              pointerEvents: "none",
              zIndex: 0
            }}
          />
          {/* Dots at intersections */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              backgroundImage: `radial-gradient(circle at 0 0, ${COLOR.border} 1.5px, transparent 1.5px)`,
              backgroundSize: "24px 24px",
              opacity: 0.5,
              pointerEvents: "none",
              zIndex: 0
            }}
          />
          {/* Scrollable content layer */}
          <div style={{ position: "absolute", inset: 0, overflow: "auto", padding: 24 }}>

          <div style={{ position: "sticky", top: 0, marginBottom: 8, zIndex: 4, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <span style={{ color: COLOR.amber, fontSize: 13 }}>concept-graph</span>{" "}
              <Meta>{snapshot.subjects.join(", ") || "all subjects"}</Meta>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 14, fontSize: 12 }}>
              {goalOverlay ? (
                <span>
                  {goalError ? (
                    <Faint>goal: {goalError}</Faint>
                  ) : goalScope ? (
                    <span style={{ color: COLOR.textDim }}>
                      goal: <span style={{ color: COLOR.amber }}>{goalScope.title}</span> —{" "}
                      <span style={{ color: COLOR.amber }}>{goalScope.atRiskCount}</span> at risk /{" "}
                      {goalScope.total}
                    </span>
                  ) : (
                    <Faint>goal: loading…</Faint>
                  )}
                </span>
              ) : null}
              <button
                type="button"
                onClick={() => setGoalOverlay((on) => !on)}
                style={{
                  background: goalOverlay ? "#241d12" : "transparent",
                  border: `1px solid ${goalOverlay ? COLOR.amber : COLOR.border}`,
                  color: goalOverlay ? COLOR.amber : COLOR.textDim,
                  fontFamily: FONT_MONO,
                  fontSize: 12,
                  padding: "2px 10px",
                  cursor: "pointer"
                }}
              >
                goal overlay
              </button>
              <span>
                <Faint>tab/shift+tab</Faint> <Dim>walk concepts</Dim>
              </span>
            </div>
          </div>

          <div style={{ position: "relative", width: layout.width, height: layout.height }}>
            {/* Grid lines — clipped to the actual content bounds */}
            <div
              style={{
                position: "absolute",
                inset: 0,
                backgroundImage: [
                  `linear-gradient(to right, ${COLOR.border} 1px, transparent 1px)`,
                  `linear-gradient(to bottom, ${COLOR.border} 1px, transparent 1px)`,
                ].join(", "),
                backgroundSize: "24px 24px",
                opacity: 0.22,
                pointerEvents: "none",
                zIndex: 0
              }}
            />
            {/* Dots at intersections — clipped to the actual content bounds */}
            <div
              style={{
                position: "absolute",
                inset: 0,
                backgroundImage: `radial-gradient(circle at 0 0, ${COLOR.border} 1.5px, transparent 1.5px)`,
                backgroundSize: "24px 24px",
                opacity: 0.5,
                pointerEvents: "none",
                zIndex: 0
              }}
            />
            <svg width={layout.width} height={layout.height} overflow="visible" style={{ position: "absolute", inset: 0, zIndex: 1, pointerEvents: "none" }}>
              <defs>
                {["arrow", "arrow-red", "arrow-cyan", "arrow-green"].map((id) => {
                  const fill =
                    id === "arrow-red" ? COLOR.red : id === "arrow-cyan" ? COLOR.cyan : id === "arrow-green" ? COLOR.green : COLOR.amber;
                  return (
                    <marker key={id} id={id} viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                      <path d="M 0 0 L 10 5 L 0 10 z" fill={fill} />
                    </marker>
                  );
                })}
              </defs>
              {snapshot.edges.map((edge) => {
                const source = layout.positions[edge.source];
                const target = layout.positions[edge.target];
                if (!source || !target) return null;
                const style = relationStyle(edge.relationType);
                const incidentHover = hovered != null && (edge.source === hovered || edge.target === hovered);
                const incidentSelected = selected != null && (edge.source === selected || edge.target === selected);
                const incident = incidentHover || incidentSelected;
                return (
                  <path
                    key={edge.id}
                    d={edgePath(source, target)}
                    fill="none"
                    stroke={style.stroke}
                    strokeWidth={incidentHover ? 2.2 : incident ? 1.8 : 1}
                    strokeDasharray={style.dash}
                    opacity={incidentHover ? 0.6 : incident ? 0.9 : hovered ? 0.15 : 0.45}
                    markerEnd={edge.relationType === "confusable_with" ? undefined : `url(#${style.marker})`}
                    style={incidentHover ? { filter: `drop-shadow(0 0 6px ${style.stroke})` } : undefined}
                  />
                );
              })}
            </svg>

            {snapshot.concepts.map((concept) => {
              const pos = layout.positions[concept.id];
              if (!pos) return null;
              const isMisc = concept.type === "misconception";
              const isSelected = selected === concept.id;
              const isHovered = hovered === concept.id;
              const hoverAccent = isMisc ? "rgba(224,126,126,0.6)" : "rgba(255, 161, 67, 0.6)";
              // Goal overlay: ring on-scope concepts (amber = at risk, green = on
              // track), dim off-goal ones. Null when the overlay is off → no change.
              const gstat = goalScope?.status.get(concept.id) ?? null;
              const dimmed = goalScope != null && gstat == null;
              const goalRing =
                gstat === "atRisk" ? `0 0 0 2px ${COLOR.amber}` : gstat === "onTrack" ? `0 0 0 2px ${COLOR.green}` : null;
              const boxShadow =
                [isSelected ? `0 0 0 1px ${COLOR.amber}` : null, goalRing].filter(Boolean).join(", ") || "none";
              return (
                <div
                  key={concept.id}
                  onClick={() => setSelected(concept.id)}
                  onMouseEnter={() => setHovered(concept.id)}
                  onMouseLeave={() => setHovered(null)}
                  style={{
                    position: "absolute",
                    left: pos.x,
                    top: pos.y,
                    width: NODE_W,
                    height: NODE_H,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "0 10px",
                    border: `1px solid ${isSelected ? COLOR.amber : isHovered ? hoverAccent : isMisc ? COLOR.red : COLOR.borderStrong}`,
                    background: isSelected ? "#241d12" : isHovered ? COLOR.bgElev : COLOR.bg,
                    color: isSelected ? COLOR.amber : isHovered ? hoverAccent : COLOR.text,
                    fontFamily: FONT_MONO,
                    fontSize: 12,
                    cursor: "pointer",
                    boxShadow,
                    opacity: dimmed ? 0.4 : 1,
                    filter: isHovered
                      ? `drop-shadow(0 0 10px ${isMisc ? "rgba(224,126,126,0.27)" : "rgba(227,160,99,0.24)"})`
                      : "none",
                    transition: "border-color 0.12s ease, background 0.12s ease, color 0.12s ease, filter 0.15s ease, opacity 0.15s ease",
                    zIndex: isHovered ? 4 : isSelected ? 3 : 2
                  }}
                >
                  <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{concept.title}</span>
                  <span style={{ fontSize: 10, color: isMisc ? COLOR.red : isSelected ? COLOR.amber : COLOR.textFaint, marginLeft: 6, fontStyle: "italic" }}>
                    {concept.type}
                  </span>
                </div>
              );
            })}
          </div>
          </div>{/* end scrollable content */}
          {/* Vignette overlay — last child so it paints above the scroll layer without a z-index war */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              background: `radial-gradient(ellipse at 50% 50%, rgba(14,14,14,0) 40%, rgba(14,14,14,0.55) 75%, ${COLOR.bg} 100%)`,
              pointerEvents: "none"
            }}
          />
        </div>

        <ConceptDetail concept={selectedConcept} edges={snapshot.edges} onInspect={onInspect} />
      </div>

      <Legend counts={snapshot.counts} />

      <KeyBar
        keys={[
          { key: "tab", label: "Next" },
          { key: "shift+tab", label: "Prev" },
          { key: "click", label: "Select" }
        ]}
        right={{ key: "^p", label: "palette" }}
      />
    </div>
  );
}

function Legend({ counts }: { counts: ConceptGraphSnapshot["counts"] }) {
  return (
    <div
      style={{
        display: "flex",
        gap: 18,
        padding: "8px 14px",
        borderTop: `1px solid ${COLOR.border}`,
        fontSize: 12,
        color: COLOR.textDim,
        background: COLOR.bg,
        flexShrink: 0,
        flexWrap: "wrap"
      }}
    >
      <Faint>edge types:</Faint>
      {(Object.keys(RELATION_STYLE) as Relation[]).map((relation) => {
        const style = RELATION_STYLE[relation];
        return (
          <span key={relation} style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <svg width="24" height="6">
              <line x1="0" y1="3" x2="24" y2="3" stroke={style.stroke} strokeWidth="1.5" strokeDasharray={style.dash} />
            </svg>
            <span style={{ color: COLOR.text }}>{style.label}</span>
          </span>
        );
      })}
      <span style={{ flex: 1 }} />
      <Faint>
        {counts.concepts} concepts · {counts.edges} edges · {counts.misconceptions} misconception{counts.misconceptions === 1 ? "" : "s"}
      </Faint>
    </div>
  );
}

function ConceptDetail({
  concept,
  edges,
  onInspect
}: {
  concept: ConceptGraphNode | null;
  edges: ConceptGraphEdge[];
  onInspect: (id: string) => void;
}) {
  if (!concept) {
    return (
      <div style={{ width: 360, flexShrink: 0, borderLeft: `1px solid ${COLOR.border}`, background: COLOR.bg, padding: "16px 18px", color: COLOR.textFaint, fontSize: 13 }}>
        no concept selected
      </div>
    );
  }
  const incoming = edges.filter((edge) => edge.target === concept.id);
  const outgoing = edges.filter((edge) => edge.source === concept.id);

  return (
    <div className = "ll-scroll" style={{ width: 360, flexShrink: 0, borderLeft: `1px solid ${COLOR.border}`, background: COLOR.bg, overflowY: "auto", padding: "16px 18px", fontSize: 13 }}>
      <div style={{ fontSize: 11, color: COLOR.textFaint, marginBottom: 4 }}>
        <EntityLink id={concept.id} onInspect={onInspect}>
          {concept.id}
        </EntityLink>
      </div>
      <div style={{ fontSize: 15, fontWeight: 600, color: COLOR.text }}>{concept.title}</div>
      <div style={{ marginTop: 4, display: "flex", gap: 6, flexWrap: "wrap" }}>
        <Pill color={conceptPillColor(concept.type)}>{concept.type}</Pill>
        {concept.aliases.map((alias) => (
          <Pill key={alias} color="slate">
            {alias}
          </Pill>
        ))}
      </div>

      {concept.description ? <div style={{ marginTop: 12, color: COLOR.text, lineHeight: 1.55 }}>{concept.description}</div> : null}

      <SectionHeader>Edges</SectionHeader>
      <div style={{ display: "grid", gap: 4 }}>
        {incoming.map((edge) => (
          <div key={`in-${edge.id}`} style={{ display: "flex", gap: 8, alignItems: "center", fontSize: 12 }}>
            <span style={{ color: relationStyle(edge.relationType).stroke, width: 78 }}>← {relationStyle(edge.relationType).label}</span>
            <Dim>{edge.source}</Dim>
          </div>
        ))}
        {outgoing.map((edge) => (
          <div key={`out-${edge.id}`} style={{ display: "flex", gap: 8, alignItems: "center", fontSize: 12 }}>
            <span style={{ color: relationStyle(edge.relationType).stroke, width: 78 }}>→ {relationStyle(edge.relationType).label}</span>
            <Dim>{edge.target}</Dim>
          </div>
        ))}
        {incoming.length === 0 && outgoing.length === 0 ? <Faint>no edges</Faint> : null}
      </div>

      <SectionHeader>Learning objects</SectionHeader>
      {concept.learningObjects.length === 0 ? <Faint>none</Faint> : null}
      {concept.learningObjects.map((lo) => (
        <div
          key={lo.id}
          style={{ display: "grid", gridTemplateColumns: "1fr 80px 40px", gap: 8, alignItems: "center", padding: "6px 0", borderTop: `1px solid ${COLOR.border}`, fontSize: 12 }}
        >
          <span>
            <div style={{ color: COLOR.text }}>{lo.title}</div>
            <EntityLink id={lo.id} onInspect={onInspect}>
              <Meta>{lo.id}</Meta>
            </EntityLink>
          </span>
          {lo.mastery == null ? (
            <Faint>—</Faint>
          ) : (
            <BlockBar value={lo.mastery} width={8} color={masteryColor(lo.mastery)} />
          )}
          <Dim style={{ textAlign: "right" }}>{lo.mastery == null ? "" : lo.mastery.toFixed(2)}</Dim>
        </div>
      ))}

      <SectionHeader>State</SectionHeader>
      <div style={{ display: "grid", gap: 4, fontSize: 12 }}>
        <div>
          <Faint>practice items</Faint> <Dim>{concept.practiceItemCount}</Dim>
        </div>
        <div>
          <Faint>open error events</Faint>{" "}
          <span style={{ color: concept.openErrorEventCount > 0 ? COLOR.red : COLOR.green }}>{concept.openErrorEventCount}</span>
        </div>
      </div>
    </div>
  );
}
