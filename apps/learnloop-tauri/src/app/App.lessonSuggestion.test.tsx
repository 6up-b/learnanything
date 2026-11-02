// Teacher TE1b, Codex review F1: Today's lesson suggestion card in the DEFAULT shell (`ui.shell = "simple"`,
// where Today is TodayPlace), mounted through the App: Start opens the lesson with the suggestion's ids, "Not
// now" answers once and opens nothing, a Start whose lesson never opened is offered again (review F2), and
// with the sidecar's `teacher.suggestions` key absent Today never asks for a card.
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { clear } from "../api/queryCache";

const stubs = vi.hoisted(() => ({
  config: {} as Record<string, unknown>,
  api: {} as Record<string, (...args: unknown[]) => unknown>,
  lessons: [] as Array<Record<string, unknown>>
}));

vi.mock("@tauri-apps/api/event", () => ({ listen: vi.fn(async () => () => undefined) }));
vi.mock("@tauri-apps/plugin-dialog", () => ({ open: vi.fn(async () => null) }));
vi.mock("../components/useSourceFileDrop", () => ({ useSourceFileDrop: () => false, pickSourceFiles: async () => [] }));
vi.mock("../components/InboxStrip", () => ({ InboxStrip: () => null }));

vi.mock("../api/client", () => {
  const base: Record<string, unknown> = {
    loadVault: vi.fn(async () => ({
      vault: { root: "/vault", subjects: [], subjectTitles: [], counts: { learningObjects: 4, practiceItems: 6 }, algorithmVersion: "mvp-0.43" },
      health: { ai: { ready: true, settingsReady: true, manualGrading: false, activeProvider: "chatgpt_plan" }, codex: { ready: false } },
      config: stubs.config,
      activeSession: null,
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

vi.mock("../screens/LessonScreen", () => ({
  LessonScreen: (props: { entry: Record<string, unknown> }) => {
    stubs.lessons.push(props.entry);
    return <div data-testid="lesson-stub" data-entry={JSON.stringify(props.entry)}>lesson</div>;
  }
}));
vi.mock("../screens/ReaderScreen", () => ({ ReaderScreen: stub("reader-stub") }));
vi.mock("../screens/LibraryPlace", () => ({ LibraryPlace: stub("library-stub") }));
vi.mock("../screens/StartScreen", () => ({ StartScreen: stub("start-stub") }));
vi.mock("../screens/TodayScreen", () => ({ TodayScreen: stub("today-stub") }));
vi.mock("../screens/PracticeScreen", () => ({ PracticeScreen: stub("practice-stub") }));
vi.mock("../screens/GraphScreen", () => ({ GraphScreen: stub("graph-stub") }));
vi.mock("../screens/IngestScreen", () => ({ IngestScreen: stub("ingest-stub") }));
vi.mock("../screens/ProposalsScreen", () => ({ ProposalsScreen: stub("proposals-stub") }));
vi.mock("../screens/RegistryReviewScreen", () => ({ RegistryReviewScreen: stub("registry-stub") }));
vi.mock("../screens/MaintenanceScreen", () => ({ MaintenanceScreen: stub("maintain-stub") }));
vi.mock("../screens/ReviewScreen", () => ({ ReviewScreen: stub("review-stub") }));
vi.mock("../screens/SettingsScreen", () => ({ SettingsOverlay: stub("settings-stub") }));
vi.mock("../screens/reader/WrapUpOffer", () => ({ WrapUpOffer: () => null }));

import { App } from "./App";

const PLAN = {
  version: 1, enabled: true, headlineEnabled: false, localDate: "2026-11-02",
  plan: {
    id: "plan_1", localDate: "2026-11-02", kind: "normal", status: "open", stopReason: null, parentPlanId: null,
    minutesBudget: 25, rememberedMinutes: 25, minutesSource: "carried", minuteChoices: [10, 15, 25], minutesLeft: 25,
    split: { rule: "split_v1", line: "", lanesAllowed: ["maintain"], requestedMinutes: 0, lanes: [] },
    admission: { admittedCount: 0, exemptRequests: 0, stoppedBy: null, floorApplied: false, reviewLoadPerDay: null, ceilingMinutes: null, override: null },
    blocks: [], currentBlockId: null, projected: [], blockCountEstimate: 0, firstBlock: null, nextStep: null,
    totals: { plannedMinutes: 0, plannedItems: 0, doneItems: 0, skippedItems: 0, displacedItems: 0, readingBlocks: 0, readingBlocksEnded: 0, estMinutesDone: 0, actualMinutes: 0 },
    reentry: null, source: null, chooser: null
  },
  streak: { current: 4, activeToday: false, longest: 9 }
};

const ENTRY = (ref: string, title: string, lo: string) => ({
  ref, title, learningObjectIds: [lo], reason: "new_goal", why: "It's on your goal and you haven't started it yet."
});

const CARD = {
  decisionId: "rd_1", day: "2026-11-02", minutes: 15, whyLabel: "Suggested by LearnLoop's planner",
  suggestion: ENTRY("lesson:lo_svd", "The SVD", "lo_svd"),
  alternatives: [ENTRY("lesson:lo_eigen", "Eigenvalues", "lo_eigen")],
  pendingLesson: null
};

function apis(card: Record<string, unknown> | null = CARD) {
  const lessonSuggestion = vi.fn(async () => ({ version: 1, suggestion: card }));
  const lessonSuggestionRespond = vi.fn(async (input: { decisionId: string; response: string; candidateRef?: string }) => ({
    version: 1, decisionId: input.decisionId, response: input.response,
    candidateRef: input.candidateRef ?? "lesson:lo_svd",
    lesson: input.response === "declined" ? null
      : input.response === "chose_alternative"
        ? { lessonId: "les_alt", decisionId: input.decisionId, learningObjectIds: ["lo_eigen"], title: "Eigenvalues" }
        : { lessonId: "les_new", decisionId: input.decisionId, learningObjectIds: ["lo_svd"], title: "The SVD" }
  }));
  Object.assign(stubs.api, {
    getDailyPlan: vi.fn(async () => PLAN),
    goalsList: vi.fn(async () => ({ version: 1, goals: [] })),
    getTodayHeadline: vi.fn(async () => ({ version: 1, enabled: false })),
    listQuestionQueue: vi.fn(async () => ({ version: 1, questions: [], openCount: 0 })),
    workbenchOpenProblems: vi.fn(async () => ({ version: 1, problems: [] })),
    getReviewCounts: vi.fn(async () => ({ version: 1, pendingProposals: 0, openConflicts: 0 })),
    lessonSuggestion,
    lessonSuggestionRespond
  });
  return { lessonSuggestion, lessonSuggestionRespond };
}

async function flush() {
  await act(async () => {
    for (let i = 0; i < 10; i += 1) await Promise.resolve();
  });
}

let store: Map<string, string>;

beforeEach(() => {
  stubs.config = { teacher: { lessons: true, suggestions: true } };
  stubs.api = {};
  stubs.lessons = [];
  store = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => { store.set(key, value); },
    removeItem: (key: string) => { store.delete(key); },
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
});

describe("the lesson suggestion card in the default shell (TE1b review F1)", () => {
  it("Today (TodayPlace) shows the card, and Start opens the lesson with the suggestion's ids", async () => {
    const { lessonSuggestion, lessonSuggestionRespond } = apis();
    render(<App />);
    const place = await screen.findByTestId("today-place");
    const card = await within(place).findByTestId("lesson-suggestion-card");
    expect(screen.queryByTestId("today-stub")).toBeNull();
    expect(lessonSuggestion).toHaveBeenCalled();
    expect(card.textContent).toContain("Learn The SVD now? (about 15 min)");
    expect(screen.queryByRole("dialog")).toBeNull();
    await act(async () => { fireEvent.click(within(card).getByText("Start")); });
    await flush();
    expect(lessonSuggestionRespond).toHaveBeenCalledWith(expect.objectContaining({ decisionId: "rd_1", response: "accepted" }));
    const lesson = await screen.findByTestId("lesson-stub");
    expect(JSON.parse(lesson.dataset.entry ?? "{}")).toEqual({
      kind: "open", entry: "learning_object", learningObjectIds: ["lo_svd"], title: "The SVD",
      suggestion: { decisionId: "rd_1", lessonId: "les_new" }
    });
    expect(screen.queryByTestId("lesson-suggestion-card")).toBeNull();
  });

  it("an alternative opens its own lesson", async () => {
    const { lessonSuggestionRespond } = apis();
    render(<App />);
    const card = await screen.findByTestId("lesson-suggestion-card");
    await act(async () => { fireEvent.click(within(card).getByText("Or: Eigenvalues")); });
    await flush();
    expect(lessonSuggestionRespond).toHaveBeenCalledWith(expect.objectContaining({
      decisionId: "rd_1", response: "chose_alternative", candidateRef: "lesson:lo_eigen" }));
    const lesson = await screen.findByTestId("lesson-stub");
    expect(JSON.parse(lesson.dataset.entry ?? "{}").suggestion).toEqual({ decisionId: "rd_1", lessonId: "les_alt" });
  });

  it("Not now answers once, hides the card and opens nothing", async () => {
    const { lessonSuggestionRespond } = apis();
    render(<App />);
    const card = await screen.findByTestId("lesson-suggestion-card");
    await act(async () => { fireEvent.click(within(card).getByText("Not now")); });
    await flush();
    expect(lessonSuggestionRespond).toHaveBeenCalledTimes(1);
    expect(lessonSuggestionRespond).toHaveBeenCalledWith(expect.objectContaining({ decisionId: "rd_1", response: "declined" }));
    expect(screen.queryByTestId("lesson-suggestion-card")).toBeNull();
    expect(screen.queryByTestId("lesson-stub")).toBeNull();
    expect(screen.getByTestId("today-place")).toBeTruthy();
  });

  it("a Start whose lesson never opened is offered again after a restart, under its recorded id (review F2)", async () => {
    const { lessonSuggestionRespond } = apis({
      ...CARD, alternatives: [],
      pendingLesson: { lessonId: "les_new", decisionId: "rd_1", learningObjectIds: ["lo_svd"], title: "The SVD" }
    });
    render(<App />);
    const card = await screen.findByTestId("lesson-suggestion-card");
    expect(card.textContent).toContain("Your lesson on The SVD hasn't opened yet.");
    await act(async () => { fireEvent.click(within(card).getByText("Open the lesson")); });
    const lesson = await screen.findByTestId("lesson-stub");
    expect(JSON.parse(lesson.dataset.entry ?? "{}").suggestion).toEqual({ decisionId: "rd_1", lessonId: "les_new" });
    expect(lessonSuggestionRespond).not.toHaveBeenCalled();
  });

  it("without the sidecar's teacher.suggestions key Today never asks for the card", async () => {
    stubs.config = { teacher: { lessons: true } };
    const { lessonSuggestion } = apis();
    render(<App />);
    await screen.findByTestId("today-place");
    await flush();
    expect(lessonSuggestion).not.toHaveBeenCalled();
    expect(screen.queryByTestId("lesson-suggestion-card")).toBeNull();
  });
});
