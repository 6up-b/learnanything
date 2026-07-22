import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { api } from "../api/client";
import type {
  ClaimCandidateDto,
  DecayPressureDto,
  GoalDto,
  OverconfidentFacetDto,
  PracticeItemDetail,
  QueueSection,
  QueueSnapshot,
  ReentrySummaryDto,
  ScheduledItemDto,
  SchedulerComponents,
  SessionEndSummary,
  SessionSnapshot
} from "../api/dto";
import { EmptyPlaceholder, EntityLink } from "../components/ui";
import { BlockBar, COLOR, Dim, Faint, FONT_MONO, KeyBar, Meta, modePillColor, Pill, SectionHeader } from "../components/term";
import { ClaimSurface, mintVisitId } from "../components/ClaimSurface";
import { GoalBanner } from "../components/GoalBanner";
import { GoalWizard } from "../components/GoalWizard";
import { GoalReviewCard, type ReviewReason } from "../components/GoalReviewCard";
import { FacetEvidenceDrawer } from "../components/KnowledgeModel";
import { QuestionQueuePanel } from "../components/QuestionQueue";
import { WriteCardDialog } from "../components/WriteCardDialog";
import { masteryTone } from "../app/algoConfig";
import { MarkdownMath } from "../render/MarkdownMath";

const HOTKEYS = "123456789abcdef";

function masteryColor(mastery: number): string {
  return masteryTone(mastery, COLOR);
}

