import { type ReactNode, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import type {
  CandidateErrorTypeDto,
  CriterionEvidenceRowDto,
  ErrorEventDto,
  FeedbackBundle,
  PracticeItemDetail,
} from "../api/dto";
import { EntityLink, KeyBar, Pill } from "../components/ui";
import { MarkdownMath } from "../render/MarkdownMath";

// ── Palette ──────────────────────────────────────────────────────────────────
const C = {
  bg: "#0e0e0e",
  bgElev: "#181818",
  border: "#2a2a2a",
  borderStrong: "#3a3a3a",
  text: "#d8d8e0",
  textDim: "#9090a0",
  textItalic: "#8088a0",
  textFaint: "#666778",
  amber: "#e3a063",
  amberLink: "#f0b878",
  green: "#7fd28f",
  greenSoft: "#5fa672",
  cyan: "#6ad0e0",
  red: "#e07e7e",
};

const MONO = '"JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular, Menlo, monospace';

// ── Tiny text helpers ────────────────────────────────────────────────────────
function Faint({ children }: { children: ReactNode }) {
  return <span style={{ color: C.textFaint }}>{children}</span>;
}
function Dim({ children }: { children: ReactNode }) {
  return <span style={{ color: C.textDim }}>{children}</span>;
}
function Meta({ children }: { children: ReactNode }) {
  return <span style={{ color: C.textItalic, fontStyle: "italic", fontFamily: MONO }}>{children}</span>;
}

// Section header matching handoff design (amber underline, 22px top spacing)
function FbHeader({ children, first = false }: { children: ReactNode; first?: boolean }) {
  return (
    <div style={{
      fontFamily: MONO,
      fontSize: 14,
      color: C.amber,
      textDecoration: "underline",
      textUnderlineOffset: "3px",
      marginBottom: 14,
      marginTop: first ? 0 : 22,
    }}>
      {children}
    </div>
  );
}

// ── BlockBar ─────────────────────────────────────────────────────────────────
function BlockBar({ value, max = 1, width = 8, color = C.amber }: {
  value: number; max?: number; width?: number; color?: string;
}) {
  const filled = Math.max(0, Math.min(width, Math.round((value / max) * width)));
  return (
    <span style={{ fontFamily: MONO, letterSpacing: 0 }}>
      <span style={{ color }}>{"▓".repeat(filled)}</span>
      <span style={{ color: C.borderStrong }}>{"░".repeat(width - filled)}</span>
    </span>
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function fmtDue(iso: string | null): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    const now = new Date();
    const diffH = (d.getTime() - now.getTime()) / 3_600_000;
    const tomorrow = new Date(now);
    tomorrow.setDate(now.getDate() + 1);
    if (diffH < -23)
      return d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" }) +
        ", " + d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
    if (diffH < 0) return `${Math.round(-diffH)}h ago`;
    if (diffH < 1) return "< 1 hour";
    if (d.toDateString() === tomorrow.toDateString())
      return `tomorrow, ${d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}`;
    if (diffH < 24) return `in ${Math.round(diffH)}h`;
    return d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" }) +
      ", " + d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
}

function ratingPill(r: string): string {
  return r === "easy" ? "green" : r === "good" ? "cyan" : r === "hard" ? "amber" : "red";
}

function modePillTone(mode: string): string {
  const m: Record<string, string> = {
    short_answer: "cyan", explanation: "amber", proof: "slate",
    worked_problem: "green", free_recall: "slate", transfer: "pink",
    diagnostic_probe: "red",
  };
  return m[mode] ?? "slate";
}

// ── ScoreBlock ────────────────────────────────────────────────────────────────
function ScoreBlock({ f }: { f: FeedbackBundle }) {
  const { rubricScore: score, maxPoints: max } = f;
  const tone = score === max ? C.green
    : score >= max * 0.75 ? C.greenSoft
    : score >= max * 0.5 ? C.amber
    : C.red;
  const label = score === max ? "perfect"
    : score >= max * 0.75 ? "good"
    : score >= max * 0.5 ? "partial credit"
    : "needs work";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
      <div style={{
        border: `2px solid ${tone}`,
        padding: "14px 22px",
        fontSize: 32, fontWeight: 700,
        color: tone, lineHeight: 1,
        fontFamily: MONO, letterSpacing: 0,
        flexShrink: 0,
      }}>
        {score}<span style={{ color: C.textFaint, fontSize: 22 }}> / {max}</span>
      </div>
      <div style={{ fontSize: 13, lineHeight: 1.8 }}>
        <div><span style={{ color: tone, fontWeight: 600 }}>{label}</span></div>
        <div>
          <Faint>grader_confidence</Faint>
          {"  "}<Dim>{f.graderConfidence.toFixed(2)}</Dim>
          {"  "}<BlockBar value={f.graderConfidence} width={6} color={C.cyan} />
        </div>
        <div>
          <Faint>FSRS rating</Faint>{"  "}
          <Pill tone={ratingPill(f.fsrsRating)}>{f.fsrsRating}</Pill>
          {"  "}<Faint>next due</Faint>{" "}<Dim>{fmtDue(f.nextDueAt)}</Dim>
        </div>
        {f.gradingSource === "self" && (
          <div><Faint>source</Faint>{"  "}<Dim>self-graded</Dim></div>
        )}
        {f.fallbackReason && (
          <div><Faint>fallback</Faint>{"  "}<span style={{ color: C.amber }}>{f.fallbackReason}</span></div>
        )}
      </div>
    </div>
  );
}

// ── CriterionRow ──────────────────────────────────────────────────────────────
function CriterionRow({ row }: { row: CriterionEvidenceRowDto }) {
  const ok = row.pointsAwarded === row.pointsPossible;
  const partial = row.pointsAwarded > 0 && row.pointsAwarded < row.pointsPossible;
  const mark = ok ? "✓" : partial ? "◐" : "✗";
  const tone = ok ? C.green : partial ? C.amber : C.red;
  return (
    <div style={{
      display: "grid", gridTemplateColumns: "24px 1fr 64px",
      gap: 12, padding: "10px 0",
      borderTop: `1px solid ${C.border}`,
      fontSize: 13,
    }}>
      <div style={{ color: tone, textAlign: "center", fontWeight: 700 }}>{mark}</div>
      <div>
        <div style={{ color: C.text }}>{row.criterionDescription}</div>
        {row.evidence && (
          <div className="markdown" style={{ marginTop: 3, color: C.textDim, fontSize: 12, lineHeight: 1.55 }}>
            <MarkdownMath value={row.evidence} />
          </div>
        )}
        {row.notes && (
          <div style={{ marginTop: 3, color: C.textItalic, fontStyle: "italic", fontSize: 11 }}>
            {row.notes}
          </div>
        )}
      </div>
      <div style={{ textAlign: "right", color: tone, fontFamily: MONO }}>
        {row.pointsAwarded.toFixed(1)} / {row.pointsPossible.toFixed(1)}
      </div>
    </div>
  );
}

// ── ErrorAttribution ──────────────────────────────────────────────────────────
function ErrorAttribution({ ea, onInspect }: { ea: ErrorEventDto; onInspect: (id: string) => void }) {
  return (
    <div style={{
      padding: "12px 14px",
      border: `1px solid ${C.borderStrong}`,
      borderLeft: `3px solid ${C.red}`,
      background: "#221416",
      fontSize: 13,
      marginTop: 10,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
        <span style={{ color: C.red, fontWeight: 600 }}>
          <EntityLink id={ea.id} onInspect={onInspect}>
            {ea.errorTitle ?? ea.errorType}
          </EntityLink>
        </span>
        <span style={{ display: "inline-flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <Faint>severity</Faint>
          <BlockBar value={ea.severity} width={6} color={C.red} />
          <Dim>{ea.severity.toFixed(2)}</Dim>
          {ea.isMisconception && <Pill tone="red">misconception</Pill>}
          <Pill tone={ea.status === "active" ? "amber" : "slate"}>{ea.status}</Pill>
        </span>
      </div>
    </div>
  );
}

// ── MasteryDelta ──────────────────────────────────────────────────────────────
function MasteryDelta({ f }: { f: FeedbackBundle }) {
  const { masteryBefore: before, masteryAfter: after, surprise } = f;
  if (!before || !after) return null;

  const barColor = (m: number) => m > 0.6 ? C.green : m > 0.35 ? C.amber : C.red;
  // The backend supplies the configured surprise threshold; 0.30 is only a
  // legacy fallback for older bundles.
  const tau = surprise.followupThresholdNats ?? 0.30;
  const hasSurprise = (surprise.bayesianSurprise ?? 0) > tau;

  return (
    <div style={{ border: `1px solid ${C.border}`, borderRadius: 2, padding: "14px 18px" }}>
      <div style={{ fontSize: 13, color: C.text, marginBottom: 10 }}>
        <span style={{ color: C.amber, fontWeight: 600 }}>mastery posterior · </span>
        <Meta>logit-space Kalman update</Meta>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 24px 1fr", gap: 14, alignItems: "center" }}>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 12 }}><Faint>before</Faint></div>
          <div style={{ marginTop: 4 }}>
            <BlockBar value={before.mean} width={12} color={barColor(before.mean)} />
          </div>
          <div style={{ marginTop: 4, fontFamily: MONO, fontSize: 12 }}>
            <Dim>{before.mean.toFixed(2)} ± {Math.sqrt(before.variance).toFixed(2)}</Dim>
          </div>
        </div>
        <div style={{ textAlign: "center", color: C.amber, fontSize: 18 }}>→</div>
        <div>
          <div style={{ fontSize: 12 }}><Faint>after</Faint></div>
          <div style={{ marginTop: 4 }}>
            <BlockBar value={after.mean} width={12} color={barColor(after.mean)} />
          </div>
          <div style={{ marginTop: 4, fontFamily: MONO, fontSize: 12 }}>
            <Dim>{after.mean.toFixed(2)} ± {Math.sqrt(after.variance).toFixed(2)}</Dim>
          </div>
        </div>
      </div>
      {hasSurprise && (
        <div style={{
          marginTop: 14, padding: "8px 12px",
          background: "#221814", borderLeft: `3px solid ${C.amber}`,
          fontSize: 12, color: C.text,
        }}>
          <Pill tone="amber">surprise · {surprise.surpriseDirection ?? "unknown"}</Pill>
          {"  "}
          bayesian {(surprise.bayesianSurprise ?? 0).toFixed(2)} nats &gt; τ {tau.toFixed(2)}
          {f.followupQueued ? " — diagnostic follow-up queued." : "."}
        </div>
      )}
    </div>
  );
}

function followupStatus(f: FeedbackBundle, tau: number): string {
  const reasons = interventionReasons(f.surprise.triggeredActions ?? []);
  if (f.followupQueued) {
    return reasons.length
      ? `queued by ${reasons.join(", ")}`
      : "queued by intervention policy";
  }
  if (f.interventionNeed) {
    return `need recorded: ${formatInterventionAction(f.interventionNeed.triggerReason)} (${formatInterventionAction(f.interventionNeed.blockedReason)})`;
  }
  const suppressed = f.surprise.suppressedActions ?? [];
  if (suppressed.length > 0) {
    return `blocked: ${formatInterventionAction(suppressed[0])}`;
  }
  return `no intervention trigger; surprise threshold tau ${tau.toFixed(2)}`;
}

function interventionReasons(actions: string[]): string[] {
  const reasons = actions
    .map((action) => {
      if (action.startsWith("intervention_followup:queued:")) return null;
      if (action.startsWith("intervention_followup:")) return action.split(":")[1] ?? null;
      if (action.startsWith("negative_surprise_followup:")) return "negative_surprise";
      return null;
    })
    .filter((reason): reason is string => Boolean(reason));
  return Array.from(new Set(reasons)).map(formatInterventionAction);
}

function formatInterventionAction(action: string): string {
  return action
    .replace(/^intervention_followup:/, "")
    .replace(/^negative_surprise_followup:/, "negative_surprise:")
    .split(":")[0]
    .replace(/_/g, " ");
}

// ── FeedbackScreen ────────────────────────────────────────────────────────────
export function FeedbackScreen({
  attemptId,
  onNext,
  onBack,
  onInspect,
  onError,
}: {
  attemptId: string;
  onNext: () => void;
  onBack: () => void;
  onInspect: (id: string) => void;
  onError: (message: string) => void;
}) {
  const [feedback, setFeedback] = useState<FeedbackBundle | null>(null);
  const [item, setItem] = useState<PracticeItemDetail | null>(null);
  const [regrading, setRegrading] = useState(false);
  const [addingError, setAddingError] = useState(false);
  const [errorTypeInput, setErrorTypeInput] = useState("");
  const [selectedSuggestionIdx, setSelectedSuggestionIdx] = useState(-1);
  const errorInputRef = useRef<HTMLInputElement>(null);

  const suggestions = useMemo<CandidateErrorTypeDto[]>(() => {
    const all = item?.candidateErrorTypes ?? [];
    const q = errorTypeInput.trim().toLowerCase();
    const filtered = q
      ? all.filter((e) => e.id.toLowerCase().includes(q) || e.title.toLowerCase().includes(q))
      : all;
    return [...filtered].sort((a, b) => (b.relevant ? 1 : 0) - (a.relevant ? 1 : 0));
  }, [item, errorTypeInput]);

  useEffect(() => {
    let cancelled = false;
    api
      .getFeedback(attemptId)
      .then((bundle) => {
        if (cancelled) return;
        setFeedback(bundle);
        api
          .getPracticeItem(bundle.practiceItemId)
          .then((detail) => { if (!cancelled) setItem(detail); })
          .catch(() => {});
      })
      .catch((error) => { if (!cancelled) onError(error.message); });
    return () => { cancelled = true; };
  }, [attemptId, onError]);

  useEffect(() => {
    if (addingError) {
      errorInputRef.current?.focus();
    }
  }, [addingError]);

  useEffect(() => {
    setSelectedSuggestionIdx(-1);
  }, [errorTypeInput]);

  const handleRegrade = async () => {
    if (!feedback || regrading) return;
    setRegrading(true);
    try {
      const updated = await api.triggerRegrade(feedback.attemptId);
      setFeedback(updated);
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setRegrading(false);
    }
  };

  const doAddError = async (errorType: string, severity?: number) => {
    if (!feedback || !errorType.trim()) {
      setAddingError(false);
      setErrorTypeInput("");
      setSelectedSuggestionIdx(-1);
      return;
    }
    try {
      const updated = await api.addErrorEvent(feedback.attemptId, errorType.trim(), severity);
      setFeedback(updated);
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setAddingError(false);
      setErrorTypeInput("");
      setSelectedSuggestionIdx(-1);
    }
  };

  const handleAddError = () => {
    const sel = selectedSuggestionIdx >= 0 ? suggestions[selectedSuggestionIdx] : null;
    void doAddError(sel?.id ?? errorTypeInput, sel?.severityDefault);
  };

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea") return;
      if (event.key === "n" || event.key === "Enter") { event.preventDefault(); onNext(); }
      else if (event.key === "Escape" || event.key === "b") { event.preventDefault(); onBack(); }
      else if (event.key === "r") { event.preventDefault(); void handleRegrade(); }
      else if (event.key === "a") { event.preventDefault(); setAddingError(true); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onNext, onBack, feedback, regrading]);

  if (!feedback) {
    return (
      <div className="screen">
        <div className="screen-scroll" style={{ fontFamily: MONO, fontSize: 13, color: C.textDim }}>
          loading feedback…
        </div>
      </div>
    );
  }

  const f = feedback;
  const subject = item?.subject ?? item?.subjects?.[0] ?? null;
  // Surprise threshold from backend config; 0.30 only as a legacy fallback.
  const tau = f.surprise.followupThresholdNats ?? 0.30;
  const interventionNeed = f.interventionNeed;

  return (
    <div className="screen">
      <div className="screen-scroll" style={{ padding: "14px 24px 20px" }}>

        {/* breadcrumb */}
        <div style={{
          fontFamily: MONO, fontSize: 12, marginBottom: 14,
          display: "flex", alignItems: "center", gap: 6,
        }}>
          <span
            style={{ color: C.amberLink, textDecoration: "underline", cursor: "pointer" }}
            onClick={onBack}
          >today</span>
          <Faint>›</Faint>
          <span
            style={{ color: C.amberLink, textDecoration: "underline", cursor: "pointer" }}
            onClick={onBack}
          >practice</span>
          <Faint>›</Faint>
          <Dim>feedback</Dim>
          <Faint>›</Faint>
          <EntityLink id={f.attemptId} onInspect={onInspect} />
          <span style={{ flex: 1 }} />
          <Meta>
            grader_tier {f.criterionEvidence[0]?.graderTier ?? 0} · {f.gradingSource}
          </Meta>
        </div>

        {f.manualReviewReason && (
          <div className="toast" style={{ marginBottom: 14 }}>
            manual review recommended: {f.manualReviewReason}
          </div>
        )}

        <FbHeader first>Feedback</FbHeader>

        {/* ── main card ── */}
        <div style={{ border: `1px solid ${C.border}`, borderRadius: 2, padding: "20px 22px" }}>

          {/* item title row */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 14 }}>
            <div>
              <div style={{ fontSize: 15, fontWeight: 600, color: C.text }}>{f.learningObjectTitle}</div>
              <div style={{ marginTop: 3 }}>
                <Meta>
                  <EntityLink id={f.practiceItemId} onInspect={onInspect} />
                  {subject ? ` · ${subject}` : ""}
                </Meta>
              </div>
            </div>
            {item && <Pill tone={modePillTone(item.practiceMode)}>{item.practiceMode}</Pill>}
          </div>

          {/* divider */}
          <div style={{
            margin: "14px -22px 16px", padding: "0 22px",
            color: C.border, fontFamily: MONO,
            lineHeight: 1, whiteSpace: "nowrap", overflow: "hidden", userSelect: "none",
          }}>
            {"─".repeat(400)}
          </div>

          <ScoreBlock f={f} />

          {/* rubric criteria */}
          <div style={{ marginTop: 22 }}>
            <div style={{
              color: C.amber, fontSize: 13, marginBottom: 6,
              textDecoration: "underline", textUnderlineOffset: 3,
            }}>
              Rubric · criterion evidence
            </div>
            {f.criterionEvidence.map((row) => (
              <CriterionRow key={row.criterionId} row={row} />
            ))}
            <div style={{ borderTop: `1px solid ${C.border}` }} />
          </div>

          {/* fatal errors */}
          {f.fatalErrors.length > 0 && (
            <div style={{
              marginTop: 12, padding: "10px 12px",
              background: "#2a1010", borderLeft: `3px solid ${C.red}`,
              fontSize: 13,
            }}>
              <span style={{ color: C.red, fontWeight: 600 }}>fatal errors · </span>
              <span style={{ color: C.text }}>{f.fatalErrors.join(", ")}</span>
            </div>
          )}

          {/* tutor note */}
          {f.feedbackMd && (
            <div style={{
              marginTop: 18, padding: "12px 14px",
              background: C.bgElev, borderLeft: `3px solid ${C.cyan}`,
              fontSize: 13, lineHeight: 1.6,
            }}>
              <div style={{ color: C.cyan, fontWeight: 600, marginBottom: 4 }}>tutor note</div>
              <div className="markdown" style={{ color: C.text }}>
                <MarkdownMath value={f.feedbackMd} />
              </div>
            </div>
          )}
        </div>

        {/* ── error attribution ── */}
        {f.errorAttributions.length > 0 && (
          <>
            <FbHeader>Error attribution</FbHeader>
            {f.errorAttributions.map((ea) => (
              <ErrorAttribution key={ea.id} ea={ea} onInspect={onInspect} />
            ))}
          </>
        )}

        {/* ── belief update ── */}
        {(f.masteryBefore != null || f.masteryAfter != null) && (
          <>
            <FbHeader>Belief update</FbHeader>
            <MasteryDelta f={f} />
          </>
        )}

        {/* ── what's next ── */}
        <FbHeader>What's next</FbHeader>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>

          {/* diagnostic follow-up */}
          <div style={{
            border: `1px solid ${C.border}`,
            borderLeft: `3px solid ${f.followupQueued ? C.green : interventionNeed ? C.amber : C.borderStrong}`,
            borderRadius: 2, padding: "14px 18px",
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
              <span style={{ color: C.text, fontWeight: 600 }}>Diagnostic follow-up</span>
              {f.followupQueued
                ? <Pill tone="amber">queued</Pill>
                : interventionNeed
                ? <Pill tone="amber">need recorded</Pill>
                : <Pill tone="slate">not triggered</Pill>}
            </div>
            <div style={{ marginTop: 3 }}>
              <Meta>
                {followupStatus(f, tau)}
              </Meta>
            </div>
            {interventionNeed && (
              <div style={{ marginTop: 10, fontSize: 12, color: C.textDim, lineHeight: 1.7 }}>
                <div>
                  <Faint>need</Faint>{"  "}
                  <span style={{ fontFamily: MONO, color: C.amber }}>{interventionNeed.id}</span>
                </div>
                <div>
                  <Faint>intent</Faint>{"  "}
                  <Dim>{interventionNeed.desiredIntent}</Dim>
                  {"  "}
                  <Faint>status</Faint>{"  "}
                  <Dim>{interventionNeed.status}</Dim>
                </div>
                {interventionNeed.targetFacets.length > 0 && (
                  <div style={{ marginTop: 6, display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
                    <Faint>target facets</Faint>
                    {interventionNeed.targetFacets.map((facet) => (
                      <Pill key={facet} tone="cyan">{facet}</Pill>
                    ))}
                  </div>
                )}
              </div>
            )}
            {f.repairSuggestions.length > 0 && (
              <>
                <div style={{ marginTop: 10, fontSize: 13, color: C.text, lineHeight: 1.55 }}>
                  {f.repairSuggestions[0].rationale}
                </div>
                <div style={{ marginTop: 10, fontSize: 12 }}>
                  <Faint>mode</Faint>{"  "}
                  <Dim>{f.repairSuggestions[0].practiceMode}</Dim>
                  {f.repairSuggestions[0].learningObjectId && (
                    <>
                      {"  "}
                      <EntityLink
                        id={f.repairSuggestions[0].learningObjectId}
                        onInspect={onInspect}
                      />
                    </>
                  )}
                </div>
              </>
            )}
          </div>

          {/* schedule */}
          <div style={{ border: `1px solid ${C.border}`, borderRadius: 2, padding: "14px 18px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
              <span style={{ color: C.text, fontWeight: 600 }}>Schedule</span>
              <Pill tone="slate">FSRS · {f.fsrsRating}</Pill>
            </div>
            <div style={{ marginTop: 10, fontSize: 13, color: C.text, lineHeight: 1.6 }}>
              retrievability target 0.90 · next due <Dim>{fmtDue(f.nextDueAt)}</Dim>
            </div>
            {f.surprise.fsrsIntervalFactor != null && (
              <div style={{ marginTop: 10, fontSize: 12 }}>
                <Faint>FSRS interval factor</Faint>{"  "}
                <Dim>
                  {f.surprise.fsrsIntervalFactor.toFixed(2)}
                  {f.surprise.surpriseDirection === "negative"
                    ? " (negative surprise discount)"
                    : ""}
                </Dim>
              </div>
            )}
          </div>
        </div>

        <div style={{ height: 24 }} />
      </div>

      {addingError && (
        <div style={{ borderTop: `1px solid ${C.borderStrong}`, background: C.bgElev }}>
          {suggestions.length > 0 && (
            <div className="error-suggestions" style={{ maxHeight: 180, overflowY: "auto", borderBottom: `1px solid ${C.border}` }}>
              {suggestions.map((s, i) => (
                <div
                  key={s.id}
                  onMouseDown={(e) => { e.preventDefault(); void doAddError(s.id, s.severityDefault); }}
                  style={{
                    padding: "5px 24px",
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    cursor: "pointer",
                    background: i === selectedSuggestionIdx ? C.borderStrong : "transparent",
                    fontFamily: MONO,
                    fontSize: 12,
                  }}
                >
                  <span style={{ color: s.relevant ? C.amber : C.textFaint, flexShrink: 0, fontSize: 10 }}>
                    {s.relevant ? "◆" : "◇"}
                  </span>
                  <span style={{ color: i === selectedSuggestionIdx ? C.text : C.textDim, flex: 1 }}>{s.title}</span>
                  <span style={{ color: C.textFaint, fontSize: 10 }}>{s.id}</span>
                  {s.isMisconception && (
                    <span style={{ color: C.red, fontSize: 10, flexShrink: 0 }}>misconception</span>
                  )}
                </div>
              ))}
            </div>
          )}
          <div style={{ padding: "10px 24px", display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontFamily: MONO, fontSize: 11, color: C.amber, whiteSpace: "nowrap" }}>add error type</span>
            <input
              ref={errorInputRef}
              type="text"
              value={errorTypeInput}
              onChange={(e) => setErrorTypeInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "ArrowDown") {
                  e.preventDefault();
                  setSelectedSuggestionIdx((i) => Math.min(i + 1, suggestions.length - 1));
                } else if (e.key === "ArrowUp") {
                  e.preventDefault();
                  setSelectedSuggestionIdx((i) => Math.max(i - 1, -1));
                } else if (e.key === "Tab") {
                  e.preventDefault();
                  const s = suggestions[selectedSuggestionIdx];
                  if (s) { setErrorTypeInput(s.id); setSelectedSuggestionIdx(-1); }
                } else if (e.key === "Enter") {
                  e.preventDefault();
                  handleAddError();
                } else if (e.key === "Escape") {
                  e.preventDefault();
                  setAddingError(false);
                  setErrorTypeInput("");
                  setSelectedSuggestionIdx(-1);
                }
              }}
              placeholder="error type id or label…"
              style={{
                flex: 1,
                background: C.bg,
                border: `1px solid ${C.amber}`,
                color: C.text,
                fontFamily: MONO,
                fontSize: 13,
                padding: "6px 10px",
                outline: "none",
              }}
            />
            <span style={{ fontSize: 11, color: C.textFaint, whiteSpace: "nowrap" }}>↑↓ select · tab fill · ↵ confirm · esc cancel</span>
          </div>
        </div>
      )}

      <KeyBar
        keys={[
          { key: "n / ↵", label: "next item" },
          { key: "r", label: regrading ? "regrading…" : "regrade" },
          { key: "a", label: "add error" },
          { key: "esc / b", label: "back to queue" },
          { key: "^p", label: "palette" },
        ]}
      />
    </div>
  );
}
