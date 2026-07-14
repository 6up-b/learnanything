import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { KnowledgeFacetPoint, KnowledgeMapHistory, KnowledgeMapPoint, KnowledgeMapSnapshot } from "../api/dto";
import { EntityLink } from "../components/ui";
import { COLOR, Dim, Faint, FONT_MONO, KeyBar, Meta, Pill, SectionHeader } from "../components/term";
import { masteryTone } from "../app/algoConfig";
import { KnowledgeTerrainView } from "./KnowledgeTerrainView";
import { KnowledgeStrataView } from "./KnowledgeStrataView";

// Knowledge map with two complementary read levels:
//
//  - "terrain" (default): a recipe-graph dual manifold. Solid Demonstrated
//    evidence bends the lower sheet; vaporous Ready prediction bends the upper.
//  - "strata": belief stratigraphy — one row per learning object (ordered so
//    latent-space neighbors are adjacent), x = time, each row carrying the
//    mastery step-series with attempt ticks and frontier-crossing marks, plus
//    an aggregate portfolio band. History (attempt events + reconstructed
//    mastery series) loads lazily on first switch.
//
// Sticky hover selects a facet; exact values remain in the capability grid.

const FRONTIER_LEVEL = 0.7;

export function KnowledgeMapView({ onInspect, onError }: { onInspect: (id: string) => void; onError: (message: string) => void }) {
  const [snapshot, setSnapshot] = useState<KnowledgeMapSnapshot | null>(null);
  // Sticky hover selection, same convention as the facet radar: the last point
  // touched stays selected until another one is hovered/clicked.
  const [selected, setSelected] = useState<string | null>(null);
  const [mode, setMode] = useState<"terrain" | "strata">("terrain");
  const [history, setHistory] = useState<KnowledgeMapHistory | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getKnowledgeMap()
      .then((data) => {
        if (cancelled) return;
        setSnapshot(data);
        setSelected((current) => current ?? data.facetField.points[0]?.id ?? null);
      })
      .catch((error) => {
        if (!cancelled) onError(error.message);
      });
    return () => {
      cancelled = true;
    };
  }, [onError]);

  // The strata view's history feed is only fetched once, on first switch.
  useEffect(() => {
    if (mode !== "strata" || history != null) return;
    let cancelled = false;
    api
      .getKnowledgeMapHistory()
      .then((data) => {
        if (!cancelled) setHistory(data);
      })
      .catch((error) => {
        if (!cancelled) onError(error.message);
      });
    return () => {
      cancelled = true;
    };
  }, [mode, history, onError]);

  useEffect(() => {
    if (!snapshot) return;
    setSelected((current) => {
      const candidates = mode === "terrain" ? snapshot.facetField.points : snapshot.points;
      return candidates.some((point) => point.id === current) ? current : candidates[0]?.id ?? null;
    });
  }, [mode, snapshot]);

  const points = snapshot?.points ?? [];

  if (!snapshot) {
    return <div style={{ padding: 30, color: COLOR.textFaint, fontSize: 13 }}>loading knowledge map…</div>;
  }

  const pointById = new Map(points.map((point) => [point.id, point] as const));
  const facetById = new Map(snapshot.facetField.points.map((point) => [point.id, point] as const));
  const active = selected ? pointById.get(selected) ?? null : null;
  const activeFacet = selected ? facetById.get(selected) ?? null : null;

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
        {/* Canvas */}
        <div style={{ flex: 1, position: "relative", overflow: "hidden", background: COLOR.bg }}>
          {/* Grid backdrop — same treatment as the concept map and radar */}
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
              pointerEvents: "none"
            }}
          />
          <div
            style={{
              position: "absolute",
              inset: 0,
              backgroundImage: `radial-gradient(circle at 0 0, ${COLOR.border} 1.5px, transparent 1.5px)`,
              backgroundSize: "24px 24px",
              opacity: 0.5,
              pointerEvents: "none"
            }}
          />
          <div className="ll-scroll" style={{ position: "absolute", inset: 0, overflow: "auto", padding: 24 }}>
            <div style={{ marginBottom: 8, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <span style={{ color: COLOR.amber, fontSize: 13 }}>knowledge-map</span>{" "}
                <Meta>
                  {snapshot.facetField.points.length} facets · {snapshot.counts.concepts} concepts
                </Meta>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 12 }}>
                <span style={{ display: "flex", gap: 4 }}>
                  <Faint>view:</Faint>
                  {(["terrain", "strata"] as const).map((id) => (
                    <button
                      key={id}
                      type="button"
                      onClick={() => setMode(id)}
                      style={{
                        background: mode === id ? "#241d12" : "transparent",
                        border: `1px solid ${mode === id ? COLOR.amber : COLOR.border}`,
                        color: mode === id ? COLOR.amber : COLOR.textDim,
                        font: "inherit",
                        fontFamily: FONT_MONO,
                        padding: "1px 8px",
                        cursor: "pointer",
                        transition: "border-color 0.22s ease, color 0.22s ease"
                      }}
                    >
                      {id}
                    </button>
                  ))}
                </span>
                <Faint>stress {(mode === "terrain" ? snapshot.facetField.stress : snapshot.stress).toFixed(2)}</Faint>
              </div>
            </div>

            {(mode === "terrain" ? snapshot.facetField.points.length : points.length) === 0 ? (
              <div style={{ color: COLOR.textFaint, fontSize: 13, padding: 30 }}>no mapped evidence yet</div>
            ) : mode === "terrain" ? (
              <div style={{ display: "flex", justifyContent: "center" }}>
                <KnowledgeTerrainView field={snapshot.facetField} selected={selected} onSelect={setSelected} onInspect={onInspect} />
              </div>
            ) : history == null ? (
              <div style={{ color: COLOR.textFaint, fontSize: 13, padding: 30 }}>loading strata…</div>
            ) : (
              <div style={{ display: "flex", justifyContent: "center" }}>
                <KnowledgeStrataView
                  points={points}
                  history={history}
                  selected={selected}
                  onSelect={setSelected}
                  onInspect={onInspect}
                />
              </div>
            )}
          </div>
        </div>

        {mode === "terrain" ? (
          <FacetFieldDetail point={activeFacet} nextGap={snapshot.facetField.nextGap?.facetId === activeFacet?.id ? snapshot.facetField.nextGap : null} onInspect={onInspect} />
        ) : (
          <PointDetail point={active} onInspect={onInspect} />
        )}
      </div>

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
        {mode === "terrain" ? (
          <>
            <Faint>markers:</Faint>
            <span style={{ color: COLOR.green }}>━ solid = Demonstrated evidence</span>
            <span style={{ color: COLOR.cyan }}>┄ vapor = Ready prediction</span>
            <span style={{ color: COLOR.amber }}>△ one model-selected Next gap</span>
            <span style={{ color: COLOR.textDim }}>rim: solid certified · hollow required</span>
            <Dim>only Ready fogs · × means no blueprint, not failure</Dim>
          </>
        ) : (
          <>
            <Faint>strata:</Faint>
            <span style={{ color: COLOR.green }}>▁▄ row = LO belief over time</span>
            <span style={{ color: COLOR.amber }}>● frontier crossing ≥ {FRONTIER_LEVEL.toFixed(1)}</span>
            <span style={{ color: COLOR.green }}>| attempt tick (◆ probe)</span>
            <span style={{ color: COLOR.textFaint }}>╌╌ no belief yet</span>
            <Dim>rows ordered by latent similarity · top band = portfolio drift</Dim>
          </>
        )}
        <span style={{ flex: 1 }} />
        <Faint>{mode === "terrain" ? "recipe graph field — values live in the capability grid" : "similarity map — distances are approximate"}</Faint>
      </div>

      <KeyBar
        keys={[
          { key: "hover", label: "Select item" },
          { key: "click", label: "Inspect" },
          ...(mode === "terrain" ? [{ key: "drag", label: "Orbit" }] : [{ key: "hover", label: "Crosshair date" }])
        ]}
        right={{ key: "^p", label: "palette" }}
      />
    </div>
  );
}

