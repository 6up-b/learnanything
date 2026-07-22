// Golden-path run surface (spec_p2 §4; spec_tauri_ui §3 P2 "Golden-path run" row).
//
// Body-pre-emption screen (exam/calibration precedent). Renders the server-side
// run state machine: the stage strip is the ✓ → ◐ → · checkpoint ladder; each
// stage answers the four §9 questions (why-now / teaching-practice-diagnosis-
// assessment / what-can-update / how-much-remains). Reuses PracticeScreen/
// FeedbackScreen idioms via the shared golden-path primitives. Cold-assessment
// burn state is surfaced from the DTO eligibility/burn-reason fields. Milestone +
// suggest_next depth invitation is accept/decline — never auto-anything (U-018).
//
// Offline render (spec_tauri_ui §5.3): with runId omitted the whole surface
// renders from src/fixtures/goldenpath (no live jobs, no AI).

import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type {
  AssessOpenDto,
  AssessResultDto,
  CommandError,
  DepthInvitationResultDto,
  LadderAdvanceResultDto,
  LadderPolicyDto,
  LadderStatusDto,
  PoolDto,
  PoolForRunDto,
  PoolNextSurfaceDto,
  RestoreDto,
  ServedSurfaceDto,
  RunStateDto,
  TriageResultDto,
  TriageStatusDto,
} from "../api/dto";
import { COLOR, Card, Dim, Faint, FONT_MONO, KeyBar, Meta, Pill, SectionHeader, TermSelect } from "../components/term";
import {
  AffectTap,
  CalibrationBadge,
  CheckpointLadder,
  ClaimBadge,
  DepthEnvelopeCard,
  IntervalBar,
  PrimaryButton,
  SecondaryButton,
  BoundaryView,
  type Checkpoint,
} from "../components/goldenpath/shared";
import { TriageDecisionAid } from "../components/goldenpath/TriageDecisionAid";
import { goldenPathFixtures } from "../fixtures/goldenpath";

// Canonical display order for the run-state checkpoint ladder (§4 launch states).
const RUN_STAGES: Array<{ key: string; label: string }> = [
  { key: "ready", label: "ready" },
  { key: "measuring", label: "baseline" },
  { key: "triaging", label: "triage" },
  { key: "instructing", label: "instruct" },
  { key: "practicing", label: "practice" },
  { key: "ready_to_assess", label: "ready-to-assess" },
  { key: "assessing", label: "assess" },
  { key: "restoring", label: "restore" },
  { key: "complete", label: "complete" },
];

function runCheckpoints(run: RunStateDto): Checkpoint[] {
  const visited = new Set<string>(run.history.map((h) => h.toState));
  const currentIdx = RUN_STAGES.findIndex((s) => s.key === run.currentState);
  return RUN_STAGES.map((s, i) => {
    let state: Checkpoint["state"] = "pending";
    if (s.key === run.currentState) state = "current";
    else if (currentIdx >= 0 && i < currentIdx) state = "done";
    else if (visited.has(s.key)) state = "done";
    return { key: s.key, label: s.label, state };
  });
}

/** §7.3 served-surface freshness flag: glyph + label + color. A `fresh` surface
 * earns full evidence; a `reducedEvidence` (familiar/uncertain) surface is visibly
 * consolidation-only and never reported as fresh. */
function ServedFreshness({ surface }: { surface: ServedSurfaceDto }) {
  if (surface.fresh) {
    return <Pill color="green">✦ fresh · {surface.exposureStatus}</Pill>;
  }
  return <Pill color="amber">◐ reduced-evidence · {surface.exposureStatus}</Pill>;
}

// Run states where the pattern-ladder workspace drives the transition (§7.1).
const INSTRUCTION_STATES = new Set(["instructing", "completing", "practicing", "integrating"]);

interface RunBundle {
  run: RunStateDto;
  ladder: LadderPolicyDto | null;
  triage: TriageResultDto | null;
  assess: AssessResultDto | null;
  restore: RestoreDto | null;
  depth: DepthInvitationResultDto | null;
  pool: PoolDto | null;
  nextSurface: PoolNextSurfaceDto | null;
  // Live-run administration state (null offline / when unavailable).
  triageStatus: TriageStatusDto | null;
  ladderStatus: LadderStatusDto | null;
  poolForRun: PoolForRunDto | null;
}

function fixtureBundle(): RunBundle {
  return {
    run: goldenPathFixtures.runStatusAssessed,
    ladder: goldenPathFixtures.ladderPolicy,
    triage: goldenPathFixtures.triageProvisional,
    assess: goldenPathFixtures.assessResult,
    restore: goldenPathFixtures.restore,
    depth: goldenPathFixtures.depthInvitation,
    pool: goldenPathFixtures.poolAssembled,
    nextSurface: goldenPathFixtures.poolNextSurface,
    triageStatus: null,
    ladderStatus: null,
    poolForRun: null,
  };
}

