// UX Phase 3 (docs/specs/ux_learnloop_v1.md §7.1, W4, §4.2 rules 9-10, §10
// 3.1-3.4): Today in the simple shell. One sentence and Enter: the plan in
// minutes, with no count of waiting things anywhere; re-entry after a break
// as a short plan with no debt screen; the lanes, the split and the reasons
// behind why?; Begin, the minutes, keep going and the full list calling
// exactly the RPCs classic's Start and Today call; threads, the goal card and
// the captures line; the first-run, done, loading and error states.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { DailyPlanBodyDto, DailyPlanDto, GoalDto, PlanBlockDto, QueueSnapshot, QuestionQueueRowDto, ScheduledItemDto, WorkbenchOpenProblemDto } from "../../api/dto";
import { clear, invalidateAll } from "../../api/queryCache";
import { setRenderedShell } from "../../app/algoConfig";
import { findJargon } from "../../copy/denyList";

const { fns, inbox } = vi.hoisted(() => ({ fns: {} as Record<string, ReturnType<typeof vi.fn>>, inbox: { real: false } }));

vi.mock("../../api/client", () => ({
  api: new Proxy(
    {},
    {
      get: (_target, name: string) => {
        if (!(name in fns)) fns[name] = vi.fn(() => new Promise(() => undefined));
        return fns[name];
      }
    }
  )
}));
// The inbox is a word here, except where a test asks for the real strip
// (fix round 1, F5: what the learner sees when captures are expanded).
vi.mock("../../components/InboxStrip", async () => {
  const real = await vi.importActual<typeof import("../../components/InboxStrip")>("../../components/InboxStrip");
  return {
    InboxStrip: (props: Parameters<typeof real.InboxStrip>[0]) =>
      inbox.real ? <real.InboxStrip {...props} /> : <div data-testid="inbox-strip">inbox</div>
  };
});
vi.mock("../../components/GoalBanner", async () => {
  const real = await vi.importActual<typeof import("../../components/GoalBanner")>("../../components/GoalBanner");
  return { ...real, GoalBanner: () => <div data-testid="goal-banner">banner</div> };
});
vi.mock("../../components/GoalWizard", () => ({ GoalWizard: () => <div data-testid="goal-wizard" /> }));

import { TodayPlace, type TodayPlaceProps } from "./TodayPlace";

/** No count of waiting things (rule 10), no lane names, no percentages (rule 9). */
const WAITING_WORDS = /due now|probe queue|later today|follow-ups?\b|\bqueue\b|overdue|backlog|to review|pending|slipped|\bitems?\b/i;
const LANE_WORDS = /\b(maintain|repair|push)\b|\bnew \d/i;

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
    whyDetails: "Receipt: learnloop router card --decision d1",
    fallback: false,
    estMinutes: 7.4,
    status: "current",
    startedAt: null,
    endedAt: null,
    outcome: null,
    reading: null,
    learningObjectTitles: ["Eigenvalues"],
    items: [
      { practiceItemId: "pi_a", learningObjectId: "lo_e", learningObjectTitle: "Eigenvalues", practiceMode: "short_answer", promptPreview: "", lane: "maintain", estMinutes: 3.5, state: "planned", origin: "chooser", servedAt: null, doneAt: null },
      { practiceItemId: "pi_b", learningObjectId: "lo_e", learningObjectTitle: "Eigenvalues", practiceMode: "short_answer", promptPreview: "", lane: "maintain", estMinutes: 3.9, state: "planned", origin: "chooser", servedAt: null, doneAt: null }
    ],
    displacedCount: 0,
    ...overrides
  };
}

function readingBlock(overrides: Partial<PlanBlockDto> = {}): PlanBlockDto {
  return block({
    id: "blk_r",
    lane: "new",
    action: "read",
    why: "new: the next section of Probability",
    whyDetails: null,
    estMinutes: 12,
    reading: { sourceId: "src_prob", extractionId: "ext_prob", sectionId: "s54", sectionTitle: "§5.4 Mixtures", wordsLeft: 2400, partial: false, startSpanId: "sp1", spansSeen: 3, spanCount: 20 },
    learningObjectTitles: [],
    items: [],
    ...overrides
  });
}

function body(overrides: Partial<DailyPlanBodyDto> = {}): DailyPlanBodyDto {
  return {
    id: "plan_1",
    localDate: "2026-10-26",
    kind: "normal",
    status: "open",
    stopReason: null,
    parentPlanId: null,
    minutesBudget: 25,
    rememberedMinutes: 25,
    minutesSource: "carried",
    minuteChoices: [10, 15, 25, 40, 60],
    minutesLeft: 25,
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
    admission: { admittedCount: 1, exemptRequests: 0, stoppedBy: null, floorApplied: false, reviewLoadPerDay: 12, ceilingMinutes: 20, override: null },
    blocks: [readingBlock({ status: "current" }), block({ id: "blk_2", ordinal: 2, status: "upcoming" })],
    currentBlockId: "blk_r",
    projected: [{ ordinal: 3, lane: "repair", estMinutes: 4, itemCount: 1, learningObjectTitles: ["Conditional probability"], readingTitle: null, why: "repair: a mix-up named last week" }],
    blockCountEstimate: 3,
    firstBlock: { title: "§5.4 Mixtures", lane: "new", itemCount: 0, estMinutes: 12, reading: true },
    nextStep: null,
    totals: { plannedMinutes: 23.4, plannedItems: 3, doneItems: 0, skippedItems: 0, displacedItems: 0, readingBlocks: 1, readingBlocksEnded: 0, estMinutesDone: 0, actualMinutes: 0 },
    reentry: null,
    source: "legacy_lanes_v1",
    chooser: "lane_quota_v1",
    ...overrides
  };
}