export function TodayScreen({
  session,
  gradingReady = true,
  gradingProvider = "codex",
  algorithmVersion,
  onOpenPractice,
  onPaletteEntities,
  onEndSession,
  onInspect,
  onTakeExam,
  noGoalBannerDismissed = false,
  onDismissNoGoalBanner,
  onGotoReader,
  readerSeedingActive = false,
  onError
}: {
  session: SessionSnapshot | null;
  gradingReady?: boolean;
  gradingProvider?: string;
  algorithmVersion: string;
  onOpenPractice: (practiceItemId: string) => void;
  onPaletteEntities?: (ids: { inspectIds: string[]; practiceItemIds: string[] }) => void;
  onEndSession: (summary: SessionEndSummary) => void;
  onInspect: (id: string) => void;
  /** Wired by App.tsx to launch the ExamScreen for a goal; banner hides the exam button when absent. */
  onTakeExam?: (goalId: string) => void;
  noGoalBannerDismissed?: boolean;
  onDismissNoGoalBanner?: () => void;
  /** Jump to the Reader tab (items-off empty state: practice builds from reading). */
  onGotoReader?: () => void;
  /** True when the vault has a study map but zero practice items — the items-off
   * bootstrap state where practice accrues from reading. */
  readerSeedingActive?: boolean;
  onError: (message: string) => void;
}) {
  const [queue, setQueue] = useState<QueueSnapshot | null>(null);
  const [queueLoading, setQueueLoading] = useState(true);
  const [focusedId, setFocusedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<PracticeItemDetail | null>(null);
  const [bannerOpen, setBannerOpen] = useState(true);
  const [ending, setEnding] = useState(false);
  const [goals, setGoals] = useState<GoalDto[] | null>(null);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [writeCardOpen, setWriteCardOpen] = useState(false);
  const [evidenceFacetId, setEvidenceFacetId] = useState<string | null>(null);
  const [dismissedReview, setDismissedReview] = useState<Set<string>>(() => new Set());
  const queueRequestRef = useRef<{ key: string; promise: Promise<QueueSnapshot>; id: number } | null>(null);
  const queueRequestSeqRef = useRef(0);
  const now = useNowMinute();
  // F5/F7 hypothesis surfaces: one visit id per Today visit for schedule_choice
  // claim telemetry (§2.2 — outside a practice session).
  const visitIdRef = useRef<string>(mintVisitId());
  const [overconfidence, setOverconfidence] = useState<OverconfidentFacetDto[]>([]);
  const [reentry, setReentry] = useState<ReentrySummaryDto | null>(null);
  const [decayPressure, setDecayPressure] = useState<DecayPressureDto | null>(null);

  const refreshGoals = useCallback(() => {
    api
      .goalsList()
      .then((snap) => setGoals(snap.goals))
      .catch((error) => onError((error as Error).message));
  }, [onError]);

  useEffect(() => {
    refreshGoals();
  }, [refreshGoals]);

  // Active goals ordered for the banner: nearest due first, ties by higher priority.
  const activeGoals = useMemo(() => {
    const active = (goals ?? []).filter((g) => g.status === "active");
    return active.slice().sort((a, b) => {
      const da = a.dueAt ? Date.parse(a.dueAt) : Infinity;
      const db = b.dueAt ? Date.parse(b.dueAt) : Infinity;
      if (da !== db) return da - db;
      return b.priority - a.priority;
    });
  }, [goals]);

  // First active goal that needs a weekly-review decision (and isn't session-dismissed).
  const reviewCandidate = useMemo((): { goal: GoalDto; reason: ReviewReason } | null => {
    for (const goal of activeGoals) {
      if (dismissedReview.has(goal.id)) continue;
      const duePassed = goal.dueAt != null && !Number.isNaN(Date.parse(goal.dueAt)) && Date.parse(goal.dueAt) < Date.now();
      const stale = Date.now() - Date.parse(goal.updatedAt) > 7 * 86_400_000;
      const frontierClear = goal.report != null && goal.report.atRiskCount === 0 && goal.report.total > 0;
      if (duePassed) return { goal, reason: "due_passed" };
      if (frontierClear) return { goal, reason: "frontier_clear" };
      if (stale) return { goal, reason: "stale" };
    }
    return null;
  }, [activeGoals, dismissedReview]);

  const items = useMemo(() => queue?.sections.flatMap((section) => section.items) ?? [], [queue]);
  const flatIds = useMemo(() => items.map((item) => item.practiceItemId), [items]);
  const focusedItem = useMemo(
    () => items.find((item) => item.practiceItemId === focusedId) ?? items[0] ?? null,
    [items, focusedId]
  );
  const followup = useMemo(() => items.find((item) => item.isFollowup) ?? null, [items]);

  const dueCount = useMemo(
    () => items.filter((item) => !item.isProbe && /due|overdue|now|followup/i.test(item.dueStatus ?? "")).length,
    [items]
  );
  const probeCount = useMemo(() => items.filter((item) => item.isProbe).length, [items]);
  const laterCount = useMemo(() => items.filter((item) => /later/i.test(item.dueStatus ?? "")).length, [items]);

  // KM3b §9.6 session narrative: the primary active goal's next-gap bottleneck
  // (deterministic; from the KM3a blueprint readiness projection, no LLM).
  const [nextGap, setNextGap] = useState<string | null>(null);
  const primaryGoalId = activeGoals[0]?.id ?? null;
  useEffect(() => {
    if (!primaryGoalId) { setNextGap(null); return; }
    let alive = true;
    api
      .getGoalReport(primaryGoalId)
      .then((snap) => {
        if (!alive) return;
        const readiness = snap.report.blueprintReadiness ?? {};
        let worst: { facet: string; predicted: number } | null = null;
        for (const lo of Object.values(readiness)) {
          const b = lo.bottleneck;
          if (b && (!worst || b.predictedRecall < worst.predicted)) {
            worst = { facet: b.facet, predicted: b.predictedRecall };
          }
        }
        setNextGap(worst ? worst.facet.replace(/^facet_/, "") : null);
      })
      .catch(() => { if (alive) setNextGap(null); });
    return () => { alive = false; };
  }, [primaryGoalId]);

  // F5 overconfidence list + F7 welcome-back diff, both anchored on the primary
  // active goal (§4.3, §4.4). Refetched when the goal or queue changes.
  const hasActiveGoal = activeGoals.length > 0;
  useEffect(() => {
    if (!primaryGoalId) {
      setOverconfidence([]);
      setReentry(null);
      return;
    }
    let alive = true;
    api
      .getOverconfidenceList(primaryGoalId)
      .then((snap) => { if (alive) setOverconfidence(snap.facets); })
      .catch(() => { if (alive) setOverconfidence([]); });
    api
      .getReentrySummary(primaryGoalId)
      .then((snap) => { if (alive) setReentry(snap.summary.show ? snap.summary : null); })
      .catch(() => { if (alive) setReentry(null); });
    return () => { alive = false; };
  }, [primaryGoalId, queue?.totalItems]);

  // F7 no-goal / fresh-vault fallback (§4.5): decay pressure fills the hero slot
  // only when there is no active goal.
  useEffect(() => {
    if (hasActiveGoal) { setDecayPressure(null); return; }
    if (goals == null) return;
    let alive = true;
    api
      .getDecayPressure(null)
      .then((snap) => { if (alive) setDecayPressure(snap.pressure); })
      .catch(() => { if (alive) setDecayPressure(null); });
    return () => { alive = false; };
  }, [hasActiveGoal, goals]);

  const startOverconfidenceProbe = useCallback(
    (facet: OverconfidentFacetDto) => {
      api
        .startOverconfidenceProbe(facet.learningObjectId, facet.facetId)
        .then(() => refreshQueue({ force: true }))
        .catch((error) => onError((error as Error).message));
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [onError]
  );

  // One deterministic line from the built queue composition (§9.6, §11.2).
  const sessionNarrative = useMemo(() => {
    const followups = items.filter((item) => item.isFollowup).length;
    const reps = Math.max(0, items.length - probeCount - followups);
    if (items.length === 0) return null;
    const parts: string[] = [];
    if (probeCount > 0) parts.push(`${probeCount} diagnostic`);
    if (reps > 0) parts.push(`${reps} retrieval rep${reps === 1 ? "" : "s"}`);
    if (followups > 0) parts.push(`${followups} follow-up${followups === 1 ? "" : "s"}`);
    if (parts.length === 0) return null;
    const gap = nextGap ? ` — next gap: ${nextGap}` : "";
    return `Today: ${parts.join(", ")}${gap}`;
  }, [items, probeCount, nextGap]);

  useEffect(() => {
    void refreshQueue();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session?.sessionId]);

  // Background-applied content (rung variants, reader-driven practice
  // expansion, synthesis) lands via durable batches, not user actions on this
  // screen. Poll the batch list — the RPC itself also triggers the sidecar's
  // vault reload — and refetch the queue when a batch newly completes, so a
  // freshly minted item pops into the queue without re-opening the screen.
  const seenBatchStatusRef = useRef<Map<string, string> | null>(null);
  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      try {
        const { batches } = await api.listIngestBatches(8);
        if (cancelled) return;
        const previous = seenBatchStatusRef.current;
        const next = new Map(batches.map((batch) => [batch.id, batch.status] as const));
        if (previous !== null) {
          const newlyCompleted = batches.some(
            (batch) => batch.status === "completed" && previous.get(batch.id) !== "completed"
          );
          if (newlyCompleted) void refreshQueue({ force: true });
        }
        seenBatchStatusRef.current = next;
      } catch {
        /* transient poll failure — try again next tick */
      }
    };
    void poll();
    const interval = window.setInterval(() => void poll(), 7000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    onPaletteEntities?.({
      inspectIds: unique(items.flatMap((item) => [item.practiceItemId, item.learningObjectId])),
      practiceItemIds: unique(items.map((item) => item.practiceItemId))
    });
  }, [items, onPaletteEntities]);

  useEffect(() => {
    if (!focusedItem) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    api
      .openQueueItem(focusedItem.practiceItemId)
      .then((item) => {
        if (!cancelled) setDetail(item);
      })
      .catch((error) => {
        if (!cancelled) onError(error.message);
      });
    return () => {
      cancelled = true;
    };
  }, [focusedItem?.practiceItemId, onError]);

  const finishSession = useCallback(async () => {
    if (!session || ending) return;
    setEnding(true);
    try {
      const summary = await api.endSession(session.sessionId);
      setQueue(null);
      setDetail(null);
      onEndSession(summary);
    } catch (error) {
      onError((error as Error).message);
    } finally {
      setEnding(false);
    }
  }, [ending, onEndSession, onError, session]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea") return;
      const index = focusedItem ? flatIds.indexOf(focusedItem.practiceItemId) : -1;
      if (["j", "ArrowDown"].includes(event.key)) {
        setFocusedId(flatIds[Math.min(flatIds.length - 1, index + 1)] ?? null);
        event.preventDefault();
      } else if (["k", "ArrowUp"].includes(event.key)) {
        setFocusedId(flatIds[Math.max(0, index - 1)] ?? null);
        event.preventDefault();
      } else if (["Enter", "l", "ArrowRight"].includes(event.key) && focusedItem) {
        onOpenPractice(focusedItem.practiceItemId);
        event.preventDefault();
      } else if (/^[1-9]$/.test(event.key)) {
        const target = flatIds[Number(event.key) - 1];
        if (target) {
          setFocusedId(target);
          onOpenPractice(target);
          event.preventDefault();
        }
      } else if (event.key.toLowerCase() === "e") {
        void finishSession();
        event.preventDefault();
      } else if (event.key.toLowerCase() === "r") {
        void refreshQueue({ force: true });
        event.preventDefault();
      } else if (event.key.toLowerCase() === "w") {
        setWriteCardOpen(true);
        event.preventDefault();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [finishSession, flatIds, focusedItem, onOpenPractice]);

  async function refreshQueue({ force = false }: { force?: boolean } = {}): Promise<QueueSnapshot | null> {
    const input = {
      sessionId: session?.sessionId ?? null,
      availableMinutes: session?.availableMinutes ?? null,
      energy: session?.energy ?? null
    };
    const key = JSON.stringify(input);
    const inFlight = queueRequestRef.current;
    const reuse = !force && inFlight?.key === key;
    const requestId = reuse ? inFlight.id : queueRequestSeqRef.current + 1;
    const promise = reuse ? inFlight.promise : api.getTodayQueue(input);

    if (!reuse) {
      queueRequestSeqRef.current = requestId;
      queueRequestRef.current = { key, promise, id: requestId };
    }
    setQueueLoading(true);
    try {
      const next = await promise;
      if (queueRequestSeqRef.current === requestId) {
        setQueue(next);
        setFocusedId(queueItems(next)[0]?.practiceItemId ?? null);
      }
      return next;
    } catch (error) {
      onError((error as Error).message);
      return null;
    } finally {
      if (queueRequestRef.current?.promise === promise) {
        queueRequestRef.current = null;
      }
      if (queueRequestSeqRef.current === requestId) {
        setQueueLoading(false);
      }
    }
  }

  function refreshAfterGoalChange() {
    refreshGoals();
    void refreshQueue({ force: true });
  }

  async function practiceAtRisk() {
    let target = firstGoalFrontierItem(queue);
    if (!target) {
      target = firstGoalFrontierItem(await refreshQueue({ force: true }));
    }
    if (!target) {
      onError("No at-risk goal practice item is scheduled yet.");
      return;
    }
    setFocusedId(target.practiceItemId);
    onOpenPractice(target.practiceItemId);
  }

  if (queueLoading && !queue) {
    return <EmptyPlaceholder title="Loading today's queue" />;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      {/* F7 welcome-back diff (§4.4): survival-first, BEFORE the hero. */}
      {reentry ? <ReentryPanel summary={reentry} /> : null}

      <TodayHero
        session={session}
        now={now}
        dueCount={dueCount}
        probeCount={probeCount}
        laterCount={laterCount}
        narrative={sessionNarrative}
        overconfidence={overconfidence}
        onProbe={startOverconfidenceProbe}
        queueReady={Boolean(queue?.totalItems)}
        gradingReady={gradingReady}
        gradingProvider={gradingProvider}
        ending={ending}
        onFinish={finishSession}
      />

      {goals != null ? (
        activeGoals.length > 0 ? (
          <GoalBanner
            goals={activeGoals}
            onError={onError}
            onPracticeAtRisk={practiceAtRisk}
            onTakeExam={onTakeExam}
            onNewGoal={() => setWizardOpen(true)}
          />
        ) : !noGoalBannerDismissed ? (
          <NoGoalFallback
            pressure={decayPressure}
            onDismiss={onDismissNoGoalBanner ?? (() => undefined)}
            onSetGoal={() => setWizardOpen(true)}
            onReadFirst={() => {
              const first = items[0];
              if (first) onInspect(first.learningObjectId);
              else onError("Nothing to read yet — import a source first.");
            }}
            onDiagnostic={() => {
              const first = items.find((item) => !item.isProbe) ?? items[0];
              if (first) {
                api
                  .startOverconfidenceProbe(first.learningObjectId, null)
                  .then(() => refreshQueue({ force: true }))
                  .catch((error) => onError((error as Error).message));
              } else {
                onError("No learning objects to diagnose yet.");
              }
            }}
          />
        ) : null
      ) : null}

      {reviewCandidate ? (
        <GoalReviewCard
          goal={reviewCandidate.goal}
          reason={reviewCandidate.reason}
          onKeep={(id) => setDismissedReview((prev) => new Set(prev).add(id))}
          onChanged={refreshAfterGoalChange}
          onError={onError}
        />
      ) : null}

      <div
        className={wizardOpen ? "modal-underlay-obscured" : undefined}
        style={{ flex: 1, display: "flex", minHeight: 0 }}
      >
        {/* Master list */}
        <div className="library-tree" style={{ flex: 1, overflowY: "auto", minHeight: 0 }}>
          {bannerOpen && followup ? (
            <SurpriseInsertionBanner
              followup={followup}
              onDismiss={() => setBannerOpen(false)}
              onOpen={(id) => {
                setFocusedId(id);
                onOpenPractice(id);
              }}
              onInspect={onInspect}
            />
          ) : null}

          {queue?.sections.map((section) => (
            <QueueSectionGroup
              key={section.title}
              section={section}
              now={now}
              focusedId={focusedItem?.practiceItemId ?? null}
              hotkeyOf={(id) => HOTKEYS[flatIds.indexOf(id)] ?? "·"}
              onSelect={setFocusedId}
              onInspect={onInspect}
            />
          ))}

          {queue && queue.totalItems === 0 ? (
            readerSeedingActive ? (
              <div style={{ padding: 30, fontSize: 13, lineHeight: 1.7 }}>
                <div style={{ color: COLOR.text }}>Your study map is ready.</div>
                <div style={{ color: COLOR.textDim, marginTop: 6 }}>
                  Start reading — practice builds itself as you complete sections.
                </div>
                {onGotoReader ? (
                  <button
                    type="button"
                    onClick={onGotoReader}
                    style={{
                      marginTop: 14,
                      padding: "8px 16px",
                      border: `1px solid ${COLOR.amber}`,
                      background: "#241d12",
                      color: COLOR.amber,
                      fontFamily: FONT_MONO,
                      fontSize: 12,
                      cursor: "pointer"
                    }}
                  >
                    open the reader →
                  </button>
                ) : null}
              </div>
            ) : (
              <div style={{ padding: 30, color: COLOR.textFaint, fontSize: 13 }}>No scheduled items.</div>
            )
          ) : null}

          <QuestionQueuePanel onError={onError} />

          <QueueRankingStrip algorithmVersion={algorithmVersion} />
        </div>

        {/* Detail pane */}
        <div
          className="ll-scroll"
          style={{
            width: 380,
            flexShrink: 0,
            borderLeft: `1px solid ${COLOR.border}`,
            background: COLOR.bg,
            overflowY: "auto"
          }}
        >
          <QueueDetail
            item={focusedItem}
            detail={detail}
            sessionId={session?.sessionId ?? null}
            visitId={visitIdRef.current}
            producerVersion={algorithmVersion}
            onPractice={() => focusedItem && onOpenPractice(focusedItem.practiceItemId)}
            onWriteCard={() => setWriteCardOpen(true)}
            onInspect={onInspect}
            onOpenFacet={setEvidenceFacetId}
            onError={onError}
          />
        </div>
      </div>

      <KeyBar
        keys={[
          { key: "j/k", label: "Move" },
          { key: "enter", label: "Practice" },
          { key: "1-9", label: "Quick open" },
          { key: "w", label: "Write a card" },
          { key: "e", label: "End session" },
          { key: "r", label: "Refresh" }
        ]}
        right={{ key: "^p", label: "palette" }}
      />

      {wizardOpen ? (
        <GoalWizard onClose={() => setWizardOpen(false)} onCreated={refreshAfterGoalChange} onError={onError} />
      ) : null}

      {writeCardOpen ? (
        <WriteCardDialog
          defaultLearningObjectId={focusedItem?.learningObjectId ?? null}
          defaultLearningObjectTitle={focusedItem?.learningObjectTitle ?? null}
          onClose={() => setWriteCardOpen(false)}
          onCreated={() => void refreshQueue({ force: true })}
        />
      ) : null}

      {evidenceFacetId ? (
        <FacetEvidenceDrawer
          facetId={evidenceFacetId}
          onClose={() => setEvidenceFacetId(null)}
          onInspect={(entityId) => {
            setEvidenceFacetId(null);
            onInspect(entityId);
          }}
        />
      ) : null}
    </div>
  );
}

function TodayHero({
  session: rawSession,
  now,
  dueCount,
  probeCount,
  laterCount,
  narrative,
  overconfidence,
  onProbe,
  queueReady,
  gradingReady,
  gradingProvider,
  ending,
  onFinish
}: {
  session: SessionSnapshot | null;
  now: Date;
  dueCount: number;
  probeCount: number;
  laterCount: number;
  narrative: string | null;
  overconfidence: OverconfidentFacetDto[];
  onProbe: (facet: OverconfidentFacetDto) => void;
  queueReady: boolean;
  gradingReady: boolean;
  gradingProvider: string;
  ending: boolean;
  onFinish: () => void;
}) {
  const remainingMinutes = remainingSessionMinutes(rawSession, now);
  const session = rawSession && remainingMinutes != null ? { ...rawSession, availableMinutes: remainingMinutes } : rawSession;
  const stats: Array<{ label: string; val: string | number; color: string }> = [
    { label: "DUE", val: dueCount, color: COLOR.amber },
    { label: "PROBE", val: probeCount, color: COLOR.pink },
    { label: "LATER", val: laterCount, color: COLOR.textDim },
    { label: "BUDGET", val: session?.availableMinutes ? `${session.availableMinutes}m` : "—", color: COLOR.green }
  ];
  const sep = <span style={{ color: COLOR.textFaint, margin: "0 8px" }}>·</span>;
  const Stat = ({ value, label, color }: { value: string | number; label: string; color: string }) => (
    <span style={{ whiteSpace: "nowrap" }}>
      <span style={{ color, fontWeight: 600 }}>{value}</span> <span style={{ color: COLOR.textDim }}>{label}</span>
    </span>
  );

  return (
    <div
      style={{
        padding: "24px 32px 22px",
        background: COLOR.bg,
        borderBottom: `1px solid ${COLOR.border}`,
        display: "flex",
        gap: 32,
        alignItems: "flex-end",
        flexShrink: 0
      }}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: 13,
            color: COLOR.textFaint,
            display: "flex",
            flexWrap: "wrap",
            alignItems: "baseline",
            rowGap: 4
          }}
        >
          <span style={{ textTransform: "uppercase", letterSpacing: "0.18em", color: COLOR.textFaint, fontSize: 11 }}>
            today · session {session ? formatSessionNumber(session.sessionId) : "none"} · {formatHeroTime(now)}
          </span>
          {sep}
          <Stat value={`${dueCount} ${dueCount === 1 ? "item" : "items"}`} label="due" color={COLOR.amber} />
          {sep}
          <Stat value={probeCount} label="probe" color={COLOR.pink} />
          {sep}
          <Stat value={session?.availableMinutes ? `${session.availableMinutes} min` : "—"} label="budget" color={COLOR.green} />
        </div>

        {narrative && (
          <div style={{ marginTop: 10, fontSize: 13, color: COLOR.amber }}>{narrative}</div>
        )}

        <OverconfidenceList facets={overconfidence} onProbe={onProbe} />

        <div style={{ marginTop: 12, fontSize: 13, color: COLOR.textDim, lineHeight: 1.65 }}>
          vault <span style={{ color: COLOR.green }}>● healthy</span>
          {"  ·  "}
          ai:{gradingProvider}{" "}
          <span style={{ color: gradingReady ? COLOR.green : COLOR.red }}>● {gradingReady ? "ready" : "down"}</span>
          {"  ·  "}
          queue{" "}
          <span style={{ color: queueReady ? COLOR.green : COLOR.textFaint }}>● {queueReady ? "ready" : "empty"}</span>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, auto)", border: `1px solid ${COLOR.border}`, flexShrink: 0 }}>
        {stats.map((s, i) => (
          <div
            key={s.label}
            style={{
              padding: "10px 16px",
              borderRight: i < stats.length - 1 ? `1px solid ${COLOR.border}` : "none",
              minWidth: 78,
              textAlign: "right",
              background: COLOR.bgElev
            }}
          >
            <div style={{ fontSize: 10, color: COLOR.textFaint, letterSpacing: "0.14em" }}>{s.label}</div>
            <div style={{ fontSize: 20, color: s.color, fontFamily: FONT_MONO, marginTop: 3, lineHeight: 1.1 }}>{s.val}</div>
          </div>
        ))}
      </div>

      {session ? (
        <button
          type="button"
          onClick={onFinish}
          disabled={ending}
          style={{
            alignSelf: "flex-end",
            padding: "8px 14px",
            border: `1px solid ${COLOR.borderStrong}`,
            background: "transparent",
            color: COLOR.textDim,
            fontFamily: FONT_MONO,
            fontSize: 12,
            cursor: ending ? "default" : "pointer",
            whiteSpace: "nowrap"
          }}
        >
          {ending ? "ending…" : "finish session"}
        </button>
      ) : null}
    </div>
  );
}

