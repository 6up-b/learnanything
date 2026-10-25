// UX Phase 3 (docs/specs/ux_learnloop_v1.md §7.1, §10 3.1-3.3, §11 T4): the
// App with the real Today (TodayPlace) and every other screen a stub.
//
// - The simple shell opens on Today, Start and Today merged; classic keeps
//   StartScreen and TodayScreen as they were.
// - T4, as §11 measures it: "Close LearnLoop. It's tomorrow: open it and do
//   today's learning." Success is the plan started with ↵. Measured here on
//   the next day's launch: Today is the plan in minutes, nothing to decide
//   first (no dialog, no required choice), no count of waiting things and no
//   jargon, and one key (Enter) from launch to the first question; after a
//   break, the same with the welcome-back plan.
// - Implicit sessions (3.2): the first practice action with no session open
//   starts one with the remembered minutes and carries on; no "start a
//   session first" notice. One start for two quick actions. Classic keeps
//   its notice and starts nothing.
// - Threads (3.3): resume ▸ opens the problem's book in the Reader and asks
//   the workbench to resume that problem; open in book ▸ opens the passage.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { clear } from "../api/queryCache";
import { findJargon } from "../copy/denyList";

const stubs = vi.hoisted(() => ({
  config: {} as Record<string, unknown>,
  session: null as Record<string, unknown> | null,
  api: {} as Record<string, (...args: unknown[]) => unknown>,
  reader: [] as Array<Record<string, unknown>>
}));

vi.mock("@tauri-apps/api/event", () => ({ listen: vi.fn(async () => () => undefined) }));
vi.mock("@tauri-apps/plugin-dialog", () => ({ open: vi.fn(async () => null) }));
vi.mock("../components/useSourceFileDrop", () => ({ useSourceFileDrop: () => false, pickSourceFiles: async () => [] }));
vi.mock("../components/InboxStrip", () => ({ InboxStrip: () => null }));

const PROB = { sourceId: "src_prob", title: "Probability" };

vi.mock("../api/client", () => {
  const base: Record<string, unknown> = {
    loadVault: vi.fn(async () => ({
      vault: { root: "/vault", subjects: [], subjectTitles: [], counts: { learningObjects: 4, practiceItems: 6 }, algorithmVersion: "mvp-0.31" },
      health: { ai: { ready: true, settingsReady: true, manualGrading: false, activeProvider: "chatgpt_plan" }, codex: { ready: false } },
      config: stubs.config,
      activeSession: stubs.session,
      streak: { current: 4, activeToday: false, longest: 9 }
    })),
    getSourceLibrary: vi.fn(async () => ({ sources: [{ sourceId: "src_prob", title: "Probability" }], pending: [] }))
  };
  const api = new Proxy(base, {
    get: (target, name: string) => {
      if (name in stubs.api) return stubs.api[name];
      return name in target ? target[name] : () => new Promise(() => undefined);
    }
  });
  return { api };
});

function stub(name: string) {
  return () => <div data-testid={name}>{name}</div>;
}

