// Broken controls, second round (UX journey audit part 2), the shell's part, through the App with its screens
// stubbed: a lesson closed with Close says where it went and Today reads its open lessons again (UX-14); a quick
// check with nothing to ask says so where it was asked and opens no empty check (UX-18); Begin that lands on a
// lesson offer opens the offer's page (UX-21); the place tabs leave a check screen (UX-27).
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { clear } from "../api/queryCache";
import { findJargon } from "../copy/denyList";

const stubs = vi.hoisted(() => ({
  api: {} as Record<string, (...args: unknown[]) => unknown>,
  lessons: [] as Array<Record<string, unknown>>,
  todayProps: null as Record<string, unknown> | null
}));

vi.mock("@tauri-apps/api/event", () => ({ listen: vi.fn(async () => () => undefined) }));
vi.mock("@tauri-apps/plugin-dialog", () => ({ open: vi.fn(async () => null) }));
vi.mock("../components/useSourceFileDrop", () => ({ useSourceFileDrop: () => false, pickSourceFiles: async () => [] }));
vi.mock("../components/InboxStrip", () => ({ InboxStrip: () => null }));

const SESSION = { version: 1, sessionId: "s1", startedAt: "2026-11-19T17:30:00Z", endedAt: null, energy: null,
                  sleepQuality: null, availableMinutes: 25, notesMdPath: null, checkpoint: null };