function QueueSectionGroup({
  section,
  now,
  focusedId,
  hotkeyOf,
  onSelect,
  onInspect
}: {
  section: QueueSection;
  now: Date;
  focusedId: string | null;
  hotkeyOf: (id: string) => string;
  onSelect: (id: string) => void;
  onInspect: (id: string) => void;
}) {
  const isProbe = /probe/i.test(section.title);
  const isDue = /due|now|overdue/i.test(section.title);
  const color = isProbe ? COLOR.pink : isDue ? COLOR.amber : COLOR.textDim;
  const mark = isProbe ? "◆" : "▸";

  return (
    <div>
      <div style={{ padding: "20px 24px 10px", display: "flex", alignItems: "center", gap: 12 }}>
        <span style={{ color, fontFamily: FONT_MONO, fontSize: 12 }}>{mark}</span>
        <span style={{ color, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.18em" }}>
          {section.title}
        </span>
        <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textFaint, padding: "1px 7px", border: `1px solid ${COLOR.border}` }}>
          {String(section.items.length).padStart(2, "0")}
        </span>
        <span style={{ flex: 1, height: 1, background: COLOR.border, opacity: 0.6 }} />
      </div>
      {section.items.map((item) => (
        <QueueRow
          key={item.practiceItemId}
          item={item}
          now={now}
          focused={focusedId === item.practiceItemId}
          hotkey={hotkeyOf(item.practiceItemId)}
          onSelect={() => onSelect(item.practiceItemId)}
          onInspect={onInspect}
        />
      ))}
    </div>
  );
}