vi.mock("../screens/ReaderScreen", () => ({
  ReaderScreen: (props: Record<string, unknown>) => {
    stubs.reader.push(props);
    const initial = props.initialSource as { card: { sourceId: string }; spanId: string | null } | null;
    const workbench = props.workbench as { resumeProblem?: { sessionId: string } | null } | undefined;
    return (
      <div data-testid="reader-stub" data-source={initial?.card.sourceId ?? "shelf"} data-span={initial?.spanId ?? ""} data-resume={workbench?.resumeProblem?.sessionId ?? ""}>
        <button
          type="button"
          onClick={() =>
            (props.onCheckMe as (request: unknown) => void)({
              practiceItemId: "pi_check",
              spanId: "sp3",
              card: PROB,
              proposalId: null,
              importId: null
            })
          }
        >
          check me
        </button>
      </div>
    );
  }
}));
vi.mock("../screens/LibraryPlace", () => ({ LibraryPlace: stub("library-stub") }));
vi.mock("../screens/StartScreen", () => ({ StartScreen: stub("start-stub") }));
vi.mock("../screens/TodayScreen", () => ({ TodayScreen: stub("today-stub") }));
vi.mock("../screens/PracticeScreen", () => ({
  PracticeScreen: ({ practiceItemId, session }: { practiceItemId: string; session: { sessionId: string } }) => (
    <div data-testid="practice-stub" data-item={practiceItemId} data-session={session.sessionId}>
      practice
    </div>
  )
}));
vi.mock("../screens/GraphScreen", () => ({ GraphScreen: stub("graph-stub") }));
vi.mock("../screens/IngestScreen", () => ({ IngestScreen: stub("ingest-stub") }));
vi.mock("../screens/ProposalsScreen", () => ({ ProposalsScreen: stub("proposals-stub") }));
vi.mock("../screens/RegistryReviewScreen", () => ({ RegistryReviewScreen: stub("registry-stub") }));
vi.mock("../screens/MaintenanceScreen", () => ({ MaintenanceScreen: stub("maintain-stub") }));
vi.mock("../screens/ReviewScreen", () => ({ ReviewScreen: stub("review-stub") }));
vi.mock("../screens/SettingsScreen", () => ({ SettingsOverlay: stub("settings-stub") }));
vi.mock("../screens/reader/WrapUpOffer", () => ({ WrapUpOffer: () => null }));

import { App } from "./App";

const STARTED = { version: 1, sessionId: "s_new", startedAt: "2026-10-27T18:30:00Z", endedAt: null, energy: null, sleepQuality: null, availableMinutes: 25, notesMdPath: null, checkpoint: null };

function planBody(overrides: Record<string, unknown> = {}) {
  return {
    id: "plan_27",
    localDate: "2026-10-27",
    kind: "normal",
    status: "open",
    stopReason: null,
    parentPlanId: null,
    minutesBudget: 25,
    rememberedMinutes: 25,
    minutesSource: "carried",
    minuteChoices: [10, 15, 25, 40, 60],
    minutesLeft: 25,
    split: { rule: "split_v1", line: "25 min · maintain 21 · repair 4", lanesAllowed: ["maintain", "repair"], requestedMinutes: 0, lanes: [] },
    admission: { admittedCount: 0, exemptRequests: 0, stoppedBy: null, floorApplied: false, reviewLoadPerDay: null, ceilingMinutes: null, override: null },
    blocks: [
      {
        id: "blk_1", ordinal: 1, lane: "maintain", action: "practice", subtype: null, chosenBy: "lane_quota", why: "maintain: 6 reviews past their target",
        whyKind: "computed", fallback: false, estMinutes: 8, status: "current", startedAt: null, endedAt: null, outcome: null, reading: null,
        learningObjectTitles: ["Conditional probability"],
        items: [{ practiceItemId: "pi_1", learningObjectId: "lo_1", learningObjectTitle: "Conditional probability", practiceMode: "short_answer", promptPreview: "", lane: "maintain", estMinutes: 8, state: "planned", origin: "chooser", servedAt: null, doneAt: null }],
        displacedCount: 0
      }
    ],
    currentBlockId: "blk_1",
    projected: [{ ordinal: 2, lane: "repair", estMinutes: 4, itemCount: 1, learningObjectTitles: ["Bayes"], readingTitle: null, why: "repair" }],
    blockCountEstimate: 2,
    firstBlock: null,
    nextStep: null,
    totals: { plannedMinutes: 12, plannedItems: 2, doneItems: 0, skippedItems: 0, displacedItems: 0, readingBlocks: 0, readingBlocksEnded: 0, estMinutesDone: 0, actualMinutes: 0 },
    reentry: null,
    source: null,
    chooser: null,
    ...overrides
  };
}

function plan(body: Record<string, unknown> | null = planBody()) {
  return {
    version: 1,
    enabled: body !== null,
    headlineEnabled: false,
    localDate: "2026-10-27",
    plan: body,
    day: body ? { plans: 1, kinds: ["normal"], complete: false, ...(body.totals as Record<string, number>) } : undefined,
    streak: { current: 4, activeToday: false, longest: 9 }
  };
}

