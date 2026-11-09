// Instruct hand-off IH1 (spec_instruct_handoff_v1 §4): feedback's Next resolving to a `lesson_offer` step opens the
// offer page (it no longer falls through to Today); Start opens the lesson; Not now goes on to the plan's next step.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { clear, invalidate } from "../api/queryCache";
import { TAG } from "../api/queryTags";

const stubs = vi.hoisted(() => ({
  api: {} as Record<string, (...args: unknown[]) => unknown>,
  lessons: [] as Array<Record<string, unknown>>,
  nextStep: null as unknown
}));

vi.mock("@tauri-apps/api/event", () => ({ listen: vi.fn(async () => () => undefined) }));
vi.mock("@tauri-apps/plugin-dialog", () => ({ open: vi.fn(async () => null) }));
vi.mock("../components/useSourceFileDrop", () => ({ useSourceFileDrop: () => false, pickSourceFiles: async () => [] }));
vi.mock("../components/InboxStrip", () => ({ InboxStrip: () => null }));

vi.mock("../api/client", () => {
  const base: Record<string, unknown> = {
    loadVault: vi.fn(async () => ({
      vault: { root: "/vault", subjects: [], subjectTitles: [], counts: { learningObjects: 4, practiceItems: 6 }, algorithmVersion: "mvp-0.54" },
      health: { ai: { ready: true, settingsReady: true, manualGrading: false, activeProvider: "chatgpt_plan" }, codex: { ready: false } },
      config: { teacher: { lessons: true, suggestions: true } },
      activeSession: { version: 1, sessionId: "s1", startedAt: "2026-11-08T17:30:00Z", endedAt: null, energy: null,
                       sleepQuality: null, availableMinutes: 25, notesMdPath: null, checkpoint: null },
      streak: { current: 4, activeToday: false, longest: 9 }
    })),
    getSourceLibrary: vi.fn(async () => ({ sources: [], pending: [] }))
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

const OFFER = {
  decisionId: "dec1", blockId: "blk1", minutes: 12, whyLabel: "Suggested by LearnLoop's planner", answered: null,
  suggestion: { ref: "lesson:lo_relu", title: "ReLU", learningObjectIds: ["lo_relu"], reason: "cold_failing", why: "Two misses." },
  alternatives: []
};
const OFFER_STEP = { kind: "lesson_offer", planId: "p1", blockId: "blk1", blockOrdinal: 2, offer: OFFER, estMinutes: 12,
                     boundary: true, why: "", whyKind: "computed" };
const ITEM_STEP = { kind: "item", planId: "p1", blockId: "b3", blockOrdinal: 3, practiceItemId: "pi_9", learningObjectId: "lo",
                    learningObjectTitle: "Next topic", origin: "chooser", schedulerCandidateId: null, boundary: false };

vi.mock("../screens/LessonScreen", () => ({
  LessonScreen: (props: { entry: Record<string, unknown> }) => {
    stubs.lessons.push(props.entry);
    return <div data-testid="lesson-stub">lesson</div>;
  }
}));
vi.mock("../screens/today/TodayPlace", () => ({
  TodayPlace: (props: { onOpenPractice: (id: string) => void }) => (
    <div data-testid="today-place"><button onClick={() => props.onOpenPractice("pi_1")}>open item</button></div>
  )
}));
vi.mock("../screens/PracticeScreen", () => ({
  PracticeScreen: (props: { onFeedback: (id: string) => void; practiceItemId: string; planPresentationId?: string | null }) => (
    <div data-testid={`practice-${props.practiceItemId}`} data-presentation={props.planPresentationId ?? ""}>
      <button onClick={() => props.onFeedback("att_1")}>submit</button>
    </div>
  )
}));
vi.mock("../screens/FeedbackScreen", () => ({
  FeedbackScreen: (props: { onPlanStep?: (step: unknown) => void }) => (
    <div data-testid="feedback-stub"><button onClick={() => props.onPlanStep?.(stubs.nextStep)}>Next</button></div>
  )
}));
vi.mock("../screens/ReaderScreen", () => ({ ReaderScreen: stub("reader-stub") }));
vi.mock("../screens/LibraryPlace", () => ({ LibraryPlace: stub("library-stub") }));
vi.mock("../screens/StartScreen", () => ({ StartScreen: stub("start-stub") }));
vi.mock("../screens/TodayScreen", () => ({ TodayScreen: stub("today-stub") }));
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
  version: 1, enabled: true, headlineEnabled: false, localDate: "2026-11-08",
  plan: {
    id: "plan_1", localDate: "2026-11-08", kind: "normal", status: "open", stopReason: null, parentPlanId: null,
    minutesBudget: 25, rememberedMinutes: 25, minutesSource: "carried", minuteChoices: [10, 15, 25], minutesLeft: 25,
    split: { rule: "split_v1", line: "", lanesAllowed: ["maintain"], requestedMinutes: 0, lanes: [] },
    admission: { admittedCount: 0, exemptRequests: 0, stoppedBy: null, floorApplied: false, reviewLoadPerDay: null, ceilingMinutes: null, override: null },
    blocks: [], currentBlockId: null, projected: [], blockCountEstimate: 0, firstBlock: null, nextStep: null,
    totals: { plannedMinutes: 0, plannedItems: 0, doneItems: 0, skippedItems: 0, displacedItems: 0, readingBlocks: 0, readingBlocksEnded: 0, estMinutesDone: 0, actualMinutes: 0 },
    reentry: null, source: null, chooser: null
  },
  streak: { current: 4, activeToday: false, longest: 9 }
};

stubs.nextStep = OFFER_STEP;
let store: Map<string, string>;

function apis() {
  const lessonSuggestionRespond = vi.fn(async (input: { decisionId: string; response: string }) => ({
    version: 1, decisionId: input.decisionId, response: input.response, candidateRef: "lesson:lo_relu",
    lesson: input.response === "declined" ? null
      : { lessonId: "les_1", decisionId: input.decisionId, learningObjectIds: ["lo_relu"], title: "ReLU" }
  }));
  const nextPlanItem = vi.fn(async (input: { serve?: boolean }) => ({
    ...PLAN, enabled: true, step: input.serve ? { ...ITEM_STEP, presentationId: "pp_9" } : ITEM_STEP
  }));
  const recordOfferShown = vi.fn(async () => ({ version: 1, recorded: true }));
  // IH3: the plan says the quiet link may show; the options and the served choice come from the sidecar.
  const planSomethingElseOptions = vi.fn(async () => ({
    version: 1, enabled: true, drawn: true, decisionId: "dec1", device: "desktop",
    options: [
      { kind: "question", ref: "cand_q", label: "Another question", minutes: 6, propensity: null, plansPick: false, servable: true },
      { kind: "lesson", ref: "lesson_offer:lo_relu", label: "Learn ReLU", minutes: 12, propensity: null, plansPick: true, servable: true }
    ]
  }));
  const planSomethingElse = vi.fn(async (input: { kind: string }) => input.kind === "lesson"
    ? { ...PLAN, step: null, preference: { id: "k", outcome: "lesson", kind: "lesson", ref: "lesson_offer:lo_relu", servedDecisionId: "d1",
                                           lesson: { learningObjectIds: ["lo_relu"], title: "ReLU" }, replayed: false } }
    : { ...PLAN, step: ITEM_STEP, preference: { id: "k", outcome: "served", kind: "question", ref: "cand_q", servedDecisionId: "d1",
                                                lesson: null, replayed: false } });
  Object.assign(stubs.api, {
    getDailyPlan: vi.fn(async () => ({ ...PLAN, somethingElse: true })),
    planSomethingElseOptions, planSomethingElse,
    goalsList: vi.fn(async () => ({ version: 1, goals: [] })),
    getTodayHeadline: vi.fn(async () => ({ version: 1, enabled: false })),
    listQuestionQueue: vi.fn(async () => ({ version: 1, questions: [], openCount: 0 })),
    workbenchOpenProblems: vi.fn(async () => ({ version: 1, problems: [] })),
    getReviewCounts: vi.fn(async () => ({ version: 1, pendingProposals: 0, openConflicts: 0 })),
    lessonSuggestion: vi.fn(async () => ({ version: 1, suggestion: null })),
    lessonSuggestionRespond, nextPlanItem, recordOfferShown
  });
  return { lessonSuggestionRespond, nextPlanItem, recordOfferShown, planSomethingElse, planSomethingElseOptions };
}

async function flush() {
  await act(async () => {
    for (let i = 0; i < 10; i += 1) await Promise.resolve();
  });
}

async function toFeedbackNext() {
  render(<App />);
  const openItem = await screen.findByText("open item");
  await act(async () => { fireEvent.click(openItem); });
  const submit = await screen.findByText("submit");
  await act(async () => { fireEvent.click(submit); });
  const next = await screen.findByText("Next");
  await act(async () => { fireEvent.click(next); });
  await flush();
}

beforeEach(() => {
  stubs.api = {};
  stubs.lessons = [];
  stubs.nextStep = OFFER_STEP;
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

it("feedback's Next on a lesson_offer step opens the offer page, not Today, and records that it was shown", async () => {
  const { recordOfferShown } = apis();
  await toFeedbackNext();
  expect(screen.getByTestId("lesson-offer-sentence").textContent)
    .toBe("This looks like something to learn. Start a 12 minute lesson on ReLU?");
  expect(screen.queryByTestId("today-place")).toBeNull();
  expect(recordOfferShown).toHaveBeenCalledTimes(1);
  expect(recordOfferShown).toHaveBeenCalledWith({ blockId: "blk1", surface: "offer_page", sessionId: "s1" });
});

it("Start opens the lesson at once and never before the tap", async () => {
  const { lessonSuggestionRespond } = apis();
  await toFeedbackNext();
  expect(lessonSuggestionRespond).not.toHaveBeenCalled();
  expect(screen.queryByTestId("lesson-stub")).toBeNull();
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Start" })); });
  await flush();
  expect(lessonSuggestionRespond).toHaveBeenCalledWith(expect.objectContaining({ decisionId: "dec1", response: "accepted" }));
  expect(await screen.findByTestId("lesson-stub")).toBeTruthy();
  expect(screen.queryByTestId("lesson-offer-page")).toBeNull();
});

it("Not now moves on to the plan's next step: its item is served, then opens, with no lesson", async () => {
  // Review M1: inside the block the read's step names an item nobody served. It must be served as feedback's Next serves it,
  // or the attempt binds to no presentation and the serve's eligibility decision is skipped.
  const { lessonSuggestionRespond, nextPlanItem } = apis();
  await toFeedbackNext();
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Not now" })); });
  await flush();
  expect(lessonSuggestionRespond).toHaveBeenCalledWith(expect.objectContaining({ response: "declined" }));
  expect(nextPlanItem).toHaveBeenCalledWith({ sessionId: "s1", serve: false });
  expect(nextPlanItem).toHaveBeenCalledWith({ sessionId: "s1", serve: true });
  const practice = await screen.findByTestId("practice-pi_9");
  expect(practice.getAttribute("data-presentation")).toBe("pp_9");
  expect(screen.queryByTestId("lesson-stub")).toBeNull();
  expect(screen.queryByTestId("lesson-offer-page")).toBeNull();
});

it("Not now with a new block next stays a read: the block line is shown, nothing is served", async () => {
  const { nextPlanItem } = apis();
  nextPlanItem.mockImplementation(async () => ({ ...PLAN, enabled: true, step: { ...ITEM_STEP, boundary: true } }));
  await toFeedbackNext();
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Not now" })); });
  await flush();
  expect(nextPlanItem).not.toHaveBeenCalledWith({ sessionId: "s1", serve: true });
  expect(screen.queryByTestId("lesson-offer-page")).toBeNull();
  expect(screen.getByTestId("today-place")).toBeTruthy();
});

it("Not now under an open problem's hold stays a read: Today says so, nothing is served, no decision is drawn", async () => {
  // Second review R2-m1: "Not now" answers the offer and asks for nothing else. The boundary waits for that problem's answer.
  const { nextPlanItem } = apis();
  nextPlanItem.mockImplementation(async () => ({
    ...PLAN, enabled: true,
    step: { kind: "question_in_progress", planId: "p1", workbenchSessionId: "wb", practiceItemId: "pi_8", learningObjectTitle: "ReLU" }
  }));
  await toFeedbackNext();
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Not now" })); });
  await flush();
  expect(nextPlanItem).not.toHaveBeenCalledWith({ sessionId: "s1", serve: true });
  expect(screen.queryByTestId("lesson-offer-page")).toBeNull();
  expect(screen.getByTestId("today-place")).toBeTruthy();
});

// Review M2: a read crossed the boundary while the page was up, so a newer decision superseded the offer.
it.each([["Start"], ["Not now"]])("%s on an offer already gone closes the page and re-reads the plan, with no error", async (button) => {
  const { lessonSuggestionRespond } = apis();
  lessonSuggestionRespond.mockImplementation(async () => {
    throw { code: "not_found", message: "That suggestion is no longer in your plan.", retryable: false };
  });
  await toFeedbackNext();
  const getDailyPlan = stubs.api.getDailyPlan as ReturnType<typeof vi.fn>;
  const reads = getDailyPlan.mock.calls.length;
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: button })); });
  await flush();
  expect(screen.queryByTestId("lesson-offer-page")).toBeNull();
  expect(screen.getByTestId("today-place")).toBeTruthy();
  expect(getDailyPlan.mock.calls.length).toBeGreaterThan(reads);
  expect(screen.queryByText("That suggestion is no longer in your plan.")).toBeNull();
});