function QueueRow({
  item,
  now,
  focused,
  hotkey,
  onSelect,
  onInspect
}: {
  item: ScheduledItemDto;
  now: Date;
  focused: boolean;
  hotkey: string;
  onSelect: () => void;
  onInspect: (id: string) => void;
}) {
  const dueOffset = relativeDue(item, now);
  const overdue = dueOffset.includes("ago");
  const mastery = item.mastery;
  const borderLeft = focused || item.isFollowup ? COLOR.amber : item.isProbe ? COLOR.pink : "transparent";

  return (
    <div
      onClick={onSelect}
      style={{
        padding: "14px 24px",
        background: focused ? COLOR.bgElev : "transparent",
        borderLeft: `3px solid ${borderLeft}`,
        cursor: "pointer",
        display: "grid",
        gridTemplateColumns: "34px minmax(0, 1fr) 200px 130px",
        gap: 18,
        alignItems: "center",
        transition: "background 100ms ease"
      }}
    >
      <span
        style={{
          color: focused ? COLOR.amber : COLOR.textFaint,
          fontFamily: FONT_MONO,
          fontSize: 12,
          fontWeight: 700,
          textAlign: "center",
          padding: "4px 0",
          border: `1px solid ${focused ? COLOR.amber : COLOR.borderStrong}`,
          background: focused ? "#241d12" : "transparent"
        }}
      >
        {hotkey}
      </span>

      <div style={{ minWidth: 0 }}>
        <div
          style={{
            fontSize: 14,
            color: COLOR.text,
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
            gap: 8,
            flexWrap: "wrap",
            rowGap: 4,
            lineHeight: 1.35
          }}
        >
          <span style={{ overflowWrap: "anywhere" }}>{item.learningObjectTitle}</span>
          {item.isProbe ? <Pill color="pink">probe</Pill> : null}
          {item.isFollowup ? <Pill color="amber">intervention</Pill> : null}
        </div>
        
        <div style={{ marginTop: 3, display: "flex", alignItems: "center", gap: 8 }}>
          <EntityLink id={item.practiceItemId} onInspect={onInspect} style={{ textDecorationColor: COLOR.textFaint }}>
            <Meta style={{ fontSize: 11 }}>{item.practiceItemId}</Meta>
          </EntityLink>
          <Faint>·</Faint>
          <Pill color={modePillColor(item.practiceMode)}>{item.practiceMode}</Pill>
        </div>
      </div>

      <span style={{ display: "inline-flex", gap: 10, alignItems: "center", fontSize: 12 }}>
        <Faint style={{ fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase" }}>mastery</Faint>
        {mastery == null ? (
          <Faint>—</Faint>
        ) : (
          <>
            <BlockBar value={mastery} width={10} color={masteryColor(mastery)} />
            <span style={{ fontFamily: FONT_MONO, color: COLOR.text }}>{mastery.toFixed(2)}</span>
          </>
        )}
      </span>

      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 3 }}>
        <div style={{ fontFamily: FONT_MONO, fontSize: 13, color: overdue ? COLOR.amber : item.isProbe ? COLOR.pink : COLOR.text }}>
          {dueOffset}
        </div>
        <span style={{ fontSize: 10, color: COLOR.textFaint, letterSpacing: "0.08em", textTransform: "uppercase" }}>
          {overdue ? "overdue" : item.isProbe ? "probe" : "scheduled"}
        </span>
      </div>
    </div>
  );
}

