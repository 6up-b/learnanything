// UX Phase 2, fix round 3 (whole-stage verify 20261021-130232-Uk06Al): the App
// shell with the real screens each finding is about.
//
// 1. Every actionable error has a stable identity (its source) and a
//    self-contained retry. The real KnowledgeMapView: Strata's history
//    fails, the view changes to Terrain, Try again reads the history again
//    (round 2's retry resolved without a request and dropped the error).
//    Well's decay pressure: the same after navigating away. Two failures
//    with the same sentence from two sources are two errors; retrying one
//    leaves the other.
// 2. Until loadVault has named the current library's shell, the app is the
//    base shell: Alt+2 does what base does (Today), whatever a stale or
//    missing per-machine cache says.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { clear } from "../api/queryCache";

const stubs = vi.hoisted(() => ({
  config: {} as Record<string, unknown>,
  loadGate: null as Promise<void> | null,
  loadFails: false,
  api: {} as Record<string, (...args: unknown[]) => unknown>
}));

vi.mock("@tauri-apps/api/event", () => ({ listen: vi.fn(async () => () => undefined) }));
vi.mock("@tauri-apps/plugin-dialog", () => ({ open: vi.fn(async () => null) }));
vi.mock("../components/useSourceFileDrop", () => ({ useSourceFileDrop: () => false, pickSourceFiles: async () => [] }));

vi.mock("../api/client", () => {
  const base: Record<string, unknown> = {
    loadVault: vi.fn(async () => {
      if (stubs.loadGate) await stubs.loadGate;
      if (stubs.loadFails) throw { code: "vault_unavailable", message: "The library could not be opened.", retryable: false };
      return {
        vault: { root: "/vault", subjects: [], subjectTitles: [], counts: { learningObjects: 1, practiceItems: 1 }, algorithmVersion: "mvp-0.29" },
        health: { ai: { ready: false, settingsReady: false, manualGrading: false, activeProvider: null }, codex: { ready: false } },
        config: stubs.config,
        activeSession: null,
        streak: null
      };
    }),
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
vi.mock("../screens/StartScreen", () => ({ StartScreen: stub("start-stub") }));
vi.mock("../screens/TodayScreen", () => ({ TodayScreen: stub("today-stub") }));
vi.mock("../screens/PracticeScreen", () => ({ PracticeScreen: stub("practice-stub") }));
vi.mock("../screens/GraphScreen", () => ({ GraphScreen: stub("graph-stub") }));
vi.mock("../screens/IngestScreen", () => ({ IngestScreen: stub("ingest-stub") }));
vi.mock("../screens/ProposalsScreen", () => ({ ProposalsScreen: stub("proposals-stub") }));
vi.mock("../screens/RegistryReviewScreen", () => ({ RegistryReviewScreen: stub("registry-stub") }));
vi.mock("../screens/MaintenanceScreen", () => ({ MaintenanceScreen: stub("maintain-stub") }));
vi.mock("../screens/ReviewScreen", () => ({ ReviewScreen: stub("review-stub") }));
vi.mock("../screens/reader/WrapUpOffer", () => ({ WrapUpOffer: () => null }));

import { App } from "./App";
import { StrictMode } from "react";
import { activeShell } from "./algoConfig";
import { keyScope } from "./keyScope";
import { screenLeavesKey } from "./keymap";

let store: Map<string, string>;

// The lazily loaded screens are big modules: load them once up front so the
// first test does not spend its time budget transforming them.
beforeAll(async () => {
  await import("../screens/KnowledgeMapScreen");
  await import("../screens/LibraryScreen");
}, 120_000);

function storage(map: Map<string, string>) {
  return {
    getItem: (key: string) => map.get(key) ?? null,
    setItem: (key: string, value: string) => {
      map.set(key, value);
    },
    removeItem: (key: string) => {
      map.delete(key);
    },
    clear: () => map.clear()
  };
}

beforeEach(() => {
  stubs.config = {};
  stubs.loadGate = null;
  stubs.loadFails = false;
  stubs.api = {};
  store = new Map<string, string>();
  vi.stubGlobal("localStorage", storage(store));
  Element.prototype.scrollIntoView = () => undefined;
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
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

async function runPalette(text: string) {
  await press({ key: "k", ctrlKey: true });
  fireEvent.change(screen.getByRole("textbox"), { target: { value: text } });
  await act(async () => {
    fireEvent.keyDown(screen.getByRole("textbox"), { key: "Enter" });
  });
}

async function openUnderTheHood(tool: "Analyst views" | "Files") {
  await press({ key: "0", altKey: true });
  await screen.findByTestId("maintain-stub");
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: tool }));
  });
  await flush();
}

async function view(mode: "terrain" | "well" | "strata") {
  await act(async () => {
    fireEvent.click(await screen.findByRole("button", { name: mode }, { timeout: 5000 }));
  });
  await flush();
}

function alertWith(text: string): HTMLElement[] {
  return screen.queryAllByRole("alert").filter((alert) => alert.textContent?.includes(text));
}

