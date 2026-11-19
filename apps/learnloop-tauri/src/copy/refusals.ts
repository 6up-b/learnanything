// UX fix stage 3 (item 5; stage 1's UX-6 sweep): refusals that explain rather
// than fail. Each is said in place, as a status line where the learner acted,
// never as the shell's sticky red error, and in plain words: no "diagnostic
// check", no "ask-tutor". The short check's way out is named by its own
// button's words, so the learner can find it.
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
