// ING M7 — Update study map surfaces (§10-§11, §15):
//   * Maintenance feed (§11): deterministic notices grouped by severity, each with
//     one concrete action + dismiss/snooze (no source/curriculum state change).
//   * Update study map (§10): run a bounded affected-neighborhood append on a
//     source set and render the study-map diff + post-append merge-review pass.
//   * Conflict review (§10.2/§10.5): open source_conflicts with side-by-side
//     bounded evidence and the four resolution kinds (never applies a side).
//   * Exam readiness (§15): a deterministic Ready-vs-Demonstrated table per task
//     family — never one blended number.

import { useCallback, useEffect, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import type {
  AppendResultDto,
  ExamReadinessReportDto,
  MaintenanceNoticeDto,
  MaintenanceSeverity,
  MeasurementHealthDto,
  SourceConflictDto,
  SourceSetSummaryDto,
  ConflictResolutionKind,
  AmbiguousEdgeDirectionDetail,
  RestructureRequestDetail,
  EdgeDirectionResolution
} from "../api/dto";
import { OpenInSource } from "../components/OpenInSource";
import { COLOR, Dim, Divider, Faint, FONT_MONO, Pill, SectionHeader, TermSelect, type PillColor } from "../components/term";

// Canonical locators are `span:<extraction>/<span>`; the optional extraction
// group preserves the malformed pre-v2 `span:<span>` compatibility shape.
// (heading_path_v1 / time_range_v1) carry no span the viewer can open.
function spanIdFromLocator(locator: string | null): string | null {
  return /^span:(?:[^/]+\/)?(.+)$/.exec(locator ?? "")?.[1] ?? null;
}

const SEVERITY_PILL: Record<MaintenanceSeverity, PillColor> = {
  action_needed: "red",
  warning: "amber",
  info: "slate"
};

const RESOLUTION_KINDS: { kind: ConflictResolutionKind; label: string }[] = [
  { kind: "prefer_for_context", label: "Prefer one (scoped)" },
  { kind: "keep_both_scoped", label: "Keep both scoped" },
  { kind: "notation_mapping", label: "Notation mapping" },
  { kind: "dismiss", label: "Dismiss" }
];

const panel: CSSProperties = {
  border: `1px solid ${COLOR.border}`,
  borderRadius: 3,
  padding: "12px 14px",
  marginBottom: 14,
  background: COLOR.bgElev
};

const btn: CSSProperties = {
  fontFamily: FONT_MONO,
  fontSize: 12,
  color: COLOR.text,
  background: COLOR.bgInput,
  border: `1px solid ${COLOR.border}`,
  borderRadius: 2,
  padding: "3px 10px",
  cursor: "pointer"
};

export function MaintenanceScreen({
  subjects,
  onError,
  onInspect
}: {
  subjects: { id: string; title: string }[];
  onError: (message: string) => void;
  onInspect?: (id: string) => void;
}) {
  const [subjectId, setSubjectId] = useState<string | null>(subjects[0]?.id ?? null);
  const [notices, setNotices] = useState<MaintenanceNoticeDto[]>([]);
  const [conflicts, setConflicts] = useState<SourceConflictDto[]>([]);
  const [readiness, setReadiness] = useState<ExamReadinessReportDto | null>(null);
  const [sourceSets, setSourceSets] = useState<SourceSetSummaryDto[]>([]);
  const [measurementHealth, setMeasurementHealth] = useState<MeasurementHealthDto | null>(null);
  const [busy, setBusy] = useState(false);
  const [append, setAppend] = useState<AppendResultDto | null>(null);
  const [openSpan, setOpenSpan] = useState<{
    extractionId: string;
    spanId: string;
    entityType: string;
    entityId: string;
  } | null>(null);

  const reportError = useCallback(
    (err: unknown) => onError(err instanceof Error ? err.message : String(err)),
    [onError]
  );

  const load = useCallback(() => {
    api.getMaintenanceFeed(subjectId).then((r) => setNotices(r.notices)).catch(reportError);
    api.listSourceConflicts("open").then((r) => setConflicts(r.conflicts)).catch(reportError);
    api.getExamReadiness(subjectId).then((r) => setReadiness(r.report)).catch(reportError);
    api.listSourceSets().then((r) => setSourceSets(r.sourceSets)).catch(reportError);
    api.getMeasurementHealth().then(setMeasurementHealth).catch(reportError);
  }, [subjectId, reportError]);

  useEffect(() => {
    load();
  }, [load]);

  const noticeAction = async (notice: MaintenanceNoticeDto, action: "dismiss" | "snooze") => {
    try {
      await api.maintenanceNoticeAction(notice.id, action);
      load();
    } catch (err) {
      reportError(err);
    }
  };

  const resolveDirection = async (
    edgeId: string,
    resolution: EdgeDirectionResolution,
    rationale: string
  ) => {
    try {
      await api.resolveEdgeDirection({ edgeId, resolution, rationale });
      load();
    } catch (err) {
      reportError(err);
    }
  };

  const runAppend = async (sourceSetId: string) => {
    setBusy(true);
    setAppend(null);
    try {
      const res = await api.appendSource({ sourceSetId });
      setAppend(res.append);
      load();
    } catch (err) {
      reportError(err);
    } finally {
      setBusy(false);
    }
  };

  const resolve = async (conflict: SourceConflictDto, kind: ConflictResolutionKind) => {
    try {
      let resolution: Record<string, unknown> = {};
      if (kind === "notation_mapping") {
        const canonical = window.prompt("Canonical notation?") ?? "";
        const alternate = window.prompt("Alternate notation?") ?? "";
        if (!canonical || !alternate) return;
        resolution = { canonicalNotation: canonical, alternateNotation: alternate };
      }
      await api.resolveSourceConflict({ conflictId: conflict.id, resolutionKind: kind, resolution });
      load();
    } catch (err) {
      reportError(err);
    }
  };

  const bySeverity = (sev: MaintenanceSeverity) => notices.filter((n) => n.severity === sev);

  const scheduleColdProbes = async () => {
    setBusy(true);
    try {
      await api.scheduleCertificationColdProbes();
      load();
    } catch (err) {
      reportError(err);
    } finally {
      setBusy(false);
    }
  };

  const transitionProbe = async (candidateId: string, toStatus: string) => {
    const needsReviewer = toStatus === "reviewed" || toStatus === "rejected";
    const reviewer = needsReviewer ? window.prompt("Reviewer name?")?.trim() : null;
    if (needsReviewer && !reviewer) return;
    const reason = needsReviewer ? window.prompt("Review reason (optional)?")?.trim() || null : null;
    try {
      await api.transitionCausalProbeCandidate({ candidateId, toStatus, reviewer, reason });
      load();
    } catch (err) {
      reportError(err);
    }
  };

  const applyIntegrationBackfill = async () => {
    const confirmed = window.confirm(
      "Apply the reviewed D3 coordination backfill? This rewrites authored learning-object YAML, rebuilds affected state, and records one learner-visible recalibration boundary."
    );
    if (!confirmed) return;
    setBusy(true);
    try {
      await api.applyIntegrationBackfill();
      load();
    } catch (err) {
      reportError(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ fontFamily: FONT_MONO, color: COLOR.text, padding: "8px 4px", overflowY: "auto" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
        <SectionHeader>Maintain</SectionHeader>
        {subjects.length > 0 ? (
          <TermSelect
            value={subjectId ?? ""}
            options={[{ value: "", label: "all subjects" }, ...subjects.map((s) => ({ value: s.id, label: s.title }))]}
            onChange={(v) => setSubjectId(v || null)}
          />
        ) : null}
        <button style={btn} onClick={load}>↻ refresh</button>
      </div>

      <MeasurementHealthPanel
        health={measurementHealth}
        busy={busy}
        onScheduleColdProbes={scheduleColdProbes}
        onTransitionProbe={transitionProbe}
        onApplyIntegrationBackfill={applyIntegrationBackfill}
      />

      {/* Maintenance feed (§11) */}
      <div style={panel}>
        <Faint>Maintenance feed · {notices.length} live notice(s), each with a declared aging policy</Faint>
        {notices.length === 0 ? <div style={{ marginTop: 8, color: COLOR.textDim }}>Feed is clear.</div> : null}
        {(["action_needed", "warning", "info"] as MaintenanceSeverity[]).map((sev) =>
          bySeverity(sev).map((notice) => (
            <div key={notice.id} style={{ marginTop: 10 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Pill color={SEVERITY_PILL[notice.severity]}>{notice.severity}</Pill>
                <span style={{ color: COLOR.textDim, fontSize: 11 }}>{notice.noticeType}</span>
                <span style={{ color: COLOR.textFaint, fontSize: 11 }}>· {notice.agingPolicy}</span>
              </div>
              {notice.noticeType === "ambiguous_edge_direction" ? (
                <AmbiguousEdgeCard notice={notice} onResolve={resolveDirection} onInspect={onInspect} />
              ) : notice.noticeType === "restructure_request" ? (
                <RestructureRequestCard notice={notice} onInspect={onInspect} />
              ) : (
                <div style={{ marginTop: 3 }}>{notice.title}</div>
              )}
              <div style={{ display: "flex", gap: 6, marginTop: 4 }}>
                {notice.noticeType === "ambiguous_edge_direction" ||
                notice.noticeType === "restructure_request" ? null : (
                  <button style={btn} title={notice.action.action}>
                    {notice.action.label ?? notice.action.action ?? "action"}
                  </button>
                )}
                <button style={btn} onClick={() => noticeAction(notice, "snooze")}>
                  snooze{notice.snoozeCount > 0 ? ` (${notice.snoozeCount})` : ""}
                </button>
                <button style={btn} onClick={() => noticeAction(notice, "dismiss")}>dismiss</button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Update study map (§10) */}
      <div style={panel}>
        <Faint>Update study map · bounded affected-neighborhood append (never resends the full map)</Faint>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 }}>
          {sourceSets.length === 0 ? <span style={{ color: COLOR.textDim }}>No source sets.</span> : null}
          {sourceSets.map((s) => (
            <button key={s.id} style={btn} disabled={busy} onClick={() => runAppend(s.id)}>
              {busy ? "…" : "update"} {s.title}
            </button>
          ))}
        </div>
        {append ? <StudyMapDiffView append={append} onInspect={onInspect} /> : null}
      </div>

      {/* Conflict review (§10.2/§10.5) */}
      <div style={panel}>
        <Faint>Open conflicts · resolving preserves BOTH evidence locators; it never applies either side</Faint>
        {conflicts.length === 0 ? <div style={{ marginTop: 8, color: COLOR.textDim }}>No open conflicts.</div> : null}
        {conflicts.map((c) => (
          <div key={c.id} style={{ marginTop: 10, borderTop: `1px solid ${COLOR.border}`, paddingTop: 8 }}>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <Pill color="red">conflict</Pill>
              <span style={{ color: COLOR.textDim }}>{c.entityType}</span>
              {onInspect ? (
                <span className="entity-link" role="button" onClick={() => onInspect(c.entityId)}>{c.entityId}</span>
              ) : (
                <span>{c.entityId}</span>
              )}
            </div>
            <div style={{ marginTop: 4 }}>{c.statement}</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginTop: 6 }}>
              <ConflictSide
                label="Left"
                source={c.leftSourceId}
                revision={c.leftRevisionId}
                locator={c.leftLocator}
                extractionId={c.leftExtractionId}
                onOpen={(extractionId, spanId) =>
                  setOpenSpan({ extractionId, spanId, entityType: c.entityType, entityId: c.entityId })
                }
              />
              <ConflictSide
                label="Right"
                source={c.rightSourceId}
                revision={c.rightRevisionId}
                locator={c.rightLocator}
                extractionId={c.rightExtractionId}
                onOpen={(extractionId, spanId) =>
                  setOpenSpan({ extractionId, spanId, entityType: c.entityType, entityId: c.entityId })
                }
              />
            </div>
            <div style={{ display: "flex", gap: 6, marginTop: 6, flexWrap: "wrap" }}>
              {RESOLUTION_KINDS.map((r) => (
                <button key={r.kind} style={btn} onClick={() => resolve(c, r.kind)}>{r.label}</button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Exam readiness (§15) — Ready vs Demonstrated, never blended */}
      <div style={panel}>
        <Faint>
          Exam readiness · Ready = projected performance, Demonstrated = certified evidence
          {readiness?.hasCalibration ? " · calibration overlay present" : ""}
        </Faint>
        {readiness && readiness.rows.length > 0 ? (
          <div style={{ overflowX: "auto", marginTop: 8 }}>
            <table style={{ borderCollapse: "collapse", width: "100%", fontSize: 12 }}>
              <thead>
                <tr style={{ color: COLOR.textDim, textAlign: "left" }}>
                  <th style={th}>task family</th>
                  <th style={th}>weight</th>
                  <th style={th}>Ready (predicted)</th>
                  <th style={th}>Demonstrated</th>
                  <th style={th}>facets · capabilities</th>
                </tr>
              </thead>
              <tbody>
                {readiness.rows.map((row) => (
                  <tr key={row.taskFamily} style={{ borderTop: `1px solid ${COLOR.border}` }}>
                    <td style={td}>{row.taskFamily}</td>
                    <td style={td}>{(row.normalizedWeight * 100).toFixed(0)}%</td>
                    <td style={{ ...td, color: COLOR.cyan }}>
                      {row.ready == null ? "n/a" : `${(row.ready * 100).toFixed(0)}%`}
                      {row.predicted ? (
                        <span style={{ color: COLOR.textFaint }}> ±{(row.predicted.std * 100).toFixed(0)}%</span>
                      ) : null}
                    </td>
                    <td style={{ ...td, color: COLOR.green }}>{(row.demonstratedFraction * 100).toFixed(0)}%</td>
                    <td style={td}>
                      {row.facetCapabilities.map((fc, i) => (
                        <span key={i}>
                          <Pill color={fc.demonstrated ? "green" : "slate"} style={{ marginRight: 4 }}>
                            {fc.facet.replace(/^facet_/, "")}·{fc.capability}
                          </Pill>
                        </span>
                      ))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {readiness.predictedScore ? (
              <div style={{ marginTop: 10, fontSize: 12, display: "flex", gap: 16, flexWrap: "wrap" }}>
                <span style={{ color: COLOR.cyan }}>
                  Predicted exam score {(readiness.predictedScore.mean * 100).toFixed(0)}% ± {(readiness.predictedScore.std * 100).toFixed(0)}%
                  <Faint style={{ marginLeft: 6 }}>predicted performance</Faint>
                </span>
                <span style={{ color: COLOR.green }}>
                  Demonstrated {((readiness.demonstratedScore ?? 0) * 100).toFixed(0)}%
                  <Faint style={{ marginLeft: 6 }}>evidence banked</Faint>
                </span>
              </div>
            ) : null}
          </div>
        ) : (
          <div style={{ marginTop: 8, color: COLOR.textDim }}>No blueprints to report yet.</div>
        )}
      </div>

      {openSpan ? (
        <OpenInSource
          extractionId={openSpan.extractionId}
          spanId={openSpan.spanId}
          context="conflict_review"
          entityType={openSpan.entityType}
          entityId={openSpan.entityId}
          onClose={() => setOpenSpan(null)}
        />
      ) : null}
    </div>
  );
}

function metricValue(metric: MeasurementHealthDto["scoreboard"]["metrics"][number]): string {
  if (!metric.available || metric.value == null) return metric.availability.replace(/_/g, " ");
  if (metric.unit === "rate") return `${(metric.value * 100).toFixed(1)}%`;
  return `${Number(metric.value.toFixed(2))} ${metric.unit}`;
}

function MeasurementHealthPanel({
  health,
  busy,
  onScheduleColdProbes,
  onTransitionProbe,
  onApplyIntegrationBackfill
}: {
  health: MeasurementHealthDto | null;
  busy: boolean;
  onScheduleColdProbes: () => void;
  onTransitionProbe: (candidateId: string, toStatus: string) => void;
  onApplyIntegrationBackfill: () => void;
}) {
  if (!health) {
    return (
      <div style={panel}>
        <Faint>Measurement & causal health · loading authoritative producers…</Faint>
      </div>
    );
  }

  const reach = health.reachability.summary;
  const inference = health.inferencePrecheck.summary;
  const cold = health.coldProbes.coverage;
  const backfill = health.integrationBackfill.summary;
  const backfillChanges =
    (backfill.dispositions.DROP ?? 0) + (backfill.dispositions.LOWER ?? 0);
  const queue = health.reachability.cells.filter((cell) => cell.verdict !== "REACHABLE").slice(0, 8);
  const nextStatus = (status: string): string | null =>
    status === "candidate" ? "registered" :
    status === "registered" ? "reviewed" :
    status === "reviewed" ? "active" : null;

  return (
    <div style={panel}>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <Faint>Measurement & causal health · Stages 0–6 + inference precheck</Faint>
        <Pill color={reach.cellCount === 0 ? "slate" : reach.unreachableCount === 0 ? "green" : "amber"}>
          {reach.cellCount === 0
            ? "no contract cells declared"
            : `${reach.reachableCount}/${reach.cellCount} contract cells reachable`}
        </Pill>
        <Pill color={health.missingVocabulary.uncapturedDiagnosticAbstentions === 0 ? "green" : "red"}>
          {health.missingVocabulary.uncapturedDiagnosticAbstentions} uncaptured abstentions
        </Pill>
        <Pill color={cold.certificatesActive === 0 ? "slate" : cold.certificatesUnscheduled === 0 ? "green" : "amber"}>
          {cold.certificatesActive === 0
            ? "no active certificates to probe"
            : `${cold.certificatesUnscheduled} cold probes unscheduled`}
        </Pill>
      </div>

      <Divider />
      <Faint>Efficiency scoreboard · unavailable arms remain visible and are never rendered as zero</Faint>
      <div style={{ overflowX: "auto", marginTop: 6 }}>
        <table style={{ borderCollapse: "collapse", width: "100%", fontSize: 11 }}>
          <thead>
            <tr style={{ color: COLOR.textDim, textAlign: "left" }}>
              <th style={th}>metric</th>
              <th style={th}>value / availability</th>
              <th style={th}>denominator</th>
            </tr>
          </thead>
          <tbody>
            {health.scoreboard.metrics.map((metric) => (
              <tr key={metric.name} style={{ borderTop: `1px solid ${COLOR.border}` }}>
                <td style={td}>{metric.name.replace(/_/g, " ")}</td>
                <td style={{ ...td, color: metric.available ? COLOR.green : COLOR.amber }}>
                  {metricValue(metric)}
                </td>
                <td style={{ ...td, color: COLOR.textFaint }}>
                  {metric.denominator ?? "—"} · {metric.denominatorLabel}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Divider />
      <div style={{ display: "grid", gridTemplateColumns: "minmax(280px, 1fr) minmax(280px, 1fr)", gap: 14 }}>
        <TraceEvidenceBlock traceEvidence={health.traceEvidence} />
        <ClarificationRateBlock clarificationRate={health.clarificationRate} />
      </div>

      <Divider />
      <InstrumentAuditBlock audit={health.instrumentAudit} />

      <Divider />
      <div style={{ display: "grid", gridTemplateColumns: "minmax(280px, 1fr) minmax(280px, 1fr)", gap: 14 }}>
        <div>
          <Faint>
            Contract reachability · {reach.facetsInstrumented}/{reach.facetsDeclared} facets instrumented
          </Faint>
          {reach.cellCount === 0 ? (
            <div style={{ marginTop: 5, color: COLOR.amber }}>
              No contract cells are declared; reachability is unknown, not 100%.
            </div>
          ) : queue.length === 0 ? (
            <div style={{ marginTop: 5, color: COLOR.green }}>All declared cells have an instrument.</div>
          ) : (
            queue.map((cell) => (
              <div key={`${cell.learningObjectId}:${cell.facetId}:${cell.requiredCapability}`} style={{ marginTop: 5, fontSize: 11 }}>
                <Pill color="amber">{cell.verdict}</Pill>{" "}
                <span>{cell.requiredCapability}</span>{" "}
                <Faint>{cell.remedy} · {cell.learningObjectId}</Faint>
              </div>
            ))
          )}
          {health.reachability.cells.filter((cell) => cell.verdict !== "REACHABLE").length > queue.length ? (
            <Faint style={{ display: "block", marginTop: 5 }}>
              first {queue.length} of {reach.unreachableCount} commissioning rows
            </Faint>
          ) : null}
          <div style={{ marginTop: 12 }}>
            <Faint>Wave 4 inference precheck · static cells converted, no credit applied</Faint>
            <div style={{ display: "flex", gap: 5, flexWrap: "wrap", marginTop: 5 }}>
              <Pill color={inference.capabilityDominance.movesCount ? "green" : "slate"}>
                B1 dominance {inference.capabilityDominance.cellsConverted}
              </Pill>
              <Pill color={inference.prerequisiteEntailment.movesCount ? "green" : "slate"}>
                B3 hard entailment {inference.prerequisiteEntailment.cellsConverted}
              </Pill>
              <Pill color={inference.prerequisiteEntailment.conditionalCells > 0 ? "amber" : "slate"}>
                path-conditional {inference.prerequisiteEntailment.conditionalCells}
              </Pill>
              <Pill color={inference.combined.movesCount ? "green" : "slate"}>
                combined {inference.combined.cellsConverted}
              </Pill>
            </div>
            <Faint style={{ display: "block", marginTop: 5 }}>
              prerequisite declarations: {inference.prerequisiteEntailment.prerequisiteDeclarationCount}
              {" · "}untyped {inference.prerequisiteEntailment.modalityCounts.untyped ?? 0}
              {" · "}instructional only {inference.prerequisiteEntailment.modalityCounts.instructional_order ?? 0}
            </Faint>
          </div>
        </div>

        <div>
          <Faint>Delayed held-out cold probes · certification §5.7</Faint>
          <div style={{ marginTop: 5, fontSize: 12 }}>
            active {cold.certificatesActive} · unmeasurable {cold.certificatesUnmeasurable} · unscheduled {cold.certificatesUnscheduled}
          </div>
          <button style={{ ...btn, marginTop: 6 }} disabled={busy} onClick={onScheduleColdProbes}>
            {busy ? "scheduling…" : "schedule eligible probes"}
          </button>
          <div style={{ marginTop: 10 }}>
            <Faint>Missing vocabulary</Faint>
            <div style={{ fontSize: 12, marginTop: 3 }}>
              {health.missingVocabulary.notes} note(s) · {(health.missingVocabulary.abstentionRate * 100).toFixed(1)}% diagnostic abstention
            </div>
          </div>
          <div style={{ marginTop: 10 }}>
            <Faint>Persona realism validity</Faint>
            <div style={{ fontSize: 12, marginTop: 3, color: COLOR.amber }}>
              not validated · pre-B2 gate verdicts do not count
            </div>
            <Faint style={{ display: "block", marginTop: 2 }}>
              precision producer: {health.personaGate.availability.replace(/_/g, " ")} · {health.personaGate.note}
            </Faint>
          </div>
          <div style={{ marginTop: 10 }}>
            <Faint>D2 facet mint gate</Faint>
            <div style={{ fontSize: 12, marginTop: 3, color: COLOR.amber }}>
              structural proxy · original shared-harness gate incomplete
            </div>
            <Faint style={{ display: "block", marginTop: 2 }}>
              MINT {health.facetMintGate.summary.dispositions.MINT ?? 0} · ALIAS {health.facetMintGate.summary.dispositions.ALIAS ?? 0} · ABSTAIN {health.facetMintGate.summary.dispositions.ABSTAIN ?? 0}
            </Faint>
          </div>
        </div>
      </div>

      <Divider />
      <div style={{ display: "grid", gridTemplateColumns: "minmax(280px, 1fr) minmax(280px, 1fr)", gap: 14 }}>
        <div>
          <Faint>Causal-lane fill / abstention health</Faint>
          {health.causalHealth.channels.map((channel) => (
            <div key={channel.channel} style={{ display: "flex", justifyContent: "space-between", gap: 8, marginTop: 4, fontSize: 11 }}>
              <span>{channel.channel.replace(/_/g, " ")}</span>
              <span style={{ color: channel.missing > 0 ? COLOR.red : COLOR.textDim }}>
                fill {(channel.fillRate * 100).toFixed(0)}% · abstain {channel.abstained} · missing {channel.missing}
              </span>
            </div>
          ))}
        </div>
        <div>
          <Faint>D3 integration backfill · coordination scope</Faint>
          <div style={{ fontSize: 12, marginTop: 4 }}>
            {backfill.integrationComponentCount} component(s) · {backfillChanges} content edit(s) · {backfill.owedCapstones.length} owed capstone(s)
          </div>
          <Faint style={{ display: "block", marginTop: 4 }}>
            KEEP {backfill.dispositions.KEEP ?? 0} · LOWER {backfill.dispositions.LOWER ?? 0} · DROP {backfill.dispositions.DROP ?? 0}
          </Faint>
          {health.integrationBackfill.previewEdits.map((edit) => (
            <details key={edit.learningObjectId} style={{ marginTop: 5, fontSize: 11 }}>
              <summary style={{ cursor: "pointer", color: COLOR.cyan }}>
                review {edit.learningObjectId}
              </summary>
              <pre style={{ overflowX: "auto", color: COLOR.textDim, whiteSpace: "pre-wrap" }}>
                {edit.diff}
              </pre>
            </details>
          ))}
          {backfillChanges > 0 ? (
            <button style={{ ...btn, marginTop: 6 }} disabled={busy} onClick={onApplyIntegrationBackfill}>
              {busy ? "applying…" : `review & apply ${backfillChanges} edit(s)`}
            </button>
          ) : null}
          {!backfill.coordinationObserved ? (
            <div style={{ color: COLOR.amber, fontSize: 11, marginTop: 5 }}>
              No active instrument observes coordination; coordination claims remain gated.
            </div>
          ) : null}
        </div>
      </div>

      <Divider />
      <Faint>
        Causal probe review · {health.causalProbeReview.openFactors.length} open factor(s) ·{" "}
        {health.causalProbeReview.pendingMachineChecks.length} pending machine check(s)
      </Faint>
      {health.causalProbeReview.candidates.length === 0 ? (
        <div style={{ marginTop: 5, color: COLOR.textDim }}>No commissioned probe candidates awaiting review.</div>
      ) : (
        health.causalProbeReview.candidates.map((candidate) => {
          const next = nextStatus(candidate.status);
          return (
            <div key={candidate.id} style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap", marginTop: 6, fontSize: 11 }}>
              <Pill color={candidate.distinguishable ? "green" : "red"}>
                {candidate.distinguishable ? "blind-separable" : "not separable"}
              </Pill>
              {!candidate.blindInputContractValid ? (
                <Pill color="red">obsolete observation-exposed input</Pill>
              ) : null}
              <span>{candidate.practiceItemId}</span>
              <Faint>{candidate.status} · factor {candidate.factorId}</Faint>
              {next && candidate.blindInputContractValid ? (
                <button style={btn} onClick={() => onTransitionProbe(candidate.id, next)}>
                  advance to {next}
                </button>
              ) : null}
              {candidate.status !== "rejected" && candidate.status !== "active" ? (
                <button style={btn} onClick={() => onTransitionProbe(candidate.id, "rejected")}>reject</button>
              ) : null}
            </div>
          );
        })
      )}
    </div>
  );
}

// Meas §3.A6 revert criterion. Concentration is printed beside the counts it is
// computed from and given NO verdict colour on purpose: the docstring's own
// standard is that a reader can check it by hand, and inventing a threshold the
// spec does not name would be the confident wrongness this panel exists to
// catch. The abstaining arm stays visible and is never rendered as 0%.
function TraceEvidenceBlock({
  traceEvidence
}: {
  traceEvidence: MeasurementHealthDto["traceEvidence"];
}) {
  const t = traceEvidence;
  return (
    <div>
      <Faint>A6 opportunistic trace evidence · §3.A6 revert criterion</Faint>
      <div style={{ fontSize: 12, marginTop: 4 }}>
        {t.opportunisticObservations} opportunistic · {t.declaredObservations} declared ·{" "}
        across {t.attemptsWithObservations} attempt(s)
      </div>
      <div style={{ fontSize: 12, marginTop: 3 }}>
        {t.opportunisticConcentration == null ? (
          <span style={{ color: COLOR.amber }}>
            concentration unmeasured · too few observations to report one
          </span>
        ) : (
          <>
            top facet holds{" "}
            <span style={{ color: COLOR.text }}>
              {(t.opportunisticConcentration * 100).toFixed(0)}%
            </span>{" "}
            of opportunistic credit across {t.distinctOpportunisticFacets} facet(s)
          </>
        )}
      </div>
      <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginTop: 5 }}>
        {t.topOpportunisticFacets.slice(0, 6).map((row) => (
          <Pill key={row.facetId} color="slate">
            {row.facetId.replace(/^facet_/, "")} ×{row.count}
          </Pill>
        ))}
      </div>
      <Faint style={{ display: "block", marginTop: 6 }}>
        A1 guard 1 · {t.unexercisedSupportingCellCount} cell(s) accrued mass for a facet the trace
        never showed exercised
      </Faint>
      {t.unexercisedSupportingCells.slice(0, 4).map((cell) => (
        <div key={`${cell.facetId}:${cell.capability}`} style={{ fontSize: 11, marginTop: 3 }}>
          <Pill color="amber">{cell.unexercisedSupportingMass.toFixed(2)}</Pill>{" "}
          <span>{cell.facetId.replace(/^facet_/, "")}</span> <Faint>· {cell.capability}</Faint>
        </div>
      ))}
    </div>
  );
}

// Plan item 6.4 — the four Meas §3 instrument classes' REVERT criteria, which
// shipped as `learnloop instrument-audit` and nowhere else. A revert criterion
// only a terminal can read is a rung kept on judgement, which §3 forbids; this
// is the same four producers, in the same order, rendered.
//
// The screen's standing rule holds here exactly as it does above: an unavailable
// arm STAYS VISIBLE and is never rendered as zero. A metric over too little data
// prints its availability word and its counts — "no_data 1/3 paired facets" says
// something true, "0.0%" says something false and alarming. Nothing here is
// coloured against a threshold the spec does not name; the verdict string the
// producer computed is the verdict shown.
function InstrumentAuditBlock({ audit }: { audit: MeasurementHealthDto["instrumentAudit"] }) {
  const hunts = audit.errorHuntOutcomes;
  const coverage = audit.discriminationProfileCoverage;
  const ladders = audit.ladderedStems.filter((stem) => stem.isLadder);
  const commissioning = audit.contrastPairCommissioning.summary;
  return (
    <div>
      <Faint>
        Instrument revert criteria · §3.A2–§3.A5 · unavailable arms remain visible and are never
        rendered as zero
      </Faint>
      <div style={{ overflowX: "auto", marginTop: 6 }}>
        <table style={{ borderCollapse: "collapse", width: "100%", fontSize: 11 }}>
          <thead>
            <tr style={{ color: COLOR.textDim, textAlign: "left" }}>
              <th style={th}>instrument</th>
              <th style={th}>value / availability</th>
              <th style={th}>verdict</th>
              <th style={th}>denominator</th>
            </tr>
          </thead>
          <tbody>
            {audit.metrics.map((metric) => (
              <tr key={metric.name} style={{ borderTop: `1px solid ${COLOR.border}` }}>
                <td style={td}>{metric.name.replace(/_/g, " ")}</td>
                <td style={{ ...td, color: metric.available ? COLOR.green : COLOR.amber }}>
                  {metricValue(metric)}
                </td>
                <td style={{ ...td, color: COLOR.textDim }}>
                  {String(metric.detail?.verdict ?? "—").replace(/_/g, " ")}
                </td>
                <td style={{ ...td, color: COLOR.textFaint }}>
                  {metric.denominator ?? "—"} · {metric.denominatorLabel}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "minmax(280px, 1fr) minmax(280px, 1fr)", gap: 14, marginTop: 10 }}>
        <div>
          <Faint>A3 error hunts · outcomes and the clean rotation</Faint>
          <div style={{ fontSize: 12, marginTop: 4 }}>
            {hunts.attempts} attempt(s) · {hunts.plantedRepaired} plant(s) repaired ·{" "}
            {hunts.plantedFoundNotRepaired} flagged not repaired · {hunts.plantedMissed} missed
          </div>
          <div style={{ fontSize: 12, marginTop: 3 }}>
            {/* The rotation share is the one number an author can act on: the
                "there is always an error" strategy returns the moment clean
                solutions stop being served. Null with no attempts — a 0% here
                would read as that failure rather than as no data. */}
            {hunts.cleanRotationShare == null ? (
              <span style={{ color: COLOR.amber }}>
                clean rotation unmeasured · no error-hunt attempts recorded
              </span>
            ) : (
              <>
                clean rotation{" "}
                <span style={{ color: COLOR.text }}>
                  {(hunts.cleanRotationShare * 100).toFixed(0)}%
                </span>{" "}
                <Faint>
                  · {hunts.cleanSolutionAttempts} of {hunts.attempts} solutions served correct
                </Faint>
              </>
            )}
          </div>
          <Faint style={{ display: "block", marginTop: 4 }}>
            {hunts.falsePositiveReports} false positive(s) · {hunts.misconceptionCandidatesWritten}{" "}
            misconception candidate(s) written · {hunts.facetFailuresSuppressed} facet failure(s)
            suppressed
          </Faint>
        </div>
        <div>
          <Faint>A2 laddered stems · a one-column "stem" is the failure mode</Faint>
          <div style={{ fontSize: 12, marginTop: 4 }}>
            {audit.ladderedStems.length === 0 ? (
              <span style={{ color: COLOR.textDim }}>no stems authored</span>
            ) : (
              <>
                {ladders.length} ladder(s) of {audit.ladderedStems.length} stem(s) ·{" "}
                <Faint>
                  the rest are near-clones on one stimulus, which kinship collapses to ~one
                  observation
                </Faint>
              </>
            )}
          </div>
          {audit.ladderedStems.slice(0, 4).map((stem) => (
            <div key={stem.stemId} style={{ fontSize: 11, marginTop: 3 }}>
              <Pill color={stem.isLadder ? "green" : "amber"}>
                {stem.columnsFilled} column{stem.columnsFilled === 1 ? "" : "s"}
              </Pill>{" "}
              <span>{stem.stemId}</span>{" "}
              <Faint>
                · {stem.partIds.length} part(s)
                {stem.unplacedParts.length > 0
                  ? ` · ${stem.unplacedParts.length} declaring no capability`
                  : ""}
              </Faint>
            </div>
          ))}
        </div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "minmax(280px, 1fr) minmax(280px, 1fr)", gap: 14, marginTop: 10 }}>
        <div>
          <Faint>A5 discrimination profiles · the pool the rejection rate is read against</Faint>
          <div style={{ fontSize: 12, marginTop: 4 }}>
            {coverage.profiles} profile(s) on {coverage.itemsWithProfiles}/{coverage.practiceItems}{" "}
            item(s)
          </div>
          <Faint style={{ display: "block", marginTop: 3 }}>
            {coverage.unlinkedAuthoredProfiles} authored without a registry link — legitimate, but
            the arm A4 commissioning exists to replace
          </Faint>
        </div>
        <div>
          <Faint>A4 contrast pairs · commissioning queue</Faint>
          <div style={{ fontSize: 12, marginTop: 4 }}>
            {commissioning.queueLength === 0 ? (
              <span style={{ color: COLOR.textDim }}>
                no identifiability findings to commission from
              </span>
            ) : (
              <>
                {commissioning.commissioned} commissioned · {commissioning.deferred} deferred · over{" "}
                {commissioning.queueLength} finding(s)
              </>
            )}
          </div>
          {/* Deferred requests stay listed with their typed reason. A queue that
              silently omits its uncommissionable rows is how an obligation goes
              unnoticed for months. */}
          {audit.contrastPairCommissioning.requests.slice(0, 4).map((request) => (
            <div key={`${request.targetKey}:${request.queueRank}`} style={{ fontSize: 11, marginTop: 3 }}>
              <Pill color={request.disposition === "COMMISSION" ? "green" : "slate"}>
                {request.disposition.replace(/_/g, " ").toLowerCase()}
              </Pill>{" "}
              <span>{request.facetIds.join(" / ") || request.targetKey}</span>{" "}
              <Faint>· {request.reason ?? request.check}</Faint>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Meas §3.A8 revert criterion. Over threshold is the loud state because of what
// it means: machine-resident uncertainty (grader flakiness, a missing item
// contract) misclassified as learner-resident, which principle 8 requires be
// fixed machine-side rather than paid for in learner effort.
function ClarificationRateBlock({
  clarificationRate
}: {
  clarificationRate: MeasurementHealthDto["clarificationRate"];
}) {
  const c = clarificationRate;
  return (
    <div>
      <Faint>A8 clarification rate · §3.A8 revert criterion</Faint>
      {!c.available ? (
        <>
          <div style={{ fontSize: 12, marginTop: 4, color: COLOR.amber }}>
            unavailable · {(c.unavailableReason ?? "no_data").replace(/_/g, " ")}
          </div>
          <Faint style={{ display: "block", marginTop: 3 }}>
            {c.clarifications} question(s) over {c.gradeableAttempts} model-graded attempt(s) — too
            few to state a rate, so none is stated
          </Faint>
        </>
      ) : (
        <>
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", marginTop: 4 }}>
            <Pill color={c.overThreshold ? "red" : "green"}>
              {((c.rate ?? 0) * 100).toFixed(1)}% of model-graded attempts
            </Pill>
            <Faint>threshold {(c.threshold * 100).toFixed(0)}%</Faint>
          </div>
          <div style={{ fontSize: 12, marginTop: 4 }}>
            {c.clarifications} asked · {c.answered ?? 0} answered · {c.gradeableAttempts} model-graded
            attempt(s)
          </div>
          {c.overThreshold ? (
            <div style={{ color: COLOR.red, fontSize: 11, marginTop: 5, lineHeight: 1.5 }}>
              Over threshold. This is machine-resident uncertainty being charged to the learner — a
              grader or item-contract problem, and it must be fixed machine-side.
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}

function ConflictSide({
  label,
  source,
  revision,
  locator,
  extractionId,
  onOpen
}: {
  label: string;
  source: string | null;
  revision: string | null;
  locator: string | null;
  extractionId: string | null;
  onOpen: (extractionId: string, spanId: string) => void;
}) {
  const spanId = spanIdFromLocator(locator);
  const openable = extractionId != null && spanId != null;
  return (
    <div style={{ border: `1px solid ${COLOR.border}`, borderRadius: 2, padding: "6px 8px", background: COLOR.bgInput }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ color: COLOR.textDim, fontSize: 11 }}>{label}</span>
        {openable ? (
          <button style={{ ...btn, padding: "1px 8px", fontSize: 11 }} onClick={() => onOpen(extractionId, spanId)}>
            open in source ▸
          </button>
        ) : null}
      </div>
      <div style={{ fontSize: 12 }}>{source ?? "—"}</div>
      <Faint>{revision ?? "—"} · {locator ?? "—"}</Faint>
    </div>
  );
}

function StudyMapDiffView({ append, onInspect }: { append: AppendResultDto; onInspect?: (id: string) => void }) {
  const diff = append.studyMapDiff;
  return (
    <div style={{ marginTop: 10, border: `1px solid ${COLOR.border}`, borderRadius: 2, padding: "8px 10px" }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <Pill color="cyan">{append.changeKind}</Pill>
        <span style={{ color: COLOR.textDim, fontSize: 11 }}>
          auto-applied {append.autoAppliedItemIds.length} · review {append.reviewItemIds.length}
        </span>
      </div>
      <Divider />
      <div style={{ display: "flex", gap: 14, flexWrap: "wrap", fontSize: 12 }}>
        <span>links +{diff?.newLinks ?? 0}</span>
        <span>conflicts +{diff?.newConflicts ?? 0}</span>
        <span>notations +{diff?.newNotations ?? 0}</span>
        <span>stale repaired {diff?.staleLinksRepaired ?? 0}</span>
        <span>blueprint shifts {(diff?.blueprintDistributionShift ?? []).length}</span>
      </div>
      {diff?.newFacets && diff.newFacets.length > 0 ? (
        <div style={{ marginTop: 6 }}>
          <Faint>new facets</Faint>{" "}
          {diff.newFacets.map((f) => (
            <Pill key={f} color="green" style={{ marginRight: 4 }}>{f}</Pill>
          ))}
        </div>
      ) : null}
      {append.mergeReviewProposals.length > 0 ? (
        <div style={{ marginTop: 6 }}>
          <Faint>post-append near-duplicate merge review (never auto-merged)</Faint>
          {append.mergeReviewProposals.map((m, i) => (
            <div key={i} style={{ fontSize: 12, marginTop: 2 }}>
              {onInspect ? (
                <span className="entity-link" role="button" onClick={() => onInspect(m.leftFacetId)}>{m.leftFacetId}</span>
              ) : m.leftFacetId}
              {" ⇄ "}
              {onInspect ? (
                <span className="entity-link" role="button" onClick={() => onInspect(m.rightFacetId)}>{m.rightFacetId}</span>
              ) : m.rightFacetId}
              <Faint> jaccard {m.similarity.toFixed(2)}</Faint>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

const th: CSSProperties = { padding: "4px 8px", fontWeight: 400 };
const td: CSSProperties = { padding: "4px 8px", verticalAlign: "top" };

// -- Direction-resolution card (ambiguous_edge_direction notices) -------------

const DIRECTION_ACTIONS: { resolution: EdgeDirectionResolution; label: string }[] = [
  { resolution: "keep", label: "keep" },
  { resolution: "flip", label: "flip" },
  { resolution: "retype_related", label: "merely related" },
  { resolution: "retire", label: "retire" }
];

const REASON_COPY: Record<AmbiguousEdgeDirectionDetail["reason"], string> = {
  cycle: "part of a prerequisite cycle",
  bidirectional: "A→B and B→A both asserted",
  proposed: "pending proposed prerequisite edge"
};

function AmbiguousEdgeCard({
  notice,
  onResolve,
  onInspect
}: {
  notice: MaintenanceNoticeDto;
  onResolve: (edgeId: string, resolution: EdgeDirectionResolution, rationale: string) => void;
  onInspect?: (id: string) => void;
}) {
  const detail = notice.detail as unknown as AmbiguousEdgeDirectionDetail | null;
  const [selected, setSelected] = useState<EdgeDirectionResolution | null>(null);
  const [rationale, setRationale] = useState("");
  const edgeId = detail?.edgeId ?? (notice.action.edgeId as string | null | undefined) ?? null;
  const evidence = detail?.evidence ?? null;

  if (!detail) return <div style={{ marginTop: 3 }}>{notice.title}</div>;

  const src = detail.sourceConcept;
  const tgt = detail.targetConcept;

  return (
    <div style={{ marginTop: 4, border: `1px solid ${COLOR.border}`, borderRadius: 2, padding: "8px 10px", background: COLOR.bgInput }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <ConceptRef id={src.id} title={src.title} onInspect={onInspect} />
        <span style={{ color: COLOR.amber }}>→</span>
        <ConceptRef id={tgt.id} title={tgt.title} onInspect={onInspect} />
        <Pill color="slate">{detail.relationType}</Pill>
        <Pill color="amber">{detail.reason}</Pill>
      </div>
      <Faint style={{ fontSize: 11 }}>{REASON_COPY[detail.reason]}</Faint>

      {evidence ? (
        <div style={{ marginTop: 6, fontSize: 12 }}>
          <div style={{ fontSize: 11, color: COLOR.textFaint }}>
            attempt-ordering evidence · success on {tgt.title} items, split at first correct {src.title} attempt
          </div>
          <div style={{ display: "flex", gap: 16, marginTop: 2 }}>
            <span>
              before{" "}
              <span style={{ fontFamily: FONT_MONO, color: COLOR.amber }}>
                {(evidence.targetSuccessBefore * 100).toFixed(0)}%
              </span>{" "}
              <Faint>(n={evidence.targetAttemptsBefore})</Faint>
            </span>
            <span>
              after{" "}
              <span style={{ fontFamily: FONT_MONO, color: COLOR.green }}>
                {(evidence.targetSuccessAfter * 100).toFixed(0)}%
              </span>{" "}
              <Faint>(n={evidence.targetAttemptsAfter})</Faint>
            </span>
          </div>
        </div>
      ) : (
        <Faint style={{ fontSize: 11, display: "block", marginTop: 4 }}>
          no attempt-ordering evidence yet (too sparse to inform direction)
        </Faint>
      )}

      {detail.rationale ? (
        <div style={{ marginTop: 6, fontSize: 12 }}>
          <Faint>edge rationale:</Faint> <Dim>{detail.rationale}</Dim>
        </div>
      ) : null}

      {edgeId ? (
        <div style={{ marginTop: 8 }}>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {DIRECTION_ACTIONS.map((a) => (
              <button
                key={a.resolution}
                style={{ ...btn, borderColor: selected === a.resolution ? COLOR.amber : COLOR.border }}
                onClick={() => setSelected(a.resolution)}
              >
                {a.label}
              </button>
            ))}
          </div>
          {selected ? (
            <div style={{ display: "flex", gap: 6, marginTop: 6, alignItems: "center" }}>
              <input
                value={rationale}
                onChange={(e) => setRationale(e.target.value)}
                placeholder={`why ${selected}? (required)`}
                style={{
                  flex: 1,
                  fontFamily: FONT_MONO,
                  fontSize: 12,
                  background: COLOR.bgInput,
                  color: COLOR.text,
                  border: `1px solid ${COLOR.borderFocus}`,
                  borderRadius: 2,
                  padding: "3px 8px",
                  outline: "none"
                }}
              />
              <button
                style={{ ...btn, color: rationale.trim() ? COLOR.green : COLOR.textFaint }}
                disabled={!rationale.trim()}
                onClick={() => {
                  onResolve(edgeId, selected, rationale.trim());
                  setSelected(null);
                  setRationale("");
                }}
              >
                confirm
              </button>
            </div>
          ) : null}
        </div>
      ) : (
        <Faint style={{ fontSize: 11, display: "block", marginTop: 6 }}>
          This edge is a pending proposal — resolve it in the Proposals inbox.
        </Faint>
      )}
    </div>
  );
}

function ConceptRef({
  id,
  title,
  onInspect
}: {
  id: string;
  title: string;
  onInspect?: (id: string) => void;
}) {
  if (onInspect) {
    return (
      <span className="entity-link" role="button" onClick={() => onInspect(id)} style={{ color: COLOR.text }}>
        {title}
      </span>
    );
  }
  return <span style={{ color: COLOR.text }}>{title}</span>;
}

// -- Restructure-request card (queued locked-facet intent — read-only) --------

function RestructureRequestCard({
  notice,
  onInspect
}: {
  notice: MaintenanceNoticeDto;
  onInspect?: (id: string) => void;
}) {
  const detail = notice.detail as unknown as RestructureRequestDetail | null;
  if (!detail) return <div style={{ marginTop: 3 }}>{notice.title}</div>;
  return (
    <div style={{ marginTop: 4, border: `1px solid ${COLOR.border}`, borderRadius: 2, padding: "8px 10px", background: COLOR.bgInput }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <Pill color="purple">{detail.operation}</Pill>
        <Pill color="slate">queued</Pill>
        <Faint style={{ fontSize: 11 }}>read-only intent · §17 restructure machinery not built yet</Faint>
      </div>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 6 }}>
        {detail.facetIds.map((f) => (
          <span key={f}>
            {onInspect ? (
              <span className="entity-link" role="button" onClick={() => onInspect(f)}>
                <Pill color="cyan">{f.replace(/^facet_/, "")}</Pill>
              </span>
            ) : (
              <Pill color="cyan">{f.replace(/^facet_/, "")}</Pill>
            )}
          </span>
        ))}
      </div>
      {detail.rationale ? (
        <div style={{ marginTop: 6, fontSize: 12 }}>
          <Faint>rationale:</Faint> <Dim>{detail.rationale}</Dim>
        </div>
      ) : null}
    </div>
  );
}
