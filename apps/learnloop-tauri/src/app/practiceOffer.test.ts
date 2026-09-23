import { expect, it } from "vitest";
import { schedulerCandidateForServe } from "./practiceOffer";

const freshServe = {
  offer: { itemId: "item-x", candidateId: "candidate-2" },
  practiceItemId: "item-x",
  primedRetry: false,
  guidedRedo: false,
  restoredSubmissionId: null
};

it("attributes a fresh serve to the offer the learner opened", () => {
  expect(schedulerCandidateForServe(freshServe)).toBe("candidate-2");
});

it("sends no candidate when resuming a retry key the sidecar has already bound", () => {
  // Esc back to Today rebuilds the queue, so reopening the same item carries a
  // new candidate id while the restored draft keeps the original retry key.
  expect(schedulerCandidateForServe({ ...freshServe, restoredSubmissionId: "retry-key-1" })).toBeNull();
});

it("sends no candidate for an offer that belongs to another item", () => {
  expect(schedulerCandidateForServe({ ...freshServe, practiceItemId: "item-y" })).toBeNull();
});

it("sends no candidate for primed retries or guided redos", () => {
  expect(schedulerCandidateForServe({ ...freshServe, primedRetry: true })).toBeNull();
  expect(schedulerCandidateForServe({ ...freshServe, guidedRedo: true })).toBeNull();
});
