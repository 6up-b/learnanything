// Shell notices that ask the learner to do something first. A notice like
// this is true only until the thing is done, so it leaves the screen then
// (UX Phase 1 usability round 2: "Begin today's plan on Start first." stayed
// over the Reader and Today after the plan had begun).

export const NEEDS_SESSION = {
  plan: "Begin today's plan on Start first.",
  practice: "Start a session before opening practice.",
  redo: "Start a session to begin the redo.",
  quickCheck: "Start a session first: the quick check runs inside a practice session.",
  primed: "Start a session to practice the primed item — it will open automatically.",
  checkMe: "Start a session to take this check on your own — it will open automatically.",
  exercise: "Start a session to work on this exercise — it will open automatically."
} as const;

const SESSION_NOTICES: ReadonlySet<string> = new Set(Object.values(NEEDS_SESSION));

/** The notice to keep once a session has begun: a session-first notice is resolved. */
export function noticeAfterSessionBegins(current: string | null): string | null {
  return current !== null && SESSION_NOTICES.has(current) ? null : current;
}