export function GoldenPathScreen({
  runId,
  onExit,
  onError,
  onWhy,
  onOpenConfirm,
}: {
  // Omit / null → offline fixture render (per-screen render acceptance).
  runId?: string | null;
  onExit: () => void;
  onError: (message: string) => void;
  onWhy?: (triage: TriageResultDto) => void;
  onOpenConfirm?: () => void;
}) {
  const offline = !runId;
  const [bundle, setBundle] = useState<RunBundle | null>(offline ? fixtureBundle() : null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    if (!runId) {
      setBundle(fixtureBundle());
      return;
    }
    try {
      const run = await api.goldenPathRunStatus(runId);
      // Optional surfaces — available only at the relevant states; ignore misses.
      const [ladder, assess, restore, depth, triageStatus, ladderStatus, poolForRun] = await Promise.all([
        api.ladderPolicy().catch(() => null),
        api.goldenPathAssessResult(runId).catch(() => null),
        api.goldenPathRestore(runId).catch(() => null),
        api.goldenPathDepthInvitation(runId).catch(() => null),
        api.diagnosticTriageStatus(runId).catch(() => null),
        api.ladderStatus(runId).catch(() => null),
        api.practicePoolForRun(runId).catch(() => null),
      ]);
      setBundle({
        run,
        ladder,
        triage: null,
        assess,
        restore,
        depth,
        pool: null,
        nextSurface: null,
        triageStatus,
        ladderStatus,
        poolForRun,
      });
    } catch (error) {
      onError((error as CommandError).message);
    }
  }, [runId, onError]);

  useEffect(() => {
    void load();
  }, [load]);

  const advance = useCallback(async () => {
    if (!runId || !bundle) return;
    // Triage / ladder own their transitions — Enter must not blind-advance past them.
    if (bundle.run.currentState === "triaging" || INSTRUCTION_STATES.has(bundle.run.currentState)) return;
    const next = bundle.run.nextAction;
    if (!next.toState || next.terminal) return;
    setBusy(true);
    try {
      await api.goldenPathAdvance({
        runId,
        toState: next.toState,
        reason: next.reason,
        idempotencyKey: `advance:${bundle.run.headSeq}:${next.toState}`,
        expectedHeadEventId: bundle.run.headEventId,
      });
      await load();
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  }, [runId, bundle, load, onError]);

  const acceptEdge = useCallback(async () => {
    if (!runId) return;
    setBusy(true);
    try {
      await api.goldenPathAcceptEdge(runId);
      await load();
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  }, [runId, load, onError]);

  const declineEdge = useCallback(async () => {
    if (!runId) return;
    setBusy(true);
    try {
      await api.goldenPathDeclineEdge(runId);
      await load();
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  }, [runId, load, onError]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement | null)?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea") return;
      if (e.key === "Escape") onExit();
      if (e.key === "Enter" && !offline && !busy) void advance();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onExit, advance, offline, busy]);

  const checkpoints = useMemo(() => (bundle ? runCheckpoints(bundle.run) : []), [bundle]);

  if (!bundle) {
    return (
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: FONT_MONO, color: COLOR.textDim }}>
        loading run…
      </div>
    );
  }

  const { run, ladder, triage, assess, restore, depth, pool, nextSurface, triageStatus, ladderStatus, poolForRun } = bundle;
  const invitation = depth?.invitation ?? restore?.invitation ?? null;
  // In triaging / instruction states the workspace below drives the transition —
  // a blind advance there would skip the administration the state exists for.
  const workspaceOwnsTransition =
    !offline && (run.currentState === "triaging" || INSTRUCTION_STATES.has(run.currentState));
  const committedReason = triageStatus?.latest?.selectedReason ?? null;
  const currentRung = ladderStatus?.currentStage ?? null;

  return (
    <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
      {/* hero */}
      <div style={{ flexShrink: 0, borderBottom: `1px solid ${COLOR.border}`, padding: "22px 32px", display: "flex", flexDirection: "column", gap: 10 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
          <span style={{ fontFamily: FONT_MONO, fontSize: 11, letterSpacing: "0.18em", color: COLOR.textFaint }}>
            GOLDEN PATH · RUN
          </span>
          <Meta>{run.runId}</Meta>
          <Pill color={run.mode === "certifying" ? "green" : "slate"}>{run.mode}</Pill>
          {run.milestone ? <Pill color="amber">{run.milestone}</Pill> : null}
          {offline ? <Pill color="cyan">offline · fixture</Pill> : null}
          {offline && onOpenConfirm ? (
            <span style={{ marginLeft: "auto" }}>
              <SecondaryButton onClick={onOpenConfirm}>preview confirmation →</SecondaryButton>
            </span>
          ) : null}
        </div>
        <span style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.textDim }}>
          the P2 §4 run state machine — narrow, transparent, one edge per decision.
        </span>
        <CheckpointLadder steps={checkpoints} />
      </div>

      {/* scroll body */}
      <div className="ll-scroll" style={{ flex: 1, overflowY: "auto", padding: "18px 32px", display: "flex", flexDirection: "column", gap: 8 }}>
        {/* current stage — answers the four §9 questions */}
        <SectionHeader style={{ marginTop: 0 }}>Current Stage — {run.currentState}</SectionHeader>
        <Card status="running" style={{ background: COLOR.washCyan, display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.cyan }}>{run.nextAction.reason}</div>
          <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.textDim, lineHeight: 1.7 }}>
            <div>
              <Faint>why now</Faint> {run.nextAction.reason}
            </div>
            <div>
              <Faint>what can update</Faint> the run projection; posteriors only from cold observations
            </div>
            <div>
              <Faint>how much remains</Faint> {run.nextAction.terminal ? "terminal — nothing further" : `→ ${run.nextAction.toState}`}
            </div>
            <div>
              <Faint>events</Faint> {run.eventCount} <Faint>· head-seq</Faint> {run.headSeq}
            </div>
          </div>
          {!offline && run.nextAction.toState && !run.nextAction.terminal && !workspaceOwnsTransition ? (
            <div>
              <PrimaryButton onClick={advance} disabled={busy}>
                advance → {run.nextAction.toState} ↵
              </PrimaryButton>
            </div>
          ) : null}
          {workspaceOwnsTransition ? (
            <Faint style={{ fontSize: 11 }}>
              this stage advances through the {run.currentState === "triaging" ? "triage" : "ladder"} workspace below —
              no blind state jump.
            </Faint>
          ) : null}
        </Card>

        {/* pattern ladder strip */}
        {ladder ? (
          <>
            <SectionHeader>Pattern Ladder</SectionHeader>
            <Card style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <Faint style={{ fontSize: 11 }}>
                nearest-useful rung, not always the bottom — no rung mints unassisted certification.
              </Faint>
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {[...ladder.stages]
                  .sort((a, b) => a.ordinal - b.ordinal || a.stageKey.localeCompare(b.stageKey))
                  .map((s) => {
                    const isCurrent = currentRung === s.stageKey;
                    return (
                      <div key={s.id} style={{ display: "flex", alignItems: "baseline", gap: 10, fontFamily: FONT_MONO, fontSize: 12, flexWrap: "wrap" }}>
                        <span style={{ color: isCurrent ? COLOR.amber : COLOR.textFaint, width: 18 }}>
                          {isCurrent ? "▶" : s.ordinal}
                        </span>
                        <span style={{ color: isCurrent ? COLOR.amber : COLOR.text, minWidth: 200, fontWeight: isCurrent ? 700 : 400 }}>
                          {s.stageKey}
                        </span>
                        <Pill color={s.purpose === "practice" ? "green" : "cyan"}>{s.purpose}</Pill>
                        {s.requiresCold ? <Pill color="pink">cold</Pill> : null}
                        {s.recordsScaffold ? <Pill color="amber">records scaffold</Pill> : null}
                        {isCurrent ? <Pill color="amber">you are here</Pill> : null}
                        <Dim style={{ fontSize: 11 }}>{s.exitCriteria}</Dim>
                      </div>
                    );
                  })}
              </div>
            </Card>
          </>
        ) : null}

        {/* interactive ladder workspace — enter at the routed rung, log outcomes,
            climb to ready_to_assess (§7.1/§7.2). */}
        {!offline && runId && (INSTRUCTION_STATES.has(run.currentState) || currentRung) && run.currentState !== "complete" ? (
          <LadderWorkspace
            runId={runId}
            currentRung={currentRung}
            committedReason={committedReason}
            runState={run.currentState}
            busy={busy}
            onError={onError}
            onChanged={() => void load()}
          />
        ) : null}

        {/* interactive rotating-practice workspace — seed from anchors, owner
            admission, review, serve (§7.3, U-028). Live runs only. */}
        {!offline && runId ? (
          <PoolWorkspace runId={runId} poolForRun={poolForRun} onError={onError} onChanged={() => void load()} />
        ) : null}

        {/* rotating practice pool + owner admission (§7.3, U-028) — offline fixture render */}
        {pool ? (
          <>
            <SectionHeader>Rotating Practice</SectionHeader>
            <Card style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
                <Meta>{pool.poolSlug}</Meta>
                <Pill color={pool.status === "reviewed" ? "green" : "amber"}>{pool.status}</Pill>
                <Faint>current + one spare at most — card-level scheduling, never per-surface</Faint>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {pool.surfaces.map((s) => (
                  <div key={s.surfaceSlug} style={{ display: "flex", alignItems: "center", gap: 10, fontFamily: FONT_MONO, fontSize: 12, flexWrap: "wrap" }}>
                    <span style={{ color: COLOR.text, minWidth: 180 }}>{s.surfaceSlug}</span>
                    <Pill color="cyan">{s.angle}</Pill>
                    <Faint>{s.provenance}</Faint>
                    <Pill color={s.admissionStatus === "admitted" ? "green" : s.admissionStatus === "rejected" ? "red" : "slate"}>
                      {s.admissionStatus === "candidate" ? "awaiting owner review" : s.admissionStatus}
                    </Pill>
                  </div>
                ))}
              </div>
              {nextSurface?.current ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 4, borderTop: `1px solid ${COLOR.border}`, paddingTop: 8 }}>
                  <Faint style={{ fontSize: 11 }}>served now — §7.3 freshness (familiar practice is never reported fresh)</Faint>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, fontFamily: FONT_MONO, fontSize: 12, flexWrap: "wrap" }}>
                    <span style={{ color: COLOR.text, minWidth: 180 }}>{nextSurface.current.surfaceSlug}</span>
                    <Pill color="cyan">{nextSurface.current.angle}</Pill>
                    <ServedFreshness surface={nextSurface.current} />
                    {nextSurface.rotated ? <Pill color="amber">↻ rotated</Pill> : null}
                    {nextSurface.fallback ? <Pill color="slate">fallback</Pill> : null}
                  </div>
                </div>
              ) : null}
              <Faint style={{ fontSize: 11 }}>
                U-028: LLM drafts within admitted-card bounds; nothing serves until owner-reviewed. No freshness claim when
                the ledger is uncertain.
              </Faint>
            </Card>
          </>
        ) : null}

        {/* triage decision aid (offline fixture render) */}
        {triage ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <TriageDecisionAid triage={triage} />
            {onWhy ? (
              <div>
                <SecondaryButton onClick={() => onWhy(triage)}>❯ why this diagnosis</SecondaryButton>
              </div>
            ) : null}
          </div>
        ) : null}

        {/* interactive triage workspace — report the attempt, get the two-tier
            route, commit a reason when tier two (§6.1). Live runs only. */}
        {!offline && runId ? (
          <TriageWorkspace
            runId={runId}
            runState={run.currentState}
            triageStatus={triageStatus}
            onWhy={onWhy}
            onError={onError}
            onChanged={() => void load()}
          />
        ) : null}

        {/* cold assessment workspace — open, answer, self-grade, submit (§8.2) */}
        {!offline && runId && !assess && (run.currentState === "ready_to_assess" || run.currentState === "assessing") ? (
          <AssessmentWorkspace runId={runId} onSubmitted={() => void load()} onError={onError} />
        ) : null}

        {/* cold assessment — burn state visibility (§8) */}
        {assess ? (
          <>
            <SectionHeader>Cold Assessment</SectionHeader>
            <Card status={assess.passed ? "done" : "error"} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                <span style={{ fontFamily: FONT_MONO, fontSize: 13, color: assess.passed ? COLOR.green : COLOR.red }}>
                  {assess.passed ? "✓ passed" : "✕ not passed"}
                </span>
                <ClaimBadge claim={assess.claimLanguage} />
                <CalibrationBadge status={assess.calibrationStatus} />
                <Faint>cites target v{assess.citedVersion}</Faint>
              </div>
              <IntervalBar interval={assess.interval} />
              <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.textDim, lineHeight: 1.7 }}>
                <div>
                  <Faint>surface eligibility</Faint>{" "}
                  <span style={{ color: assess.surfaceEligibility === "consumed" ? COLOR.red : COLOR.textDim }}>
                    {assess.surfaceEligibility}
                  </span>{" "}
                  <Faint>· burn</Faint> {assess.burnReason}
                  {assess.eligibilityReason ? <Faint> · {assess.eligibilityReason}</Faint> : null}
                </div>
                <div>
                  <Faint>review state</Faint>{" "}
                  {assess.reviewState.quarantined ? <Pill color="red">quarantined</Pill> : null}
                  {assess.reviewState.reviewFlag ? <Pill color="amber">review</Pill> : null}
                  {!assess.reviewState.quarantined && !assess.reviewState.reviewFlag ? (
                    <span style={{ color: COLOR.green }}>clean</span>
                  ) : null}
                </div>
                <div>
                  <Faint>coverage</Faint>{" "}
                  {assess.coverage.map((c) => `${c.facet}×${c.capability}`).join(", ")}
                </div>
              </div>
            </Card>
          </>
        ) : null}

        {/* restoration + boundary diff (§8.4) */}
        {restore ? (
          <>
            <SectionHeader>Restoration &amp; Boundary Diff</SectionHeader>
            <Card style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
                <Pill color="green">milestone {restore.milestoneRecorded ? "recorded" : "pending"}</Pill>
                <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.amber }}>{restore.achievedMilestone}</span>
              </div>
              <BoundaryView cells={restore.boundaryDiff.cells} passed={restore.boundaryDiff.passed} />
              <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.textDim }}>
                <Faint>exemplar comparison</Faint>{" "}
                {restore.exemplarComparison
                  .map((e) => `${e.exemplarRef}${e.heldOut ? " (held-out)" : ""}`)
                  .join(", ")}
              </div>
            </Card>
          </>
        ) : null}

        {/* milestone + suggest_next depth invitation (§7.5, U-018 — never auto) */}
        {invitation ? (
          <>
            <SectionHeader>Depth Invitation</SectionHeader>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <Faint style={{ fontSize: 11 }}>
                served as {invitation.servedAs} — this never fires on its own (U-018). One edge per decision.
              </Faint>
              <DepthEnvelopeCard
                preset="master_tasks_like_these"
                edge={invitation.edge}
                policyRecommendation={invitation.servedAs}
              />
              {!offline ? (
                <div style={{ display: "flex", gap: 8 }}>
                  <PrimaryButton onClick={acceptEdge} disabled={busy}>
                    accept — develop this edge ↵
                  </PrimaryButton>
                  <SecondaryButton onClick={declineEdge} disabled={busy}>
                    decline
                  </SecondaryButton>
                </div>
              ) : (
                <Faint style={{ fontSize: 11 }}>offline — accept/decline disabled</Faint>
              )}
            </div>
          </>
        ) : null}

        <div style={{ marginTop: 8 }}>
          <AffectTap />
        </div>
      </div>

      <KeyBar
        keys={[
          ...(offline ? [] : [{ key: "↵", label: "advance stage" }]),
          { key: "esc", label: "exit run" },
        ]}
        right={{ key: "^p", label: "palette" }}
      />
    </div>
  );
}

