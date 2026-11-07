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
// already covers the next D.
//
// Round 4: every signal that may precede a suspend or a loss of attention
// (the document hidden, pagehide, freeze, window blur, and, round 5, every
// shell window resize, scale change or focus change, before its state is
// even asked) hides the answer synchronously, and it shows again only after a
// fresh row is acknowledged (for a shell event, once the window is known
// visible and unminimized); so does a clock discontinuity (the wall clock
// going back, or a check long after the last one: a wake). The residual: an
// OS suspend that delivers none of those signals keeps the last frame on
// screen until the page's first check after waking (one tick).
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
import { flushSync } from "react-dom";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { AnswerExposureGate, EXPOSURE, type ExposureStatus, type RecordDisplay } from "./answerExposureGate";

export { AnswerExposureGate, EXPOSURE };
export type { DisplayReceipt, ExposureStatus, RecordDisplay } from "./answerExposureGate";


function documentVisible(): boolean {
  return typeof document === "undefined" || document.visibilityState !== "hidden";
}

const PRESENCE_EVENTS = ["pointerdown", "pointermove", "keydown", "wheel", "touchstart"] as const;

/** How long the shell's window events settle before its state is asked (a
 *  drag resize sends many; the answer stays hidden meanwhile). */
const SHELL_SETTLE_MS = 300;

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
  // A shell window event is pending its state query: nothing shows, nothing
  // is written, until the shell says the window is visible and unminimized.
  // The hold belongs to the window, not to one answer: a new key keeps it and
  // asks the shell again (round 6, G).
  const [shellHeld, setShellHeld] = useState(false);
  const shellHeldRef = useRef(shellHeld);
  shellHeldRef.current = shellHeld;
  const wanted = onScreen && visible && !shellHeld && record !== undefined;
  const wantedRef = useRef(wanted);
  wantedRef.current = wanted;

  useEffect(() => {
    // In the shell: hold the answer and ask the window's state again (set
    // below). Every hiding signal calls it, so only the latest question may
    // release the hold (round 6, A).
    let requery: (() => void) | null = null;
    // A signal that may precede a suspend or a loss of attention: hide the
    // answer synchronously (so the frame a suspend keeps is the hidden one),
    // and show it again only after a fresh row is acknowledged (round 4).
    const hide = () => {
      gate.interrupt();
      flushSync(bump);
      requery?.();
    };
    const onVisibility = () => {
      const isVisible = documentVisible();
      if (isVisible) {
        gate.activity();
        setVisible(true);
      } else {
        gate.interrupt();
        flushSync(() => setVisible(false));
        requery?.();
      }
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
    document.addEventListener("freeze", hide);
    document.addEventListener("resume", back);
    window.addEventListener("blur", hide);
    window.addEventListener("pagehide", hide);
    window.addEventListener("focus", back);
    window.addEventListener("pageshow", back);
    for (const name of PRESENCE_EVENTS) window.addEventListener(name, present, { passive: true });
    // The desktop window's own signals, where the shell provides them (round
    // 5): a resize, a scale change or a focus change may mean the window is
    // being minimized or the machine suspended, so each hides the answer AT
    // ONCE, before the window's state is asked. The answer returns only once
    // the shell says the window is visible and unminimized (asked after the
    // events settle) and a fresh row is then acknowledged. Every event (these,
    // and the hiding signals above) starts a new generation, synchronously; a
    // reply to an earlier generation's question is stale and releases
    // nothing, so only the latest question may release the hold (round 6).
    let disposed = false;
    let generation = 0;
    const unlisten: (() => void)[] = [];
    const keep = (listener: Promise<() => void>) => {
      listener
        .then((stop) => (disposed ? stop() : unlisten.push(stop)))
        .catch(() => undefined);
    };
    let settle: number | undefined;
    try {
      const appWindow = getCurrentWindow();
      // Ask the window's state once the events settle; only the reply to the
      // latest question counts.
      const ask = () => {
        generation += 1;
        const asked = generation;
        window.clearTimeout(settle);
        settle = window.setTimeout(() => {
          Promise.all([appWindow.isMinimized(), appWindow.isVisible()])
            .then(([minimized, shown]) => {
              if (disposed || asked !== generation || minimized || !shown) return;
              gate.activity();
              shellHeldRef.current = false;
              setShellHeld(false);
            })
            .catch(() => undefined);
        }, SHELL_SETTLE_MS);
      };
      const shellEvent = () => {
        gate.interrupt();
        shellHeldRef.current = true;
        flushSync(() => setShellHeld(true));
        ask();
      };
      requery = shellEvent;
      keep(appWindow.onFocusChanged(shellEvent));
      keep(appWindow.onResized(shellEvent));
      keep(appWindow.onScaleChanged(shellEvent));
      // A hold left by the previous answer (a new key while held): this
      // answer's gate asks the shell itself (round 6, G).
      if (shellHeldRef.current) ask();
    } catch {
      // Not in the shell (a browser, a test): the DOM signals above suffice.
    }
    // The wall clock, every tick: a renewal that is due, a retry, and the
    // answer hidden once its row stops covering it (also after a sleep).
    const timer = window.setInterval(() => {
      gate.check(wantedRef.current);
      bump();
    }, EXPOSURE.tickMs);
    return () => {
      disposed = true;
      window.clearTimeout(settle);
      for (const stop of unlisten) stop();
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisibility);
      document.removeEventListener("freeze", hide);
      document.removeEventListener("resume", back);
      window.removeEventListener("blur", hide);
      window.removeEventListener("pagehide", hide);
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
