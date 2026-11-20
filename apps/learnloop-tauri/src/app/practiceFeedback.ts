// UX Phase 4: practice and feedback (docs/specs/ux_learnloop_v1.md §7.4, §7.5,
// §10). The kill switch and the plain words the practice card, feedback, the
// short check's results, the repair step and the session finish share.
//
// Display only: nothing here is read by grading, scheduling, evidence,
// projections or replay (the owner's ruling: live changes behind kill
// switches, no algorithm successor). `[ui] practice_feedback = "classic"`
// restores every one of those screens exactly as it was before Phase 4.
import type { ColdCheckResultDto } from "../api/dto";
import { algoConfig } from "./algoConfig";

/** Whether the Phase 4 presentation is on (the default). */
export function simplePracticeFeedback(): boolean {
  return algoConfig().practiceFeedback !== "classic";
}

export function unestablishedRepairCopy(check: ColdCheckResultDto): string {
  const result = check.passed ? "You passed this check." : "You didn't pass this check.";
  switch (check.claimDowngradedReason) {
    case "episode_reveal_over_budget":
      return `${result} The repair showed too much of the answer for this check to tell whether it helped.`;
    default:
      return `${result} This check can't show whether the repair helped.`;
  }
}

export type Verdict = "right" | "partly" | "not_yet" | "held";

/** A verdict in words (§7.5); the score in numbers goes in details. */
export const VERDICT_TEXT: Record<Verdict, string> = {
  right: "Right",
  partly: "Partly right",
  not_yet: "Not yet",
  held: "Held for review"
};

/** A grade held for review, in the feedback's words (the grade counts for nothing until then). */
export const HELD_GRADE_LINE =
  "The grader couldn't check the way you answered, so this answer doesn't count either way until it's reviewed.";
/** A grade waiting on the learner's answer to one clarifying question. */
export const PROVISIONAL_GRADE_LINE = "This grade may change after one question";
/** A valid answer by another route: the criteria that route never used are out of the grade. */
export const UNASSESSED_ROUTE_LINE =
  "your answer checks out by a different route · criteria that route did not exercise are not assessed (no credit, no lost points)";

/**
 * Every review reason the sidecar writes on an attempt (`manual_review_reason`), by its code. The last
 * five arrive with the ids they concern after a colon (`unknown_target_criterion:c1,c2`).
 */
export const REVIEW_REASON_CODES = [
  "valid_alternative_unverified",
  "provisional_pending_clarification",
  "grade_held_for_review",
  "grade_contract_unrecorded",
  "codex_manual_review",
  "low_grader_confidence",
  "low_self_confidence",
  "blank_answer",
  "unknown_target_evidence_family",
  "unknown_target_criterion",
  "unanchored_diagnosis_facet",
  "attribution_scope",
  "unknown_error_type"
] as const;
export type ReviewReasonCode = (typeof REVIEW_REASON_CODES)[number];

// What a feedback says for each: the desktop feedback's own sentence, or nothing where it says
// nothing. A request for a person to look at the grade is not the learner's to act on.
const REVIEW_REASON_LINES: Record<ReviewReasonCode, string | null> = {
  valid_alternative_unverified: UNASSESSED_ROUTE_LINE,
  provisional_pending_clarification: `${PROVISIONAL_GRADE_LINE}.`,
  grade_held_for_review: HELD_GRADE_LINE,
  grade_contract_unrecorded: HELD_GRADE_LINE,
  codex_manual_review: null,
  low_grader_confidence: null,
  low_self_confidence: null,
  blank_answer: null,
  unknown_target_evidence_family: null,
  unknown_target_criterion: null,
  unanchored_diagnosis_facet: null,
  attribution_scope: null,
  unknown_error_type: null
};

/** The words a feedback shows for a grade's review reason, or null. Never the code: a reason this
 *  list does not know (a newer sidecar's) shows nothing. */
export function reviewReasonLine(reason: string | null | undefined): string | null {
  if (!reason) return null;
  const head = reason.split(":", 1)[0];
  return Object.prototype.hasOwnProperty.call(REVIEW_REASON_LINES, head)
    ? REVIEW_REASON_LINES[head as ReviewReasonCode]
    : null;
}

/**
 * The verdict for one grade. A grade held for review is the grader's own
 * provisional score and counts for nothing (THE held predicate,
 * `learnloop.held_grades`), so it is never a verdict and never a score.
 * The grade's own correctness decides when it is known: criteria a valid
 * route never exercised are out of the grade, not lost points (PF-c).
 */
export function verdictOf({
  score,
  max,
  correctness,
  held = false
}: {
  score: number | null | undefined;
  max: number;
  correctness?: number | null;
  held?: boolean;
}): Verdict {
  if (held) return "held";
  const ratio =
    typeof correctness === "number" && Number.isFinite(correctness)
      ? correctness
      : typeof score === "number" && max > 0
        ? score / max
        : 0;
  if (ratio >= 1 - 1e-9) return "right";
  if (ratio > 0) return "partly";
  return "not_yet";
}

/**
 * Repair as one timed step (§7.5): compare the two ideas, read both passages,
 * then one related question. A planning label in the daily plan's units:
 * about a minute to compare and read, and one question at the plan's
 * fallback estimate of three minutes (`daily_plan.estimates`
 * FALLBACK_PRIOR_MINUTES), before the learner's own durations exist.
 */
export const REPAIR_STEP_MINUTES = 4;
export const FIX_MIX_UP_LABEL = `Fix this mix-up · about ${REPAIR_STEP_MINUTES} min`;

/** Where an attempt started, so Next returns there (§7.5). */
export type FeedbackOrigin = "plan" | "today" | "reader";

export function feedbackOrigin({ fromReader, planServing }: { fromReader: boolean; planServing: boolean }): FeedbackOrigin {
  if (fromReader) return "reader";
  return planServing ? "plan" : "today";
}

export const ORIGIN_LABEL: Record<FeedbackOrigin, string> = {
  plan: "Today's plan",
  today: "Today",
  reader: "Back to the book"
};

/** A facet or topic slug in words, for the few places only a slug exists. */
export function plainSlug(slug: string | null | undefined): string {
  return (slug ?? "").replace(/^(facet|lo|concept)_/, "").replace(/[_-]+/g, " ").trim();
}

/** An expected answer as text: a string as it is, a structured key as lines. */
export function expectedAnswerText(value: unknown): string {
  if (typeof value === "string") return value;
  if (value == null) return "";
  if (Array.isArray(value)) return value.map(expectedAnswerText).join("\n");
  if (typeof value === "object") {
    return Object.entries(value as Record<string, unknown>)
      .map(([key, entry]) => `${plainSlug(key)}: ${expectedAnswerText(entry)}`)
      .join("\n");
  }
  return String(value);
}