function dto(plan: DailyPlanBodyDto | null, extra: Partial<DailyPlanDto> = {}): DailyPlanDto {
  return {
    version: 1,
    enabled: plan !== null,
    headlineEnabled: true,
    localDate: "2026-10-26",
    plan,
    day: plan ? { plans: 1, kinds: [plan.kind], complete: plan.status !== "open", ...plan.totals } : undefined,
    streak: { current: 4, activeToday: false, longest: 9 },
    ...extra
  };
}

function scheduled(index: number, overrides: Partial<ScheduledItemDto> = {}): ScheduledItemDto {
  return {
    schedulerSlateId: "slate_1",
    schedulerCandidateId: `cand_${index}`,
    practiceItemId: `pi_${index}`,
    learningObjectId: `lo_${index}`,
    learningObjectTitle: `Topic ${index}`,
    subject: null,
    practiceMode: "free_recall",
    selectedMode: "free_recall",
    priority: 0.412,
    components: { forgettingRisk: 0.2, recentError: 0, probeEig: 0 } as ScheduledItemDto["components"],
    readinessFactor: null,
    plainEnglish: ["due"],
    dominantReason: "due",
    mastery: 0.4,
    masteryVariance: 0.1,
    dueAt: null,
    dueStatus: "due",
    isProbe: false,
    isFollowup: false,
    followupKind: null,
    ...overrides
  };
}

function queue(items: ScheduledItemDto[]): QueueSnapshot {
  return { version: 1, generatedAt: "2026-10-26T18:00:00Z", sessionId: null, sections: [{ title: "Due", items }], totalItems: items.length };
}

const SESSION = { version: 1, sessionId: "s1", startedAt: "2026-10-26T18:00:00Z", endedAt: null, energy: null, sleepQuality: null, availableMinutes: 25, notesMdPath: null, checkpoint: null };
const STARTED = { ...SESSION, sessionId: "s_new" };

function question(id: string, overrides: Partial<QuestionQueueRowDto> = {}): QuestionQueueRowDto {
  return {
    id,
    context: "reader",
    questionMd: "Why is the density of a sum a convolution?",
    answerMd: null,
    answerStatus: "answered",
    resolution: "open",
    questionType: null,
    practiceItemId: null,
    attemptId: null,
    noteId: "note_1",
    sessionId: null,
    savedNoteId: null,
    createdAt: "2026-10-25T10:00:00Z",
    promotion: null,
    promotionRequest: null,
    promotionTargetIds: [],
    sourceCitation: { extractionId: "ext_prob", spanId: "sp9", label: "§5.4", sourceId: "src_prob" },
    ...overrides
  };
}

function problem(id: string, overrides: Partial<WorkbenchOpenProblemDto> = {}): WorkbenchOpenProblemDto {
  return {
    sessionId: id,
    status: "open",
    practiceItemId: null,
    stemMd: "Exercise 5.9: show that the sum of two independent Poissons is Poisson.",
    origin: "reader",
    entry: "work_through",
    extractionId: "ext_prob",
    spanIds: ["sp12"],
    importStatus: "none",
    sourceVisible: false,
    stepCount: 3,
    createdAt: "2026-10-24T10:00:00Z",
    updatedAt: "2026-10-26T09:00:00Z",
    unfinished: false,
    sourceId: "src_prob",
    ...overrides
  };
}

function goal(overrides: Partial<GoalDto> = {}): GoalDto {
  return {
    id: "goal_1",
    title: "Probability midterm",
    intentSentence: null,
    creationSource: "learner",
    resolvedQuestSentence: null,
    questBasis: null,
    status: "active",
    priority: 1,
    targetRecall: 0.85,
    dueAt: "2026-11-14T12:00:00Z",
    facetScope: { concepts: [], facets: [] },
    exam: { enabled: true, itemCount: 10 },
    practicableItemCount: 12,
    createdAt: "2026-10-01T00:00:00Z",
    updatedAt: "2026-10-20T00:00:00Z",
    report: { onTrackCount: 9, total: 9, onTrackFraction: 1, atRiskCount: 0, horizon: "due", dueAt: "2026-11-14T12:00:00Z", attainmentFraction: 0.98 },
    ...overrides
  };
}

function apis(plan: DailyPlanDto | (() => Promise<DailyPlanDto>), extra: Record<string, ReturnType<typeof vi.fn>> = {}) {
  const getDailyPlan = typeof plan === "function" ? vi.fn(plan) : vi.fn(async () => plan);
  Object.assign(fns, {
    getDailyPlan,
    getTodayHeadline: vi.fn(async () => ({ version: 1, enabled: true, line: "14 demonstrated · 9 learning — expected recall today 87%" })),
    getSourceLibrary: vi.fn(async () => ({ sources: [{ sourceId: "src_prob", title: "Probability" }], pending: [] })),
    goalsList: vi.fn(async () => ({ version: 1, goals: [] })),
    listQuestionQueue: vi.fn(async () => ({ version: 1, questions: [], openCount: 0 })),
    workbenchOpenProblems: vi.fn(async () => ({ version: 1, problems: [] })),
    getInboxSummary: vi.fn(async () => ({ count: 0, newCount: 0, captures: [], deletePending: [], deletePendingCount: 0, pinnedVault: null, vaultMismatch: false, enabled: true })),
    getStartSummary: vi.fn(async () => ({ version: 1, rememberedMinutes: 15, minutesSource: "last_session", minutesPresets: [10, 15, 25, 40, 60], minuteChoices: [10, 15, 25, 40, 60], streak: { current: 4, activeToday: false, longest: 9 } })),
    getTodayQueue: vi.fn(async () => queue([scheduled(1), scheduled(2)])),
    startSession: vi.fn(async () => STARTED),
    nextPlanItem: vi.fn(async () => ({ ...plan, step: { kind: "item", planId: "plan_1", blockId: "blk_2", practiceItemId: "pi_a", learningObjectId: "lo_e", origin: "chooser", schedulerCandidateId: "cand_a", presentationId: "pres_a", boundary: false } })),
    setPlanMinutes: vi.fn(async () => plan),
    planKeepGoing: vi.fn(async () => plan),
    planMoreNew: vi.fn(async () => ({ ...plan, preview: { items: 3, estMinutes: 9, addsMinutesPerDay: 0.8, horizonDays: 14, available: true } })),
    planLearnerPick: vi.fn(async () => ({ step: { kind: "item", planId: "plan_1", blockId: "blk_pick", practiceItemId: "pi_2", learningObjectId: "lo_2", origin: "learner_pick", schedulerCandidateId: "cand_pick", presentationId: "pres_pick", boundary: false } })),
    planReadingEnded: vi.fn(async () => plan),
    endSession: vi.fn(async () => ({ sessionId: "s1" })),
    getExamStatus: vi.fn(async () => ({ version: 1, goalId: "goal_1", inWindow: true, daysUntilDue: 19, pastDueGrace: false, existingSessionId: null, poolItemCount: 10, uncoveredFacets: [], reservationDeferred: false, reservableCandidateCount: 10 })),
    ...extra
  });
  return fns;
}

