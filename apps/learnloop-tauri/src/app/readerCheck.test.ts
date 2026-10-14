// RW3a "check me" (spec §6.1, D40): back from the item a Reader cue opened
// (Esc or b on its practice or feedback) returns to the passage in the
// Reader; any other item goes back to the queue as before.
import { expect, it } from "vitest";
import type { PlanStepDto, SourceLibraryCard } from "../api/dto";
import { planPresentationForServe, proposalOriginForServe, schedulerCandidateForServe } from "./practiceOffer";
import { keepReaderReturn, readerCheckOffer, returnsToReader, type ReaderReturn } from "./readerCheck";

const back: ReaderReturn = { card: { sourceId: "src", title: "Probability" } as SourceLibraryCard, spanId: "b1", practiceItemId: "pi_check" };

it("back from the checked item returns to its passage; from any other item, to the queue", () => {
  expect(returnsToReader(back, "pi_check")).toBe(true);
  expect(returnsToReader(back, "pi_other")).toBe(false);
  expect(returnsToReader(null, "pi_check")).toBe(false);
  expect(returnsToReader(back, null)).toBe(false);
});

it("opening another item drops the way back; the checked item itself keeps it", () => {
  expect(keepReaderReturn(back, "pi_check")).toBe(back);
  expect(keepReaderReturn(back, "pi_next")).toBeNull();
  expect(keepReaderReturn(null, "pi_check")).toBeNull();
});

const PICKED: PlanStepDto = {
  kind: "item", planId: "p", blockId: "b_pick", blockOrdinal: 3, practiceItemId: "pi_check", learningObjectId: "lo",
  learningObjectTitle: "Densities", origin: "learner_pick", schedulerCandidateId: "cand_pick", boundary: false,
};

it("plan on: check me is a learner pick -- served by the pick's block, which records the delivery itself", () => {
  const offer = readerCheckOffer({ enabled: true, step: PICKED }, "pi_check", "pp_1");
  expect(offer).toEqual({ itemId: "pi_check", candidateId: "cand_pick", proposalOrigin: null, presentationId: null });
  const serve = { offer, practiceItemId: "pi_check", primedRetry: false, guidedRedo: false, restoredSubmissionId: null };
  expect(schedulerCandidateForServe(serve)).toBe("cand_pick");
  expect(proposalOriginForServe(serve)).toBeNull();
});

it("plan off: the open serves it as an ordinary attempt and carries the proposal, so that serve records its delivery", () => {
  const offer = readerCheckOffer({ enabled: false }, "pi_check", "pp_1");
  expect(offer).toEqual({ itemId: "pi_check", candidateId: null, proposalOrigin: { proposalId: "pp_1", importId: null }, presentationId: null });
  const serve = { offer, practiceItemId: "pi_check", primedRetry: false, guidedRedo: false, restoredSubmissionId: null };
  expect(proposalOriginForServe(serve)).toEqual({ proposalId: "pp_1", importId: null });
  // A check with no proposal (nothing to deliver) opens bare.
  expect(readerCheckOffer({ enabled: false }, "pi_check", null).proposalOrigin).toBeNull();
});

// Landing onto main after router R2a: plan_learner_pick logs the pick block's
// own decision and presentation; the answer to a check binds to that
// presentation exactly (not R1's labelled session-rule fallback).
it("plan on: the answer to a check binds to the pick's own presentation", () => {
  const offer = readerCheckOffer({ enabled: true, step: { ...PICKED, presentationId: "pres_pick" } }, "pi_check", "pp_1");
  expect(offer.presentationId).toBe("pres_pick");
  const serve = { offer, practiceItemId: "pi_check", primedRetry: false, guidedRedo: false };
  expect(planPresentationForServe(serve)).toBe("pres_pick");
  // Plan off: nothing was presented, so nothing binds.
  expect(readerCheckOffer({ enabled: false }, "pi_check", "pp_1").presentationId ?? null).toBeNull();
  // A step not yet served carries no presentation.
  expect(readerCheckOffer({ enabled: true, step: PICKED }, "pi_check", "pp_1").presentationId ?? null).toBeNull();
});
