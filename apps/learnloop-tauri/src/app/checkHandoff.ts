// The two hand-offs out of a diagnostic check ("Teach me this" when a check ends with a gap to teach, "Stop
// diagnosing and teach me" during one) ask to be taught, so they open a Teacher lesson on the check's topic, naming
// the check's episode so the lesson reads what the check found (the brief's from_check). Ask tutor stays the place
// for questions about what is on screen; here it opens only as the fallback, when lessons are off or the lesson
// can't open, with today's proactive opening from the check's persisted decision.
import { algoConfig } from "./algoConfig";

export interface CheckHandoff {
  learningObjectId: string;
  title?: string;
  /** The check's episode (absent when the stop found nothing open: the lesson then opens as "Teach me this" does). */
  probeEpisodeId?: string | null;
  /** The tutor's proactive opening, run instead of the lesson when lessons are off or the lesson can't open. */
  fallback: () => void;
}

export const STOP_AND_TEACH_LABEL = "Stop diagnosing and teach me";
export const TEACH_AFTER_CHECK_LABEL = "Teach me this";
export const TUTOR_AFTER_CHECK_LABEL = "Learn it with the tutor";

/** Whether a hand-off opens a lesson (the host wires one and lessons are on), so its label can say so. */
export function handoffOpensLesson(onTeachFromCheck: ((handoff: CheckHandoff) => void) | undefined): boolean {
  return Boolean(onTeachFromCheck) && algoConfig().lessons;
}