// ── AssessmentWorkspace — open the cold administration, answer, self-grade,
// submit (§8.2). The expected answer is fetched only AFTER the learner locks
// their answer, so the cold observation is never contaminated pre-response. ──
function AssessmentWorkspace({
  runId,
  onSubmitted,
  onError,
}: {
  runId: string;
  onSubmitted: () => void;
  onError: (message: string) => void;
}) {
  const [opened, setOpened] = useState<AssessOpenDto | null>(null);
  const [answer, setAnswer] = useState("");
  const [locked, setLocked] = useState(false);
  const [expected, setExpected] = useState<string | null>(null);
  const [score, setScore] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);

  const openAssessment = async () => {
    setBusy(true);
    try {
      setOpened(await api.goldenPathAssessOpen(runId));
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  };

  const lockAnswer = async () => {
    if (!opened?.practiceItemId || !answer.trim()) return;
    setLocked(true);
    try {
      const item = await api.getPracticeItem(opened.practiceItemId);
      setExpected(typeof item.expectedAnswer === "string" ? item.expectedAnswer : JSON.stringify(item.expectedAnswer));
    } catch {
      setExpected(null);
    }
  };

  const submit = async () => {
    if (!opened || score === null) return;
    setBusy(true);
    try {
      await api.goldenPathAssessSubmit({
        runId,
        administrationId: opened.administrationId,
        surfaceId: opened.surfaceId,
        rubricScore: score,
        maxPoints: opened.maxPoints ?? 4,
        attemptId: `assess-${runId}-${opened.administrationId}`,
        responseText: answer,
      });
      onSubmitted();
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  };

  const maxPoints = opened?.maxPoints ?? 4;
  return (
    <>
      <SectionHeader>Cold Assessment — take it</SectionHeader>
      <Card status="probe" style={{ background: COLOR.washPurple, display: "flex", flexDirection: "column", gap: 8 }}>
        {!opened ? (
          <>
            <Faint style={{ fontSize: 12, lineHeight: 1.6 }}>
              opening administers the reserved unseen sibling — it burns on submission and can never be reused as a fresh
              assessment. Answer cold: no notes, no hints.
            </Faint>
            <div>
              <PrimaryButton onClick={() => void openAssessment()} disabled={busy}>
                open cold assessment ↵
              </PrimaryButton>
            </div>
          </>
        ) : (
          <>
            <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <Meta>{opened.administrationId}</Meta>
              {opened.consumesUnseen ? <Pill color="pink">consumes unseen</Pill> : null}
            </div>
            <div style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.text, lineHeight: 1.7 }}>
              {opened.prompt ?? "(no prompt available for this surface)"}
            </div>
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              disabled={locked}
              placeholder="your answer — cold, in your own words…"
              style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: 8, minHeight: 90, resize: "vertical" }}
            />
            {!locked ? (
              <div>
                <PrimaryButton onClick={() => void lockAnswer()} disabled={busy || !answer.trim()}>
                  lock answer &amp; reveal ↵
                </PrimaryButton>
              </div>
            ) : (
              <>
                <div style={{ borderTop: `1px solid ${COLOR.border}`, paddingTop: 8, display: "flex", flexDirection: "column", gap: 6 }}>
                  <Faint style={{ fontSize: 11 }}>expected answer</Faint>
                  <div style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.textDim, lineHeight: 1.6 }}>
                    {expected ?? "(unavailable)"}
                  </div>
                </div>
                <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
                  <Faint style={{ fontSize: 11 }}>self-grade</Faint>
                  {Array.from({ length: maxPoints + 1 }, (_, i) => (
                    <SecondaryButton key={i} onClick={() => setScore(i)} active={score === i}>
                      {i}
                    </SecondaryButton>
                  ))}
                  <Faint style={{ fontSize: 11 }}>/ {maxPoints}</Faint>
                </div>
                <div>
                  <PrimaryButton onClick={() => void submit()} disabled={busy || score === null}>
                    submit — burn the surface ↵
                  </PrimaryButton>
                </div>
              </>
            )}
          </>
        )}
      </Card>
    </>
  );
}