function SurpriseInsertionBanner({
  followup,
  onDismiss,
  onOpen,
  onInspect
}: {
  followup: ScheduledItemDto;
  onDismiss: () => void;
  onOpen: (id: string) => void;
  onInspect: (id: string) => void;
}) {
  return (
    <div
      style={{
        margin: "18px 24px 0",
        padding: "14px 18px",
        border: `1px solid ${COLOR.borderStrong}`,
        borderLeft: `3px solid ${COLOR.amber}`,
        background: "#231a0e",
        display: "flex",
        alignItems: "flex-start",
        gap: 16
      }}
    >
      <div
        style={{
          width: 36,
          height: 36,
          flexShrink: 0,
          border: `1px solid ${COLOR.amber}`,
          background: "#0a0a0a",
          color: COLOR.amber,
          fontFamily: FONT_MONO,
          fontSize: 14,
          fontWeight: 700,
          display: "flex",
          alignItems: "center",
          justifyContent: "center"
        }}
      >
        +1
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 11, color: COLOR.amber, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.14em" }}>
          intervention gate - diagnostic follow-up inserted
        </div>
        <div style={{ marginTop: 6, fontSize: 13, color: COLOR.text, lineHeight: 1.55 }}>
          A diagnostic follow-up on{" "}
          <EntityLink id={followup.practiceItemId} onInspect={onInspect}>
            {followup.learningObjectTitle}
          </EntityLink>{" "}
          was queued after the latest attempt crossed an intervention trigger.
        </div>
        <div style={{ marginTop: 10, display: "flex", gap: 16, flexWrap: "wrap", fontSize: 11, alignItems: "center" }}>
          <span>
            <Faint>follow-up</Faint> <Meta>{followup.practiceItemId}</Meta>
          </span>
          <span style={{ flex: 1 }} />
          <span
            onClick={() => onOpen(followup.practiceItemId)}
            style={{
              padding: "5px 14px",
              border: `1px solid ${COLOR.amber}`,
              background: "#241d12",
              color: COLOR.amber,
              fontFamily: FONT_MONO,
              fontSize: 11,
              fontWeight: 600,
              cursor: "pointer"
            }}
          >
            open follow-up →
          </span>
        </div>
      </div>
      <span onClick={onDismiss} title="dismiss" style={{ color: COLOR.textFaint, cursor: "pointer", fontSize: 16, padding: "0 4px" }}>
        ×
      </span>
    </div>
  );
}

