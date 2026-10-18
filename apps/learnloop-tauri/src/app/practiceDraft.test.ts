import { expect, it } from "vitest";
import type { SessionCheckpoint } from "../api/dto";
import { restoredPracticeDraft, type PracticeDraftMirror } from "./practiceDraft";

const checkpoint = (overrides: Partial<SessionCheckpoint> = {}): SessionCheckpoint => ({
  currentPracticeItemId: "item-1",
  currentAnswer: "Why is V transposed?",
  hintsUsed: 0,
  submissionId: "key-1",
  focusBlockState: null,
  pendingGradingProposal: null,
  readiness: null,
  updatedAt: "2026-10-12T00:00:00Z",
  ...overrides
});

const mirror = (overrides: Partial<PracticeDraftMirror> = {}): PracticeDraftMirror => ({
  practiceItemId: "item-1",
  answerMd: "mirrored",
  hintsUsed: 1,
  submissionId: "key-2",
  declaredStuck: true,
  ...overrides
});

it("restores the stuck marker from the in-memory mirror after navigation", () => {
  expect(restoredPracticeDraft("item-1", mirror(), checkpoint())).toEqual({
    answer: "mirrored", hints: 1, submissionId: "key-2", stuck: true, teachBack: null, planPresentationId: null,
    selfGradeDisclosure: null, firstHintProgress: null, hintSeen: false
  });
  expect(restoredPracticeDraft("item-1", mirror({ declaredStuck: false }), null).stuck).toBe(false);
});

it("restores the stuck marker from the session checkpoint after a restart", () => {
  const restored = restoredPracticeDraft("item-1", null, checkpoint({ declaredStuck: true }));
  expect(restored).toMatchObject({ answer: "Why is V transposed?", submissionId: "key-1", stuck: true });
  // An older sidecar never sent the field: not stuck.
  expect(restoredPracticeDraft("item-1", null, checkpoint()).stuck).toBe(false);
});

it("never carries a stuck marker to another item", () => {
  expect(restoredPracticeDraft("item-2", mirror(), checkpoint({ declaredStuck: true }))).toEqual({
    answer: "", hints: 0, submissionId: null, stuck: false, teachBack: null, planPresentationId: null,
    selfGradeDisclosure: null, firstHintProgress: null, hintSeen: false
  });
});

// Router R2a (review F5): the draft's plan presentation is restored with it,
// from the in-memory mirror or (after a restart) the session checkpoint.
it("restores the draft's plan presentation with the draft", () => {
  expect(restoredPracticeDraft("item-1", mirror({ planPresentationId: "pres_m" }), null).planPresentationId).toBe("pres_m");
  expect(restoredPracticeDraft("item-1", null, checkpoint({ planPresentationId: "pres_c" })).planPresentationId).toBe("pres_c");
  // An older sidecar never sent the field; another item never inherits it.
  expect(restoredPracticeDraft("item-1", null, checkpoint()).planPresentationId).toBeNull();
  expect(restoredPracticeDraft("item-2", null, checkpoint({ planPresentationId: "pres_c" })).planPresentationId).toBeNull();
});

// UX Phase 4 (Codex review F1): a draft whose full answer the plain self-grade
// already showed reopens locked to the trace it froze, from the mirror after
// navigation or the checkpoint after a restart; never under another retry key
// or on another item.
it("restores the trace frozen before a full answer was shown, under its own retry key only", () => {
  const frozen = { submissionId: "key-2", answerMd: "U Sigma V^T", explanationMd: "it factorises" };
  expect(restoredPracticeDraft("item-1", mirror({ selfGradeDisclosure: frozen }), null).selfGradeDisclosure).toEqual(frozen);
  expect(
    restoredPracticeDraft("item-1", mirror({ selfGradeDisclosure: { ...frozen, submissionId: "key-old" } }), null).selfGradeDisclosure
  ).toBeNull();
  const fromCheckpoint = { ...frozen, submissionId: "key-1" };
  expect(restoredPracticeDraft("item-1", null, checkpoint({ selfGradeDisclosure: fromCheckpoint })).selfGradeDisclosure).toEqual(
    fromCheckpoint
  );
  expect(restoredPracticeDraft("item-2", null, checkpoint({ selfGradeDisclosure: fromCheckpoint })).selfGradeDisclosure).toBeNull();
  expect(restoredPracticeDraft("item-1", null, checkpoint()).selfGradeDisclosure).toBeNull();
});

// Adaptive difficulty AD1 (§11.2): the first-hint progress marker is restored
// with its draft, from the mirror or the checkpoint (which holds it only under
// the draft's own retry key); another item never inherits it.
it("restores the draft's first-hint progress marker with the draft", () => {
  expect(restoredPracticeDraft("item-1", mirror({ firstHintProgress: "no_draft" }), null).firstHintProgress).toBe("no_draft");
  expect(restoredPracticeDraft("item-1", null, checkpoint({ firstHintProgress: "draft_started" })).firstHintProgress)
    .toBe("draft_started");
  expect(restoredPracticeDraft("item-1", null, checkpoint()).firstHintProgress).toBeNull();
  expect(restoredPracticeDraft("item-2", null, checkpoint({ firstHintProgress: "no_draft" })).firstHintProgress).toBeNull();
});
