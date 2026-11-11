// Mobile PR-7 (spec_mobile_tailnet_v1 §3.3, §6.5): the desktop's freshness, at app level.
//
// The phone host bumps `queue_revision` after each committed mutation that changes
// what the desktop shows, so this one token says when a cached read is out of date,
// on every screen, not only while Today is mounted. It replaces Today's own poll.
//
// What a tick costs: one `get_queue_revision`. Nothing else runs until the revision
// changes or the read itself reloaded the vault, so an idle desktop never refetches
// Today. It never holds a second call behind the serialized sidecar pipe.
//
// The window coming back reads the token and the session at once and refetches nothing
// on its own (orchestrator ruling R1): a rebuild per alt-tab can start background model
// work and writes offer and decision rows for lists nobody looked at. A refetch needs a
// revision change or a reload. A bump that never landed stays owed in the host, whose
// next request pays it.
//
// Where it refetches and reloads (ruling R2): only on Today's list, with nothing over it
// (`revisionPollHeld`), on the classic Today and on the simple shell's Today and Start. Main's
// only poller was the classic Today, so the simple shell's freshness is new, on purpose
// (ruling R5): a real revision change or a completed reload job refreshes it, and an idle
// token rebuilds nothing. Everywhere else the screen is
// `quiet`: the token is still read, asking the sidecar not to reload now, a change is
// remembered, and on the return to Today one read reloads whatever is owed and one
// refetch pays for it all. The App-level plan read would otherwise rebuild on the pipe
// under an answer being typed, and start work for a list nobody is looking at. Reading
// the session never touches the App's session or the screen.
//
// session_moved: on a change, and when the window comes back, on every screen, the open
// session is re-read until a read answers, and a session that left this desktop is noted
// (`sessionMoved.ts`), which is what the banner reads (§6.5). A write the desktop makes
// meanwhile is refused by the sidecar with `session_moved`, which notes it too.
//
// M2a settled whether a phone needs R2's hold widened: it does not (docs/reviews/mobile-m2a.md).
// A phone's change reaches Today's list on the next tick there, and otherwise once, on the
// return to it, with no rebuild per return; the move itself is seen on every screen.
import { useEffect, useRef, useSyncExternalStore } from "react";
import { api } from "../api/client";
import type { SessionSnapshot } from "../api/dto";
import { notifyQueueChanged } from "../queueEvents";
import { sessionMovedFrom, setSessionMoved } from "./sessionMoved";

/** How often the token is read. A `keep` bound: Today's existing poll, a cheap read, and what §6.5's handoff can feel. */
export const REVISION_POLL_MS = 3000;

export { sessionMovedFrom, useSessionMoved, type SessionMoved } from "./sessionMoved";

/** What decides whether a refetch or a reload may run now (ruling R2). */
export interface RevisionPollView {
  readonly tab: string;
  readonly todayStage: string;
  /** The simple shell, whose Start is Today with no session. */
  readonly simple: boolean;
  readonly examOpen: boolean;
  readonly calibrationOpen: boolean;
  readonly lessonOpen: boolean;
}

/**
 * Whether the poll holds its refetches and reloads: anywhere but Today's list (ruling R2).
 * Feedback and block review replace the list on the Today tab. A command overlay (Ask, Settings, the inspector) sits over a list
 * that stays mounted, so it does not hold.
 */
export function revisionPollHeld(view: RevisionPollView): boolean {
  const onToday = view.tab === "today" || (view.simple && view.tab === "start");
  const overToday = view.examOpen || view.calibrationOpen || view.lessonOpen;
  return !onToday || view.todayStage !== "queue" || overToday;
}

export interface QueueRevisionPollOptions {
  /** The open vault; null polls nothing, and a new one starts from a fresh token. */
  readonly vaultRoot: string | null;
  /** The session this desktop has open. */
  readonly sessionId: string | null;
  /** The snapshot it opened with: a session a phone holds at load is a move already. */
  readonly openedSession?: SessionSnapshot | null;
  /** `revisionPollHeld`: no reload and no refetch now; both are paid when this lifts. */
  readonly quiet: boolean;
}

