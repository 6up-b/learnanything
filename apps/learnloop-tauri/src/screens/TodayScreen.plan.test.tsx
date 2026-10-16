// UX Phase 1 usability round 2 (docs/reviews/ux-phase1.md, "Usability round 2
// fixes"): Today's plan, on the first-run path.
//
// R1 — after "more new material" a red "query is disabled" banner appeared with
//      no failed backend call and stayed on every tab: a background batch
//      finished while the plan view had its full-list read turned off, and the
//      list refresh reported the disabled read as an error.
// R2 — Today's own "begin ↵" bounced the learner to Start with "Begin today's
//      plan on Start first."; Today's begin must begin the plan.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { DailyPlanBodyDto, DailyPlanDto, PlanBlockDto, PlanStepDto } from "../api/dto";
import { clear } from "../api/queryCache";
import { TodayScreen } from "./TodayScreen";

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
    planKeepGoing: vi.fn()
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

function show(dto: DailyPlanDto, session: { sessionId: string } | null = null) {
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
    onError: vi.fn()
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
});

async function flush() {
  await act(async () => {
    for (let i = 0; i < 10; i += 1) await Promise.resolve();
  });
}

it("R1: a background batch finishing under the plan view raises no 'query is disabled' error", async () => {
  vi.useFakeTimers();
  api.listIngestBatches
    .mockResolvedValueOnce({ version: 1, batches: [{ id: "b1", status: "running", workflowType: "practice_expansion" }] })
    .mockResolvedValue({ version: 1, batches: [{ id: "b1", status: "completed", workflowType: "practice_expansion" }] });
  const props = show(plan(body({ status: "complete", currentBlockId: null })), { sessionId: "s1" });
  await flush();
  expect(screen.getByText("more new material")).toBeTruthy();

  // The batch poll runs every 7 s: the practice items it wrote land now.
  await act(async () => {
    await vi.advanceTimersByTimeAsync(7_100);
  });
  await flush();

  expect(api.listIngestBatches.mock.calls.length).toBeGreaterThanOrEqual(2);
  expect(props.onError).not.toHaveBeenCalled();
  // The full list is not shown, so it is not read either.
  expect(api.getTodayQueue).not.toHaveBeenCalled();
});

it("R2: Today's begin starts today's plan itself instead of sending the learner to Start", async () => {
  const step: PlanStepDto = {
    kind: "reading",
    planId: "plan_1",
    blockId: "blk_read",
    blockOrdinal: 1,
    reading: readingBlock().reading!,
    estMinutes: 7,
    boundary: true
  };
  api.startSession.mockResolvedValue({ sessionId: "s_new" });
  api.nextPlanItem.mockResolvedValue({ ...plan(body()), step });
  const props = show(plan(body()), null);
  await flush();

  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "begin ↵" }));
  });
  await flush();

  expect(api.startSession).toHaveBeenCalledWith({ availableMinutes: 10 });
  expect(api.nextPlanItem).toHaveBeenCalledWith({ sessionId: "s_new", serve: true });
  expect(props.onBeginSession).toHaveBeenCalledWith({ sessionId: "s_new" }, step);
  expect(props.onRequireSession).not.toHaveBeenCalled();
  expect(props.onError).not.toHaveBeenCalled();
});

it("UX Phase 4 round 8: a waiting plan offers no Begin; Enter starts no session and serves nothing", async () => {
  const waiting = body({
    kind: "normal",
    blocks: [],
    currentBlockId: null,
    firstBlock: null,
    deciding: false,
    waiting: { until: new Date(Date.now() + 5 * 60_000).toISOString(), minutes: 5, practiceItemId: "pi_cold", learningObjectTitle: "Eigenvalues" }
  });
  const props = show(plan(waiting), null);
  await flush();

  expect(screen.getByTestId("plan-waiting").textContent).toContain("Back in 5 min: a question on Eigenvalues.");
  expect(screen.queryByRole("button", { name: "begin ↵" })).toBeNull();
  expect(screen.queryByText("begin")).toBeNull();
  expect(screen.getByText("back in 5 min")).toBeTruthy();

  await act(async () => {
    fireEvent.keyDown(window, { key: "Enter" });
  });
  await flush();

  expect(api.startSession).not.toHaveBeenCalled();
  expect(api.nextPlanItem).not.toHaveBeenCalled();
  expect(props.onBeginSession).not.toHaveBeenCalled();
  expect(props.onRequireSession).not.toHaveBeenCalled();
});
