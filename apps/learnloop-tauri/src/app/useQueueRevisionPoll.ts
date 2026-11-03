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
// The window coming back refetches once whatever the token says (§3.3): it is the
// recovery for a bump that never landed, which no token can show.
//
// What it leaves alone: an open practice answer and an open Reader. While the screen
// is `quiet` a change is remembered and the queue is invalidated once when the learner
// leaves; the App-level plan read would otherwise rebuild on the pipe under their
// typing. Reading the session never touches the App's session or the screen.
//
// session_moved: on a change, and when the window comes back, the open session is
// re-read until a read answers, and a session that left this desktop is noted here. The banner and the
// adopt / start fresh prompts that act on it are M2's (§6.5); a write the desktop
// makes meanwhile is refused by the sidecar with `session_moved`.
import { useEffect, useRef, useSyncExternalStore } from "react";
import { api } from "../api/client";
import type { SessionSnapshot } from "../api/dto";
import { notifyQueueChanged } from "../queueEvents";

/** How often the token is read. A `keep` bound: Today's existing poll, a cheap read, and what §6.5's handoff can feel. */
export const REVISION_POLL_MS = 3000;

export interface SessionMoved {
  readonly sessionId: string;
  /** `adopted`: another device holds it. `ended`: it ended elsewhere (a phone's start fresh). */
  readonly reason: "adopted" | "ended";
  readonly ownerLabel: string | null;
  readonly ownerGeneration: number | null;
}

/** How a re-read session differs from the one this desktop has open; null when it is still ours. */
export function sessionMovedFrom(snapshot: SessionSnapshot): SessionMoved | null {
  const ownership = { ownerLabel: snapshot.ownerLabel ?? null, ownerGeneration: snapshot.ownerGeneration ?? null };
  if (snapshot.ownerDeviceId) return { sessionId: snapshot.sessionId, reason: "adopted", ...ownership };
  if (snapshot.endedAt) return { sessionId: snapshot.sessionId, reason: "ended", ...ownership };
  return null;
}

let moved: SessionMoved | null = null;
const movedListeners = new Set<() => void>();

function setSessionMoved(next: SessionMoved | null): void {
  if (moved === next || (moved !== null && next !== null && JSON.stringify(moved) === JSON.stringify(next))) return;
  moved = next;
  for (const listener of movedListeners) listener();
}

function subscribeSessionMoved(listener: () => void): () => void {
  movedListeners.add(listener);
  return () => movedListeners.delete(listener);
}

/** The open session's move, if the desktop has seen one. M2's banner reads this. */
export function useSessionMoved(): SessionMoved | null {
  return useSyncExternalStore(subscribeSessionMoved, () => moved);
}

export interface QueueRevisionPollOptions {
  /** The open vault; null polls nothing, and a new one starts from a fresh token. */
  readonly vaultRoot: string | null;
  /** The session this desktop has open. */
  readonly sessionId: string | null;
  /** A practice answer or the Reader is open: remember changes, refetch on leaving. */
  readonly quiet: boolean;
}

export function useQueueRevisionPoll({ vaultRoot, sessionId, quiet }: QueueRevisionPollOptions): void {
  const sessionIdRef = useRef(sessionId);
  sessionIdRef.current = sessionId;
  const quietRef = useRef(quiet);
  quietRef.current = quiet;
  const pendingRef = useRef(false);

  useEffect(() => {
    // A move belongs to the session it was seen on.
    setSessionMoved(null);
  }, [sessionId, vaultRoot]);

  useEffect(() => {
    if (!vaultRoot) return undefined;
    let disposed = false;
    let inFlight = false;
    let seen: number | null = null;
    // The window came back: one refetch owed at any token, kept until a token read answers.
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
      try {
        const snapshot = await api.getQueueRevision();
        if (disposed) return;
        answered = true;
        // Read after the await, so a focus and a visibilitychange that arrive
        // together during this read are one return, and one refetch.
        const back = windowBack;
        windowBack = false;
        const changed = seen !== null && seen !== snapshot.revision;
        seen = snapshot.revision;
        if (changed || snapshot.reloaded || back) {
          if (quietRef.current) pendingRef.current = true;
          else notifyQueueChanged();
        }
        if (changed || back) sessionReadOwed = true;
        if (sessionReadOwed && (await readOpenSession())) sessionReadOwed = false;
      } catch {
        /* transient poll failure: try again next tick */
      } finally {
        inFlight = false;
      }
      if (answered && windowBack && !disposed) void tick();
    };

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
      pendingRef.current = false;
      window.clearInterval(interval);
      window.removeEventListener("focus", onWindowBack);
      document.removeEventListener("visibilitychange", onWindowBack);
    };
  }, [vaultRoot]);

  useEffect(() => {
    if (quiet || !pendingRef.current) return;
    pendingRef.current = false;
    notifyQueueChanged();
  }, [quiet]);
}
