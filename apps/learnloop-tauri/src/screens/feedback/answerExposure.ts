// UX Phase 4 (Codex review F1, re-review F1, final verification F1, round 3):
// a routine full answer (feedback's "A full answer", the plain self-grade's
// key) is an exposure, and the screen shows it only while the reveal ledger
// already holds a committed row that covers it.
//
// The invariant (docs/reviews/ux-phase4-feedback-codex-review.md §9): for any
// attempt or admissibility read at T, if the answer was on screen in any
// window at a moment v in [T - D, T], a committed row the reader counts at T
// exists. It is two properties:
//
// * the readers count a routine row stamped s at every T in [s, s + D + G]
//   (`reveal_ledger.ROUTINE_ANSWER_DISPLAY_COVERAGE`; G is the renewal grace);
// * this gate: the answer is on screen at v only while a committed row stamped
//   s <= v with v < s + G - margin exists (`AnswerExposureGate.covered`).
//
// Together: s <= v <= T and T <= v + D < s + G + D. The gate needs no closing
// row and no flush before an action: whatever ends the screen (a crash, a
// kill, navigating to an attempt), the row that made the answer visible
// already covers the next D. A machine that slept with the answer open shows
// its last frame until the page's first check after waking (one tick at
// most), which hides it until a new row is committed.
//
// Rows are written, each under a new display id:
// * before the answer first appears, and whenever it is wanted again after its
//   row stopped covering it (the document visible again, an overlay closed,
//   the machine awake again);
// * every `renewAfterMs` while it stays on screen AND the learner is present
//   (input, focus, the page shown, since the last row). An unattended screen
//   lets its row lapse and hides the answer ("away") until the learner is
//   back, so an open window writes nothing more while nobody uses it.
// A write that fails is retried under the same display id until it lands (the
// sidecar records each id once and says when); a refused one stops.

import { useCallback, useEffect, useRef, useState } from "react";
import contract from "./exposureContract.json";

/** The numbers the screen and the readers share (a test pins them equal). */
export const EXPOSURE = contract as {
  horizonMs: number;
  renewalGraceMs: number;
  showMarginMs: number;
  renewAfterMs: number;
  tickMs: number;
};

/** What the ledger says about one display row (`record_answer_display`). */
export interface DisplayReceipt {
  recordedAt?: string | null;
  alreadyRecorded?: boolean;
}

export type RecordDisplay = (displayId: string) => Promise<DisplayReceipt | unknown>;

export type ExposureStatus = "shown" | "waiting" | "away" | "unavailable";

interface Row {
  id: string;
  /** The row's stamp (the sidecar's, floored to the second). */
  stampMs: number;
  /** When this display id was first sent (client clock). */
  sentMs: number;
}

interface Pending {
  id: string;
  firstSentMs: number;
  sending: boolean;
  failures: number;
}

function newDisplayId(): string {
  const random = globalThis.crypto?.randomUUID?.();
  return `display_${random ?? `${Date.now().toString(36)}${Math.random().toString(36).slice(2)}`}`;
}

function refused(error: unknown): boolean {
  return Boolean(error && typeof error === "object" && (error as { retryable?: unknown }).retryable === false);
}

/** The gate for one answer on one screen (the clock and the writer are injected). */
export class AnswerExposureGate {
  private latest: Row | null = null;
  private pending: Pending | null = null;
  private activityMs: number;
  private lastCheckMs: number | null = null;
  private stopped = false;

  constructor(
    private readonly record: RecordDisplay,
    private readonly now: () => number = () => Date.now(),
    private readonly onChange: () => void = () => undefined
  ) {
    this.activityMs = now();
  }

  /** A committed row covers the answer being on screen at `at`. */
  covered(at: number = this.now()): boolean {
    return this.latest !== null && at < this.latest.stampMs + EXPOSURE.renewalGraceMs - EXPOSURE.showMarginMs;
  }

  /** The learner is here: input, focus, the page shown, the answer asked for. */
  activity(): void {
    this.activityMs = this.now();
  }

  /** The learner was present since the latest row was sent. */
  private present(): boolean {
    return this.latest === null || this.activityMs > this.latest.sentMs;
  }

  /** One check while the answer is wanted on screen (`wanted` false: it is
   *  not, so nothing is written). Starts the write a row needs; returns
   *  whether the answer may be on screen now. */
  check(wanted: boolean): boolean {
    const at = this.now();
    // A check long after the last one is the machine waking (no timer ran
    // while it slept): a return, like the page shown again.
    if (this.lastCheckMs !== null && at - this.lastCheckMs > 3 * EXPOSURE.tickMs) this.activityMs = at;
    this.lastCheckMs = at;
    if (!wanted || this.stopped) return false;
    const covered = this.covered(at);
    const due = !covered || at - (this.latest?.sentMs ?? Number.NEGATIVE_INFINITY) >= EXPOSURE.renewAfterMs;
    if (due && this.present()) this.write(at);
    return covered;
  }

