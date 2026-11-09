// An attempt's active clock (recognition and effort RE0, spec_recognition_and_effort_v1 §4.1). Pure: no API, no React.
//
// It is the router objective's own active clock, not a second definition: the Reader's visit clock (`visitClock.ts`,
// whose close the router reads in `router_objective.price.activity_spans`). A gap between two touches (typing, pointing,
// scrolling) shorter than VISIT_IDLE_MS is active time, a longer one counts for nothing here. Never blended with
// `latencySeconds`, the wall-clock time since the problem opened.
//
// Summed across resumes: the active milliseconds so far are kept under the draft's submission key (stable across a
// restart, see PracticeScreen) and the next open starts from them. The time the draft sat closed is no gap at all: the
// clock restarts at "now" on every open, so a pause, a night or a day away adds nothing.
import { accrueVisit, type VisitClock } from "./reader/visitClock";

/** localStorage key prefix; one entry per open draft, removed once its submit is acknowledged. */
const KEY_PREFIX = "learnloop.activeMs.";

/** A clock opened at `now`, starting from the active milliseconds a draft already carries (zero on a first open). */
export function openAttemptClock(now: number, carriedMs = 0): VisitClock {
  return { lastActive: now, active: Math.max(0, Math.round(carriedMs)), idle: 0 };
}

/** The learner touched the problem at `now`. */
export function touchAttempt(clock: VisitClock, now: number): void {
  accrueVisit(clock, now);
}

/** The active seconds so far, whole seconds, counting the gap up to `now` as the visit clock does. */
export function attemptActiveSeconds(clock: VisitClock, now: number): number {
  accrueVisit(clock, now);
  return Math.round(clock.active / 1000);
}

export type ActiveStorage = Pick<Storage, "getItem" | "setItem" | "removeItem">;

/** The active milliseconds a draft carried from earlier opens (0 when none, or storage is unavailable). */
export function carriedActiveMs(storage: ActiveStorage | null, key: string): number {
  if (!storage) return 0;
  try {
    const value = Number(storage.getItem(KEY_PREFIX + key));
    return Number.isFinite(value) && value > 0 ? value : 0;
  } catch {
    return 0;
  }
}

export function keepActiveMs(storage: ActiveStorage | null, key: string, ms: number): void {
  if (!storage) return;
  try {
    storage.setItem(KEY_PREFIX + key, String(Math.max(0, Math.round(ms))));
  } catch {
    // A full or blocked store only loses the carry-over; the attempt still sends this open's seconds.
  }
}

export function forgetActiveMs(storage: ActiveStorage | null, key: string): void {
  if (!storage) return;
  try {
    storage.removeItem(KEY_PREFIX + key);
  } catch {
    // Nothing to do: a stale entry is read only under a key that is never reused.
  }
}

/** Forget every carried clock whose key starts with `prefix` (a whole cache cleared at once). */
export function forgetActiveMsWithPrefix(storage: ActiveStorage | null, prefix: string): void {
  if (!storage || typeof (storage as Storage).length !== "number") return;
  try {
    const store = storage as Storage;
    const doomed: string[] = [];
    for (let i = 0; i < store.length; i += 1) {
      const key = store.key(i);
      if (key !== null && key.startsWith(KEY_PREFIX + prefix)) doomed.push(key);
    }
    for (const key of doomed) store.removeItem(key);
  } catch {
    // Nothing to do: a stale entry is read only under a key that is never reused.
  }
}

export function defaultActiveStorage(): ActiveStorage | null {
  try {
    return typeof window !== "undefined" ? window.localStorage : null;
  } catch {
    return null;
  }
}