export function FacetFieldDetail({
  point,
  nextGap,
  onInspect
}: {
  point: KnowledgeFacetPoint | null;
  nextGap: KnowledgeMapSnapshot["facetField"]["nextGap"];
  onInspect: (id: string) => void;
}) {
  if (!point) {
    return <div style={{ width: 320, flexShrink: 0, borderLeft: `1px solid ${COLOR.border}`, padding: "16px 18px", color: COLOR.textFaint }}>hover a facet</div>;
  }
  const stat = (label: string, value: string, color?: string) => (
    <div style={{ display: "flex", justifyContent: "space-between", gap: 10, padding: "3px 0", fontSize: 12 }}>
      <Faint>{label}</Faint><span style={{ color: color ?? COLOR.text, fontFamily: FONT_MONO }}>{value}</span>
    </div>
  );
  return (
    <div className="ll-scroll" style={{ width: 320, flexShrink: 0, borderLeft: `1px solid ${COLOR.border}`, background: COLOR.bg, overflowY: "auto", padding: "16px 18px", fontSize: 13 }}>
      <div style={{ fontSize: 11, color: COLOR.textFaint, marginBottom: 4 }}>evidence facet</div>
      <div style={{ fontSize: 14, fontWeight: 600 }}>{point.title}</div>
      <Meta>{point.id}</Meta>
      <SectionHeader>Two independent axes</SectionHeader>
      {stat("Demonstrated", `${Math.round(point.demonstratedMass * 100)}%`, COLOR.green)}
      {stat("Ready", `${Math.round(point.ready * 100)}%`, COLOR.cyan)}
      {point.readyGhost - point.ready >= 0.01 ? stat("Ready before decay", `${Math.round(point.readyGhost * 100)}%`, COLOR.textDim) : null}
      {stat("Ready variance", point.readyVariance.toFixed(4))}
      {stat("evidence mass", point.evidenceMass.toFixed(2))}
      {!point.hasBlueprints ? <Pill color="slate">absent · no blueprint</Pill> : null}
      {nextGap ? (
        <div style={{ marginTop: 10, padding: 8, border: `1px solid ${COLOR.amber}`, color: COLOR.amber }}>
          Next · {nextGap.label}
        </div>
      ) : null}
      {point.correction ? (
        <div style={{ marginTop: 8 }}><Pill color="amber">regrade correction {point.correction.delta >= 0 ? "+" : ""}{point.correction.delta.toFixed(2)}</Pill></div>
      ) : null}
      <SectionHeader>Capability rim</SectionHeader>
      {point.capabilityArcs.filter((arc) => arc.status !== "absent").map((arc) => (
        <div key={arc.capability} style={{ display: "flex", justifyContent: "space-between", padding: "3px 0", fontSize: 12 }}>
          <span>{arc.capability}</span>
          <span style={{ color: arc.status === "demonstrated" ? COLOR.green : COLOR.textFaint }}>
            {arc.status === "demonstrated" ? "● demonstrated" : "○ required"}
          </span>
        </div>
      ))}
      {point.ambiguityCandidates.length ? (
        <><SectionHeader>Positional ambiguity</SectionHeader><Faint>candidate causes: {point.ambiguityCandidates.join(", ")}</Faint></>
      ) : null}
      <SectionHeader>Used by</SectionHeader>
      {point.learningObjectIds.length ? point.learningObjectIds.map((id) => (
        <div key={id}><EntityLink id={id} onInspect={onInspect}><Meta>{id}</Meta></EntityLink></div>
      )) : <Faint>no BlueprintRecipe references this facet</Faint>}
    </div>
  );
}

