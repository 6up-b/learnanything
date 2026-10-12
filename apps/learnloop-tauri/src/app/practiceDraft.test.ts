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
    answer: "mirrored", hints: 1, submissionId: "key-2", stuck: true, teachBack: null
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
    answer: "", hints: 0, submissionId: null, stuck: false, teachBack: null
  });
});
