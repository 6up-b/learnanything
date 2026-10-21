// UX Phase 2, fix round 2 (whole-stage verify 20261021-114726-Jrt7sA): the
// App shell with the real screens each finding is about, so no stub hides
// the path under test.
//
// 2. Closing Settings (the real SettingsOverlay) or clicking its message
//    dismisses only the message it showed; every other error and every
//    notice not yet delivered stays in the queue. Classic clears its one
//    toast, as before.
// 3. Try again after leaving the screen that raised the error (the real
//    KnowledgeMapView and LibraryScreen): a second failure is shown again,
//    with Try again; a retry that succeeds clears it.
// 4. The real Today listener: Alt+2 goes to the Library and neither opens
//    the second item nor calls planLearnerPick.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { clear } from "../api/queryCache";

const stubs = vi.hoisted(() => ({
  config: {} as Record<string, unknown>,
  session: null as Record<string, unknown> | null,
  api: {} as Record<string, (...args: unknown[]) => unknown>
}));

vi.mock("@tauri-apps/api/event", () => ({ listen: vi.fn(async () => () => undefined) }));
vi.mock("@tauri-apps/plugin-dialog", () => ({ open: vi.fn(async () => null) }));
vi.mock("../components/useSourceFileDrop", () => ({ useSourceFileDrop: () => false, pickSourceFiles: async () => [] }));
vi.mock("../components/InboxStrip", () => ({ InboxStrip: () => null }));

