// "Waiting you can see" (docs/reviews/ux-waiting.md) on the feedback screen of
// the simple shell: the graded answer's feedback being read (the end of the
// owner's case 2) and Next until the next step opens. Through the real client
// and query cache, only the Tauri transport faked (as FeedbackScreen.plan.test.tsx).
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { FeedbackBundle, PlanStepDto } from "../api/dto";
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
  version: 1, attemptId: "att_1", practiceItemId: "pi_1", learningObjectId: "lo_eigen", learningObjectTitle: "Eigenvalues",
  rubricScore: 3, maxPoints: 4, correctness: 0.75, graderConfidence: 0.9, gradingSource: "manual", fallbackReason: null,
  manualReviewReason: null, fsrsRating: "good", nextDueAt: "2026-10-20T00:00:00Z", criterionEvidence: [], fatalErrors: [],
  errorAttributions: [],
  surprise: {
    predictiveSurprise: null, bayesianSurprise: null, surpriseDirection: null, fsrsIntervalFactor: null,
    followupThresholdNats: null, triggeredActions: [], suppressedActions: [], gateDiagnostics: null
  },
  masteryBefore: null, masteryAfter: null, masteryStep: null, feedbackMd: null, repairSuggestions: [],
  guidedRedoAvailable: false, interventionNeed: null, primed: false, sourceRefs: [], followupQueued: false
} as unknown as FeedbackBundle;

const NEXT: PlanStepDto = {
  kind: "item", planId: "p", blockId: "b", blockOrdinal: 1, practiceItemId: "pi_2", learningObjectId: "lo",
  learningObjectTitle: "Eigenvectors", origin: "chooser", schedulerCandidateId: null, boundary: false
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

let feedbackRead: Promise<FeedbackBundle>;
let served: Promise<unknown> | null;
let diagnosis: () => unknown;
beforeEach(() => {
  vi.useFakeTimers();
  feedbackRead = Promise.resolve(FEEDBACK);
  served = null;
  diagnosis = () => ({ version: 1, attemptId: "att_1", status: "done", cardEnabled: true, responses: [], summaryMd: "You stopped early." });
  invoke.mockImplementation(async (command: string, args: { input?: Record<string, unknown> }) => {
    switch (command) {
      case "get_feedback":
        return feedbackRead;
      case "get_practice_item":
        return new Promise(() => undefined);
      case "diagnosis_status":
        return diagnosis();
      case "next_plan_item":
        if (args.input?.serve && served) return served;
        return { version: 1, enabled: true, plan: null, step: NEXT };
      default:
        throw new Error(`${command} not faked`);
    }
  });
});
afterEach(() => { cleanup(); clear(); vi.clearAllMocks(); vi.useRealTimers(); });

async function advance(ms: number) {
  await act(async () => { await vi.advanceTimersByTimeAsync(ms); });
}

function show() {
  const callbacks = { onPlanStep: vi.fn(), onNext: vi.fn(), onOpenNext: vi.fn() };
  render(
    <FeedbackScreen
      attemptId="att_1" sessionId="s1"
      nextQueue={{ sessionId: "s1", availableMinutes: 25, energy: null }} onOpenNext={callbacks.onOpenNext}
      nextPlan={{ sessionId: "s1" }} onPlanStep={callbacks.onPlanStep} onNext={callbacks.onNext}
      onBack={vi.fn()} onOpenNotes={vi.fn()} onPrimedRetry={vi.fn()} onInspect={vi.fn()} onAsk={vi.fn()} onError={vi.fn()}
    />
  );
  return callbacks;
}

it("the feedback's read: nothing before the delay, then 'Opening your feedback…', gone when the feedback shows", async () => {
  const read = deferred<FeedbackBundle>();
  feedbackRead = read.promise;
  show();
  await advance(300);
  expect(screen.queryByText(/Opening your feedback…/)).toBeNull();
  await advance(100);
  expect(screen.getByTestId("feedback-wait").textContent).toBe("◐ Opening your feedback…");
  read.resolve(FEEDBACK);
  await advance(0);
  expect(screen.getByRole("button", { name: /Next/ })).toBeTruthy();
  expect(screen.queryByTestId("feedback-wait")).toBeNull();
});

it("Next: 'Choosing what's next…' after the delay, gone when the step is handed on", async () => {
  const serve = deferred<unknown>();
  served = serve.promise;
  const callbacks = show();
  await advance(0);
  const next = screen.getByRole("button", { name: /Next/ });
  fireEvent.click(next);
  await advance(300);
  expect(screen.queryByText(/Choosing what's next…/)).toBeNull();
  await advance(100);
  const line = screen.getByTestId("next-wait");
  expect(line.getAttribute("role")).toBe("status");
  expect(line.textContent).toBe("◐ Choosing what's next…");
  serve.resolve({ version: 1, enabled: true, plan: null, step: { ...NEXT, schedulerCandidateId: "cand_2" } });
  await advance(0);
  expect(callbacks.onPlanStep).toHaveBeenCalledOnce();
  expect(screen.queryByTestId("next-wait")).toBeNull();
});

it("a miss being looked into: 'Looking into what happened here…' after the delay (the phone's words), gone when it lands", async () => {
  feedbackRead = Promise.resolve({ ...FEEDBACK, diagnosisStatus: "pending" } as FeedbackBundle);
  let polls = 0;
  diagnosis = () => (++polls > 1
    ? { version: 1, attemptId: "att_1", status: "done", cardEnabled: true, responses: [], summaryMd: "You stopped early." }
    : { version: 1, attemptId: "att_1", status: "pending", cardEnabled: true, responses: [], summaryMd: null });
  show();
  await advance(0);
  expect(screen.getByRole("button", { name: /Next/ })).toBeTruthy();
  await advance(300);
  expect(screen.queryByText("Looking into what happened here…")).toBeNull();
  await advance(100);
  expect(screen.getByTestId("diagnosis-wait").textContent).toBe("◐ Looking into what happened here…");
  await advance(2500);
  // (MarkdownMath is mocked to nothing here: the landing is the second read saying done.)
  expect(polls).toBe(2);
  expect(screen.queryByTestId("diagnosis-wait")).toBeNull();
});