function show(overrides: Partial<TodayPlaceProps> = {}) {
  const props: TodayPlaceProps = {
    session: null,
    streak: { current: 4, activeToday: false, longest: 9 },
    onBeginSession: vi.fn(),
    onOpenPractice: vi.fn(),
    onOpenPlanReading: vi.fn(),
    onEndSession: vi.fn(),
    onAdd: vi.fn(),
    onOpenPassage: vi.fn(),
    onResumeProblem: vi.fn(),
    onAsk: vi.fn(),
    onTakeExam: vi.fn(),
    onError: vi.fn(),
    ...overrides
  };
  render(<TodayPlace {...props} />);
  return props;
}

async function press(init: KeyboardEventInit) {
  await act(async () => {
    window.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, cancelable: true, ...init }));
  });
}

async function flush() {
  await act(async () => {
    for (let i = 0; i < 10; i += 1) await Promise.resolve();
  });
}

function surface(): string {
  return screen.getByTestId("today-place").textContent ?? "";
}

beforeEach(() => {
  for (const key of Object.keys(fns)) delete fns[key];
  inbox.real = false;
  setRenderedShell("simple");
  vi.useFakeTimers({ shouldAdvanceTime: true, toFake: ["Date"] });
  vi.setSystemTime(new Date(2026, 9, 27, 19, 30)); // Tuesday evening
});
afterEach(() => {
  cleanup();
  clear();
  setRenderedShell(null);
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe("the plan as one sentence and Enter (3.1)", () => {
  it("states the plan in minutes, in words, with the blocks as about-N-min rows and no lane names", async () => {
    apis(dto(body()));
    show();
    const sentence = await screen.findByTestId("today-sentence");
    expect(sentence.textContent).toContain(
      "25 minutes today: finish §5.4 Mixtures, then 2 short questions from earlier days and a fix for a mix-up."
    );
    expect(screen.getByText("Tuesday evening")).toBeTruthy();
    const rows = screen.getAllByTestId("today-block").map((row) => row.textContent ?? "");
    expect(rows).toEqual([
      expect.stringContaining("Continue §5.4 Mixtures"),
      expect.stringContaining("2 short questions · Eigenvalues"),
      expect.stringContaining("Fix a mix-up · Conditional probability")
    ]);
    expect(rows[0]).toContain("about 12 min");
    expect(rows[1]).toContain("about 7 min");
    expect(screen.getAllByTestId("today-block")[0].getAttribute("aria-current")).toBe("step");
    // The split line and the lanes are not on the surface.
    expect(surface()).not.toMatch(LANE_WORDS);
    expect(surface()).not.toContain("25 min · maintain");
  });

  it("shows no count of waiting things anywhere: no tiles, no queue size, no percentages (rules 9, 10)", async () => {
    apis(dto(body()));
    show();
    await screen.findByTestId("today-sentence");
    await flush();
    const text = surface();
    expect(text).not.toMatch(WAITING_WORDS);
    expect(text).not.toMatch(/%/);
    expect(text).not.toMatch(/scheduler mode|probe_eig|short_session|concepts in scope|learning_objects|backdrop/);
    expect(findJargon(text)).toEqual([]);
  });

  it("puts the split, each block's reason and the knowledge headline behind why? (and ?)", async () => {
    apis(dto(body()));
    show();
    await screen.findByTestId("today-sentence");
    expect(screen.queryByTestId("today-why")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /why\?/ }));
    const why = await screen.findByTestId("today-why");
    expect(why.textContent).toContain("about 13 min for keeping what you know");
    expect(why.textContent).toContain("about 4 min for fixing mix-ups");
    expect(why.textContent).toContain("Continue §5.4 Mixtures: new: the next section of Probability");
    expect(why.textContent).toContain("Receipt: learnloop router card --decision d1");
    await waitFor(() => expect(why.textContent).toContain("expected recall today 87%"));
    await press({ key: "?" });
    expect(screen.queryByTestId("today-why")).toBeNull();
    await press({ key: "?" });
    expect(screen.getByTestId("today-why")).toBeTruthy();
  });

  it("Begin ↵ with no session starts one for the plan's minutes and serves its first step, as Start's begin does", async () => {
    const f = apis(dto(body()));
    const props = show();
    await screen.findByTestId("today-sentence");
    await press({ key: "Enter" });
    await waitFor(() => expect(props.onBeginSession).toHaveBeenCalledTimes(1));
    expect(f.startSession).toHaveBeenCalledWith({ availableMinutes: 25 });
    expect(f.nextPlanItem).toHaveBeenCalledWith({ sessionId: "s_new", serve: true });
    expect((props.onBeginSession as ReturnType<typeof vi.fn>).mock.calls[0][0]).toEqual(STARTED);
    expect((props.onBeginSession as ReturnType<typeof vi.fn>).mock.calls[0][1]).toMatchObject({ kind: "item", practiceItemId: "pi_a" });
  });

  it("Begin with a session open serves the next step: a question opens Practice, a reading step the Reader", async () => {
    const f = apis(dto(body()));
    const props = show({ session: SESSION });
    await screen.findByTestId("today-sentence");
    fireEvent.click(screen.getByTestId("today-begin"));
    await waitFor(() => expect(props.onOpenPractice).toHaveBeenCalledWith("pi_a", "cand_a", null, "pres_a"));
    expect(f.startSession).not.toHaveBeenCalled();
    f.nextPlanItem.mockResolvedValueOnce({ step: { kind: "reading", planId: "plan_1", blockId: "blk_r", blockOrdinal: 1, reading: readingBlock().reading, estMinutes: 12, boundary: false } });
    await press({ key: "Enter" });
    await waitFor(() => expect(props.onOpenPlanReading).toHaveBeenCalledWith(readingBlock().reading));
  });

  it("one tap (or ←/→) on the minutes re-plans through set_plan_minutes", async () => {
    const f = apis(dto(body()));
    show();
    await screen.findByTestId("today-sentence");
    const chips = screen.getByRole("radiogroup", { name: "minutes today" });
    expect(within(chips).getByRole("radio", { checked: true }).textContent).toBe("25m");
    fireEvent.click(within(chips).getByText("40m"));
    await waitFor(() => expect(f.setPlanMinutes).toHaveBeenCalledWith(40, null));
    await flush();
    await press({ key: "ArrowLeft" });
    await waitFor(() => expect(f.setPlanMinutes).toHaveBeenLastCalledWith(15, null));
  });

  it("skip on the current block ends the reading block (or skips the next question) as the plan view's skip", async () => {
    const f = apis(dto(body()));
    show({ session: SESSION });
    await screen.findByTestId("today-sentence");
    fireEvent.click(screen.getByRole("button", { name: "skip" }));
    await waitFor(() => expect(f.planReadingEnded).toHaveBeenCalledWith("skipped", "s1"));
  });

  it("a waiting plan says when it resumes and offers no Begin", async () => {
    apis(dto(body({ blocks: [], currentBlockId: null, projected: [], waiting: { until: new Date(Date.now() + 9 * 60000).toISOString(), minutes: 9, practiceItemId: "pi_a", learningObjectTitle: "Eigenvalues" } })));
    show();
    const sentence = await screen.findByTestId("today-sentence");
    expect(sentence.textContent).toContain("Nothing to do right now. Back in 9 min: a question on Eigenvalues.");
    expect(screen.queryByTestId("today-begin")).toBeNull();
  });

  it("marks a check on your own in its block, never with the old 'voids the measurement' wording", async () => {
    const cold = block({
      id: "blk_cold",
      lane: "repair",
      items: [{ practiceItemId: "pi_c", learningObjectId: "lo_c", learningObjectTitle: "Bayes", practiceMode: "short_answer", promptPreview: "", lane: "repair", estMinutes: 3, state: "planned", origin: "followup", servedAt: null, doneAt: null }],
      learningObjectTitles: ["Bayes"]
    });
    apis(dto(body({ blocks: [cold], currentBlockId: "blk_cold", projected: [] })));
    show();
    await screen.findByTestId("today-sentence");
    expect(screen.getByTestId("today-block").textContent).toContain("Fix a mix-up · Bayes · on your own");
    expect(surface()).not.toMatch(/void|rejected|measurement/i);
  });
});

