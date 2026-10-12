import type { ReaderAuthoredCardDto } from "../../api/dto";

/** What happened to a question written with "write my own question". */
export type AuthoredQuestionStatus = ReaderAuthoredCardDto["practiceStatus"] | "offline_demo";

/**
 * What the reader may truthfully say once the learner's own question is saved.
 * Only a card the sidecar reports as `scheduled` (a Practice Item the scheduler
 * serves) earns the personal-practice promise; a card with no Learning Object to
 * file under is kept as a reference, and says so (daily-loop audit 2026-10-11).
 */
export function authoredQuestionMessage(status: AuthoredQuestionStatus | undefined): { text: string; scheduled: boolean } {
  if (status === "scheduled") {
    return { text: "✓ Saved in your exact words. It will return as personal practice.", scheduled: true };
  }
  if (status === "offline_demo") {
    return { text: "Offline demo: nothing was saved.", scheduled: false };
  }
  return {
    text: "✓ Saved in your exact words as a reference. Nothing on your study map covers this passage yet, so it is not scheduled for practice.",
    scheduled: false
  };
}
