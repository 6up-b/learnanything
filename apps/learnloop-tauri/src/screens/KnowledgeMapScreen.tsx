import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import { useCachedQuery } from "../api/useCachedQuery";
import { TAG } from "../api/queryTags";
import type { DecayPressureDto, KnowledgeFacetPoint, KnowledgeMapHistory, KnowledgeMapPoint, KnowledgeMapSnapshot } from "../api/dto";
import { EntityLink } from "../components/ui";
import { COLOR, Dim, Faint, FONT_MONO, KeyBar, Meta, Pill, SectionHeader } from "../components/term";
import { FacetInspector } from "../components/FacetInspector";
import { masteryTone } from "../app/algoConfig";
import { KnowledgeTerrainView } from "./KnowledgeTerrainView";
import { KnowledgeWellView } from "./KnowledgeWellView";
import { KnowledgeStrataView } from "./KnowledgeStrataView";
import { useElementSize } from "./wire3d";

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
  // The map is the most expensive read in the app (pure-Python MDS plus a
  // scheduler pass), so it is cached with generous freshness: returning to
  // the field repaints instantly and revalidates only after five minutes or
  // an explicit invalidation (attempts, proposals, vault edits).
  const snapshotQuery = useCachedQuery(["get_knowledge_map"], () => api.getKnowledgeMap(), {
    tags: [TAG.graph],
    staleAfterMs: 5 * 60_000
  });
  const snapshot: KnowledgeMapSnapshot | null = snapshotQuery.data ?? null;
  // Sticky hover selection, same convention as the facet radar: the last point
  // touched stays selected until another one is hovered/clicked.
  const [selected, setSelected] = useState<string | null>(null);
  // Hard select (well view): clicking a node latches it, so drifting the
  // pointer across the field can no longer steal the sidebar out from under
  // whatever the user was reading. The latch releases when the pointer reaches
  // the sidebar — by then they have arrived at what the pick was for, and
  // coming back to the field is a fresh look.
  const [pinned, setPinned] = useState(false);
  const [mode, setMode] = useState<"terrain" | "well" | "strata">("terrain");
  // The strata view's history feed loads lazily on first switch and then stays
  // cached across tab switches.
  const historyQuery = useCachedQuery(["get_knowledge_map_history"], () => api.getKnowledgeMapHistory(), {
    tags: [TAG.graph, TAG.review],
    enabled: mode === "strata",
    staleAfterMs: 5 * 60_000
  });
  const history: KnowledgeMapHistory | null = historyQuery.data ?? null;
  // The well view's decay-pressure feed (which facets the FSRS model holds flat
  // for lack of history, and which cross target soon). Fetched lazily on first
  // switch to "well"; the view degrades gracefully to no-decay if it's absent.
  const decayQuery = useCachedQuery(["get_decay_pressure", null], () => api.getDecayPressure(), {
    tags: [TAG.goals, TAG.queue],
    enabled: mode === "well",
    staleAfterMs: 60_000
  });
  const decay: DecayPressureDto | null = decayQuery.data?.pressure ?? null;
  // One facet side window owns both its semantic contract and evidence receipt.
  // Facets have no map coordinate — we join by id.
  const [inspectFacetId, setInspectFacetId] = useState<string | null>(null);
  // The canvas hands its live pixel box to whichever view is showing, so the
  // scene fills the pane instead of sitting in a fixed 860-wide letterbox.
  const canvas = useElementSize<HTMLDivElement>();

  // Load failures surface as toasts, as before; whatever was cached stays up.
  const loadError = snapshotQuery.error ?? historyQuery.error ?? decayQuery.error;
  useEffect(() => {
    if (loadError) onError(loadError.message);
  }, [loadError, onError]);

  // Keeps the selection valid for the current field (and picks the first
  // point when nothing is selected yet, including right after the map loads).
  useEffect(() => {
    if (!snapshot) return;
    setSelected((current) => {
      const candidates = mode === "strata" ? snapshot.points : snapshot.facetField.points;
      return candidates.some((point) => point.id === current) ? current : candidates[0]?.id ?? null;
    });
  }, [mode, snapshot]);

  // A latch only makes sense against the field the user latched it on.
  useEffect(() => setPinned(false), [mode]);

  const points = snapshot?.points ?? [];

  // Per-facet lock state (§3.4), joined by canonical facet id. Locks live on the
  // facet-field points themselves; legacy facets carry `locked: false`.
  const facetLockById = useMemo(() => {
    const map = new Map<string, KnowledgeFacetPoint>();
    for (const point of snapshot?.facetField.points ?? []) map.set(point.id, point);
    return map;
  }, [snapshot]);

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
          <div
            className="ll-scroll"
            style={{
              position: "absolute",
              inset: 0,
              overflow: "auto",
              padding: 24,
              display: "flex",
              flexDirection: "column"
            }}
          >
            <div style={{ marginBottom: 8, display: "flex", justifyContent: "space-between", alignItems: "center", flexShrink: 0 }}>
              <div>
                <span style={{ color: COLOR.amber, fontSize: 13 }}>knowledge-map</span>{" "}
                <Meta>
                  {snapshot.facetField.points.length} facets · {snapshot.counts.concepts} concepts
                </Meta>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 12 }}>
                <span style={{ display: "flex", gap: 4 }}>
                  <Faint>view:</Faint>
                  {(["terrain", "well", "strata"] as const).map((id) => (
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
                <Faint>stress {(mode === "strata" ? snapshot.stress : snapshot.facetField.stress).toFixed(2)}</Faint>
              </div>
            </div>

            {(mode === "strata" ? points.length : snapshot.facetField.points.length) === 0 ? (
              <div style={{ color: COLOR.textFaint, fontSize: 13, padding: 30 }}>no mapped evidence yet</div>
            ) : mode === "strata" ? (
              // Strata is a list: it takes the full width but keeps its own
              // content height, so the pane scrolls rather than squashing rows.
              <div ref={canvas.ref} style={{ flex: "0 0 auto", minHeight: 0 }}>
                {history == null ? (
                  <div style={{ color: COLOR.textFaint, fontSize: 13, padding: 30 }}>loading strata…</div>
                ) : (
                  <KnowledgeStrataView
                    points={points}
                    history={history}
                    selected={selected}
                    onSelect={setSelected}
                    onInspect={onInspect}
                    width={canvas.width}
                  />
                )}
              </div>
            ) : (
              // The 3D views take the whole remaining box; they size their own
              // viewBox to it, so there is never dead background around them.
              <div ref={canvas.ref} style={{ flex: 1, minHeight: 0, position: "relative" }}>
                {canvas.width > 0 && canvas.height > 0 ? (
                  mode === "terrain" ? (
                    <KnowledgeTerrainView
                      field={snapshot.facetField}
                      selected={selected}
                      onSelect={setSelected}
                      onInspect={onInspect}
                      width={canvas.width}
                      height={canvas.height}
                    />
                  ) : (
                    <KnowledgeWellView
                      field={snapshot.facetField}
                      decay={decay}
                      selected={selected}
                      onSelect={(id) => {
                        if (!pinned) setSelected(id);
                      }}
                      onPin={(id) => {
                        setSelected(id);
                        setPinned(true);
                      }}
                      onInspect={onInspect}
                      width={canvas.width}
                      height={canvas.height}
                    />
                  )
                ) : null}
              </div>
            )}
          </div>
        </div>

        {mode !== "strata" ? (
          <FacetFieldDetail
            point={activeFacet}
            nextGap={snapshot.facetField.nextGap?.facetId === activeFacet?.id ? snapshot.facetField.nextGap : null}
            onInspect={onInspect}
            onInspectFacet={setInspectFacetId}
            pinned={pinned}
            onEnter={() => setPinned(false)}
          />
        ) : (
          <PointDetail point={active} onInspect={onInspect} facetLockById={facetLockById} onInspectFacet={setInspectFacetId} />
        )}
      </div>

      {inspectFacetId ? (
        <FacetInspector
          facetId={inspectFacetId}
          onClose={() => setInspectFacetId(null)}
          onInspect={onInspect}
          onError={onError}
        />
      ) : null}

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
        ) : mode === "well" ? (
          <>
            <Faint>well:</Faint>
            <span style={{ color: COLOR.textDim }}>depth = Ready × evidence · flat = unexplored</span>
            <span style={{ color: COLOR.green }}>● filled bead = Demonstrated</span>
            <span style={{ color: COLOR.cyan }}>○ hollow = predicted, not demonstrated</span>
            <span style={{ color: COLOR.cyan }}>◌ ghost ring = relaxing after decay</span>
            <span style={{ color: COLOR.textDim }}>◇ dashed = held flat, not enough history</span>
            <Dim>× means no blueprint, not failure · contours bunch at the frontier</Dim>
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
        <span style={{ color: COLOR.amber }}>🔒 locked facet</span>
        <Dim>locked = history is significant; unlocked facets still merge/split cheaply</Dim>
        <span style={{ flex: 1 }} />
        <Faint>
          {mode === "strata"
            ? "similarity map — distances are approximate"
            : mode === "well"
              ? "ambient surface — Ready leads, values live in the side panel"
              : "recipe graph field — values live in the capability grid"}
        </Faint>
      </div>

      <KeyBar
        keys={[
          { key: "hover", label: "Select item" },
          { key: "click", label: "Inspect" },
          ...(mode === "terrain"
            ? [{ key: "drag", label: "Orbit" }]
            : mode === "well"
              ? [{ key: "drag", label: "Orbit" }, { key: "← →", label: "Facets" }]
              : [{ key: "hover", label: "Crosshair date" }])
        ]}
        right={{ key: "^p", label: "palette" }}
      />
    </div>
  );
}

export function FacetFieldDetail({
  point,
  nextGap,
  onInspect,
  onInspectFacet,
  pinned,
  onEnter
}: {
  point: KnowledgeFacetPoint | null;
  nextGap: KnowledgeMapSnapshot["facetField"]["nextGap"];
  onInspect: (id: string) => void;
  onInspectFacet?: (facetId: string) => void;
  /** The field's selection is latched on this facet (well view click). */
  pinned?: boolean;
  /** Pointer reached the sidebar — releases the field's hard select. */
  onEnter?: () => void;
}) {
  if (!point) {
    return (
      <div
        onMouseEnter={onEnter}
        style={{ width: 320, flexShrink: 0, borderLeft: `1px solid ${COLOR.border}`, padding: "16px 18px", color: COLOR.textFaint }}
      >
        hover a facet
      </div>
    );
  }
  const stat = (label: string, value: string, color?: string) => (
    <div style={{ display: "flex", justifyContent: "space-between", gap: 10, padding: "3px 0", fontSize: 12 }}>
      <Faint>{label}</Faint><span style={{ color: color ?? COLOR.text, fontFamily: FONT_MONO }}>{value}</span>
    </div>
  );
  return (
    <div
      className="ll-scroll"
      onMouseEnter={onEnter}
      style={{ width: 320, flexShrink: 0, borderLeft: `1px solid ${COLOR.border}`, background: COLOR.bg, overflowY: "auto", padding: "16px 18px", fontSize: 13 }}
    >
      <div style={{ fontSize: 11, color: COLOR.textFaint, marginBottom: 4, display: "flex", justifyContent: "space-between", gap: 8 }}>
        <span>evidence facet</span>
        {/* Without this the field just stops responding to hover and reads as
            broken; name the latch and how to drop it. */}
        {pinned ? <span style={{ color: COLOR.amber }} title="click latched this facet — move here to unlatch">pinned</span> : null}
      </div>
      <div style={{ fontSize: 14, fontWeight: 600 }}>
        {point.title}
        {point.locked ? <span style={{ color: COLOR.amber, marginLeft: 6 }} title={`🔒 locked · ${point.lockSources.join(", ") || "identity locked"}`}>🔒</span> : null}
      </div>
      <Meta>{point.id}</Meta>
      {onInspectFacet ? (
        <div style={{ marginTop: 6, display: "flex", gap: 6, flexWrap: "wrap" }}>
          <button
            type="button"
            onClick={() => onInspectFacet(point.id)}
            title="open facet evidence, contract, membership, and restructure tools"
            style={facetActionButton}
          >
            inspect facet ▸
          </button>
        </div>
      ) : null}
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

const facetActionButton: CSSProperties = {
  fontFamily: FONT_MONO,
  fontSize: 12,
  color: COLOR.amber,
  background: COLOR.bgInput,
  border: `1px solid ${COLOR.amber}`,
  borderRadius: 2,
  padding: "2px 10px",
  cursor: "pointer"
};

function PointDetail({
  point,
  onInspect,
  facetLockById,
  onInspectFacet
}: {
  point: KnowledgeMapPoint | null;
  onInspect: (id: string) => void;
  facetLockById: Map<string, KnowledgeFacetPoint>;
  onInspectFacet: (facetId: string) => void;
}) {
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
      {stat("mastery estimate (LO)", point.mastery != null ? point.mastery.toFixed(2) : null, tone)}
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
      <Faint style={{ fontSize: 11 }}>click a facet to open its contract inspector</Faint>
      {point.facets.map((facet) => {
        const entry = facetLockById.get(facet);
        const locked = entry?.locked ?? false;
        return (
          <div
            key={facet}
            role="button"
            tabIndex={0}
            onClick={() => onInspectFacet(facet)}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                onInspectFacet(facet);
              }
            }}
            title={locked ? `🔒 locked · ${entry?.lockSources.join(", ") || "identity locked"}` : "unlocked (pre-lock)"}
            style={{
              display: "flex",
              justifyContent: "space-between",
              gap: 8,
              fontSize: 12,
              padding: "2px 0",
              color: COLOR.amberLink,
              cursor: "pointer",
              overflowWrap: "anywhere"
            }}
          >
            <span>{facet}</span>
            {locked ? <span style={{ color: COLOR.amber, flexShrink: 0 }}>🔒</span> : null}
          </div>
        );
      })}
    </div>
  );
}
