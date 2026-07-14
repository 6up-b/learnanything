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
  SourceConflictDto,
  SourceSetSummaryDto,
  ConflictResolutionKind
} from "../api/dto";
import { OpenInSource } from "../components/OpenInSource";
import { COLOR, Divider, Faint, FONT_MONO, Pill, SectionHeader, TermSelect, type PillColor } from "../components/term";

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
              <div style={{ marginTop: 3 }}>{notice.title}</div>
              <div style={{ display: "flex", gap: 6, marginTop: 4 }}>
                <button style={btn} title={notice.action.action}>{notice.action.label ?? notice.action.action ?? "action"}</button>
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