export function useQueueRevisionPoll({ vaultRoot, sessionId, openedSession, quiet }: QueueRevisionPollOptions): void {
  const sessionIdRef = useRef(sessionId);
  sessionIdRef.current = sessionId;
  const quietRef = useRef(quiet);
  quietRef.current = quiet;
  const pendingRef = useRef(false);
  const tickRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    // A move belongs to the session it was seen on.
    setSessionMoved(openedSession?.sessionId === sessionId && openedSession ? sessionMovedFrom(openedSession) : null);
    // Keyed on the id: a later snapshot of the same session is the poll's to read.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, vaultRoot]);

  useEffect(() => {
    if (!vaultRoot) return undefined;
    let disposed = false;
    let inFlight = false;
    let seen: number | null = null;
    // The window came back: one session read owed, kept until a token read answers.
    let windowBack = false;
    // A session read owed by a change or a return. Kept until one answers: the change that
    // owed it is already in `seen`, so no later tick would ask again.
    let sessionReadOwed = false;

    /** Whether it answered for the session still open. A failed read says nothing about who holds it. */
    const readOpenSession = async (): Promise<boolean> => {
      const id = sessionIdRef.current;
      if (!id) return true;
      try {
        const snapshot = await api.getSession(id);
        if (disposed) return true;
        if (sessionIdRef.current !== id) return false;
        setSessionMoved(sessionMovedFrom(snapshot));
        return true;
      } catch {
        return false;
      }
    };

    const tick = async () => {
      // One call at a time: a tick behind a long grade waits on the pipe, and the
      // ones after it have nothing to add. A failure waits for the next interval.
      if (inFlight || disposed) return;
      inFlight = true;
      let answered = false;
      const heldRead = quietRef.current;
      try {
        const snapshot = await api.getQueueRevision(heldRead ? { holdReload: true } : {});
        if (disposed) return;
        answered = true;
        // Read after the await, so a focus and a visibilitychange that arrive
        // together during this read are one return, and one session read.
        const back = windowBack;
        windowBack = false;
        const changed = seen !== null && seen !== snapshot.revision;
        seen = snapshot.revision;
        if (changed || snapshot.reloaded) pendingRef.current = true;
        // Only a read that was free to reload pays: otherwise the refetch would run on a
        // vault still owing a reload, and that reload would ask for a second one.
        if (pendingRef.current && !heldRead && !quietRef.current) {
          pendingRef.current = false;
          notifyQueueChanged();
        }
        if (changed || back) sessionReadOwed = true;
        if (sessionReadOwed && (await readOpenSession())) sessionReadOwed = false;
      } catch {
        /* transient poll failure: try again next tick */
      } finally {
        inFlight = false;
      }
      // A return during this read, or a hold that lifted during a read that was held.
      if (answered && !disposed && (windowBack || (heldRead && !quietRef.current))) void tick();
    };
    tickRef.current = () => void tick();

    const onWindowBack = () => {
      if (document.visibilityState === "hidden") return;
      windowBack = true;
      void tick();
    };
    void tick();
    // A hidden window has nobody to refresh for; coming back reads at once.
    const interval = window.setInterval(() => {
      if (document.visibilityState !== "hidden") void tick();
    }, REVISION_POLL_MS);
    window.addEventListener("focus", onWindowBack);
    document.addEventListener("visibilitychange", onWindowBack);
    return () => {
      disposed = true;
      tickRef.current = null;
      pendingRef.current = false;
      window.clearInterval(interval);
      window.removeEventListener("focus", onWindowBack);
      document.removeEventListener("visibilitychange", onWindowBack);
    };
  }, [vaultRoot]);

  // The hold lifted: read now, free to reload, and pay what was remembered once.
  const wasQuietRef = useRef(quiet);
  useEffect(() => {
    const wasQuiet = wasQuietRef.current;
    wasQuietRef.current = quiet;
    if (wasQuiet && !quiet) tickRef.current?.();
  }, [quiet]);
}