function todayApis(daily: ReturnType<typeof plan> = plan()) {
  const startSession = vi.fn(async () => STARTED);
  const nextPlanItem = vi.fn(async () => ({
    ...daily,
    step: { kind: "item", planId: "plan_27", blockId: "blk_1", practiceItemId: "pi_1", learningObjectId: "lo_1", origin: "chooser", schedulerCandidateId: "cand_1", presentationId: "pres_1", boundary: false }
  }));
  const planLearnerPick = vi.fn(async () => ({ step: { kind: "item", planId: "plan_27", blockId: "blk_pick", practiceItemId: "pi_check", learningObjectId: "lo_c", origin: "learner_pick", schedulerCandidateId: "cand_c", presentationId: "pres_c", boundary: false } }));
  Object.assign(stubs.api, {
    getDailyPlan: vi.fn(async () => daily),
    getStartSummary: vi.fn(async () => ({ version: 1, rememberedMinutes: 15, minutesSource: "last_session", minutesPresets: [10, 15, 25, 40, 60], minuteChoices: [10, 15, 25, 40, 60], streak: { current: 4, activeToday: false, longest: 9 } })),
    getTodayQueue: vi.fn(async () => ({
      version: 1,
      generatedAt: "2026-10-27T18:30:00Z",
      sessionId: null,
      sections: [{ title: "Due", items: [{ schedulerCandidateId: "cand_q1", practiceItemId: "pi_q1", learningObjectId: "lo_q1", learningObjectTitle: "Counting", components: {}, dueStatus: "due", isProbe: false, isFollowup: false, followupKind: null }] }],
      totalItems: 1
    })),
    goalsList: vi.fn(async () => ({ version: 1, goals: [] })),
    getTodayHeadline: vi.fn(async () => ({ version: 1, enabled: false })),
    listQuestionQueue: vi.fn(async () => ({ version: 1, questions: [], openCount: 0 })),
    workbenchOpenProblems: vi.fn(async () => ({ version: 1, problems: [] })),
    getInboxSummary: vi.fn(async () => ({ count: 0, newCount: 0, captures: [], deletePending: [], deletePendingCount: 0, pinnedVault: null, vaultMismatch: false, enabled: true })),
    getReviewCounts: vi.fn(async () => ({ version: 1, pendingProposals: 0, openConflicts: 0 })),
    startSession,
    nextPlanItem,
    planLearnerPick,
    getPracticeItem: vi.fn(async () => ({ prompt: "Q" }))
  });
  return { startSession, nextPlanItem, planLearnerPick };
}

let store: Map<string, string>;

