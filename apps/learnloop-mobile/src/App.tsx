import { useCallback, useEffect, useRef, useState } from "react";
import type { AttemptResultDto, CommandError, ScheduledItemDto, SessionEndSummary, SessionSnapshot } from "@desktop/api/dto";
import { invalidate, setQueryData, clear as clearQueries } from "@desktop/api/queryCache";
import { TAG } from "@desktop/api/queryTags";
import { pollJob } from "./api/http";
import { phone, type OwnerSnapshot } from "./api/phone";
import { useVisibleInterval } from "./util/useVisibleInterval";
import { CaptureScreen } from "./screens/CaptureScreen";
import { FeedbackScreen } from "./screens/FeedbackScreen";
import { PairScreen } from "./screens/PairScreen";
import { QuestionScreen, type QuestionTarget } from "./screens/QuestionScreen";
import { PHONE_QUEUE_LIMIT, queueKey, queueRows, TodayScreen } from "./screens/TodayScreen";
import { readCredential, subscribeCredential, type Credential } from "./store/credential";
import { flushOutbox, listOutbox, type FlushStop } from "./store/outbox";
import { cachedSessionId, cacheSessionId, pendingSubmit, rememberPendingSubmit } from "./store/sessionCache";

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
  const [waiting, setWaiting] = useState(0);
  useEffect(() => {
    if (credential === null) void listOutbox().then((records) => setWaiting(records.filter((one) => !one.problem).length));
  }, [credential]);
  if (credential === undefined) return null;
  if (credential === null) return <PairScreen waiting={waiting} />;
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