// ── TriageWorkspace — report the attempt honestly, get the two-tier route,
// commit a reason when tier two (§6.1). Tier one auto-routes the run; tier two
// never applies anything without the learner's confirmation. ──
const TRIAGE_COARSE_OPTIONS = [
  { value: "wrong", label: "I answered wrong" },
  { value: "dont_know", label: "I didn't know / left it blank" },
  { value: "correct", label: "correct, but it felt shaky" },
];
const TRIAGE_SIGNATURE_OPTIONS = [
  { value: "", label: "no clear signature" },
  { value: "wrong_method", label: "picked the wrong method" },
  { value: "execution_error", label: "slipped executing the steps" },
  { value: "schema_gap", label: "concept / schema gap" },
  { value: "misconception", label: "believed something false" },
  { value: "integration_gap", label: "couldn't combine the pieces" },
  { value: "task_misread", label: "misread the task" },
];
const TRIAGE_EXPOSURE_OPTIONS = [
  { value: "exposed", label: "I've studied this before" },
  { value: "never_exposed", label: "never saw this content" },
];
const TRIAGE_TRACE_OPTIONS = [
  { value: "intact", label: "reviewed it recently" },
  { value: "expired", label: "long time since last review" },
];
const TRIAGE_CONFIDENCE_OPTIONS = [
  { value: "0.9", label: "confident in this read" },
  { value: "0.7", label: "somewhat sure" },
  { value: "0.4", label: "just guessing" },
];