it("a plan read that shows another block closes the page", async () => {
  apis();
  await toFeedbackNext();
  expect(screen.getByTestId("lesson-offer-page")).toBeTruthy();
  (stubs.api.getDailyPlan as ReturnType<typeof vi.fn>).mockImplementation(async () => ({
    ...PLAN, somethingElse: true, plan: { ...PLAN.plan, currentBlockId: "blk_probe" }
  }));
  await act(async () => { invalidate({ tags: [TAG.queue] }); });
  await flush();
  expect(screen.queryByTestId("lesson-offer-page")).toBeNull();
  expect(screen.getByTestId("today-place")).toBeTruthy();
});

it("a plan read still on the offer's block leaves the page up", async () => {
  apis();
  await toFeedbackNext();
  (stubs.api.getDailyPlan as ReturnType<typeof vi.fn>).mockImplementation(async () => ({
    ...PLAN, somethingElse: true, plan: { ...PLAN.plan, currentBlockId: "blk1" }
  }));
  await act(async () => { invalidate({ tags: [TAG.queue] }); });
  await flush();
  expect(screen.getByTestId("lesson-offer-page")).toBeTruthy();
});

it("a step that is not a lesson offer still routes as before (no offer page, no offer_shown)", async () => {
  const { recordOfferShown } = apis();
  stubs.nextStep = ITEM_STEP;
  await toFeedbackNext();
  expect(screen.queryByTestId("lesson-offer-page")).toBeNull();
  expect(screen.getByTestId("practice-pi_9")).toBeTruthy();
  expect(recordOfferShown).not.toHaveBeenCalled();
});

it("IH3: 'Something else would help' sits under the offer's actions; a served choice closes the page and opens its step", async () => {
  const { planSomethingElse, lessonSuggestionRespond } = apis();
  await toFeedbackNext();
  const slot = screen.getByTestId("lesson-offer-something-else-slot");
  const link = await screen.findByTestId("something-else-link");
  expect(slot.contains(link)).toBe(true);
  await act(async () => { fireEvent.click(link); });
  // the page is the plan's own pick already, so "learn this" isn't offered on it
  expect(screen.queryByTestId("something-else-option-lesson")).toBeNull();
  await act(async () => { fireEvent.click(screen.getByTestId("something-else-option-question")); });
  await flush();
  expect(planSomethingElse).toHaveBeenCalledWith(expect.objectContaining({ kind: "question", surface: "offer_page", sessionId: "s1" }));
  expect(await screen.findByTestId("practice-pi_9")).toBeTruthy();
  expect(screen.queryByTestId("lesson-offer-page")).toBeNull();
  // the offer itself was neither started nor answered by the learner: the sidecar ended it
  expect(lessonSuggestionRespond).not.toHaveBeenCalled();
});