describe("re-entry after a break: a short plan, no debt screen (DL P6)", () => {
  it("says welcome back and the minutes; what slipped is only behind why?", async () => {
    apis(
      dto(
        body({
          kind: "reentry",
          minutesBudget: 12,
          reentry: { gapDays: 9, solidCount: 14, slippedCount: 6, slippedNames: ["Bayes", "Variance"], namedBy: "priority", target: 0.85, planMinutes: 12, planItems: 5 }
        })
      )
    );
    show();
    const sentence = await screen.findByTestId("today-sentence");
    expect(sentence.textContent).toContain(
      "Welcome back. A short catch-up today: 12 minutes of the most useful questions. Nothing else is waiting on you."
    );
    const text = surface();
    expect(text).not.toMatch(/Bayes|Variance|slipped|Still solid|\b14\b|\b6\b/i);
    expect(screen.queryByTestId("plan-reentry")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /why\?/ }));
    const why = await screen.findByTestId("today-why");
    expect(why.textContent).toContain("You were away 9 days.");
    expect(why.textContent).toContain("Bayes, Variance");
  });
});

describe("the states (§7.1)", () => {
  it("first run, no books: nothing to plan yet, with + Add", async () => {
    apis(dto(body({ blocks: [], currentBlockId: null, projected: [], status: "complete", totals: { ...body().totals, plannedItems: 0, readingBlocks: 0 } })), {
      getSourceLibrary: vi.fn(async () => ({ sources: [], pending: [] }))
    });
    const props = show();
    const first = await screen.findByTestId("today-first-run");
    expect(first.textContent).toContain("Nothing to plan yet. Add a book, paper or lecture and LearnLoop will plan your days around it.");
    expect(surface()).not.toMatch(/Nothing due today|No new material/);
    fireEvent.click(within(first).getByRole("button", { name: "+ Add" }));
    expect(props.onAdd).toHaveBeenCalledTimes(1);
  });

  it("one book, no answers yet: day one is a plan to start reading", async () => {
    apis(dto(body({ blocks: [readingBlock({ startedAt: null, reading: { ...readingBlock().reading!, sectionTitle: "Chapter 1", spansSeen: 0 } })], currentBlockId: "blk_r", projected: [], minutesBudget: 15, rememberedMinutes: 15 })));
    show();
    expect((await screen.findByTestId("today-sentence")).textContent).toContain("15 minutes today: read Chapter 1.");
    expect(screen.getByTestId("today-begin").textContent).toContain("Begin ↵");
  });

  it("done: the time spent, Keep going on Enter, Something new's trade-off, and Done for today ends the session", async () => {
    const done = body({ status: "complete", blocks: [block({ status: "done" })], currentBlockId: null, projected: [] });
    const f = apis(dto(done, { day: { plans: 1, kinds: ["normal"], complete: true, ...done.totals, actualMinutes: 26.2, doneItems: 9 } }));
    const props = show({ session: SESSION });
    const sentence = await screen.findByTestId("today-sentence");
    expect(sentence.textContent).toBe("Done for today · 26 minutes.");
    expect(surface()).not.toMatch(/\b9 items?\b|Today complete/);
    await press({ key: "Enter" });
    await waitFor(() => expect(f.planKeepGoing).toHaveBeenCalledWith({ sessionId: "s1" }));
    await flush();
    fireEvent.click(screen.getByRole("button", { name: "Something new" }));
    expect((await screen.findByTestId("today-more-new")).textContent).toContain("about 9 min of new material today");
    fireEvent.click(screen.getByRole("button", { name: "Done for today" }));
    await waitFor(() => expect(f.endSession).toHaveBeenCalledWith("s1"));
    expect(f.planKeepGoing).toHaveBeenCalledWith({ sessionId: "s1", stop: true });
    await waitFor(() => expect(props.onEndSession).toHaveBeenCalledWith({ sessionId: "s1" }));
  });

  it("loading: the frame, never 'Loading today's queue'", async () => {
    apis(() => new Promise<DailyPlanDto>(() => undefined));
    show();
    expect(await screen.findByTestId("today-loading")).toBeTruthy();
    expect(surface()).not.toMatch(/Loading/i);
  });

  it("error: Couldn't plan today · Try again, which reads the plan again", async () => {
    let fail = true;
    const f = apis(async () => {
      if (fail) throw { code: "sidecar_timeout", message: "The read timed out.", retryable: true };
      return dto(body());
    });
    show();
    const error = await screen.findByTestId("today-error");
    expect(error.textContent).toContain("Couldn't plan today");
    expect(error.textContent).not.toContain("timed out");
    fail = false;
    fireEvent.click(within(error).getByRole("button", { name: "Try again" }));
    expect(await screen.findByTestId("today-sentence")).toBeTruthy();
    expect(f.getDailyPlan.mock.calls.length).toBeGreaterThanOrEqual(2);
  });

  it("the plan switched off: the remembered minutes and Begin, which opens a session and its first question", async () => {
    const f = apis(dto(null, { reason: "plan_disabled" }));
    const props = show();
    expect((await screen.findByTestId("today-sentence")).textContent).toBe("15 minutes today: starting with Topic 1.");
    await press({ key: "Enter" });
    await waitFor(() => expect(props.onOpenPractice).toHaveBeenCalledWith("pi_1", "cand_1"));
    expect(f.startSession).toHaveBeenCalledWith({ availableMinutes: 15 });
    expect(props.onBeginSession).toHaveBeenCalledWith(STARTED);
    expect(surface()).not.toMatch(WAITING_WORDS);
  });
});