const WHY_ROWS: Array<{ key: keyof SchedulerComponents; label: string; color: string }> = [
  { key: "forgettingRisk", label: "forgetting_risk", color: COLOR.amber },
  { key: "goalFrontier", label: "goal_frontier", color: COLOR.green },
  { key: "recentError", label: "recent_error", color: COLOR.red },
  { key: "probeEig", label: "probe_eig", color: COLOR.pink }
];

function WhyRow({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "130px 1fr 50px", gap: 10, alignItems: "center", padding: "4px 0", fontSize: 12 }}>
      <span style={{ color, fontFamily: FONT_MONO }}>{label}</span>
      <div style={{ height: 6, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, position: "relative" }}>
        <div style={{ position: "absolute", inset: 0, width: `${Math.min(100, value * 100)}%`, background: color }} />
      </div>
      <span style={{ fontFamily: FONT_MONO, color, textAlign: "right" }}>{value.toFixed(2)}</span>
    </div>
  );
}

function QueueDetail({
  item,
  detail,
  sessionId,
  visitId,
  producerVersion,
  onPractice,
  onWriteCard,
  onInspect,
  onOpenFacet,
  onError
}: {
  item: ScheduledItemDto | null;
  detail: PracticeItemDetail | null;
  sessionId: string | null;
  visitId: string | null;
  producerVersion: string;
  onPractice: () => void;
  onWriteCard: () => void;
  onInspect: (id: string) => void;
  onOpenFacet: (facetId: string) => void;
  onError: (message: string) => void;
}) {
  if (!item) {
    return (
      <div style={{ padding: 30, color: COLOR.textFaint, fontSize: 13, display: "flex", flexDirection: "column", gap: 14 }}>
        <span>no item selected</span>
        <span
          onClick={onWriteCard}
          style={{
            alignSelf: "flex-start",
            padding: "6px 14px",
            border: `1px solid ${COLOR.borderStrong}`,
            color: COLOR.textDim,
            fontSize: 12,
            cursor: "pointer"
          }}
        >
          write a card <Faint>w</Faint>
        </span>
      </div>
    );
  }
  const components = detail?.scheduler?.components ?? item.components;
  const variance = detail?.mastery?.variance ?? item.masteryVariance ?? 0.1;
  const mastery = detail?.mastery?.mean ?? item.mastery;

  return (
    <div className = "ll-scroll" style={{ padding: "20px 22px" }}>
      <div style={{ fontSize: 11, color: COLOR.textFaint, marginBottom: 4, fontFamily: FONT_MONO }}>
        <EntityLink id={item.practiceItemId} onInspect={onInspect}>
          {item.practiceItemId}
        </EntityLink>
      </div>
      <div style={{ fontSize: 17, fontWeight: 600, color: COLOR.text, lineHeight: 1.3 }}>{item.learningObjectTitle}</div>
      <div style={{ marginTop: 8, display: "flex", gap: 6, flexWrap: "wrap" }}>
        <Pill color={modePillColor(item.practiceMode)}>{item.practiceMode}</Pill>
        {item.isProbe ? <Pill color="pink">probe</Pill> : null}
        {item.subject ? <Pill color="slate">{item.subject}</Pill> : null}
      </div>

      <SectionHeader>Prompt</SectionHeader>
      <div style={{ padding: "12px 14px", background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, fontSize: 13, lineHeight: 1.6, color: COLOR.text }}>
        {detail ? <MarkdownMath value={detail.prompt} /> : <Faint>loading…</Faint>}
      </div>

      <div style={{ marginTop: 22, display: "flex", gap: 10, flexWrap: "wrap" }}>
        <span
          onClick={onPractice}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            padding: "8px 16px",
            border: `1px solid ${COLOR.amber}`,
            background: "#241d12",
            color: COLOR.amber,
            fontSize: 13,
            fontWeight: 600,
            cursor: "pointer"
          }}
        >
          start practice
          <Faint style={{ color: COLOR.amber }}>↵</Faint>
        </span>
        <span
          onClick={onWriteCard}
          title="write your own card for this learning object — saved to your vault, no review step"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            padding: "8px 16px",
            border: `1px solid ${COLOR.borderStrong}`,
            background: "transparent",
            color: COLOR.textDim,
            fontSize: 13,
            cursor: "pointer"
          }}
        >
          write a card
          <Faint>w</Faint>
        </span>
      </div>

      <SectionHeader>Mastery posterior</SectionHeader>
      <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 12 }}>
        {mastery == null ? (
          <Faint>no evidence yet</Faint>
        ) : (
          <>
            <BlockBar value={mastery} width={14} color={masteryColor(mastery)} />
            <span style={{ fontFamily: FONT_MONO, color: COLOR.text }}>{mastery.toFixed(2)}</span>
            <Faint>±{Math.sqrt(variance).toFixed(2)}</Faint>
          </>
        )}
        <span style={{ flex: 1 }} />
        {detail?.difficulty != null ? (
          <>
            <Faint>difficulty</Faint>
            <Dim style={{ fontFamily: FONT_MONO }}>{detail.difficulty.toFixed(2)}</Dim>
          </>
        ) : null}
      </div>

      {/* F5 reason column as a schedule_choice policy claim (§4.3). Affordances
          only on the focused/expanded row, keeping the queue itself light. */}
      {item.dominantReason ? (
        <>
          <SectionHeader>Scheduler choice</SectionHeader>
          <ClaimSurface
            key={`${item.practiceItemId}:${item.dominantReason}`}
            claim={scheduleChoiceClaim(item, producerVersion)}
            sessionId={sessionId}
            visitId={visitId}
            variant="detail-panel"
            onError={onError}
          />
        </>
      ) : null}

      <SectionHeader>Why this position</SectionHeader>
      {WHY_ROWS.map((row) => (
        <WhyRow key={row.key} label={row.label} value={components[row.key] ?? 0} color={row.color} />
      ))}
      <div style={{ marginTop: 8, fontSize: 11, color: COLOR.textFaint }}>
        <Faint>priority</Faint> <Dim style={{ fontFamily: FONT_MONO }}>{item.priority.toFixed(3)}</Dim>
        <span style={{ margin: "0 10px" }}>·</span>
        <Faint>full breakdown</Faint>{" "}
        <EntityLink id={item.practiceItemId} onInspect={onInspect}>
          <span style={{ color: COLOR.amberLink, textDecoration: "underline", textUnderlineOffset: 2 }}>show</span>
        </EntityLink>
        {detail?.hints?.length ? (
          <>
            <span style={{ margin: "0 10px" }}>·</span>
            <Faint>{detail.hints.length} hints available</Faint>
          </>
        ) : null}
      </div>

      {detail?.evidenceFacets?.length ? (
        <>
          <SectionHeader>Evidence facets</SectionHeader>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {detail.evidenceFacets.map((facet) => (
              <button
                key={facet}
                type="button"
                onClick={() => onOpenFacet(facet)}
                title={`learnloop show ${facet}`}
                aria-label={`Open evidence receipt for ${facet}`}
                style={evidenceFacetButtonStyle}
              >
                <Pill color="cyan" style={{ cursor: "pointer" }}>↗ {facet}</Pill>
              </button>
            ))}
          </div>
        </>
      ) : null}




    </div>
  );
}

