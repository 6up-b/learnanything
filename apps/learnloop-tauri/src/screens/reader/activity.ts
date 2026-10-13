// The Reader's funnel activity (reader workbench RW1a; spec §4.1, §4.3).
//
// Visits, selections, actions, detours, reconnect lines and model jobs go to
// reader.log_activity in small batches, off the hot path: logging never
// blocks reading, never retries loudly and never surfaces an error. Only
// ids, kinds, counts and timings are sent (the sidecar drops anything else);
// never the learner's words or a quoted passage. Off while reader_inquiry is
// off, so the switched-off Reader writes nothing new.
import { api } from "../../api/client";
import type { ReaderActivityEvent } from "../../api/dto";

const FLUSH_MS = 1500;
const MAX_BATCH = 200;

let enabled = false;
let queue: ReaderActivityEvent[] = [];
let timer: ReturnType<typeof setTimeout> | null = null;

// Learner activity counters, read before and after a model wait (the
// report's waiting behaviour: did the learner keep reading while it ran?).
const counters = { scrolled: 0, selected: 0, typed: 0 };

export function setReaderActivityEnabled(on: boolean): void {
  enabled = on;
  if (!on) {
    queue = [];
    if (timer !== null) clearTimeout(timer);
    timer = null;
  }
}

export function readerActivityEnabled(): boolean {
  return enabled;
}

export function newActivityId(): string {
  try {
    return crypto.randomUUID();
  } catch {
    return `act-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  }
}

export function flushReaderActivity(): void {
  if (timer !== null) clearTimeout(timer);
  timer = null;
  if (!enabled || queue.length === 0) return;
  const batch = queue.splice(0, MAX_BATCH);
  try {
    const send = (api as { readerLogActivity?: (input: { events: ReaderActivityEvent[] }) => Promise<unknown> }).readerLogActivity;
    if (typeof send !== "function") return;
    void Promise.resolve(send({ events: batch })).catch(() => undefined);
  } catch {
    /* Activity is best-effort; reading never notices. */
  }
  if (queue.length > 0) timer = setTimeout(flushReaderActivity, FLUSH_MS);
}

export function logReaderActivity(event: ReaderActivityEvent): void {
  if (!enabled) return;
  queue.push(event);
  if (timer === null) timer = setTimeout(flushReaderActivity, FLUSH_MS);
}

export function logReaderAction(
  event: NonNullable<ReaderActivityEvent["event"]>,
  payload: ReaderActivityEvent["payload"],
): void {
  logReaderActivity({ kind: "reader_action_invoked", event, payload });
}

export function noteLearnerActivity(kind: keyof typeof counters): void {
  counters[kind] += 1;
}

export function learnerActivitySnapshot(): Readonly<typeof counters> {
  return { ...counters };
}

/** Which kinds of learner activity happened since ``before``. */
export function activitySince(before: Readonly<typeof counters>): Record<string, boolean> {
  const out: Record<string, boolean> = {};
  for (const key of Object.keys(counters) as Array<keyof typeof counters>) {
    if (counters[key] > before[key]) out[key] = true;
  }
  return out;
}

/** Test seam: forget queued events and counters. */
export function resetReaderActivityForTests(): void {
  setReaderActivityEnabled(false);
  counters.scrolled = 0;
  counters.selected = 0;
  counters.typed = 0;
}