function Phone({ credential }: { credential: Credential }) {
  const [tab, setTab] = useState<"today" | "capture">("today");
  const [view, setView] = useState<View>({ name: "today" });
  const [session, setSession] = useState<SessionSnapshot | null>(null);
  const [moved, setMoved] = useState<Moved | null>(null);
  const [elsewhere, setElsewhere] = useState<Elsewhere | null>(null);
  const [offline, setOffline] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [finished, setFinished] = useState<SessionEndSummary | null>(null);
  const [outboxWaiting, setOutboxWaiting] = useState(0);
  // Diagnostic checks this session left for the desktop: not offered again from this list (§6.4).
  const [held, setHeld] = useState<ReadonlySet<string>>(() => new Set());
  const sessionRef = useRef(session);
  sessionRef.current = session;
  const deviceId = credential.deviceId;

  const reportError = useCallback((error: unknown) => {
    const command = error as CommandError;
    if (command?.code === "desktop_offline") {
      setOffline(true);
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
    setNotice(command?.message ?? "Something went wrong.");
  }, []);

  const installSession = useCallback((next: SessionSnapshot | null) => {
    sessionRef.current = next;
    setSession(next);
    cacheSessionId(next ? next.sessionId : null);
    setMoved(null);
    setElsewhere(null);
    setHeld(new Set());
    clearQueries();
  }, []);

  /** §6.5, a checkpoint that carries a submission id: finished, under way, or a draft. */
  const resumeCheckpoint = useCallback(async (next: SessionSnapshot) => {
    const checkpoint = next.checkpoint;
    const itemId = checkpoint?.currentPracticeItemId ?? null;
    if (!checkpoint || !itemId) {
      setView({ name: "today" });
      return;
    }
    const restored = { answer: checkpoint.currentAnswer ?? "", submissionId: checkpoint.submissionId, stuck: checkpoint.declaredStuck === true };
    if (checkpoint.submissionId) {
      const status = await phone.submissionStatus(checkpoint.submissionId);
      if (status.state === "completed") {
        const result = status.result as AttemptResultDto;
        await phone.acknowledge(next.sessionId, itemId, checkpoint.submissionId).catch(() => undefined);
        setView({ name: "feedback", attemptId: result.attemptId, practiceItemId: itemId });
        return;
      }
      if (status.state === "accepted" || status.state === "running") {
        setView({ name: "waiting", submissionId: checkpoint.submissionId, practiceItemId: itemId });
        return;
      }
    }
    if (restored.answer.trim()) setView({ name: "question", target: { practiceItemId: itemId, schedulerCandidateId: null, restored } });
    else setView({ name: "today" });
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
      await resumeCheckpoint(snapshot);
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
      let result: AttemptResultDto | null = null;
      if (pending?.submissionId === submissionId) {
        result = await pollJob<AttemptResultDto>(pending.jobId, () => cancelled);
      } else {
        for (;;) {
          const status = await phone.submissionStatus(submissionId);
          if (status.state === "completed") {
            result = status.result as AttemptResultDto;
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
      if (result) {
        await phone.acknowledge(sessionId, practiceItemId, submissionId).catch(() => undefined);
        setView({ name: "feedback", attemptId: result.attemptId, practiceItemId });
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
  useVisibleInterval(() => {
    void phone.queueRevision().then(
      ({ revision }) => {
        setOffline(false);
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
  }, REVISION_POLL_MS, pollToday);

  // §7: on open, on focus and every minute while open. iOS has no Background Sync.
  const flush = useCallback(() => {
    void flushOutbox()
      .then((stop: FlushStop) => {
        if (stop.reason === "offline") setOffline(true);
        if (stop.reason === "forbidden") setNotice(stop.message);
        return listOutbox();
      })
      .then((records) => setOutboxWaiting(records.filter((one) => !one.problem).length))
      .catch(() => undefined);
  }, []);
  useVisibleInterval(flush, OUTBOX_FLUSH_MS);

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
      installSession(next);
      await resumeCheckpoint(next);
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

  async function nextAfter(practiceItemId: string | null) {
    const open = sessionRef.current;
    if (!open) {
      setView({ name: "today" });
      return;
    }
    try {
      const queue = await phone.getTodayQueue(open.sessionId, PHONE_QUEUE_LIMIT);
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

  async function skip(practiceItemId: string) {
    const open = sessionRef.current;
    if (!open) return;
    try {
      const queue = await phone.skipItem(open.sessionId, practiceItemId);
      setQueryData(queueKey(open.sessionId), queue, [TAG.queue]);
      setView({ name: "today" });
    } catch (error) {
      reportError(error);
    }
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
  return (
    <div className="shell">
      {offline ? (
        <div className="banner" role="status">
          Desktop offline.{outboxWaiting > 0 ? ` ${outboxWaiting} ${outboxWaiting === 1 ? "capture" : "captures"} waiting to send.` : " Captures are saved and sent when it wakes."}
        </div>
      ) : null}
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
      {elsewhere ? (
        <div className="banner" role="dialog" aria-label="A session is open elsewhere">
          <div>You have a session open on {elsewhere.details.owner_label ?? "the desktop"}.</div>
          {elsewhere.details.has_draft ? (
            <div className="dim">It has an unsent answer{elsewhere.details.draft_first_line ? `: “${elsewhere.details.draft_first_line}”` : "."}</div>
          ) : null}
          <div className="row">
            <button className="primary" type="button" disabled={busy} onClick={() => void adopt(elsewhere.details.session_id, elsewhere.details.owner_generation ?? 0)}>Continue it here</button>
            <button className="plain" type="button" disabled={busy} onClick={() => void begin(elsewhere.minutes, elsewhere.details.session_id)}>Start fresh</button>
            <button className="plain" type="button" onClick={() => setElsewhere(null)}>Cancel</button>
          </div>
        </div>
      ) : null}
      {notice ? <div className="banner bad" role="alert" onClick={() => setNotice(null)}>{notice}</div> : null}
      {tab === "capture" ? (
        <CaptureScreen onSaved={flush} />
      ) : view.name === "question" && session ? (
        <QuestionScreen
          key={`${session.sessionId}:${view.target.practiceItemId}`}
          session={session}
          target={view.target}
          frozen={frozen}
          onFeedback={(attemptId, practiceItemId) => setView({ name: "feedback", attemptId, practiceItemId })}
          onDesktopOnly={leftForDesktop}
          onSkipped={(practiceItemId) => void skip(practiceItemId)}
          onBack={() => setView({ name: "today" })}
          onError={reportError}
        />
      ) : view.name === "waiting" ? (
        <div className="main"><p className="dim" role="status">Your answer is being graded. The result will be here in a moment.</p></div>
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
          onOpen={(row: ScheduledItemDto) => setView({ name: "question", target: targetOf(row) })}
          onEnd={() => void endSession()}
          onError={reportError}
        />
      )}
      <nav className="tabs">
        <button type="button" aria-current={tab === "today" ? "page" : undefined} onClick={() => setTab("today")}>Today</button>
        <button type="button" aria-current={tab === "capture" ? "page" : undefined} onClick={() => setTab("capture")}>Capture</button>
      </nav>
    </div>
  );
}

function targetOf(row: ScheduledItemDto): QuestionTarget {
  return { practiceItemId: row.practiceItemId, schedulerCandidateId: row.schedulerCandidateId ?? null };
}
