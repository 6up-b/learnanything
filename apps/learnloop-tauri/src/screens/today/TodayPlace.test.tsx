// UX Phase 3 (docs/specs/ux_learnloop_v1.md §7.1, W4, §4.2 rules 9-10, §10
// 3.1-3.4): Today in the simple shell. One sentence and Enter: the plan in
// minutes, with no count of waiting things anywhere; re-entry after a break
// as a short plan with no debt screen; the lanes, the split and the reasons
// behind why?; Begin, the minutes, keep going and the full list calling
// exactly the RPCs classic's Start and Today call; threads, the goal card and
// the captures line; the first-run, done, loading and error states.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { AiConnectionDto, DailyPlanBodyDto, DailyPlanDto, GoalDto, PlanBlockDto, QueueSnapshot, QuestionQueueRowDto, ScheduledItemDto, SessionSnapshot, SourceLibraryCard, SourceStatusLineDto, WorkbenchOpenProblemDto } from "../../api/dto";
import { clear, invalidateAll } from "../../api/queryCache";
import { setAlgoConfig, setRenderedShell } from "../../app/algoConfig";
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
import { KEEP_GOING_NOTHING_LEAD } from "../../app/todayCause";
import { notifyQueueChanged } from "../../queueEvents";

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
    // The shell's start (fix round 2), here the bare RPC: the App's binding
    // to the vault is App.today.test.tsx's.
    onStartSession: vi.fn(async (minutes: number) => (await fns.startSession({ availableMinutes: minutes })) as SessionSnapshot),
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

describe("a question in progress (IH6)", () => {
  const QUESTION = { workbenchSessionId: "wb_1", practiceItemId: "pi_q", learningObjectTitle: "ReLU" };
  const held = () => body({ blocks: [], currentBlockId: null, projected: [], firstBlock: null, deciding: false, questionInProgress: QUESTION });

  it("says so plainly, never 'Choosing what's next…', and offers Begin rather than Keep going", async () => {
    apis(dto(held()));
    show();
    const sentence = await screen.findByTestId("today-sentence");
    expect(sentence.textContent).toContain("A question is in progress on ReLU.");
    expect(surface()).not.toContain("Choosing what's next");
    expect(surface()).not.toContain("Nothing planned for today");
    expect(screen.getByTestId("today-begin").textContent).toContain("Begin");
    expect(screen.queryByRole("button", { name: "Keep going" })).toBeNull();
    expect(findJargon(surface())).toEqual([]);
  });

  it("does not poll: a read that held its boundary would answer the same 40 times", async () => {
    vi.useRealTimers();
    vi.useFakeTimers({ toFake: ["setInterval", "clearInterval"] });
    apis(dto(held()));
    show();
    await flush();
    const reads = fns.getDailyPlan.mock.calls.length;
    await act(async () => {
      vi.advanceTimersByTime(60_000);
    });
    expect(fns.getDailyPlan.mock.calls.length).toBe(reads);
  });

  it("while a block really is being chosen it still polls (the control for the test above)", async () => {
    vi.useRealTimers();
    vi.useFakeTimers({ toFake: ["setInterval", "clearInterval"] });
    apis(dto(body({ blocks: [], currentBlockId: null, projected: [], firstBlock: null, deciding: true })));
    show();
    await flush();
    const reads = fns.getDailyPlan.mock.calls.length;
    await act(async () => {
      vi.advanceTimersByTime(3_100);
    });
    expect(fns.getDailyPlan.mock.calls.length).toBeGreaterThan(reads);
  });

  it("Begin and Enter are explicit steps: they serve, which decides", async () => {
    apis(dto(held()), { nextPlanItem: vi.fn(async () => dto(body(), { step: { kind: "item", planId: "plan_1", blockId: "b", position: 1, practiceItemId: "pi_n", learningObjectId: "lo", learningObjectTitle: "T", estMinutes: 2, lane: "new", origin: "chooser", boundary: true, schedulerCandidateId: null, presentationId: "pp" } as never })) });
    const props = show({ session: { sessionId: "s1", availableMinutes: 25 } as SessionSnapshot });
    fireEvent.click(await screen.findByTestId("today-begin"));
    await waitFor(() => expect(fns.nextPlanItem).toHaveBeenCalledWith({ sessionId: "s1", serve: true }));
    await waitFor(() => expect(props.onOpenPractice).toHaveBeenCalledWith("pi_n", null, null, "pp"));
  });

  it("resume opens a problem on an item in practice, and a Reader problem in its book", async () => {
    apis(dto(held()));
    const props = show();
    fireEvent.click(await screen.findByRole("button", { name: "resume ▸" }));
    expect(props.onOpenPractice).toHaveBeenCalledWith("pi_q");
    cleanup();
    clear();
    const open = problem("wb_1");
    apis(dto(held()), { workbenchOpenProblems: vi.fn(async () => ({ version: 1, problems: [open] })) });
    const reader = show();
    await flush();
    fireEvent.click(within(await screen.findByTestId("question-in-progress-actions")).getByRole("button", { name: "resume ▸" }));
    expect(reader.onResumeProblem).toHaveBeenCalledWith(open);
  });

  it("set it aside closes the problem and the plan is read again", async () => {
    setAlgoConfig({ workbench: { enabled: true, openItem: true } } as never);
    apis(dto(held()), { workbenchAbandon: vi.fn(async () => ({ version: 1, session: {} })) });
    show();
    const aside = await screen.findByRole("button", { name: "set it aside" });
    const reads = fns.getDailyPlan.mock.calls.length;
    fireEvent.click(aside);
    await waitFor(() => expect(fns.workbenchAbandon).toHaveBeenCalledWith({ sessionId: "wb_1" }));
    await waitFor(() => expect(fns.getDailyPlan.mock.calls.length).toBeGreaterThan(reads));
    setAlgoConfig({} as never);
  });
});

describe("'Something else would help' on the default Today (IH3, review m7)", () => {
  const SESSION = { sessionId: "s1", availableMinutes: 25 } as SessionSnapshot;
  const OPTIONS = {
    version: 1, enabled: true, drawn: false, decisionId: null, device: "desktop",
    options: [{ kind: "question", ref: "cand_q", label: "Another question", minutes: 5, propensity: null, plansPick: false, servable: true }]
  };

  it("shows with a session where the plan says it may; never without one or without the flag", async () => {
    apis(dto(body(), { somethingElse: true }));
    show({ session: SESSION });
    expect((await screen.findByTestId("something-else-link")).textContent).toBe("Something else would help");
    cleanup();
    clear();
    apis(dto(body()));
    show({ session: SESSION });
    await screen.findByTestId("today-sentence");
    expect(screen.queryByTestId("something-else-link")).toBeNull();
    cleanup();
    clear();
    apis(dto(body(), { somethingElse: true }));
    show();
    await screen.findByTestId("today-sentence");
    expect(screen.queryByTestId("something-else-link")).toBeNull();
  });

  it("a served choice opens its step", async () => {
    const step = { kind: "item", planId: "plan_1", blockId: "b", position: 1, practiceItemId: "pi_n", learningObjectId: "lo", learningObjectTitle: "T",
                   estMinutes: 2, lane: "new", origin: "learner_pick", boundary: false, schedulerCandidateId: null, presentationId: "pp" };
    apis(dto(body(), { somethingElse: true }), {
      planSomethingElseOptions: vi.fn(async () => OPTIONS),
      planSomethingElse: vi.fn(async () => ({ ...dto(body()), step, preference: { id: "k", outcome: "served", kind: "question", ref: "cand_q", servedDecisionId: "d", lesson: null, replayed: false } }))
    });
    const props = show({ session: SESSION });
    fireEvent.click(await screen.findByTestId("something-else-link"));
    fireEvent.click(await screen.findByTestId("something-else-option-question"));
    await waitFor(() => expect(fns.planSomethingElse).toHaveBeenCalledWith(expect.objectContaining({ surface: "today", sessionId: "s1", kind: "question" })));
    await waitFor(() => expect(props.onOpenPractice).toHaveBeenCalledWith("pi_n", null, null, "pp"));
  });

  it("the plan's own pick, chosen, is served as Begin serves it", async () => {
    apis(dto(body(), { somethingElse: true }), {
      planSomethingElseOptions: vi.fn(async () => ({ ...OPTIONS, options: [{ ...OPTIONS.options[0], plansPick: true }] })),
      planSomethingElse: vi.fn(async () => ({ ...dto(body()), step: null, preference: { id: "k", outcome: "agreed", kind: "question", ref: "cand_q", servedDecisionId: "d", lesson: null, replayed: false } }))
    });
    show({ session: SESSION });
    fireEvent.click(await screen.findByTestId("something-else-link"));
    fireEvent.click(await screen.findByTestId("something-else-option-question"));
    await waitFor(() => expect(fns.nextPlanItem).toHaveBeenCalledWith({ sessionId: "s1", serve: true }));
  });
});

