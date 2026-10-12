// Daily-loop DL1 (§6.5): feedback's Next under the finite plan, through the
// real client and query cache (only the Tauri transport is faked). The next
// step is read while feedback shows (serve: false); Next serves it when it
// continues the current block, and the queue head is never read.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { DailyPlanDto, FeedbackBundle, PlanStepDto } from "../api/dto";
import { clear } from "../api/queryCache";

const { invoke } = vi.hoisted(() => ({ invoke: vi.fn() }));
vi.mock("@tauri-apps/api/core", () => ({ invoke }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: () => null }));
vi.mock("../components/ClaimSurface", () => ({ ClaimSurface: () => null, mintVisitId: () => "visit" }));
vi.mock("../components/KnowledgeModel", () => ({ AttemptTraceView: () => null, UnresolvedCauseCard: () => null }));
vi.mock("../components/CardControls", () => ({ CardControls: () => null, ProbeRemintAction: () => null }));
vi.mock("../components/RepairTrace", () => ({ RepairTraceBlocks: () => null }));
vi.mock("../components/RepairAffordances", () => ({ CommonRepairCard: () => null, GuidedRedoAffordance: () => null }));

import { FeedbackScreen } from "./FeedbackScreen";

const FEEDBACK = {
  version: 1,
  attemptId: "att_1",
  practiceItemId: "pi_1",
  learningObjectId: "lo_eigen",
  learningObjectTitle: "Eigenvalues",
  rubricScore: 3,
  maxPoints: 4,
  correctness: 0.75,
  graderConfidence: 0.9,
  gradingSource: "manual",
  fallbackReason: null,
  manualReviewReason: null,
  fsrsRating: "good",
  nextDueAt: "2026-10-20T00:00:00Z",
  criterionEvidence: [],
  fatalErrors: [],
  errorAttributions: [],
  surprise: {
    predictiveSurprise: null, bayesianSurprise: null, surpriseDirection: null, fsrsIntervalFactor: null,
    followupThresholdNats: null, triggeredActions: [], suppressedActions: [], gateDiagnostics: null
  },
  masteryBefore: null,
  masteryAfter: null,
  masteryStep: null,
  feedbackMd: null,
  repairSuggestions: [],
  guidedRedoAvailable: false,
  interventionNeed: null,
  primed: false,
  sourceRefs: [],
  followupQueued: false
} as unknown as FeedbackBundle;

const NEXT: PlanStepDto = {
  kind: "item", planId: "p", blockId: "b", blockOrdinal: 1, practiceItemId: "pi_2", learningObjectId: "lo",
  learningObjectTitle: "Eigenvectors", origin: "chooser", schedulerCandidateId: null, boundary: false
};

let peekStep: PlanStepDto;
let calls: Array<Record<string, unknown>>;
beforeEach(() => {
  peekStep = NEXT;
  calls = [];
  invoke.mockImplementation(async (command: string, args: { input?: Record<string, unknown> }) => {
    switch (command) {
      case "get_feedback":
        return FEEDBACK;
      case "get_practice_item":
        return new Promise(() => undefined);
      case "next_plan_item": {
        calls.push(args.input ?? {});
        const step = args.input?.serve ? { ...peekStep, schedulerCandidateId: "cand_2" } : peekStep;
        return { version: 1, enabled: true, plan: null, step } satisfies Partial<DailyPlanDto>;
      }
      default:
        throw new Error(`${command} not faked`);
    }
  });
});
afterEach(() => { cleanup(); clear(); vi.clearAllMocks(); });

function show() {
  const callbacks = {
    onPlanStep: vi.fn(),
    onNext: vi.fn(),
    onOpenNext: vi.fn()
  };
  render(
    <FeedbackScreen
      attemptId="att_1"
      sessionId="s1"
      nextQueue={{ sessionId: "s1", availableMinutes: 25, energy: null }}
      onOpenNext={callbacks.onOpenNext}
      nextPlan={{ sessionId: "s1" }}
      onPlanStep={callbacks.onPlanStep}
      onNext={callbacks.onNext}
      onBack={vi.fn()}
      onOpenNotes={vi.fn()}
      onPrimedRetry={vi.fn()}
      onInspect={vi.fn()}
      onAsk={vi.fn()}
      onError={vi.fn()}
    />
  );
  return callbacks;
}

it("serves the next item of the block on Next and hands it to the shell", async () => {
  const callbacks = show();
  expect(await screen.findByText("next: Eigenvectors")).toBeTruthy();
  expect(invoke.mock.calls.some(([command]) => command === "get_today_queue")).toBe(false);
  await act(async () => { fireEvent.keyDown(window, { key: "n" }); });
  await waitFor(() => expect(callbacks.onPlanStep).toHaveBeenCalledOnce());
  expect(callbacks.onPlanStep.mock.calls[0][0]).toMatchObject({ kind: "item", practiceItemId: "pi_2", schedulerCandidateId: "cand_2" });
  // Read while feedback shows, then served once (any later read is the prefetch again).
  expect(calls.slice(0, 2).map((input) => input.serve)).toEqual([false, true]);
  expect(calls.filter((input) => input.serve).length).toBe(1);
  expect(callbacks.onOpenNext).not.toHaveBeenCalled();
  expect(callbacks.onNext).not.toHaveBeenCalled();
});

it("hands a new block to the plan view without serving it", async () => {
  peekStep = { ...NEXT, boundary: true };
  const callbacks = show();
  expect(await screen.findByText("next block")).toBeTruthy();
  await act(async () => { fireEvent.keyDown(window, { key: "Enter" }); });
  await waitFor(() => expect(callbacks.onPlanStep).toHaveBeenCalledOnce());
  expect(callbacks.onPlanStep.mock.calls[0][0]).toMatchObject({ boundary: true });
  expect(calls.every((input) => !input.serve)).toBe(true);
});
