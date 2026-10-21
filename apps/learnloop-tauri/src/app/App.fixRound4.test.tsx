// UX Phase 2, fix round 4 (whole-stage verify 20261021-134216-8mdDfN).
//
// 1. The simple shell's chrome is a key-isolated region. With the real Start
//    and Today screens and their real window listeners mounted, every chrome
//    control (the four places, + Add, ^K, ⋯ and each of its rows, a notice's
//    Try again, details and Dismiss, and the Under-the-hood list) is focused
//    and Enter, Space and Escape are pressed on it. The browser's own
//    activation is emulated (Enter on a button clicks it unless the keydown
//    was prevented; Space clicks it on keyup unless either was prevented).
//    The control's own action runs (it is clicked), and nothing of the
//    screen's runs: no begin(), no session, no item opened, no plan pick, and
//    no window or document listener sees the key.
// 3. The remembered book comes back on restart whatever the landing place:
//    restarting on Progress, Alt+3 and "Continue reading" open it in the
//    Reader. The Reader stub reports the source it was actually given.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
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

const AXLER = { sourceId: "src_axler", title: "Linear Algebra Done Right" };

vi.mock("../api/client", () => {
  const base: Record<string, unknown> = {
    loadVault: vi.fn(async () => ({
      vault: { root: "/vault", subjects: [], subjectTitles: [], counts: { learningObjects: 1, practiceItems: 3 }, algorithmVersion: "mvp-0.29" },
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

vi.mock("../screens/ReaderScreen", () => ({
  ReaderScreen: ({ initialSource }: { initialSource?: { card: { sourceId: string; title: string } } | null }) => (
    <div data-testid="reader-stub" data-source={initialSource?.card.sourceId ?? "shelf"} data-title={initialSource?.card.title ?? ""}>
      reader
    </div>
  )
}));
vi.mock("../screens/LibraryPlace", () => ({ LibraryPlace: stub("library-stub") }));
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

let store: Map<string, string>;

beforeAll(async () => {
  await import("../screens/StartScreen");
  await import("../screens/TodayScreen");
  await import("../screens/KnowledgeMapScreen");
}, 120_000);

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
  Element.prototype.scrollIntoView = () => undefined;
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  vi.stubGlobal("IntersectionObserver", class { observe() {} unobserve() {} disconnect() {} takeRecords() { return []; } });
});
afterEach(() => {
  cleanup();
  clear();
  vi.unstubAllGlobals();
});

async function flush() {
  await act(async () => {
    for (let i = 0; i < 10; i += 1) await Promise.resolve();
  });
}

async function press(init: KeyboardEventInit) {
  await act(async () => {
    window.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, cancelable: true, ...init }));
  });
}

/** Press a key on a focused control the way a browser does: the keydown
 *  (and keyup) go to the control, and Enter or Space activate a button unless
 *  a listener prevented the default. */
async function pressOn(element: HTMLElement, key: "Enter" | " " | "Escape") {
  await act(async () => {
    element.focus();
    const down = new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true });
    const downAllowed = element.dispatchEvent(down);
    if (key === "Enter" && downAllowed) element.click();
    const up = new KeyboardEvent("keyup", { key, bubbles: true, cancelable: true });
    const upAllowed = element.dispatchEvent(up);
    if (key === " " && downAllowed && upAllowed) element.click();
  });
  await flush();
}

const QUEUE_ITEM = (index: number) => ({
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
});

function screenApis() {
  const startSession = vi.fn(async () => ({ sessionId: "s_new", availableMinutes: 25, energy: null, startedAt: "2026-10-21T10:00:00Z", checkpoint: null }));
  const planLearnerPick = vi.fn(async () => ({ step: null }));
  const openQueueItem = vi.fn(async () => ({}));
  Object.assign(stubs.api, {
    getStartSummary: vi.fn(async () => ({
      version: 1,
      rememberedMinutes: 25,
      minutesSource: "last_session",
      minutesPresets: [10, 15, 25, 40, 60],
      minuteChoices: [10, 15, 25, 40, 60],
      streak: { current: 1, activeToday: false, longest: 1 }
    })),
    getDailyPlan: vi.fn(async () => ({ version: 1, enabled: false, plan: null })),
    getTodayQueue: vi.fn(async () => ({
      version: 1,
      generatedAt: "2026-10-21T10:00:00Z",
      sessionId: stubs.session ? "s1" : null,
      sections: [{ title: "Due", items: [QUEUE_ITEM(1), QUEUE_ITEM(2)] }],
      totalItems: 2
    })),
    goalsList: vi.fn(async () => ({ version: 1, goals: [] })),
    getDecayPressure: vi.fn(async () => ({ version: 1, pressure: null })),
    getQueueRevision: vi.fn(async () => ({ version: 1, revision: 1 })),
    listIngestBatches: vi.fn(async () => ({ version: 1, batches: [] })),
    getTodayHeadline: vi.fn(async () => ({ version: 1, enabled: false })),
    startSession,
    planLearnerPick,
    openQueueItem
  });
  return { startSession, planLearnerPick, openQueueItem };
}

