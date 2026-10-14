/**
 * A `find_practice` proposal a learner picked an item from while the daily plan
 * is off (and, for a textbook exercise, the import that wrote it). Opening the
 * item from the open list is its serve, so that serve records the pick's
 * delivery (canonical sources, Codex re-review F10).
 */
export type ProposalOrigin = { proposalId: string; importId: string | null };

/** The scheduler slate candidate that led the learner to open a practice item,
 *  and (router R2a) the daily-plan presentation it was served under. */
export type PracticeOffer = {
  itemId: string;
  candidateId: string | null;
  proposalOrigin?: ProposalOrigin | null;
  presentationId?: string | null;
};

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

/**
 * Router R2a: the daily-plan presentation an answer to this serve binds to,
 * or null. A primed retry or guided redo is not a plan serve. A live offer for
 * this item names its own presentation; otherwise a restored draft's (review
 * F5: after a restart the offer is gone, the draft kept its presentation).
 * The sidecar binds the presentation when the attempt is written, and refuses
 * a used one without failing the submit.
 */
export function planPresentationForServe({
  offer,
  practiceItemId,
  primedRetry,
  guidedRedo,
  restoredPresentationId = null
}: {
  offer: PracticeOffer | null;
  practiceItemId: string;
  primedRetry: boolean;
  guidedRedo: boolean;
  restoredPresentationId?: string | null;
}): string | null {
  if (primedRetry || guidedRedo) return null;
  if (offer?.itemId === practiceItemId && offer.presentationId) return offer.presentationId;
  return restoredPresentationId ?? null;
}

/** The proposal a serve delivers, or null (same rules as the scheduler candidate). */
export function proposalOriginForServe({
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
}): ProposalOrigin | null {
  if (primedRetry || guidedRedo || restoredSubmissionId) return null;
  if (offer?.itemId !== practiceItemId) return null;
  return offer.proposalOrigin ?? null;
}
