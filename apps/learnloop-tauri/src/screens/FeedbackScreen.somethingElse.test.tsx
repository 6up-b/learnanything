// Instruct hand-off IH3 (spec_instruct_handoff_v1 §6): "Something else would help" on feedback, through the real client and
// query cache (only the Tauri transport is faked). One quiet link under the grade while the plan serves, only where the
// sidecar says so; the options are the plan's own; a choice is served (the step it placed), a lesson opens as the learner's
// own start, and the plan's own pick is served as Next serves it.
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


const OPTIONS = {
  version: 1, enabled: true, drawn: true, decisionId: "dec1", device: "desktop",
  options: [
    { kind: "question", ref: "cand_q", label: "Another question", minutes: 6, propensity: null, plansPick: false, servable: true },
    { kind: "new", ref: "cand_new", label: "Something new", minutes: 8, propensity: null, plansPick: false, servable: true },
    { kind: "lesson", ref: "lesson_offer:lo_relu", label: "Learn ReLU", minutes: 15, propensity: null, plansPick: false, servable: true },
    { kind: "review", ref: "cand_r", label: "Review something from earlier", minutes: 4, propensity: null, plansPick: true, servable: true }
  ]
};
const PLACED: PlanStepDto = {
  kind: "item", planId: "p", blockId: "b_learner", blockOrdinal: 3, practiceItemId: "pi_pick", learningObjectId: "lo",
  learningObjectTitle: "Chosen", origin: "learner_pick", schedulerCandidateId: null, boundary: false
};

let flag: boolean;
let chosen: Record<string, unknown>;
let sent: Array<Record<string, unknown>>;
let nextCalls: Array<Record<string, unknown>>;
beforeEach(() => {
  flag = true;
  sent = [];
  nextCalls = [];
  chosen = {};
  invoke.mockImplementation(async (command: string, args: { input?: Record<string, unknown> }) => {
    switch (command) {
      case "get_feedback":
        return FEEDBACK;
      case "get_practice_item":
        return new Promise(() => undefined);
      case "get_daily_plan":
        return { version: 1, enabled: true, plan: null, ...(flag ? { somethingElse: true } : {}) };
      case "next_plan_item":
        nextCalls.push(args.input ?? {});
        return { version: 1, enabled: true, plan: null, step: NEXT };
      case "plan_something_else_options":
        return OPTIONS;
      case "plan_something_else":
        sent.push(args.input ?? {});
        return { version: 1, enabled: true, plan: null, step: PLACED,
                 preference: { id: "k", outcome: "served", kind: "question", ref: "cand_q", servedDecisionId: "d1", lesson: null,
                               replayed: false }, ...chosen };
      default:
        throw new Error(`${command} not faked`);
    }
  });
});
afterEach(() => { cleanup(); clear(); vi.clearAllMocks(); });

// A session of its own per test: a plan read still in flight when one test ends must not seed the next one's cache.
let counter = 0;
function show(extra: Record<string, unknown> = {}) {
  const sid = `s${++counter}`;
  const callbacks = { onPlanStep: vi.fn(), onStartLesson: vi.fn(), onNext: vi.fn(), onError: vi.fn() };
  render(
    <FeedbackScreen
      attemptId="att_1"
      sessionId={sid}
      nextPlan={{ sessionId: sid }}
      onPlanStep={callbacks.onPlanStep}
      onStartLesson={callbacks.onStartLesson}
      onNext={callbacks.onNext}
      onBack={vi.fn()}
      onOpenNotes={vi.fn()}
      onPrimedRetry={vi.fn()}
      onInspect={vi.fn()}
      onAsk={vi.fn()}
      onError={callbacks.onError}
      {...extra}
    />
  );
  return callbacks;
}

it("shows one quiet link under the feedback, only where the plan says so, and never a modal", async () => {
  show();
  expect((await screen.findByTestId("something-else-link")).textContent).toBe("Something else would help");
  expect(screen.queryByRole("dialog")).toBeNull();
  expect(sent).toEqual([]);
});

it("is not there with the switch off, and Next is as it was", async () => {
  flag = false;
  show();
  expect(await screen.findByText("next: Eigenvectors")).toBeTruthy();
  await act(async () => undefined);
  expect(screen.queryByTestId("something-else")).toBeNull();
  expect(invoke.mock.calls.some(([command]) => command === "plan_something_else_options")).toBe(false);
});

it("is not offered outside the plan (the queue's feedback keeps its own Next)", async () => {
  show({ nextPlan: null, nextQueue: null });
  await screen.findByText(/Eigenvalues/);
  await act(async () => undefined);
  expect(screen.queryByTestId("something-else")).toBeNull();
});

it("serves the choice and hands the step it placed to the shell, with this answer's id", async () => {
  const callbacks = show();
  const link = await screen.findByTestId("something-else-link");
  await act(async () => { fireEvent.click(link); });
  expect(screen.getByTestId("something-else-option-question").textContent).toBe("Another question (about 6 min)");
  fireEvent.change(screen.getByTestId("something-else-note"), { target: { value: "easier first" } });
  await act(async () => { fireEvent.click(screen.getByTestId("something-else-option-question")); });
  expect(sent).toHaveLength(1);
  expect(sent[0]).toMatchObject({ kind: "question", ref: "cand_q", surface: "feedback", attemptId: "att_1", sessionId: `s${counter}`,
                                  noteMd: "easier first" });
  expect(callbacks.onPlanStep).toHaveBeenCalledOnce();
  expect(callbacks.onPlanStep.mock.calls[0][0]).toMatchObject({ practiceItemId: "pi_pick", origin: "learner_pick" });
  expect(callbacks.onStartLesson).not.toHaveBeenCalled();
});

it("opens a chosen lesson as the learner's own start", async () => {
  chosen = { step: null, preference: { id: "k", outcome: "lesson", kind: "lesson", ref: "lesson_offer:lo_relu",
                                       servedDecisionId: "d1", lesson: { learningObjectIds: ["lo_relu"], title: "ReLU" },
                                       replayed: false } };
  const callbacks = show();
  const link = await screen.findByTestId("something-else-link");
  await act(async () => { fireEvent.click(link); });
  await act(async () => { fireEvent.click(screen.getByTestId("something-else-option-lesson")); });
  expect(callbacks.onStartLesson).toHaveBeenCalledWith({
    kind: "open", entry: "learning_object", learningObjectIds: ["lo_relu"], title: "ReLU"
  });
  expect(callbacks.onPlanStep).not.toHaveBeenCalled();
});

it("leaves 'learn this' off when the shell can't open lessons", async () => {
  show({ onStartLesson: undefined });
  const link = await screen.findByTestId("something-else-link");
  await act(async () => { fireEvent.click(link); });
  expect(screen.queryByTestId("something-else-option-lesson")).toBeNull();
});

it("serves the plan's own pick as Next serves it when the learner chose what was already drawn", async () => {
  chosen = { step: null, preference: { id: "k", outcome: "agreed", kind: "review", ref: "cand_r", servedDecisionId: "dec1",
                                       lesson: null, replayed: false } };
  const callbacks = show();
  const link = await screen.findByTestId("something-else-link");
  await act(async () => { fireEvent.click(link); });
  await act(async () => { fireEvent.click(screen.getByTestId("something-else-option-review")); });
  await waitFor(() => expect(callbacks.onPlanStep).toHaveBeenCalledOnce());
  expect(callbacks.onPlanStep.mock.calls[0][0]).toMatchObject({ practiceItemId: "pi_2" });
  expect(nextCalls.some((input) => input.serve === true)).toBe(true);
});