describe("the streak in the footer", () => {
  it("is one quiet line, never a loss", async () => {
    apis(dto(body()));
    show();
    await screen.findByTestId("today-sentence");
    expect(screen.getByTestId("today-streak").textContent).toBe("4 days · best 9");
    expect(screen.getByTestId("today-footer").textContent).not.toMatch(/keep your streak|lose/i);
  });

  it("says nothing before there is a streak", async () => {
    apis(dto(body(), { streak: { current: 0, activeToday: false, longest: 0 } }));
    show({ streak: { current: 0, activeToday: false, longest: 0 } });
    await screen.findByTestId("today-sentence");
    expect(screen.getByTestId("today-streak").textContent).toBe("");
  });
});

describe("the full list (l)", () => {
  it("is a plain list: titles, minutes where the plan has them, a short why; no ids, modes, mastery or priorities", async () => {
    apis(dto(body()), {
      getTodayQueue: vi.fn(async () => queue([scheduled(1, { practiceItemId: "pi_a" }), scheduled(2, { isFollowup: true, followupKind: "cold_retry", dueStatus: "followup" })]))
    });
    show();
    await screen.findByTestId("today-sentence");
    await press({ key: "l" });
    const rows = await screen.findAllByTestId("today-list-row");
    expect(rows.map((row) => row.textContent)).toEqual([
      expect.stringContaining("Topic 1about 4 mintime to bring it back"),
      expect.stringContaining("Topic 2on your own · no hints")
    ]);
    const text = surface();
    expect(text).not.toMatch(/pi_|cand_|free_recall|0\.412|mastery|priority/);
    fireEvent.click(within(rows[1]).getByRole("button", { name: "why?" }));
    expect(rows[1].textContent).toContain("To see whether last week's fix held.");
    await press({ key: "p" });
    expect(screen.queryByTestId("today-list")).toBeNull();
  });

  it("opening one while the plan serves is a learner pick, served with the pick's offer", async () => {
    const f = apis(dto(body()));
    const props = show({ session: SESSION });
    await screen.findByTestId("today-sentence");
    fireEvent.click(screen.getByRole("button", { name: "all of today's list (l)" }));
    await screen.findAllByTestId("today-list-row");
    await press({ key: "j" });
    await press({ key: "Enter" });
    await waitFor(() => expect(props.onOpenPractice).toHaveBeenCalledWith("pi_2", "cand_pick", null, "pres_pick"));
    expect(f.planLearnerPick).toHaveBeenCalledWith("pi_2", "s1", "cand_2");
  });

  it("with no session yet, a pick begins today's plan with that pick", async () => {
    const f = apis(dto(body()));
    const props = show();
    await screen.findByTestId("today-sentence");
    await press({ key: "l" });
    const rows = await screen.findAllByTestId("today-list-row");
    fireEvent.click(within(rows[0]).getByRole("button", { name: "Topic 1" }));
    await waitFor(() => expect(props.onBeginSession).toHaveBeenCalledTimes(1));
    expect(f.startSession).toHaveBeenCalledWith({ availableMinutes: 25 });
    expect(f.planLearnerPick).toHaveBeenCalledWith("pi_1", "s_new", "cand_1");
  });
});