async function tryAgain(alert: HTMLElement) {
  await act(async () => {
    fireEvent.click(within(alert).getByRole("button", { name: "Try again" }));
  });
  await flush();
}

const SNAPSHOT = {
  version: 1,
  points: [],
  counts: { items: 0, learningObjects: 0, concepts: 0, facets: 0 },
  stress: 0,
  facetField: { points: [], graphNodes: [], edges: [], layoutVersion: "v1", stress: 0, layoutValid: true, layoutWarning: null, nextGap: null },
  itemTextNeighbors: {}
};

function switchable<T>(value: T, error: Record<string, unknown>) {
  const state = { fail: true };
  const fn = vi.fn(async () => {
    if (state.fail) throw { ...error };
    return value;
  });
  return { state, fn };
}

const TIMEOUT = { code: "sidecar_timeout", message: "The read timed out.", retryable: true };

// ── 1. A self-contained retry, and identity by source ──────────────────

describe("every actionable error has an identity and a self-contained retry (items 1 and 2)", () => {
  it("Strata, then Terrain, then Try again: the history is read again; the error stays until it succeeds", async () => {
    stubs.api.getKnowledgeMap = vi.fn(async () => SNAPSHOT);
    const history = switchable({ version: 1, attempts: [], learningObjects: [] }, TIMEOUT);
    stubs.api.getKnowledgeMapHistory = history.fn;
    await launch();
    await openUnderTheHood("Analyst views");
    await view("strata");
    await waitFor(() => expect(alertWith("The read timed out.")).toHaveLength(1));
    await view("terrain");
    const before = history.fn.mock.calls.length;

    await tryAgain(alertWith("The read timed out.")[0]);
    expect(history.fn.mock.calls.length).toBe(before + 1);
    await waitFor(() => expect(alertWith("The read timed out.")).toHaveLength(1));

    history.state.fail = false;
    await tryAgain(alertWith("The read timed out.")[0]);
    expect(history.fn.mock.calls.length).toBe(before + 2);
    await waitFor(() => expect(alertWith("The read timed out.")).toHaveLength(0));
  });

  it("Well, then another view, then away: Try again reads the decay pressure again", async () => {
    stubs.api.getKnowledgeMap = vi.fn(async () => SNAPSHOT);
    const decay = switchable({ version: 1, pressure: null }, TIMEOUT);
    stubs.api.getDecayPressure = decay.fn;
    await launch();
    await openUnderTheHood("Analyst views");
    await view("well");
    await waitFor(() => expect(alertWith("The read timed out.")).toHaveLength(1));
    await view("terrain");
    await press({ key: "2", altKey: true });
    await screen.findByTestId("library-stub");
    const before = decay.fn.mock.calls.length;

    await tryAgain(alertWith("The read timed out.")[0]);
    expect(decay.fn.mock.calls.length).toBe(before + 1);
    await waitFor(() => expect(alertWith("The read timed out.")).toHaveLength(1));
    expect(within(alertWith("The read timed out.")[0]).getByRole("button", { name: "Try again" })).toBeTruthy();

    decay.state.fail = false;
    await tryAgain(alertWith("The read timed out.")[0]);
    expect(decay.fn.mock.calls.length).toBe(before + 2);
    await waitFor(() => expect(alertWith("The read timed out.")).toHaveLength(0));
  });

  it("keeps two failures with the same sentence from two sources, each with its own Try again", async () => {
    const UNAVAILABLE = { code: "sidecar_unavailable", message: "LearnLoop's engine is not responding.", retryable: true };
    const map = switchable(SNAPSHOT, UNAVAILABLE);
    const tree = switchable({ version: 1, root: "/vault", tree: [] }, UNAVAILABLE);
    stubs.api.getKnowledgeMap = map.fn;
    stubs.api.getVaultTree = tree.fn;
    await launch();
    await openUnderTheHood("Analyst views");
    await waitFor(() => expect(alertWith(UNAVAILABLE.message)).toHaveLength(1));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Files" }));
    });
    await waitFor(() => expect(alertWith(UNAVAILABLE.message)).toHaveLength(2));

    // Files comes back; the Analyst views failure is still there, still retryable.
    tree.state.fail = false;
    const treeCalls = tree.fn.mock.calls.length;
    const mapCalls = map.fn.mock.calls.length;
    await tryAgain(alertWith(UNAVAILABLE.message)[1]);
    expect(tree.fn.mock.calls.length).toBe(treeCalls + 1);
    expect(map.fn.mock.calls.length).toBe(mapCalls);
    await waitFor(() => expect(alertWith(UNAVAILABLE.message)).toHaveLength(1));

    map.state.fail = false;
    await tryAgain(alertWith(UNAVAILABLE.message)[0]);
    expect(map.fn.mock.calls.length).toBe(mapCalls + 1);
    await waitFor(() => expect(alertWith(UNAVAILABLE.message)).toHaveLength(0));
  });
});

