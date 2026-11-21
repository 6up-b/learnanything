// Daily-loop DL1 (§6.5): feedback's Next under the finite plan, through the
// real client and query cache (only the Tauri transport is faked). The next
// step is read while feedback shows (serve: false); Next serves it when it
// continues the current block, and the queue head is never read.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { DailyPlanDto, FeedbackBundle, PlanStepDto, ScheduledItemDto } from "../api/dto";
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

// UX-44: a plan that closed before the book's questions existed answers "done" after each of them. Next then goes on
// to the question Today offers with Begin (the book's questions that can be asked now), and says so; only with none
// left does it say the plan is done and go back to Today.
describe("Next when the plan is done: the book's next question that can be asked now (UX-44)", () => {
  const DONE: PlanStepDto = { kind: "done", planId: "p", status: "complete", stopReason: "Nothing else worth doing fits today." };
  const row = (id: string, overrides: Partial<ScheduledItemDto> = {}): ScheduledItemDto => ({
    schedulerSlateId: "slate", schedulerCandidateId: `cand_${id}`, practiceItemId: id, learningObjectId: "lo_eigen",
    learningObjectTitle: id === "pi_4" ? "Construct a diagonalization" : "Recognize eigenpairs", subject: null, practiceMode: "short_answer",
    selectedMode: "short_answer", priority: 0.2, components: {} as ScheduledItemDto["components"], readinessFactor: null, plainEnglish: [],
    dominantReason: "new", mastery: null, masteryVariance: null, dueAt: null, dueStatus: "later", isProbe: false, isFollowup: false,
    followupKind: null, ...overrides
  });
  // The one just answered (pi_1, this feedback's) and the one before it wait to come back; pi_3 is kept for a later check.
  const answered = (id: string) => row(id, { dueAt: "2099-01-01T00:00:00Z" });
  const book = (questions: Record<string, unknown>) => ({
    version: 1, pending: [],
    sources: [{ sourceId: "src_sym", title: "Symmetric Matrices and Variance", readiness: "ready", readerEnabled: true,
      statusLine: { text: "Questions for Ch. 1 come up as you read", tone: "quiet", action: null, details: null,
        questions: { count: 0, itemIds: [], sections: ["Document"], writing: [], waiting: [], failed: [], toLookAt: 0, sectionCount: 1, ...questions } } }]
  });
  let library: unknown;
  let rows: ScheduledItemDto[];
  let picks: Array<Record<string, unknown>>;

  beforeEach(() => {
    peekStep = DONE;
    picks = [];
    library = book({ count: 3, itemIds: ["pi_1", "pi_2", "pi_3"], writing: ["Document"], progress: { done: 1, total: 8 }, laterItemIds: ["pi_2", "pi_3"] });
    rows = [answered("pi_2"), answered("pi_1"), row("pi_3")];
    const base = invoke.getMockImplementation() as (command: string, args: { input?: Record<string, unknown> }) => Promise<unknown>;
    invoke.mockImplementation(async (command: string, args: { input?: Record<string, unknown> }) => {
      switch (command) {
        case "get_source_library":
          return library;
        case "get_today_queue":
          return { version: 1, generatedAt: "2026-11-20T18:37:00Z", sessionId: "s1", sections: [{ title: "Later today", items: rows }], totalItems: rows.length };
        case "plan_learner_pick": {
          picks.push(args.input ?? {});
          const id = String(args.input?.practiceItemId);
          return { version: 1, enabled: true, plan: null, step: { kind: "item", planId: null, blockId: null, practiceItemId: id, learningObjectId: "lo",
            origin: "open_list", schedulerCandidateId: null, presentationId: `pres_${id}`, boundary: false } };
        }
        default:
          return base(command, args);
      }
    });
  });

  it("after the second answer, with one written since: Next names it and opens it as a pick from the list, never the one just answered", async () => {
    library = book({
      count: 6, itemIds: ["pi_1", "pi_2", "pi_3", "pi_4", "pi_5", "pi_6"], writing: ["Document"], progress: { done: 2, total: 8 }, laterItemIds: ["pi_2", "pi_3"]
    });
    rows = [answered("pi_2"), answered("pi_1"), row("pi_3"), row("pi_4"), row("pi_5"), row("pi_6")];
    const callbacks = show();
    expect(await screen.findByText("next: Construct a diagonalization")).toBeTruthy();
    expect(screen.queryByText("today's plan is done")).toBeNull();
    await act(async () => { fireEvent.keyDown(window, { key: "n" }); });
    await waitFor(() => expect(callbacks.onPlanStep).toHaveBeenCalledOnce());
    expect(picks).toEqual([{ practiceItemId: "pi_4", sessionId: "s1", schedulerCandidateId: "cand_pi_4" }]);
    expect(callbacks.onPlanStep.mock.calls[0][0]).toMatchObject({
      kind: "item", practiceItemId: "pi_4", presentationId: "pres_pi_4", schedulerCandidateId: "cand_pi_4", boundary: false
    });
  });

  it("a topic applied while feedback shows: Next reads again and opens its question", async () => {
    const callbacks = show();
    // At first nothing else can be asked: the plan's own words.
    expect(await screen.findByText("today's plan is done")).toBeTruthy();
    library = book({ count: 6, itemIds: ["pi_1", "pi_2", "pi_3", "pi_4", "pi_5", "pi_6"], writing: ["Document"], laterItemIds: ["pi_2", "pi_3"] });
    rows = [answered("pi_2"), answered("pi_1"), row("pi_3"), row("pi_4"), row("pi_5"), row("pi_6")];
    await act(async () => { fireEvent.keyDown(window, { key: "Enter" }); });
    await waitFor(() => expect(callbacks.onPlanStep).toHaveBeenCalledOnce());
    expect(picks.map((input) => input.practiceItemId)).toEqual(["pi_4"]);
    expect(callbacks.onPlanStep.mock.calls[0][0]).toMatchObject({ kind: "item", practiceItemId: "pi_4" });
  });

  it("the last one that can be asked answered while more are written: 'today's plan is done', and Next goes back to Today", async () => {
    const callbacks = show();
    expect(await screen.findByText("today's plan is done")).toBeTruthy();
    await act(async () => { fireEvent.keyDown(window, { key: "n" }); });
    await waitFor(() => expect(callbacks.onPlanStep).toHaveBeenCalledOnce());
    expect(callbacks.onPlanStep.mock.calls[0][0]).toMatchObject({ kind: "done" });
    expect(picks).toEqual([]);
  });

  // UX-69 (the live walk partread-3): Today offered three; after the second answer the third was kept for a later check
  // on the learner's own and "today's plan is done" said nothing of it.
  it("the third question offered kept for a check after the second answer: the line under Next says so, with its day", async () => {
    const check = { date: "2026-12-05", count: 1, itemIds: ["pi_3"], learningObjectIds: ["lo_eigen"], kinds: ["certification_cold_probe"] };
    const nextPractice = {
      asOf: "2026-11-21T18:40:00Z", calendar: { zone: "EST", today: "2026-11-21", tomorrow: "2026-11-22", nextDayStartsAt: "2099-11-22T05:00:00Z" },
      reviews: [{ date: "2026-11-30", count: 2, itemIds: ["pi_1", "pi_2"], learningObjectIds: ["lo_eigen"], minutes: null }],
      checks: [check], nextReviewDate: "2026-11-30", writing: { topicCount: 3, learningObjectIds: ["lo_b"] }, waiting: { sectionCount: 0 },
      held: { topicCount: 0, learningObjectIds: [] }
    };
    const base = invoke.getMockImplementation() as (command: string, args: { input?: Record<string, unknown> }) => Promise<unknown>;
    invoke.mockImplementation(async (command: string, args: { input?: Record<string, unknown> }) =>
      command === "get_daily_plan" ? { version: 1, enabled: true, plan: null, nextPractice } : base(command, args));
    show();
    expect(await screen.findByText("today's plan is done")).toBeTruthy();
    expect((await screen.findByTestId("feedback-next-note")).textContent).toBe(
      "1 question from your reading is kept for a check on your own, available from 5 December."
    );
  });

  it("with the plan done and nothing kept for a check, no line is added under Next", async () => {
    library = book({ count: 3, itemIds: ["pi_1", "pi_2", "pi_3"], writing: ["Document"], laterItemIds: ["pi_1", "pi_2", "pi_3"] });
    const base = invoke.getMockImplementation() as (command: string, args: { input?: Record<string, unknown> }) => Promise<unknown>;
    invoke.mockImplementation(async (command: string, args: { input?: Record<string, unknown> }) =>
      command === "get_daily_plan" ? { version: 1, enabled: true, plan: null, nextPractice: null } : base(command, args));
    show();
    expect(await screen.findByText("today's plan is done")).toBeTruthy();
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 20)); });
    expect(screen.queryByTestId("feedback-next-note")).toBeNull();
  });

  it("a step the plan has next is followed as before, and the books are not read", async () => {
    peekStep = NEXT;
    const callbacks = show();
    expect(await screen.findByText("next: Eigenvectors")).toBeTruthy();
    await act(async () => { fireEvent.keyDown(window, { key: "n" }); });
    await waitFor(() => expect(callbacks.onPlanStep).toHaveBeenCalledOnce());
    expect(callbacks.onPlanStep.mock.calls[0][0]).toMatchObject({ kind: "item", practiceItemId: "pi_2" });
    expect(invoke.mock.calls.some(([command]) => command === "get_source_library" || command === "get_today_queue")).toBe(false);
    expect(picks).toEqual([]);
  });
});