describe("threads (3.3)", () => {
  it("lists open questions and unfinished problems with no count; each opens where it belongs", async () => {
    apis(dto(body()), {
      listQuestionQueue: vi.fn(async () => ({ version: 1, questions: [question("q1")], openCount: 1 })),
      workbenchOpenProblems: vi.fn(async () => ({ version: 1, problems: [problem("wb1")] }))
    });
    const props = show();
    const threads = await screen.findByTestId("today-threads");
    await waitFor(() => expect(within(threads).getAllByTestId("today-thread")).toHaveLength(2));
    const [first, second] = within(threads).getAllByTestId("today-thread");
    expect(first.textContent).toContain("Exercise 5.9: show that the sum of two independent Poissons is Poisson. — 3 steps written");
    expect(second.textContent).toContain("“Why is the density of a sum a convolution?” · §5.4");
    expect(threads.textContent).not.toMatch(/\(\d+\)|\d+ open|open questions/i);
    fireEvent.click(within(first).getByRole("button", { name: "resume ▸" }));
    expect(props.onResumeProblem).toHaveBeenCalledWith(expect.objectContaining({ sessionId: "wb1", sourceId: "src_prob" }));
    fireEvent.click(within(second).getByRole("button", { name: "open in book ▸" }));
    expect(props.onOpenPassage).toHaveBeenCalledWith("src_prob", "sp9", "ext_prob");
  });

  it("shows at most three, then more ▸; a question with no passage continues in Ask", async () => {
    apis(dto(body()), {
      listQuestionQueue: vi.fn(async () => ({
        version: 1,
        questions: [
          question("q1", { createdAt: "2026-10-26T01:00:00Z" }),
          question("q2", { createdAt: "2026-10-26T02:00:00Z" }),
          question("q3", { createdAt: "2026-10-26T03:00:00Z" }),
          question("q4", { createdAt: "2026-10-26T04:00:00Z", context: "practice", practiceItemId: "pi_x", sessionId: "s0", sourceCitation: null, questionMd: "What is a pmf?" }),
          question("q5", { resolution: "resolved" })
        ],
        openCount: 4
      }))
    });
    const props = show();
    await waitFor(() => expect(screen.getAllByTestId("today-thread")).toHaveLength(3));
    fireEvent.click(screen.getByRole("button", { name: "more ▸" }));
    const rows = screen.getAllByTestId("today-thread");
    expect(rows).toHaveLength(4);
    fireEvent.click(within(rows[0]).getByRole("button", { name: "continue ▸" }));
    expect(props.onAsk).toHaveBeenCalledWith(expect.objectContaining({ context: "practice", practiceItemId: "pi_x" }));
  });

  it("shows the wrap-up the shell armed, and no thread heading when there is nothing else", async () => {
    apis(dto(body()));
    show({ wrapUp: <button type="button">Reading wrap-up ready — under a minute ▸</button> });
    expect(await screen.findByRole("button", { name: /wrap-up ready/ })).toBeTruthy();
    expect(screen.queryByText("Pick up a thread")).toBeNull();
  });

  it("shows one captures line, with no number, only when there are captures; it opens the inbox", async () => {
    apis(dto(body()), {
      getInboxSummary: vi.fn(async () => ({ count: 2, newCount: 2, captures: [], deletePending: [], deletePendingCount: 0, pinnedVault: null, vaultMismatch: false, enabled: true }))
    });
    show();
    const line = await screen.findByTestId("today-captures");
    expect(line.textContent).toBe("New captures ▸");
    expect(screen.queryByTestId("inbox-strip")).toBeNull();
    fireEvent.click(line);
    expect(screen.getByTestId("inbox-strip")).toBeTruthy();
  });

  it("shows no captures line and no inbox when there are none", async () => {
    apis(dto(body()));
    show();
    await screen.findByTestId("today-sentence");
    await flush();
    expect(screen.queryByTestId("today-captures")).toBeNull();
    expect(screen.queryByTestId("inbox-strip")).toBeNull();
  });
});

