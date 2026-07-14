// Motivating goal banner for the top of TodayScreen. Renders immediately from the
// goalsList summary (report is embedded on GoalDto) and streams in the trajectory
// chart (get_goal_report_series) + at-risk facet checklist (get_goal_report, lazy
// on expand). Two honest progress axes: attainment (mastery-blended predicted
// recall vs target) and certification (evidence-mass coverage), plus earned work,
// attempts-remaining pace, countdown urgency, and certification milestones.
// Degrades quietly: series/report errors render as small dim text, and every
// dual-axis field is optional-read so a stale sidecar falls back to the legacy
// on-track rendering.

import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { ClaimCandidateDto, ExamStatusSnapshot, GoalAtRiskFacetDto, GoalDto, GoalPaceDto, GoalReportSummaryDto, GoalSeriesPointDto } from "../api/dto";
import { GoalTrajectoryChart } from "./GoalTrajectoryChart";
import { mintVisitId } from "./ClaimSurface";
import { TrackRecordView } from "./TrackRecordView";
import { BlockBar, COLOR, Faint, FONT_MONO, Pill } from "./term";

function daysUntil(dueAt: string | null): number | null {
  if (!dueAt) return null;
  const due = Date.parse(dueAt);
  if (Number.isNaN(due)) return null;
  return Math.ceil((due - Date.now()) / 86_400_000);
}

function dueLabel(dueAt: string | null): string {
  const d = daysUntil(dueAt);
  if (d == null) return "open-ended";
  if (d < 0) return `${-d}d OVERDUE`;
  if (d === 0) return "due today";
  return `due in ${d}d`;
}

// Countdown urgency ramp: relaxed → amber → pink → red as the due date nears.
function dueTone(dueAt: string | null): string {
  const d = daysUntil(dueAt);
  if (d == null) return COLOR.textDim;
  if (d < 0) return COLOR.red;
  if (d < 7) return COLOR.pink;
  if (d <= 14) return COLOR.amber;
  return COLOR.textDim;
}

function statusOf(attainment: number | null): { label: string; color: string } {
  const f = attainment ?? 0;
  if (f >= 0.97) return { label: "ON TRACK", color: COLOR.green };
  if (f >= 0.8) return { label: "CLOSING IN", color: COLOR.amber };
  return { label: "BEHIND", color: COLOR.pink };
}

function actionOf(label: GoalAtRiskFacetDto["label"]): string {
  if (label === "known_gap") return "repair";
  if (label === "solid") return "review";
  return "probe";
}

const pct = (value: number | null | undefined): string =>
  value == null ? "—" : `${Math.round(value * 100)}%`;

const capitalize = (s: string): string => (s.length ? s[0].toUpperCase() + s.slice(1) : s);

// The honest pace sentence (spec §4.2). Qualifying-attempt debt, projected against the
// learner's recent rate — with every edge state (zero pace, passed due date, unknowable
// remaining work) said out loud. Days, never minutes; "roughly", never a precise date.
function buildPaceSentence(report: GoalReportSummaryDto, pace: GoalPaceDto, dueAt: string | null): string {
  const remaining = report.attemptsRemaining ?? pace.attemptsRemaining;
  const partial = report.attemptsRemainingIsPartial === true;
  const dLeft = pace.daysLeft;
  const overdue = (daysUntil(dueAt) ?? 0) < 0;

  if (remaining == null) {
    return "the remaining work isn't fully knowable yet — some facets have no practice items, so there's no attempt count to project.";
  }
  if (remaining === 0) {
    return "all facets certified — hold the line until the due date.";
  }

  const head = `≈ ${remaining} qualifying attempts outstanding${partial ? ", at least" : ""}`;
  // Until the numerator is qualification-scoped the copy must say "recent activity".
  const paceNoun = pace.paceKind === "qualifying" ? "goal pace" : "recent activity";

  const allow =
    dLeft == null
      ? "the due date is open-ended"
      : overdue
        ? `the due date passed ${Math.abs(dLeft)} ${Math.abs(dLeft) === 1 ? "day" : "days"} ago`
        : `the due date allows ${dLeft} ${dLeft === 1 ? "day" : "days"}`;

  // Zero recent pace: no rate to project — never fabricate a completion horizon.
  if (pace.attemptsLast14d <= 0 || pace.attemptsPerDay <= 0) {
    return `${head} — no goal practice in 14 days, so no pace to project. ${capitalize(allow)}.`;
  }

  const days = Math.max(1, Math.ceil(remaining / pace.attemptsPerDay));
  const verdict = overdue
    ? "Behind — past due."
    : pace.onPace
      ? "On pace."
      : `Behind pace — ${pace.neededPerDay ?? "?"}/day needed.`;
  return `${head} — at your recent ${paceNoun} of ${pace.attemptsPerDay}/day that's roughly ${days} ${days === 1 ? "day" : "days"}; ${allow}. ${verdict}`;
}

