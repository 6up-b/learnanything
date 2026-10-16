// Daily-loop DL1: Today's plan view, block lines, the done screen and keep
// going (spec_daily_loop_v1.md §6.5, §6.7, §7). Gate G3: every number on screen
// is one the plan DTO carries; the view computes none.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { DailyPlanBodyDto, DailyPlanDto, PlanBlockDto, TodayHeadlineDto } from "../../api/dto";
import { DailyPlanView, type DailyPlanViewProps } from "./DailyPlanView";

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

function block(overrides: Partial<PlanBlockDto> = {}): PlanBlockDto {
  return {
    id: "blk_1",
    ordinal: 1,
    lane: "maintain",
    action: "maintain",
    subtype: null,
    chosenBy: "lane_quota",
    why: "maintain: 2 reviews past their 90% recall target (Eigenvalues)",
    whyKind: "computed",
    fallback: false,
    estMinutes: 7.4,
    status: "current",
    startedAt: null,
    endedAt: null,
    outcome: null,
    reading: null,
    learningObjectTitles: ["Eigenvalues"],
    items: [
      { practiceItemId: "pi_a", learningObjectId: "lo_e", learningObjectTitle: "Eigenvalues", practiceMode: "short_answer", promptPreview: "", lane: "maintain", estMinutes: 3.5, state: "done", origin: "chooser", servedAt: null, doneAt: null },
      { practiceItemId: "pi_b", learningObjectId: "lo_e", learningObjectTitle: "Eigenvectors", practiceMode: "short_answer", promptPreview: "", lane: "maintain", estMinutes: 3.9, state: "planned", origin: "chooser", servedAt: null, doneAt: null }
    ],
    displacedCount: 0,
    ...overrides
  };
}

function plan(overrides: Partial<DailyPlanBodyDto> = {}): DailyPlanBodyDto {
  return {
    id: "plan_1",
    localDate: "2026-10-12",
    kind: "normal",
    status: "open",
    stopReason: null,
    parentPlanId: null,
    minutesBudget: 25,
    rememberedMinutes: 25,
    minutesSource: "carried",
    minuteChoices: [10, 15, 25, 40, 60],
    minutesLeft: 17.6,
    split: {
      rule: "split_v1",
      line: "25 min · maintain 13 · repair 4 · new 4 · push 4",
      lanesAllowed: ["repair", "maintain", "new", "push"],
      requestedMinutes: 0,
      lanes: [
        { lane: "repair", minutes: 4, displayMinutes: 4, load: 4, cap: 7.5, reason: "repair: about 4 min of work" },
        { lane: "maintain", minutes: 13, displayMinutes: 13, load: 30, cap: 15, reason: "maintain: about 30 min of work due" },
        { lane: "new", minutes: 4, displayMinutes: 4, load: 4, cap: 4, reason: "new: about 4 min admitted" },
        { lane: "push", minutes: 4, displayMinutes: 4, load: 9, cap: null, reason: "push: about 9 min toward your goals" }
      ]
    },
    admission: { admittedCount: 1, exemptRequests: 0, stoppedBy: "load_ceiling", floorApplied: false, reviewLoadPerDay: 12, ceilingMinutes: 20, override: null },
    blocks: [block()],
    currentBlockId: "blk_1",
    projected: [
      { ordinal: 2, lane: "new", estMinutes: 6.2, itemCount: 2, learningObjectTitles: ["Spectral theorem"], readingTitle: null, why: "new: 2 new items" },
      { ordinal: 3, lane: "push", estMinutes: 4, itemCount: 1, learningObjectTitles: ["SVD"], readingTitle: null, why: "push" }
    ],
    blockCountEstimate: 3,
    firstBlock: { title: "Eigenvalues", lane: "maintain", itemCount: 2, estMinutes: 7.4, reading: false },
    nextStep: null,
    totals: { plannedMinutes: 7.4, plannedItems: 2, doneItems: 1, skippedItems: 0, displacedItems: 0, readingBlocks: 0, readingBlocksEnded: 0, estMinutesDone: 3.5, actualMinutes: 2.6 },
    reentry: null,
    source: "legacy_lanes_v1",
    chooser: "lane_quota_v1",
    ...overrides
  };
}