vi.mock("../api/client", () => {
  const base: Record<string, unknown> = {
    loadVault: vi.fn(async () => ({
      vault: { root: "/vault", subjects: [], subjectTitles: [], counts: { learningObjects: 4, practiceItems: 6 }, algorithmVersion: "mvp-0.60" },
      health: { ai: { ready: true, settingsReady: true, manualGrading: false, activeProvider: "chatgpt_plan" }, codex: { ready: false } },
      config: { teacher: { lessons: true } },
      activeSession: SESSION,
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
  decisionId: "dec1", blockId: "blk1", minutes: 15, whyLabel: "Suggested by LearnLoop's planner", answered: null,
  suggestion: { ref: "lesson:lo_eig", title: "Eigenvalues", learningObjectIds: ["lo_eig"], reason: "cold_failing", why: "Two misses." },
  alternatives: []
};
const OFFER_STEP = { kind: "lesson_offer", planId: "p1", blockId: "blk1", blockOrdinal: 1, offer: OFFER, estMinutes: 15,
                     boundary: true, why: "", whyKind: "computed" };

vi.mock("../screens/LessonScreen", () => ({
  LessonScreen: (props: { entry: Record<string, unknown>; onClose: (kept?: boolean) => void; onQuickCheck?: (ids: string[]) => void }) => {
    stubs.lessons.push(props.entry);
    return (
      <div data-testid="lesson-stub">
        <button onClick={() => props.onClose(true)}>close kept</button>
        <button onClick={() => props.onClose(false)}>close ended</button>
        <button onClick={() => props.onQuickCheck?.(["lo_cov"])}>check first</button>
      </div>
    );
  }
}));
vi.mock("../screens/today/TodayPlace", () => ({
  TodayPlace: (props: Record<string, unknown>) => {
    stubs.todayProps = props;
    const onStartLesson = props.onStartLesson as ((entry: unknown) => void) | undefined;
    const onLessonOffer = props.onLessonOffer as ((step: unknown) => void) | undefined;
    const onBeginSession = props.onBeginSession as (session: unknown, step: unknown) => void;
    const onOpenPractice = props.onOpenPractice as (id: string) => void;
    return (
      <div data-testid="today-place" data-lesson-open={String(props.lessonOpen)}>
        <button onClick={() => onStartLesson?.({ kind: "resume", lessonId: "les_dot" })}>open lesson</button>
        <button onClick={() => onLessonOffer?.(OFFER_STEP)}>begin to offer</button>
        <button onClick={() => onBeginSession({ ...SESSION, sessionId: "s_new" }, OFFER_STEP)}>begin new session to offer</button>
        <button onClick={() => onOpenPractice("pi_1")}>open item</button>
      </div>
    );
  }
}));
vi.mock("../screens/CalibrationScreen", () => ({ CalibrationScreen: stub("calibration-stub") }));
vi.mock("../screens/PracticeScreen", () => ({
  PracticeScreen: (props: { practiceItemId: string }) => <div data-testid={`practice-${props.practiceItemId}`}>question</div>
}));
vi.mock("../screens/FeedbackScreen", () => ({ FeedbackScreen: stub("feedback-stub") }));
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

function quickCheckProgress(quickCheck: Record<string, unknown>, status = "completed") {
  return {
    version: 1, calibrationSessionId: "cal1", sessionId: "s1", goalId: null, status,
    timeBudgetMinutes: 8, elapsedMinutes: 0, remainingMinutes: 8, blocksCompleted: 0, blocksPlanned: 0, episodes: [],
    nextTarget: status === "active"
      ? { episodeId: null, learningObjectId: "lo_cov", practiceItemId: "pi_cov", selectionObjective: "conditional_gain", entropy: null }
      : null,
    quickCheck
  };
}

const NOTHING_ASKED = {
  learningObjectIds: ["lo_cov"], k: 4, answered: 0, remaining: 4, finished: true,
  results: [{ learningObjectId: "lo_cov", learningObjectTitle: "Covariance matrices", verdict: "undecided", assumptionId: null, answers: [] }]
};

function apis(extra: Record<string, (...args: unknown[]) => unknown> = {}) {
  Object.assign(stubs.api, {
    getDailyPlan: vi.fn(async () => ({ version: 1, enabled: true, plan: null })),
    goalsList: vi.fn(async () => ({ version: 1, goals: [] })),
    getReviewCounts: vi.fn(async () => ({ version: 1, pendingProposals: 0, openConflicts: 0 })),
    recordOfferShown: vi.fn(async () => ({ version: 1, recorded: true })),
    ...extra
  });
}

async function flush() {
  await act(async () => {
    for (let i = 0; i < 10; i += 1) await Promise.resolve();
  });
}

async function click(text: string) {
  const target = await screen.findByText(text);
  await act(async () => { fireEvent.click(target); });
  await flush();
}

let store: Map<string, string>;

beforeEach(() => {
  stubs.api = {};
  stubs.lessons = [];
  stubs.todayProps = null;
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

it("UX-14: a lesson closed while still open says it is kept and where; Today is told the lesson closed", async () => {
  apis();
  render(<App />);
  const today = await screen.findByTestId("today-place");
  expect(today.dataset.lessonOpen).toBe("false");
  await click("open lesson");
  expect(screen.getByTestId("lesson-stub")).toBeTruthy();
  expect(screen.getByTestId("today-place").dataset.lessonOpen).toBe("true");
  await click("close kept");
  expect(screen.queryByTestId("lesson-stub")).toBeNull();
  const notice = await screen.findByText("Your lesson is kept. It's on Today when you want it.");
  expect(findJargon(notice.textContent ?? "")).toEqual([]);
  expect(screen.getByTestId("today-place").dataset.lessonOpen).toBe("false");
});

it("UX-14: closing a lesson that has ended says nothing", async () => {
  apis();
  render(<App />);
  await click("open lesson");
  await click("close ended");
  expect(screen.queryByTestId("lesson-stub")).toBeNull();
  expect(screen.queryByText(/Your lesson is kept/)).toBeNull();
});

it("UX-18: a quick check with nothing to ask says so where it was asked, opens no empty check, and leaves the lesson open", async () => {
  const startQuickCheck = vi.fn(async () => quickCheckProgress(NOTHING_ASKED));
  apis({ startQuickCheck });
  render(<App />);
  await click("open lesson");
  await click("check first");
  expect(startQuickCheck).toHaveBeenCalledWith(expect.objectContaining({ sessionId: "s1", learningObjectIds: ["lo_cov"] }));
  expect(screen.queryByTestId("calibration-stub")).toBeNull();
  expect(screen.getByTestId("lesson-stub")).toBeTruthy();
  const notice = await screen.findByText(/^Nothing to ask yet on “Covariance matrices”/);
  expect(findJargon(notice.textContent ?? "")).toEqual([]);
});

it("UX-18: a quick check with a question to ask opens as before (the lesson closes for it)", async () => {
  apis({ startQuickCheck: vi.fn(async () => quickCheckProgress({ ...NOTHING_ASKED, finished: false, results: null }, "active")) });
  render(<App />);
  await click("open lesson");
  await click("check first");
  expect(await screen.findByTestId("calibration-stub")).toBeTruthy();
  expect(screen.queryByTestId("lesson-stub")).toBeNull();
});

it("UX-21: Begin whose first step is a lesson offer opens the offer's page", async () => {
  apis();
  render(<App />);
  await click("begin to offer");
  expect(await screen.findByTestId("lesson-offer-page")).toBeTruthy();
  expect(screen.getByTestId("lesson-offer-sentence").textContent).toBe("This looks like something to learn. Start a 15 minute lesson on Eigenvalues?");
});

it("UX-21: the same when Begin started the session", async () => {
  apis();
  render(<App />);
  await click("begin new session to offer");
  expect(await screen.findByTestId("lesson-offer-page")).toBeTruthy();
});

it("UX-27: a place tab leaves the 'Check what I already know' screen", async () => {
  apis({ startQuickCheck: vi.fn(async () => quickCheckProgress({ ...NOTHING_ASKED, finished: false, results: null }, "active")) });
  render(<App />);
  await click("open lesson");
  await click("check first");
  expect(await screen.findByTestId("calibration-stub")).toBeTruthy();
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Progress" })); });
  await flush();
  expect(screen.queryByTestId("calibration-stub")).toBeNull();
  expect(screen.getByTestId("graph-stub")).toBeTruthy();
});

it("UX-27: Today's tab on a question (a short check among them) goes back to Today's plan", async () => {
  apis();
  render(<App />);
  await click("open item");
  expect(await screen.findByTestId("practice-pi_1")).toBeTruthy();
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Today" })); });
  await flush();
  expect(screen.queryByTestId("practice-pi_1")).toBeNull();
  expect(screen.getByTestId("today-place")).toBeTruthy();
});