describe("the goal card (3.4)", () => {
  it("is one line of plain words with Practise and Practice exam; the numbers are behind details", async () => {
    const f = apis(dto(body()), {
      goalsList: vi.fn(async () => ({ version: 1, goals: [goal()] })),
      getTodayQueue: vi.fn(async () => queue([scheduled(1), scheduled(2, { components: { goalFrontier: 0.4 } as ScheduledItemDto["components"] })]))
    });
    const props = show({ session: SESSION });
    const card = await screen.findByTestId("goal-card");
    expect(card.textContent).toContain("Probability midterm · Nov 14 · on track");
    expect(card.textContent).not.toMatch(/%|Brier|ON TRACK|\d+\/\d+/);
    fireEvent.click(await within(card).findByRole("button", { name: "Practice exam" }));
    expect(props.onTakeExam).toHaveBeenCalledWith("goal_1");
    fireEvent.click(within(card).getByRole("button", { name: "Practise for this goal" }));
    await waitFor(() => expect(f.planLearnerPick).toHaveBeenCalledWith("pi_2", "s1", "cand_2"));
    expect(screen.queryByTestId("goal-banner")).toBeNull();
    fireEvent.click(within(card).getByRole("button", { name: /details/ }));
    expect(screen.getByTestId("goal-banner")).toBeTruthy();
  });

  it("offers no exam while its pool is not ready", async () => {
    apis(dto(body()), {
      goalsList: vi.fn(async () => ({ version: 1, goals: [goal({ report: null })] })),
      getExamStatus: vi.fn(async () => ({ version: 1, goalId: "goal_1", inWindow: true, daysUntilDue: 19, pastDueGrace: false, existingSessionId: null, poolItemCount: 0, uncoveredFacets: [], reservationDeferred: true, reservableCandidateCount: 0 }))
    });
    show();
    const card = await screen.findByTestId("goal-card");
    await flush();
    expect(card.textContent).toContain("Probability midterm · Nov 14");
    expect(within(card).queryByRole("button", { name: "Practice exam" })).toBeNull();
  });
});

describe("keys", () => {
  it("leaves modified keys to the shell (screenLeavesKey): Alt+Enter and Ctrl+L do nothing here", async () => {
    const f = apis(dto(body()));
    show();
    await screen.findByTestId("today-sentence");
    await press({ key: "Enter", altKey: true });
    await press({ key: "l", ctrlKey: true });
    await flush();
    expect(f.startSession).not.toHaveBeenCalled();
    expect(screen.queryByTestId("today-list")).toBeNull();
  });
});

// ── Fix round 1 (Codex review 20261025-022429-GJcOzo) ──────────────────────

describe("fix round 1, F2: Enter on a focused control is that control's", () => {
  function enterOn(element: HTMLElement): boolean {
    element.focus();
    // false when a listener took the key (preventDefault): the control's own
    // activation would then never run.
    return fireEvent.keyDown(element, { key: "Enter", bubbles: true, cancelable: true });
  }

  it("why?, skip and a thread's resume ▸ keep Enter; Begin is not started", async () => {
    const f = apis(dto(body()), { workbenchOpenProblems: vi.fn(async () => ({ version: 1, problems: [problem("wb1")] })) });
    show();
    await screen.findByTestId("today-sentence");
    const resume = await screen.findByRole("button", { name: "resume ▸" });
    for (const control of [screen.getByRole("button", { name: /why\?/ }), screen.getByRole("button", { name: "skip" }), resume]) {
      expect(enterOn(control), control.textContent ?? "").toBe(true);
    }
    await flush();
    expect(f.startSession).not.toHaveBeenCalled();
    expect(f.nextPlanItem).not.toHaveBeenCalled();
    expect(f.planReadingEnded).not.toHaveBeenCalled();
  });

  it("Something new keeps Enter when the day is done; Keep going is not asked", async () => {
    const f = apis(dto(body({ status: "complete", stopReason: "budget" })));
    show({ session: SESSION });
    const something = await screen.findByRole("button", { name: "Something new" });
    expect(enterOn(something)).toBe(true);
    await flush();
    expect(f.planKeepGoing).not.toHaveBeenCalled();
  });

  it("Enter on the page itself still begins", async () => {
    const f = apis(dto(body()));
    show();
    await screen.findByTestId("today-sentence");
    expect(fireEvent.keyDown(screen.getByTestId("today-place"), { key: "Enter", bubbles: true, cancelable: true })).toBe(false);
    await waitFor(() => expect(f.startSession).toHaveBeenCalledTimes(1));
  });

  it("in the full list, Enter on a row's why? or on back to the plan opens nothing", async () => {
    const f = apis(dto(body()), {
      getTodayQueue: vi.fn(async () => queue([scheduled(1, { isFollowup: true, followupKind: "cold_retry", dueStatus: "followup" })]))
    });
    const props = show({ session: SESSION });
    await screen.findByTestId("today-sentence");
    await press({ key: "l" });
    const row = (await screen.findAllByTestId("today-list-row"))[0];
    expect(enterOn(within(row).getByRole("button", { name: "why?" }))).toBe(true);
    expect(enterOn(screen.getByRole("button", { name: "back to the plan (p)" }))).toBe(true);
    await flush();
    expect(f.planLearnerPick).not.toHaveBeenCalled();
    expect(props.onOpenPractice).not.toHaveBeenCalled();
  });
});

describe("fix round 1, F4: the full list with the plan off starts the session with the minutes chosen here", () => {
  it("40m chosen, then a question from the list: the session is 40 minutes, then the question opens", async () => {
    const f = apis(dto(null, { reason: "plan_disabled" }));
    const props = show();
    expect((await screen.findByTestId("today-sentence")).textContent).toContain("15 minutes today");
    fireEvent.click(screen.getByRole("radio", { name: "40m" }));
    expect(screen.getByTestId("today-sentence").textContent).toContain("40 minutes today");
    await press({ key: "l" });
    const rows = await screen.findAllByTestId("today-list-row");
    fireEvent.click(within(rows[0]).getByRole("button", { name: "Topic 1" }));
    await waitFor(() => expect(props.onOpenPractice).toHaveBeenCalledWith("pi_1", "cand_1"));
    expect(f.startSession).toHaveBeenCalledTimes(1);
    expect(f.startSession).toHaveBeenCalledWith({ availableMinutes: 40 });
    expect(props.onBeginSession).toHaveBeenCalledWith(STARTED);
  });

  it("with a session open it starts none and opens the question", async () => {
    const f = apis(dto(null, { reason: "plan_disabled" }));
    const props = show({ session: SESSION });
    await screen.findByTestId("today-sentence");
    await press({ key: "l" });
    fireEvent.click(within((await screen.findAllByTestId("today-list-row"))[0]).getByRole("button", { name: "Topic 1" }));
    await waitFor(() => expect(props.onOpenPractice).toHaveBeenCalledWith("pi_1", "cand_1"));
    expect(f.startSession).not.toHaveBeenCalled();
  });
});

