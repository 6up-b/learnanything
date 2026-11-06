// The phone app: the shell of mobile v2 §4.2 (four places, a stack in each, sheets, the URL
// fragment) around M2a's practice, whose logic is unchanged: the same requests with the same
// parameters, the same handoff, the same outbox (spec §6.1, stage V1). What moved is where things
// sit on the screen; `App.test.tsx` and `src/api/contract.test.ts` pin that nothing else did.
import { useCallback, useEffect, useRef, useState } from "react";
import type { AttemptResultDto, CommandError, ScheduledItemDto, SessionEndSummary, SessionSnapshot } from "@desktop/api/dto";
import { invalidate, setQueryData, clear as clearQueries } from "@desktop/api/queryCache";
import { TAG } from "@desktop/api/queryTags";
import { committedAttempt, pollJob, refusedOutright } from "./api/http";
import { phone, type OwnerSnapshot } from "./api/phone";
import { useVisibleInterval } from "./util/useVisibleInterval";
import { CaptureScreen } from "./capture/CaptureScreen";
import { FeedbackScreen } from "./practice/FeedbackScreen";
import { PairScreen } from "./pair/PairScreen";
import { GRADING_DOWN, QuestionScreen, type QuestionTarget, type SkipOutcome, type SkipSettled } from "./practice/QuestionScreen";
import { ProgressScreen } from "./progress/ProgressScreen";
import { ReadScreen } from "./read/ReadScreen";
import { ConnectionLine } from "./shell/ConnectionLine";
import { markOffline, onReconnect } from "./shell/connection";
import { DbBlockedScreen, useDbBlocked } from "./shell/DbBlocked";
import { DisplaySheet } from "./shell/DisplaySheet";
import { checkFreshness } from "./shell/freshness";
import { parseFragment, TABS, writeFragment, type Tab } from "./shell/navigation";
import { ScreenFrame, type FrameAction } from "./shell/ScreenFrame";
import { Sheet } from "./shell/Sheet";
import { TabBar } from "./shell/TabBar";
import { useVisualViewportInset } from "./shell/viewport";
import { PHONE_QUEUE_LIMIT, queueKey, queueRows, TodayScreen } from "./today/TodayScreen";
import { readCredential, subscribeCredential, type Credential } from "./store/credential";
import { flushOutbox, listOutbox, type FlushStop } from "./store/outbox";
import {
  assistOf,
  cachedSessionId,
  cacheSessionId,
  clearQuestionDraft,
  clearQuestionDrafts,
  pendingSubmit,
  readQuestionDraft,
  rememberPendingSubmit
} from "./store/sessionCache";

/** A `keep` bound: the desktop's own token poll (`REVISION_POLL_MS`), while Today is on screen. */
const REVISION_POLL_MS = 3000;
/** §7: the outbox is flushed every minute while the app is open. */
const OUTBOX_FLUSH_MS = 60_000;

function useCredential(): Credential | null | undefined {
  const [credential, setCredential] = useState<Credential | null | undefined>(undefined);
  useEffect(() => {
    let cancelled = false;
    const read = () => {
      void readCredential().then((value) => {
        if (!cancelled) setCredential(value);
      });
    };
    read();
    const unsubscribe = subscribeCredential(read);
    return () => {
      cancelled = true;
      unsubscribe();
    };
  }, []);
  return credential;
}

export function App() {
  const credential = useCredential();
  const blocked = useDbBlocked();
  const [waiting, setWaiting] = useState(0);
  useEffect(() => {
    if (credential === null) void listOutbox().then((records) => setWaiting(records.filter((one) => !one.problem).length));
  }, [credential]);
  // An upgrade waiting on another tab: the credential can't be read until it closes (F2).
  if (blocked) return <DbBlockedScreen />;
  if (credential === undefined) return null;
  if (credential === null) {
    return (
      <div className="shell">
        <main className="frame">
          <PairScreen waiting={waiting} />
        </main>
      </div>
    );
  }
  return <Phone credential={credential} />;
}

type View =
  | { name: "today" }
  | { name: "question"; target: QuestionTarget }
  | { name: "waiting"; submissionId: string; practiceItemId: string }
  | { name: "feedback"; attemptId: string; practiceItemId: string };

interface Moved {
  readonly sessionId: string;
  readonly reason: "adopted" | "ended";
  readonly ownerLabel: string | null;
  readonly ownerGeneration: number | null;
}