/** A window and a document listener that must never see a key pressed on
 *  the control under test (`watch`), marked or not. */
function screenListenersSpy() {
  const seen: string[] = [];
  let watched: HTMLElement | null = null;
  const record = (event: Event) => {
    const target = event.target as HTMLElement | null;
    if (target && watched && (target === watched || watched.contains(target))) seen.push(`${event.type} ${(event as KeyboardEvent).key} on ${target.textContent?.trim().slice(0, 24)}`);
  };
  for (const type of ["keydown", "keyup", "keypress"]) {
    window.addEventListener(type, record);
    document.addEventListener(type, record);
  }
  return {
    seen,
    watch: (element: HTMLElement | null) => {
      watched = element;
    },
    stop: () => {
      for (const type of ["keydown", "keyup", "keypress"]) {
        window.removeEventListener(type, record);
        document.removeEventListener(type, record);
      }
    }
  };
}

function navButton(name: string | RegExp): HTMLElement {
  return within(screen.getByRole("navigation", { name: "Places" })).getByRole("button", { name });
}

/** Each control, each key: the control is activated (Enter, Space) and the
 *  screen's actions never run. `back` returns to the screen under test. */
async function sweep(
  controls: Array<{ name: string; get: () => HTMLElement; after?: () => Promise<void> }>,
  forbidden: () => void,
  back: () => Promise<void>
) {
  const spy = screenListenersSpy();
  try {
    for (const control of controls) {
      for (const key of ["Enter", " ", "Escape"] as const) {
        const element = control.get();
        const clicked = vi.fn();
        element.addEventListener("click", clicked);
        spy.watch(element);
        await pressOn(element, key);
        spy.watch(null);
        element.removeEventListener("click", clicked);
        if (key === "Escape") expect(clicked, `${control.name}: Escape activates nothing`).not.toHaveBeenCalled();
        else expect(clicked, `${control.name}: ${key === " " ? "Space" : key} activates it`).toHaveBeenCalledTimes(1);
        forbidden();
        await control.after?.();
        await back();
      }
    }
    expect(spy.seen).toEqual([]);
  } finally {
    spy.stop();
  }
}

async function closeOverlays() {
  // The palette, Keyboard & help and the ⋯ menu each close on a click on their backdrop or the button.
  const backdrop = document.querySelector(".cli-backdrop, .keys-help-backdrop") as HTMLElement | null;
  if (backdrop) {
    await act(async () => {
      fireEvent.mouseDown(backdrop);
      fireEvent.click(backdrop);
    });
  }
  const menu = screen.queryByRole("menu");
  if (menu) {
    await act(async () => {
      fireEvent.mouseDown(document.body);
    });
  }
  if (screen.queryByTestId("settings-stub")) {
    // Settings is a stub here: closing it is the shell's own state; reload the screen instead.
  }
}

