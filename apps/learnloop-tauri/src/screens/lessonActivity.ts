// Teacher TE2-log: the lesson screen's activity intervals (spec_teacher_v1 §11.6).
//
// The screen cuts its own time into intervals, each "in the foreground with
// input" or not, on its own clock, and sends them to lesson.activity at natural
// boundaries (before every lesson step, when the window hides, when the screen
// closes). Active time is the window visible and focused, with input (a key, a
// pointer, a scroll) at gaps shorter than the Reader's idle gap (VISIT_IDLE_MS,
// reused: no new constant); a longer gap is open but not active, from the last
// input on (as the Reader counts it). Only times and a yes/no are sent, never the
// learner's words. Logging never blocks the lesson: a failed send is kept and
// sent again with the next batch (the sidecar writes each (screen session, seq)
// once), and an interval that never arrives (the app was closed) stays missing on
// the server, never filled in.
import { VISIT_IDLE_MS } from "./reader/useReaderVisit";
import type { LessonActivityIntervalDto } from "../api/dto";

export interface LessonActivityBatch {
  lessonId: string;
  intervals: LessonActivityIntervalDto[];
  occurredAt: string;
}

export interface LessonActivityTracker {
  /** The learner did something (a key, a pointer, a scroll). */
  input(): void;
  /** The window became foreground (visible and focused) or not. */
  foreground(on: boolean): void;
  /** Close the interval in progress (the next one continues it) and send everything pending. */
  flush(): void;
  /** Close the interval in progress, send everything pending, and stop. */
  stop(): void;
}

type Kind = "active" | "idle" | "hidden";

function newSessionId(): string {
  try {
    return crypto.randomUUID();
  } catch {
    return `lesson-screen-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  }
}

export function createLessonActivity(options: {
  lessonId: string;
  send: (batch: LessonActivityBatch) => Promise<unknown>;
  now?: () => number;
  foreground?: boolean;
  screenSession?: string;
}): LessonActivityTracker {
  const now = options.now ?? (() => Date.now());
  const session = options.screenSession ?? newSessionId();
  let seq = 0;
  let stopped = false;
  let sending = false;
  let pending: LessonActivityIntervalDto[] = [];
  let start = now();
  let kind: Kind = options.foreground === false ? "hidden" : "active";
  let lastInput = start;

  function emit(from: number, to: number, foreground: boolean): void {
    if (to <= from) return;
    seq += 1;
    pending.push({ screenSession: session, seq, startedAt: new Date(from).toISOString(),
                   endedAt: new Date(to).toISOString(), foreground });
  }

  /** An active stretch with no input for the idle gap ended at its last input; from there it is idle. */
  function settle(at: number): void {
    if (kind === "active" && at - lastInput >= VISIT_IDLE_MS) {
      const last = Math.max(start, lastInput);
      emit(start, last, true);
      start = last;
      kind = "idle";
    }
  }

  /** Close the interval in progress at `at`; the next one starts there with the same kind. */
  function cut(at: number): void {
    emit(start, at, kind === "active");
    start = at;
  }

  function send(): void {
    if (sending || pending.length === 0) return;
    const batch = pending;
    pending = [];
    sending = true;
    let request: Promise<unknown>;
    try {
      request = Promise.resolve(options.send({ lessonId: options.lessonId, intervals: batch,
                                               occurredAt: new Date(now()).toISOString() }));
    } catch (error) {
      request = Promise.reject(error);
    }
    void request
      .catch(() => {
        // Kept for the next batch: the sidecar records each (screen session, seq) once.
        pending = [...batch, ...pending];
      })
      .finally(() => {
        sending = false;
      });
  }

  return {
    input() {
      if (stopped) return;
      const at = now();
      settle(at);
      if (kind === "idle") {
        cut(at);
        kind = "active";
      }
      if (kind === "active") lastInput = at;
    },
    foreground(on: boolean) {
      if (stopped) return;
      const at = now();
      settle(at);
      if (on && kind === "hidden") {
        cut(at);
        kind = "active";
        lastInput = at;
      } else if (!on && kind !== "hidden") {
        cut(at);
        kind = "hidden";
        send();
      }
    },
    flush() {
      if (stopped) return;
      const at = now();
      settle(at);
      cut(at);
      send();
    },
    stop() {
      if (stopped) return;
      const at = now();
      settle(at);
      cut(at);
      stopped = true;
      send();
    },
  };
}
