// The attempt's active clock as a hook (see `attemptClock.ts`): touches from the window's own input events, kept per
// draft key so a resumed draft carries its earlier active time. Shared by the desktop's problem screens and the phone's.
import { useCallback, useEffect, useMemo, useRef } from "react";
import {
  attemptActiveSeconds,
  carriedActiveMs,
  defaultActiveStorage,
  forgetActiveMs,
  keepActiveMs,
  openAttemptClock,
  touchAttempt,
  type ActiveStorage
} from "./attemptClock";
import type { VisitClock } from "./reader/visitClock";

/** What counts as touching the problem. */
const TOUCH_EVENTS = ["keydown", "pointerdown", "wheel", "scroll", "input"] as const;
/** The carry-over is written at most this often while touching (and at once on leaving), so typing costs no writes. */
const SAVE_EVERY_MS = 5000;

export interface AttemptClock {
  /** Start (or restart) the clock for a draft: from what that key carried, at now. Call when the problem opens. */
  open: (key: string | null) => void;
  /** Active seconds so far, to send at submit; null before the clock was opened. */
  seconds: () => number | null;
  /** The draft's submit was acknowledged: its carry-over is no longer needed. */
  forget: (key?: string | null) => void;
}

export function useAttemptClock(storage: ActiveStorage | null = defaultActiveStorage()): AttemptClock {
  const clock = useRef<VisitClock | null>(null);
  const keyRef = useRef<string | null>(null);
  const savedAt = useRef(0);

  const save = useCallback(() => {
    if (clock.current && keyRef.current) {
      const now = Date.now();
      touchAttempt(clock.current, now);
      keepActiveMs(storage, keyRef.current, clock.current.active);
      savedAt.current = now;
    }
  }, [storage]);

  const open = useCallback((key: string | null) => {
    if (clock.current && keyRef.current && keyRef.current !== key) save();
    keyRef.current = key;
    clock.current = openAttemptClock(Date.now(), key ? carriedActiveMs(storage, key) : 0);
    savedAt.current = Date.now();
  }, [save, storage]);

  useEffect(() => {
    const onTouch = () => {
      const current = clock.current;
      if (!current) return;
      const now = Date.now();
      touchAttempt(current, now);
      if (keyRef.current && now - savedAt.current >= SAVE_EVERY_MS) {
        keepActiveMs(storage, keyRef.current, current.active);
        savedAt.current = now;
      }
    };
    for (const name of TOUCH_EVENTS) window.addEventListener(name, onTouch, { capture: true, passive: true });
    window.addEventListener("pagehide", save);
    return () => {
      for (const name of TOUCH_EVENTS) window.removeEventListener(name, onTouch, { capture: true });
      window.removeEventListener("pagehide", save);
      save();
    };
  }, [save, storage]);

  const seconds = useCallback(() => (clock.current ? attemptActiveSeconds(clock.current, Date.now()) : null), []);

  const forget = useCallback((key?: string | null) => {
    const target = key ?? keyRef.current;
    if (!target) return;
    forgetActiveMs(storage, target);
    // A later unmount must not write the entry back.
    if (target === keyRef.current) keyRef.current = null;
  }, [storage]);

  return useMemo(() => ({ open, seconds, forget }), [open, seconds, forget]);
}
