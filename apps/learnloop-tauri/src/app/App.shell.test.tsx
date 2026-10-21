// UX Phase 2 (docs/specs/ux_learnloop_v1.md §5, §7.7, §7.9, §10 2.1–2.5): the
// App shell itself, with every screen a stub (the demoted screens mount
// unchanged; only their entry points move). The classic nav's snapshot was
// recorded on the base shell (c80c54cbb) before any Phase 2 change.
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const stubs = vi.hoisted(() => ({
  config: {} as Record<string, unknown>,
  readerOpensBook: false,
  readerError: null as string | null
}));

vi.mock("@tauri-apps/api/event", () => ({ listen: vi.fn(async () => () => undefined) }));
vi.mock("@tauri-apps/plugin-dialog", () => ({ open: vi.fn(async () => null) }));
vi.mock("../components/useSourceFileDrop", () => ({ useSourceFileDrop: () => false, pickSourceFiles: async () => [] }));

vi.mock("../api/client", () => {
  const card = { sourceId: "src_axler", title: "Linear Algebra Done Right" };
  const api = new Proxy(
    {
      loadVault: vi.fn(async () => ({
        vault: { root: "/vault", subjects: [], subjectTitles: [], counts: { learningObjects: 1, practiceItems: 1 }, algorithmVersion: "mvp-0.29" },
        health: { ai: { ready: false, settingsReady: false, manualGrading: false, activeProvider: null }, codex: { ready: false } },
        config: stubs.config,
        activeSession: null,
        streak: null
      })),
      getSourceLibrary: vi.fn(async () => ({ sources: [card], pending: [] }))
    } as Record<string, unknown>,
    { get: (target, name: string) => (name in target ? target[name] : () => new Promise(() => undefined)) }
  );
  return { api };
});

function stub(name: string) {
  return () => <div data-testid={name}>{name}</div>;
}

vi.mock("../screens/ReaderScreen", async () => {
  const React = await import("react");
  return {
    ReaderScreen: ({
      onSourceChange,
      onError
    }: {
      onSourceChange?: (source: unknown) => void;
      onError: (message: string) => void;
    }) => {
      React.useEffect(() => {
        if (stubs.readerOpensBook) onSourceChange?.({ card: { sourceId: "src_axler", title: "Linear Algebra Done Right" }, spanId: null });
        if (stubs.readerError) onError(stubs.readerError);
      }, [onSourceChange, onError]);
      return <div data-testid="reader-stub">reader</div>;
    }
  };
});
vi.mock("../screens/LibraryPlace", () => ({ LibraryPlace: stub("library-stub") }));
vi.mock("../screens/StartScreen", () => ({ StartScreen: stub("start-stub") }));
vi.mock("../screens/TodayScreen", () => ({ TodayScreen: stub("today-stub") }));
vi.mock("../screens/GraphScreen", () => ({ GraphScreen: stub("graph-stub") }));
vi.mock("../screens/KnowledgeMapScreen", () => ({ KnowledgeMapView: stub("knowledge-stub") }));
vi.mock("../screens/IngestScreen", () => ({ IngestScreen: stub("ingest-stub") }));
vi.mock("../screens/ProposalsScreen", () => ({ ProposalsScreen: stub("proposals-stub") }));
vi.mock("../screens/RegistryReviewScreen", () => ({ RegistryReviewScreen: stub("registry-stub") }));
vi.mock("../screens/MaintenanceScreen", () => ({ MaintenanceScreen: stub("maintain-stub") }));
vi.mock("../screens/LibraryScreen", () => ({ LibraryScreen: stub("files-stub") }));
vi.mock("../screens/SettingsScreen", () => ({ SettingsOverlay: stub("settings-stub") }));
vi.mock("../screens/ReviewScreen", () => ({
  ReviewScreen: ({ onClose }: { onClose: () => void }) => (
    <button type="button" data-testid="review-stub" onClick={onClose}>
      close review
    </button>
  )
}));
vi.mock("../screens/reader/WrapUpOffer", () => ({ WrapUpOffer: () => null }));

import { App } from "./App";

let store: Map<string, string>;

