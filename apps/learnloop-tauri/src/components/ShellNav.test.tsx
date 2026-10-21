// UX Phase 2 (docs/specs/ux_learnloop_v1.md §5.1, §10 2.1/2.5): the simple
// nav (four places, + Add, ^K, ⋯) and the classic nav, pinned byte for byte
// against the base shell (c80c54cbb): the snapshot below was recorded there,
// before any Phase 2 change.
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@tauri-apps/plugin-dialog", () => ({ open: vi.fn(async () => null) }));

import { TerminalFrame } from "./ui";
import { ShellChromeRoot } from "../app/ShellChromeRoot";

beforeEach(() => {
  const store = new Map<string, string>([["learnloop.recentVaults", JSON.stringify(["/home/u/LearnLoop", "/home/u/old-notes"])]]);
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

describe("classic (ui.shell = 'classic')", () => {
  it("renders the base shell's ten-tab nav exactly", () => {
    const { container } = render(
      <TerminalFrame
        shell="classic"
        active="today"
        onTab={() => undefined}
        aiReady
        vaultRoot="/home/u/LearnLoop"
        onSelectVault={() => undefined}
        badges={{ proposals: 41, maintain: 3 }}
        onAdd={() => undefined}
      >
        <div>body</div>
      </TerminalFrame>
    );
    expect(container.querySelector("nav")?.outerHTML).toMatchSnapshot();
  });

  it("is the default when no shell is named (screens and tests that predate Phase 2)", () => {
    render(
      <TerminalFrame active="start" onTab={() => undefined} aiReady={false} onSelectVault={() => undefined}>
        <div>body</div>
      </TerminalFrame>
    );
    expect(screen.getByRole("button", { name: /\[1\]\s*Start/ })).toBeTruthy();
    expect(screen.getByRole("button", { name: /\[0\]\s*Maintain/ })).toBeTruthy();
  });
});

function renderSimple(overrides: Partial<Parameters<typeof TerminalFrame>[0]["simpleNav"] & object> = {}) {
  const handlers = {
    onPlace: vi.fn(),
    onPalette: vi.fn(),
    onSettings: vi.fn(),
    onUnderTheHood: vi.fn(),
    onKeyboardHelp: vi.fn(),
    onNewLibrary: vi.fn(),
    onFixGrading: vi.fn()
  };
  const onSelectVault = vi.fn();
  const onAdd = vi.fn();
  // The App draws the simple shell inside its key-isolated chrome root (fix round 4).
  const utils = render(
    <ShellChromeRoot>
    <TerminalFrame
      shell="simple"
      active="graph"
      onTab={() => undefined}
      aiReady={false}
      vaultRoot="/home/u/LearnLoop"
      onSelectVault={onSelectVault}
      badges={{ proposals: 41, maintain: 3 }}
      onAdd={onAdd}
      simpleNav={{ active: "progress", ...handlers, ...overrides }}
    >
      <div>body</div>
    </TerminalFrame>
    </ShellChromeRoot>
  );
  return { ...utils, handlers, onSelectVault, onAdd };
}

describe("simple (the default)", () => {
  it("shows four places, + Add, ^K and ⋯ and nothing else", () => {
    renderSimple();
    const nav = screen.getByRole("navigation");
    const labels = within(nav).getAllByRole("button").map((button) => button.textContent?.trim());
    expect(labels).toEqual(["Today", "Library", "Reader", "Progress", "+ Add", "^K", "⋯"]);
    // No vault chip, no settings chip, no badge in the bar (§5.2: "There is no top-nav badge").
    expect(nav.textContent).not.toMatch(/LearnLoop|Alt\+S|41|Ingest|Proposals|Maintain/);
  });

  it("marks the current place and puts its key in the tooltip, not the label (Q10)", () => {
    renderSimple();
    const progress = screen.getByRole("button", { name: "Progress" });
    expect(progress.getAttribute("aria-current")).toBe("page");
    expect(progress.getAttribute("title")).toBe("Progress (Alt+4)");
    expect(screen.getByRole("button", { name: "Today" }).getAttribute("aria-current")).toBeNull();
  });

  it("goes to a place, opens Add and the palette", () => {
    const { handlers, onAdd } = renderSimple();
    fireEvent.click(screen.getByRole("button", { name: "Library" }));
    expect(handlers.onPlace).toHaveBeenCalledWith("library");
    fireEvent.click(screen.getByRole("button", { name: "+ Add" }));
    expect(onAdd).toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "^K" }));
    expect(handlers.onPalette).toHaveBeenCalled();
  });

  it("holds Settings, Under the hood, Switch library and Keyboard & help in ⋯", () => {
    const { handlers, onSelectVault } = renderSimple();
    fireEvent.click(screen.getByRole("button", { name: "⋯" }));
    const menu = screen.getByRole("menu");
    const items = within(menu).getAllByRole("menuitem").map((item) => item.textContent?.trim());
    expect(items).toEqual([
      "Settings Ctrl+,",
      "Under the hood",
      "LearnLoop",
      "old-notes",
      "Open another library…",
      "New library…",
      "Keyboard & help"
    ]);
    expect(within(menu).getByText(/Switch library/)).toBeTruthy();
    fireEvent.click(within(menu).getByRole("menuitem", { name: "old-notes" }));
    expect(onSelectVault).toHaveBeenCalledWith("/home/u/old-notes");
    expect(screen.queryByRole("menu")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "⋯" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Under the hood" }));
    expect(handlers.onUnderTheHood).toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "⋯" }));
    fireEvent.click(screen.getByRole("menuitem", { name: /Settings/ }));
    expect(handlers.onSettings).toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "⋯" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Keyboard & help" }));
    expect(handlers.onKeyboardHelp).toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "⋯" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "New library…" }));
    expect(handlers.onNewLibrary).toHaveBeenCalled();
  });

  it("closes ⋯ on Escape without letting the screen beneath see the key", () => {
    renderSimple();
    const beneath = vi.fn();
    window.addEventListener("keydown", beneath);
    fireEvent.click(screen.getByRole("button", { name: "⋯" }));
    act(() => {
      fireEvent.keyDown(screen.getByRole("menu"), { key: "Escape" });
    });
    expect(screen.queryByRole("menu")).toBeNull();
    expect(beneath).not.toHaveBeenCalled();
    window.removeEventListener("keydown", beneath);
  });

  it("says when grading isn't working, and only then", () => {
    const { handlers, unmount } = renderSimple({ gradingTrouble: true });
    fireEvent.click(screen.getByRole("button", { name: /Grading isn't working · Fix/ }));
    expect(handlers.onFixGrading).toHaveBeenCalled();
    unmount();
    renderSimple({ gradingTrouble: false });
    expect(screen.queryByText(/Grading isn't working/)).toBeNull();
  });
});
