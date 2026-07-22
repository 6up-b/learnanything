// KM3b §9.6 provenance UI: attempt trace, unresolved-cause card, capability
// grid, recipe tree, and the facet evidence drawer (Demonstrated timeline).
// Terminal aesthetic — inline styles over term.tsx primitives.
import { useEffect, useState, type ReactNode } from "react";
import { api } from "../api/client";
import type {
  AttemptTraceDto,
  CapabilityGridResult,
  ComponentReadinessDto,
  DemonstratedTimelinePointDto,
  FacetEvidenceTimelineDto,
  LoReadinessDto,
  ObservationDerivationDto,
  ReadyDerivationDto,
  TraceCriterionDto,
  UnresolvedCauseDto,
} from "../api/dto";
import { BlockBar, COLOR, Dim, Faint, FONT_MONO, Pill, SectionHeader, type PillColor } from "./term";
import { CommandOverlayFrame, learnloopShowOverlayWidth } from "./CommandOverlayFrame";

const pct = (value: number | null | undefined): string =>
  value == null ? "—" : `${Math.round(value * 100)}%`;

const shortFacet = (facetId: string): string => facetId.replace(/^facet_/, "");
const facetTitle = (facetId: string): string =>
  shortFacet(facetId)
    .replace(/[_-]+/g, " ")
    .replace(/^\w/, (letter) => letter.toUpperCase());

// -- Attempt trace view (criterion DAG per attempt) ---------------------------

const STATUS_META: Record<TraceCriterionDto["status"], { glyph: string; label: string; color: string; pill: PillColor }> = {
  demonstrated: { glyph: "✓", label: "demonstrated", color: COLOR.green, pill: "green" },
  first_error: { glyph: "✗", label: "first error", color: COLOR.red, pill: "red" },
  not_judged: { glyph: "○", label: "not judged", color: COLOR.textFaint, pill: "slate" },
  partial: { glyph: "◐", label: "partial", color: COLOR.yellow, pill: "amber" },
};

function TraceCriterionRow({ row }: { row: TraceCriterionDto }) {
  const meta = STATUS_META[row.status];
  return (
    <div style={{ padding: "6px 0", borderBottom: `1px solid ${COLOR.border}` }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
        <span style={{ color: meta.color, width: 14, textAlign: "center" }}>{meta.glyph}</span>
        <span style={{ color: COLOR.text, flex: 1 }}>{row.description}</span>
        <Pill color={meta.pill}>{meta.label}</Pill>
        <span style={{ color: COLOR.textDim, minWidth: 44, textAlign: "right" }}>
          {row.pointsAwarded == null ? "—" : row.pointsAwarded}/{row.pointsPossible}
        </span>
      </div>
      <div style={{ marginLeft: 22, marginTop: 2, display: "flex", flexWrap: "wrap", gap: 6, alignItems: "baseline" }}>
        {row.targets.map((t, i) => (
          <Pill key={`${t.facet}:${t.capability}:${i}`} color="slate">
            {shortFacet(t.facet)} · {t.capability}
          </Pill>
        ))}
        {row.dependsOn.length > 0 && <Faint>depends on {row.dependsOn.join(", ")}</Faint>}
        {row.status === "not_judged" && <Faint>downstream of an earlier error — not judged, not wrong</Faint>}
      </div>
    </div>
  );
}

export function AttemptTraceView({ trace }: { trace: AttemptTraceDto }) {
  if (!trace.criteria.length) return null;
  return (
    <div style={{ fontFamily: FONT_MONO }}>
      <div style={{ marginBottom: 6 }}>
        <Pill color="green">{trace.demonstratedCount} demonstrated</Pill>{" "}
        {trace.firstErrorCount > 0 && <Pill color="red">{trace.firstErrorCount} first error</Pill>}{" "}
        {trace.notJudgedCount > 0 && <Pill color="slate">{trace.notJudgedCount} not judged</Pill>}
      </div>
      {trace.criteria.map((row) => (
        <TraceCriterionRow key={row.criterionId} row={row} />
      ))}
    </div>
  );
}

// -- Unresolved-cause diagnostic card -----------------------------------------

export function UnresolvedCauseCard({
  causes,
  onRunDiagnostic,
}: {
  causes: UnresolvedCauseDto[];
  onRunDiagnostic?: () => void;
}) {
  if (!causes.length) return null;
  // The candidate set is the union across factors (each is one ambiguous failure).
  const candidates = new Map<string, { facet: string; capability: string }>();
  for (const factor of causes) {
    for (const cause of factor.candidateCauses) {
      candidates.set(`${cause.facet}:${cause.capability}`, cause);
    }
  }
  const list = Array.from(candidates.values());
  return (
    <div
      style={{
        border: `1px solid ${COLOR.amber}`,
        borderRadius: 4,
        padding: 10,
        fontFamily: FONT_MONO,
        background: COLOR.bgElev,
      }}
    >
      <div style={{ color: COLOR.amber, marginBottom: 4 }}>
        This failure is consistent with {list.length} cause{list.length === 1 ? "" : "s"}
      </div>
      <Dim>The evidence can't yet tell these apart — each implies a different repair.</Dim>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, margin: "8px 0" }}>
        {list.map((cause) => (
          <Pill key={`${cause.facet}:${cause.capability}`} color="amber">
            {shortFacet(cause.facet)} · {cause.capability}
          </Pill>
        ))}
      </div>
      {onRunDiagnostic && (
        <button
          type="button"
          onClick={onRunDiagnostic}
          style={{
            fontFamily: FONT_MONO,
            fontSize: 12,
            color: COLOR.bg,
            background: COLOR.amber,
            border: "none",
            borderRadius: 3,
            padding: "4px 10px",
            cursor: "pointer",
          }}
        >
          ▸ run a short diagnostic
        </button>
      )}
    </div>
  );
}

// -- Recipe tree ("why not ready") --------------------------------------------

function ComponentRow({ c, bottleneck }: { c: ComponentReadinessDto; bottleneck: boolean }) {
  const marker = bottleneck ? "◆" : c.gating ? "●" : "○";
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "14px minmax(0, 1fr) 92px 42px",
        alignItems: "center",
        gap: 8,
        padding: "4px 0",
        fontSize: 11
      }}
    >
      <span aria-hidden style={{ color: bottleneck ? COLOR.red : c.gating ? COLOR.cyan : COLOR.textFaint }}>
        {marker}
      </span>
      <span style={{ color: bottleneck ? COLOR.red : COLOR.text, minWidth: 0, overflowWrap: "anywhere" }}>
        {shortFacet(c.facet)} · {c.capability}
        {!c.gating && <Faint> · facilitating</Faint>}
      </span>
      <BlockBar value={c.predictedRecall} width={8} color={bottleneck ? COLOR.red : COLOR.cyan} />
      <span style={{ textAlign: "right", color: bottleneck ? COLOR.red : COLOR.textDim }}>{pct(c.predictedRecall)}</span>
    </div>
  );
}