const evidenceFacetButtonStyle: CSSProperties = {
  padding: 0,
  border: 0,
  background: "transparent",
  cursor: "pointer"
};

function QueueRankingStrip({ algorithmVersion }: { algorithmVersion: string }) {
  return (
    <div style={{ margin: "28px 24px", padding: "14px 18px", border: `1px dashed ${COLOR.border}`, fontSize: 12, color: COLOR.textDim, lineHeight: 1.7 }}>
      <span style={{ color: COLOR.amber, fontSize: 10, textTransform: "uppercase", letterSpacing: "0.14em", fontWeight: 700 }}>
        queue ranking · priority = Σ wᵢ · componentᵢ
      </span>
      <div style={{ marginTop: 8, fontFamily: FONT_MONO }}>
        forgetting_risk × 1.00 {"  +  "}goal_frontier × 0.25 {"  +  "}recent_error × 0.50 {"  +  "}probe_eig × 0.25
      </div>
      <div style={{ marginTop: 6 }}>
        <Faint>algorithm</Faint> <Dim>{algorithmVersion}</Dim>
        <span style={{ margin: "0 10px" }}>·</span>
        <Faint>focus a row to see its per-component breakdown</Faint>
      </div>
    </div>
  );
}

// F5: build a schedule_choice policy claim for a queue item (§2.1, §4.3). The
// claim_ref is the structured item identity; claim_version keys on the reason so
// a materially changed reason re-presents (§2.2). producer_version stamps the
// selection policy that produced the reason.
function scheduleChoiceClaim(item: ScheduledItemDto, producerVersion: string): ClaimCandidateDto {
  return {
    claimClass: "policy",
    claimType: "schedule_choice",
    claimRef: { practiceItemId: item.practiceItemId, learningObjectId: item.learningObjectId },
    claimVersion: `reason:${item.dominantReason ?? ""}`,
    producerVersion,
    surface: "today",
    temperature: "cold",
    claimText: `Chosen next because ${item.dominantReason}`,
    provenance: item.practiceItemId
  };
}