describe("the plan as one sentence and Enter (3.1)", () => {
  it("states the plan in minutes, in words, with the blocks as about-N-min rows and no lane names", async () => {
    apis(dto(body()));
    show();
    const sentence = await screen.findByTestId("today-sentence");
    expect(sentence.textContent).toContain(
      "Up to 25 minutes today. Planned so far: finish §5.4 Mixtures, then 2 short questions from earlier days and a fix for a mix-up."
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
    expect((await screen.findByTestId("today-sentence")).textContent).toContain("Up to 15 minutes today. Planned so far: read Chapter 1.");
    expect(screen.getByTestId("today-begin").textContent).toContain("Begin ↵");
  });

  it("done: the time spent, Keep going on Enter, Something new's trade-off, and Done for today ends the session", async () => {
    const done = body({ status: "complete", blocks: [block({ status: "done" })], currentBlockId: null, projected: [] });
    const f = apis(dto(done, { day: { plans: 1, kinds: ["normal"], complete: true, ...done.totals, actualMinutes: 26.2, doneItems: 9 } }));
    const props = show({ session: SESSION });
    const sentence = await screen.findByTestId("today-sentence");
    expect(sentence.textContent).toBe("Done for today · 26 minutes spent answering and reading.");
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

  // UX journey audit UX-4 (student-1 #44, retainer-1 #63): Keep going with
  // nothing to add redrew the same Today and said nothing.
  it("UX-4: Keep going with nothing to add says so, in place, and what would give LearnLoop more", async () => {
    const empty = body({ status: "complete", blocks: [], currentBlockId: null, projected: [], totals: { ...body().totals, plannedItems: 0, readingBlocks: 0 } });
    const f = apis(dto(empty), { planKeepGoing: vi.fn(async () => dto({ ...empty, id: "plan_kg", kind: "keep_going" })) });
    show({ session: SESSION });
    expect((await screen.findByTestId("today-sentence")).textContent).toBe("Nothing planned for today.");
    expect(screen.queryByTestId("today-keep-going-nothing")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /Keep going/ }));
    await waitFor(() => expect(f.planKeepGoing).toHaveBeenCalledWith({ sessionId: "s1" }));
    const line = await screen.findByTestId("today-keep-going-nothing");
    // UX fix stage 3 (item 6): the line now leads into the day's cause, said beside it.
    expect(line.textContent).toBe(KEEP_GOING_NOTHING_LEAD);
    expect(line.getAttribute("role")).toBe("status");
    expect(findJargon(line.textContent ?? "")).toEqual([]);
  });

  it("UX-4: Keep going that adds a block says nothing extra", async () => {
    const done = body({ status: "complete", blocks: [block({ status: "done" })], currentBlockId: null, projected: [] });
    const more = body({ id: "plan_kg", kind: "keep_going", blocks: [block({ id: "blk_kg" })], currentBlockId: "blk_kg", projected: [] });
    const f = apis(dto(done), { planKeepGoing: vi.fn(async () => dto(more)) });
    show({ session: SESSION });
    await screen.findByTestId("today-done");
    fireEvent.click(screen.getByRole("button", { name: /Keep going/ }));
    await waitFor(() => expect(f.planKeepGoing).toHaveBeenCalledOnce());
    await flush();
    expect(screen.queryByTestId("today-keep-going-nothing")).toBeNull();
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

  // UX journey audit UX-6 (beginner-1 #80-120, student-1 #42): this line went
  // through the error channel, red, and stayed over every screen.
  it("UX-6: Practise for this goal with nothing ready says so on the card, as a notice, never an error", async () => {
    const f = apis(dto(body()), {
      goalsList: vi.fn(async () => ({ version: 1, goals: [goal()] })),
      getTodayQueue: vi.fn(async () => queue([scheduled(1)]))
    });
    const props = show({ session: SESSION });
    const card = await screen.findByTestId("goal-card");
    fireEvent.click(within(card).getByRole("button", { name: "Practise for this goal" }));
    const line = await screen.findByTestId("goal-nothing-ready");
    // UX fix stage 3: a goal with questions of its own that are not up today says so.
    expect(line.textContent).toBe("Nothing for this goal is up today. Its questions come back on the days they're due.");
    expect(line.getAttribute("role")).toBe("status");
    expect(props.onError).not.toHaveBeenCalled();
    expect(f.planLearnerPick).not.toHaveBeenCalled();
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

describe("fix round 2: the shell owns Begin's start", () => {
  it("Begin asks the shell for the plan's minutes, and a start the shell did not make stops quietly", async () => {
    const f = apis(dto(body()));
    const onStartSession = vi.fn(async () => null);
    const props = show({ onStartSession });
    await screen.findByTestId("today-sentence");
    await press({ key: "Enter" });
    await flush();
    expect(onStartSession).toHaveBeenCalledWith(25);
    expect(f.startSession).not.toHaveBeenCalled();
    expect(f.nextPlanItem).not.toHaveBeenCalled();
    expect(props.onBeginSession).not.toHaveBeenCalled();
    expect(props.onError).not.toHaveBeenCalled();
  });
});

// ── UX fix stage 3 (UX journey audit P1, F1): Today explains itself ────────

const EMPTY_TOTALS = { plannedMinutes: 0, plannedItems: 0, doneItems: 0, skippedItems: 0, displacedItems: 0, readingBlocks: 0, readingBlocksEnded: 0, estMinutesDone: 0, actualMinutes: 0 };
const emptyPlan = (overrides: Partial<DailyPlanBodyDto> = {}) =>
  body({ status: "complete", blocks: [], currentBlockId: null, projected: [], totals: EMPTY_TOTALS, ...overrides });

const WHAT_LEAVES = "LearnLoop sends passages of the books you add, and your answers, to ChatGPT to write questions and give feedback.";

function connection(overrides: Partial<AiConnectionDto> = {}): AiConnectionDto {
  return {
    canAuthor: false,
    provider: "codex_medium",
    providerLabel: "ChatGPT",
    consentKey: "codex",
    consented: false,
    consentedAt: null,
    needs: "consent",
    message: null,
    whatLeaves: WHAT_LEAVES,
    chatgptSignedIn: true,
    openrouterKeyPresent: false,
    ...overrides
  };
}

function libraryCard(statusLine: SourceStatusLineDto | null, overrides: Partial<SourceLibraryCard> = {}): SourceLibraryCard {
  return {
    sourceId: "src_sym",
    title: "Symmetric Matrices and Variance",
    acquisitionKind: "web",
    canonicalUri: "https://example.org/sym",
    workId: null,
    currentRevisionId: "rev_1",
    revisionCount: 1,
    readiness: "ready",
    unitCount: 4,
    blockCount: 120,
    extractionStatus: "completed",
    suggestedRole: null,
    readerEnabled: true,
    updateAvailable: false,
    kindNoun: "article",
    statusLine,
    ...overrides
  };
}

const LINE = {
  waitingOk: { text: "Questions wait for your OK", tone: "quiet", action: { kind: "connect_ai", label: "Review" }, details: "Codex (your ChatGPT account)" },
  needsAi: { text: "Questions need an AI connection", tone: "quiet", action: { kind: "connect_ai", label: "Connect" }, details: null },
  writing: { text: "Writing questions for Ch. 1", tone: "working", action: null, details: null },
  failed: { text: "Questions for Ch. 1 need another try", tone: "problem", action: { kind: "retry", label: "Retry" }, details: null },
  costs: { text: "Building questions for Ch. 1 would cost about $0.40", tone: "quiet", action: { kind: "build_now", label: "Build them" }, details: null },
  built: { text: "Questions for Ch. 1 come up as you read", tone: "quiet", action: null, details: null }
} satisfies Record<string, SourceStatusLineDto>;

function emptyToday(cards: SourceLibraryCard[], extra: Record<string, ReturnType<typeof vi.fn>> = {}, plan: DailyPlanBodyDto = emptyPlan()) {
  return apis(dto(plan), {
    getSourceLibrary: vi.fn(async () => ({ version: 1, sources: cards, pending: [] })),
    getTodayQueue: vi.fn(async () => queue([])),
    ...extra
  });
}

function causeProps(overrides: Partial<TodayPlaceProps> = {}): Partial<TodayPlaceProps> {
  return { aiConnection: connection(), onConnectAi: vi.fn(), onOpenBook: vi.fn(), onOpenLibrary: vi.fn(), ...overrides };
}

describe("UX fix stage 3, P1: an empty or finished Today names its cause and carries its one action", () => {
  it("questions waiting for the OK: the cause, Give your OK (the one-time OK), and what's sent on demand", async () => {
    emptyToday([libraryCard(LINE.waitingOk)]);
    const props = show(causeProps({ session: SESSION }));
    expect((await screen.findByTestId("today-sentence")).textContent).toBe("Nothing planned for today.");
    const cause = await screen.findByTestId("today-cause");
    expect(cause.getAttribute("role")).toBe("status");
    expect(cause.textContent).toContain("Questions for “Symmetric Matrices and Variance” are waiting for your OK.");
    expect(cause.textContent).not.toContain(WHAT_LEAVES);
    fireEvent.click(within(cause).getByRole("button", { name: "what's sent ▸" }));
    expect(cause.textContent).toContain(WHAT_LEAVES);
    fireEvent.click(within(cause).getByRole("button", { name: "Give your OK" }));
    expect(props.onConnectAi).toHaveBeenCalledTimes(1);
    expect(findJargon(cause.textContent ?? "")).toEqual([]);
  });

  it("several books waiting: the first by name and how many more; with no AI connected, Connect", async () => {
    emptyToday([libraryCard(LINE.waitingOk), libraryCard(LINE.waitingOk, { sourceId: "src_2", title: "Elevator Paradox" })]);
    show(causeProps());
    expect((await screen.findByTestId("today-cause")).textContent).toContain("Questions for “Symmetric Matrices and Variance” and 1 more are waiting for your OK.");
    cleanup();
    clear();
    emptyToday([libraryCard(LINE.needsAi)]);
    const props = show(causeProps({ aiConnection: connection({ needs: "connect" }) }));
    const cause = await screen.findByTestId("today-cause");
    expect(cause.textContent).toContain("LearnLoop needs an AI connected to write questions for “Symmetric Matrices and Variance”.");
    fireEvent.click(within(cause).getByRole("button", { name: "Connect" }));
    expect(props.onConnectAi).toHaveBeenCalledTimes(1);
  });

  it("questions being written: on their way, keep reading, and Continue reading opens the book", async () => {
    const card = libraryCard(LINE.writing);
    emptyToday([card]);
    const props = show(causeProps({ aiConnection: connection({ needs: null, consented: true, canAuthor: true }) }));
    const cause = await screen.findByTestId("today-cause");
    expect(await within(cause).findByText("Getting “Symmetric Matrices and Variance” ready for questions")).toBeTruthy();
    expect(cause.textContent).toContain("Questions come as you finish sections. Keep reading meanwhile.");
    expect(within(cause).queryByRole("button", { name: /what's sent/ })).toBeNull();
    fireEvent.click(within(cause).getByRole("button", { name: "Continue reading" }));
    expect(props.onOpenBook).toHaveBeenCalledWith(card);
  });

  it("question writing failed: Couldn't get questions ready, Try again retries on the card, with what's sent beside it", async () => {
    const f = emptyToday([libraryCard(LINE.failed)], { sourceAction: vi.fn(async () => ({ sourceId: "src_sym", action: "retry" })) });
    show(causeProps({ aiConnection: connection({ needs: null, consented: true, canAuthor: true }) }));
    const cause = await screen.findByTestId("today-cause");
    expect(cause.textContent).toContain("Couldn't get questions ready for “Symmetric Matrices and Variance”.");
    expect(within(cause).getByRole("button", { name: "what's sent ▸" })).toBeTruthy();
    fireEvent.click(within(cause).getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(f.sourceAction).toHaveBeenCalledWith({ sourceId: "src_sym", action: "retry" }));
  });

  it("a card asking for something else (a cost to approve): the book needs a look, and Open Library goes there", async () => {
    emptyToday([libraryCard(LINE.costs)]);
    const props = show(causeProps({ aiConnection: connection({ needs: null, consented: true, canAuthor: true }) }));
    const cause = await screen.findByTestId("today-cause");
    expect(cause.textContent).toContain("“Symmetric Matrices and Variance” needs a look in your Library.");
    fireEvent.click(within(cause).getByRole("button", { name: "Open Library" }));
    expect(props.onOpenLibrary).toHaveBeenCalledTimes(1);
  });

  it("everything read has its questions: nothing more to add, and reading on brings more", async () => {
    const card = libraryCard(LINE.built);
    emptyToday([card]);
    const props = show(causeProps({ aiConnection: connection({ needs: null, consented: true, canAuthor: true }) }));
    const cause = await screen.findByTestId("today-cause");
    expect(cause.textContent).toContain("Your first questions come when you finish a section of “Symmetric Matrices and Variance”: finish its quick check, or press Done with this section at its end.");
    expect(cause.textContent).not.toContain("Everything you've read");
    fireEvent.click(within(cause).getByRole("button", { name: "Continue reading" }));
    expect(props.onOpenBook).toHaveBeenCalledWith(card);
  });

  it("today's list still has questions: says so (never 'nothing to practise') and opens the list", async () => {
    emptyToday([libraryCard(LINE.waitingOk)], { getTodayQueue: vi.fn(async () => queue([scheduled(1)])) });
    show(causeProps());
    const cause = await screen.findByTestId("today-cause");
    expect(cause.textContent).toContain("Today's list still has questions, if you'd like some.");
    fireEvent.click(within(cause).getByRole("button", { name: "Open today's list" }));
    expect(await screen.findByTestId("today-list")).toBeTruthy();
  });

  it("an open plan with no rows says its cause too", async () => {
    emptyToday([libraryCard(LINE.writing)], {}, body({ blocks: [], currentBlockId: null, projected: [], deciding: false, totals: EMPTY_TOTALS }));
    show(causeProps());
    expect(await within(await screen.findByTestId("today-cause")).findByText(/ready for questions/)).toBeTruthy();
  });

  it("a finished plan: nothing else is needed", async () => {
    const done = body({ status: "complete", blocks: [block({ status: "done" })], currentBlockId: null, projected: [] });
    // UX-16: "nothing else is needed" is said only when nothing is left, so today's list is empty here.
    apis(dto(done, { day: { plans: 1, kinds: ["normal"], complete: true, ...done.totals, actualMinutes: 6 } }), {
      getSourceLibrary: vi.fn(async () => ({ version: 1, sources: [libraryCard(LINE.built)], pending: [] })),
      getTodayQueue: vi.fn(async () => queue([]))
    });
    show(causeProps({ session: SESSION }));
    const line = await screen.findByTestId("today-finished");
    expect(line.textContent).toBe("Nothing else is needed today.");
    expect(line.getAttribute("role")).toBe("status");
    expect(screen.queryByTestId("today-cause")).toBeNull();
  });

  it("every cause line is in plain words", async () => {
    const lines = [LINE.waitingOk, LINE.needsAi, LINE.writing, LINE.failed, LINE.costs, LINE.built];
    for (const line of lines) {
      emptyToday([libraryCard(line)]);
      show(causeProps());
      const cause = await screen.findByTestId("today-cause");
      expect(findJargon(cause.textContent ?? "")).toEqual([]);
      cleanup();
      clear();
    }
  });
});

describe("UX fix stage 3: Practise for this goal with nothing ready says why, and offers the step", () => {
  it("a goal with no questions yet: the same cause as an empty Today, for the goal, with its action", async () => {
    const f = emptyToday([libraryCard(LINE.waitingOk)], {
      goalsList: vi.fn(async () => ({ version: 1, goals: [goal({ practicableItemCount: 0 })] })),
      getTodayQueue: vi.fn(async () => queue([scheduled(1)]))
    }, body());
    const props = show(causeProps({ session: SESSION }));
    const card = await screen.findByTestId("goal-card");
    fireEvent.click(within(card).getByRole("button", { name: "Practise for this goal" }));
    const line = await screen.findByTestId("goal-nothing-ready");
    expect(line.getAttribute("role")).toBe("status");
    expect(line.textContent).toContain("Nothing for this goal is ready to practise yet: questions for “Symmetric Matrices and Variance” are waiting for your OK.");
    fireEvent.click(within(line).getByRole("button", { name: "what's sent ▸" }));
    expect(line.textContent).toContain(WHAT_LEAVES);
    fireEvent.click(within(line).getByRole("button", { name: "Give your OK" }));
    expect(props.onConnectAi).toHaveBeenCalledTimes(1);
    expect(props.onError).not.toHaveBeenCalled();
    expect(f.planLearnerPick).not.toHaveBeenCalled();
    expect(findJargon(line.textContent ?? "")).toEqual([]);
  });

  it("a goal whose books' questions are all written: reading on brings more", async () => {
    const book = libraryCard(LINE.built);
    emptyToday([book], {
      goalsList: vi.fn(async () => ({ version: 1, goals: [goal({ practicableItemCount: 0 })] })),
      getTodayQueue: vi.fn(async () => queue([]))
    }, body());
    const props = show(causeProps({ session: SESSION, aiConnection: connection({ needs: null, consented: true, canAuthor: true }) }));
    const card = await screen.findByTestId("goal-card");
    fireEvent.click(within(card).getByRole("button", { name: "Practise for this goal" }));
    const line = await screen.findByTestId("goal-nothing-ready");
    expect(line.textContent).toContain("Nothing for this goal is ready to practise yet: your first questions come when you finish a section of “Symmetric Matrices and Variance”: finish its quick check, or press Done with this section at its end.");
    fireEvent.click(within(line).getByRole("button", { name: "Continue reading" }));
    expect(props.onOpenBook).toHaveBeenCalledWith(book);
  });
});

describe("UX fix stage 3 (item 6): Keep going that comes back with nothing open says the right thing for each way", () => {
  const finished = () => body({ status: "complete", blocks: [block({ status: "done" })], currentBlockId: null, projected: [] });
  const extension = () => dto(body({ id: "plan_kg", kind: "keep_going", status: "complete", stopReason: "nothing more worth doing today", blocks: [], currentBlockId: null, projected: [], totals: EMPTY_TOTALS }));

  it("nothing left to plan: says so where Keep going was pressed, and the day's cause with its action", async () => {
    const book = libraryCard(LINE.built);
    const f = apis(dto(finished()), {
      getSourceLibrary: vi.fn(async () => ({ version: 1, sources: [book], pending: [] })),
      getTodayQueue: vi.fn(async () => queue([])),
      planKeepGoing: vi.fn(async () => extension())
    });
    const props = show(causeProps({ session: SESSION, aiConnection: connection({ needs: null, consented: true, canAuthor: true }) }));
    expect((await screen.findByTestId("today-finished")).textContent).toBe("Nothing else is needed today.");
    fireEvent.click(screen.getByRole("button", { name: /Keep going/ }));
    await waitFor(() => expect(f.planKeepGoing).toHaveBeenCalledWith({ sessionId: "s1" }));
    expect((await screen.findByTestId("today-keep-going-nothing")).textContent).toBe("Nothing more to plan today.");
    const cause = await screen.findByTestId("today-cause");
    expect(cause.textContent).toContain("Your first questions come when you finish a section of");
    expect(screen.queryByTestId("today-finished")).toBeNull();
    fireEvent.click(within(cause).getByRole("button", { name: "Continue reading" }));
    expect(props.onOpenBook).toHaveBeenCalledWith(book);
  });

  it("a stop with questions still on today's list: never 'nothing to add', the list is offered", async () => {
    const f = apis(dto(finished()), {
      getSourceLibrary: vi.fn(async () => ({ version: 1, sources: [libraryCard(LINE.built)], pending: [] })),
      getTodayQueue: vi.fn(async () => queue([scheduled(1), scheduled(2)])),
      planKeepGoing: vi.fn(async () => extension())
    });
    show(causeProps({ session: SESSION }));
    await screen.findByTestId("today-done");
    fireEvent.click(screen.getByRole("button", { name: /Keep going/ }));
    await waitFor(() => expect(f.planKeepGoing).toHaveBeenCalledOnce());
    const cause = await screen.findByTestId("today-cause");
    expect(cause.textContent).toContain("Today's list still has questions, if you'd like some.");
    expect(surface()).not.toMatch(/everything you've read|Reading on, or adding a book/i);
    fireEvent.click(within(cause).getByRole("button", { name: "Open today's list" }));
    expect(await screen.findByTestId("today-list")).toBeTruthy();
  });

  it("the plan switched off meanwhile: no 'nothing more' line and no error (Today becomes the plan-off Begin)", async () => {
    const f = apis(dto(finished()), {
      getSourceLibrary: vi.fn(async () => ({ version: 1, sources: [libraryCard(LINE.built)], pending: [] })),
      planKeepGoing: vi.fn(async () => dto(null, { reason: "plan_disabled" }))
    });
    const props = show(causeProps({ session: SESSION }));
    await screen.findByTestId("today-done");
    fireEvent.click(screen.getByRole("button", { name: /Keep going/ }));
    await waitFor(() => expect(f.planKeepGoing).toHaveBeenCalledOnce());
    await flush();
    expect(screen.queryByTestId("today-keep-going-nothing")).toBeNull();
    expect(screen.queryByTestId("today-cause")).toBeNull();
    expect(props.onError).not.toHaveBeenCalled();
  });
});

describe("UX fix stage 3 (item 3, F9): one clock on Today", () => {
  it("a begun plan names its room, the rows their own estimates, and the minute chips the plan's length", async () => {
    const begun = body({
      minutesAreASuggestion: true,
      minutesLeft: 22,
      minutesPastPlan: 0,
      blocks: [block({ id: "b0", status: "done" }), block({ id: "blk_2", ordinal: 2, status: "current", startedAt: "2026-10-26T18:05:00Z", estMinutes: 2 })],
      currentBlockId: "blk_2",
      projected: []
    });
    apis(dto(begun));
    show({ session: SESSION });
    const sentence = await screen.findByTestId("today-sentence");
    expect(sentence.textContent).toContain("Room for about 22 more minutes of today's suggested time. Next: ");
    expect(sentence.textContent).not.toMatch(/minutes left/);
    expect(screen.getByTestId("today-block").textContent).toContain("about 2 min");
    expect(screen.getByRole("radiogroup", { name: "minutes today" })).toBeTruthy();
  });

  it("after the plan is done the minute chips are not shown: today's length means nothing then", async () => {
    const done = body({ status: "complete", blocks: [block({ status: "done" })], currentBlockId: null, projected: [] });
    apis(dto(done, { day: { plans: 1, kinds: ["normal"], complete: true, ...done.totals, readingBlocks: 0, actualMinutes: 2.2 } }));
    show({ session: SESSION });
    expect((await screen.findByTestId("today-sentence")).textContent).toBe("Done for today · 2 minutes spent answering.");
    expect(screen.queryByRole("radiogroup", { name: "minutes today" })).toBeNull();
  });
});

// "Waiting you can see" (docs/reviews/ux-waiting.md, the owner's case 1): from
// the press until the question is on screen, Today says what is happening, but
// only once the wait outlasts the indicator's delay, and the line is gone when
// the step opens.
describe("waiting you can see: Today to the question", () => {
  function deferred<T>() {
    let resolve!: (value: T) => void;
    const promise = new Promise<T>((done) => { resolve = done; });
    return { promise, resolve };
  }
  // The screen is read with the harness's real timers; the press and the wait run on fake ones.
  // (A second useFakeTimers is a no-op while the harness fakes Date: real timers first.)
  function freezeTimers() {
    const now = Date.now();
    vi.useRealTimers();
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "Date"], now });
  }
  async function advance(ms: number) {
    await act(async () => { await vi.advanceTimersByTimeAsync(ms); });
  }
  const STEP = { step: { kind: "item", planId: "plan_1", blockId: "blk_2", practiceItemId: "pi_a", learningObjectId: "lo_e", origin: "chooser", schedulerCandidateId: "cand_a", presentationId: "pres_a", boundary: false } };

  it("Begin: nothing before the delay, then 'Choosing what's next…', gone when the question opens", async () => {
    const served = deferred<unknown>();
    apis(dto(body()), { nextPlanItem: vi.fn(() => served.promise) });
    const props = show({ session: SESSION });
    await screen.findByTestId("today-sentence");
    freezeTimers();
    fireEvent.click(screen.getByTestId("today-begin"));
    await advance(300);
    expect(screen.queryByText(/Choosing what's next…/)).toBeNull();
    await advance(100);
    const line = screen.getByTestId("waiting");
    expect(line.getAttribute("role")).toBe("status");
    expect(line.textContent).toBe("◐ Choosing what's next…");
    served.resolve(STEP);
    await advance(0);
    expect(props.onOpenPractice).toHaveBeenCalledWith("pi_a", "cand_a", null, "pres_a");
    expect(screen.queryByTestId("waiting")).toBeNull();
  });

  it("Begin with no session: the line covers starting the session and serving its first step", async () => {
    const served = deferred<unknown>();
    apis(dto(body()), { nextPlanItem: vi.fn(() => served.promise) });
    const props = show();
    await screen.findByTestId("today-sentence");
    freezeTimers();
    await press({ key: "Enter" });
    await advance(400);
    expect(screen.getByTestId("waiting").textContent).toBe("◐ Choosing what's next…");
    served.resolve(STEP);
    await advance(0);
    expect(props.onBeginSession).toHaveBeenCalledTimes(1);
    expect(screen.queryByTestId("waiting")).toBeNull();
  });

  it("a row of the full list: 'Opening the question…' until the pick is served", async () => {
    const picked = deferred<unknown>();
    apis(dto(body()), { planLearnerPick: vi.fn(() => picked.promise) });
    const props = show({ session: SESSION });
    await screen.findByTestId("today-sentence");
    await press({ key: "l" });
    const row = (await screen.findAllByTestId("today-list-row"))[0];
    freezeTimers();
    fireEvent.click(within(row).getAllByRole("button")[0]);
    await advance(300);
    expect(screen.queryByText(/Opening the question…/)).toBeNull();
    await advance(100);
    expect(screen.getByTestId("waiting").textContent).toBe("◐ Opening the question…");
    picked.resolve({ step: { kind: "item", planId: "plan_1", blockId: "blk_pick", practiceItemId: "pi_1", learningObjectId: "lo_1", origin: "learner_pick", schedulerCandidateId: "cand_pick", presentationId: "pres_pick", boundary: false } });
    await advance(0);
    expect(props.onOpenPractice).toHaveBeenCalled();
    expect(screen.queryByTestId("waiting")).toBeNull();
  });

  it("Practise for this goal: 'Finding a question for this goal…' through the list read and the pick", async () => {
    const picked = deferred<unknown>();
    apis(dto(body()), {
      goalsList: vi.fn(async () => ({ version: 1, goals: [goal()] })),
      getTodayQueue: vi.fn(async () => queue([scheduled(1), scheduled(2, { components: { goalFrontier: 0.4 } as ScheduledItemDto["components"] })])),
      planLearnerPick: vi.fn(() => picked.promise)
    });
    const props = show({ session: SESSION });
    const card = await screen.findByTestId("goal-card");
    const practise = await within(card).findByRole("button", { name: "Practise for this goal" });
    freezeTimers();
    fireEvent.click(practise);
    await advance(300);
    expect(screen.queryByTestId("waiting")?.textContent ?? "").toBe("");
    await advance(100);
    expect(screen.getByTestId("waiting").textContent).toBe("◐ Finding a question for this goal…");
    picked.resolve({ step: null });
    await advance(0);
    expect(props.onOpenPractice).toHaveBeenCalled();
    expect(screen.queryByTestId("waiting")).toBeNull();
  });

  it("Keep going on a finished day: 'Adding more to today…' until the plan is back", async () => {
    const done = body({ status: "complete", blocks: [block({ status: "done" })], currentBlockId: null, projected: [] });
    const more = body({ id: "plan_kg", kind: "keep_going", blocks: [block({ id: "blk_kg" })], currentBlockId: "blk_kg", projected: [] });
    const extended = deferred<unknown>();
    apis(dto(done), { planKeepGoing: vi.fn(() => extended.promise) });
    show({ session: SESSION });
    await screen.findByTestId("today-done");
    freezeTimers();
    fireEvent.click(screen.getByRole("button", { name: /Keep going/ }));
    await advance(300);
    expect(screen.queryByText(/Adding more to today…/)).toBeNull();
    await advance(100);
    expect(screen.getByTestId("waiting").textContent).toBe("◐ Adding more to today…");
    extended.resolve(dto(more));
    await advance(0);
    expect(screen.queryByTestId("waiting")).toBeNull();
  });

  it("app start and every return to Today: 'Reading today's plan…' after the delay, gone when the plan is there", async () => {
    const read = deferred<DailyPlanDto>();
    apis(() => read.promise);
    freezeTimers();
    show({ session: SESSION });
    await advance(300);
    expect(screen.getByTestId("today-loading").textContent).toBe("");
    await advance(100);
    expect(screen.getByTestId("plan-wait").textContent).toBe("◐ Reading today's plan…");
    read.resolve(dto(body()));
    await advance(0);
    expect(screen.getByTestId("today-sentence")).toBeTruthy();
    expect(screen.queryByTestId("plan-wait")).toBeNull();
  });

  it("a fast step never shows the line", async () => {
    apis(dto(body()));
    const props = show({ session: SESSION });
    await screen.findByTestId("today-sentence");
    freezeTimers();
    fireEvent.click(screen.getByTestId("today-begin"));
    await advance(50);
    expect(props.onOpenPractice).toHaveBeenCalled();
    await advance(1000);
    expect(screen.queryByTestId("waiting")).toBeNull();
  });
});

// ── Broken controls, second round (UX journey audit part 2) ────────────────

describe("UX-14: a lesson left open waits on Today with its one action", () => {
  const OPEN = { lessonId: "les_dot", title: "Dot product", goal: null, openedAt: "2026-10-27T18:00:00Z", learningObjectIds: ["lo_dot"] };

  it("an open lesson shows as 'Continue your lesson on …', and Continue resumes that lesson", async () => {
    const f = apis(dto(body()), { lessonOpenLessons: vi.fn(async () => ({ lessons: [OPEN] })) });
    const onStartLesson = vi.fn();
    show({ session: SESSION, onStartLesson });
    const line = await screen.findByTestId("today-open-lesson");
    expect(line.textContent).toContain("Continue your lesson on Dot product");
    expect(findJargon(line.textContent ?? "")).toEqual([]);
    fireEvent.click(within(line).getByRole("button", { name: "Continue" }));
    expect(onStartLesson).toHaveBeenCalledWith({ kind: "resume", lessonId: "les_dot" });
    expect(f.lessonOpenLessons).toHaveBeenCalledTimes(1);
  });

  it("read again when a lesson on top of Today closes, so a lesson closed with Close shows at once", async () => {
    const lessonOpenLessons = vi.fn(async () => ({ lessons: [] as typeof OPEN[] }));
    apis(dto(body()), { lessonOpenLessons });
    const props = { session: SESSION, onStartLesson: vi.fn(), lessonOpen: true };
    const { rerender } = render(<TodayPlace {...defaultProps()} {...props} />);
    await screen.findByTestId("today-sentence");
    expect(lessonOpenLessons).not.toHaveBeenCalled();
    lessonOpenLessons.mockResolvedValueOnce({ lessons: [OPEN] });
    rerender(<TodayPlace {...defaultProps()} {...props} lessonOpen={false} />);
    expect((await screen.findByTestId("today-open-lesson")).textContent).toContain("Dot product");
  });

  it("without lessons (no onStartLesson) nothing is asked", async () => {
    const f = apis(dto(body()), { lessonOpenLessons: vi.fn(async () => ({ lessons: [OPEN] })) });
    show({ session: SESSION });
    await screen.findByTestId("today-sentence");
    await flush();
    expect(f.lessonOpenLessons).not.toHaveBeenCalled();
    expect(screen.queryByTestId("today-open-lesson")).toBeNull();
  });
});

function defaultProps(): TodayPlaceProps {
  return {
    session: null,
    streak: { current: 4, activeToday: false, longest: 9 },
    onBeginSession: vi.fn(),
    onStartSession: vi.fn(async (minutes: number) => (await fns.startSession({ availableMinutes: minutes })) as SessionSnapshot),
    onOpenPractice: vi.fn(),
    onOpenPlanReading: vi.fn(),
    onEndSession: vi.fn(),
    onAdd: vi.fn(),
    onOpenPassage: vi.fn(),
    onResumeProblem: vi.fn(),
    onAsk: vi.fn(),
    onTakeExam: vi.fn(),
    onError: vi.fn()
  };
}

describe("UX-16: a plan that stopped with work left never says nothing else is needed", () => {
  const finished = (overrides: Partial<DailyPlanBodyDto> = {}) =>
    body({ status: "complete", stopReason: "A good place to stop for today.", blocks: [block({ status: "done" })], currentBlockId: null, projected: [], ...overrides });

  it("stopped with questions still on today's list: says there is more, and offers the list (seasoned-2 #59)", async () => {
    const done = finished();
    apis(dto(done, { day: { plans: 1, kinds: ["normal"], complete: true, ...done.totals, actualMinutes: 0.6 } }), {
      getTodayQueue: vi.fn(async () => queue([scheduled(1), scheduled(2), scheduled(3)]))
    });
    show({ session: SESSION });
    const line = await screen.findByTestId("today-stopped-more");
    expect(line.getAttribute("role")).toBe("status");
    expect(line.textContent).toContain("The plan stopped here, but there's more for today if you'd like it.");
    expect(screen.queryByTestId("today-finished")).toBeNull();
    expect(surface()).not.toContain("Nothing else is needed today.");
    expect(screen.getByRole("button", { name: /Keep going/ })).toBeTruthy();
    expect(findJargon(line.textContent ?? "")).toEqual([]);
    fireEvent.click(within(line).getByRole("button", { name: "Open today's list" }));
    expect(await screen.findByTestId("today-list")).toBeTruthy();
  });

  it("a catch-up done beside a list still holding questions says the same (returner-1 #49-51)", async () => {
    const done = finished({ kind: "reentry", reentry: { gapDays: 22, solidCount: 4, slippedCount: 9, slippedNames: [], namedBy: "priority", target: 0.8, planMinutes: 2, planItems: 2 } });
    apis(dto(done), { getTodayQueue: vi.fn(async () => queue(Array.from({ length: 9 }, (_, index) => scheduled(index + 1)))) });
    show({ session: SESSION });
    expect((await screen.findByTestId("today-sentence")).textContent).toBe("Catch-up done.");
    expect((await screen.findByTestId("today-stopped-more")).textContent).toContain("there's more for today");
    expect(surface()).not.toContain("Nothing else is needed today.");
  });

  it("a block of the closed plan not done yet is work left too, whatever the list says", async () => {
    const done = finished({ blocks: [block({ status: "done" }), block({ id: "blk_2", ordinal: 2, status: "upcoming" })] });
    apis(dto(done), { getTodayQueue: vi.fn(async () => queue([])) });
    show({ session: SESSION });
    const line = await screen.findByTestId("today-stopped-more");
    expect(within(line).queryByRole("button", { name: "Open today's list" })).toBeNull();
    expect(screen.queryByTestId("today-finished")).toBeNull();
  });

  it("nothing is claimed before the list is read", async () => {
    const done = finished();
    apis(dto(done), { getTodayQueue: vi.fn(() => new Promise<QueueSnapshot>(() => undefined)) });
    show({ session: SESSION });
    await screen.findByTestId("today-done");
    await flush();
    expect(screen.queryByTestId("today-finished")).toBeNull();
    expect(screen.queryByTestId("today-stopped-more")).toBeNull();
  });
});

describe("UX-21: Begin whose first step is a lesson offer leads to the offer", () => {
  const OFFER_STEP = {
    kind: "lesson_offer" as const, planId: "plan_1", blockId: "blk_offer", blockOrdinal: 1, estMinutes: 15, boundary: true,
    offer: { decisionId: "dec1", blockId: "blk_offer", minutes: 15, whyLabel: "Suggested by LearnLoop's planner", answered: null,
             suggestion: { ref: "lesson:lo_e", title: "Eigenvalues", learningObjectIds: ["lo_e"], reason: "cold_failing", why: "Two misses." },
             alternatives: [] }
  };

  it("with a session: the served offer goes to the shell, which opens its page (returner-1 #21-23)", async () => {
    apis(dto(body()), { nextPlanItem: vi.fn(async () => ({ ...dto(body()), step: OFFER_STEP })) });
    const onLessonOffer = vi.fn();
    const props = show({ session: SESSION, onLessonOffer });
    await screen.findByTestId("today-sentence");
    fireEvent.click(screen.getByTestId("today-begin"));
    await waitFor(() => expect(onLessonOffer).toHaveBeenCalledWith(OFFER_STEP));
    expect(props.onOpenPractice).not.toHaveBeenCalled();
  });

  it("without a session: the started session and the offer go to the shell together", async () => {
    apis(dto(body()), { nextPlanItem: vi.fn(async () => ({ ...dto(body()), step: OFFER_STEP })) });
    const props = show({ onLessonOffer: vi.fn() });
    await screen.findByTestId("today-sentence");
    fireEvent.click(screen.getByTestId("today-begin"));
    await waitFor(() => expect(props.onBeginSession).toHaveBeenCalledWith(STARTED, OFFER_STEP));
  });
});

describe("First questions arrive (P11, F20): Today offers a book's first questions, or says what must happen first", () => {
  const ready = () => connection({ needs: null, consented: true, canAuthor: true });
  const facts = (overrides: Partial<NonNullable<SourceStatusLineDto["questions"]>> = {}) => ({
    count: 0, itemIds: [], sections: [], writing: [], failed: [], toLookAt: 0, sectionCount: 4, ...overrides
  });
  const built = (questions = facts()): SourceStatusLineDto => ({ ...LINE.built, questions });

  it("a build under way: the waiting line says how far it is and the measured time, with Continue reading from the first moment", async () => {
    const card = libraryCard({ ...LINE.writing, progress: { done: 1, total: 2 }, minutes: 3.6 });
    emptyToday([card]);
    const props = show(causeProps({ aiConnection: ready() }));
    const cause = await screen.findByTestId("today-cause");
    // The action is there before the line's delay; the wait is the status region.
    fireEvent.click(within(cause).getByRole("button", { name: "Continue reading" }));
    expect(props.onOpenBook).toHaveBeenCalledWith(card);
    expect(cause.getAttribute("role")).toBeNull();
    expect(within(cause).getByTestId("today-cause-wait").getAttribute("role")).toBe("status");
    expect(await within(cause).findByText("Getting “Symmetric Matrices and Variance” ready for questions · 1 of 2 steps done · usually about 4 min")).toBeTruthy();
    expect(cause.textContent).toContain("Questions come as you finish sections. Keep reading meanwhile.");
  });

  it("a build with no measured time says none, and under a minute only when measured so", async () => {
    emptyToday([libraryCard({ ...LINE.writing, progress: { done: 0, total: 2 } })]);
    show(causeProps({ aiConnection: ready() }));
    expect(await within(await screen.findByTestId("today-cause")).findByText("Getting “Symmetric Matrices and Variance” ready for questions · 0 of 2 steps done")).toBeTruthy();
    cleanup();
    clear();
    emptyToday([libraryCard({ ...LINE.writing, minutes: 0.4 })]);
    show(causeProps({ aiConnection: ready() }));
    expect(await within(await screen.findByTestId("today-cause")).findByText("Getting “Symmetric Matrices and Variance” ready for questions · usually under a minute")).toBeTruthy();
  });

  it("a build that stopped after trying twice: P11's words, and Try again retries on the card", async () => {
    const f = emptyToday([libraryCard({ ...LINE.failed, retried: true })], { sourceAction: vi.fn(async () => ({ sourceId: "src_sym", action: "retry" })) });
    show(causeProps({ aiConnection: ready() }));
    const cause = await screen.findByTestId("today-cause");
    expect(cause.textContent).toContain("Couldn't get “Symmetric Matrices and Variance” ready for questions, after trying twice. Try again, or keep reading: nothing is lost.");
    fireEvent.click(within(cause).getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(f.sourceAction).toHaveBeenCalledWith({ sourceId: "src_sym", action: "retry" }));
    cleanup();
    clear();
    emptyToday([libraryCard({ ...LINE.failed, retried: false })]);
    show(causeProps({ aiConnection: ready() }));
    expect((await screen.findByTestId("today-cause")).textContent).toContain("Couldn't get “Symmetric Matrices and Variance” ready for questions. Try again, or keep reading: nothing is lost.");
  });

  it("built, no section finished yet: the rule that brings the first questions, never 'everything you've read has its questions'", async () => {
    const card = libraryCard(built());
    emptyToday([card]);
    const props = show(causeProps({ aiConnection: ready() }));
    const cause = await screen.findByTestId("today-cause");
    expect(cause.textContent).toContain("Your first questions come when you finish a section of “Symmetric Matrices and Variance”: finish its quick check, or press Done with this section at its end.");
    expect(cause.textContent).not.toMatch(/Everything you've read|on their way/);
    fireEvent.click(within(cause).getByRole("button", { name: "Continue reading" }));
    expect(props.onOpenBook).toHaveBeenCalledWith(card);
  });

  it("a finished section's questions being written: the waiting line names the part read", async () => {
    const card = libraryCard(built(facts({ writing: ["Conditional probability"] })));
    emptyToday([card]);
    const props = show(causeProps({ aiConnection: ready() }));
    const cause = await screen.findByTestId("today-cause");
    expect(await within(cause).findByText("Writing questions from “Conditional probability”, the part you read…")).toBeTruthy();
    expect(cause.textContent).toContain("Keep reading meanwhile.");
    fireEvent.click(within(cause).getByRole("button", { name: "Continue reading" }));
    expect(props.onOpenBook).toHaveBeenCalledWith(card);
  });

  it("first questions on today's list: how many, from the part read, and Begin opens the first of them", async () => {
    const f = emptyToday([libraryCard(built(facts({ count: 5, itemIds: ["pi_2", "pi_7", "pi_8", "pi_9", "pi_1"], sections: ["Conditional probability"] })))], {
      getTodayQueue: vi.fn(async () => queue([scheduled(1), scheduled(2), scheduled(3)]))
    });
    const props = show(causeProps({ aiConnection: ready() }));
    const cause = await screen.findByTestId("today-cause");
    expect(cause.textContent).toContain("2 questions from “Conditional probability”, the part you read. More come as you finish sections.");
    expect(cause.textContent).not.toContain("Today's list still has questions");
    fireEvent.click(within(cause).getByRole("button", { name: "Begin ↵" }));
    // The first of them in today's list's order, as a pick from the list (a session for the plan's minutes first).
    await waitFor(() => expect(f.planLearnerPick).toHaveBeenCalledWith("pi_1", "s_new", "cand_1"));
    await waitFor(() => expect(props.onBeginSession).toHaveBeenCalled());
  });

  it("Enter on the page is that Begin", async () => {
    const f = emptyToday([libraryCard(built(facts({ count: 1, itemIds: ["pi_2"], sections: ["Conditional probability"] })))], {
      getTodayQueue: vi.fn(async () => queue([scheduled(1), scheduled(2)]))
    });
    show(causeProps({ aiConnection: ready(), session: SESSION }));
    expect((await screen.findByTestId("today-cause")).textContent).toContain("1 question from “Conditional probability”, the part you read.");
    await press({ key: "Enter" });
    await waitFor(() => expect(f.planLearnerPick).toHaveBeenCalledWith("pi_2", "s1", "cand_2"));
    expect(f.planKeepGoing).not.toHaveBeenCalled();
  });

  it("a reading that is one section is named by its book", async () => {
    emptyToday([libraryCard(built(facts({ count: 3, itemIds: ["pi_1"], sections: ["Document"], sectionCount: 1 })))], {
      getTodayQueue: vi.fn(async () => queue([scheduled(1)]))
    });
    show(causeProps({ aiConnection: ready() }));
    expect((await screen.findByTestId("today-cause")).textContent).toContain("1 question from what you read in “Symmetric Matrices and Variance”. More come as you finish sections.");
  });

  it("questions from reading, none on today's list: not up today, and more come as sections are finished", async () => {
    emptyToday([libraryCard(built(facts({ count: 4, itemIds: ["pi_x"], sections: ["Conditional probability"] })))]);
    show(causeProps({ aiConnection: ready() }));
    expect((await screen.findByTestId("today-cause")).textContent).toContain("Nothing from “Symmetric Matrices and Variance” is up today. More questions come as you finish sections.");
  });

  it("a finished section whose questions stopped: Try again asks for them again", async () => {
    const f = emptyToday([libraryCard(built(facts({ failed: [{ label: "Conditional probability", resumeId: "batch_sec" }] })))], {
      resumeIngestBatch: vi.fn(async () => ({ id: "batch_sec", status: "queued" }))
    });
    show(causeProps({ aiConnection: ready() }));
    const cause = await screen.findByTestId("today-cause");
    expect(cause.textContent).toContain("Couldn't write the questions from “Conditional probability”. Try again, or keep reading: nothing is lost.");
    fireEvent.click(within(cause).getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(f.resumeIngestBatch).toHaveBeenCalledWith("batch_sec"));
  });

  it("a build that ends while the learner is elsewhere updates Today when the shell says the queue changed, with no press", async () => {
    const lines = [{ ...LINE.writing, progress: { done: 1, total: 2 } } as SourceStatusLineDto];
    const f = emptyToday([], { getSourceLibrary: vi.fn(async () => ({ version: 1, sources: [libraryCard(lines[0])], pending: [] })) });
    show(causeProps({ aiConnection: ready() }));
    expect(await within(await screen.findByTestId("today-cause")).findByText(/ready for questions · 1 of 2 steps done/)).toBeTruthy();
    const reads = f.getSourceLibrary.mock.calls.length;
    lines[0] = { ...LINE.failed, retried: true };
    // The shell's revision poll reports the build's end: well before Today's own five-second reread.
    act(() => notifyQueueChanged());
    await waitFor(() => expect(screen.getByTestId("today-cause").textContent).toContain("after trying twice"), { timeout: 2000 });
    expect(f.getSourceLibrary.mock.calls.length).toBeGreaterThan(reads);
  });

  it("every new line is in plain words", async () => {
    const lines: SourceStatusLineDto[] = [
      { ...LINE.writing, progress: { done: 1, total: 2 }, minutes: 3 },
      { ...LINE.failed, retried: true },
      built(),
      built(facts({ writing: ["Conditional probability"] })),
      built(facts({ failed: [{ label: "Conditional probability", resumeId: "b" }] })),
      built(facts({ count: 2, itemIds: ["pi_x"], sections: ["Conditional probability"] }))
    ];
    for (const line of lines) {
      emptyToday([libraryCard(line)]);
      show(causeProps({ aiConnection: ready() }));
      const cause = await screen.findByTestId("today-cause");
      await new Promise((resolve) => setTimeout(resolve, 400));
      expect(findJargon(cause.textContent ?? "")).toEqual([]);
      cleanup();
      clear();
    }
  });
});

describe("A section finished before its book is ready: Today says its questions come once the book is (UX-31)", () => {
  const ready = () => connection({ needs: null, consented: true, canAuthor: true });
  const facts = (overrides: Partial<NonNullable<SourceStatusLineDto["questions"]>> = {}) => ({
    count: 0, itemIds: [], sections: [], writing: [], waiting: [], failed: [], toLookAt: 0, sectionCount: 4, ...overrides
  });

  it("while the book is being got ready: the wait, and the finished section's questions promised for then, not 'finish a section'", async () => {
    const card = libraryCard({ ...LINE.writing, progress: { done: 1, total: 2 }, questions: facts({ waiting: ["Conditional probability"] }) });
    emptyToday([card]);
    const props = show(causeProps({ aiConnection: ready() }));
    const cause = await screen.findByTestId("today-cause");
    expect(await within(cause).findByText("Getting “Symmetric Matrices and Variance” ready for questions · 1 of 2 steps done")).toBeTruthy();
    expect(cause.textContent).toContain(
      "Your questions from “Conditional probability” will be written as soon as “Symmetric Matrices and Variance” is ready. Keep reading meanwhile."
    );
    expect(cause.textContent).not.toMatch(/finish a section|Questions come as you finish sections/);
    fireEvent.click(within(cause).getByRole("button", { name: "Continue reading" }));
    expect(props.onOpenBook).toHaveBeenCalledWith(card);
  });

  it("a reading that is one section is said as what you read", async () => {
    emptyToday([libraryCard({ ...LINE.writing, questions: facts({ waiting: ["Document"], sectionCount: 1 }) })]);
    show(causeProps({ aiConnection: ready() }));
    expect((await screen.findByTestId("today-cause")).textContent).toContain(
      "Your questions from what you read will be written as soon as “Symmetric Matrices and Variance” is ready."
    );
  });

  it("a waiting section on a book whose card says nothing else: the promise, with Continue reading", async () => {
    const card = libraryCard({ ...LINE.built, questions: facts({ waiting: ["Conditional probability"] }) });
    emptyToday([card]);
    const props = show(causeProps({ aiConnection: ready() }));
    const cause = await screen.findByTestId("today-cause");
    expect(cause.textContent).toContain(
      "Your questions from “Conditional probability” will be written as soon as “Symmetric Matrices and Variance” is ready."
    );
    expect(cause.textContent).not.toContain("Your first questions come when you finish a section");
    fireEvent.click(within(cause).getByRole("button", { name: "Continue reading" }));
    expect(props.onOpenBook).toHaveBeenCalledWith(card);
  });

  it("when the book is ready the writing shows on the shell's queue-changed signal, with no press", async () => {
    const lines: SourceStatusLineDto[] = [{ ...LINE.writing, questions: facts({ waiting: ["Conditional probability"] }) }];
    const f = emptyToday([], { getSourceLibrary: vi.fn(async () => ({ version: 1, sources: [libraryCard(lines[0])], pending: [] })) });
    show(causeProps({ aiConnection: ready() }));
    await waitFor(() => expect(screen.getByTestId("today-cause").textContent).toContain("will be written as soon as"));
    const reads = f.getSourceLibrary.mock.calls.length;
    // The build applied its topics and started the section's writing; its end bumps the revision the shell reads.
    lines[0] = { ...LINE.built, questions: facts({ writing: ["Conditional probability"] }) };
    act(() => notifyQueueChanged());
    await waitFor(() => expect(screen.getByTestId("today-cause").textContent).toContain("Writing questions from “Conditional probability”, the part you read…"), { timeout: 2000 });
    expect(f.getSourceLibrary.mock.calls.length).toBeGreaterThan(reads);
  });

  it("the new lines are in plain words", async () => {
    for (const line of [
      { ...LINE.writing, questions: facts({ waiting: ["Conditional probability"] }) },
      { ...LINE.built, questions: facts({ waiting: ["Document"], sectionCount: 1 }) }
    ] as SourceStatusLineDto[]) {
      emptyToday([libraryCard(line)]);
      show(causeProps({ aiConnection: ready() }));
      const cause = await screen.findByTestId("today-cause");
      await new Promise((resolve) => setTimeout(resolve, 400));
      expect(findJargon(cause.textContent ?? "")).toEqual([]);
      cleanup();
      clear();
    }
  });
});

describe("Question writing you can follow: how far it is, the questions already there, a topic that could not be written", () => {
  const ready = () => connection({ needs: null, consented: true, canAuthor: true });
  const facts = (overrides: Partial<NonNullable<SourceStatusLineDto["questions"]>> = {}) => ({
    count: 0, itemIds: [], sections: [], writing: [], waiting: [], failed: [], toLookAt: 0, sectionCount: 4, ...overrides
  });
  const built = (questions = facts()): SourceStatusLineDto => ({ ...LINE.built, questions });
  const FAILED_TOPIC = "Not every topic's questions could be written.";

  it("the writing line says how many topics are done, where the fact gives it for the section named", async () => {
    const card = libraryCard(built(facts({ writing: ["Conditional probability"], progress: { done: 2, total: 8 } })));
    emptyToday([card]);
    const props = show(causeProps({ aiConnection: ready() }));
    const cause = await screen.findByTestId("today-cause");
    expect(await within(cause).findByText("Writing questions from “Conditional probability”, the part you read · 2 of 8 topics done")).toBeTruthy();
    expect(cause.textContent).toContain("Keep reading meanwhile.");
    fireEvent.click(within(cause).getByRole("button", { name: "Continue reading" }));
    expect(props.onOpenBook).toHaveBeenCalledWith(card);
    cleanup();
    clear();
    // A reading that is one section: named by its book, with its amount.
    emptyToday([libraryCard(built(facts({ writing: ["Document"], sectionCount: 1, progress: { done: 0, total: 1 } })))]);
    show(causeProps({ aiConnection: ready() }));
    expect(await within(await screen.findByTestId("today-cause")).findByText("Writing questions from what you read in “Symmetric Matrices and Variance” · 0 of 1 topic done")).toBeTruthy();
  });

  it("no amount where the fact gives none, or where it adds up another finished section too", async () => {
    emptyToday([libraryCard(built(facts({ writing: ["Conditional probability"] })))]);
    show(causeProps({ aiConnection: ready() }));
    expect(await within(await screen.findByTestId("today-cause")).findByText("Writing questions from “Conditional probability”, the part you read…")).toBeTruthy();
    cleanup();
    clear();
    // "Bayes' rule" was finished earlier and gave its questions (no longer on today's list): the book's count adds
    // up its topics too, so it is not how far “Conditional probability” is.
    emptyToday([libraryCard(built(facts({ count: 3, itemIds: ["pi_x"], sections: ["Bayes' rule"], writing: ["Conditional probability"], progress: { done: 8, total: 14 } })))]);
    show(causeProps({ aiConnection: ready() }));
    const cause = await screen.findByTestId("today-cause");
    expect(await within(cause).findByText("Writing questions from “Conditional probability”, the part you read…")).toBeTruthy();
    expect(cause.textContent).not.toMatch(/topics? done/);
  });

  it("questions ready while more are written: how many and how far, Begin opens the first, and the count follows the parts", async () => {
    const lines = [built(facts({ count: 3, itemIds: ["pi_2", "pi_1", "pi_9"], sections: ["Conditional probability"], writing: ["Conditional probability"], progress: { done: 2, total: 8 } }))];
    const f = emptyToday([], {
      getSourceLibrary: vi.fn(async () => ({ version: 1, sources: [libraryCard(lines[0])], pending: [] })),
      getTodayQueue: vi.fn(async () => queue([scheduled(1), scheduled(2), scheduled(3)]))
    });
    const props = show(causeProps({ aiConnection: ready() }));
    const cause = await screen.findByTestId("today-cause");
    await waitFor(() => expect(cause.textContent).toContain("2 questions from “Conditional probability” are ready. More are being written (2 of 8 topics done)."));
    expect(cause.textContent).not.toMatch(/Writing questions from|More come as you finish sections/);
    expect(within(cause).queryByRole("button", { name: "Continue reading" })).toBeNull();
    // The next topic's questions apply: the revision the shell reads moves, Today reads the books and the list again.
    lines[0] = built(facts({ count: 6, itemIds: ["pi_2", "pi_1", "pi_9", "pi_3"], sections: ["Conditional probability"], writing: ["Conditional probability"], progress: { done: 3, total: 8 } }));
    act(() => notifyQueueChanged());
    await waitFor(() => expect(screen.getByTestId("today-cause").textContent).toContain("3 questions from “Conditional probability” are ready. More are being written (3 of 8 topics done)."), { timeout: 2000 });
    fireEvent.click(within(screen.getByTestId("today-cause")).getByRole("button", { name: "Begin ↵" }));
    // The first of them in today's list's order, as a pick from the list.
    await waitFor(() => expect(f.planLearnerPick).toHaveBeenCalledWith("pi_1", "s_new", "cand_1"));
    await waitFor(() => expect(props.onBeginSession).toHaveBeenCalled());
  });

  it("one question ready while more are written, from a reading that is one section; Enter is its Begin", async () => {
    const f = emptyToday([libraryCard(built(facts({ count: 1, itemIds: ["pi_2"], sections: ["Document"], writing: ["Document"], sectionCount: 1 })))], {
      getTodayQueue: vi.fn(async () => queue([scheduled(1), scheduled(2)]))
    });
    show(causeProps({ aiConnection: ready(), session: SESSION }));
    await waitFor(() => expect(screen.getByTestId("today-cause").textContent).toContain(
      "1 question from what you read in “Symmetric Matrices and Variance” is ready. More are being written."
    ));
    await press({ key: "Enter" });
    await waitFor(() => expect(f.planLearnerPick).toHaveBeenCalledWith("pi_2", "s1", "cand_2"));
  });

  it("ready, and a topic's questions could not be written: still offered with Begin; Try again resumes the stopped part", async () => {
    const f = emptyToday([libraryCard(built(facts({
      count: 2, itemIds: ["pi_1", "pi_4"], sections: ["Conditional probability"], progress: { done: 7, total: 8 },
      failed: [{ label: "Conditional probability: Bayes' rule", resumeId: "batch_sec" }]
    })))], {
      getTodayQueue: vi.fn(async () => queue([scheduled(1), scheduled(4)])),
      resumeIngestBatch: vi.fn(async () => ({ id: "batch_sec", status: "queued" }))
    });
    const props = show(causeProps({ aiConnection: ready() }));
    const cause = await screen.findByTestId("today-cause");
    await waitFor(() => expect(cause.textContent).toContain("2 questions from “Conditional probability”, the part you read. More come as you finish sections."));
    const failed = within(cause).getByTestId("today-cause-failed");
    expect(failed.textContent).toContain(FAILED_TOPIC);
    expect(cause.textContent).not.toContain("Couldn't write the questions");
    // What's sent sits beside the Try again that sends passages, not beside Begin.
    expect(within(failed).getByRole("button", { name: /what's sent/ })).toBeTruthy();
    fireEvent.click(within(failed).getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(f.resumeIngestBatch).toHaveBeenCalledWith("batch_sec"));
    fireEvent.click(within(cause).getByRole("button", { name: "Begin ↵" }));
    await waitFor(() => expect(f.planLearnerPick).toHaveBeenCalledWith("pi_1", "s_new", "cand_1"));
    await waitFor(() => expect(props.onBeginSession).toHaveBeenCalled());
  });

  it("a topic failed while the rest are still written: said, with no Try again until that writing stops (a resume would do nothing then)", async () => {
    const lines = [built(facts({
      count: 3, itemIds: ["pi_1"], sections: ["Conditional probability"], writing: ["Conditional probability"], progress: { done: 4, total: 8 },
      failed: [{ label: "Conditional probability: Bayes' rule", resumeId: "batch_sec" }]
    }))];
    const f = emptyToday([], {
      getSourceLibrary: vi.fn(async () => ({ version: 1, sources: [libraryCard(lines[0])], pending: [] })),
      getTodayQueue: vi.fn(async () => queue([scheduled(1)])),
      resumeIngestBatch: vi.fn(async () => ({ id: "batch_sec", status: "queued" }))
    });
    show(causeProps({ aiConnection: ready() }));
    await waitFor(() => expect(screen.getByTestId("today-cause").textContent).toContain("1 question from “Conditional probability” is ready. More are being written (4 of 8 topics done)."));
    const failed = within(screen.getByTestId("today-cause")).getByTestId("today-cause-failed");
    expect(failed.textContent).toBe(FAILED_TOPIC);
    expect(within(failed).queryByRole("button", { name: "Try again" })).toBeNull();
    // The writing stops with the topic still missing: Try again appears, and resumes that part.
    lines[0] = built(facts({
      count: 3, itemIds: ["pi_1"], sections: ["Conditional probability"], progress: { done: 7, total: 8 },
      failed: [{ label: "Conditional probability: Bayes' rule", resumeId: "batch_sec" }]
    }));
    act(() => notifyQueueChanged());
    const retry = await within(screen.getByTestId("today-cause")).findByRole("button", { name: "Try again" }, { timeout: 2000 });
    fireEvent.click(retry);
    await waitFor(() => expect(f.resumeIngestBatch).toHaveBeenCalledWith("batch_sec"));
  });

  it("several topics or sections could not be written: the same line, no count it cannot know; Try again resumes the first stopped one", async () => {
    const f = emptyToday([libraryCard(built(facts({
      count: 2, itemIds: ["pi_1", "pi_2"], sections: ["Conditional probability", "Independence"],
      failed: [{ label: "Conditional probability: Bayes' rule, Total probability", resumeId: "batch_a" }, { label: "Independence: Pairwise", resumeId: "batch_b" }]
    })))], {
      getTodayQueue: vi.fn(async () => queue([scheduled(1), scheduled(2)])),
      resumeIngestBatch: vi.fn(async () => ({ id: "batch_a", status: "queued" }))
    });
    show(causeProps({ aiConnection: ready() }));
    const cause = await screen.findByTestId("today-cause");
    await waitFor(() => expect(cause.textContent).toContain("2 questions from what you read in “Symmetric Matrices and Variance”. More come as you finish sections."));
    const failed = within(cause).getByTestId("today-cause-failed");
    expect(failed.textContent).toContain(FAILED_TOPIC);
    fireEvent.click(within(failed).getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(f.resumeIngestBatch).toHaveBeenCalledWith("batch_a"));
  });

  it("every topic failed and nothing ready: the stopped section's own line, unchanged", async () => {
    emptyToday([libraryCard(built(facts({ failed: [{ label: "Conditional probability", resumeId: "batch_sec" }], progress: { done: 0, total: 8 } })))]);
    show(causeProps({ aiConnection: ready() }));
    const cause = await screen.findByTestId("today-cause");
    expect(cause.textContent).toContain("Couldn't write the questions from “Conditional probability”. Try again, or keep reading: nothing is lost.");
    expect(cause.textContent).not.toContain(FAILED_TOPIC);
  });

  describe("a new library's first build", () => {
    // The screen is read with the harness's real timers; the build's line arrives, and its wait runs, on fake ones.
    function freezeTimers() {
      const now = Date.now();
      vi.useRealTimers();
      vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "Date"], now });
    }
    async function advance(ms: number) {
      await act(async () => { await vi.advanceTimersByTimeAsync(ms); });
    }
    async function buildArrives(line: SourceStatusLineDto) {
      // Before: the book's card asks for something else; then its build is under way.
      const lines: SourceStatusLineDto[] = [LINE.costs];
      emptyToday([], { getSourceLibrary: vi.fn(async () => ({ version: 1, sources: [libraryCard(lines[0])], pending: [] })) });
      show(causeProps({ aiConnection: ready() }));
      await waitFor(() => expect(screen.getByTestId("today-cause").textContent).toContain("needs a look in your Library"));
      freezeTimers();
      lines[0] = line;
      act(() => notifyQueueChanged());
      // The reread lands a few ticks later; the wait's own clock starts when its line mounts.
      for (let tick = 0; tick < 20 && !screen.queryByTestId("today-cause-wait"); tick += 1) await advance(10);
      expect(screen.getByTestId("today-cause-wait")).toBeTruthy();
      await advance(400);
    }

    it("with no measured time: after five seconds, a quiet second line that this can take several minutes the first time", async () => {
      await buildArrives({ ...LINE.writing, progress: { done: 0, total: 2 } });
      expect(screen.getByTestId("today-cause-wait").textContent).toContain("Getting “Symmetric Matrices and Variance” ready for questions · 0 of 2 steps done");
      expect(screen.queryByTestId("today-cause-wait-later")).toBeNull();
      await advance(4300);
      expect(screen.queryByTestId("today-cause-wait-later")).toBeNull();
      await advance(400);
      expect(screen.getByTestId("today-cause-wait-later").textContent).toBe("The first time, this can take several minutes.");
    });

    it("with a measured time: the usual time on the line, and no second line", async () => {
      await buildArrives({ ...LINE.writing, progress: { done: 1, total: 2 }, minutes: 3.6 });
      expect(screen.getByTestId("today-cause-wait").textContent).toContain("ready for questions · 1 of 2 steps done · usually about 4 min");
      await advance(6000);
      expect(screen.queryByTestId("today-cause-wait-later")).toBeNull();
    });

    it("a line that is not the build's own (the book still being read in, chapters being chosen) claims nothing about a first time", async () => {
      await buildArrives({ text: "Chapters found", tone: "working", action: null, details: null });
      expect(screen.getByTestId("today-cause-wait").textContent).toContain("Getting “Symmetric Matrices and Variance” ready for questions");
      await advance(6000);
      expect(screen.queryByTestId("today-cause-wait-later")).toBeNull();
    });
  });

  it("every new line is in plain words", async () => {
    const cases: Array<{ line: SourceStatusLineDto; list: ScheduledItemDto[] }> = [
      { line: built(facts({ writing: ["Conditional probability"], progress: { done: 2, total: 8 } })), list: [] },
      { line: built(facts({ count: 3, itemIds: ["pi_1"], sections: ["Conditional probability"], writing: ["Conditional probability"], progress: { done: 2, total: 8 } })), list: [scheduled(1)] },
      { line: built(facts({ count: 3, itemIds: ["pi_1"], sections: ["Conditional probability"], failed: [{ label: "Conditional probability: Bayes' rule", resumeId: "b" }] })), list: [scheduled(1)] }
    ];
    for (const { line, list } of cases) {
      emptyToday([libraryCard(line)], { getTodayQueue: vi.fn(async () => queue(list)) });
      show(causeProps({ aiConnection: ready() }));
      const cause = await screen.findByTestId("today-cause");
      await new Promise((resolve) => setTimeout(resolve, 400));
      expect(cause.textContent).not.toBe("");
      expect(findJargon(cause.textContent ?? "")).toEqual([]);
      cleanup();
      clear();
    }
  });
});