interface Elsewhere {
  readonly details: OwnerSnapshot;
  readonly minutes: number;
  readonly message?: string;
}

function movedFrom(snapshot: SessionSnapshot, deviceId: string | null): Moved | null {
  const ownership = { sessionId: snapshot.sessionId, ownerLabel: snapshot.ownerLabel ?? null, ownerGeneration: snapshot.ownerGeneration ?? 0 };
  if (snapshot.endedAt) return { reason: "ended", ...ownership };
  if ((snapshot.ownerDeviceId ?? null) !== deviceId) return { reason: "adopted", ...ownership };
  return null;
}

/** The draft a checkpoint holds for this item, with the help it has already had. */
function restoredFrom(snapshot: SessionSnapshot, practiceItemId: string): NonNullable<QuestionTarget["restored"]> | null {
  const checkpoint = snapshot.checkpoint;
  if (!checkpoint || checkpoint.currentPracticeItemId !== practiceItemId) return null;
  return {
    answer: checkpoint.currentAnswer ?? "",
    submissionId: checkpoint.submissionId,
    stuck: checkpoint.declaredStuck === true,
    assist: assistOf(checkpoint)
  };
}

/**
 * Today's stack, as the fragment names it. Only the tab and the path are mirrored: a question or a
 * feedback is never reopened from the fragment, because opening either writes (the serve, the
 * feedback's open). They come back from the checkpoint and a pending submit, as M2a built it.
 */
function todayPath(view: View): string[] {
  if (view.name === "question") return ["question", view.target.practiceItemId];
  if (view.name === "feedback") return ["feedback", view.attemptId];
  if (view.name === "waiting") return ["waiting"];
  return [];
}

