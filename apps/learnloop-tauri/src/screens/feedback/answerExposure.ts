// UX Phase 4 (Codex review F1, re-review F1, final verification F1): the full
// answer on feedback is an exposure, charged to the reveal ledger.
//
// A routine display counts only within the cold retrieval delay (one day) of
// the row that records it (`reveal_ledger.ROUTINE_ANSWER_DISPLAY_HORIZON`). So
// the ledger must hold a row no older than the last time the learner could
// read the answer, not just one from when the screen first showed it:
//
// * An exposure starts whenever the answer comes (back) on screen: the screen
//   mounts with it, the document becomes visible again, the window regains
//   focus, the page is shown or resumed, or an overlay over it closes. Each
//   start is a new display id, so a new row stamped then.
// * While it stays on screen it is renewed at least hourly (a new display id),
//   well inside the delay, so an answer left open for days never lapses.
//   The check runs on wall-clock time, so a machine that slept with the answer
//   open renews within a minute of waking.
// * When it leaves the screen (hidden, covered, the screen unmounted) after
//   more than a minute, a closing row is written, so the delay runs from the
//   last moment the answer was on screen. A retry or unaided attempt started
//   from feedback therefore always follows a row at most a minute old.
// * Within a minute of the latest row nothing new is written (that row already
//   covers the moment), and a write that failed is retried under the SAME
//   display id until it is confirmed: the sidecar records each id once.
//
// Every row is amount 1.0. Auto-prime compares the total against a threshold
// one row already crosses, so renewals change no `primed`; the receipts that
// sum amounts (the router's coldness covariates, the cold-task deferral) count
// each renewal, as they already counted each visit.

import { useEffect, useRef, useState } from "react";

/** Renew an exposure still on screen at least this often (well inside the one-day delay). */
export const EXPOSURE_RENEW_MS = 60 * 60 * 1000;
/** A row this recent already covers the answer coming back or leaving. */
export const EXPOSURE_FRESH_MS = 60 * 1000;
/** How often the open screen checks its exposure (wall clock). */
export const EXPOSURE_TICK_MS = 60 * 1000;

type RecordDisplay = (attemptId: string, displayId: string) => Promise<unknown>;

interface Exposure {
  attemptId: string;
  id: string;
  stampedAt: number;
  confirmed: boolean;
  sending: boolean;
}

function newDisplayId(): string {
  const random = globalThis.crypto?.randomUUID?.();
  return `display_${random ?? `${Date.now().toString(36)}${Math.random().toString(36).slice(2)}`}`;
}

/** The exposure bookkeeping, apart from React (one per mounted feedback surface). */
export class AnswerExposure {
  private current: Exposure | null = null;

  constructor(private readonly record: RecordDisplay, private readonly now: () => number = () => Date.now()) {}

  /** The answer came (back) on screen: a new exposure unless the latest row is fresh. */
  show(attemptId: string): void {
    this.refresh(attemptId, EXPOSURE_FRESH_MS);
  }

  /** The answer is still on screen: renew a stale exposure, retry an unconfirmed one. */
  tick(attemptId: string): void {
    this.refresh(attemptId, EXPOSURE_RENEW_MS);
  }

  /** The answer left the screen: close the exposure with a row stamped now, unless the latest is fresh. */
  end(): void {
    const current = this.current;
    if (current === null) return;
    if (this.now() - current.stampedAt >= EXPOSURE_FRESH_MS) this.open(current.attemptId);
    else this.send(current);
  }

  private refresh(attemptId: string, staleAfter: number): void {
    const current = this.current;
    if (current === null || current.attemptId !== attemptId || this.now() - current.stampedAt >= staleAfter) {
      this.open(attemptId);
    } else {
      this.send(current);
    }
  }

  private open(attemptId: string): void {
    const exposure: Exposure = { attemptId, id: newDisplayId(), stampedAt: this.now(), confirmed: false, sending: false };
    this.current = exposure;
    this.send(exposure);
  }

  private send(exposure: Exposure): void {
    if (exposure.confirmed || exposure.sending) return;
    exposure.sending = true;
    // Best effort, like every ledger write: the screen never waits on it. A
    // failure is retried under the same id on the next tick, show or end.
    this.record(exposure.attemptId, exposure.id)
      .then(() => {
        exposure.confirmed = true;
      })
      .catch(() => undefined)
      .finally(() => {
        exposure.sending = false;
      });
  }
}

function documentVisible(): boolean {
  return typeof document === "undefined" || document.visibilityState !== "hidden";
}

/** Keep the reveal ledger charged for as long as the full answer is on screen. */
export function useAnswerExposure(attemptId: string, onScreen: boolean, record: RecordDisplay | undefined): void {
  const recordRef = useRef(record);
  recordRef.current = record;
  const exposure = useRef<AnswerExposure | null>(null);
  if (exposure.current === null) {
    exposure.current = new AnswerExposure((attempt, displayId) =>
      recordRef.current ? recordRef.current(attempt, displayId) : Promise.resolve()
    );
  }
  const [visible, setVisible] = useState(documentVisible);
  useEffect(() => {
    const onVisibility = () => setVisible(documentVisible());
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, []);
  const shown = onScreen && visible && record !== undefined;
  useEffect(() => {
    if (!shown) return;
    const tracker = exposure.current!;
    tracker.show(attemptId);
    const again = () => {
      if (documentVisible()) tracker.show(attemptId);
    };
    const away = () => tracker.end();
    const timer = window.setInterval(() => tracker.tick(attemptId), EXPOSURE_TICK_MS);
    window.addEventListener("focus", again);
    window.addEventListener("pageshow", again);
    window.addEventListener("pagehide", away);
    document.addEventListener("resume", again);
    document.addEventListener("freeze", away);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("focus", again);
      window.removeEventListener("pageshow", again);
      window.removeEventListener("pagehide", away);
      document.removeEventListener("resume", again);
      document.removeEventListener("freeze", away);
      tracker.end();
    };
  }, [attemptId, shown]);
}
