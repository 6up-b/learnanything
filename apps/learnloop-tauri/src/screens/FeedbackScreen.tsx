import { type ReactNode, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import type {
  CandidateErrorTypeDto,
  CriterionEvidenceRowDto,
  ErrorEventDto,
  FeedbackBundle,
  FollowupGateDiagnosticsDto,
  FollowupGateSignalDto,
  MasteryDto,
  PracticeItemDetail,
  ResolvedSourceRefDto,
} from "../api/dto";
import { EntityLink, KeyBar, Pill } from "../components/ui";
import { modePillColor } from "../components/term";
import { algoConfig, masteryTone } from "../app/algoConfig";
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

// Class-based Pill (ui.tsx) tones are the same names as term's PillColor, so we
// reuse the shared keyword classifier — keeping mode colors consistent with the
// Today queue and inspector instead of maintaining a divergent table here.
function modePillTone(mode: string): string {
  return modePillColor(mode);
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
// `showTier` lights up when the rubric actually distinguishes core/transfer
// tiers (teach-back items) — plain rubrics stay visually unchanged.
function CriterionRow({ row, showTier = false }: { row: CriterionEvidenceRowDto; showTier?: boolean }) {
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
        <div style={{ color: C.text, display: "flex", alignItems: "baseline", gap: 8, flexWrap: "wrap" }}>
          <span>{row.criterionDescription}</span>
          {showTier && row.tier ? (
            <Pill tone={row.tier === "transfer" ? "pink" : "slate"}>{row.tier}</Pill>
          ) : null}
        </div>
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

// ── Belief-shift chart ────────────────────────────────────────────────────────
// Prior and posterior mastery are Gaussian in logit/θ space (the update is a
// Kalman step there). The bundle only carries display-space mean/variance, so we
// invert the backend's delta-method transform to recover (μ, σ) in θ-space and
// draw the two true bell curves. The x-axis stays in θ but is annotated with
// probability gridlines so it stays readable.
const SQRT_2PI = Math.sqrt(2 * Math.PI);
const PROB_TICKS = [0.1, 0.25, 0.5, 0.75, 0.9];

function logit(p: number): number {
  const c = Math.min(1 - 1e-4, Math.max(1e-4, p));
  return Math.log(c / (1 - c));
}

// Display (mean m, variance v) → θ-space (μ, σ). Backend maps θ→display via
// m = σ(μ) and v = (m(1−m))²·Var(θ) (delta method around the mean); invert both.
function toLogitSpace(mean: number, variance: number): { mu: number; sd: number } {
  const m = Math.min(1 - 1e-4, Math.max(1e-4, mean));
  const slope = m * (1 - m); // dm/dμ at the mean
  const logitVar = Math.max(1e-4, variance / (slope * slope));
  return { mu: logit(m), sd: Math.sqrt(logitVar) };
}

function gaussianPdf(x: number, mu: number, sd: number): number {
  const z = (x - mu) / sd;
  return Math.exp(-0.5 * z * z) / (sd * SQRT_2PI);
}

// The prior (dashed, dim) and posterior (filled, mastery-toned) as true Gaussians
// in θ-space, drawn to a shared vertical scale so the posterior's narrowing (or
// forgetting-driven widening) is visible, not just its shift. A directional arrow
// renders only when the Bayesian surprise crosses τ — the same bar that triggers
// a re-probe — so its presence is meaningful rather than decorative.
function BeliefShiftChart({
  before,
  after,
  bayesianSurprise,
  tau,
  width = 480,
  height = 150,
}: {
  before: MasteryDto;
  after: MasteryDto;
  bayesianSurprise: number;
  tau: number;
  width?: number;
  height?: number;
}) {
  const prior = toLogitSpace(before.mean, before.variance);
  const post = toLogitSpace(after.mean, after.variance);

  const padL = 8;
  const padR = 8;
  const padT = 20;
  const padB = 20;
  const plotW = width - padL - padR;
  const plotH = height - padT - padB;

  // Domain covers both bells (±3.4σ) and always spans the 0.15–0.85 band so the
  // probability ticks give orientation even when the belief is tight.
  const lo = Math.min(prior.mu - 3.4 * prior.sd, post.mu - 3.4 * post.sd, logit(0.15));
  const hi = Math.max(prior.mu + 3.4 * prior.sd, post.mu + 3.4 * post.sd, logit(0.85));
  const span = Math.max(1e-3, hi - lo);
  const xOf = (t: number) => padL + ((t - lo) / span) * plotW;

  // Shared vertical scale from the taller (narrower) peak, with headroom.
  const peak = Math.max(gaussianPdf(prior.mu, prior.mu, prior.sd), gaussianPdf(post.mu, post.mu, post.sd));
  const yMax = peak * 1.12;
  const baseY = padT + plotH;
  const yOf = (d: number) => padT + (1 - Math.min(1, d / yMax)) * plotH;

  const N = 72;
  const curvePath = (mu: number, sd: number, close: boolean): string => {
    let d = "";
    for (let i = 0; i <= N; i++) {
      const x = lo + (span * i) / N;
      const y = gaussianPdf(x, mu, sd);
      d += `${i === 0 ? "M" : "L"} ${xOf(x).toFixed(1)} ${yOf(y).toFixed(1)} `;
    }
    if (close) d += `L ${xOf(hi).toFixed(1)} ${baseY.toFixed(1)} L ${xOf(lo).toFixed(1)} ${baseY.toFixed(1)} Z`;
    return d;
  };

  const postColor = masteryTone(after.mean, C);
  const shift = post.mu - prior.mu;
  const showArrow = bayesianSurprise > tau && Math.abs(shift) > 1e-3;
  const arrowColor = shift >= 0 ? C.green : C.red;
  const arrowY = 11;
  const xPrior = xOf(prior.mu);
  const xPost = xOf(post.mu);
  const yPrior = yOf(gaussianPdf(prior.mu, prior.mu, prior.sd));
  const yPost = yOf(gaussianPdf(post.mu, post.mu, post.sd));

  return (
    <svg width={width} height={height} style={{ display: "block", maxWidth: "100%", overflow: "visible" }}>
      {/* probability gridlines (positioned in θ, labeled in p) */}
      {PROB_TICKS.map((p) => {
        const t = logit(p);
        if (t < lo || t > hi) return null;
        const x = xOf(t);
        const mid = p === 0.5;
        return (
          <g key={p}>
            <line
              x1={x}
              y1={padT}
              x2={x}
              y2={baseY}
              stroke={C.border}
              strokeWidth={1}
              strokeDasharray={mid ? "2 3" : "1 4"}
              opacity={mid ? 0.6 : 0.4}
            />
            <text x={x} y={baseY + 12} fill={C.textFaint} fontFamily={MONO} fontSize={9} textAnchor="middle">
              {Math.round(p * 100)}%
            </text>
          </g>
        );
      })}

      {/* baseline */}
      <line x1={padL} y1={baseY} x2={padL + plotW} y2={baseY} stroke={C.border} strokeWidth={1} />

      {/* prior peak drop-line, then the prior bell (dashed, dim) */}
      <line x1={xPrior} y1={yPrior} x2={xPrior} y2={baseY} stroke={C.textDim} strokeWidth={1} strokeDasharray="2 2" opacity={0.45} />
      <path d={curvePath(prior.mu, prior.sd, false)} fill="none" stroke={C.textDim} strokeWidth={1} strokeDasharray="3 3" opacity={0.85} />

      {/* posterior peak drop-line, then the posterior bell (filled, mastery-toned) */}
      <line x1={xPost} y1={yPost} x2={xPost} y2={baseY} stroke={postColor} strokeWidth={1} opacity={0.5} />
      <path d={curvePath(post.mu, post.sd, true)} fill={postColor} fillOpacity={0.12} stroke={postColor} strokeWidth={1.5} />

      {/* shift arrow — only when the surprise crosses τ */}
      {showArrow && (
        <g>
          <line x1={xPrior} y1={arrowY} x2={xPost} y2={arrowY} stroke={arrowColor} strokeWidth={1.5} />
          <path
            d={
              shift >= 0
                ? `M ${xPost.toFixed(1)} ${arrowY} L ${(xPost - 5).toFixed(1)} ${arrowY - 3} L ${(xPost - 5).toFixed(1)} ${arrowY + 3} Z`
                : `M ${xPost.toFixed(1)} ${arrowY} L ${(xPost + 5).toFixed(1)} ${arrowY - 3} L ${(xPost + 5).toFixed(1)} ${arrowY + 3} Z`
            }
            fill={arrowColor}
          />
        </g>
      )}
    </svg>
  );
}

// ── MasteryDelta ──────────────────────────────────────────────────────────────
function MasteryDelta({ f }: { f: FeedbackBundle }) {
  const { masteryBefore: before, masteryAfter: after, surprise } = f;
  if (!before || !after) return null;

  // The backend supplies the configured surprise threshold per bundle; the
  // config-level τ covers older bundles that predate the field.
  const tau = surprise.followupThresholdNats ?? algoConfig().tauFollowupNats;
  const bayes = surprise.bayesianSurprise ?? 0;
  const hasSurprise = bayes > tau;
  const postColor = masteryTone(after.mean, C);
  const evidence = f.criterionEvidence ?? [];

  return (
    <div style={{ border: `1px solid ${C.border}`, borderRadius: 2, padding: "14px 18px" }}>
      <div style={{
        fontSize: 13, color: C.text, marginBottom: 10,
        display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12, flexWrap: "wrap",
      }}>
        <span>
          <span style={{ color: C.amber, fontWeight: 600 }}>mastery posterior · </span>
          <Meta>logit-space Kalman update</Meta>
        </span>
        <span style={{ fontFamily: MONO, fontSize: 11, color: C.textFaint, display: "inline-flex", gap: 14, alignItems: "center" }}>
          <span><span style={{ color: C.textDim }}>╌╌</span> before</span>
          <span><span style={{ color: postColor }}>━</span> after</span>
        </span>
      </div>

      <BeliefShiftChart before={before} after={after} bayesianSurprise={bayes} tau={tau} />

      {/* numeric readout of the shift */}
      <div style={{ display: "flex", justifyContent: "center", alignItems: "baseline", gap: 12, fontFamily: MONO, fontSize: 12, marginTop: 6 }}>
        <Dim>{before.mean.toFixed(2)} ± {Math.sqrt(before.variance).toFixed(2)}</Dim>
        <span style={{ color: hasSurprise ? (after.mean >= before.mean ? C.green : C.red) : C.amber, fontSize: 15 }}>→</span>
        <span style={{ color: postColor }}>{after.mean.toFixed(2)} ± {Math.sqrt(after.variance).toFixed(2)}</span>
      </div>

      {hasSurprise && (
        <div style={{
          marginTop: 12, padding: "8px 12px",
          background: "#221814", borderLeft: `3px solid ${C.amber}`,
          fontSize: 12, color: C.text,
        }}>
          <Pill tone="amber">surprise · {surprise.surpriseDirection ?? "unknown"}</Pill>
          {"  "}
          bayesian {bayes.toFixed(2)} nats &gt; τ {tau.toFixed(2)}
          {f.followupQueued ? " — diagnostic follow-up queued." : "."}
        </div>
      )}

      {/* evidence from this attempt — the facet observations that drove the shift */}
      {evidence.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 11, color: C.textFaint, fontFamily: MONO, marginBottom: 6 }}>evidence this attempt</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {evidence.map((row) => {
              const ok = row.pointsAwarded === row.pointsPossible;
              const partial = row.pointsAwarded > 0 && row.pointsAwarded < row.pointsPossible;
              const mark = ok ? "✓" : partial ? "◐" : "✗";
              const tone = ok ? C.green : partial ? C.amber : C.red;
              return (
                <span
                  key={row.criterionId}
                  title={row.criterionDescription}
                  style={{
                    display: "inline-flex", alignItems: "center", gap: 5,
                    border: `1px solid ${C.border}`, borderLeft: `2px solid ${tone}`,
                    padding: "2px 7px", fontSize: 11, color: C.text, maxWidth: 220,
                  }}
                >
                  <span style={{ color: tone, fontWeight: 700 }}>{mark}</span>
                  <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {row.criterionDescription}
                  </span>
                </span>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function followupStatus(f: FeedbackBundle, tau: number): string {
  // Preferred: the backend gate trace names the single decisive signal for this
  // attempt (why it did or didn't fire). Falls back to the legacy action-string
  // reconstruction for attempts recorded before the trace was persisted.
  const gate = f.surprise.gateDiagnostics;
  if (gate) return describeGate(gate);

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

// ── Follow-up gate explanation ────────────────────────────────────────────────
// Renders the one decisive trigger/threshold/signal from the backend gate trace.
const GATE_SIGNAL_LABELS: Record<string, string> = {
  bayesian_surprise: "surprise",
  max_error_severity: "error severity",
  unfamiliar_posterior: "unfamiliar posterior",
  repeated_item_failures: "repeated item failures",
  repeated_facet_failures: "repeated facet failures",
  grader_confidence: "grader confidence",
  available_minutes: "available minutes",
  session_interventions: "session interventions",
  gate_score: "gate score",
};

const GATE_COMPARATORS: Record<string, string> = {
  ">": ">", ">=": "≥", "<": "<", "<=": "≤", "==": "=",
};

function gateNum(value: number | boolean | null): string | null {
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(2);
  if (typeof value === "boolean") return value ? "yes" : "no";
  return null;
}

function describeSignal(sig: FollowupGateSignalDto): string {
  const name = sig.name ?? "";
  // Signals that aren't a clean numeric comparison.
  if (name === "error_event_written") return "no error event written";
  if (name === "manual_trigger") return "manually forced";
  if (name === "eligible_items") return "no eligible diagnostic item";

  const label = GATE_SIGNAL_LABELS[name] ?? name.replace(/_/g, " ");
  const value = gateNum(sig.value);
  const cmp = sig.comparator ? GATE_COMPARATORS[sig.comparator] ?? sig.comparator : "";
  let threshold = gateNum(sig.threshold);
  // Surprise compares against τ; grader confidence against γ_min.
  if (threshold != null && name === "bayesian_surprise") threshold = `τ ${threshold}`;
  else if (threshold != null && name === "grader_confidence") threshold = `γ_min ${threshold}`;
  // Quantile-resolved thresholds say where the number came from — the
  // explanation must stay truthful when τ is data-relative, not a constant.
  if (threshold != null && sig.thresholdSource === "quantile" && sig.thresholdQuantile != null) {
    threshold = `${threshold} (p${Math.round(sig.thresholdQuantile * 100)} of your history)`;
  }
  const unit = sig.unit === "nats" ? " nats" : "";

  if (value == null && threshold == null) return label;
  if (value == null) return `${label} ${cmp} ${threshold}`.trim();
  if (threshold == null) return `${label} ${value}${unit}`.trim();
  return `${label} ${value}${unit} ${cmp} ${threshold}`.trim();
}

function describeGate(gate: FollowupGateDiagnosticsDto): string {
  const sig = gate.decisiveSignal;
  const signalText = sig ? describeSignal(sig) : gate.decisiveReason.replace(/_/g, " ");
  // In score mode, always show the continuous score against its operating
  // point — the counterfactual margin is the whole point of the redesign.
  const scoreSuffix =
    typeof gate.gateScore === "number" && sig?.name !== "gate_score"
      ? ` · score ${gate.gateScore.toFixed(2)} / ${(gate.gateScoreThreshold ?? algoConfig().gateScoreThreshold).toFixed(2)}`
      : "";

  const base = (() => {
    switch (gate.outcome) {
      case "queued":
        if (gate.decisiveReason === "manual_trigger" || gate.manualOverride) {
          return gate.naturalTriggerReasons.length
            ? `manually forced (would auto-fire: ${gate.naturalTriggerReasons.join(", ").replace(/_/g, " ")})`
            : "manually forced — gate was silent";
        }
        return `triggered by ${signalText}`;
      case "need_recorded": {
        const trigger = gate.triggeredReasons.find((r) => r !== "manual_trigger");
        const trigText = trigger ? trigger.replace(/_/g, " ") : "trigger";
        return `${trigText} fired · no suitable item, diagnostic need recorded`;
      }
      case "suppressed":
        return `blocked: ${signalText}`;
      case "not_triggered":
      default:
        // Most informative single line for "nothing fired": surprise vs τ. For a
        // non-negative surprise, the threshold comparison is moot — say so.
        if (sig && sig.name === "bayesian_surprise" && gate.surpriseDirection !== "negative") {
          const v = gateNum(sig.value);
          return `no trigger · ${gate.surpriseDirection ?? "non-negative"} surprise${v != null ? ` ${v} nats` : ""}`;
        }
        return `no trigger · ${signalText}`;
    }
  })();
  return `${base}${scoreSuffix}`;
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

// ── Source review panel ──────────────────────────────────────────────────────
// After a miss, show where in the canonical source the item came from: the
// resolved text section, or (for video sources) the transcript excerpt with a
// timestamp range, an on-demand embedded player, and an external YouTube link.
function fmtTimestamp(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const mm = h > 0 ? String(m).padStart(2, "0") : String(m);
  return `${h > 0 ? `${h}:` : ""}${mm}:${String(s).padStart(2, "0")}`;
}

function timeRangeLabel(video: { startSeconds: number; endSeconds: number | null }): string {
  return video.endSeconds != null
    ? `${fmtTimestamp(video.startSeconds)}–${fmtTimestamp(video.endSeconds)}`
    : fmtTimestamp(video.startSeconds);
}

function SourceRefCard({ sourceRef, onOpenLibraryFile, onError }: {
  sourceRef: ResolvedSourceRefDto;
  onOpenLibraryFile?: (path: string) => void;
  onError: (message: string) => void;
}) {
  // The player is never mounted until asked for: no request leaves the app on
  // feedback render (privacy + weight), and WebKitGTK codec hiccups stay opt-in.
  const [playerOpen, setPlayerOpen] = useState(false);
  const video = sourceRef.video;

  const openExternal = async (url: string) => {
    try {
      const { openUrl } = await import("@tauri-apps/plugin-opener");
      await openUrl(url);
    } catch (error) {
      onError((error as Error).message);
    }
  };

  const externalVideoUrl = video
    ? `https://www.youtube.com/watch?v=${video.videoId}&t=${Math.max(0, Math.floor(video.startSeconds))}s`
    : sourceRef.externalUrl;
  // Start the embed a few seconds early: cue boundaries rarely coincide with
  // the start of the explanation.
  const embedUrl = video
    ? `https://www.youtube-nocookie.com/embed/${video.videoId}?start=${Math.max(0, Math.floor(video.startSeconds) - 7)}`
    : null;
  // NOTE: tauri.conf.json currently ships csp: null. If a CSP is ever added,
  // it needs `frame-src https://www.youtube-nocookie.com` or this embed breaks.

  return (
    <div style={{
      border: `1px solid ${C.border}`,
      borderLeft: `3px solid ${C.cyan}`,
      borderRadius: 2, padding: "12px 16px", marginBottom: 10,
    }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
        <span style={{ color: C.text, fontWeight: 600, fontSize: 13 }}>{sourceRef.title}</span>
        {video && <Pill tone="cyan">{timeRangeLabel(video)}</Pill>}
        {sourceRef.headingPath && sourceRef.headingPath.length > 0 && (
          <Meta>{sourceRef.headingPath.join(" › ")}</Meta>
        )}
        <span style={{ flex: 1 }} />
        {sourceRef.notePath && onOpenLibraryFile && (
          <span
            style={{ color: C.amberLink, textDecoration: "underline", cursor: "pointer", fontFamily: MONO, fontSize: 12 }}
            onClick={() => onOpenLibraryFile(sourceRef.notePath!)}
          >view in Library</span>
        )}
        {externalVideoUrl && (
          <span
            style={{ color: C.amberLink, textDecoration: "underline", cursor: "pointer", fontFamily: MONO, fontSize: 12 }}
            onClick={() => void openExternal(externalVideoUrl)}
          >
            {video ? `open on YouTube at ${fmtTimestamp(video.startSeconds)}` : "open source"}
          </span>
        )}
      </div>
      {sourceRef.sourceChanged && (
        <div style={{ marginTop: 8, fontFamily: MONO, fontSize: 11, color: C.amber }}>
          ⚠ the source changed since this question was created
          {!sourceRef.locatorResolved ? " — showing the original excerpt" : ""}
        </div>
      )}
      {sourceRef.sectionMd && (
        <div className="markdown" style={{ marginTop: 10, fontSize: 13, lineHeight: 1.6, color: C.text }}>
          <MarkdownMath value={sourceRef.sectionMd} />
        </div>
      )}
      {embedUrl && (
        playerOpen ? (
          <div style={{ marginTop: 10 }}>
            <iframe
              src={embedUrl}
              title={sourceRef.title}
              style={{ width: "100%", aspectRatio: "16 / 9", border: `1px solid ${C.border}` }}
              allow="autoplay; encrypted-media; picture-in-picture"
              allowFullScreen
            />
          </div>
        ) : (
          <div style={{ marginTop: 10 }}>
            <span
              style={{ color: C.amberLink, textDecoration: "underline", cursor: "pointer", fontFamily: MONO, fontSize: 12 }}
              onClick={() => setPlayerOpen(true)}
            >▶ play here from {video ? fmtTimestamp(video.startSeconds) : "the start"}</span>
          </div>
        )
      )}
    </div>
  );
}

function SourceReviewPanel({ f, onPrimedRetry, onOpenLibraryFile, onNoteCapture, startingRetry, onError }: {
  f: FeedbackBundle;
  onPrimedRetry: () => void;
  onOpenLibraryFile?: (path: string) => void;
  onNoteCapture: () => void;
  startingRetry: boolean;
  onError: (message: string) => void;
}) {
  const refs = (f.sourceRefs ?? []).filter((ref) => ref.sectionMd || ref.video);
  // Expanded when the miss looks like a knowledge gap (an intervention need was
  // recorded, or the score was poor); a mere slip gets a collapsed disclosure.
  const missed = f.rubricScore < f.maxPoints;
  const [open, setOpen] = useState(Boolean(f.interventionNeed) || f.correctness < 0.5);
  if (refs.length === 0 || !missed) return null;

  return (
    <>
      <FbHeader>Review the source</FbHeader>
      {open ? (
        <>
          {refs.map((ref, index) => (
            <SourceRefCard
              key={`${ref.notePath ?? ref.title}:${ref.locator ?? index}`}
              sourceRef={ref}
              onOpenLibraryFile={onOpenLibraryFile}
              onError={onError}
            />
          ))}
          <div style={{ fontFamily: MONO, fontSize: 12, color: C.textDim, marginTop: 4 }}>
            {startingRetry ? (
              <span style={{ color: C.amber }}>finding a question to retry… (writing a new one can take a while)</span>
            ) : (
              <>
                <span
                  style={{ color: C.amberLink, textDecoration: "underline", cursor: "pointer" }}
                  onClick={onPrimedRetry}
                >[t] try another question on this</span>
                {"   "}
                <span
                  style={{ color: C.amberLink, textDecoration: "underline", cursor: "pointer" }}
                  onClick={onNoteCapture}
                >[j] note something down</span>
                {"   "}
                <Faint>the retry is scored as source-fresh (primed) evidence</Faint>
              </>
            )}
          </div>
        </>
      ) : (
        <div style={{ fontFamily: MONO, fontSize: 12 }}>
          <span
            style={{ color: C.amberLink, textDecoration: "underline", cursor: "pointer" }}
            onClick={() => setOpen(true)}
          >show the source this question came from ({refs.length})</span>
        </div>
      )}
    </>
  );
}

// ── FeedbackScreen ────────────────────────────────────────────────────────────
export function FeedbackScreen({
  attemptId,
  onNext,
  onBack,
  onOpenNotes,
  onPrimedRetry,
  onOpenLibraryFile,
  onInspect,
  onPaletteEntities,
  onAsk,
  onError,
}: {
  attemptId: string;
  onNext: () => void;
  onBack: () => void;
  onOpenNotes: () => void;
  /** Open a sibling practice item as a primed retry. */
  onPrimedRetry: (practiceItemId: string) => void;
  /** Open a vault file in the Library (source panel "view in Library"). */
  onOpenLibraryFile?: (path: string) => void;
  onInspect: (id: string) => void;
  onPaletteEntities?: (ids: { inspectIds: string[]; practiceItemIds: string[] }) => void;
  onAsk: (target: { context: "feedback"; attemptId: string; practiceItemId?: string }) => void;
  onError: (message: string) => void;
}) {
  const [feedback, setFeedback] = useState<FeedbackBundle | null>(null);
  const [item, setItem] = useState<PracticeItemDetail | null>(null);
  const [regrading, setRegrading] = useState(false);
  const [triggeringFollowup, setTriggeringFollowup] = useState(false);
  const [addingError, setAddingError] = useState(false);
  const [errorTypeInput, setErrorTypeInput] = useState("");
  const [selectedSuggestionIdx, setSelectedSuggestionIdx] = useState(-1);
  const errorInputRef = useRef<HTMLInputElement>(null);

  // Quick note capture — files a learner_note in the vault, linked to this
  // item's subject and learning object, without leaving the feedback view.
  const [addingNote, setAddingNote] = useState(false);
  const [noteTitle, setNoteTitle] = useState("");
  const [noteBody, setNoteBody] = useState("");
  const [savingNote, setSavingNote] = useState(false);
  const noteTitleRef = useRef<HTMLInputElement>(null);
  const noteBodyRef = useRef<HTMLTextAreaElement>(null);

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
    if (!onPaletteEntities) return;
    const inspectIds = feedback
      ? uniqueIds([
          feedback.attemptId,
          feedback.practiceItemId,
          feedback.learningObjectId,
          ...feedback.errorAttributions.map((event) => event.id),
          feedback.interventionNeed?.id ?? null,
        ])
      : uniqueIds([attemptId]);
    const practiceItemIds = feedback ? uniqueIds([feedback.practiceItemId]) : [];
    onPaletteEntities({ inspectIds, practiceItemIds });
    return () => onPaletteEntities({ inspectIds: [], practiceItemIds: [] });
  }, [attemptId, feedback, onPaletteEntities]);

  useEffect(() => {
    if (addingNote) {
      noteTitleRef.current?.focus();
    }
  }, [addingNote]);

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

  // Manually force a diagnostic follow-up even when the automatic intervention
  // gate did not fire. The backend bypasses the gates, queues the best-fit
  // diagnostic item (or records an intervention need), and logs the surprise /
  // gate context for later threshold tuning. The refreshed bundle re-renders
  // the "Diagnostic follow-up" card with the manual-trigger reason.
  const handleTriggerFollowup = async () => {
    if (!feedback || triggeringFollowup) return;
    setTriggeringFollowup(true);
    try {
      const updated = await api.triggerFollowup(feedback.attemptId);
      setFeedback(updated);
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setTriggeringFollowup(false);
    }
  };

  // Primed retry: pick (or generate) a sibling item on the same LO and open it
  // in the practice screen with primed=true. Generation is a real LLM call, so
  // the button shows a persistent working state.
  const [startingRetry, setStartingRetry] = useState(false);
  const handlePrimedRetry = async () => {
    if (!feedback || startingRetry) return;
    setStartingRetry(true);
    try {
      const result = await api.startPrimedRetry(feedback.attemptId);
      if (!result.available || !result.practiceItem) {
        onError(result.reason ?? "No retry question is available for this topic yet.");
        return;
      }
      onPrimedRetry(result.practiceItem.id);
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setStartingRetry(false);
    }
  };

  // One-tap "was this follow-up useful?" — the label stream that lets
  // `learnloop fit gate` learn the trigger weights from real usage.
  const [ratingFollowup, setRatingFollowup] = useState(false);
  const handleRateFollowup = async (useful: boolean) => {
    if (!feedback?.followupSource || ratingFollowup) return;
    setRatingFollowup(true);
    try {
      const updated = await api.rateFollowup(feedback.attemptId, useful);
      setFeedback(updated);
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setRatingFollowup(false);
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

  const resetNote = () => {
    setAddingNote(false);
    setNoteTitle("");
    setNoteBody("");
  };

  const openNoteCapture = () => {
    setAddingError(false);
    setNoteTitle((current) => current || (feedback?.learningObjectTitle ?? ""));
    setAddingNote(true);
  };

  const doSaveNote = async () => {
    if (!feedback || savingNote) return;
    const title = noteTitle.trim();
    const body = noteBody.trim();
    if (!title && !body) {
      resetNote();
      return;
    }
    const subjectId = item?.subject ?? item?.subjects?.[0] ?? null;
    if (!subjectId) {
      onError("Cannot add note: this item has no associated subject.");
      return;
    }
    const stamp = new Date().toISOString().replace(/[-:T.]/g, "").slice(0, 14);
    const noteId = `${feedback.learningObjectId}_${stamp}`;
    setSavingNote(true);
    try {
      const result = await api.addNote({
        subjectId,
        noteId,
        title: title || "Untitled note",
        body,
        relatedLos: [feedback.learningObjectId],
      });
      if (result.exitCode !== 0) {
        throw new Error(result.stderr.trim() || `add-note exited ${result.exitCode}`);
      }
      resetNote();
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setSavingNote(false);
    }
  };

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea") return;
      if (event.key === "n" || event.key === "Enter") { event.preventDefault(); onNext(); }
      else if (event.key === "Escape" || event.key === "b") { event.preventDefault(); onBack(); }
      else if (event.key === "r") { event.preventDefault(); void handleRegrade(); }
      else if (event.key === "D") { event.preventDefault(); void handleTriggerFollowup(); }
      else if (event.key === "a") { event.preventDefault(); setAddingError(true); }
      else if (event.key === "t") { event.preventDefault(); void handlePrimedRetry(); }
      else if (event.key === "j") { event.preventDefault(); openNoteCapture(); }
      else if (event.key === "o") { event.preventDefault(); onOpenNotes(); }
      else if (event.key === "?") {
        event.preventDefault();
        onAsk({ context: "feedback", attemptId, practiceItemId: feedback?.practiceItemId });
      }
      else if (event.key === "u" && feedback?.followupSource) { event.preventDefault(); void handleRateFollowup(true); }
      else if (event.key === "x" && feedback?.followupSource) { event.preventDefault(); void handleRateFollowup(false); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onNext, onBack, onOpenNotes, onAsk, attemptId, feedback, regrading, triggeringFollowup, ratingFollowup, startingRetry]);

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
  // Surprise threshold from the bundle; config-level τ for legacy bundles.
  const tau = f.surprise.followupThresholdNats ?? algoConfig().tauFollowupNats;
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

        {(f.questionHintEquivalents ?? 0) > 0 && (
          <div style={{ marginBottom: 14, fontSize: 12, color: C.textDim, fontFamily: MONO }}>
            {f.questionHintEquivalents} tutor question{(f.questionHintEquivalents ?? 0) === 1 ? "" : "s"} counted as hint
            {(f.questionHintEquivalents ?? 0) === 1 ? "" : "s"} on this attempt
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
              <CriterionRow
                key={row.criterionId}
                row={row}
                showTier={f.criterionEvidence.some((r) => r.tier === "transfer")}
              />
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

        {/* ── review the source ── */}
        <SourceReviewPanel
          f={f}
          onPrimedRetry={() => void handlePrimedRetry()}
          onOpenLibraryFile={onOpenLibraryFile}
          onNoteCapture={openNoteCapture}
          startingRetry={startingRetry}
          onError={onError}
        />

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
            {f.followupSource && (
              <div style={{ marginTop: 8, fontFamily: MONO, fontSize: 12, color: C.textDim }}>
                {f.followupRating ? (
                  <>
                    rated {f.followupRating.useful ? "useful ✓" : "not useful ✗"}
                    {"  "}
                    <Faint>[u] / [x] to change</Faint>
                  </>
                ) : (
                  <>
                    this attempt was a follow-up · was it useful?{"  "}
                    <span
                      style={{ color: C.amberLink, textDecoration: "underline", cursor: "pointer" }}
                      onClick={() => void handleRateFollowup(true)}
                    >[u] yes</span>
                    {"  "}
                    <span
                      style={{ color: C.amberLink, textDecoration: "underline", cursor: "pointer" }}
                      onClick={() => void handleRateFollowup(false)}
                    >[x] no</span>
                  </>
                )}
              </div>
            )}
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

      {addingNote && (
        <div style={{ borderTop: `1px solid ${C.borderStrong}`, background: C.bgElev }}>
          <div style={{ padding: "10px 24px 12px", display: "flex", flexDirection: "column", gap: 8 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span style={{ fontFamily: MONO, fontSize: 11, color: C.cyan, whiteSpace: "nowrap" }}>note title</span>
              <input
                ref={noteTitleRef}
                type="text"
                value={noteTitle}
                onChange={(e) => setNoteTitle(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    noteBodyRef.current?.focus();
                  } else if (e.key === "Escape") {
                    e.preventDefault();
                    resetNote();
                  }
                }}
                placeholder="note title…"
                style={{
                  flex: 1,
                  background: C.bg,
                  border: `1px solid ${C.cyan}`,
                  color: C.text,
                  fontFamily: MONO,
                  fontSize: 13,
                  padding: "6px 10px",
                  outline: "none",
                }}
              />
            </div>
            <textarea
              ref={noteBodyRef}
              value={noteBody}
              onChange={(e) => setNoteBody(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                  e.preventDefault();
                  void doSaveNote();
                } else if (e.key === "Escape") {
                  e.preventDefault();
                  resetNote();
                }
              }}
              placeholder="write your note… (markdown, math ok)"
              rows={4}
              style={{
                width: "100%",
                resize: "vertical",
                background: C.bg,
                border: `1px solid ${C.border}`,
                color: C.text,
                fontFamily: MONO,
                fontSize: 13,
                lineHeight: 1.5,
                padding: "8px 10px",
                outline: "none",
              }}
            />
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <Faint>
                files a learner_note in{" "}
                <span style={{ color: C.cyan }}>{subject ?? "—"}</span>
                {" · linked to "}
                <span style={{ color: C.cyan }}>{f.learningObjectId}</span>
              </Faint>
              <span style={{ flex: 1 }} />
              <span style={{ fontSize: 11, color: C.textFaint, whiteSpace: "nowrap" }}>
                {savingNote ? "saving…" : "⌘/⌃ ↵ save · esc cancel"}
              </span>
            </div>
          </div>
        </div>
      )}

      <KeyBar
        keys={[
          { key: "n / ↵", label: "next item" },
          { key: "r", label: regrading ? "regrading…" : "regrade" },
          { key: "⇧D", label: triggeringFollowup ? "triggering…" : "force follow-up" },
          { key: "a", label: "add error" },
          { key: "j", label: "add note" },
          { key: "o", label: "open notes" },
          { key: "?", label: "ask tutor" },
          { key: "esc / b", label: "back to queue" },
          { key: "^p", label: "palette" },
        ]}
      />
    </div>
  );
}

function uniqueIds(values: Array<string | null | undefined>): string[] {
  return Array.from(new Set(values.filter((value): value is string => Boolean(value))));
}
