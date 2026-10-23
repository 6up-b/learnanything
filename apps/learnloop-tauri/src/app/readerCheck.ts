/**
 * Reader workbench RW3a: "check me" on a margin cue (spec §6.1, D40).
 *
 * The item opens as an ordinary attempt on your own, recorded as a learner
 * pick through the daily plan when it serves (DL1's `plan_learner_pick`;
 * with the plan off, the open serves it and records the proposal's
 * delivery). Until the workbench's working posture lands (RW2a), it opens on
 * the practice screen, so the book is out of view; going back from that
 * item's practice or feedback (Esc or b) returns to the passage in the
 * Reader instead of the queue.
 */
import type { DailyPlanDto, SourceLibraryCard } from "../api/dto";
import type { PracticeOffer } from "./practiceOffer";

export interface ReaderReturn {
  card: SourceLibraryCard;
  spanId: string;
  practiceItemId: string;
  /** RW2a: the attempt was a Reader workbench submit; back opens its problem. */
  workbenchAttemptId?: string;
}

/** Whether going back from `practiceItemId` returns to the Reader's passage. */
export function returnsToReader(readerReturn: ReaderReturn | null, practiceItemId: string | null): boolean {
  return readerReturn !== null && practiceItemId !== null && readerReturn.practiceItemId === practiceItemId;
}

/** The return kept while another item opens: only that item's own. */
export function keepReaderReturn(readerReturn: ReaderReturn | null, openingItemId: string): ReaderReturn | null {
  return readerReturn && readerReturn.practiceItemId === openingItemId ? readerReturn : null;
}

/**
 * The practice offer for a Reader check the daily plan answered: with the plan
 * serving, the pick's own block step (its scheduler candidate and, since
 * router R2a, its presentation, so the answer binds to the pick's own logged
 * decision exactly) and no proposal origin, because the pick recorded the
 * delivery itself; with the plan off, the open serves the item and carries
 * the proposal so that serve records its delivery.
 */
export function readerCheckOffer(
  result: Pick<DailyPlanDto, "enabled" | "step">,
  practiceItemId: string,
  proposalId: string | null,
  /** RW4b: the sources service's import that wrote the item (a textbook exercise). */
  importId: string | null = null,
): PracticeOffer {
  const step = result.step;
  const item = step && step.kind === "item" ? step : null;
  return {
    itemId: practiceItemId,
    candidateId: item?.schedulerCandidateId ?? null,
    proposalOrigin: result.enabled || !proposalId ? null : { proposalId, importId },
    presentationId: result.enabled ? item?.presentationId ?? null : null,
  };
}