vi.mock("../api/client", () => {
  const base: Record<string, unknown> = {
    loadVault: vi.fn(async () => ({
      vault: { root: "/vault", subjects: [], subjectTitles: [], counts: { learningObjects: 1, practiceItems: 2 }, algorithmVersion: "mvp-0.29" },
      health: { ai: { ready: false, settingsReady: false, manualGrading: false, activeProvider: null }, codex: { ready: false } },
      config: stubs.config,
      activeSession: stubs.session,
      streak: null
    })),
    getSourceLibrary: vi.fn(async () => ({ sources: [{ sourceId: "src_axler", title: "Linear Algebra Done Right" }], pending: [] }))
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

vi.mock("../screens/ReaderScreen", () => ({ ReaderScreen: stub("reader-stub") }));
vi.mock("../screens/LibraryPlace", () => ({ LibraryPlace: stub("library-stub") }));
vi.mock("../screens/StartScreen", () => ({
  StartScreen: ({ onError }: { onError: (message: string) => void }) => (
    <div data-testid="start-stub">
      {["First", "Second", "Third", "Fourth"].map((word) => (
        <button key={word} type="button" onClick={() => onError(`${word} error.`)}>
          fail {word.toLowerCase()}
        </button>
      ))}
    </div>
  )
}));
vi.mock("../screens/PracticeScreen", () => ({ PracticeScreen: stub("practice-stub") }));
vi.mock("../screens/GraphScreen", () => ({ GraphScreen: stub("graph-stub") }));
vi.mock("../screens/IngestScreen", () => ({ IngestScreen: stub("ingest-stub") }));
vi.mock("../screens/ProposalsScreen", () => ({ ProposalsScreen: stub("proposals-stub") }));
vi.mock("../screens/RegistryReviewScreen", () => ({ RegistryReviewScreen: stub("registry-stub") }));
vi.mock("../screens/MaintenanceScreen", () => ({ MaintenanceScreen: stub("maintain-stub") }));
vi.mock("../screens/ReviewScreen", () => ({ ReviewScreen: stub("review-stub") }));
vi.mock("../screens/reader/WrapUpOffer", () => ({ WrapUpOffer: () => null }));

import { App } from "./App";

let store: Map<string, string>;

beforeEach(() => {
  stubs.config = {};
  stubs.session = null;
  stubs.api = {};
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
  // jsdom draws no layout and has no IntersectionObserver.
  Element.prototype.scrollIntoView = () => undefined;
  vi.stubGlobal(
    "IntersectionObserver",
    class {
      observe() {}
      unobserve() {}
      disconnect() {}
      takeRecords() {
        return [];
      }
    }
  );
});
afterEach(() => {
  cleanup();
  clear();
  vi.unstubAllGlobals();
});

async function launch() {
  render(<App />);
  await screen.findByTestId("start-stub");
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

function alertTexts(): string[] {
  return screen.queryAllByRole("alert").map((alert) => alert.querySelector(".shell-notice-text")?.textContent ?? "");
}

async function runPalette(text: string) {
  await press({ key: "k", ctrlKey: true });
  fireEvent.change(screen.getByRole("textbox"), { target: { value: text } });
  await act(async () => {
    fireEvent.keyDown(screen.getByRole("textbox"), { key: "Enter" });
  });
}

// ── 2. Settings keeps the queue ─────────────────────────────────────────

describe("closing Settings dismisses only the message it showed (item 2)", () => {
  const NOTHING_TO_ASK = /Nothing here to ask about/;

  async function queueThreeErrorsANoticeAndAFourthError() {
    await launch();
    for (const word of ["first", "second", "third"]) fireEvent.click(screen.getByRole("button", { name: `fail ${word}` }));
    expect(alertTexts()).toEqual(["First error.", "Second error.", "Third error."]);
    // A notice behind three errors waits: it has not been delivered.
    await press({ key: "2", altKey: true });
    await screen.findByTestId("library-stub");
    await runPalette("ask the tutor");
    expect(screen.queryByText(NOTHING_TO_ASK)).toBeNull();
    await press({ key: "1", altKey: true });
    await screen.findByTestId("start-stub");
    fireEvent.click(screen.getByRole("button", { name: "fail fourth" }));
  }

  async function openSettings() {
    await press({ key: ",", ctrlKey: true });
    return screen.findByRole("dialog", { name: "Settings" });
  }

  it("keeps every other error and the undelivered notice when Settings closes", async () => {
    await queueThreeErrorsANoticeAndAFourthError();
    const dialog = await openSettings();
    // Settings shows the newest message only.
    expect(within(dialog).getByText("Fourth error.")).toBeTruthy();
    await act(async () => {
      fireEvent.keyDown(dialog, { key: "Escape" });
    });
    expect(screen.queryByRole("dialog", { name: "Settings" })).toBeNull();
    // The message Settings showed is gone; the rest of the queue is not.
    expect(alertTexts()).toEqual(["First error.", "Second error.", "Third error."]);
    // The notice that waited behind them is still there, and arrives when a row frees up.
    fireEvent.click(within(screen.getAllByRole("alert")[0]).getByRole("button", { name: "Dismiss" }));
    expect(screen.getByText(NOTHING_TO_ASK)).toBeTruthy();
  });

  it("clicking the message in Settings dismisses only that message", async () => {
    await queueThreeErrorsANoticeAndAFourthError();
    const dialog = await openSettings();
    fireEvent.click(within(dialog).getByText("Fourth error."));
    // The next newest takes its place; nothing else was dropped.
    expect(within(dialog).queryByText("Fourth error.")).toBeNull();
    expect(within(dialog).getByText(NOTHING_TO_ASK)).toBeTruthy();
    await act(async () => {
      fireEvent.keyDown(dialog, { key: "Escape" });
    });
    expect(alertTexts()).toEqual(["First error.", "Second error.", "Third error."]);
  });

  it("classic clears its one toast when Settings closes, as before", async () => {
    stubs.config = { ui: { shell: "classic" } };
    await launch();
    fireEvent.click(screen.getByRole("button", { name: "fail first" }));
    fireEvent.click(screen.getByRole("button", { name: "fail second" }));
    // Classic's toast holds one message, the last.
    expect(screen.getByText("Second error.")).toBeTruthy();
    expect(screen.queryByText("First error.")).toBeNull();
    await press({ key: "s", altKey: true });
    const dialog = await screen.findByRole("dialog", { name: "Settings" });
    expect(within(dialog).getByText("Second error.")).toBeTruthy();
    await act(async () => {
      fireEvent.keyDown(dialog, { key: "Escape" });
    });
    expect(screen.queryByText("Second error.")).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
  });
});

// ── 3. Try again after navigation ───────────────────────────────────────

const TIMEOUT = { code: "sidecar_timeout", message: "The read timed out.", retryable: true };

function failingThenSucceeding(success: unknown) {
  const state = { fail: true, calls: 0 };
  const fn = vi.fn(async () => {
    state.calls += 1;
    if (state.fail) throw { ...TIMEOUT };
    return success;
  });
  return { state, fn };
}

async function retryFrom(text: string) {
  const alert = screen.getAllByRole("alert").find((entry) => entry.textContent?.includes(text));
  expect(alert, `an error saying ${text}`).toBeTruthy();
  await act(async () => {
    fireEvent.click(within(alert as HTMLElement).getByRole("button", { name: "Try again" }));
  });
  await flush();
}

describe("Try again after leaving the screen (item 3)", () => {
  it("Analyst views: a second failure is shown again with Try again; a success clears it", async () => {
    const map = failingThenSucceeding({ points: [], facetField: { points: [] } });
    stubs.api.getKnowledgeMap = map.fn;
    await launch();
    await runPalette("analyst views");
    const first = await screen.findByRole("alert");
    expect(first.textContent).toContain("The read timed out.");
    const callsBefore = map.state.calls;

    // Leave the screen that raised it.
    await press({ key: "2", altKey: true });
    await screen.findByTestId("library-stub");

    await retryFrom("The read timed out.");
    expect(map.state.calls).toBe(callsBefore + 1);
    // Failed again: still shown, with its code and a new Try again.
    await waitFor(() => expect(screen.getAllByRole("alert")).toHaveLength(1));
    const again = screen.getByRole("alert");
    expect(again.textContent).toContain("The read timed out.");
    expect(within(again).getByRole("button", { name: "Try again" })).toBeTruthy();
    fireEvent.click(within(again).getByRole("button", { name: "details ▸" }));
    expect(again.textContent).toContain("sidecar_timeout");

    // The next try succeeds: the error goes.
    map.state.fail = false;
    await retryFrom("The read timed out.");
    expect(map.state.calls).toBe(callsBefore + 2);
    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
  });

  it("Files (the Library screen): the same after navigating away", async () => {
    const tree = failingThenSucceeding({ version: 1, root: "/vault", tree: [] });
    stubs.api.getVaultTree = tree.fn;
    await launch();
    // Under the hood → Files mounts the Library screen.
    await press({ key: "0", altKey: true });
    await screen.findByTestId("maintain-stub");
    fireEvent.click(screen.getByRole("button", { name: "Files" }));
    const first = await screen.findByRole("alert");
    expect(first.textContent).toContain("The read timed out.");

    await press({ key: "4", altKey: true });
    await screen.findByTestId("graph-stub");

    await retryFrom("The read timed out.");
    await waitFor(() => expect(screen.getAllByRole("alert")).toHaveLength(1));
    expect(within(screen.getByRole("alert")).getByRole("button", { name: "Try again" })).toBeTruthy();

    tree.state.fail = false;
    await retryFrom("The read timed out.");
    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
  });

  it("shows one error, not two, when the retry fails while the screen is still there", async () => {
    const map = failingThenSucceeding({ points: [], facetField: { points: [] } });
    stubs.api.getKnowledgeMap = map.fn;
    await launch();
    await runPalette("analyst views");
    await screen.findByRole("alert");
    await retryFrom("The read timed out.");
    await flush();
    expect(screen.getAllByRole("alert")).toHaveLength(1);
    expect(within(screen.getByRole("alert")).getByRole("button", { name: "Try again" })).toBeTruthy();
  });
});

// ── 4. The real Today listener under the shell's place keys ─────────────

function queueItem(index: number) {
  return {
    schedulerSlateId: "slate_1",
    schedulerCandidateId: `cand_${index}`,
    practiceItemId: `pi_${index}`,
    learningObjectId: `lo_${index}`,
    learningObjectTitle: `Item ${index}`,
    subject: null,
    practiceMode: "free_recall",
    selectedMode: "free_recall",
    priority: 1 - index / 10,
    components: { forgettingRisk: 0.2, recentError: 0, probeEig: 0 },
    readinessFactor: null,
    plainEnglish: ["due"],
    dominantReason: "due",
    mastery: 0.4,
    masteryVariance: 0.1,
    dueAt: null,
    dueStatus: "due",
    isProbe: false,
    isFollowup: false,
    followupKind: null
  };
}

function todayApis(plan: unknown) {
  const planLearnerPick = vi.fn(async () => ({ step: null }));
  stubs.session = { sessionId: "s1", availableMinutes: 25, energy: null, startedAt: "2026-10-21T10:00:00Z", checkpoint: null };
  stubs.api = {
    getDailyPlan: vi.fn(async () => plan),
    getTodayQueue: vi.fn(async () => ({
      version: 1,
      generatedAt: "2026-10-21T10:00:00Z",
      sessionId: "s1",
      sections: [{ title: "Due", items: [queueItem(1), queueItem(2), queueItem(3)] }],
      totalItems: 3
    })),
    goalsList: vi.fn(async () => ({ version: 1, goals: [] })),
    getDecayPressure: vi.fn(async () => ({ version: 1, pressure: null })),
    getQueueRevision: vi.fn(async () => ({ version: 1, revision: 1 })),
    listIngestBatches: vi.fn(async () => ({ version: 1, batches: [] })),
    getTodayHeadline: vi.fn(async () => ({ version: 1, enabled: false })),
    planLearnerPick
  };
  return { planLearnerPick };
}

function enabledPlan() {
  const planBody = {
    id: "plan_1",
    localDate: "2026-10-21",
    kind: "keep_going",
    status: "open",
    stopReason: null,
    parentPlanId: null,
    minutesBudget: 25,
    rememberedMinutes: 25,
    minutesSource: "carried",
    minuteChoices: [10, 15, 25, 40, 60],
    minutesLeft: 25,
    split: { rule: "split_v1", line: "25 min · review 25", lanesAllowed: ["review"], requestedMinutes: 0, lanes: [] },
    admission: { admittedCount: 0, exemptRequests: 0, stoppedBy: null, floorApplied: false, reviewLoadPerDay: null, ceilingMinutes: null, override: null },
    blocks: [],
    currentBlockId: null,
    projected: [],
    blockCountEstimate: 1,
    firstBlock: null,
    nextStep: null,
    totals: { plannedMinutes: 25, plannedItems: 3, doneItems: 0, skippedItems: 0, displacedItems: 0, readingBlocks: 0, readingBlocksEnded: 0, estMinutesDone: 0, actualMinutes: 0 },
    reentry: null,
    source: null,
    chooser: null
  };
  return {
    version: 1,
    enabled: true,
    headlineEnabled: false,
    localDate: "2026-10-21",
    plan: planBody,
    day: { plans: 1, kinds: ["keep_going"], complete: false, ...planBody.totals },
    streak: { current: 1, activeToday: true, longest: 1 }
  };
}

async function openToday() {
  render(<App />);
  // With a session open, Alt+1 is Today itself.
  await screen.findByTestId("start-stub").catch(() => undefined);
  await press({ key: "1", altKey: true });
  await flush();
}

describe("the shell's place keys never reach Today's numbered pick (item 4)", () => {
  it("plan off: Alt+2 opens the Library and does not open item 2", async () => {
    const { planLearnerPick } = todayApis({ version: 1, enabled: false, plan: null });
    await openToday();
    expect(await screen.findByText("Item 2")).toBeTruthy();
    await press({ key: "2", altKey: true });
    await flush();
    expect(screen.getByTestId("library-stub")).toBeTruthy();
    expect(screen.queryByTestId("practice-stub")).toBeNull();
    expect(planLearnerPick).not.toHaveBeenCalled();
    // A plain "2" on Today still picks the second item.
    await press({ key: "1", altKey: true });
    await screen.findByText("Item 2");
    await press({ key: "2" });
    await flush();
    expect(screen.getByTestId("practice-stub")).toBeTruthy();
  });

  it("plan on, full list shown: Alt+2 opens the Library and calls no planLearnerPick", async () => {
    const { planLearnerPick } = todayApis(enabledPlan());
    await openToday();
    await screen.findByTestId("daily-plan");
    await press({ key: "l" });
    expect(await screen.findByText("Item 2")).toBeTruthy();
    await press({ key: "2", altKey: true });
    await flush();
    expect(screen.getByTestId("library-stub")).toBeTruthy();
    expect(planLearnerPick).not.toHaveBeenCalled();
    expect(screen.queryByTestId("practice-stub")).toBeNull();
  });
});
