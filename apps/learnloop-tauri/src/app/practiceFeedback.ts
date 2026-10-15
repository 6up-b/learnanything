// UX Phase 4: practice and feedback (docs/specs/ux_learnloop_v1.md §7.4, §7.5,
// §10). The kill switch and the plain words the practice card, feedback, the
// short check's results, the repair step and the session finish share.
//
// Display only: nothing here is read by grading, scheduling, evidence,
// projections or replay (the owner's ruling: live changes behind kill
// switches, no algorithm successor). `[ui] practice_feedback = "classic"`
// restores every one of those screens exactly as it was before Phase 4.
import { algoConfig } from "./algoConfig";

/** Whether the Phase 4 presentation is on (the default). */
export function simplePracticeFeedback(): boolean {
  return algoConfig().practiceFeedback !== "classic";
}

export type Verdict = "right" | "partly" | "not_yet" | "held";

/** A verdict in words (§7.5); the score in numbers goes in details. */
export const VERDICT_TEXT: Record<Verdict, string> = {
  right: "Right",
  partly: "Partly right",
  not_yet: "Not yet",
  held: "Held for review"
};

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