function Phone({ credential }: { credential: Credential }) {
  const [tab, setTab] = useState<Tab>(() => parseFragment(window.location.hash).tab);
  const [view, setView] = useState<View>({ name: "today" });
  const [session, setSession] = useState<SessionSnapshot | null>(null);
  const [moved, setMoved] = useState<Moved | null>(null);
  const [elsewhere, setElsewhere] = useState<Elsewhere | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [finished, setFinished] = useState<SessionEndSummary | null>(null);
  const [outboxWaiting, setOutboxWaiting] = useState(0);
  const [display, setDisplay] = useState(false);
  // A submit or a skip on its way: the question's own Back is disabled meanwhile, and so are the
  // frame's chevron and edge swipe, or its reply would land on whatever opened after (F1).
  const [questionBusy, setQuestionBusy] = useState(false);
  // Diagnostic checks this session left for the desktop. The next build holds them back and counts
  // them; this covers a list read before that build (§6.4).
  const [held, setHeld] = useState<ReadonlySet<string>>(() => new Set());
  const sessionRef = useRef(session);
  sessionRef.current = session;
  const deviceId = credential.deviceId;
  useVisualViewportInset();

  const reportError = useCallback((error: unknown) => {
    const command = error as CommandError;
    if (command?.code === "desktop_offline") {
      markOffline();
      return;
    }
    if (command?.code === "session_moved") {
      const details = (command.details ?? {}) as Record<string, unknown>;
      setMoved({
        sessionId: String(details.session_id ?? sessionRef.current?.sessionId ?? ""),
        reason: "adopted",
        ownerLabel: typeof details.owner_label === "string" ? details.owner_label : null,
        ownerGeneration: typeof details.owner_generation === "number" ? details.owner_generation : 0
      });
      return;
    }
    if (command?.code === "not_paired" || command?.code === "unauthorized") return;
    // A method this build names and the host no longer allows: the connection line offers the reload (§5.2).
    if (command?.code === "method_not_allowed") return;
    // A job's end read from afar: the phone has no self-grade to offer, whatever the message says.
    if (command?.code === "grading_fallback_required") {
      setNotice(GRADING_DOWN);
      return;
    }
    setNotice(command?.message ?? "Something went wrong.");
  }, []);

  const installSession = useCallback((next: SessionSnapshot | null) => {
    sessionRef.current = next;
    setSession(next);
    cacheSessionId(next ? next.sessionId : null);
    clearQuestionDrafts();
    setMoved(null);
    setElsewhere(null);
    setHeld(new Set());
    clearQueries();
  }, []);

  /** §6.5, a checkpoint that carries a submission id: finished, under way, or a draft. */
  const viewOfCheckpoint = useCallback(async (next: SessionSnapshot): Promise<View> => {
    const checkpoint = next.checkpoint;
    const itemId = checkpoint?.currentPracticeItemId ?? null;
    const restored = itemId ? restoredFrom(next, itemId) : null;
    if (!checkpoint || !itemId || !restored) return { name: "today" };
    if (checkpoint.submissionId) {
      // Out of reach, it is a draft for now: its submit asks again before it sends.
      const status = await phone.submissionStatus(checkpoint.submissionId).catch(() => null);
      if (status?.state === "completed") {
        const result = status.result as AttemptResultDto;
        clearQuestionDraft(next.sessionId, itemId);
        await phone.acknowledge(next.sessionId, itemId, checkpoint.submissionId).catch(() => undefined);
        return { name: "feedback", attemptId: result.attemptId, practiceItemId: itemId };
      }
      if (status?.state === "recorded" && status.attempt_id) {
        clearQuestionDraft(next.sessionId, itemId);
        await phone.acknowledge(next.sessionId, itemId, checkpoint.submissionId).catch(() => undefined);
        return { name: "feedback", attemptId: status.attempt_id, practiceItemId: itemId };
      }
      if (status?.state === "accepted" || status?.state === "running") {
        return { name: "waiting", submissionId: checkpoint.submissionId, practiceItemId: itemId };
      }
    }
    // Help already had is worth reopening for too: it counts on whatever is answered next.
    if (restored.answer.trim() || restored.assist.hintsUsed > 0 || restored.assist.pageSeen) {
      return { name: "question", target: { practiceItemId: itemId, schedulerCandidateId: null, restored } };
    }
    return { name: "today" };
  }, []);

  // Opening the app: the session this phone was in, and a submit it left mid-grade (A4).
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const sessionId = cachedSessionId();
      if (!sessionId) return;
      const snapshot = await phone.getSession(sessionId);
      if (cancelled) return;
      if (snapshot.endedAt) {
        installSession(null);
        return;
      }
      setSession(snapshot);
      sessionRef.current = snapshot;
      const away = movedFrom(snapshot, deviceId);
      if (away) {
        setMoved(away);
        return;
      }
      const pending = pendingSubmit();
      if (pending && pending.sessionId === sessionId) {
        setView({ name: "waiting", submissionId: pending.submissionId, practiceItemId: pending.practiceItemId });
        return;
      }
      const next = await viewOfCheckpoint(snapshot);
      if (!cancelled) setView(next);
    })().catch(reportError);
    return () => {
      cancelled = true;
    };
    // Once per pairing.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // A submit that outlived its screen: the job is still the answer's path to its feedback.
  useEffect(() => {
    if (view.name !== "waiting") return undefined;
    let cancelled = false;
    const { submissionId, practiceItemId } = view;
    const sessionId = sessionRef.current?.sessionId ?? "";
    const pending = pendingSubmit();
    (async () => {
      let attemptId: string | null = null;
      if (pending?.submissionId === submissionId) {
        attemptId = await pollJob<AttemptResultDto>(pending.jobId, () => cancelled).then(
          (result) => result.attemptId,
          (error) => {
            const committed = committedAttempt(error);
            if (committed) return committed;
            throw error;
          }
        );
      } else {
        for (;;) {
          // A lost desktop is no end to the wait: the job runs on, and this finds it after (A4).
          const status = await phone.submissionStatus(submissionId).catch((error: CommandError) => {
            if (error.code === "desktop_offline") return { state: "running" } as const;
            throw error;
          });
          if (status.state === "completed") {
            attemptId = (status.result as AttemptResultDto).attemptId;
            break;
          }
          if (status.state === "recorded" && status.attempt_id) {
            attemptId = status.attempt_id;
            break;
          }
          if (status.state === "failed") throw status.error;
          if (status.state === "unknown") break;
          await new Promise((resolve) => setTimeout(resolve, 2000));
          if (cancelled) return;
        }
      }
      if (cancelled) return;
      rememberPendingSubmit(null);
      if (attemptId) {
        clearQuestionDraft(sessionId, practiceItemId);
        await phone.acknowledge(sessionId, practiceItemId, submissionId).catch(() => undefined);
        setView({ name: "feedback", attemptId, practiceItemId });
      } else {
        setView({ name: "today" });
      }
    })().catch((error) => {
      if (cancelled) return;
      rememberPendingSubmit(null);
      reportError(error);
      setView({ name: "today" });
    });
    return () => {
      cancelled = true;
    };
  }, [reportError, view]);

  // Today's token: a change refetches once, as the desktop's poll does, and re-reads the session.
  const seenRevision = useRef<number | null>(null);
  const pollToday = view.name === "today" && tab === "today";
  const pollRevision = useCallback(() => {
    void phone.queueRevision().then(
      ({ revision }) => {
        const changed = seenRevision.current !== null && seenRevision.current !== revision;
        seenRevision.current = revision;
        const open = sessionRef.current;
        if (!changed || !open) return;
        invalidate({ tags: [TAG.queue] });
        void phone.getSession(open.sessionId).then((snapshot) => {
          const away = movedFrom(snapshot, deviceId);
          if (away) setMoved(away);
        }, reportError);
      },
      (error) => reportError(error)
    );
  }, [deviceId, reportError]);
  useVisibleInterval(pollRevision, REVISION_POLL_MS, pollToday);

  // §7: on open, on focus and every minute while open. iOS has no Background Sync.
  const flushNow = useCallback(
    (): Promise<void> =>
      flushOutbox()
        .then((stop: FlushStop) => {
          if (stop.reason === "offline") markOffline();
          if (stop.reason === "forbidden") setNotice(stop.message);
          return listOutbox();
        })
        .then((records) => setOutboxWaiting(records.filter((one) => !one.problem).length))
        .catch(() => undefined),
    []
  );
  const flush = useCallback(() => void flushNow(), [flushNow]);
  useVisibleInterval(flush, OUTBOX_FLUSH_MS);

  // Mobile v2 §4.4: back from offline, in this order, each step done before the next starts: the
  // outbox, the session (it may have moved meanwhile), the token, and the screen in view. Today
  // refreshes through its token, so nothing refreshes under an answer being typed.
  // The screen in view when the token's turn comes, not when the reconnect began.
  const readTokenIfToday = useRef(() => undefined as void);
  readTokenIfToday.current = () => {
    if (pollToday) pollRevision();
  };
  const reconnect = useRef(async (): Promise<void> => undefined);
  reconnect.current = async () => {
    await flushNow();
    const open = sessionRef.current;
    if (open) {
      await phone.getSession(open.sessionId).then((snapshot) => {
        const away = movedFrom(snapshot, deviceId);
        if (away) setMoved(away);
      }, () => undefined);
    }
    readTokenIfToday.current();
  };
  useEffect(() => onReconnect(() => void reconnect.current()), []);
  useEffect(() => {
    const online = () => flush();
    window.addEventListener("online", online);
    return () => window.removeEventListener("online", online);
  }, [flush]);

  // §5.2: a cached app built against another allowlist says so, on open and on every return.
  useEffect(() => {
    void checkFreshness();
    const onVisible = () => {
      if (document.visibilityState === "visible") void checkFreshness();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => document.removeEventListener("visibilitychange", onVisible);
  }, []);

  // §4.2: the current view, mirrored in the fragment.
  const path = tab === "today" ? todayPath(view) : [];
  const pathKey = path.join("/");
  useEffect(() => {
    writeFragment(tab, pathKey ? pathKey.split("/") : []);
  }, [tab, pathKey]);

  async function begin(minutes: number, replace?: string) {
    setBusy(true);
    setNotice(null);
    setFinished(null);
    try {
      installSession(await phone.startSession(minutes, replace));
      setView({ name: "today" });
    } catch (error) {
      const command = error as CommandError;
      if (command.code === "session_open_elsewhere") setElsewhere({ details: command.details as unknown as OwnerSnapshot, minutes });
      else reportError(error);
    } finally {
      setBusy(false);
    }
  }

  async function adopt(sessionId: string, generation: number): Promise<void> {
    setBusy(true);
    setNotice(null);
    try {
      await phone.adoptSession(sessionId, generation);
      const next = await phone.getSession(sessionId);
      // In one step, so a question open before this never renders under the new owner: the
      // generation in its key remounts it on the checkpoint just read (F4).
      const nextView = await viewOfCheckpoint(next);
      installSession(next);
      setView(nextView);
    } catch (error) {
      const command = error as CommandError;
      if (command.code === "current_item_desktop_only") {
        // §6.5: adopting never loses a draft. It is finished there, or kept on record by a fresh start.
        setNotice("Its open question has an unsent answer that can only be finished on the desktop. Finish it there, or start fresh; starting fresh keeps that answer on record.");
      } else {
        reportError(error);
      }
    } finally {
      setBusy(false);
    }
  }

  /** A row of Today: its draft, if this phone or the checkpoint has one (F5). */
  async function openRow(row: ScheduledItemDto) {
    const open = sessionRef.current;
    const target = targetOf(row);
    if (!open || readQuestionDraft(open.sessionId, row.practiceItemId)) {
      setView({ name: "question", target });
      return;
    }
    let restored: QuestionTarget["restored"] = null;
    try {
      const snapshot = await phone.getSession(open.sessionId);
      const away = movedFrom(snapshot, deviceId);
      if (away) {
        setMoved(away);
        return;
      }
      restored = restoredFrom(snapshot, row.practiceItemId);
    } catch {
      // The question's own load will say what is wrong.
    }
    setView({ name: "question", target: { ...target, restored } });
  }

  async function nextAfter(practiceItemId: string | null) {
    const open = sessionRef.current;
    if (!open) {
      setView({ name: "today" });
      return;
    }
    try {
      const queue = await phone.getTodayQueue(open.sessionId, PHONE_QUEUE_LIMIT, open.availableMinutes);
      setQueryData(queueKey(open.sessionId), queue, [TAG.queue]);
      const rows = queueRows(queue, practiceItemId ? new Set([...held, practiceItemId]) : held);
      const head = rows[0];
      if (head) setView({ name: "question", target: targetOf(head) });
      else setView({ name: "today" });
    } catch (error) {
      reportError(error);
      setView({ name: "today" });
    }
  }

  /** Short of `recorded` the question stays open. Only a typed refusal says the skip didn't happen (F11). */
  async function skip(practiceItemId: string): Promise<SkipOutcome> {
    const open = sessionRef.current;
    if (!open) return "refused";
    try {
      const queue = await phone.skipItem(open.sessionId, practiceItemId);
      clearQuestionDraft(open.sessionId, practiceItemId);
      setQueryData(queueKey(open.sessionId), queue, [TAG.queue]);
      setView({ name: "today" });
      return "recorded";
    } catch (error) {
      if (!refusedOutright(error)) return "unknown";
      reportError(error);
      return "refused";
    }
  }

  /** A skip with no reply: it clears the checkpoint, so what the checkpoint holds says if it landed. */
  async function settleSkip(practiceItemId: string, writtenSince: () => boolean): Promise<SkipSettled> {
    const open = sessionRef.current;
    if (!open) return "unreachable";
    let snapshot: SessionSnapshot;
    try {
      snapshot = await phone.getSession(open.sessionId);
    } catch (error) {
      reportError(error);
      return "unreachable";
    }
    const away = movedFrom(snapshot, deviceId);
    if (away) setMoved(away);
    if (snapshot.checkpoint?.currentPracticeItemId === practiceItemId) return "not_landed";
    invalidate({ tags: [TAG.queue] });
    // Asked only now: the editor stays open during a read that an edit started.
    if (writtenSince()) return "landed_written_since";
    clearQuestionDraft(open.sessionId, practiceItemId);
    setView({ name: "today" });
    return "landed";
  }

  async function endSession() {
    const open = sessionRef.current;
    if (!open) return;
    setBusy(true);
    try {
      const summary = await phone.endSession(open.sessionId);
      installSession(null);
      setFinished(summary);
    } catch (error) {
      reportError(error);
    } finally {
      setBusy(false);
    }
  }

  function leftForDesktop(practiceItemId: string) {
    const nextHeld = new Set([...held, practiceItemId]);
    setHeld(nextHeld);
    void nextAfter(practiceItemId);
  }

  const frozen = moved !== null;
  // §4.2: Question and Feedback (and the wait between them) cover the tab bar, so the primary
  // action owns the bottom. Capture stays one tap away in the top bar, and the practice side stays
  // mounted under it, as M2a's tab did: an open question keeps its editor, its serve and a submit.
  const covering = tab === "today" && view.name !== "today";
  const toCapture: FrameAction = { label: "+", name: "Capture", onClick: () => setTab("capture") };
  const toDisplay: FrameAction = { label: "Aa", name: "Display", onClick: () => setDisplay(true) };
  const frame = covering
    ? view.name === "question"
      ? { title: "Question", onBack: () => setView({ name: "today" }), backDisabled: questionBusy, actions: [toCapture] }
      : { title: view.name === "waiting" ? "Grading" : "Feedback", onBack: null, backDisabled: false, actions: [toCapture] }
    : { title: TABS.find((spec) => spec.tab === tab)?.title ?? "Today", onBack: null, backDisabled: false, actions: [toDisplay] };

  return (
    <div className={covering ? "shell covering" : "shell"}>
      <ScreenFrame
        screenKey={`${tab}:${pathKey}`}
        title={frame.title}
        onBack={frame.onBack}
        backDisabled={frame.backDisabled}
        backName="Back to Today"
        actions={frame.actions}
      >
        <ConnectionLine outboxWaiting={outboxWaiting} />
        {moved ? (
          <div className="banner" role="status">
            {moved.reason === "adopted" ? (
              <>
                <div>This session continued on {moved.ownerLabel ?? "the desktop"}.</div>
                <div className="row">
                  <button className="primary" type="button" disabled={busy} onClick={() => void adopt(moved.sessionId, moved.ownerGeneration ?? 0)}>Take it back</button>
                  <button className="plain" type="button" disabled={busy} onClick={() => void begin(sessionRef.current?.availableMinutes ?? 15, moved.sessionId)}>Start fresh</button>
                </div>
              </>
            ) : (
              <>
                <div>This session ended on another device.</div>
                <div className="row">
                  <button className="primary" type="button" onClick={() => { installSession(null); setView({ name: "today" }); }}>OK</button>
                </div>
              </>
            )}
          </div>
        ) : null}
        {notice ? <div className="banner bad" role="alert" onClick={() => setNotice(null)}>{notice}</div> : null}
        {tab === "capture" ? <CaptureScreen onSaved={flush} /> : null}
        {tab === "read" ? <ReadScreen /> : null}
        {tab === "progress" ? <ProgressScreen /> : null}
        {/* The practice side stays mounted under the other places. */}
        <div style={{ display: tab === "today" ? "contents" : "none" }}>
          {view.name === "question" && session ? (
            <QuestionScreen
              key={`${session.sessionId}:${session.ownerGeneration ?? 0}:${view.target.practiceItemId}`}
              session={session}
              target={view.target}
              frozen={frozen}
              onFeedback={(attemptId, practiceItemId) => setView({ name: "feedback", attemptId, practiceItemId })}
              onWaiting={(submissionId, practiceItemId) => setView({ name: "waiting", submissionId, practiceItemId })}
              onDesktopOnly={leftForDesktop}
              onSkipped={skip}
              onSkipUnknown={settleSkip}
              onBack={() => setView({ name: "today" })}
              onBusy={setQuestionBusy}
              onError={reportError}
            />
          ) : view.name === "waiting" ? (
            <div className="screen"><p className="dim" role="status">Your answer is being graded. The result will be here in a moment.</p></div>
          ) : view.name === "feedback" ? (
            <FeedbackScreen
              key={view.attemptId}
              attemptId={view.attemptId}
              onNext={() => void nextAfter(null)}
              onError={reportError}
            />
          ) : (
            <TodayScreen
              session={session}
              held={held}
              finished={finished}
              busy={busy}
              onBegin={(minutes) => void begin(minutes)}
              onOpen={(row: ScheduledItemDto) => void openRow(row)}
              onEnd={() => void endSession()}
              onError={reportError}
            />
          )}
        </div>
      </ScreenFrame>
      {covering ? null : <TabBar current={tab} onSelect={setTab} />}
      {elsewhere ? (
        <Sheet title="A session is open elsewhere" onClose={() => setElsewhere(null)} closeLabel="Cancel">
          <p>You have a session open on {elsewhere.details.owner_label ?? "the desktop"}.</p>
          {elsewhere.details.has_draft ? (
            <p className="dim">It has an unsent answer{elsewhere.details.draft_first_line ? `: “${elsewhere.details.draft_first_line}”` : "."}</p>
          ) : null}
          <div className="actions">
            <button className="primary block" type="button" disabled={busy} onClick={() => void adopt(elsewhere.details.session_id, elsewhere.details.owner_generation ?? 0)}>Continue it here</button>
            <div className="row">
              <button className="plain" type="button" disabled={busy} onClick={() => void begin(elsewhere.minutes, elsewhere.details.session_id)}>Start fresh</button>
            </div>
          </div>
        </Sheet>
      ) : null}
      {display ? <DisplaySheet onClose={() => setDisplay(false)} /> : null}
    </div>
  );
}

function targetOf(row: ScheduledItemDto): QuestionTarget {
  return { practiceItemId: row.practiceItemId, schedulerCandidateId: row.schedulerCandidateId ?? null };
}