// Reason strings must reach the sidecar snake_case; the distribution fallback in
// the decision aid can surface camelized keys, so normalize before committing.
function snakeReason(reason: string): string {
  return reason.replace(/[A-Z]/g, (m) => `_${m.toLowerCase()}`);
}

function TriageWorkspace({
  runId,
  runState,
  triageStatus,
  onWhy,
  onError,
  onChanged,
}: {
  runId: string;
  runState: string;
  triageStatus: TriageStatusDto | null;
  onWhy?: (triage: TriageResultDto) => void;
  onError: (message: string) => void;
  onChanged: () => void;
}) {
  const [result, setResult] = useState<TriageResultDto | null>(null);
  const [coarse, setCoarse] = useState("wrong");
  const [signature, setSignature] = useState("");
  const [exposure, setExposure] = useState("exposed");
  const [memoryTrace, setMemoryTrace] = useState("intact");
  const [confidence, setConfidence] = useState("0.9");
  const [busy, setBusy] = useState(false);

  const committed = triageStatus?.latest ?? null;

  const runTriage = async () => {
    setBusy(true);
    try {
      const res = await api.diagnosticTriage({
        runId,
        attempt: {
          attempt_id: `ui-triage-${runId}-${Date.now()}`,
          coarse_class: coarse,
          error_signature: signature || null,
          grader_confidence: Number(confidence),
          exposure_history: exposure,
          memory_trace: memoryTrace,
        },
      });
      setResult(res);
      onChanged();
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  };

  const commitReason = async (reason: string) => {
    if (!result) return;
    setBusy(true);
    try {
      const res = await api.diagnosticTriageDecide({
        runId,
        triageEventId: result.eventId,
        chosenReason: snakeReason(reason),
      });
      setResult(res);
      onChanged();
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  };

  if (result) {
    const needsDecision = result.tier === "two" && !result.autoCommitted && !result.routed;
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        <TriageDecisionAid triage={result} onOverride={needsDecision && !busy ? commitReason : undefined} />
        {onWhy ? (
          <div>
            <SecondaryButton onClick={() => onWhy(result)}>❯ why this diagnosis</SecondaryButton>
          </div>
        ) : null}
        {result.routed && result.routedTo ? (
          <Faint style={{ fontSize: 11 }}>routed — the run moved to {result.routedTo}.</Faint>
        ) : null}
      </div>
    );
  }

  if (runState === "triaging") {
    return (
      <>
        <SectionHeader>Failure Triage — report the attempt</SectionHeader>
        <Card status="probe" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <Faint style={{ fontSize: 12, lineHeight: 1.6 }}>
            describe what actually happened on the baseline attempt. decisive evidence routes automatically (tier one);
            anything ambiguous comes back as a decision aid you confirm (tier two).
          </Faint>
          <div style={{ display: "flex", gap: 18, flexWrap: "wrap" }}>
            <div>
              <Faint style={{ fontSize: 11 }}>what happened</Faint>
              <TermSelect value={coarse} options={TRIAGE_COARSE_OPTIONS} onChange={setCoarse} width={230} />
            </div>
            <div>
              <Faint style={{ fontSize: 11 }}>how it went wrong</Faint>
              <TermSelect value={signature} options={TRIAGE_SIGNATURE_OPTIONS} onChange={setSignature} width={240} />
            </div>
          </div>
          <div style={{ display: "flex", gap: 18, flexWrap: "wrap" }}>
            <div>
              <Faint style={{ fontSize: 11 }}>exposure</Faint>
              <TermSelect value={exposure} options={TRIAGE_EXPOSURE_OPTIONS} onChange={setExposure} width={230} />
            </div>
            <div>
              <Faint style={{ fontSize: 11 }}>memory trace</Faint>
              <TermSelect value={memoryTrace} options={TRIAGE_TRACE_OPTIONS} onChange={setMemoryTrace} width={240} />
            </div>
            <div>
              <Faint style={{ fontSize: 11 }}>how sure are you</Faint>
              <TermSelect value={confidence} options={TRIAGE_CONFIDENCE_OPTIONS} onChange={setConfidence} width={200} />
            </div>
          </div>
          <div>
            <PrimaryButton onClick={() => void runTriage()} disabled={busy}>
              triage this attempt →
            </PrimaryButton>
          </div>
        </Card>
      </>
    );
  }

  if (committed?.selectedReason) {
    return (
      <>
        <SectionHeader>Failure Triage — committed</SectionHeader>
        <Card style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
          <Pill color={committed.tier === "one" ? "amber" : "pink"}>tier {committed.tier}</Pill>
          <span style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.amber }}>
            {snakeReason(committed.selectedReason).replace(/_/g, " ")}
          </span>
          {committed.overrideActor ? <Faint>overridden by {committed.overrideActor}</Faint> : null}
        </Card>
      </>
    );
  }

  return null;
}