beforeEach(() => {
  stubs.config = {};
  stubs.readerOpensBook = false;
  stubs.readerError = null;
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
});
afterEach(() => {
  cleanup();
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

describe("classic (ui.shell = 'classic')", () => {
  beforeEach(() => {
    stubs.config = { ui: { shell: "classic" } };
  });

  it("keeps the base shell's nav byte for byte", async () => {
    await launch();
    expect(document.querySelector("nav.top-nav")?.outerHTML).toMatchSnapshot();
  });

  it("keeps the base keys: Alt+3 Graph, Alt+4 Ingest, no Ctrl+K", async () => {
    await launch();
    await press({ key: "3", altKey: true });
    expect(await screen.findByTestId("graph-stub")).toBeTruthy();
    await press({ key: "4", altKey: true });
    expect(await screen.findByTestId("ingest-stub")).toBeTruthy();
    expect(screen.queryByRole("navigation", { name: "Under the hood" })).toBeNull();
    await press({ key: "k", ctrlKey: true });
    expect(screen.queryByText(/learnloop/, { selector: ".cli-title" })).toBeNull();
    await press({ key: "p", ctrlKey: true });
    expect(screen.getByText(/learnloop/, { selector: ".cli-title" })).toBeTruthy();
  });
});

describe("simple (the default)", () => {
  it("opens on Today with the four places", async () => {
    await launch();
    const nav = screen.getByRole("navigation", { name: "Places" });
    expect(within(nav).getByRole("button", { name: "Today" }).getAttribute("aria-current")).toBe("page");
    expect(within(nav).queryByText(/Ingest|Proposals|Registry|Maintain/)).toBeNull();
  });

  it("goes to the places on Alt+1…4", async () => {
    await launch();
    await press({ key: "4", altKey: true });
    expect(await screen.findByTestId("graph-stub")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Progress" }).getAttribute("aria-current")).toBe("page");
    await press({ key: "2", altKey: true });
    expect(await screen.findByTestId("library-stub")).toBeTruthy();
    await press({ key: "3", altKey: true });
    expect(await screen.findByTestId("reader-stub")).toBeTruthy();
    await press({ key: "1", altKey: true });
    expect(await screen.findByTestId("start-stub")).toBeTruthy();
  });

  it("opens Under the hood from ⋯, on the last tool used, with the demoted screens unchanged", async () => {
    await launch();
    // Alt+0 was Maintain: it opens System health under the hood.
    await press({ key: "0", altKey: true });
    expect(await screen.findByTestId("maintain-stub")).toBeTruthy();
    expect(screen.getByRole("heading", { level: 2 }).textContent).toBe("System health");
    expect(screen.getByText("was Maintain")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Imports & builds" }));
    expect(await screen.findByTestId("ingest-stub")).toBeTruthy();
    await press({ key: "1", altKey: true });
    await screen.findByTestId("start-stub");
    fireEvent.click(screen.getByRole("button", { name: "⋯" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Under the hood" }));
    expect(await screen.findByTestId("ingest-stub")).toBeTruthy();
    // Alt+5 was Proposals.
    await press({ key: "5", altKey: true });
    expect(await screen.findByTestId("proposals-stub")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Files" }));
    expect(await screen.findByTestId("files-stub")).toBeTruthy();
  });

  it("opens the mistake history when it is picked, not when Under the hood is reopened on it", async () => {
    await launch();
    await press({ key: "0", altKey: true });
    await screen.findByTestId("maintain-stub");
    fireEvent.click(screen.getByRole("button", { name: "Mistake history" }));
    fireEvent.click(await screen.findByTestId("review-stub"));
    expect(screen.queryByTestId("review-stub")).toBeNull();
    await press({ key: "1", altKey: true });
    await screen.findByTestId("start-stub");
    fireEvent.click(screen.getByRole("button", { name: "⋯" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Under the hood" }));
    expect(await screen.findByRole("button", { name: "open mistake history" })).toBeTruthy();
    expect(screen.queryByTestId("review-stub")).toBeNull();
  });

  it("remembers the last place across a restart", async () => {
    await launch();
    await press({ key: "4", altKey: true });
    await screen.findByTestId("graph-stub");
    cleanup();
    render(<App />);
    expect(await screen.findByTestId("graph-stub")).toBeTruthy();
  });

  it("reopens the book that was open in the Reader", async () => {
    stubs.readerOpensBook = true;
    await launch();
    await press({ key: "3", altKey: true });
    await screen.findByTestId("reader-stub");
    expect(store.get("learnloop.place")).toBe("reader");
    cleanup();
    stubs.readerOpensBook = false;
    render(<App />);
    expect(await screen.findByTestId("reader-stub")).toBeTruthy();
    expect(Array.from(store.keys()).some((key) => key.startsWith("learnloop.reader.book"))).toBe(true);
  });

  it("opens the palette on Ctrl+K and Ctrl+, opens settings", async () => {
    await launch();
    await press({ key: "k", ctrlKey: true });
    expect(screen.getByRole("listbox", { name: "Commands" })).toBeTruthy();
    fireEvent.keyDown(screen.getByRole("textbox"), { key: "Escape" });
    await press({ key: ",", ctrlKey: true });
    expect(await screen.findByTestId("settings-stub")).toBeTruthy();
  });

  it("holds a notice while a book is open in the Reader and delivers it at the destination", async () => {
    stubs.readerOpensBook = true;
    await launch();
    await press({ key: "3", altKey: true });
    await screen.findByTestId("reader-stub");
    await press({ key: "k", ctrlKey: true });
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "ask the tutor" } });
    await act(async () => {
      fireEvent.keyDown(screen.getByRole("textbox"), { key: "Enter" });
    });
    expect(screen.queryByText(/ask from its Ask tab/)).toBeNull();
    await press({ key: "2", altKey: true });
    await screen.findByTestId("library-stub");
    expect(screen.getByText(/In the Reader, ask from its Ask tab/)).toBeTruthy();
  });

  it("shows errors in the Reader, red", async () => {
    stubs.readerOpensBook = true;
    stubs.readerError = "Could not load this section.";
    await launch();
    await press({ key: "3", altKey: true });
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("Could not load this section.");
  });
});