// Tri-state monospace coverage bar: certified ▓ / examined ▒ / untouched ░.
function SegmentBar({
  certified,
  examined,
  total,
  width = 24
}: {
  certified: number;
  examined: number;
  total: number;
  width?: number;
}) {
  if (total <= 0) return null;
  const cells = Math.min(width, Math.max(total, 1));
  const certCells = Math.round((certified / total) * cells);
  const examCells = Math.max(Math.round((examined / total) * cells) - certCells, 0);
  const restCells = Math.max(cells - certCells - examCells, 0);
  return (
    <span style={{ fontFamily: FONT_MONO, fontSize: 12, letterSpacing: 1 }}>
      <span style={{ color: COLOR.green }}>{"▓".repeat(certCells)}</span>
      <span style={{ color: COLOR.amber }}>{"▒".repeat(examCells)}</span>
      <span style={{ color: COLOR.borderStrong }}>{"░".repeat(restCells)}</span>
    </span>
  );
}

export function GoalBanner({
  goals,
  onError,
  onPracticeAtRisk,
  onTakeExam,
  onNewGoal
}: {
  goals: GoalDto[]; // active goals, primary first
  onError: (message: string) => void;
  onPracticeAtRisk: () => void;
  onTakeExam?: (goalId: string) => void;
  onNewGoal: () => void;
}) {
  const [selectedId, setSelectedId] = useState<string>(goals[0]?.id ?? "");
  const goal = useMemo(() => goals.find((g) => g.id === selectedId) ?? goals[0], [goals, selectedId]);

  const [series, setSeries] = useState<GoalSeriesPointDto[] | null>(null);
  const [seriesLoading, setSeriesLoading] = useState(false);
  const [seriesError, setSeriesError] = useState<string | null>(null);

  const [expanded, setExpanded] = useState(false);
  const [atRisk, setAtRisk] = useState<GoalAtRiskFacetDto[] | null>(null);
  const [atRiskError, setAtRiskError] = useState<string | null>(null);

  const [exam, setExam] = useState<ExamStatusSnapshot | null>(null);
  const [celebrateCount, setCelebrateCount] = useState<number | null>(null);

  const [showTrackRecord, setShowTrackRecord] = useState(false);
  const [showPlanning, setShowPlanning] = useState(false);
  const [scenarioDays, setScenarioDays] = useState<number | null>(null); // learner's study-days/week
  const [presentationId, setPresentationId] = useState<string | null>(null);
  const [overrideSaved, setOverrideSaved] = useState(false);
  const [visitId] = useState(() => mintVisitId());

  const goalId = goal?.id;
  const report = goal?.report ?? null;

  // Keep selection valid if the active-goal set changes underneath us.
  useEffect(() => {
    if (goalId && !goals.some((g) => g.id === selectedId)) setSelectedId(goalId);
  }, [goals, goalId, selectedId]);

  // Stream in the trajectory series (may take a couple seconds).
  useEffect(() => {
    if (!goalId) return;
    let cancelled = false;
    setSeries(null);
    setSeriesError(null);
    setSeriesLoading(true);
    api
      .getGoalReportSeries(goalId)
      .then((snap) => {
        if (!cancelled) setSeries(snap.series);
      })
      .catch((e) => {
        if (!cancelled) setSeriesError((e as Error).message);
      })
      .finally(() => {
        if (!cancelled) setSeriesLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [goalId]);

  // Exam availability (only when the goal opted into a held-out exam).
  useEffect(() => {
    if (!goalId || !goal?.exam.enabled) {
      setExam(null);
      return;
    }
    let cancelled = false;
    api
      .getExamStatus(goalId)
      .then((snap) => {
        if (!cancelled) setExam(snap);
      })
      .catch(() => {
        if (!cancelled) setExam(null);
      });
    return () => {
      cancelled = true;
    };
  }, [goalId, goal?.exam.enabled]);

  // Lazily load the at-risk facet checklist when the learner expands it.
  useEffect(() => {
    if (!expanded || !goalId || atRisk != null) return;
    let cancelled = false;
    api
      .getGoalReport(goalId)
      .then((snap) => {
        if (!cancelled) setAtRisk(snap.report.atRisk);
      })
      .catch((e) => {
        if (!cancelled) setAtRiskError((e as Error).message);
      });
    return () => {
      cancelled = true;
    };
  }, [expanded, goalId, atRisk]);

  // Reset lazy/streamed state when switching goals.
  useEffect(() => {
    setExpanded(false);
    setAtRisk(null);
    setAtRiskError(null);
    setCelebrateCount(null);
    setShowTrackRecord(false);
    setShowPlanning(false);
    setScenarioDays(null);
    setPresentationId(null);
    setOverrideSaved(false);
  }, [goalId]);

  // Milestone celebration: a facet certified since this goal was last rendered.
  const certifiedCount = report?.certifiedCount;
  useEffect(() => {
    if (!goalId || certifiedCount == null) return;
    const key = `learnloop.goalCertified.${goalId}`;
    const previous = Number(window.localStorage.getItem(key) ?? "0");
    if (certifiedCount > previous && previous > 0) {
      setCelebrateCount(certifiedCount - previous);
    }
    window.localStorage.setItem(key, String(certifiedCount));
  }, [goalId, certifiedCount]);

  if (!goal) return null;

  const hasDualAxis = report?.attainmentFraction !== undefined;
  const attainment = report?.attainmentFraction ?? report?.onTrackFraction ?? null;
  const status = statusOf(attainment);
  const targetPct = Math.round(goal.targetRecall * 100);
  const tone = goal.dueAt ? dueTone(goal.dueAt) : status.color;

  // Weekly delta: prefer certification milestones, fall back to attainment movement.
  const lastTwo = series && series.length >= 2 ? series.slice(-2) : null;
  const certDelta =
    lastTwo && lastTwo[0].certifiedCount != null && lastTwo[1].certifiedCount != null
      ? (lastTwo[1].certifiedCount ?? 0) - (lastTwo[0].certifiedCount ?? 0)
      : null;
  const attainDelta =
    lastTwo && lastTwo[0].attainmentFraction != null && lastTwo[1].attainmentFraction != null
      ? (lastTwo[1].attainmentFraction ?? 0) - (lastTwo[0].attainmentFraction ?? 0)
      : lastTwo
        ? (lastTwo[1].onTrackFraction ?? 0) - (lastTwo[0].onTrackFraction ?? 0)
        : null;

  const pace = report?.pace ?? null;
  const atRiskCount = report?.atRiskCount ?? 0;
  const showExamButton = Boolean(onTakeExam && goal.exam.enabled && exam && exam.poolItemCount > 0);
  const paceOverdue = (daysUntil(goal.dueAt) ?? 0) < 0;
  const paceZero = pace != null && (pace.attemptsLast14d <= 0 || pace.attemptsPerDay <= 0);
  const paceRemaining = report?.attemptsRemaining ?? pace?.attemptsRemaining ?? null;
  const paceTone = paceOverdue
    ? COLOR.pink
    : paceZero || paceRemaining == null
      ? COLOR.textDim
      : pace?.onPace === false
        ? COLOR.amber
        : COLOR.green;

  // The forecast claim behind the pace sentence. When an open pace forecast row
  // has been issued (session start / maintenance), its id reaches the boundary on
  // report.activeForecasts.pace and the planning-override claim references it
  // directly; otherwise the ref falls back to a goal-scoped one, labeled as such.
  const paceForecast = report?.activeForecasts?.pace ?? null;
  const paceSentence = report && pace ? buildPaceSentence(report, pace, goal.dueAt) : null;

  // Planning override: recompute the horizon under "n study days/week", clearly the
  // learner's scenario, and log it to the forecast ledger via respondClaim.
  const canProject = pace != null && pace.attemptsPerDay > 0 && paceRemaining != null && paceRemaining > 0;
  async function applyPlanningOverride(daysPerWeek: number) {
    setScenarioDays(daysPerWeek);
    if (!goalId || !report || !paceSentence) return;
    try {
      let pid = presentationId;
      if (!pid) {
        const candidate: ClaimCandidateDto = {
          claimClass: "estimate",
          claimType: "forecast",
          claimRef: paceForecast
            ? { forecastId: paceForecast.id, issuedAt: paceForecast.issuedAt, goalId, kind: "pace_forecast" }
            : { goalId, kind: "pace_forecast", ref: "goal_scoped" },
          claimVersion: "goal-pace-1",
          producerVersion: "goal_banner_f4",
          surface: "today_goal_hero",
          temperature: "cold",
          claimText: paceSentence
        };
        const result = await api.presentClaims([{ ...candidate, visibleAt: new Date().toISOString() }], { visitId });
        pid = result.claims[0]?.presentationId ?? null;
        setPresentationId(pid);
      }
      if (pid) {
        const rate = pace?.attemptsPerDay ?? 0;
        const projected =
          canProject && rate > 0
            ? Math.max(1, Math.ceil((paceRemaining as number) / (rate * (daysPerWeek / 7))))
            : null;
        await api.respondClaim(pid, {
          response: "planning_override",
          studyDaysPerWeek: daysPerWeek,
          projectedDays: projected,
          basePaceKind: pace?.paceKind ?? null
        });
        setOverrideSaved(true);
      }
    } catch (e) {
      onError((e as Error).message);
    }
  }

  return (
    <div
      style={{
        margin: "16px 24px 0",
        border: `1px solid ${COLOR.borderStrong}`,
        borderLeft: `3px solid ${tone}`,
        background: COLOR.bgElev
      }}
    >
      <style>{`@keyframes llGoalCertPulse { from { background: rgba(80, 200, 120, 0.22); } to { background: transparent; } }`}</style>

      {/* ── header ── */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 16px", borderBottom: `1px solid ${COLOR.border}` }}>
        <span style={{ fontSize: 10, color: COLOR.textFaint, letterSpacing: "0.18em", textTransform: "uppercase", fontFamily: FONT_MONO }}>
          goal
        </span>
        <span style={{ fontSize: 14, color: COLOR.text, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {goal.title}
        </span>
        {goals.length > 1 ? (
          <span style={{ display: "inline-flex", gap: 4, marginLeft: 4 }}>
            {goals.map((g) => (
              <span
                key={g.id}
                onClick={() => setSelectedId(g.id)}
                title={g.title}
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  cursor: "pointer",
                  background: g.id === goal.id ? COLOR.amber : COLOR.borderStrong
                }}
              />
            ))}
          </span>
        ) : null}
        <span style={{ flex: 1 }} />
        <span
          style={{
            fontFamily: FONT_MONO,
            fontSize: 12,
            fontWeight: 600,
            color: tone,
            border: `1px solid ${goal.dueAt ? tone : COLOR.border}`,
            padding: "2px 8px",
            whiteSpace: "nowrap"
          }}
        >
          {dueLabel(goal.dueAt)}
        </span>
      </div>

      {/* ── body ── */}
      <div style={{ display: "flex", gap: 24, padding: "14px 16px", flexWrap: "wrap" }}>
        {/* left: status + dual-axis progress + work remaining + at-risk checklist */}
        <div style={{ flex: "1 1 340px", minWidth: 280 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <span
              style={{
                fontFamily: FONT_MONO,
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: "0.12em",
                color: status.color,
                border: `1px solid ${status.color}`,
                padding: "2px 8px"
              }}
            >
              {status.label}
            </span>
            <span style={{ fontSize: 13, color: COLOR.text }}>
              {report == null
                ? "no report yet"
                : hasDualAxis
                  ? `predicted recall ${pct(report.predictedRecallMean)} · target ${targetPct}%`
                  : `${report.onTrackCount}/${report.total} facets ≥ ${targetPct}%`}
            </span>
            {certDelta != null && certDelta > 0 ? (
              <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.green }}>
                ▲ +{certDelta} certified this week
              </span>
            ) : attainDelta != null && Math.abs(attainDelta) >= 0.01 ? (
              <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: attainDelta > 0 ? COLOR.green : COLOR.pink }}>
                {attainDelta > 0 ? "▲" : "▼"} {attainDelta > 0 ? "+" : ""}
                {Math.round(attainDelta * 100)}pp this week
              </span>
            ) : null}
          </div>

          {/* attainment bar */}
          <div style={{ marginTop: 10, display: "flex", alignItems: "center", gap: 10 }}>
            <BlockBar value={attainment ?? 0} width={28} color={status.color} />
            <span style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.text }}>{pct(attainment)}</span>
            <Faint style={{ fontSize: 11 }}>toward target</Faint>
          </div>

          {/* coverage bar (certified / examined / untouched) */}
          {hasDualAxis && report ? (
            <div style={{ marginTop: 6, display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <SegmentBar
                certified={report.certifiedCount ?? 0}
                examined={report.examinedCount ?? 0}
                total={report.total}
                width={28}
              />
              <Faint style={{ fontSize: 11, fontFamily: FONT_MONO }}>
                {report.certifiedCount ?? 0} certified · {Math.max((report.examinedCount ?? 0) - (report.certifiedCount ?? 0), 0)} examined ·{" "}
                {Math.max(report.total - (report.examinedCount ?? 0), 0)} untouched
              </Faint>
            </div>
          ) : null}

          {/* earned progress */}
          {hasDualAxis && report ? (
            <div style={{ marginTop: 10, fontSize: 11, color: COLOR.textFaint, fontFamily: FONT_MONO }}>
              {pace ? `${pace.attemptsLogged} attempts` : null}
              {pace ? " · " : null}
              {report.examinedCount ?? 0}/{report.total} facets examined · {report.certifiedCount ?? 0} certified
              {report.latestExam?.score != null ? ` · last exam ${pct(report.latestExam.score)}` : null}
            </div>
          ) : null}

          {/* work remaining + pace — the honest pace sentence (spec §4.2) */}
          {hasDualAxis && paceSentence ? (
            <div style={{ marginTop: 8, fontSize: 12, color: paceTone, fontFamily: FONT_MONO, lineHeight: 1.55 }}>
              {paceSentence}
            </div>
          ) : null}

          {/* content-gap callout (spec §4.2 / §4.11). Goal summary DTO exposes only the
              boolean attemptsRemainingIsPartial — no per-facet no-supply count — so we
              use the at-risk list (once loaded) as a lower bound and otherwise qualify. */}
          {hasDualAxis && report?.attemptsRemainingIsPartial ? (
            (() => {
              const noSupply = atRisk ? atRisk.filter((f) => f.attemptsToCertify == null).length : null;
              return (
                <div style={{ marginTop: 6, fontSize: 11, color: COLOR.pink, fontFamily: FONT_MONO }}>
                  ⚠ {noSupply != null && noSupply > 0 ? `${noSupply}+ ` : "some "}facets have no practice items yet — create practice so they can count.
                </div>
              );
            })()
          ) : null}

          {/* planning override + track record — one tap from the forecast hero */}
          {hasDualAxis && paceSentence ? (
            <div style={{ marginTop: 8, display: "flex", gap: 14, flexWrap: "wrap", alignItems: "center" }}>
              {canProject ? (
                <button
                  type="button"
                  onClick={() => setShowPlanning((v) => !v)}
                  style={{ background: "transparent", border: "none", padding: 0, color: COLOR.amberLink, cursor: "pointer", fontFamily: FONT_MONO, fontSize: 11 }}
                >
                  {showPlanning ? "▾" : "▸"} plan around my week
                </button>
              ) : null}
              <button
                type="button"
                onClick={() => setShowTrackRecord((v) => !v)}
                style={{ background: "transparent", border: "none", padding: 0, color: COLOR.amberLink, cursor: "pointer", fontFamily: FONT_MONO, fontSize: 11 }}
              >
                {showTrackRecord ? "▾" : "▸"} how good are these forecasts?
              </button>
            </div>
          ) : null}

          {showPlanning && canProject && pace ? (
            <div style={{ marginTop: 8, padding: "8px 10px", border: `1px solid ${COLOR.border}`, fontFamily: FONT_MONO, fontSize: 11 }}>
              <div style={{ color: COLOR.textDim, display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                <span>use my usual</span>
                {[2, 3, 4, 5, 6, 7].map((n) => (
                  <button
                    key={n}
                    type="button"
                    onClick={() => void applyPlanningOverride(n)}
                    aria-pressed={scenarioDays === n}
                    style={{
                      minWidth: 22,
                      padding: "1px 6px",
                      border: `1px solid ${scenarioDays === n ? COLOR.amber : COLOR.borderStrong}`,
                      background: scenarioDays === n ? COLOR.amber : "transparent",
                      color: scenarioDays === n ? COLOR.bg : COLOR.text,
                      cursor: "pointer",
                      fontFamily: FONT_MONO,
                      fontSize: 11
                    }}
                  >
                    {n}
                  </button>
                ))}
                <span>study days/week</span>
              </div>
              {scenarioDays != null ? (
                <div style={{ marginTop: 6, color: COLOR.cyan }}>
                  your scenario — {scenarioDays} days/week at ~{pace.attemptsPerDay}/study-day →{" "}
                  {(() => {
                    const projected = Math.max(1, Math.ceil((paceRemaining as number) / (pace.attemptsPerDay * (scenarioDays / 7))));
                    return `roughly ${projected} ${projected === 1 ? "day" : "days"}`;
                  })()}
                  {pace.daysLeft != null ? `; the due date allows ${pace.daysLeft} ${pace.daysLeft === 1 ? "day" : "days"}` : ""}.
                  <Faint style={{ display: "block", marginTop: 2, fontSize: 10 }}>
                    your what-if, not a system forecast{overrideSaved ? " · saved to your forecast ledger" : ""}
                  </Faint>
                </div>
              ) : null}
            </div>
          ) : null}

          {showTrackRecord ? (
            <TrackRecordView goalId={goalId} onClose={() => setShowTrackRecord(false)} onError={onError} />
          ) : null}

          {/* milestone celebration */}
          {celebrateCount != null ? (
            <div
              style={{
                marginTop: 10,
                padding: "6px 10px",
                border: `1px solid ${COLOR.green}`,
                color: COLOR.green,
                fontFamily: FONT_MONO,
                fontSize: 12,
                animation: "llGoalCertPulse 2.4s ease-out 1"
              }}
            >
              ▲ {celebrateCount === 1 ? "facet certified" : `${celebrateCount} facets certified`} — {report?.certifiedCount ?? 0} total
            </div>
          ) : null}

          {/* at-risk facet checklist (lazy on expand) */}
          {atRiskCount > 0 ? (
            <div style={{ marginTop: 12 }}>
              <span
                onClick={() => setExpanded((v) => !v)}
                style={{ fontSize: 12, color: COLOR.amberLink, cursor: "pointer", fontFamily: FONT_MONO }}
              >
                {expanded ? "▾" : "▸"} to do: {atRiskCount} {atRiskCount === 1 ? "facet" : "facets"} need work
              </span>
              {expanded ? (
                <div style={{ marginTop: 6, fontSize: 12, color: COLOR.textDim, lineHeight: 1.7 }}>
                  {atRiskError ? (
                    <Faint style={{ color: COLOR.red }}>{atRiskError}</Faint>
                  ) : atRisk == null ? (
                    <Faint>loading…</Faint>
                  ) : atRisk.length === 0 ? (
                    <Faint>none</Faint>
                  ) : (
                    <>
                      {atRisk.slice(0, 8).map((f) => (
                        <div key={`${f.learningObjectId}:${f.facetId}`} style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
                          <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1, minWidth: 80 }}>
                            {f.learningObjectTitle}
                          </span>
                          <Pill color="slate">{f.facetId}</Pill>
                          {/* KM3 §9.6 display rule: a goal surface leads with
                              Demonstrated (direct evidence), then the Ready
                              prediction — never blended into one number. */}
                          {f.demonstrated ? (
                            <Pill color="green">demonstrated</Pill>
                          ) : (
                            <Pill color="slate">not demonstrated</Pill>
                          )}
                          {f.evidenceMass != null ? (
                            <BlockBar value={Math.min(f.evidenceMass / 0.5, 1)} width={6} color={f.certified ? COLOR.green : COLOR.amber} />
                          ) : null}
                          <Faint style={{ fontFamily: FONT_MONO, fontSize: 11, whiteSpace: "nowrap" }}>
                            {(f.ready ?? f.predictedAtHorizon) != null ? `ready ${pct(f.ready ?? f.predictedAtHorizon)}` : f.label}
                          </Faint>
                          <Faint style={{ fontFamily: FONT_MONO, fontSize: 11, whiteSpace: "nowrap" }}>
                            {f.attemptsToCertify == null
                              ? "needs items"
                              : f.attemptsToCertify > 0
                                ? `≈${f.attemptsToCertify} att.`
                                : actionOf(f.label)}
                          </Faint>
                        </div>
                      ))}
                      {atRisk.length > 8 ? <Faint style={{ fontSize: 11 }}>… and {atRisk.length - 8} more</Faint> : null}
                    </>
                  )}
                </div>
              ) : null}
            </div>
          ) : null}

          {/* actions */}
          <div style={{ marginTop: 14, display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button
              type="button"
              onClick={onPracticeAtRisk}
              title="goal items are floored in your normal queue — practicing now covers them"
              style={btnStyle(COLOR.amber)}
            >
              practice at-risk facets ↵
            </button>
            {showExamButton ? (
              <button type="button" onClick={() => onTakeExam?.(goal.id)} style={btnStyle(COLOR.cyan)}>
                take practice exam
              </button>
            ) : null}
            <span style={{ flex: 1 }} />
            <span onClick={onNewGoal} style={{ fontSize: 12, color: COLOR.textFaint, cursor: "pointer", alignSelf: "center", fontFamily: FONT_MONO }}>
              + new goal
            </span>
          </div>
        </div>

        {/* right: trajectory chart */}
        <div style={{ flex: "0 0 auto", minWidth: 260 }}>
          <div style={{ fontSize: 10, color: COLOR.textFaint, letterSpacing: "0.14em", textTransform: "uppercase", fontFamily: FONT_MONO, marginBottom: 4 }}>
            trajectory · demonstrated + ready lanes
          </div>
          {seriesError ? (
            <Faint style={{ color: COLOR.red, fontSize: 11 }}>{seriesError}</Faint>
          ) : seriesLoading || series == null ? (
            <div style={{ fontSize: 11, color: COLOR.textFaint, fontFamily: FONT_MONO, padding: "8px 0" }}>loading trajectory…</div>
          ) : (
            <GoalTrajectoryChart series={series} dueAt={goal.dueAt} targetRecall={goal.targetRecall} />
          )}
        </div>
      </div>
    </div>
  );
}

function btnStyle(color: string) {
  return {
    padding: "6px 14px",
    border: `1px solid ${color}`,
    background: "transparent",
    color,
    fontFamily: FONT_MONO,
    fontSize: 12,
    fontWeight: 600,
    cursor: "pointer",
    whiteSpace: "nowrap" as const
  };
}
