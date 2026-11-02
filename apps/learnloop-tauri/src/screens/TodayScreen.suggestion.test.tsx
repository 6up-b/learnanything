// Teacher TE1b (spec_teacher_v1 §15.1, §19): Today's lesson suggestion card. Shown above the plan only while
// the sidecar says Today may suggest a lesson (`teacher.suggestions`) and the shell can open a lesson; with the
// switch off Today never asks for it (byte-identical Today). The plan fixtures are TodayScreen.plan.test's.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { DailyPlanBodyDto, DailyPlanDto, PlanBlockDto, PlanStepDto } from "../api/dto";
import { clear } from "../api/queryCache";
import { TodayScreen } from "./TodayScreen";
import { setAlgoConfig } from "../app/algoConfig";

const { api } = vi.hoisted(() => ({
  api: {
    getDailyPlan: vi.fn(),
    getTodayHeadline: vi.fn(),
    getTodayQueue: vi.fn(),
    goalsList: vi.fn(),
    getDecayPressure: vi.fn(),
    getQueueRevision: vi.fn(),
    listIngestBatches: vi.fn(),
    startSession: vi.fn(),
    nextPlanItem: vi.fn(),
    planMoreNew: vi.fn(),
    planKeepGoing: vi.fn(),
    lessonSuggestion: vi.fn(),
    lessonSuggestionRespond: vi.fn()
  }
}));
vi.mock("../api/client", () => ({ api }));
vi.mock("../components/InboxStrip", () => ({ InboxStrip: () => null }));

function readingBlock(): PlanBlockDto {
  return {
    id: "blk_read",
    ordinal: 1,
    lane: "new",
    action: "read",
    subtype: null,
    chosenBy: "reading",
    why: "new: continue reading",
    whyKind: "computed",
    fallback: false,
    estMinutes: 7,
    status: "current",
    startedAt: null,
    endedAt: null,
    outcome: null,
    reading: {
      sourceId: "src_prob",
      extractionId: "ext_prob",
      sectionId: "u3",
      sectionTitle: "Sample spaces and Pebble World",
      wordsLeft: 1400,
      partial: false,
      startSpanId: "s30"
    },
    learningObjectTitles: [],
    items: [],
    displacedCount: 0
  };
}

function body(overrides: Partial<DailyPlanBodyDto> = {}): DailyPlanBodyDto {
  return {
    id: "plan_1",
    localDate: "2026-10-13",
    kind: "keep_going",
    status: "open",
    stopReason: null,
    parentPlanId: null,
    minutesBudget: 10,
    rememberedMinutes: 25,
    minutesSource: "carried",
    minuteChoices: [10, 15, 25, 40, 60],
    minutesLeft: 10,
    split: { rule: "split_v1", line: "10 min · new 7", lanesAllowed: ["new"], requestedMinutes: 0, lanes: [] },
    admission: { admittedCount: 0, exemptRequests: 0, stoppedBy: null, floorApplied: false, reviewLoadPerDay: null, ceilingMinutes: null, override: null },
    blocks: [readingBlock()],
    currentBlockId: "blk_read",
    projected: [],
    blockCountEstimate: 1,
    firstBlock: { title: "Sample spaces and Pebble World", lane: "new", itemCount: 0, estMinutes: 7, reading: true },
    nextStep: null,
    totals: { plannedMinutes: 7, plannedItems: 0, doneItems: 0, skippedItems: 0, displacedItems: 0, readingBlocks: 1, readingBlocksEnded: 0, estMinutesDone: 0, actualMinutes: 0 },
    reentry: null,
    source: null,
    chooser: null,
    ...overrides
  };
}

function plan(planBody: DailyPlanBodyDto): DailyPlanDto {
  return {
    version: 1,
    enabled: true,
    headlineEnabled: false,
    localDate: "2026-10-13",
    plan: planBody,
    day: { plans: 1, kinds: [planBody.kind], complete: planBody.status !== "open", ...planBody.totals },
    streak: { current: 1, activeToday: true, longest: 1 }
  };
}

function show(dto: DailyPlanDto, session: { sessionId: string } | null = null, onStartLesson?: () => void) {
  api.getDailyPlan.mockResolvedValue(dto);
  const props = {
    onOpenPractice: vi.fn(),
    onOpenPrimedPractice: vi.fn(),
    onAsk: vi.fn(),
    onEndSession: vi.fn(),
    onInspect: vi.fn(),
    onOpenPlanReading: vi.fn(),
    onRequireSession: vi.fn(),
    onBeginSession: vi.fn(),
    onError: vi.fn(),
    ...(onStartLesson ? { onStartLesson } : {})
  };
  render(
    <TodayScreen
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      session={session as any}
      algorithmVersion="mvp-0.12"
      {...props}
    />
  );
  return props;
}

beforeEach(() => {
  api.getTodayHeadline.mockResolvedValue({ version: 1, enabled: false });
  api.getTodayQueue.mockResolvedValue({ version: 1, generatedAt: "2026-10-13T12:00:00Z", sessionId: null, sections: [], totalItems: 0 });
  api.goalsList.mockResolvedValue({ version: 1, goals: [] });
  api.getDecayPressure.mockResolvedValue({ version: 1, pressure: null });
  api.getQueueRevision.mockResolvedValue({ version: 1, revision: 1 });
  api.listIngestBatches.mockResolvedValue({ version: 1, batches: [] });
});

afterEach(() => {
  cleanup();
  clear();
  vi.useRealTimers();
  setAlgoConfig({});
  vi.clearAllMocks();
});

async function flush() {
  await act(async () => {
    for (let i = 0; i < 10; i += 1) await Promise.resolve();
  });
}

const CARD = {
  decisionId: "dec1", day: "2026-10-13", minutes: 15, whyLabel: "Suggested by LearnLoop's planner",
  suggestion: { ref: "lesson:lo_eigen", title: "Eigenvalues", learningObjectIds: ["lo_eigen"], reason: "new_goal",
                why: "It's on your goal and you haven't started it yet." },
  alternatives: []
};

it("with the switch on, the day's card shows above the plan", async () => {
  setAlgoConfig({ teacher: { lessons: true, suggestions: true } });
  api.lessonSuggestion.mockResolvedValue({ suggestion: CARD });
  show(plan(body()), { sessionId: "s1" }, vi.fn());
  await flush();
  expect(api.lessonSuggestion).toHaveBeenCalledWith({ sessionId: "s1" });
  expect(screen.getByTestId("lesson-suggestion-card").textContent).toContain("Learn Eigenvalues now? (about 15 min)");
  expect(screen.getAllByText("Sample spaces and Pebble World", { exact: false }).length).toBeGreaterThan(0);
});

it("with the switch off (or lessons off), Today never asks for a card", async () => {
  for (const config of [{ teacher: { lessons: true } }, {}]) {
    setAlgoConfig(config);
    show(plan(body()), { sessionId: "s1" }, vi.fn());
    await flush();
    expect(screen.queryByTestId("lesson-suggestion-card")).toBeNull();
    cleanup();
    clear();
  }
  expect(api.lessonSuggestion).not.toHaveBeenCalled();
});

it("without a way to open a lesson, Today asks for no card", async () => {
  setAlgoConfig({ teacher: { lessons: true, suggestions: true } });
  show(plan(body()), { sessionId: "s1" });
  await flush();
  expect(api.lessonSuggestion).not.toHaveBeenCalled();
});