// ── 2. Startup is the base shell until the snapshot names the shell ─────

describe("startup is the base shell until loadVault has named it (item 3)", () => {
  function deferLoad() {
    let release: () => void = () => undefined;
    stubs.loadGate = new Promise<void>((resolve) => (release = resolve));
    return async () => {
      await act(async () => {
        release();
      });
      await flush();
    };
  }

  async function altTwoBeforeLoad(): Promise<void> {
    render(<App />);
    await flush();
    // Nothing of the simple shell before the library has loaded.
    expect(screen.queryByRole("navigation", { name: "Places" })).toBeNull();
    await press({ key: "2", altKey: true });
  }

  it("a stale 'simple' cache, a classic library: Alt+2 before loading opens Today, as base", async () => {
    store.set("learnloop.shell", "simple");
    stubs.config = { ui: { shell: "classic" } };
    const load = deferLoad();
    await altTwoBeforeLoad();
    await load();
    expect(await screen.findByTestId("today-stub")).toBeTruthy();
    expect(screen.queryByTestId("library-stub")).toBeNull();
    expect(screen.queryByRole("navigation", { name: "Places" })).toBeNull();
  });

  it.each([
    ["nothing stored", () => storage(new Map())],
    ["storage that cannot be read", () => ({ ...storage(new Map()), getItem: () => { throw new Error("blocked"); } })]
  ])("missing storage (%s), a classic library: the same", async (_name, make) => {
    vi.stubGlobal("localStorage", make());
    stubs.config = { ui: { shell: "classic" } };
    const load = deferLoad();
    await altTwoBeforeLoad();
    await load();
    expect(await screen.findByTestId("today-stub")).toBeTruthy();
    expect(screen.queryByTestId("library-stub")).toBeNull();
  });

  it("a simple library: a key pressed before loading still does what base does", async () => {
    store.set("learnloop.shell", "simple");
    stubs.config = {};
    const load = deferLoad();
    await altTwoBeforeLoad();
    await load();
    // Base's Alt+2 is Today; the simple shell then shows its four places.
    const nav = await screen.findByRole("navigation", { name: "Places" });
    expect(within(nav).getByRole("button", { name: "Today" }).getAttribute("aria-current")).toBe("page");
    expect(screen.queryByTestId("library-stub")).toBeNull();
  });

  it("the simple shell's keys work once the snapshot has named it", async () => {
    stubs.config = {};
    await launch();
    await press({ key: "2", altKey: true });
    expect(await screen.findByTestId("library-stub")).toBeTruthy();
  });
});

// The palette is used above only to reach places; keep a direct use so a
// regression in it fails here too.
it("opens the palette in the simple shell after loading", async () => {
  await launch();
  await runPalette("analyst views");
  await waitFor(() => expect(screen.queryByRole("listbox", { name: "Commands" })).toBeNull());
});

// ── Fix round 6 (Low 3): the classic frames carry no key scopes ─────────
// Before the snapshot names a shell the App draws the base (classic) shell,
// but the config module's default shell is simple, so round 5's key scopes
// (keyScope) and target rule followed the default, and the loading frame's
// titlebar carried data-key-scope. They now follow the shell on screen.
describe("the loading and startup-error frames are classic through and through (fix round 6)", () => {
  it("draws no data-key-scope while the library loads", async () => {
    let release: () => void = () => undefined;
    stubs.loadGate = new Promise<void>((resolve) => (release = resolve));
    render(<App />);
    await flush();
    expect(document.querySelector(".titlebar")).not.toBeNull();
    expect(document.querySelectorAll("[data-key-scope]")).toHaveLength(0);
    await act(async () => release());
    await flush();
    // Once the snapshot names the simple shell, the titlebar is its own part.
    await screen.findByRole("navigation", { name: "Places" });
    expect(document.querySelector(".titlebar")?.getAttribute("data-key-scope")).toBe("window");
  });

  // Round-6 verify (Low): under React.StrictMode, as the owner runs the dev
  // app, the mount-only cleanup cleared the rendered-shell mirror right after
  // the first commit, so the classic loading frame's key scopes and target
  // rule fell back to the config's simple shell.
  it("keeps the loading frame classic under React.StrictMode, after its first commit too", async () => {
    stubs.loadGate = new Promise<void>(() => undefined);
    render(
      <StrictMode>
        <App />
      </StrictMode>
    );
    await flush();
    expect(activeShell()).toBe("classic");
    expect(screenLeavesKey(new KeyboardEvent("keydown", { key: "k", ctrlKey: true }))).toBe(false);
    expect(keyScope("window")).toEqual({});
  });


  it("draws no data-key-scope in the startup-error frame", async () => {
    stubs.loadFails = true;
    render(<App />);
    await screen.findByText(/could not be opened|Could not load/i);
    expect(document.querySelector(".titlebar")).not.toBeNull();
    expect(document.querySelectorAll("[data-key-scope]")).toHaveLength(0);
  });
});
