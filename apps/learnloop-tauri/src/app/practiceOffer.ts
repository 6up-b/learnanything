/** The scheduler slate candidate that led the learner to open a practice item. */
export type PracticeOffer = { itemId: string; candidateId: string | null };

/**
 * The scheduler candidate to attribute this practice serve to, or null.
 *
 * The sidecar binds a retry key to the first offer it receives and rejects a
 * different one later. Every queue rebuild mints fresh candidate ids, so a
 * resumed retry key (from the local draft mirror or the session checkpoint)
 * sends no candidate and the sidecar keeps the offer it already bound.
 * Primed retries and guided redos are not scheduler serves at all.
 */
export function schedulerCandidateForServe({
  offer,
  practiceItemId,
  primedRetry,
  guidedRedo,
  restoredSubmissionId
}: {
  offer: PracticeOffer | null;
  practiceItemId: string;
  primedRetry: boolean;
  guidedRedo: boolean;
  restoredSubmissionId: string | null;
}): string | null {
  if (primedRetry || guidedRedo) return null;
  if (restoredSubmissionId) return null;
  if (offer?.itemId !== practiceItemId) return null;
  return offer.candidateId;
}
