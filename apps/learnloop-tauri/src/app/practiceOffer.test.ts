import { expect, it } from "vitest";
import { planPresentationForServe, proposalOriginForServe, schedulerCandidateForServe } from "./practiceOffer";

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

// Codex re-review F10: a plan-off pick's proposal rides with the serve that records its delivery.
it("passes a plan-off pick's proposal to the serve of that item only", () => {
  const origin = { proposalId: "pp_1", importId: "imp" };
  const offered = { ...freshServe, offer: { itemId: "item-x", candidateId: null, proposalOrigin: origin } };
  expect(proposalOriginForServe(offered)).toEqual(origin);
  expect(proposalOriginForServe({ ...offered, practiceItemId: "item-y" })).toBeNull();
  expect(proposalOriginForServe({ ...offered, restoredSubmissionId: "retry-key-1" })).toBeNull();
  expect(proposalOriginForServe({ ...offered, primedRetry: true })).toBeNull();
  expect(proposalOriginForServe(freshServe)).toBeNull();
});

// Router R2a: the plan presentation rides with the serve of its own item, a
// resumed retry key included (the sidecar binds it when the attempt is written).
it("passes the plan presentation to the serve of that item only", () => {
  const offered = { offer: { itemId: "item-x", candidateId: "c", presentationId: "pres_1" }, practiceItemId: "item-x",
                    primedRetry: false, guidedRedo: false };
  expect(planPresentationForServe(offered)).toBe("pres_1");
  expect(planPresentationForServe({ ...offered, practiceItemId: "item-y" })).toBeNull();
  expect(planPresentationForServe({ ...offered, primedRetry: true })).toBeNull();
  expect(planPresentationForServe({ ...offered, guidedRedo: true })).toBeNull();
  expect(planPresentationForServe({ ...offered, offer: { itemId: "item-x", candidateId: "c" } })).toBeNull();
});

// Review F5: after a restart the offer is gone; the restored draft's own
// presentation is sent instead (the sidecar also reads it from the draft).
it("falls back to the restored draft's presentation when no offer names the item", () => {
  const resumed = { offer: null, practiceItemId: "item-x", primedRetry: false, guidedRedo: false,
                    restoredPresentationId: "pres_saved" };
  expect(planPresentationForServe(resumed)).toBe("pres_saved");
  expect(planPresentationForServe({ ...resumed, primedRetry: true })).toBeNull();
  expect(planPresentationForServe({ ...resumed, guidedRedo: true })).toBeNull();
  // A live offer for this item names its own presentation.
  expect(planPresentationForServe({
    ...resumed, offer: { itemId: "item-x", candidateId: "c", presentationId: "pres_live" }
  })).toBe("pres_live");
});
