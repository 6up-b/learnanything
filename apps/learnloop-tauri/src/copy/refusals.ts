// UX fix stage 3 (item 5; stage 1's UX-6 sweep): refusals that explain rather
// than fail. Each is said in place, as a status line where the learner acted,
// never as the shell's sticky red error, and in plain words: no "diagnostic
// check", no "ask-tutor". The short check's way out is named by its own
// button's words, so the learner can find it.
import type { CalibrationSessionProgressDto } from "../api/dto";
import { STOP_AND_TEACH_LABEL } from "../app/checkHandoff";

/** A hint asked for on a check on your own (a cold follow-up). */
export const NO_HINTS_ON_YOUR_OWN = "No hints on this one: it's a check on your own.";

/** A hint asked for during a short check (a diagnostic block). */
export const NO_HINTS_SHORT_CHECK = `No hints during this short check. Answer with what you know, or choose “${STOP_AND_TEACH_LABEL}”.`;

/** Ask during a short check. */
export const NO_ASK_SHORT_CHECK = `Ask is paused during this short check. To be taught instead, choose “${STOP_AND_TEACH_LABEL}”.`;

/** Ask while the learner teaches a topic back (the tutor could give away what is being checked). */
export const NO_ASK_TEACH_BACK = "Ask is paused while you teach this one back, so the tutor can't give the answer away.";

/** The palette's Ask before the question has loaded (its check for a short check not yet read). */
export const NO_ASK_NOT_YET = "Ask opens once this question has loaded, and stays paused during a short check.";

/** A note on feedback for a question filed under no subject. */
export const NOTE_NO_SUBJECT = "This note can't be saved here: the question isn't filed under a subject yet. Your words are still here.";

/** Topic titles in a line: one by name, more as the first and a count. */
function topicNames(titles: readonly string[]): string {
  const [first, ...rest] = titles;
  if (rest.length === 0) return `“${first}”`;
  return `“${first}” and ${rest.length} more topic${rest.length === 1 ? "" : "s"}`;
}

/**
 * "Check what I already know" that ended the moment it started, having asked nothing: every topic already marked as
 * known (the check asks only about undecided ones), or no question on them the learner has not already seen (none
 * written yet, or all answered before). Opening that check showed "completed · 0 / 4 questions" and "not enough
 * answers to skip it", as if the learner had been asked; this sentence is said where they asked instead. Null when
 * the check asked something, can still ask, or was stopped.
 */
export function quickCheckNothingToAsk(progress: CalibrationSessionProgressDto): string | null {
  const check = progress.quickCheck;
  if (!check || !check.finished || check.answered > 0 || progress.status !== "completed") return null;
  const results = check.results ?? [];
  const unchecked = results.filter((result) => result.verdict !== "already_assumed").map((result) => result.learningObjectTitle);
  const known = results.filter((result) => result.verdict === "already_assumed").map((result) => result.learningObjectTitle);
  if (unchecked.length === 0 && known.length > 0) {
    const one = known.length === 1;
    return `${topicNames(known)} ${one ? "is" : "are"} already marked as known, so there's nothing to check now. ${one ? "Its" : "Their"} first review is the check.`;
  }
  if (unchecked.length === 0) return "Nothing to ask yet: there's no question you haven't already seen. Nothing was changed.";
  const one = unchecked.length === 1;
  return `Nothing to ask yet on ${topicNames(unchecked)}: ${one ? "it has" : "they have"} no question you haven't already seen. Nothing was changed.`;
}
