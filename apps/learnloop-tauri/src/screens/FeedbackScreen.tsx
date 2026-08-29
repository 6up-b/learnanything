import { type ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import type {
  AnswerGradingClarificationResultDto,
  AttemptTraceEvidenceDto,
  CandidateErrorTypeDto,
  CausalRepairStatusDto,
  ClaimCandidateDto,
  ColdCheckResultDto,
  CriterionEvidenceRowDto,
  ElicitingResponseResultDto,
  ErrorEventDto,
  FeedbackBundle,
  RepairSuggestionDto,
  GradingClarificationDto,
  FollowupGateDiagnosticsDto,
  FollowupGateSignalDto,
  GuidedRedoDto,
  MasteryDto,
  MasteryStepDto,
  MatchedMisconceptionDto,
  PracticeItemDetail,
  ResolvedSourceRefDto,
  UnresolvedCauseSelfReportResponse,
} from "../api/dto";
import { EntityLink, KeyBar, Pill } from "../components/ui";
import { CardControls, ProbeRemintAction } from "../components/CardControls";
import { modePillColor } from "../components/term";
import { AttemptTraceView, UnresolvedCauseCard } from "../components/KnowledgeModel";
import { ClaimSurface, mintVisitId } from "../components/ClaimSurface";
import { RepairTraceBlocks } from "../components/RepairTrace";
import type { AttemptTraceDto } from "../api/dto";
import { algoConfig, masteryTone } from "../app/algoConfig";
import { MarkdownMath } from "../render/MarkdownMath";
import {
  CausalFeedbackPanel,
  formatCausalTarget,
  formatDivergenceAnchor,
  useCausalRepairActions,
} from "../components/CausalAttribution";
import { CommonRepairCard, GuidedRedoAffordance } from "../components/RepairAffordances";
import { errorMessage } from "../errors";

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

// Compact evidence subsection used inside the scored-attempt card. Rubric
// evidence and the criterion trace are peers, so they share this hierarchy
// instead of promoting the trace to a separate top-level screen section.
function EvidenceHeader({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        color: C.amber,
        fontSize: 13,
        marginBottom: 6,
        textDecoration: "underline",
        textUnderlineOffset: 3,
      }}
    >
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

// Day-only rendering for the repair date in the cold-check banner: the learner
// remembers "Tuesday", not a timestamp, and a precise time here would imply the
// span is more exact than the claim it supports.
function fmtDay(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return iso;
  }
}

// ── ColdCheckBanner ──────────────────────────────────────────────────────────
// The post-completion announcement. It is the FIRST time this attempt is told
// what it was for: before the attempt the surface says only "unassisted check",
// because naming the repair would hand over the material under test.
function ColdCheckBanner({ result }: { result: ColdCheckResultDto }) {
  const confirmed = result.claim === "repair_confirmed";
  const failed = result.claim === "escalated_unrepaired";
  const tone = confirmed ? C.green : failed ? C.amber : C.textDim;
  const heading = confirmed
    ? "unassisted check · passed"
    : failed
      ? "unassisted check · did not hold"
      : result.claim === "downgraded"
        ? "unassisted check · recorded, not counted"
        : "unassisted check · no verdict";
  const when = fmtDay(result.instructedAt);
  const body = confirmed
    ? `This was the unassisted check for the repair you did on ${when} — you answered it without help, so the repair is confirmed and the factor is closed.`
    : failed
      ? `This was the unassisted check for the repair you did on ${when}. It did not hold on your own, so the case stays open and comes back with more support — nothing you did on ${when} is lost.`
      : result.claim === "downgraded"
        ? `This was the unassisted check for the repair you did on ${when}. Your answer is recorded, but that repair had already shown more of the solution than this check can hold constant, so it does not count as independent confirmation. Another check will be scheduled.`
        : `This was the unassisted check for the repair you did on ${when}. It did not produce a verdict${result.outcome ? ` (${result.outcome.replace(/_/g, " ")})` : ""}, so the repair stays unconfirmed.`;
  return (
    <div
      style={{
        marginTop: 14,
        padding: "11px 14px",
        background: C.bgElev,
        borderLeft: `3px solid ${tone}`,
        fontSize: 13,
        lineHeight: 1.6,
        color: C.text,
      }}
    >
      <div style={{ color: tone, fontFamily: MONO, fontSize: 11, letterSpacing: "0.08em", textTransform: "uppercase" }}>
        {heading}
      </div>
      <div style={{ marginTop: 5 }}>{body}</div>
      <div style={{ marginTop: 6, fontSize: 12 }}>
        <Faint>what it checked</Faint>{"  "}
        <Dim>{result.caseSummary}</Dim>
      </div>
      {result.claimDowngradedReason ? (
        <div style={{ marginTop: 4, fontFamily: MONO, fontSize: 11 }}>
          <Faint>downgraded · {result.claimDowngradedReason.replace(/_/g, " ")}</Faint>
        </div>
      ) : null}
    </div>
  );
}

// ── AutoPrimedNote ───────────────────────────────────────────────────────────
// The learner submitted this as an ordinary attempt and the reveal ledger
// reclassified it. Saying so is the whole point: an assisted attempt scored as
// unassisted evidence is exactly the dishonesty the ledger exists to prevent.
function AutoPrimedNote({ f }: { f: FeedbackBundle }) {
  return (
    <div
      style={{
        marginTop: 14,
        padding: "9px 12px",
        background: C.bgElev,
        borderLeft: `3px solid ${C.amber}`,
        fontSize: 12,
        lineHeight: 1.6,
        color: C.text,
      }}
    >
      Counted as assisted — tutor answers before this attempt covered part of the solution. An
      unassisted check will confirm the repair.
      {f.autoPrimedRevealTotal != null ? (
        <span style={{ marginLeft: 6 }}>
          <Faint>({(f.autoPrimedRevealTotal * 100).toFixed(0)}% of the answer already shown)</Faint>
        </span>
      ) : null}
    </div>
  );
}