export function RecipeTree({ readiness }: { readiness: LoReadinessDto }) {
  if (!readiness.hasBlueprints) return <Faint>No authored blueprints for this objective.</Faint>;
  const bottleneckKey = readiness.bottleneck
    ? `${readiness.bottleneck.facet}:${readiness.bottleneck.capability}`
    : null;
  return (
    <div style={{ fontFamily: FONT_MONO }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", marginBottom: 10 }}>
        <Pill color="cyan">projected ready · {pct(readiness.readiness)}</Pill>
        {readiness.bottleneck && (
          <span style={{ fontSize: 11 }}>
            <Faint>bottleneck</Faint>{" "}
            <span style={{ color: COLOR.red }}>
              ◆ {shortFacet(readiness.bottleneck.facet)} · {readiness.bottleneck.capability}
            </span>
          </span>
        )}
      </div>
      {readiness.blueprints.map((bp) => (
        <div key={bp.blueprintId} style={{ marginBottom: 10, border: `1px solid ${COLOR.border}`, background: COLOR.bgInput }}>
          <div
            style={{
              padding: "7px 10px",
              display: "flex",
              alignItems: "baseline",
              gap: 8,
              flexWrap: "wrap",
              fontSize: 11
            }}
          >
            <Faint>blueprint</Faint>
            <span style={{ color: COLOR.amber, overflowWrap: "anywhere" }}>{bp.blueprintId}</span>
            <span style={{ flex: 1 }} />
            <Faint>weight</Faint> <Dim>{bp.weight}</Dim>
            <Faint>projected</Faint> <span style={{ color: COLOR.cyan }}>{pct(bp.successProbability)}</span>
          </div>
          {bp.recipes.map((recipe) => {
            const isBest = recipe.recipeId === bp.bestRecipeId;
            return (
              <div
                key={recipe.recipeId}
                style={{
                  padding: "8px 10px",
                  borderTop: `1px solid ${COLOR.border}`,
                  borderLeft: `2px solid ${isBest ? COLOR.cyan : "transparent"}`
                }}
              >
                <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", fontSize: 11 }}>
                  <Faint>path</Faint>
                  <span style={{ color: COLOR.textDim, overflowWrap: "anywhere" }}>{recipe.recipeId}</span>
                  <Pill color="slate" style={{ fontSize: 11 }}>
                    {recipe.composition === "conjunctive" ? "all requirements" : recipe.composition.replace(/_/g, " ")}
                  </Pill>
                  {isBest && <Pill color="cyan">current best</Pill>}
                  <span style={{ marginLeft: "auto" }}><Faint>projected </Faint><span style={{ color: COLOR.cyan }}>{pct(recipe.successProbability)}</span></span>
                </div>
                <div style={{ marginTop: 4 }}>
                  {recipe.components.map((c, i) => (
                    <ComponentRow
                      key={`${c.facet}:${c.capability}:${i}`}
                      c={c}
                      bottleneck={`${c.facet}:${c.capability}` === bottleneckKey}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}

// -- Capability grid (facet × capability heatmap) -----------------------------

function GridCell({ demonstrated, ready, tested }: { demonstrated: boolean; ready: number; tested: boolean }) {
  const marker = demonstrated ? "●" : tested ? "◌" : "·";
  const label = demonstrated ? "demonstrated" : tested ? "tested" : "untested";
  const tone = demonstrated ? COLOR.green : tested ? COLOR.cyan : COLOR.textFaint;
  return (
    <td
      style={{
        borderTop: `1px solid ${COLOR.border}`,
        borderRight: `1px solid ${COLOR.border}`,
        padding: "6px 8px",
        background: demonstrated ? "#152018" : COLOR.bgInput,
        minWidth: 104
      }}
    >
      <div style={{ color: tone, fontSize: 11, whiteSpace: "nowrap" }}>
        <span aria-hidden>{marker}</span> {label}
      </div>
      <div style={{ marginTop: 3, display: "flex", alignItems: "center", gap: 6, color: COLOR.textDim, fontSize: 11 }}>
        <BlockBar value={ready} width={5} color={COLOR.cyan} />
        <span>{pct(ready)}</span>
      </div>
    </td>
  );
}

export function CapabilityGridView({ result }: { result: CapabilityGridResult }) {
  const { grid, readiness } = result;
  if (!grid.supported) {
    return <Faint>Capability grid is available for mvp-0.7 vaults; this vault keeps the facet radar.</Faint>;
  }
  const cellOf = new Map(grid.cells.map((c) => [`${c.facetId}:${c.capability}`, c]));
  const required = grid.cells.filter((cell) => cell.required);
  const demonstrated = required.filter((cell) => cell.demonstrated).length;
  const tested = required.filter((cell) => !cell.demonstrated && cell.tested).length;
  const untested = required.length - demonstrated - tested;
  return (
    <div style={{ fontFamily: FONT_MONO }}>
      <div style={{ color: COLOR.textDim, fontSize: 11, lineHeight: 1.5, marginBottom: 10 }}>
        Each required cell pairs a facet with the capability the learner must show. Status reflects direct evidence; the bar is predicted recall.
        <div style={{ display: "flex", alignItems: "baseline", flexWrap: "wrap", gap: 7, marginTop: 7, fontSize: 11 }}>
          <span><b style={{ color: COLOR.text }}>{required.length}</b> required</span>
          <span style={{ color: COLOR.textFaint }}>·</span>
          <span><b style={{ color: COLOR.green }}>{demonstrated}</b> demonstrated</span>
          <span style={{ color: COLOR.textFaint }}>·</span>
          <span><b style={{ color: COLOR.cyan }}>{tested}</b> tested</span>
          <span style={{ color: COLOR.textFaint }}>·</span>
          <span><b style={{ color: untested ? COLOR.amber : COLOR.textFaint }}>{untested}</b> untested</span>
        </div>
      </div>
      <div style={{ overflowX: "auto" }}>
        <table style={{ borderCollapse: "separate", borderSpacing: 0, border: `1px solid ${COLOR.border}`, fontSize: 11, minWidth: "100%" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", padding: "6px 8px", color: COLOR.textFaint, background: COLOR.bgElev, fontWeight: 400 }}>
                facet / capability
              </th>
              {grid.capabilities.map((cap) => (
                <th
                  key={cap}
                  style={{
                    padding: "6px 8px",
                    color: COLOR.amber,
                    background: COLOR.bgElev,
                    borderLeft: `1px solid ${COLOR.border}`,
                    fontSize: 11,
                    fontWeight: 400,
                    overflowWrap: "anywhere"
                  }}
                >
                  {cap}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {grid.facets.map((facet) => (
              <tr key={facet}>
                <td style={{ padding: "6px 8px", color: COLOR.text, whiteSpace: "nowrap", borderTop: `1px solid ${COLOR.border}`, background: COLOR.bgElev }}>
                  {shortFacet(facet)}
                </td>
                {grid.capabilities.map((cap) => {
                  const cell = cellOf.get(`${facet}:${cap}`);
                  if (!cell || !cell.required) {
                    return (
                      <td
                        key={cap}
                        style={{
                          borderTop: `1px solid ${COLOR.border}`,
                          borderRight: `1px solid ${COLOR.border}`,
                          textAlign: "center",
                          color: COLOR.textFaint,
                          background: COLOR.bgInput
                        }}
                      >
                        —
                      </td>
                    );
                  }
                  return <GridCell key={cap} demonstrated={cell.demonstrated} ready={cell.ready} tested={cell.tested} />;
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={{ marginTop: 7, display: "flex", gap: 14, flexWrap: "wrap", fontSize: 11 }}>
        <span style={{ color: COLOR.green }}>● demonstrated</span>
        <span style={{ color: COLOR.cyan }}>◌ tested</span>
        <span style={{ color: COLOR.textFaint }}>· required, untested</span>
        <span style={{ color: COLOR.textFaint }}>— not required</span>
        <Faint>bar = predicted recall</Faint>
      </div>
      {readiness && (
        <div style={{ marginTop: 16, paddingTop: 14, borderTop: `1px solid ${COLOR.border}` }}>
          <div style={{ color: COLOR.textFaint, fontSize: 11, marginBottom: 6 }}>recipe tree · readiness paths</div>
          <div style={{ color: COLOR.textDim, fontSize: 11, lineHeight: 1.55, marginBottom: 10, maxWidth: 720 }}>
            Blueprints define acceptable paths through the requirements. LearnLoop projects each path, uses the strongest current route, and marks its weakest gating requirement as the bottleneck.
          </div>
          <RecipeTree readiness={readiness} />
        </div>
      )}
    </div>
  );
}

// -- Facet evidence drawer (Demonstrated timeline + §5.1 receipt) -------------

// Channel glyphs are never color-only (§4.13): each carries a glyph AND a label.
const CHANNEL_META: Record<
  "direct" | "embedded" | "assisted" | "pooled",
  { glyph: string; label: string; color: string; pill: PillColor }
> = {
  direct: { glyph: "●", label: "direct", color: COLOR.green, pill: "green" },
  embedded: { glyph: "◑", label: "embedded", color: COLOR.cyan, pill: "cyan" },
  assisted: { glyph: "○", label: "assisted (no credit)", color: COLOR.textFaint, pill: "slate" },
  pooled: { glyph: "◇", label: "pooled", color: COLOR.yellow, pill: "amber" },
};

function pointChannel(p: DemonstratedTimelinePointDto): "direct" | "embedded" | "assisted" {
  if (p.assisted) return "assisted";
  const channels = (p.derivation ?? []).map((d) => d.channel);
  if (channels.length > 0 && channels.every((c) => c === "embedded")) return "embedded";
  return "direct";
}

const round3 = (v: number): string => (Math.round(v * 1000) / 1000).toString();

function formatEvidenceTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function ReceiptEntityLink({
  children,
  title,
  onClick
}: {
  children: ReactNode;
  title: string;
  onClick: () => void;
}) {
  return (
    <button type="button" title={title} onClick={onClick} style={receiptEntityLinkStyle}>
      <span aria-hidden style={{ marginRight: 4 }}>↗</span>
      <span style={receiptEntityLinkLabelStyle}>{children}</span>
    </button>
  );
}

const BOUND_LABEL: Record<string, string> = {
  group_budget: "correlation-group budget",
  attempt_ceiling: "attempt-wide ceiling",
};

// The §5.1 Ready-derivation sentence, template-rendered from ledger ingredients.
function ReadyDerivationLine({ ready }: { ready: ReadyDerivationDto }) {
  const n = ready.directObservationCount;
  const u = ready.unassistedObservationCount;
  const slices = ready.pooledCapabilities.length;
  const days = ready.daysSinceLastEvidence;
  return (
    <section style={{ marginTop: 16 }}>
      <div style={receiptSectionLabelStyle}>readiness receipt</div>
      <div style={{ padding: "10px 12px", border: `1px solid ${COLOR.border}`, borderLeft: `2px solid ${COLOR.amber}`, background: COLOR.bgInput }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 8, flexWrap: "wrap" }}>
          <span style={{ color: COLOR.amber, fontSize: 18, fontWeight: 600 }}>{pct(ready.pooledRecallMean)}</span>
          <span style={{ color: COLOR.textDim, fontSize: 11 }}>pooled ready recall</span>
        </div>
        <div style={{ marginTop: 5, color: COLOR.text, fontSize: 11, lineHeight: 1.55 }}>
          {n} direct observation{n === 1 ? "" : "s"} ({u} unassisted)
          {slices > 0 && (
            <>
              , pooled across {slices} capability slice{slices === 1 ? "" : "s"} (
              {ready.pooledCapabilities.map((s) => s.capability).join(", ")})
            </>
          )}
          {days != null && (
            <>
              , last evidence {days} day{days === 1 ? "" : "s"} ago
            </>
          )}
        </div>
        <div style={{ marginTop: 5, fontVariantNumeric: "tabular-nums", fontSize: 10 }}>
          <Faint>
            β({round3(ready.recallAlpha)}, {round3(ready.recallBeta)}) · independent evidence mass{" "}
            {round3(ready.independentEvidenceMass)}
          </Faint>
        </div>
        {ready.notes.map((note, i) => (
          <div key={i} style={{ marginTop: 2, fontSize: 10 }}>
            <Faint>· {note}</Faint>
          </div>
        ))}
      </div>
    </section>
  );
}

// One observation's per-cell derivation (raw vs capped credit + binding rule).
function ObservationDetail({
  point,
  ordinal,
  onInspect
}: {
  point: DemonstratedTimelinePointDto;
  ordinal: number;
  onInspect: (entityId: string) => void;
}) {
  const rows = point.derivation ?? [];
  const channel = pointChannel(point);
  const channelMeta = CHANNEL_META[channel];
  const deltaTone = point.delta < 0 ? COLOR.red : point.delta > 0 ? COLOR.green : COLOR.textFaint;
  return (
    <article style={{ marginTop: 9, border: `1px solid ${COLOR.borderStrong}`, borderLeft: `2px solid ${channelMeta.color}`, background: COLOR.bgInput }}>
      <div style={{ padding: "10px 12px", borderBottom: `1px solid ${COLOR.border}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
          <span style={observationEyebrowStyle}>observation {String(ordinal).padStart(2, "0")}</span>
          <span style={{ color: channelMeta.color, fontSize: 10 }}>{channelMeta.glyph} {channelMeta.label}</span>
          <span style={{ flex: 1 }} />
          <span style={{ color: deltaTone, fontSize: 11, fontWeight: 600 }}>
            {point.delta > 0 ? "▲ +" : point.delta < 0 ? "▼ " : "＝ "}{pct(point.delta)}
          </span>
          {point.isCorrection ? <Pill color="red">correction</Pill> : null}
          {point.primed ? <Pill color="amber">primed</Pill> : null}
        </div>
        <div style={{ display: "flex", alignItems: "baseline", gap: 8, flexWrap: "wrap", marginTop: 7, fontSize: 10 }}>
          <ReceiptEntityLink title={`learnloop show ${point.attemptId}`} onClick={() => onInspect(point.attemptId)}>
            <time dateTime={point.t}>{formatEvidenceTime(point.t)}</time>
          </ReceiptEntityLink>
          <Faint>· attempt</Faint>
          <ReceiptEntityLink title={`learnloop show ${point.attemptId}`} onClick={() => onInspect(point.attemptId)}>
            {point.attemptId}
          </ReceiptEntityLink>
          {point.surfaceGroup ? <Faint>· surface {point.surfaceGroup}</Faint> : null}
        </div>
      </div>
      {rows.length === 0 ? (
        <div style={{ padding: "10px 12px", color: COLOR.textDim, fontSize: 10 }}>
          {point.assisted ? "Assisted observation — certifies no direct credit." : "No direct credit was recorded for this observation."}
        </div>
      ) : (
        rows.map((d, i) => {
          const meta = CHANNEL_META[d.channel];
          return (
            <div
              key={`${d.capability}:${i}`}
              style={{ display: "grid", gridTemplateColumns: "16px minmax(0, 1fr) auto", gap: 8, alignItems: "start", padding: "9px 12px", borderTop: i > 0 ? `1px solid ${COLOR.border}` : "none", fontVariantNumeric: "tabular-nums" }}
            >
              <span style={{ color: meta.color, textAlign: "center" }}>{meta.glyph}</span>
              <div style={{ minWidth: 0 }}>
                <div style={{ color: COLOR.text, fontSize: 11 }}>{d.capability}</div>
                <div style={{ marginTop: 3, color: COLOR.textFaint, fontSize: 9, lineHeight: 1.45 }}>
                  {meta.label}
                  {d.rawCredit !== d.cappedCredit ? ` · staged ${round3(d.rawCredit)}` : ""}
                  {d.boundBy.length > 0 ? ` · bound by ${d.boundBy.map((b) => BOUND_LABEL[b] ?? b).join(" + ")}` : ""}
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ color: meta.color, fontSize: 14, fontWeight: 600 }}>{round3(d.cappedCredit)}</div>
                <div style={{ color: COLOR.textFaint, fontSize: 9, marginTop: 2 }}>banked credit</div>
              </div>
            </div>
          );
        })
      )}
    </article>
  );
}

// The evidence scrubber (§5.1): each observation a keyboard-reachable tick.
function EvidenceScrubber({
  points,
  selected,
  onSelect,
}: {
  points: DemonstratedTimelinePointDto[];
  selected: number | null;
  onSelect: (i: number) => void;
}) {
  if (!points.length) return null;
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 5, margin: "7px 0" }} role="group" aria-label="Evidence observations">
      {points.map((p, i) => {
        const channel = pointChannel(p);
        const meta = CHANNEL_META[channel];
        const isSel = selected === i;
        const label = `${p.t}, ${meta.label}${p.isCorrection ? ", correction" : ""}${p.primed ? ", primed" : ""}`;
        return (
          <button
            key={`${p.attemptId}:${p.t}:${i}`}
            type="button"
            onClick={() => onSelect(i)}
            aria-pressed={isSel}
            aria-label={label}
            title={label}
            style={{
              fontFamily: FONT_MONO,
              cursor: "pointer",
              background: isSel ? "#241d12" : COLOR.bgInput,
              border: `1px solid ${isSel ? COLOR.amber : COLOR.border}`,
              borderRadius: 2,
              padding: "4px 7px",
              color: meta.color,
              display: "inline-flex",
              alignItems: "center",
              gap: 5,
            }}
          >
            <span style={{ color: isSel ? COLOR.amber : COLOR.textFaint, fontSize: 9, letterSpacing: "0.08em" }}>
              {String(i + 1).padStart(2, "0")}
            </span>
            <span style={{ fontSize: 10 }}>{meta.glyph}</span>
            {p.isCorrection ? <span style={{ color: COLOR.red, fontSize: 9 }}>↩</span> : null}
          </button>
        );
      })}
    </div>
  );
}

function ScrubberLegend() {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 10, margin: "2px 0 6px" }}>
      {(["direct", "embedded", "assisted"] as const).map((c) => (
        <span key={c} style={{ display: "inline-flex", gap: 4, alignItems: "baseline" }}>
          <span style={{ color: CHANNEL_META[c].color, fontSize: 10 }}>{CHANNEL_META[c].glyph}</span>
          <Faint style={{ fontSize: 9 }}>{CHANNEL_META[c].label}</Faint>
        </span>
      ))}
      <span style={{ display: "inline-flex", gap: 4, alignItems: "baseline" }}>
        <span style={{ color: COLOR.red, fontSize: 10 }}>▲</span>
        <Faint style={{ fontSize: 9 }}>correction</Faint>
      </span>
    </div>
  );
}

function DemonstratedCurve({ timeline }: { timeline: FacetEvidenceTimelineDto }) {
  const points = timeline.points;
  if (!points.length) return <Faint>No demonstrated evidence yet.</Faint>;
  const w = 560;
  const h = 112;
  const left = 28;
  const right = 8;
  const top = 8;
  const bottom = 18;
  const xs = (i: number) => (points.length === 1 ? (w + left - right) / 2 : left + (i * (w - left - right)) / (points.length - 1));
  const ys = (value: number) => top + (1 - Math.max(0, Math.min(1, value))) * (h - top - bottom);
  const path = points.map((p, i) => `${i === 0 ? "M" : "L"}${xs(i).toFixed(1)},${ys(p.demonstrated).toFixed(1)}`).join(" ");
  return (
    <svg width="100%" viewBox={`0 0 ${w} ${h}`} style={{ display: "block" }} role="img" aria-label="Demonstrated curve">
      {[0, 0.5, 1].map((value) => (
        <g key={value}>
          <line x1={left} x2={w - right} y1={ys(value)} y2={ys(value)} stroke={COLOR.border} strokeWidth={1} />
          <text x={left - 5} y={ys(value) + 3} fill={COLOR.textFaint} fontSize={8} textAnchor="end">
            {Math.round(value * 100)}%
          </text>
        </g>
      ))}
      <path d={path} fill="none" stroke={COLOR.green} strokeWidth={1.5} />
      {points.map((p, i) => (
        <circle
          key={`${p.attemptId}:${p.t}:${i}`}
          cx={xs(i)}
          cy={ys(p.demonstrated)}
          r={p.isCorrection ? 3.5 : 2}
          fill={p.isCorrection ? COLOR.red : COLOR.green}
          stroke={COLOR.bgInput}
          strokeWidth={1}
        >
          <title>
            {p.t} · demonstrated {pct(p.demonstrated)}
            {p.isCorrection ? ` · correction (${p.delta >= 0 ? "+" : ""}${pct(p.delta)})` : ""}
            {p.assisted ? " · assisted (no credit)" : ""}
          </title>
        </circle>
      ))}
    </svg>
  );
}

export function FacetEvidenceReceipt({ facetId, onInspect }: { facetId: string; onInspect: (entityId: string) => void }) {
  const [timeline, setTimeline] = useState<FacetEvidenceTimelineDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<number | null>(null);

  useEffect(() => {
    let alive = true;
    setTimeline(null);
    setError(null);
    setSelected(null);
    api
      .getFacetEvidenceTimeline(facetId)
      .then((t) => alive && setTimeline(t))
      .catch((e) => alive && setError(e?.message ?? "failed to load timeline"));
    return () => {
      alive = false;
    };
  }, [facetId]);

  const corrections = timeline?.points.filter((p) => p.isCorrection) ?? [];
  const latestCaps = timeline?.points.length
    ? timeline.points[timeline.points.length - 1].demonstratedCapabilities
    : [];
  const latestPoint = timeline?.points.length ? timeline.points[timeline.points.length - 1] : null;
  const latestTone = latestPoint && latestPoint.delta < 0
    ? COLOR.red
    : latestPoint && latestPoint.delta > 0
      ? COLOR.green
      : COLOR.textFaint;

  return (
    <div style={{ fontFamily: FONT_MONO }}>
      {error ? <div style={{ padding: 18, color: COLOR.red, fontSize: 11 }}>{error}</div> : null}
      {!error && !timeline ? <div style={{ padding: 18, color: COLOR.textFaint, fontSize: 11 }}>reading evidence ledger…</div> : null}
      {timeline && (
        <>
          <div style={receiptHeroStyle}>
            <div style={receiptStatusLineStyle}>
              <span style={receiptContextStyle}>facet evidence · immutable ledger</span>
              <span style={receiptSeparatorStyle}>·</span>
              <span><b style={{ color: COLOR.green }}>{timeline.points.length}</b> <span style={{ color: COLOR.textDim }}>observations</span></span>
              <span style={receiptSeparatorStyle}>·</span>
              <span><b style={{ color: corrections.length ? COLOR.red : COLOR.textFaint }}>{corrections.length}</b> <span style={{ color: COLOR.textDim }}>corrections</span></span>
            </div>
            <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap", marginTop: 7 }}>
              <h1 style={receiptTitleStyle}>{facetTitle(facetId)}</h1>
              <span style={{ color: COLOR.textFaint, fontSize: 10 }}>{facetId}</span>
            </div>
            <div style={{ marginTop: 7, display: "flex", alignItems: "baseline", gap: 7, flexWrap: "wrap" }}>
              <span style={{ color: COLOR.green, fontSize: 18, fontWeight: 600 }}>{pct(timeline.demonstrated)}</span>
              <span style={{ color: COLOR.textDim, fontSize: 11 }}>demonstrated</span>
              {latestCaps.length > 0 ? (
                <>
                  <span style={receiptSeparatorStyle}>·</span>
                  <span style={{ color: COLOR.cyan, fontSize: 11 }}>{latestCaps.length}</span>
                  <span style={{ color: COLOR.textDim, fontSize: 11 }}>capabilities represented</span>
                </>
              ) : null}
              {latestPoint ? (
                <>
                  <span style={receiptSeparatorStyle}>·</span>
                  <span style={{ color: latestTone, fontSize: 11, fontWeight: 600 }}>
                    {latestPoint.delta > 0 ? "▲ +" : latestPoint.delta < 0 ? "▼ " : "＝ "}{pct(latestPoint.delta)}
                  </span>
                  <span style={{ color: COLOR.textDim, fontSize: 11 }}>latest evidence</span>
                </>
              ) : null}
              {!timeline.supported ? <Faint style={{ fontSize: 10 }}>legacy vault · no capability ledger</Faint> : null}
            </div>
          </div>

          <div style={receiptBodyStyle}>
            <section>
              <div style={receiptSectionLabelStyle}>demonstrated curve</div>
              <div style={{ color: COLOR.textDim, fontSize: 10, lineHeight: 1.5, marginBottom: 7 }}>
                Exact fold over the immutable evidence ledger. Corrections are red and may move the curve down.
              </div>
              <div style={{ border: `1px solid ${COLOR.border}`, background: COLOR.bgInput, padding: "8px 10px 3px" }}>
                <DemonstratedCurve timeline={timeline} />
              </div>
            </section>

            {timeline.ready && <ReadyDerivationLine ready={timeline.ready} />}

            {timeline.points.length > 0 && (
              <section style={{ marginTop: 16 }}>
                <div style={receiptSectionLabelStyle}>observation ledger</div>
                <div style={{ color: COLOR.textDim, fontSize: 10, marginBottom: 7 }}>
                  Select an observation to inspect its credit derivation.
                </div>
                <ScrubberLegend />
                <EvidenceScrubber
                  points={timeline.points}
                  selected={selected}
                  onSelect={(i) => setSelected((prev) => (prev === i ? null : i))}
                />
                {selected != null && timeline.points[selected] && (
                  <ObservationDetail point={timeline.points[selected]} ordinal={selected + 1} onInspect={onInspect} />
                )}
              </section>
            )}

            {latestCaps.length > 0 && (
              <section style={{ marginTop: 16 }}>
                <div style={receiptSectionLabelStyle}>represented capabilities</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {latestCaps.map((cap) => (
                    <Pill key={cap} color="cyan">{cap}</Pill>
                  ))}
                </div>
              </section>
            )}

            {timeline.countedToward.length > 0 && (
              <section style={{ marginTop: 16 }}>
                <div style={receiptSectionLabelStyle}>also counted toward</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "5px 12px", alignItems: "center" }}>
                  {timeline.countedToward.map((lo) => (
                    <ReceiptEntityLink
                      key={lo.learningObjectId}
                      title={`learnloop show ${lo.learningObjectId}`}
                      onClick={() => onInspect(lo.learningObjectId)}
                    >
                      {lo.learningObjectTitle}
                    </ReceiptEntityLink>
                  ))}
                </div>
              </section>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export function FacetEvidenceDrawer({
  facetId,
  onClose,
  onInspect
}: {
  facetId: string;
  onClose: () => void;
  onInspect: (entityId: string) => void;
}) {
  return (
    <CommandOverlayFrame
      command="show"
      context={facetId}
      badge={<Pill color="cyan">facet evidence</Pill>}
      footerKeys={<span><span style={{ color: COLOR.text }}>esc</span> close</span>}
      footerRight={<span>evidence receipt · <Dim>learnloop show {facetId}</Dim></span>}
      onClose={onClose}
      ariaLabel={`Evidence for ${facetTitle(facetId)}`}
      width={learnloopShowOverlayWidth}
      zIndex={220}
    >
      <div className="ll-scroll" style={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
        <FacetEvidenceReceipt facetId={facetId} onInspect={onInspect} />
      </div>
    </CommandOverlayFrame>
  );
}

const receiptHeroStyle = {
  padding: "14px 18px",
  borderBottom: `1px solid ${COLOR.border}`,
  background: `linear-gradient(110deg, ${COLOR.bgElev} 0%, ${COLOR.bg} 70%)`
};

const receiptStatusLineStyle = {
  display: "flex",
  flexWrap: "wrap" as const,
  alignItems: "baseline",
  rowGap: 4,
  color: COLOR.textFaint,
  fontSize: 10
};

const receiptContextStyle = {
  color: COLOR.textFaint,
  fontSize: 9,
  letterSpacing: "0.14em",
  textTransform: "uppercase" as const
};

const receiptSeparatorStyle = {
  color: COLOR.textFaint,
  margin: "0 7px"
};

const receiptTitleStyle = {
  margin: 0,
  color: COLOR.text,
  fontSize: 17,
  lineHeight: 1.3,
  fontWeight: 600,
  letterSpacing: "-0.02em"
};

const receiptBodyStyle = {
  padding: "14px 18px 20px"
};

const receiptSectionLabelStyle = {
  color: COLOR.amber,
  fontSize: 9,
  letterSpacing: "0.12em",
  textTransform: "uppercase" as const,
  marginBottom: 5
};

const observationEyebrowStyle = {
  color: COLOR.amber,
  fontSize: 9,
  letterSpacing: "0.12em",
  textTransform: "uppercase" as const
};

const receiptEntityLinkStyle = {
  padding: 0,
  border: 0,
  background: "transparent",
  color: COLOR.amberLink,
  fontFamily: FONT_MONO,
  fontSize: 10,
  cursor: "pointer"
};

const receiptEntityLinkLabelStyle = {
  textDecorationLine: "underline",
  textDecorationThickness: "1px",
  textUnderlineOffset: 3
};