function data(body: DailyPlanBodyDto, extra: Partial<DailyPlanDto> = {}): DailyPlanDto {
  return {
    version: 1,
    enabled: true,
    headlineEnabled: true,
    localDate: "2026-10-12",
    plan: body,
    day: { plans: 1, kinds: [body.kind], complete: body.status !== "open", ...body.totals },
    streak: { current: 6, activeToday: true, longest: 9 },
    ...extra
  };
}

const HEADLINE: TodayHeadlineDto = {
  version: 1,
  enabled: true,
  line: "14 demonstrated · 3 assumed · 9 learning · 6 untested — expected recall today 87%",
  expectedRecallTooltip: "a model estimate, not a test"
};

function show(dto: DailyPlanDto, overrides: Partial<DailyPlanViewProps> = {}) {
  const props: DailyPlanViewProps = {
    data: dto,
    headline: HEADLINE,
    onContinue: vi.fn(),
    onSetMinutes: vi.fn(),
    onKeepGoing: vi.fn(),
    onDone: vi.fn(),
    onMoreNew: vi.fn(),
    onShowList: vi.fn(),
    onSkip: vi.fn(),
    ...overrides
  };
  render(<DailyPlanView {...props} />);
  return props;
}

async function press(key: string) {
  await act(async () => { fireEvent.keyDown(window, { key }); });
}

it("shows the split line, its why and the headline exactly as the DTO says", () => {
  show(data(plan()));
  expect(screen.getByTestId("plan-split-line").textContent).toBe("25 min · maintain 13 · repair 4 · new 4 · push 4");
  fireEvent.click(screen.getByRole("button", { name: "(why)" }));
  const why = screen.getByTestId("plan-split-why").textContent ?? "";
  expect(why).toContain("maintain 13 min — maintain: about 30 min of work due");
  const headline = screen.getByTestId("plan-headline");
  expect(headline.textContent).toBe(HEADLINE.line);
  expect(headline.getAttribute("title")).toBe("a model estimate, not a test");
})

it("shows the block line, the current block's items and the next block, all labelled about", () => {
  show(data(plan()));
  expect(screen.getByTestId("plan-block-line").textContent).toContain("Block 1 of about 3 · maintain · about 7 min");
  const items = screen.getAllByTestId("plan-item");
  expect(items.map((item) => item.getAttribute("data-state"))).toEqual(["done", "planned"]);
  expect(items[1].getAttribute("aria-current")).toBe("step");
  expect(screen.getByTestId("plan-next").textContent).toBe("next: new · about 6 min · then 1 more");
  expect(screen.queryByText(/overdue/i)).toBeNull();
});

// Router R2a: a block the router's rule chose says why in plain words, with the
// receipts one more click away (behind "details"); DL1's blocks have none.
it("shows a router block's plain why with its receipts behind details", () => {
  const routed = block({
    chosenBy: "staged",
    why: "Eigenvalues again, before it slips.",
    whyDetails: "Picked by the plan's usual rule; no model was asked. Receipt: learnloop router card --decision rd_1"
  });
  show(data(plan({ blocks: [routed], currentBlockId: routed.id })));
  fireEvent.click(screen.getByRole("button", { name: "why" }));
  const why = screen.getByTestId("plan-block-why");
  expect(why.textContent).toContain("Eigenvalues again, before it slips.");
  const details = screen.getByTestId("plan-block-why-details");
  expect(details.hasAttribute("open")).toBe(false);
  expect(details.textContent).toContain("router card --decision rd_1");
});

it("shows no details under a DL1 block's why", () => {
  show(data(plan()));
  fireEvent.click(screen.getByRole("button", { name: "why" }));
  expect(screen.queryByTestId("plan-block-why-details")).toBeNull();
});