// ── ElicitingRepairCard ──────────────────────────────────────────────────────
// An eliciting repair asks ONE question at the divergence instead of showing
// corrected work. The corrected work is therefore not rendered here at any
// point: showing it would answer the question the card is asking, which is the
// entire operator. `expectedResponseContract` is likewise never displayed
// before submitting — it says what a right answer would demonstrate, which is
// a hint dressed as metadata.
function ElicitingRepairCard({
  suggestion,
  submitting,
  outcome,
  onSubmit,
}: {
  suggestion: RepairSuggestionDto;
  submitting: boolean;
  outcome: ElicitingResponseResultDto | null;
  onSubmit: (responseMd: string) => void;
}) {
  const [response, setResponse] = useState("");
  const anchor = suggestion.targetRefs?.[0] ?? null;
  const answered = outcome != null;
  return (
    <div
      style={{
        border: `1px solid ${C.borderStrong}`,
        borderLeft: `3px solid ${C.cyan}`,
        background: C.bgElev,
        padding: "14px 18px",
        fontSize: 13,
        lineHeight: 1.6,
        color: C.text,
      }}
    >
      {anchor ? (
        <div style={{ fontSize: 12, marginBottom: 8 }}>
          <Faint>where it turned · </Faint>
          <Dim>{formatCausalTarget(anchor)}</Dim>
        </div>
      ) : null}
      <div className="markdown">
        <MarkdownMath value={suggestion.elicitingQuestion ?? ""} />
      </div>
      {answered ? (
        <>
          <div style={{ marginTop: 10, fontFamily: MONO, fontSize: 12, color: C.green }}>
            recorded
          </div>
          {outcome.admissibleAsIndependent ? null : (
            <div style={{ marginTop: 4, fontSize: 12, color: C.textDim }}>
              recorded — you&apos;d already seen this answer, so it won&apos;t count as independent
              evidence.
              {outcome.inadmissibilityReason ? (
                <>
                  {" "}
                  <Faint>({outcome.inadmissibilityReason.replace(/_/g, " ")})</Faint>
                </>
              ) : null}
            </div>
          )}
        </>
      ) : (
        <>
          <textarea
            value={response}
            onChange={(event) => setResponse(event.target.value)}
            disabled={submitting}
            rows={4}
            placeholder="answer in your own words"
            style={{
              marginTop: 10,
              width: "100%",
              background: C.bg,
              border: `1px solid ${C.border}`,
              color: C.text,
              fontFamily: MONO,
              fontSize: 12,
              padding: "8px 10px",
              resize: "vertical",
            }}
          />
          <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            <button
              type="button"
              disabled={submitting || !response.trim()}
              onClick={() => onSubmit(response.trim())}
              style={{
                border: `1px solid ${submitting || !response.trim() ? C.border : C.cyan}`,
                background: "transparent",
                color: submitting || !response.trim() ? C.textFaint : C.cyan,
                cursor: submitting || !response.trim() ? "default" : "pointer",
                fontFamily: MONO,
                fontSize: 11,
                padding: "5px 12px",
              }}
            >
              {submitting ? "…" : "submit"}
            </button>
            <span style={{ fontSize: 11 }}>
              <Faint>
                your own words are the point — this is not graded, it is recorded as your account of
                what happened.
              </Faint>
            </span>
          </div>
        </>
      )}
    </div>
  );
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
  const plan = ea.repairPlan;
  const resolutionStatus =
    typeof plan?.resolutionStatus === "string" ? plan.resolutionStatus : null;
  const causeScope = typeof plan?.causeScope === "string" ? plan.causeScope : null;
  const operation = typeof plan?.operation === "string" ? plan.operation : null;
  const abstentionReason =
    typeof plan?.abstentionReason === "string" ? plan.abstentionReason : null;
  const targetRef =
    plan?.targetRef && typeof plan.targetRef === "object" && !Array.isArray(plan.targetRef)
      ? plan.targetRef as Parameters<typeof formatCausalTarget>[0]
      : null;
  const firstDivergence =
    plan?.firstDivergence &&
    typeof plan.firstDivergence === "object" &&
    !Array.isArray(plan.firstDivergence)
      ? plan.firstDivergence as Parameters<typeof formatDivergenceAnchor>[0]
      : null;
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
      {resolutionStatus || causeScope || operation || targetRef ? (
        <div
          style={{
            display: "flex",
            gap: 6,
            alignItems: "center",
            flexWrap: "wrap",
            marginTop: 8,
          }}
        >
          {resolutionStatus ? <Pill tone={resolutionStatus === "resolved" ? "green" : "amber"}>{resolutionStatus.replace(/_/g, " ")}</Pill> : null}
          {causeScope ? <Pill tone="slate">{causeScope.replace(/_/g, " ")}</Pill> : null}
          {operation ? <Meta>{operation.replace(/_/g, " ")}</Meta> : null}
          {targetRef ? <Dim>target · {formatCausalTarget(targetRef)}</Dim> : null}
        </div>
      ) : null}
      {firstDivergence ? (
        <div style={{ marginTop: 7, color: C.textDim, lineHeight: 1.5 }}>
          <Faint>first divergence · </Faint>
          {formatDivergenceAnchor(firstDivergence)}
        </div>
      ) : null}
      {abstentionReason ? (
        <div style={{ marginTop: 7, color: C.amber, lineHeight: 1.5 }}>
          attribution abstained · {abstentionReason}
        </div>
      ) : null}
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

// ── Step breakdown ────────────────────────────────────────────────────────────
// A full-credit attempt can still move the posterior very little, which reads as
// a bug unless the weighting is visible. The backend sends the observation
// weight's factor chain (product == weight); this renders it as a quiet strip so
// the shift above is self-explaining. Each row's bar is the weight the factor
// removed, so the dominant term is obvious without reading the numbers.
function MasteryStepBreakdown({ step }: { step: MasteryStepDto }) {
  if (step.factors.length === 0) return null;
  const pct = (v: number) => `${Math.round(v * 100)}%`;

  return (
    <div style={{ marginTop: 12, paddingTop: 10, borderTop: `1px solid ${C.border}`, fontFamily: MONO, fontSize: 10.5 }}>
      <div style={{ display: "flex", justifyContent: "space-between", color: C.textFaint, marginBottom: 6 }}>
        <span>why this magnitude</span>
        <span>
          evidence weight{" "}
          <span style={{ color: step.atWeightFloor ? C.amber : C.textDim }}>
            {step.observationWeight.toFixed(2)}
          </span>
          {" "}of 1.00
        </span>
      </div>

      {step.factors.map((factor) => {
        const dominant = factor.key === step.dominantFactorKey;
        // Bar length is the weight this factor removed. A factor above 1.0 adds
        // weight (error sharpening); show it in the other direction.
        const removed = 1 - factor.multiplier;
        const color = dominant ? C.amber : removed < 0 ? C.greenSoft : C.textDim;
        return (
          <div
            key={factor.key}
            style={{
              display: "grid",
              gridTemplateColumns: "minmax(88px, auto) 1fr 46px 34px",
              gap: 8,
              alignItems: "center",
              lineHeight: 1.9,
            }}
          >
            <span style={{ color: dominant ? C.text : C.textDim }}>{factor.label}</span>
            <span style={{ color: C.textFaint, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {factor.detail}
            </span>
            <span style={{ color, textAlign: "right" }}>
              ×{factor.multiplier.toFixed(2)}
            </span>
            <span aria-hidden style={{ display: "block", height: 3, background: C.border, borderRadius: 2 }}>
              <span
                style={{
                  display: "block",
                  height: "100%",
                  width: `${Math.min(100, Math.abs(removed) * 100)}%`,
                  background: color,
                  borderRadius: 2,
                  opacity: dominant ? 0.9 : 0.5,
                }}
              />
            </span>
          </div>
        );
      })}

      <div style={{ color: C.textFaint, marginTop: 7, lineHeight: 1.6 }}>
        {step.expectedCorrectness !== null && step.observedCorrectness !== null ? (
          <div>
            expected {pct(step.expectedCorrectness)} · scored {pct(step.observedCorrectness)}
            <Faint> — a correct answer the model already expected is weak evidence</Faint>
          </div>
        ) : null}
        {step.atWeightFloor ? <div style={{ color: C.amber }}>weight is at the noise floor — the step cannot shrink further</div> : null}
        {!step.productReconciles ? <div>partial breakdown — some factors predate this attempt&apos;s trace</div> : null}
      </div>
    </div>
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
          <span style={{ color: C.amber, fontWeight: 600 }}>mastery estimate · posterior update · </span>
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

      {f.masteryStep ? <MasteryStepBreakdown step={f.masteryStep} /> : null}

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
      onError(errorMessage(error));
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

// ── §4.7 misconception statement-pair card ────────────────────────────────────
// Renders the evidence-relation copy for a matched registry misconception, mounted
// as a hot `diagnosis` claim so the fits / doesn't-fit / partly / edit affordances
// and exposure logging come from ClaimSurface. Two hard rules from §4.7:
//   • states an evidence relation ("consistent with confusing …"), never a belief
//     attribution ("you appear to believe …");
//   • the misconception is NEVER shown without its authored correction in the same
//     visual unit — the correction is always part of the claim text.
// Caller guarantees `m.correctionStatement` is present; this card *replaces*
// UnresolvedCauseCard for the attempt (never both — no two diagnoses at once).
function statementPairCopy(m: MatchedMisconceptionDto): string {
  const correction = m.correctionStatement.trim();
  const x = m.targetFacet?.trim();
  const y = m.confusedWithFacet?.trim();
  const head =
    x && y
      ? `Your last answer was consistent with confusing ${x} and ${y}.`
      : `Your last answer was consistent with this misconception — ${m.statement.trim()}.`;
  return `${head} The distinction to use here: ${correction}`;
}

function MisconceptionStatementCard({
  m,
  attemptId,
  sessionId,
  visitId,
  onOpenRepair,
  onError,
}: {
  m: MatchedMisconceptionDto;
  attemptId: string;
  sessionId?: string | null;
  visitId: string;
  onOpenRepair?: (misconceptionId: string) => void;
  onError: (message: string) => void;
}) {
  const claim: ClaimCandidateDto = useMemo(
    () => ({
      claimClass: "diagnosis",
      claimType: "misconception",
      claimRef: { misconceptionId: m.id, attemptId },
      claimVersion: `misconception:${m.status}`,
      producerVersion: "feedback-f3",
      surface: "feedback",
      temperature: "hot",
      claimText: statementPairCopy(m),
      provenance: m.mechanism ? `mechanism · ${m.mechanism}` : undefined,
    }),
    [m, attemptId]
  );

  return (
    <>
      <FbHeader>Diagnosis</FbHeader>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <ClaimSurface claim={claim} sessionId={sessionId} visitId={visitId} onError={onError} />
        {onOpenRepair && (
          <div style={{ fontFamily: MONO, fontSize: 12 }}>
            <span
              style={{ color: C.amberLink, textDecoration: "underline", cursor: "pointer" }}
              onClick={() => onOpenRepair(m.id)}
            >
              repair this →
            </span>
            {"   "}
            <Faint>work the distinction with side-by-side canonical spans</Faint>
          </div>
        )}
      </div>
    </>
  );
}

// ── §4.6/§4.7 regrade ledger-fact ─────────────────────────────────────────────
// A regrade is a system-authored ledger fact, not a hot diagnosis: the old→new
// receipt is visible and the only affordance is "request review" (ClaimSurface's
// regrade variant) — no confirm button, no verdict solicitation.
type RegradeReceipt = { before: { score: number; max: number }; after: { score: number; max: number } };

function RegradeLedgerCard({
  receipt,
  attemptId,
  sessionId,
  visitId,
  onError,
}: {
  receipt: RegradeReceipt;
  attemptId: string;
  sessionId?: string | null;
  visitId: string;
  onError: (message: string) => void;
}) {
  const { before, after } = receipt;
  const claim: ClaimCandidateDto = useMemo(
    () => ({
      claimClass: "ledger_fact",
      claimType: "regrade",
      claimRef: { attemptId, kind: "regrade" },
      claimVersion: `regrade:${before.score}->${after.score}`,
      producerVersion: "feedback-f3",
      surface: "feedback_regrade",
      temperature: "cold",
      claimText: `Regrade recorded — score ${before.score} / ${before.max} → ${after.score} / ${after.max}. This is a ledger fact, not a request for your verdict.`,
    }),
    [attemptId, before.score, before.max, after.score, after.max]
  );

  return (
    <>
      <FbHeader>Regrade</FbHeader>
      <ClaimSurface claim={claim} sessionId={sessionId} visitId={visitId} onError={onError} />
    </>
  );
}

// ── Meas §3.A8 clarification channel ─────────────────────────────────────────
// One question, asked only when the grade above was hedged or abstained, and
// only about something that exists solely in the learner's head. Three things
// the copy has to make unmissable, because each of them is load-bearing:
//   • it is optional — a skip is a non-event, and this card writes nothing;
//   • the grade is provisional *right now*, not "may be revised later";
//   • skipping leaves the honest uncertainty standing, and the alternative is
//     never a guess — nothing in the timeout path writes a grade at all.
const PROVISIONAL_PENDING_CLARIFICATION = "provisional_pending_clarification";

// Mirrors the closed `reason` vocabulary in migration 142 — what shape of
// uncertainty the grader hit, shown so the question does not read as arbitrary.
const CLARIFICATION_REASON_COPY: Record<string, string> = {
  ambiguous_notation: "your notation could be read two ways",
  skipped_step: "a step is missing and could be fluency or a gap",
  correct_answer_possibly_invalid_reasoning: "the answer is right; the route to it is unclear",
  method_ambiguity: "which method you were using is unclear",
  other: "the grade could not be settled from the work alone",
};

function clarificationOutcomeCopy(result: AnswerGradingClarificationResultDto): string {
  if (result.error) return result.error;
  // `abstained` is a real result, not a failed exchange: the learner answered
  // and the grader still cannot name a cause. Saying anything warmer here would
  // make A8 a machine for manufacturing resolutions.
  if (result.outcome === "abstained") {
    return "Recorded. The grader still cannot name a cause, so the uncertainty stays on the record rather than being filled in.";
  }
  if (result.outcome === "resolved") return "Recorded — the grade above was re-graded with your answer.";
  return "Recorded. The grade has not been re-graded yet.";
}

function ClarificationCard({
  clarification,
  answer,
  setAnswer,
  submitting,
  onSubmit,
  onSkip,
}: {
  clarification: GradingClarificationDto;
  answer: string;
  setAnswer: (next: string) => void;
  submitting: boolean;
  onSubmit: () => void;
  onSkip: () => void;
}) {
  return (
    <>
      <FbHeader>One question</FbHeader>
      <div style={{
        border: `1px solid ${C.borderStrong}`,
        borderLeft: `3px solid ${C.amber}`,
        background: C.bgElev,
        borderRadius: 2,
        padding: "14px 18px",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
          <Pill tone="amber">grade is provisional</Pill>
          <Faint>optional</Faint>
          <Meta>{CLARIFICATION_REASON_COPY[clarification.reason] ?? clarification.reason.replace(/_/g, " ")}</Meta>
        </div>
        <div className="markdown" style={{ marginTop: 10, fontSize: 13, lineHeight: 1.6, color: C.text }}>
          <MarkdownMath value={clarification.questionMd} />
        </div>
        <textarea
          value={answer}
          onChange={(event) => setAnswer(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
              event.preventDefault();
              onSubmit();
            }
          }}
          disabled={submitting}
          placeholder="a sentence is plenty"
          rows={2}
          style={{
            width: "100%",
            marginTop: 10,
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
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 8, fontFamily: MONO, fontSize: 12 }}>
          <span
            style={{
              color: answer.trim() && !submitting ? C.amberLink : C.textFaint,
              textDecoration: "underline",
              cursor: answer.trim() && !submitting ? "pointer" : "default",
            }}
            onClick={() => { if (answer.trim() && !submitting) onSubmit(); }}
          >{submitting ? "re-grading…" : "answer & re-grade"}</span>
          <span
            style={{ color: C.amberLink, textDecoration: "underline", cursor: "pointer" }}
            onClick={onSkip}
          >skip this</span>
          <Faint>⌘/⌃ ↵ to send</Faint>
        </div>
        <div style={{ marginTop: 10, fontSize: 12, color: C.textDim, lineHeight: 1.6 }}>
          Only you know the answer to this, so no amount of work on our side settles it. Skipping
          leaves the uncertainty exactly as it is — the grade stays the hedge that produced this
          question, and nothing is guessed in its place.
        </div>
      </div>
    </>
  );
}

// ── FeedbackScreen ────────────────────────────────────────────────────────────
export function FeedbackScreen({
  attemptId,
  sessionId,
  onNext,
  onBack,
  onOpenNotes,
  onPrimedRetry,
  onGuidedRedo,
  onOpenPractice,
  onOpenRepair,
  onOpenLibraryFile,
  onInspect,
  onPaletteEntities,
  onAsk,
  onError,
}: {
  attemptId: string;
  /** Active session, when known — lets claim exposure attribute to the session
   *  (a per-mount visitId is always minted as a fallback). */
  sessionId?: string | null;
  onNext: () => void;
  onBack: () => void;
  onOpenNotes: () => void;
  /** Open a sibling practice item as a primed retry. */
  onPrimedRetry: (practiceItemId: string) => void;
  /** Fix 3: redo ONLY the failed part of THIS item, primed, with the preserved
   *  prefix locked (available when the attempt stored a repair selection). */
  onGuidedRedo?: (redo: GuidedRedoDto) => void;
  /** Open a practice item cold (teach-back opt-in navigation). */
  onOpenPractice?: (practiceItemId: string) => void;
  /** Launch the §4.10 Repair flow for a matched misconception (the statement
   *  card's "repair this" action). Orchestrator wires App.tsx. */
  onOpenRepair?: (misconceptionId: string) => void;
  /** Open a vault file in the Library (source panel "view in Library"). */
  onOpenLibraryFile?: (path: string) => void;
  onInspect: (id: string) => void;
  onPaletteEntities?: (ids: { inspectIds: string[]; practiceItemIds: string[] }) => void;
  onAsk: (target: { context: "feedback"; attemptId: string; practiceItemId?: string }) => void;
  onError: (message: string) => void;
}) {
  const [feedback, setFeedback] = useState<FeedbackBundle | null>(null);
  const [item, setItem] = useState<PracticeItemDetail | null>(null);
  const [trace, setTrace] = useState<AttemptTraceDto | null>(null);
  const [feedbackLoadError, setFeedbackLoadError] = useState<string | null>(null);
  const [feedbackLoadRevision, setFeedbackLoadRevision] = useState(0);
  // Meas §3.A6/§3.A8. `traceEvidence` carries the reward sentence a volunteered
  // explanation earned; `clarification` is the one question that can still move
  // a provisional grade. `clarificationNote` is what came back afterwards —
  // including "still abstained", which is a result and not a failure.
  const [traceEvidence, setTraceEvidence] = useState<AttemptTraceEvidenceDto | null>(null);
  const [clarification, setClarification] = useState<GradingClarificationDto | null>(null);
  const [clarificationAnswer, setClarificationAnswer] = useState("");
  const [answeringClarification, setAnsweringClarification] = useState(false);
  const [clarificationNote, setClarificationNote] = useState<string | null>(null);
  const [regrading, setRegrading] = useState(false);
  // Old→new receipt captured when the learner triggers a regrade on this
  // screen; drives the ledger-fact claim. On a fresh load with no in-screen
  // trigger, the persisted `feedback.regrade` marker supplies the receipt
  // instead (see the render below), so out-of-session regrades still surface.
  const [regradeReceipt, setRegradeReceipt] = useState<RegradeReceipt | null>(null);
  // Stable per-mount visit id so claim exposure is attributable even when no
  // session id is threaded into this screen (present_claims needs one of them).
  const visitId = useRef(mintVisitId()).current;
  const [triggeringFollowup, setTriggeringFollowup] = useState(false);
  const [reportingFactorId, setReportingFactorId] = useState<string | null>(null);
  // P2 §6: the typed causal repair hold for this attempt's diagnosis, rendered
  // inside the claim-checked feedback panel rather than raised as an error.
  const [repairStatus, setRepairStatus] = useState<CausalRepairStatusDto | null>(null);
  // Journey B card ("Not now" is a per-view dismissal, not a persisted
  // preference — there is no probe offer to defer on a shared-repair factor).
  const [commonRepairDismissed, setCommonRepairDismissed] = useState(false);
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
    setCommonRepairDismissed(false);
    setFeedback(null);
    setItem(null);
    setTrace(null);
    setFeedbackLoadError(null);
    api
      .getFeedback(attemptId)
      .then((bundle) => {
        if (cancelled) return;
        setFeedback(bundle);
        api
          .getPracticeItem(bundle.practiceItemId)
          .then((detail) => { if (!cancelled) setItem(detail); })
          .catch((error) => {
            if (!cancelled) {
              onError(errorMessage(error, "Feedback loaded, but its practice item details could not be loaded."));
            }
          });
        // KM3b §9.6 attempt trace: the criterion DAG for this attempt. Best
        // effort — a stale sidecar simply omits the trace section.
        api
          .getAttemptTrace(attemptId)
          .then((t) => { if (!cancelled) setTrace(t); })
          .catch(() => { if (!cancelled) setTrace(null); });
      })
      .catch((error) => {
        if (!cancelled) setFeedbackLoadError(errorMessage(error, "Feedback could not be loaded."));
      });
    return () => { cancelled = true; };
  }, [attemptId, feedbackLoadRevision, onError]);

  // Meas §3.A6/§3.A8 post-grade reads. Both are best-effort and neither is ever
  // raised as a toast: a missing reward line means the grader saw nothing extra,
  // and a missing question means there was nothing it could not settle itself.
  useEffect(() => {
    let cancelled = false;
    setTraceEvidence(null);
    setClarification(null);
    setClarificationAnswer("");
    setClarificationNote(null);
    api
      .getAttemptTraceEvidence(attemptId)
      .then((result) => { if (!cancelled) setTraceEvidence(result); })
      .catch(() => { if (!cancelled) setTraceEvidence(null); });
    api
      .getGradingClarification(attemptId)
      .then((result) => { if (!cancelled) setClarification(result.clarification); })
      .catch(() => { if (!cancelled) setClarification(null); });
    return () => { cancelled = true; };
  }, [attemptId, feedbackLoadRevision]);

  // Answering re-grades with the learner's words in hand. The refreshed bundle
  // comes back on the same call, so the resolved grade is on screen before the
  // note explaining what it did — including when it did nothing.
  const handleAnswerClarification = async () => {
    const answer = clarificationAnswer.trim();
    if (!feedback || answeringClarification || !answer) return;
    setAnsweringClarification(true);
    try {
      const result = await api.answerGradingClarification(feedback.attemptId, answer);
      setFeedback(result.feedback);
      setClarification(null);
      setClarificationNote(clarificationOutcomeCopy(result));
      // The re-grade reads the same trace again and may report facets the first
      // pass missed, so the reward line is re-read rather than left stale.
      api
        .getAttemptTraceEvidence(feedback.attemptId)
        .then(setTraceEvidence)
        .catch(() => setTraceEvidence(null));
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setAnsweringClarification(false);
    }
  };

  // Skipping writes nothing, deliberately: there is no "declined" state to
  // record, and the question expires on its own TTL to the abstention that
  // produced it. Dismissing the card is the whole action.
  const handleSkipClarification = () => {
    setClarification(null);
    setClarificationNote(
      "Skipped. The grade stays provisional and keeps the grader's original uncertainty until the question expires.",
    );
  };

  // ── P2 causal repair hold (spec_causal_attribution_v1 §6, §6.6) ───────────
  // Ask the orchestrator only when the receipt says there is something to hold:
  // divergent repair classes, or a repair mapping the machine still owes. The
  // read is pure (`start_repair: false`) but still records the decision
  // receipt, so it must not fire on every feedback view.
  const applyRepairStatus = useCallback(
    (next: CausalRepairStatusDto) => {
      setRepairStatus(next);
      // The hold has lifted (typically via "Teach me now") and an episode
      // exists — hand off to the repair flow the app already owns.
      if (next.status === "started" && next.episode && onOpenRepair) {
        onOpenRepair(next.misconceptionId);
      }
    },
    [onOpenRepair],
  );

  const repairCaseId = useMemo(() => {
    const causal = feedback?.causalFeedback;
    const need = causal?.probeNeed;
    if (!causal || !need) return null;
    // Only the divergent / machine-owed shapes need a live orchestrator read.
    // The non-divergent case is no longer a dead end: the post-attempt hook
    // already consulted the lane and `causalFeedback.commonRepair` carries the
    // recommendation, so re-reading here would only mint a duplicate receipt.
    if (!need.divergent && !need.incompleteRepairMapping) return null;
    return (
      feedback?.matchedMisconception?.id ??
      causal.causalHypotheses[0]?.hypothesisId ??
      null
    );
  }, [feedback]);

  useEffect(() => {
    setRepairStatus(null);
    if (!repairCaseId) return;
    let cancelled = false;
    api
      .causalRepairStatus(repairCaseId, sessionId)
      .then((result) => {
        // A pure read reports "started" for anything the causal state does not
        // hold. There is nothing to explain then, and the orchestrator's
        // "Starting the targeted repair." copy would be untrue here — no
        // episode was minted by a read.
        if (cancelled || result.repairStatus.status === "started") return;
        setRepairStatus(result.repairStatus);
      })
      // No open factor, or no candidate case yet: nothing is being held, so
      // there is nothing to say. Never a toast — this read is speculative.
      .catch(() => {});
    return () => { cancelled = true; };
  }, [repairCaseId, sessionId]);

  const { pendingActionId: repairPendingActionId, note: repairNote, runAction: runRepairAction } =
    useCausalRepairActions({
      sessionId,
      onStatus: applyRepairStatus,
      onProbeAccepted: (offer) => {
        if (offer.practiceItemId && onOpenPractice) onOpenPractice(offer.practiceItemId);
      },
      onError,
    });

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
    const before = { score: feedback.rubricScore, max: feedback.maxPoints };
    try {
      const updated = await api.triggerRegrade(feedback.attemptId);
      setFeedback(updated);
      setRegradeReceipt({ before, after: { score: updated.rubricScore, max: updated.maxPoints } });
    } catch (error) {
      onError(errorMessage(error));
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
      onError(errorMessage(error));
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
      onError(errorMessage(error));
    } finally {
      setStartingRetry(false);
    }
  };

  // Fix 3 guided redo: redo only the failed portion of THIS item. Available
  // when the grader stored a repair selection with a preserved prefix; the
  // sidecar re-derives everything from the stored receipt, so this is a read
  // plus (at most) an episode binding.
  const [startingRedo, setStartingRedo] = useState(false);
  const handleGuidedRedo = async () => {
    if (!feedback || startingRedo || !onGuidedRedo) return;
    setStartingRedo(true);
    try {
      const redo = await api.startGuidedRedo(feedback.attemptId);
      onGuidedRedo(redo);
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setStartingRedo(false);
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
      onError(errorMessage(error));
    } finally {
      setRatingFollowup(false);
    }
  };

  // Eliciting repair: the learner's unaided answer to the one question the
  // suggestion asks. Deliberately NOT a grade — the response is recorded as
  // evidence about the factor, and the cold lane remains the only thing that
  // converts evidence into a repair verdict.
  const [elicitingSubmitting, setElicitingSubmitting] = useState(false);
  const [elicitingOutcome, setElicitingOutcome] = useState<ElicitingResponseResultDto | null>(null);
  const handleElicitingResponse = async (suggestionIndex: number, responseMd: string) => {
    if (!feedback || elicitingSubmitting) return;
    setElicitingSubmitting(true);
    try {
      const result = await api.submitElicitingResponse({
        attemptId: feedback.attemptId,
        suggestionIndex,
        responseMd,
      });
      setElicitingOutcome(result);
      // Re-render from the bundle the call returned rather than refetching:
      // it is the state the server just wrote, and a second read could race a
      // concurrent regrade into the screen.
      setFeedback(result.feedback);
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setElicitingSubmitting(false);
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
      onError(errorMessage(error));
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

  const handleUnresolvedCauseReport = async (
    factorId: string,
    response: UnresolvedCauseSelfReportResponse,
    candidateIndex?: number | null,
  ) => {
    if (!feedback || reportingFactorId) return;
    setReportingFactorId(factorId);
    try {
      await api.reportUnresolvedCause({ factorId, response, candidateIndex });
      setFeedback(await api.getFeedback(feedback.attemptId));
    } catch (error) {
      onError(errorMessage(error));
    } finally {
      setReportingFactorId(null);
    }
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
      onError(errorMessage(error));
    } finally {
      setSavingNote(false);
    }
  };

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea") return;
      if (!feedback) {
        if (event.key === "Escape" || event.key === "b") {
          event.preventDefault();
          onBack();
        }
        return;
      }
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
    if (feedbackLoadError) {
      return (
        <div className="screen">
          <div className="screen-scroll" style={{ padding: "18px 24px", fontFamily: MONO, fontSize: 13 }}>
            <div style={{ border: `1px solid ${C.border}`, padding: "16px 18px", maxWidth: 720 }}>
              <div style={{ color: C.red, marginBottom: 8 }}>Feedback could not be loaded.</div>
              <div style={{ color: C.textDim, lineHeight: 1.6 }}>{feedbackLoadError}</div>
              <div style={{ display: "flex", gap: 8, marginTop: 14, flexWrap: "wrap" }}>
                <button
                  type="button"
                  className="queue-row focused"
                  onClick={() => setFeedbackLoadRevision((value) => value + 1)}
                >
                  <span className="queue-title">Retry loading</span>
                </button>
                <button type="button" className="queue-row" onClick={onBack}>
                  <span className="queue-title">Back to Today</span>
                </button>
              </div>
            </div>
          </div>
          <KeyBar keys={[{ key: "esc", label: "today" }]} />
        </div>
      );
    }
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
  // First eliciting suggestion, by index into `repairSuggestions` — the index
  // IS the submit contract (`submitElicitingResponse` takes it), so it is read
  // off the array rather than carried separately.
  const elicitingIndex = f.repairSuggestions.findIndex((s) => !!s.elicitingQuestion?.trim());
  const elicitingSuggestion = elicitingIndex >= 0 ? f.repairSuggestions[elicitingIndex] : null;
  // §4.7: only render the statement-pair card when the matched row carries an
  // authored correction (never show a misconception naked). Without it, fall
  // back to the unresolved-cause card.
  const matchedMisconception =
    f.matchedMisconception && f.matchedMisconception.correctionStatement?.trim()
      ? f.matchedMisconception
      : null;

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

        {/* `provisional_pending_clarification` shares the manual_review_reason
            channel but is not a review request — it means this grade is not
            final yet. Reading it out as "manual review recommended" would make
            a provisional grade look settled, which is the one thing §3.A8
            requires it never do. */}
        {f.manualReviewReason === PROVISIONAL_PENDING_CLARIFICATION ? (
          <div className="toast" style={{ marginBottom: 14 }}>
            provisional grade · not final until the open clarification is answered or expires
          </div>
        ) : f.manualReviewReason ? (
          <div className="toast" style={{ marginBottom: 14 }}>
            manual review recommended: {f.manualReviewReason}
          </div>
        ) : null}

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

          {/* learner card controls — the talk-aloud moment ("off-target",
              "wants to be two questions") happens right here, answer in view */}
          {item ? (
            <CardControls
              key={`${item.id}:${item.prompt}`}
              practiceItemId={item.id}
              prompt={item.prompt}
              expectedAnswer={typeof item.expectedAnswer === "string" ? item.expectedAnswer : null}
              onError={onError}
              onChanged={() => {
                api.getPracticeItem(item.id).then(setItem).catch((error) => {
                  onError(errorMessage(error, "The card changed, but its updated feedback view could not be loaded."));
                });
              }}
              // CardControls keeps the historical feedback visible while
              // removing all mutation actions after the durable retirement.
              // Re-fetching detail here would rebuild the scheduler merely to
              // redisplay an immutable attempt.
              onRetired={() => {}}
              onTeachBack={onOpenPractice}
            />
          ) : null}

          {/* single-use probe → keep-a-copy affordance: only ever renders for
              diagnostic_probe surfaces (the component gates on the mode) */}
          {item && item.practiceMode === "diagnostic_probe" ? (
            <div style={{ display: "flex", gap: 12, alignItems: "center", marginTop: 6, flexWrap: "wrap" }}>
              <ProbeRemintAction
                attemptId={f.attemptId}
                practiceItemId={item.id}
                practiceMode={item.practiceMode}
                onError={onError}
              />
            </div>
          ) : null}

          {/* divider */}
          <div style={{
            margin: "14px -22px 16px", padding: "0 22px",
            color: C.border, fontFamily: MONO,
            lineHeight: 1, whiteSpace: "nowrap", overflow: "hidden", userSelect: "none",
          }}>
            {"─".repeat(400)}
          </div>

          <ScoreBlock f={f} />

          {/* AFTER the grade, never before: this is the first place the surface
              is allowed to say which repair the check was verifying. */}
          {f.coldCheckResult ? <ColdCheckBanner result={f.coldCheckResult} /> : null}

          {/* Auto-priming transparency: sits next to the grade it qualifies. */}
          {f.autoPrimed ? <AutoPrimedNote f={f} /> : null}

          {/* Meas §3.A6 — the visible half of "voluntary and visibly rewarded":
              what the extra line actually bought, named facet by facet. Absent
              rather than zero when the grader saw nothing beyond the item's
              declared set, because "0 additional facets" would punish the
              learner for having volunteered. */}
          {traceEvidence?.reward ? (
            <div style={{
              marginTop: 14, padding: "9px 12px",
              background: C.bgElev, borderLeft: `3px solid ${C.green}`,
              fontSize: 12, lineHeight: 1.6, color: C.text,
              display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap",
            }}>
              <span>{traceEvidence.reward}</span>
              {traceEvidence.observations
                .filter((row) => row.observationScope === "opportunistic")
                .map((row) => (
                  <Pill key={row.facetId} tone="green">{row.facetId.replace(/^facet_/, "")}</Pill>
                ))}
            </div>
          ) : null}

          {/* rubric criteria */}
          {item?.teachBackSource?.questConnection === "connected" &&
          item.teachBackSource.questSentence ? (
            <div
              style={{
                marginTop: 14,
                padding: "9px 12px",
                background: C.bgElev,
                borderLeft: `3px solid ${C.cyan}`,
                color: C.textDim,
                fontSize: 12,
                lineHeight: 1.5
              }}
            >
              This teach-back connected your explanation to:{" "}
              <span style={{ color: C.text }}>
                {item.teachBackSource.questSentence}
              </span>
            </div>
          ) : null}

          <div style={{ marginTop: 22 }}>
            <EvidenceHeader>Rubric · criterion evidence</EvidenceHeader>
            {f.criterionEvidence.map((row) => (
              <CriterionRow
                key={row.criterionId}
                row={row}
                showTier={f.criterionEvidence.some((r) => r.tier === "transfer")}
              />
            ))}
            <div style={{ borderTop: `1px solid ${C.border}` }} />
          </div>

          {trace && trace.criteria.length > 0 ? (
            <div style={{ marginTop: 22 }}>
              <EvidenceHeader>Attempt · criterion trace</EvidenceHeader>
              <AttemptTraceView trace={trace} />
            </div>
          ) : null}

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
          {f.feedbackMd && !f.causalFeedback && (
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

        {/* ── Meas §3.A8 clarification channel ──
            Sits directly under the grade it qualifies, so "provisional" and the
            thing that would settle it are never on separate screens. */}
        {clarification ? (
          <ClarificationCard
            clarification={clarification}
            answer={clarificationAnswer}
            setAnswer={setClarificationAnswer}
            submitting={answeringClarification}
            onSubmit={() => void handleAnswerClarification()}
            onSkip={handleSkipClarification}
          />
        ) : clarificationNote ? (
          <div style={{
            marginTop: 14, padding: "9px 12px",
            background: C.bgElev, borderLeft: `3px solid ${C.amber}`,
            fontFamily: MONO, fontSize: 12, lineHeight: 1.6, color: C.textDim,
          }}>
            {clarificationNote}
          </div>
        ) : null}

        {/* P1 is authoritative for learner-facing causal claims. It replaces
            the raw tutor diagnosis/correction display with receipt-typed
            sections, but the P0 one-tap unresolved-cause question remains
            available below as an evidence channel. */}
        {f.causalFeedback ? (
          <>
            <FbHeader>Causal feedback</FbHeader>
            <CausalFeedbackPanel
              feedback={f.causalFeedback}
              // Held back only until the question is answered — after that the
              // elicitation has already happened and the work can be read.
              suppressRepairedTrace={elicitingSuggestion != null && elicitingOutcome == null}
              contestPending={reportingFactorId != null}
              repairStatus={repairStatus}
              repairPendingActionId={repairPendingActionId}
              repairNote={repairNote}
              onRepairAction={runRepairAction}
              onContest={(reason, factorId) => {
                if (factorId) {
                  void handleUnresolvedCauseReport(factorId, reason);
                  return;
                }
                setReportingFactorId(`receipt:${f.attemptId}`);
                api
                  .contestCausalDiagnosis(
                    f.attemptId,
                    reason as Exclude<UnresolvedCauseSelfReportResponse, "believed_candidate">,
                  )
                  .then(() => api.getFeedback(f.attemptId))
                  .then(setFeedback)
                  .catch((error) => onError(errorMessage(error)))
                  .finally(() => setReportingFactorId(null));
              }}
            />
            {/* Journey B: every plausible cause shares one fix — deliver the
                repair instead of holding or interrogating. Rendering reads the
                recommendation off the feedback payload (recorded post-attempt);
                "Start the fix" is the same handoff "Teach me now" uses.
                Suppressed when it targets the SAME misconception the Diagnosis
                card below already offers to repair — two adjacent CTAs to one
                repair are redundant; a different target shows both. */}
            {f.causalFeedback.commonRepair && !commonRepairDismissed && !repairStatus &&
              f.causalFeedback.commonRepair.misconceptionId !== matchedMisconception?.id ? (
              <CommonRepairCard
                commonRepair={f.causalFeedback.commonRepair}
                onStartFix={(misconceptionId) => onOpenRepair?.(misconceptionId)}
                onDismiss={() => setCommonRepairDismissed(true)}
              />
            ) : null}
          </>
        ) : null}

        {/* ── diagnosis (durable misconception + P0 self-report) ──
            A matched durable misconception renders its card ALONGSIDE the
            causal panel (owner decision): the panel types the hypotheses, the
            card carries the adjudicated belief pair and its "repair this →". */}
        {matchedMisconception ? (
          <MisconceptionStatementCard
            m={matchedMisconception}
            attemptId={f.attemptId}
            sessionId={sessionId}
            visitId={visitId}
            onOpenRepair={onOpenRepair}
            onError={onError}
          />
        ) : (f.unresolvedCauses?.length ?? 0) > 0 ? (
          <div style={{ marginTop: 16 }}>
            <UnresolvedCauseCard
              causes={f.unresolvedCauses ?? []}
              onRunDiagnostic={() => void handleTriggerFollowup()}
              onSelfReport={(factorId, response, candidateIndex) => {
                void handleUnresolvedCauseReport(factorId, response, candidateIndex);
              }}
              reportingFactorId={reportingFactorId}
            />
          </div>
        ) : null}

        {/* ── regrade ledger fact ──
            Prefer the transient receipt captured by an in-screen regrade this
            visit; otherwise fall back to the persisted marker on the bundle, so
            an out-of-session regrade renders on a fresh load. Only ever one
            card — the transient path already refreshed the bundle, so we never
            render both for the same regrade. */}
        {(() => {
          const receipt: RegradeReceipt | null =
            regradeReceipt ??
            (f.regrade
              ? {
                  before: { score: f.regrade.oldScore, max: f.regrade.maxPoints },
                  after: { score: f.regrade.newScore, max: f.regrade.maxPoints },
                }
              : null);
          return receipt ? (
            <RegradeLedgerCard
              receipt={receipt}
              attemptId={f.attemptId}
              sessionId={sessionId}
              visitId={visitId}
              onError={onError}
            />
          ) : null;
        })()}

        {/* ── eliciting repair ──
            The suggestion asks instead of showing. Rendered as its own section
            so the corrected work cannot leak in beside it from the "what's
            next" card, which suppresses its trace for the same suggestion. */}
        {elicitingSuggestion ? (
          <>
            <FbHeader>One question, unaided</FbHeader>
            <ElicitingRepairCard
              suggestion={elicitingSuggestion}
              submitting={elicitingSubmitting}
              outcome={elicitingOutcome}
              onSubmit={(responseMd) => void handleElicitingResponse(elicitingIndex, responseMd)}
            />
          </>
        ) : null}

        {/* ── error attribution ── */}
        {f.errorAttributions.length > 0 && (
          <>
            <FbHeader>Error attribution</FbHeader>
            {f.errorAttributions.map((ea) => (
              <ErrorAttribution key={ea.id} ea={ea} onInspect={onInspect} />
            ))}
          </>
        )}

        {/* ── redo the part you missed (Fix 3) ──
            Gated on the server-computed availability (the SELECTED repair
            preserves a prefix), not on "any suggestion has a prefix" — the
            latter showed buttons start_guided_redo would refuse. */}
        {onGuidedRedo && f.rubricScore < f.maxPoints && f.guidedRedoAvailable ? (
          <GuidedRedoAffordance starting={startingRedo} onStart={() => void handleGuidedRedo()} />
        ) : null}

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
            {!f.causalFeedback && f.repairSuggestions.length > 0 && (
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
                {/* The trace is stored as preserved prefix + regenerated
                    continuation; showing only the fused string made a splice
                    that landed mid-sentence read as the learner's own writing.
                    Same blocks the exam per-item review mounts. */}
                {/* An eliciting suggestion's corrected work is withheld on
                    purpose: it is the answer to the question the eliciting card
                    is asking, and rendering it here would defeat the operator
                    from the other side of the screen. */}
                {f.repairSuggestions[0].repairedTrace && !f.repairSuggestions[0].elicitingQuestion?.trim() && (
                  <RepairTraceBlocks trace={f.repairSuggestions[0].repairedTrace} />
                )}
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