function PointDetail({ point, onInspect }: { point: KnowledgeMapPoint | null; onInspect: (id: string) => void }) {
  if (!point) {
    return (
      <div style={{ width: 320, flexShrink: 0, borderLeft: `1px solid ${COLOR.border}`, background: COLOR.bg, padding: "16px 18px", color: COLOR.textFaint, fontSize: 13 }}>
        hover a point
      </div>
    );
  }
  const tone = point.mastery != null ? masteryTone(point.mastery, COLOR) : COLOR.textFaint;
  const stat = (label: string, value: string | null, color?: string) => (
    <div style={{ display: "flex", justifyContent: "space-between", gap: 10, padding: "3px 0", fontSize: 12 }}>
      <Faint>{label}</Faint>
      <span style={{ color: color ?? COLOR.text, fontFamily: FONT_MONO }}>{value ?? "—"}</span>
    </div>
  );
  return (
    <div className="ll-scroll" style={{ width: 320, flexShrink: 0, borderLeft: `1px solid ${COLOR.border}`, background: COLOR.bg, overflowY: "auto", padding: "16px 18px", fontSize: 13 }}>
      <div style={{ fontSize: 11, color: COLOR.textFaint, marginBottom: 4 }}>practice item</div>
      <div style={{ fontSize: 14, fontWeight: 600, color: COLOR.text }}>{point.title}</div>
      <div style={{ marginTop: 6 }}>
        <EntityLink id={point.id} onInspect={onInspect}>
          <Meta>{point.id}</Meta>
        </EntityLink>
      </div>

      <div style={{ marginTop: 8, display: "flex", gap: 6, flexWrap: "wrap" }}>
        {point.isProbe ? <Pill color="red">probe</Pill> : null}
        {point.queued ? <Pill color="cyan">queued</Pill> : null}
      </div>

      <SectionHeader>Belief</SectionHeader>
      {stat("mastery (LO)", point.mastery != null ? point.mastery.toFixed(2) : null, tone)}
      {stat("variance", point.variance != null ? point.variance.toFixed(3) : null)}
      {stat("p(correct)", point.predictedCorrect != null ? point.predictedCorrect.toFixed(2) : null)}
      {stat("difficulty", point.difficulty != null ? point.difficulty.toFixed(2) : null)}

      <SectionHeader>Location</SectionHeader>
      <div style={{ fontSize: 12, padding: "3px 0" }}>
        <Faint>learning object</Faint>
        <div>
          <EntityLink id={point.learningObjectId} onInspect={onInspect}>
            <Meta>{point.learningObjectId}</Meta>
          </EntityLink>
        </div>
      </div>
      {point.conceptId ? (
        <div style={{ fontSize: 12, padding: "3px 0" }}>
          <Faint>concept</Faint>
          <div>
            <EntityLink id={point.conceptId} onInspect={onInspect}>
              <Meta>{point.conceptId}</Meta>
            </EntityLink>
          </div>
        </div>
      ) : null}

      <SectionHeader>Top facets</SectionHeader>
      {point.facets.length === 0 ? <Faint>none declared</Faint> : null}
      {point.facets.map((facet) => (
        <div key={facet} style={{ fontSize: 12, padding: "2px 0", color: COLOR.textDim, overflowWrap: "anywhere" }}>
          {facet}
        </div>
      ))}
    </div>
  );
}