beforeEach(() => {
  stubs.config = {};
  stubs.session = null;
  stubs.api = {};
  stubs.reader = [];
  store = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => {
      store.set(key, value);
    },
    removeItem: (key: string) => {
      store.delete(key);
    },
    clear: () => store.clear()
  });
  Element.prototype.scrollIntoView = () => undefined;
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  vi.stubGlobal("IntersectionObserver", class { observe() {} unobserve() {} disconnect() {} takeRecords() { return []; } });
});
afterEach(() => {
  cleanup();
  clear();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

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

describe("Today is one place (3.1)", () => {
  it("the simple shell opens on Today, the plan; classic keeps Start", async () => {
    todayApis();
    render(<App />);
    expect(await screen.findByTestId("today-place")).toBeTruthy();
    expect(screen.queryByTestId("start-stub")).toBeNull();
    cleanup();
    clear();
    stubs.config = { ui: { shell: "classic" } };
    render(<App />);
    expect(await screen.findByTestId("start-stub")).toBeTruthy();
    expect(screen.queryByTestId("today-place")).toBeNull();
  });

  it("with a session open, Today is still the plan, never the old queue screen", async () => {
    stubs.session = { ...STARTED, sessionId: "s1" };
    todayApis();
    render(<App />);
    await screen.findByRole("navigation", { name: "Places" });
    await press({ key: "1", altKey: true });
    expect(await screen.findByTestId("today-place")).toBeTruthy();
    expect(screen.queryByTestId("today-stub")).toBeNull();
  });
});

describe("T4: it's tomorrow, open LearnLoop and do today's learning (§11)", () => {
  async function tomorrow(daily: ReturnType<typeof plan>) {
    vi.useFakeTimers({ shouldAdvanceTime: true, toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 9, 27, 18, 30));
    const apis = todayApis(daily);
    render(<App />);
    const sentence = await screen.findByTestId("today-sentence");
    return { apis, sentence };
  }

  it("Today is understood without explanation and the plan starts with ↵: one key from launch to the first question", async () => {
    const { apis, sentence } = await tomorrow(plan());
    expect(sentence.textContent).toContain("25 minutes today: 1 short question from earlier days, then a fix for a mix-up.");
    const place = screen.getByTestId("today-place");
    // Nothing to decide first: no dialog, no required choice, no count of waiting things, no jargon.
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(place.textContent).not.toMatch(/due now|probe queue|later today|follow-ups|\bqueue\b|overdue|\bitems?\b|%/i);
    expect(place.textContent).not.toMatch(/\b(maintain|repair|push)\b/);
    expect(findJargon(place.textContent ?? "")).toEqual([]);
    expect(screen.getByText("Tuesday evening")).toBeTruthy();
    expect(screen.getByTestId("today-streak").textContent).toBe("4 days · best 9");
    // The one action: Enter.
    await press({ key: "Enter" });
    const practice = await screen.findByTestId("practice-stub");
    expect(practice.getAttribute("data-item")).toBe("pi_1");
    expect(practice.getAttribute("data-session")).toBe("s_new");
    expect(apis.startSession).toHaveBeenCalledTimes(1);
    expect(apis.startSession).toHaveBeenCalledWith({ availableMinutes: 25 });
    expect(apis.nextPlanItem).toHaveBeenCalledWith({ sessionId: "s_new", serve: true });
    expect(screen.queryByText(/Start a session|Begin today's plan on Start/)).toBeNull();
  });

  it("after a break, the same: a short welcome-back plan, no debt screen, and ↵", async () => {
    const { apis, sentence } = await tomorrow(
      plan(planBody({ kind: "reentry", minutesBudget: 12, reentry: { gapDays: 9, solidCount: 14, slippedCount: 6, slippedNames: ["Bayes"], namedBy: "priority", target: 0.85, planMinutes: 12, planItems: 5 } }))
    );
    expect(sentence.textContent).toContain("Welcome back. A short catch-up today: 12 minutes of the most useful questions. Nothing else is waiting on you.");
    expect(screen.getByTestId("today-place").textContent).not.toMatch(/slipped|Still solid|\b6\b|\b14\b/i);
    await press({ key: "Enter" });
    expect(await screen.findByTestId("practice-stub")).toBeTruthy();
    expect(apis.startSession).toHaveBeenCalledWith({ availableMinutes: 12 });
  });
});

describe("implicit sessions (3.2)", () => {
  it("a question opened with no session starts one with the remembered minutes and opens, with no notice", async () => {
    const { startSession } = todayApis(plan(null));
    render(<App />);
    await screen.findByTestId("today-sentence");
    // The full list's question goes through the shell's openPractice.
    await press({ key: "l" });
    fireEvent.click(await screen.findByRole("button", { name: "Counting" }));
    const practice = await screen.findByTestId("practice-stub");
    expect(practice.getAttribute("data-item")).toBe("pi_q1");
    expect(practice.getAttribute("data-session")).toBe("s_new");
    expect(startSession).toHaveBeenCalledWith({ availableMinutes: 15 });
    expect(screen.queryByText(/Start a session/)).toBeNull();
  });

  it("a Reader check with no session starts one with the plan's minutes and is picked in it", async () => {
    const { startSession, planLearnerPick } = todayApis();
    render(<App />);
    await screen.findByTestId("today-sentence");
    await press({ key: "3", altKey: true });
    fireEvent.click(await screen.findByRole("button", { name: "check me" }));
    await waitFor(() => expect(planLearnerPick).toHaveBeenCalledTimes(1));
    expect(startSession).toHaveBeenCalledWith({ availableMinutes: 25 });
    expect(planLearnerPick.mock.calls[0]).toEqual(["pi_check", "s_new", null, null, null]);
    expect(await screen.findByTestId("practice-stub")).toBeTruthy();
    expect(screen.queryByText(/Start a session/)).toBeNull();
  });

  it("two quick actions start one session", async () => {
    const { startSession, planLearnerPick } = todayApis();
    let release: (value: unknown) => void = () => undefined;
    startSession.mockImplementationOnce(() => new Promise((resolve) => (release = resolve)) as never);
    render(<App />);
    await screen.findByTestId("today-sentence");
    await press({ key: "3", altKey: true });
    const check = await screen.findByRole("button", { name: "check me" });
    fireEvent.click(check);
    fireEvent.click(check);
    await flush();
    await act(async () => release(STARTED));
    await waitFor(() => expect(planLearnerPick).toHaveBeenCalledTimes(2));
    expect(startSession).toHaveBeenCalledTimes(1);
  });

  it("classic keeps its notice and starts nothing", async () => {
    stubs.config = { ui: { shell: "classic" } };
    const { startSession } = todayApis();
    render(<App />);
    await screen.findByTestId("start-stub");
    await press({ key: "9", altKey: true });
    fireEvent.click(await screen.findByRole("button", { name: "check me" }));
    expect(await screen.findByText(/Start a session to take this check on your own/)).toBeTruthy();
    expect(startSession).not.toHaveBeenCalled();
  });
});

describe("threads open where they belong (3.3)", () => {
  it("resume ▸ opens the problem's book at its passage and asks the workbench to resume it", async () => {
    stubs.config = { workbench: { enabled: true } };
    todayApis();
    stubs.api.workbenchOpenProblems = vi.fn(async () => ({
      version: 1,
      problems: [{ sessionId: "wb_1", status: "open", practiceItemId: null, stemMd: "Exercise 5.9", origin: "reader", entry: "work_through", extractionId: "ext_prob", spanIds: ["sp12"], importStatus: "none", sourceVisible: false, stepCount: 3, createdAt: "2026-10-26T00:00:00Z", updatedAt: "2026-10-26T00:00:00Z", unfinished: false, sourceId: "src_prob" }]
    }));
    render(<App />);
    const thread = await screen.findByTestId("today-thread");
    fireEvent.click(within(thread).getByRole("button", { name: "resume ▸" }));
    const reader = await screen.findByTestId("reader-stub");
    expect(reader.getAttribute("data-source")).toBe("src_prob");
    expect(reader.getAttribute("data-span")).toBe("sp12");
    expect(reader.getAttribute("data-resume")).toBe("wb_1");
  });

  it("open in book ▸ opens an open question's passage", async () => {
    todayApis();
    stubs.api.listQuestionQueue = vi.fn(async () => ({
      version: 1,
      questions: [{ id: "q1", context: "reader", questionMd: "Why a convolution?", answerMd: null, answerStatus: "answered", resolution: "open", questionType: null, practiceItemId: null, attemptId: null, noteId: "n1", sessionId: null, savedNoteId: null, createdAt: "2026-10-26T00:00:00Z", promotion: null, promotionRequest: null, promotionTargetIds: [], sourceCitation: { extractionId: "ext_prob", spanId: "sp9", label: "§5.4", sourceId: "src_prob" } }],
      openCount: 1
    }));
    render(<App />);
    const thread = await screen.findByTestId("today-thread");
    fireEvent.click(within(thread).getByRole("button", { name: "open in book ▸" }));
    const reader = await screen.findByTestId("reader-stub");
    expect(reader.getAttribute("data-source")).toBe("src_prob");
    expect(reader.getAttribute("data-span")).toBe("sp9");
  });
});