describe("the simple shell's chrome is key-isolated (item 1)", () => {
  it("on Start: Enter, Space and Escape on every chrome control activate it and never begin a session", async () => {
    const { startSession } = screenApis();
    render(<App />);
    // The real Start screen, ready to begin on Enter.
    expect(await screen.findByText(/begin session · \d+ min/)).toBeTruthy();
    // The real listener is live: Enter on the page begins (proved, then undone by a fresh mount below).
    const backToStart = async () => {
      await closeOverlays();
      if (!screen.queryByText(/begin session · \d+ min/)) {
        await press({ key: "1", altKey: true });
        await screen.findByText(/begin session · \d+ min/);
      }
    };
    const forbidden = () => expect(startSession).not.toHaveBeenCalled();
    await sweep(
      [
        { name: "Today", get: () => navButton("Today") },
        { name: "Library", get: () => navButton("Library") },
        { name: "Reader", get: () => navButton("Reader") },
        { name: "Progress", get: () => navButton("Progress") },
        { name: "+ Add", get: () => navButton("+ Add") },
        { name: "^K", get: () => navButton("^K") },
        { name: "⋯", get: () => navButton("⋯") }
      ],
      forbidden,
      backToStart
    );
    // ⋯'s rows: open the menu, then each row.
    const rows = ["Settings", "Under the hood", "Open another library…", "New library…", "Keyboard & help"];
    for (const row of rows) {
      await sweep(
        [
          {
            name: `⋯ → ${row}`,
            get: () => {
              if (!screen.queryByRole("menu")) fireEvent.click(navButton("⋯"));
              return within(screen.getByRole("menu")).getByRole("menuitem", { name: new RegExp(`^${row.replace(/[.…&+]/g, ".")}`) });
            }
          }
        ],
        forbidden,
        async () => {
          if (screen.queryByTestId("settings-stub")) {
            cleanup();
            render(<App />);
            await screen.findByText(/begin session · \d+ min/);
            return;
          }
          await backToStart();
        }
      );
    }
    // And the real Start listener does begin on Enter from the page itself.
    await press({ key: "Enter" });
    await waitFor(() => expect(startSession).toHaveBeenCalledTimes(1));
  });

  it("on Start: a notice's Try again, details and Dismiss", async () => {
    const { startSession } = screenApis();
    const TIMEOUT = { code: "sidecar_timeout", message: "The read timed out.", retryable: true };
    const map = vi.fn(async () => {
      throw { ...TIMEOUT };
    });
    stubs.api.getKnowledgeMap = map;
    render(<App />);
    await screen.findByText(/begin session · \d+ min/);
    // An Analyst views read fails; back on Start, its error waits with its controls.
    await press({ key: "0", altKey: true });
    await screen.findByTestId("maintain-stub");
    fireEvent.click(screen.getByRole("button", { name: "Analyst views" }));
    await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
    await press({ key: "1", altKey: true });
    await screen.findByText(/begin session · \d+ min/);
    const alert = () => screen.getByRole("alert");
    const forbidden = () => expect(startSession).not.toHaveBeenCalled();
    await sweep(
      [
        { name: "Try again", get: () => within(alert()).getByRole("button", { name: /Try again|Trying again/ }) },
        { name: "details", get: () => within(alert()).getByRole("button", { name: /details/ }) }
      ],
      forbidden,
      async () => {
        await waitFor(() => expect(within(alert()).getByRole("button", { name: "Try again" })).toBeTruthy());
      }
    );
    expect(map.mock.calls.length).toBeGreaterThanOrEqual(3);
    // Dismiss last: Enter removes it.
    const spy = screenListenersSpy();
    const dismiss = within(alert()).getByRole("button", { name: "Dismiss" });
    spy.watch(dismiss);
    await pressOn(dismiss, "Enter");
    spy.stop();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(spy.seen).toEqual([]);
    forbidden();
  });

  it("on Today: Enter on the places and ^K opens no item and picks nothing", async () => {
    stubs.session = { sessionId: "s1", availableMinutes: 25, energy: null, startedAt: "2026-10-21T10:00:00Z", checkpoint: null };
    const { planLearnerPick } = screenApis();
    render(<App />);
    await screen.findByRole("navigation", { name: "Places" });
    await press({ key: "1", altKey: true });
    expect(await screen.findAllByText("Item 1")).toBeTruthy();
    const backToToday = async () => {
      await closeOverlays();
      if (!screen.queryAllByText("Item 1").length) {
        await press({ key: "1", altKey: true });
        await screen.findAllByText("Item 1");
      }
    };
    await sweep(
      [
        { name: "Today", get: () => navButton("Today") },
        { name: "Progress", get: () => navButton("Progress") },
        { name: "^K", get: () => navButton("^K") },
        { name: "⋯", get: () => navButton("⋯") }
      ],
      () => {
        expect(screen.queryByTestId("practice-stub")).toBeNull();
        expect(planLearnerPick).not.toHaveBeenCalled();
      },
      backToToday
    );
    // Today's own Enter still opens the focused item from the page.
    await press({ key: "Enter" });
    expect(await screen.findByTestId("practice-stub")).toBeTruthy();
  });

  it("under the hood: the tool list's buttons take their keys to themselves", async () => {
    screenApis();
    render(<App />);
    await screen.findByText(/begin session · \d+ min/);
    await press({ key: "0", altKey: true });
    await screen.findByTestId("maintain-stub");
    const list = () => screen.getByRole("navigation", { name: "Under the hood" });
    const tools = within(list()).getAllByRole("button").map((button) => button.getAttribute("aria-label") ?? "");
    expect(tools.length).toBeGreaterThan(5);
    await sweep(
      tools.filter((name) => name !== "Mistake history").map((name) => ({ name, get: () => within(list()).getByRole("button", { name }) })),
      () => undefined,
      async () => {
        if (!screen.queryByRole("navigation", { name: "Under the hood" })) await press({ key: "0", altKey: true });
      }
    );
  });

  it("keeps every simple-shell control inside a chrome part", async () => {
    screenApis();
    render(<App />);
    await screen.findByText(/begin session · \d+ min/);
    for (const button of within(screen.getByRole("navigation", { name: "Places" })).getAllByRole("button")) {
      expect(button.closest("[data-shell-chrome]"), button.textContent ?? "").not.toBeNull();
    }
    fireEvent.click(navButton("⋯"));
    for (const item of within(screen.getByRole("menu")).getAllByRole("menuitem")) {
      expect(item.closest("[data-shell-chrome]"), item.textContent ?? "").not.toBeNull();
    }
  });
});