it("continues on Enter, opens the full list on l and steps the minutes with the arrows", async () => {
  const props = show(data(plan()));
  await press("Enter");
  expect(props.onContinue).toHaveBeenCalledOnce();
  await press("l");
  expect(props.onShowList).toHaveBeenCalledOnce();
  await press("ArrowRight");
  expect(props.onSetMinutes).toHaveBeenCalledWith(40);
  fireEvent.click(screen.getByRole("radio", { name: "10m" }));
  expect(props.onSetMinutes).toHaveBeenLastCalledWith(10);
  fireEvent.click(screen.getByRole("button", { name: "skip this item" }));
  expect(props.onSkip).toHaveBeenCalledWith("pi_b");
});

it("shows a reading block as a partial continue line", () => {
  const reading = block({
    id: "blk_r",
    lane: "new",
    estMinutes: 12,
    items: [],
    reading: { sourceId: "src", extractionId: "ext", sectionId: "s2", sectionTitle: "§3.2 Bayes", wordsLeft: 3000, partial: true, fullMinutes: 25 }
  });
  const onSkipReading = vi.fn();
  show(data(plan({ blocks: [reading], currentBlockId: "blk_r" })), { onSkipReading });
  expect(screen.getByTestId("plan-block-line").textContent).toContain("reading §3.2 Bayes · about 12 min (of about 25 min)");
  fireEvent.click(screen.getByRole("button", { name: "skip" }));
  expect(onSkipReading).toHaveBeenCalledOnce();
});

it("opens a re-entry plan with the survival-first panel and no overdue count or streak", () => {
  const reentry = plan({
    kind: "reentry",
    reentry: { gapDays: 23, solidCount: 41, slippedCount: 6, slippedNames: ["eigenvalues", "Bayes' rule"], namedBy: "retrievability", target: 0.9, planMinutes: 11.6, planItems: 7 }
  });
  show(data(reentry));
  const panel = screen.getByTestId("plan-reentry").textContent ?? "";
  expect(panel).toBe(
    "Welcome back — 23 days. Still solid: 41. Slipped below target: 6 (eigenvalues, Bayes' rule, …). Today: a short re-entry, about 12 min, 7 items."
  );
  expect(panel).not.toMatch(/overdue|streak/i);
});

it("ends with the done screen: the day's own figures, the streak, keep going and done", async () => {
  const done = plan({ status: "complete", currentBlockId: null, blocks: [block({ status: "done" })], projected: [] });
  const dto = data(done, { day: { plans: 1, kinds: ["normal"], complete: true, plannedMinutes: 25, plannedItems: 9, doneItems: 9, skippedItems: 0, displacedItems: 0, readingBlocks: 0, readingBlocksEnded: 0, estMinutesDone: 24, actualMinutes: 26.3 } });
  const props = show(dto);
  expect(screen.getByTestId("plan-done-title").textContent).toBe("Today complete");
  expect(screen.getByTestId("plan-done-figures").textContent).toBe(" · 26 min · 9 items");
  expect(screen.getByTestId("plan-done").textContent).toContain("● 6 days streak · today ✓");
  await press("Enter");
  expect(props.onKeepGoing).toHaveBeenCalledOnce();
  await press("d");
  expect(props.onDone).toHaveBeenCalledOnce();
  fireEvent.click(screen.getByRole("button", { name: "more new material" }));
  expect(props.onMoreNew).toHaveBeenCalledWith(false);
});

it("shows the more-new trade-off before adding anything", () => {
  const done = plan({ status: "complete", currentBlockId: null, projected: [] });
  const onMoreNew = vi.fn();
  show(data(done), { onMoreNew, moreNewPreview: { items: 3, estMinutes: 10.5, addsMinutesPerDay: 3.75, horizonDays: 14, available: true } });
  expect(screen.getByTestId("plan-more-new").textContent).toContain("adds about 4 min/day of reviews for two weeks");
  fireEvent.click(screen.getByRole("button", { name: "add them" }));
  expect(onMoreNew).toHaveBeenCalledWith(true);
});