// F5 overconfidence list (§4.3): compact expandable list anchored on the session
// narrative. One tap starts a probe (origin='overconfidence_list').
function OverconfidenceList({
  facets,
  onProbe
}: {
  facets: OverconfidentFacetDto[];
  onProbe: (facet: OverconfidentFacetDto) => void;
}) {
  const [open, setOpen] = useState(false);
  const [started, setStarted] = useState<Set<string>>(() => new Set());
  if (facets.length === 0) return null;
  return (
    <div style={{ marginTop: 8, fontSize: 12 }}>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        style={{
          background: "transparent",
          border: "none",
          padding: 0,
          color: COLOR.pink,
          cursor: "pointer",
          fontFamily: FONT_MONO,
          fontSize: 12
        }}
        aria-expanded={open}
      >
        {open ? "▾" : "▸"} {facets.length} facet{facets.length === 1 ? "" : "s"} you may be overconfident about
      </button>
      {open ? (
        <div style={{ marginTop: 6, display: "flex", flexDirection: "column", gap: 4 }}>
          {facets.map((facet) => {
            const key = `${facet.learningObjectId}:${facet.facetId}`;
            const done = started.has(key);
            return (
              <div key={key} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ color: COLOR.text }}>{facet.facetId.replace(/^facet_/, "")}</span>
                <Faint style={{ fontSize: 11 }}>ready {facet.ready.toFixed(2)} · not demonstrated</Faint>
                <span style={{ flex: 1 }} />
                <button
                  type="button"
                  disabled={done}
                  onClick={() => { onProbe(facet); setStarted((prev) => new Set(prev).add(key)); }}
                  className="queue-row"
                  style={{ fontSize: 11 }}
                >
                  {done ? "probe queued" : "probe this"}
                </button>
              </div>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}

// F7 welcome-back diff (§4.4): survival-first ordering. Never leads with losses;
// never mentions the streak.
function ReentryPanel({ summary }: { summary: ReentrySummaryDto }) {
  const named = summary.slippedTop.map((f) => f.facetId.replace(/^facet_/, "")).join(", ");
  return (
    <div
      style={{
        margin: "16px 24px 0",
        padding: "14px 18px",
        border: `1px solid ${COLOR.borderStrong}`,
        borderLeft: `3px solid ${COLOR.green}`,
        background: COLOR.bgElev
      }}
    >
      <div style={{ fontSize: 11, color: COLOR.green, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.14em" }}>
        welcome back — {summary.gapDays} days away
      </div>
      <div style={{ marginTop: 8, fontSize: 13, color: COLOR.text, lineHeight: 1.6 }}>
        <span style={{ color: COLOR.green }}>Still solid: {summary.solidCount} facets.</span>{" "}
        {summary.slippedCount > 0 ? (
          <>
            Slipped below target while you were away: {summary.slippedCount}
            {named ? <Faint> — {named}</Faint> : null}.{" "}
          </>
        ) : null}
        <span style={{ color: COLOR.amber }}>Your best next session: {summary.refresherCount} refreshers.</span>
      </div>
    </div>
  );
}

// F7 no-goal / fresh-vault fallback (§4.5). With FSRS history: the decay-pressure
// list fills the hero slot. Fresh vault (no history): three real actions.
function NoGoalFallback({
  pressure,
  onDismiss,
  onSetGoal,
  onReadFirst,
  onDiagnostic
}: {
  pressure: DecayPressureDto | null;
  onDismiss: () => void;
  onSetGoal: () => void;
  onReadFirst: () => void;
  onDiagnostic: () => void;
}) {
  const action = (label: string, onClick: () => void) => (
    <span
      onClick={onClick}
      style={{
        padding: "6px 14px",
        border: `1px solid ${COLOR.amber}`,
        background: "#241d12",
        color: COLOR.amber,
        fontFamily: FONT_MONO,
        fontSize: 12,
        cursor: "pointer"
      }}
    >
      {label}
    </span>
  );
  const dismiss = (
    <button type="button" onClick={onDismiss} title="dismiss" aria-label="Dismiss no active goal banner" style={dismissBannerButtonStyle}>
      ×
    </button>
  );

  if (pressure && pressure.hasHistory && pressure.facets.length > 0) {
    return (
      <div style={{ margin: "16px 24px 0", padding: "14px 18px", border: `1px solid ${COLOR.border}` }}>
        <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
          <div style={{ fontSize: 11, color: COLOR.amber, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.14em", flex: 1 }}>
            decay pressure — no active goal
          </div>
          {dismiss}
        </div>
        <div style={{ marginTop: 4, fontSize: 11, color: COLOR.textFaint }}>
          facets crossing the recall target soonest
          {pressure.heldFlatCount > 0 ? ` · ${pressure.heldFlatCount} held flat (not enough history)` : ""}
        </div>
        <div style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 5 }}>
          {pressure.facets.slice(0, 8).map((facet) => (
            <div key={`${facet.learningObjectId}:${facet.facetId}`} style={{ display: "grid", gridTemplateColumns: "1fr 130px", gap: 12, fontSize: 12, alignItems: "baseline" }}>
              <span style={{ color: COLOR.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {facet.facetId.replace(/^facet_/, "")} <Faint style={{ fontSize: 11 }}>· {facet.learningObjectTitle}</Faint>
              </span>
              <span style={{ fontFamily: FONT_MONO, color: COLOR.amber, textAlign: "right" }}>
                {facet.crossesInDays == null
                  ? "stable"
                  : facet.crossesInDays === 0
                    ? "below target"
                    : `crosses in ~${facet.crossesInDays}d`}
              </span>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 12 }}>{action("set a goal ↵", onSetGoal)}</div>
      </div>
    );
  }

  // Fresh vault: no goal, no history.
  return (
    <div style={{ margin: "16px 24px 0", padding: "14px 18px", border: `1px dashed ${COLOR.border}` }}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
        <div style={{ fontSize: 13, color: COLOR.textDim, lineHeight: 1.6, flex: 1 }}>
          No goal yet, and not enough practice history to project decay. Start here:
        </div>
        {dismiss}
      </div>
      <div style={{ marginTop: 12, display: "flex", gap: 10, flexWrap: "wrap" }}>
        {action("read first", onReadFirst)}
        {action("set a goal", onSetGoal)}
        {action("run a short diagnostic", onDiagnostic)}
      </div>
    </div>
  );
}

const dismissBannerButtonStyle: CSSProperties = {
  border: 0,
  background: "transparent",
  color: COLOR.textFaint,
  padding: "0 4px",
  fontFamily: FONT_MONO,
  fontSize: 16,
  lineHeight: 1,
  cursor: "pointer"
};

function unique(values: string[]): string[] {
  return Array.from(new Set(values.filter(Boolean)));
}

function queueItems(snapshot: QueueSnapshot | null): ScheduledItemDto[] {
  return snapshot?.sections.flatMap((section) => section.items) ?? [];
}

function firstGoalFrontierItem(snapshot: QueueSnapshot | null): ScheduledItemDto | null {
  return queueItems(snapshot).find((item) => (item.components.goalFrontier ?? 0) > 0) ?? null;
}

function useNowMinute(): Date {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 60_000);
    return () => window.clearInterval(id);
  }, []);
  return now;
}

function remainingSessionMinutes(session: SessionSnapshot | null, now: Date): number | null {
  if (!session?.availableMinutes) return null;
  const startedAt = new Date(session.startedAt).getTime();
  if (Number.isNaN(startedAt)) return session.availableMinutes;
  const elapsedMinutes = Math.max(0, Math.floor((now.getTime() - startedAt) / 60_000));
  return Math.max(0, session.availableMinutes - elapsedMinutes);
}

function formatHeroTime(date: Date): string {
  return new Intl.DateTimeFormat(undefined, { weekday: "short", hour: "2-digit", minute: "2-digit" }).format(date);
}

function formatSessionNumber(sessionId: string): string {
  const matches = sessionId.match(/\d+/g);
  const digits = matches ? matches[matches.length - 1] : undefined;
  return digits ? digits.padStart(3, "0") : sessionId.slice(0, 6);
}

// Relative due offset ("3h ago" / "in 2h" / "now") from the item's dueAt; falls
// back to the scheduler's coarse dueStatus when no timestamp is available.
function relativeDue(item: ScheduledItemDto, now: Date): string {
  if (item.isProbe && !item.dueAt) return "probe";
  if (!item.dueAt) return item.dueStatus ?? "—";
  const due = new Date(item.dueAt).getTime();
  if (Number.isNaN(due)) return item.dueStatus ?? "—";
  const diffMs = due - now.getTime();
  const past = diffMs < 0;
  const minutes = Math.round(Math.abs(diffMs) / 60_000);
  const span =
    minutes < 1
      ? "now"
      : minutes < 60
        ? `${minutes}m`
        : minutes < 60 * 24
          ? `${Math.round(minutes / 60)}h`
          : `${Math.round(minutes / (60 * 24))}d`;
  if (span === "now") return "now";
  return past ? `${span} ago` : `in ${span}`;
}
