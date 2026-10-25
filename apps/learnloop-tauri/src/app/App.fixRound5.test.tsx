// UX Phase 2, fix round 5 (the orchestrator's adversarial verify of
// 7f4a3974a, standing in for Codex).
//
// 1. The global-listener target rule: a screen's window shortcut leaves a key
//    aimed at an interactive element it does not own. With the REAL wrap-up
//    line and panel on Start: Enter on the line opens the wrap-up and starts
//    no session; Enter on an action link runs the action.
// 2. After a pointer activation of a place, a tool or a ⋯ row the focus goes
//    to the frame body, and the chrome keeps only the keys its control
//    consumes: click Today, press Enter, and the plan begins; Today's numbered
//    keys work after the click; the Proposals keys work after clicking its
//    Under-the-hood tool.
// 3. Lows: Control, Meta, Alt and Shift keyups pass through the chrome;
//    closing a book forgets it.
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
  ReaderScreen: ({
    initialSource,
    onSourceChange
  }: {
    initialSource?: { card: { sourceId: string; title: string } } | null;
    onSourceChange?: (source: null) => void;
  }) => (
    <div data-testid="reader-stub" data-source={initialSource?.card.sourceId ?? "shelf"} data-title={initialSource?.card.title ?? ""}>
      reader
      {/* The Reader's "← Library": back to the shelf, the book closed. */}
      <button type="button" onClick={() => onSourceChange?.(null)}>
        close book
      </button>
    </div>
  )
}));
vi.mock("../screens/LibraryPlace", () => ({ LibraryPlace: stub("library-stub") }));
vi.mock("../screens/PracticeScreen", () => ({ PracticeScreen: stub("practice-stub") }));
vi.mock("../screens/GraphScreen", () => ({ GraphScreen: stub("graph-stub") }));
vi.mock("../screens/IngestScreen", () => ({ IngestScreen: stub("ingest-stub") }));
vi.mock("../screens/RegistryReviewScreen", () => ({ RegistryReviewScreen: stub("registry-stub") }));
vi.mock("../screens/MaintenanceScreen", () => ({ MaintenanceScreen: stub("maintain-stub") }));
vi.mock("../screens/ReviewScreen", () => ({ ReviewScreen: stub("review-stub") }));
vi.mock("../screens/SettingsScreen", () => ({ SettingsOverlay: stub("settings-stub") }));

import { App } from "./App";

let store: Map<string, string>;