describe("fix round 1, F5: expanded captures show no waiting counts", () => {
  const summary = {
    count: 3,
    newCount: 3,
    captures: [{ captureId: "cap_1", kind: "text", status: "new", text: "the board after lecture", url: null, note: null, receivedAt: "2026-10-25T10:00:00Z", pendingRoute: null }],
    deletePending: [
      { captureId: "cap_2", kind: "image", status: "purged", text: null, url: null, note: null, receivedAt: "2026-10-20T10:00:00Z", pendingRoute: null, mediaDeletePending: true },
      { captureId: "cap_3", kind: "image", status: "purged", text: null, url: null, note: null, receivedAt: "2026-10-21T10:00:00Z", pendingRoute: null, mediaDeletePending: true }
    ],
    deletePendingCount: 2,
    pinnedVault: null,
    vaultMismatch: false,
    enabled: true
  };

  it("the real inbox under Today names no number of captures or pending deletions, and keeps every action", async () => {
    inbox.real = true;
    apis(dto(body()), { getInboxSummary: vi.fn(async () => summary) });
    show();
    fireEvent.click(await screen.findByTestId("today-captures"));
    const strip = await screen.findByRole("region", { name: "Capture inbox" });
    await waitFor(() => expect(strip.textContent).toContain("the board after lecture"));
    const text = strip.textContent ?? "";
    expect(text).toContain("New captures");
    expect(text).toContain("Original media deletion is still pending for these purged captures.");
    expect(text).not.toMatch(/Inbox ·|\b3\b|pending for 2|\b2 purged/);
    expect(within(strip).getByRole("button", { name: "Make a card" })).toBeTruthy();
    expect(within(strip).getAllByRole("button", { name: "Retry delete" })).toHaveLength(2);
  });

  it("classic's strip keeps its counts", async () => {
    const real = await vi.importActual<typeof import("../../components/InboxStrip")>("../../components/InboxStrip");
    apis(dto(body()), { getInboxSummary: vi.fn(async () => summary) });
    render(<real.InboxStrip subjects={[]} onAsk={vi.fn()} />);
    const strip = await screen.findByRole("region", { name: "Capture inbox" });
    await waitFor(() => expect(strip.textContent).toContain("Inbox · 3"));
    expect(strip.textContent).toContain("Original media deletion is pending for 2 purged captures.");
  });
});

describe("fix round 1, F6: the full list says when it could not be read, with Try again", () => {
  it("a first read that fails: the reason and Try again, which reads it again", async () => {
    let fail = true;
    const getTodayQueue = vi.fn(async () => {
      if (fail) throw { code: "internal", message: "sidecar busy", retryable: true };
      return queue([scheduled(1)]);
    });
    apis(dto(body()), { getTodayQueue });
    show({ session: SESSION });
    await screen.findByTestId("today-sentence");
    await press({ key: "l" });
    const alert = await screen.findByTestId("today-list-error");
    expect(alert.textContent).toContain("Couldn't read today's list");
    expect(screen.queryAllByTestId("today-list-row")).toHaveLength(0);
    fail = false;
    fireEvent.click(within(alert).getByRole("button", { name: "Try again" }));
    expect(await screen.findAllByTestId("today-list-row")).toHaveLength(1);
    await waitFor(() => expect(screen.queryByTestId("today-list-error")).toBeNull());
  });

  it("a refresh that fails: the rows stay, marked as possibly out of date, with Try again", async () => {
    let fail = false;
    const getTodayQueue = vi.fn(async () => {
      if (fail) throw { code: "internal", message: "sidecar busy", retryable: true };
      return queue([scheduled(1)]);
    });
    apis(dto(body()), { getTodayQueue });
    show({ session: SESSION });
    await screen.findByTestId("today-sentence");
    await press({ key: "l" });
    await screen.findAllByTestId("today-list-row");
    fail = true;
    await act(async () => invalidateAll());
    const alert = await screen.findByTestId("today-list-error");
    expect(alert.textContent).toContain("Couldn't refresh today's list; what's below may be out of date");
    expect(screen.getAllByTestId("today-list-row")).toHaveLength(1);
    fail = false;
    fireEvent.click(within(alert).getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(screen.queryByTestId("today-list-error")).toBeNull());
  });

  it("while it is read the first time: a quiet frame, not a blank", async () => {
    apis(dto(body()), { getTodayQueue: vi.fn(() => new Promise(() => undefined)) });
    show({ session: SESSION });
    await screen.findByTestId("today-sentence");
    await press({ key: "l" });
    expect(await screen.findByTestId("today-list-loading")).toBeTruthy();
  });
});

describe("fix round 1, F1: an action still running when Today unmounts (another vault opened) answers nothing", () => {
  it("Begin's session, started before the vault changed, is never handed to the shell", async () => {
    let release: (value: unknown) => void = () => undefined;
    const startSession = vi.fn(() => new Promise((resolve) => (release = resolve)));
    const f = apis(dto(body()), { startSession });
    const props = show();
    await screen.findByTestId("today-sentence");
    await press({ key: "Enter" });
    await waitFor(() => expect(startSession).toHaveBeenCalledTimes(1));
    cleanup();
    await act(async () => release(STARTED));
    await flush();
    expect(props.onBeginSession).not.toHaveBeenCalled();
    expect(props.onError).not.toHaveBeenCalled();
    // Nothing after the start: no serve with the old vault's session.
    expect(f.nextPlanItem).not.toHaveBeenCalled();
  });
});