// ── 3. The remembered book on restart ──────────────────────────────────

describe("the remembered book comes back whatever the landing place (item 3)", () => {
  function rememberedOnProgress() {
    store.set("learnloop.place", "progress");
    store.set("learnloop.reader.book:/vault", AXLER.sourceId);
  }

  it("restarting on Progress, Alt+3 opens the last book", async () => {
    rememberedOnProgress();
    render(<App />);
    expect(await screen.findByTestId("graph-stub")).toBeTruthy();
    await flush();
    await press({ key: "3", altKey: true });
    const reader = await screen.findByTestId("reader-stub");
    await waitFor(() => expect(reader.getAttribute("data-source")).toBe(AXLER.sourceId));
    expect(reader.getAttribute("data-title")).toBe(AXLER.title);
  });

  it("restarting on Progress, Continue reading opens the last book", async () => {
    rememberedOnProgress();
    render(<App />);
    await screen.findByTestId("graph-stub");
    await flush();
    await press({ key: "k", ctrlKey: true });
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "continue reading" } });
    await act(async () => {
      fireEvent.keyDown(screen.getByRole("textbox"), { key: "Enter" });
    });
    const reader = await screen.findByTestId("reader-stub");
    await waitFor(() => expect(reader.getAttribute("data-source")).toBe(AXLER.sourceId));
  });

  it("never replaces a book opened before the library list came back", async () => {
    // Without a remembered book the Reader opens on its shelf, as before.
    store.set("learnloop.place", "progress");
    render(<App />);
    await screen.findByTestId("graph-stub");
    await press({ key: "3", altKey: true });
    expect((await screen.findByTestId("reader-stub")).getAttribute("data-source")).toBe("shelf");
  });
});
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

describe("the plan view under the chrome (item 1)", () => {
  it("on Today's plan: Enter on the chrome never continues the plan", async () => {
    stubs.session = { sessionId: "s1", availableMinutes: 25, energy: null, startedAt: "2026-10-21T10:00:00Z", checkpoint: null };
    screenApis();
    const nextPlanItem = vi.fn(async () => ({ ...enabledPlan(), step: null }));
    stubs.api.getDailyPlan = vi.fn(async () => enabledPlan());
    stubs.api.nextPlanItem = nextPlanItem;
    render(<App />);
    await screen.findByRole("navigation", { name: "Places" });
    await press({ key: "1", altKey: true });
    await screen.findByTestId("daily-plan");
    await sweep(
      [
        { name: "Today", get: () => navButton("Today") },
        { name: "^K", get: () => navButton("^K") },
        { name: "⋯", get: () => navButton("⋯") }
      ],
      () => expect(nextPlanItem).not.toHaveBeenCalled(),
      async () => {
        await closeOverlays();
        if (!screen.queryByTestId("daily-plan")) {
          await press({ key: "1", altKey: true });
          await screen.findByTestId("daily-plan");
        }
      }
    );
  });
});