  status(): ExposureStatus {
    if (this.covered()) return "shown";
    if (this.stopped) return "unavailable";
    if (!this.present()) return "away";
    return (this.pending?.failures ?? 0) > 0 ? "unavailable" : "waiting";
  }

  private write(at: number): void {
    const pending = this.pending ?? { id: newDisplayId(), firstSentMs: at, sending: false, failures: 0 };
    this.pending = pending;
    if (pending.sending) return;
    pending.sending = true;
    let call: Promise<unknown>;
    try {
      call = Promise.resolve(this.record(pending.id));
    } catch (error) {
      call = Promise.reject(error);
    }
    call
      .then((receipt) => {
        const stampMs = this.stampOf(receipt, pending.firstSentMs);
        if (this.latest === null || stampMs >= this.latest.stampMs) {
          this.latest = { id: pending.id, stampMs, sentMs: pending.firstSentMs };
        }
        if (this.pending === pending) this.pending = null;
      })
      .catch((error: unknown) => {
        pending.failures += 1;
        // Refused (the self-grade's draft is done with): stop; the answer stays hidden.
        if (refused(error)) this.stopped = true;
      })
      .finally(() => {
        pending.sending = false;
        this.onChange();
      });
  }

  /** The row's stamp: the sidecar's, never later than now on this clock.
   *  Without one (an older sidecar), the id's first send: the row was written
   *  no earlier, so its grace ends no earlier than this says. */
  private stampOf(receipt: unknown, fallbackMs: number): number {
    const at = receipt && typeof receipt === "object" ? (receipt as DisplayReceipt).recordedAt : null;
    const parsed = typeof at === "string" ? Date.parse(at) : Number.NaN;
    return Number.isFinite(parsed) ? Math.min(parsed, this.now()) : fallbackMs;
  }
}

function documentVisible(): boolean {
  return typeof document === "undefined" || document.visibilityState !== "hidden";
}

const PRESENCE_EVENTS = ["pointerdown", "pointermove", "keydown", "wheel", "touchstart"] as const;

/** Gate a routine full answer on its ledger rows. `key` names the answer (a
 *  new key is a new gate); `onScreen` is whether the screen would show it now
 *  (rendered, not covered by an overlay). Returns whether it may be shown,
 *  its status, and `show()` for the learner asking for it after "away". */
export function useAnswerExposure(
  key: string,
  onScreen: boolean,
  record: RecordDisplay | undefined
): { shown: boolean; status: ExposureStatus; show: () => void } {
  const recordRef = useRef(record);
  recordRef.current = record;
  const [, setVersion] = useState(0);
  const bump = useCallback(() => setVersion((value) => value + 1), []);
  const gates = useRef<{ key: string; gate: AnswerExposureGate } | null>(null);
  if (gates.current === null || gates.current.key !== key) {
    gates.current = {
      key,
      gate: new AnswerExposureGate(
        (displayId) => (recordRef.current ? recordRef.current(displayId) : Promise.reject(new Error("no writer"))),
        () => Date.now(),
        bump
      )
    };
  }
  const gate = gates.current.gate;
  const [visible, setVisible] = useState(documentVisible);
  const wanted = onScreen && visible && record !== undefined;
  const wantedRef = useRef(wanted);
  wantedRef.current = wanted;

  useEffect(() => {
    const onVisibility = () => {
      const isVisible = documentVisible();
      if (isVisible) gate.activity();
      setVisible(isVisible);
    };
    const back = () => {
      gate.activity();
      gate.check(wantedRef.current);
      bump();
    };
    const present = () => {
      gate.activity();
      // Back after "away": write at once rather than at the next tick.
      if (wantedRef.current && !gate.covered()) {
        gate.check(true);
        bump();
      }
    };
    document.addEventListener("visibilitychange", onVisibility);
    document.addEventListener("resume", back);
    window.addEventListener("focus", back);
    window.addEventListener("pageshow", back);
    for (const name of PRESENCE_EVENTS) window.addEventListener(name, present, { passive: true });
    // The wall clock, every tick: a renewal that is due, a retry, and the
    // answer hidden once its row stops covering it (also after a sleep).
    const timer = window.setInterval(() => {
      gate.check(wantedRef.current);
      bump();
    }, EXPOSURE.tickMs);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisibility);
      document.removeEventListener("resume", back);
      window.removeEventListener("focus", back);
      window.removeEventListener("pageshow", back);
      for (const name of PRESENCE_EVENTS) window.removeEventListener(name, present);
    };
  }, [gate, bump]);

  // The answer becoming wanted again (mounted, an overlay closed, the
  // document visible again) is the learner returning to it: it writes at once
  // when no row covers it.
  useEffect(() => {
    if (!wanted) return;
    gate.activity();
    gate.check(true);
  }, [gate, wanted]);

  const show = useCallback(() => {
    gate.activity();
    gate.check(wantedRef.current);
    bump();
  }, [gate, bump]);
  // Rendering reads the gate only: the answer is on screen while covered.
  return { shown: wanted && gate.covered(), status: gate.status(), show };
}