beforeAll(async () => {
  await import("../screens/StartScreen");
  await import("../screens/TodayScreen");
  await import("../screens/KnowledgeMapScreen");
  await import("../screens/ProposalsScreen");
  await import("../screens/reader/WrapUpOffer");
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

/** A window and a document listener that must never see a key the control
 *  under test (`watch`) consumes, marked or not. */
function screenListenersSpy() {
  const seen: string[] = [];
  let watched: HTMLElement | null = null;
  const record = (event: Event) => {
    const target = event.target as HTMLElement | null;
    // Fix round 5: the chrome keeps the keys a control consumes (Enter and
    // Space on a button; every plain key in a menu or dialog). Others go on,
    // and the screens' target rule leaves them (the forbidden checks).
    const key = (event as KeyboardEvent).key;
    const consumed = key === "Enter" || key === " " || Boolean(target?.closest?.('[data-shell-chrome="dialog"], [role="menu"]'));
    if (consumed && target && watched && (target === watched || watched.contains(target))) seen.push(`${event.type} ${(event as KeyboardEvent).key} on ${target.textContent?.trim().slice(0, 24)}`);
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

/** A browser pointer activation: the press focuses the control, then the
 *  click (detail 1) activates it. */
async function pointerActivate(element: HTMLElement) {
  await act(async () => {
    element.focus();
    fireEvent.click(element, { detail: 1 });
  });
  await flush();
}

/** A key pressed wherever the focus is now, as a browser sends it. */
async function pressFocused(key: string) {
  const target = (document.activeElement as HTMLElement | null) ?? document.body;
  await pressOn(target, key as "Enter");
}

const WRAP_UP = {
  version: 1,
  wrapUpVersion: "v1",
  available: true,
  extractionId: "ext_axler",
  session: null,
  resolved: [],
  stillOpen: [
    {
      rootExchangeId: "ex_1",
      questionMd: "Why is a basis independent?",
      actions: [
        { action: "resolve", rpc: "reader.set_inquiry_status", params: { extractionId: "ext_axler", exchangeId: "ex_1", resolution: "resolved", trigger: "chip" } },
        { action: "keep_open" }
      ]
    }
  ],
  worthReinforcing: []
};

describe("the global-listener target rule (item 1)", () => {
  it("Enter on the real wrap-up line opens the wrap-up and starts no session; Enter on its action runs it", async () => {
    stubs.config = { recap: { enabled: true, wrapUpEnabled: true } };
    const { startSession } = screenApis();
    const readerWrapUp = vi.fn(async () => WRAP_UP);
    const readerSetInquiryStatus = vi.fn(async (_input: Record<string, unknown>) => ({}));
    Object.assign(stubs.api, {
      readerWrapUpOffer: vi.fn(async () => ({ version: 1, offer: { extractionId: "ext_axler", sourceId: AXLER.sourceId, session: {} } })),
      readerWrapUp,
      readerSetInquiryStatus,
      readerRecapEvent: vi.fn(async () => ({}))
    });
    render(<App />);
    await screen.findByText(/\d+ minutes today/);
    // Leave the Reader for Today (Start until a session is open): the line shows.
    await press({ key: "3", altKey: true });
    await screen.findByTestId("reader-stub");
    await press({ key: "1", altKey: true });
    const line = await screen.findByRole("button", { name: /wrap-up ready/i });
    await pressOn(line, "Enter");
    await waitFor(() => expect(readerWrapUp).toHaveBeenCalledTimes(1));
    const panel = await screen.findByRole("region", { name: /wrap up/i });
    expect(startSession).not.toHaveBeenCalled();
    await pressOn(within(panel).getByRole("button", { name: "resolve" }), "Enter");
    await waitFor(() => expect(readerSetInquiryStatus).toHaveBeenCalledTimes(1));
    expect(readerSetInquiryStatus.mock.calls[0][0]).toMatchObject({ exchangeId: "ex_1", resolution: "resolved" });
    expect(startSession).not.toHaveBeenCalled();
    // Start's own Enter, from the page, still begins.
    (document.activeElement as HTMLElement | null)?.blur();
    await press({ key: "Enter" });
    await waitFor(() => expect(startSession).toHaveBeenCalledTimes(1));
  });
});

describe("focus after a pointer activation (item 2)", () => {
  it("click Today, press Enter: the plan begins", async () => {
    const { startSession } = screenApis();
    render(<App />);
    await screen.findByText(/\d+ minutes today/);
    await pointerActivate(navButton("Today"));
    expect(document.activeElement).toBe(document.body);
    await pressFocused("Enter");
    await waitFor(() => expect(startSession).toHaveBeenCalledTimes(1));
  });

  it("a keyboard activation keeps the focus on the control", async () => {
    screenApis();
    render(<App />);
    await screen.findByText(/\d+ minutes today/);
    const today = navButton("Today");
    await pressOn(today, "Enter");
    expect(document.activeElement).toBe(today);
  });

  it("click Today, then Today's list keys open the item", async () => {
    stubs.session = { sessionId: "s1", availableMinutes: 25, energy: null, startedAt: "2026-10-21T10:00:00Z", checkpoint: null };
    screenApis();
    render(<App />);
    await screen.findByRole("navigation", { name: "Places" });
    await pointerActivate(navButton("Today"));
    await screen.findByTestId("today-place");
    expect(document.activeElement).toBe(document.body);
    // UX Phase 3: the plain list (`l`), then j and Enter on its second item.
    await pressFocused("l");
    await screen.findAllByText("Item 2");
    await pressFocused("j");
    await pressFocused("Enter");
    expect(await screen.findByTestId("practice-stub")).toBeTruthy();
  });

  it("click a ⋯ row, then the screen beneath keeps its keys", async () => {
    stubs.session = { sessionId: "s1", availableMinutes: 25, energy: null, startedAt: "2026-10-21T10:00:00Z", checkpoint: null };
    screenApis();
    render(<App />);
    await screen.findByRole("navigation", { name: "Places" });
    await pointerActivate(navButton("Today"));
    await screen.findByTestId("today-place");
    await pointerActivate(navButton("⋯"));
    await pointerActivate(within(screen.getByRole("menu")).getByRole("menuitem", { name: /Keyboard & help/ }));
    // Keyboard & help takes the focus; closing it with the mouse returns to the page.
    await act(async () => {
      fireEvent.click(document.querySelector(".keys-help-backdrop") as HTMLElement);
    });
    (document.activeElement as HTMLElement | null)?.blur();
    await pressFocused("l");
    await screen.findAllByText("Item 2");
    await pressFocused("j");
    await pressFocused("Enter");
    expect(await screen.findByTestId("practice-stub")).toBeTruthy();
  });

  it("click the Proposals tool under the hood, then the Proposals keys work", async () => {
    screenApis();
    const proposals = {
      version: 1,
      batches: [
        {
          id: "b1",
          summary: "Proposed error taxonomy entries from grading.",
          purpose: "grading_error_type",
          status: "open",
          createdAt: null,
          updatedAt: null,
          agentRun: { id: "run_b1", model: null, provider: null, purpose: "grading_error_type", codexRevision: null, startedAt: null, durationS: null, status: "done" },
          counts: { pending: 1, accepted: 0, rejected: 0 },
          items: [
            {
              id: "i1",
              clientItemId: "error_type:local_slip",
              itemType: "error_type",
              operation: "create",
              decision: "pending",
              proposedEntityId: "local_slip",
              targetEntityType: null,
              targetEntityId: null,
              reviewRoute: "review_required",
              validationStatus: "valid",
              validationErrors: [],
              edited: false,
              applied: false,
              rationale: "",
              sourceRefs: [],
              payloadLines: [],
              payloadJson: "{}"
            }
          ]
        }
      ],
      totals: { pending: 1, accepted: 0, rejected: 0 },
      batchCount: 1,
      rewordConfirms: []
    };
    const acceptProposalItems = vi.fn(async () => proposals);
    Object.assign(stubs.api, { getProposals: vi.fn(async () => proposals), acceptProposalItems });
    render(<App />);
    await screen.findByText(/\d+ minutes today/);
    await press({ key: "0", altKey: true });
    await screen.findByTestId("maintain-stub");
    const list = screen.getByRole("navigation", { name: "Under the hood" });
    await pointerActivate(within(list).getByRole("button", { name: /Study-map changes/ }));
    await screen.findAllByText("local_slip");
    expect(document.activeElement).toBe(document.body);
    await pressFocused("a");
    await waitFor(() => expect(acceptProposalItems).toHaveBeenCalledWith("b1", ["i1"]));
  });
});

describe("the lows (item 3)", () => {
  it("lets Control, Meta, Alt and Shift keyups pass through the chrome", async () => {
    screenApis();
    render(<App />);
    await screen.findByText(/\d+ minutes today/);
    const ups: string[] = [];
    const record = (event: KeyboardEvent) => ups.push(event.key);
    window.addEventListener("keyup", record);
    try {
      const today = navButton("Today");
      for (const key of ["Control", "Meta", "Alt", "Shift", "Enter"]) {
        await act(async () => {
          today.focus();
          today.dispatchEvent(new KeyboardEvent("keyup", { key, bubbles: true, cancelable: true }));
        });
      }
    } finally {
      window.removeEventListener("keyup", record);
    }
    // The modifiers' releases reach the window; Enter's stays with the button.
    expect(ups).toEqual(["Control", "Meta", "Alt", "Shift"]);
  });

  it("closing a book forgets it, so the next start opens the shelf", async () => {
    store.set("learnloop.place", "reader");
    store.set("learnloop.reader.book:/vault", AXLER.sourceId);
    render(<App />);
    await waitFor(() => expect(screen.getByTestId("reader-stub").getAttribute("data-source")).toBe(AXLER.sourceId));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "close book" }));
    });
    await waitFor(() => expect(store.get("learnloop.reader.book:/vault") ?? "").toBe(""));
    cleanup();
    render(<App />);
    expect((await screen.findByTestId("reader-stub")).getAttribute("data-source")).toBe("shelf");
  });
});