// ── LadderWorkspace — enter at the routed rung, do the activity, log the cold
// outcome, climb until the run is ready_to_assess (§7.1/§7.2). The activities
// themselves are practiced through Today; this logs their outcomes against the
// rung so the run advances only on evidence. ──
const SCAFFOLD_OPTIONS = [
  { value: "0", label: "no scaffold used" },
  { value: "0.5", label: "some scaffold" },
  { value: "1", label: "heavy scaffold" },
];

function LadderWorkspace({
  runId,
  currentRung,
  committedReason,
  runState,
  busy: parentBusy,
  onError,
  onChanged,
}: {
  runId: string;
  currentRung: string | null;
  committedReason: string | null;
  runState: string;
  busy: boolean;
  onError: (message: string) => void;
  onChanged: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [scaffold, setScaffold] = useState("0.5");
  const [lastAdvance, setLastAdvance] = useState<LadderAdvanceResultDto | null>(null);

  const enter = async () => {
    setBusy(true);
    try {
      const res = await api.ladderEnter({ runId, reason: committedReason ?? undefined });
      if (!res.stage) {
        onError("No instructional rung applies to this triage reason — resolve the fault/ambiguity first.");
      }
      onChanged();
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  };

  const logOutcome = async (outcome: "pass" | "incorrect" | "gave_up") => {
    if (!currentRung) return;
    setBusy(true);
    try {
      const res = await api.ladderAdvance({
        runId,
        fromStage: currentRung,
        outcome,
        scaffoldUse: Number(scaffold),
        idempotencyKey: `ladder-ui-${runId}-${currentRung}-${Date.now()}`,
      });
      setLastAdvance(res);
      onChanged();
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  };

  const disabled = busy || parentBusy;
  return (
    <>
      <SectionHeader>Ladder Workspace</SectionHeader>
      <Card status="running" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {!currentRung ? (
          <>
            <Faint style={{ fontSize: 12, lineHeight: 1.6 }}>
              {committedReason
                ? `triage committed «${committedReason.replace(/_/g, " ")}» — enter the ladder at its mapped rung.`
                : "no committed triage reason yet — the ladder enters at the rung the triage reason maps to."}
            </Faint>
            <div>
              <PrimaryButton onClick={() => void enter()} disabled={disabled}>
                enter the ladder ↵
              </PrimaryButton>
            </div>
          </>
        ) : (
          <>
            <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
              <Faint style={{ fontSize: 11 }}>current rung</Faint>
              <span style={{ fontFamily: FONT_MONO, fontSize: 13, color: COLOR.amber, fontWeight: 700 }}>
                {currentRung.replace(/_/g, " ")}
              </span>
              <Pill color="slate">{runState}</Pill>
            </div>
            <Faint style={{ fontSize: 12, lineHeight: 1.6 }}>
              do the rung's activity with your materials (anchor practice flows through Today), then log the outcome
              honestly — the run advances only on this evidence. no rung mints certification.
            </Faint>
            <div style={{ display: "flex", gap: 12, alignItems: "flex-end", flexWrap: "wrap" }}>
              <div>
                <Faint style={{ fontSize: 11 }}>scaffold use</Faint>
                <TermSelect value={scaffold} options={SCAFFOLD_OPTIONS} onChange={setScaffold} width={190} />
              </div>
              <PrimaryButton onClick={() => void logOutcome("pass")} disabled={disabled}>
                ✓ passed
              </PrimaryButton>
              <SecondaryButton onClick={() => void logOutcome("incorrect")} disabled={disabled}>
                ✕ failed
              </SecondaryButton>
              <SecondaryButton onClick={() => void logOutcome("gave_up")} disabled={disabled}>
                gave up
              </SecondaryButton>
            </div>
          </>
        )}
        {lastAdvance ? (
          <div style={{ fontFamily: FONT_MONO, fontSize: 12, lineHeight: 1.6 }}>
            {lastAdvance.readyToAssess ? (
              <span style={{ color: COLOR.green }}>
                ✓ ladder complete — the run is ready for the cold assessment.
              </span>
            ) : lastAdvance.needsReview ? (
              <span style={{ color: COLOR.red }}>
                repeated failures on this rung — the run was flagged for review.
              </span>
            ) : (
              <span style={{ color: COLOR.textDim }}>
                climbed to <span style={{ color: COLOR.amber }}>{String(lastAdvance.toStage ?? "").replace(/_/g, " ")}</span>
              </span>
            )}
          </div>
        ) : null}
      </Card>
    </>
  );
}

// ── PoolWorkspace — seed the rotating practice pool from the run blueprint's
// anchor exemplars, owner-admit each surface (U-028, reserve-collision guarded),
// mark reviewed, then serve with §7.3 freshness semantics. ──
function PoolWorkspace({
  runId,
  poolForRun,
  onError,
  onChanged,
}: {
  runId: string;
  poolForRun: PoolForRunDto | null;
  onError: (message: string) => void;
  onChanged: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [next, setNext] = useState<PoolNextSurfaceDto | null>(null);
  const [variantNotice, setVariantNotice] = useState<string | null>(null);

  if (!poolForRun) return null;
  const pool = poolForRun.pool?.pool ?? null;
  const anchorsInVault = poolForRun.anchors.filter((a) => a.inVault);

  // Re-rung an anchor exemplar: mint an easier/harder same-LO sibling. The
  // sibling is a plain practice item (queue + exemplar pool discovery); pool
  // admission stays owner-gated.
  const requestAnchorVariant = async (ref: string, direction: "easier" | "harder") => {
    setBusy(true);
    try {
      const result = await api.requestRungVariant({ practiceItemId: ref, direction });
      setVariantNotice(
        `authoring an ${direction} sibling of ${ref} (${result.sourceWaypoint} → ${result.targetWaypoint}) — it lands in your queue when ready`
      );
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  };

  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    try {
      await fn();
      onChanged();
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  };

  const serve = async () => {
    if (!pool) return;
    setBusy(true);
    try {
      setNext(await api.practicePoolNextSurface(pool.poolId));
    } catch (error) {
      onError((error as CommandError).message);
    } finally {
      setBusy(false);
    }
  };

  const allAdmitted = pool != null && pool.surfaces.length > 0 && pool.surfaces.every((s) => s.admissionStatus === "admitted");
  const servable = pool != null && (pool.status === "reviewed" || pool.status === "active");

  return (
    <>
      <SectionHeader>Rotating Practice</SectionHeader>
      <Card style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {anchorsInVault.length > 0 ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {anchorsInVault.map((anchor) => (
              <div key={anchor.ref} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 11 }}>
                <span style={{ fontFamily: FONT_MONO, color: COLOR.textDim, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {anchor.ref}
                </span>
                <Faint style={{ fontSize: 10 }}>{anchor.angle}</Faint>
                <span style={{ flex: 1 }} />
                <span
                  onClick={busy ? undefined : () => void requestAnchorVariant(anchor.ref, "easier")}
                  title="mint an easier sibling of this exemplar one depth waypoint down (also informs your learner model)"
                  style={{ fontFamily: FONT_MONO, fontSize: 11, color: busy ? COLOR.textFaint : COLOR.amberLink, textDecoration: "underline", textUnderlineOffset: 2, cursor: busy ? "default" : "pointer", whiteSpace: "nowrap" }}
                >
                  ↓ easier
                </span>
                <span
                  onClick={busy ? undefined : () => void requestAnchorVariant(anchor.ref, "harder")}
                  title="mint a harder sibling of this exemplar one depth waypoint up (also informs your learner model)"
                  style={{ fontFamily: FONT_MONO, fontSize: 11, color: busy ? COLOR.textFaint : COLOR.amberLink, textDecoration: "underline", textUnderlineOffset: 2, cursor: busy ? "default" : "pointer", whiteSpace: "nowrap" }}
                >
                  ↑ harder
                </span>
              </div>
            ))}
            {variantNotice ? <Faint style={{ fontSize: 11 }}>◐ {variantNotice}</Faint> : null}
          </div>
        ) : null}
        {!pool ? (
          <>
            <Faint style={{ fontSize: 12, lineHeight: 1.6 }}>
              no practice pool exists for this run's blueprint yet. seeding assembles candidates from your anchor
              exemplars — nothing serves until you admit each surface and mark the pool reviewed (U-028).
            </Faint>
            <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <PrimaryButton onClick={() => void run(() => api.practicePoolSeedForRun(runId))} disabled={busy || anchorsInVault.length === 0}>
                seed pool from {anchorsInVault.length} anchor exemplar{anchorsInVault.length === 1 ? "" : "s"} →
              </PrimaryButton>
              {anchorsInVault.length === 0 ? (
                <Faint style={{ fontSize: 11 }}>no anchor exemplar from the blueprint is present in the vault.</Faint>
              ) : null}
            </div>
          </>
        ) : (
          <>
            <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
              <Meta>{pool.poolSlug}</Meta>
              <Pill color={servable ? "green" : "amber"}>{pool.status}</Pill>
              <Faint>current + one spare at most — card-level scheduling, never per-surface</Faint>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {pool.surfaces.map((s) => {
                const anchor = poolForRun.anchors.find((a) => a.ref === s.surfaceSlug);
                return (
                  <div key={s.surfaceSlug} style={{ display: "flex", alignItems: "center", gap: 10, fontFamily: FONT_MONO, fontSize: 12, flexWrap: "wrap" }}>
                    <span style={{ color: COLOR.text, minWidth: 180 }}>{s.surfaceSlug}</span>
                    <Pill color="cyan">{s.angle}</Pill>
                    <Faint>{s.provenance}</Faint>
                    <Pill color={s.admissionStatus === "admitted" ? "green" : s.admissionStatus === "rejected" ? "red" : "slate"}>
                      {s.admissionStatus === "candidate" ? "awaiting owner review" : s.admissionStatus}
                    </Pill>
                    {s.admissionStatus === "candidate" ? (
                      <SecondaryButton
                        onClick={() =>
                          void run(() =>
                            api.practicePoolAdmitAnchor({ runId, poolId: pool.poolId, surfaceSlug: s.surfaceSlug })
                          )
                        }
                        disabled={busy || (anchor != null && !anchor.inVault)}
                      >
                        admit →
                      </SecondaryButton>
                    ) : null}
                  </div>
                );
              })}
            </div>
            {allAdmitted && !servable ? (
              <div>
                <PrimaryButton onClick={() => void run(() => api.practicePoolReview(pool.poolId))} disabled={busy}>
                  mark pool reviewed ↵
                </PrimaryButton>
              </div>
            ) : null}
            {servable ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 6, borderTop: `1px solid ${COLOR.border}`, paddingTop: 8 }}>
                <div>
                  <SecondaryButton onClick={() => void serve()} disabled={busy}>
                    serve next practice surface ↻
                  </SecondaryButton>
                </div>
                {next?.current ? (
                  <div style={{ display: "flex", alignItems: "center", gap: 10, fontFamily: FONT_MONO, fontSize: 12, flexWrap: "wrap" }}>
                    <span style={{ color: COLOR.text, minWidth: 180 }}>{next.current.surfaceSlug}</span>
                    <Pill color="cyan">{next.current.angle}</Pill>
                    <ServedFreshness surface={next.current} />
                    {next.rotated ? <Pill color="amber">↻ rotated</Pill> : null}
                    {next.fallback ? <Pill color="slate">fallback</Pill> : null}
                  </div>
                ) : null}
                {next?.current ? (
                  <Faint style={{ fontSize: 11 }}>
                    practice the served surface through Today — rotation is card-level, and familiar practice is never
                    reported fresh (§7.3).
                  </Faint>
                ) : null}
              </div>
            ) : null}
            <Faint style={{ fontSize: 11 }}>
              U-028: candidates stay inert until owner-admitted; an assessment-reserved surface is refused at admission.
            </Faint>
          </>
        )}
      </Card>
    </>
  );
}