it("shows a small trade-off as computed, never rounded up to a minute (DL1 review F9)", () => {
  const done = plan({ status: "complete", currentBlockId: null, projected: [] });
  show(data(done), { moreNewPreview: { items: 1, estMinutes: 1.5, addsMinutesPerDay: 0.32, horizonDays: 14, available: true } });
  expect(screen.getByTestId("plan-more-new").textContent).toContain("adds about 0.3 min/day of reviews");
});

it("while the next block is being chosen, says so and lets Begin decide it at once (router R2b)", () => {
  const deciding = plan({ blocks: [], currentBlockId: null, deciding: true, firstBlock: null });
  const props = show(data(deciding));
  expect(screen.getByTestId("plan-choosing").textContent).toContain("Choosing the next block…");
  fireEvent.click(screen.getByRole("button", { name: "begin ↵" }));
  expect(props.onContinue).toHaveBeenCalledOnce();
});

it("offers no Begin while no block is being chosen", () => {
  show(data(plan({ blocks: [], currentBlockId: null, deciding: false, firstBlock: null })));
  expect(screen.getByTestId("plan-choosing")).toBeTruthy();
  expect(screen.queryByRole("button", { name: "begin ↵" })).toBeNull();
});

it("says nothing is due on an empty plan, and offers keep going", () => {
  const empty = plan({ status: "complete", currentBlockId: null, blocks: [], projected: [], totals: { plannedMinutes: 0, plannedItems: 0, doneItems: 0, skippedItems: 0, displacedItems: 0, readingBlocks: 0, readingBlocksEnded: 0, estMinutesDone: 0, actualMinutes: 0 } });
  show(data(empty));
  expect(screen.getByTestId("plan-done-title").textContent).toBe("Nothing due today");
  expect(screen.getByRole("button", { name: "keep going ↵" })).toBeTruthy();
});

it("says re-entry done and offers to keep going after a re-entry plan", () => {
  const reentryDone = plan({ kind: "reentry", status: "complete", currentBlockId: null, projected: [] });
  show(data(reentryDone));
  expect(screen.getByTestId("plan-done-title").textContent).toBe("Re-entry done. Keep going?");
  expect(screen.queryByRole("button", { name: "more new material" })).toBeNull();
});

it("UX Phase 4 round 7: a plan waiting for a hold to lift says when, in plain words, and is not done", () => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-10-12T10:00:00Z"));
  try {
    const waiting = plan({
      blocks: [],
      currentBlockId: null,
      deciding: false,
      firstBlock: null,
      waiting: { until: "2026-10-12T10:04:30Z", minutes: 5, practiceItemId: "pi_cold", learningObjectTitle: "Eigenvalues" }
    });
    show(data(waiting));
    expect(screen.getByTestId("plan-waiting").textContent).toBe(
      "Nothing to do right now. Back in 5 min: a question on Eigenvalues."
    );
    expect(screen.queryByTestId("plan-choosing")).toBeNull();
    expect(screen.queryByTestId("plan-done")).toBeNull();
    expect(screen.queryByRole("button", { name: "begin ↵" })).toBeNull();
  } finally {
    vi.useRealTimers();
  }
});

it("UX Phase 4 round 8: while waiting, Enter does not continue and the key bar says when it is back", async () => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-10-12T10:00:00Z"));
  try {
    const waiting = plan({
      blocks: [],
      currentBlockId: null,
      deciding: false,
      firstBlock: null,
      waiting: { until: "2026-10-12T10:04:30Z", minutes: 5, practiceItemId: "pi_cold", learningObjectTitle: "Eigenvalues" }
    });
    const props = show(data(waiting));
    await act(async () => {
      fireEvent.keyDown(window, { key: "Enter" });
    });
    expect(props.onContinue).not.toHaveBeenCalled();
    expect(props.onKeepGoing).not.toHaveBeenCalled();
    expect(screen.getByText("back in 5 min")).toBeTruthy();
    expect(screen.queryByText("begin")).toBeNull();
  } finally {
    vi.useRealTimers();
  }
});
