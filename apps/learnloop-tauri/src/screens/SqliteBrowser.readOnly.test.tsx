// UX Phase 2, Codex review of ux-phase2-shell.
//
// F1 (docs/specs/ux_learnloop_v1.md §5.2, Q18): Under the hood → Data opens
// the library's database read-only; every change (a cell edit, + row, a
// row's ✕, the SQL console) waits behind *Allow edits*. The Library's own
// SQLite view outside the simple shell keeps the browser as it was.
//
// F8: the grid's vim keys must not take a modified key, so Ctrl+K (the
// palette) still reaches the shell while the grid has the focus.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const api = vi.hoisted(() => ({
  sqliteTables: vi.fn(async () => ({ version: 1, path: "state.sqlite", tables: [{ name: "notes", rowCount: 2 }] })),
  sqliteTable: vi.fn(async () => ({
    version: 1,
    path: "state.sqlite",
    table: "notes",
    columns: [
      { name: "id", type: "INTEGER", pk: true, notnull: true },
      { name: "body", type: "TEXT", pk: false, notnull: false }
    ],
    primaryKey: ["id"],
    rowCount: 2,
    editable: true,
    rows: [
      { rowid: 1, cells: [1, "first"] },
      { rowid: 2, cells: [2, "second"] }
    ]
  })),
  sqliteDeleteRow: vi.fn(async () => ({ ok: true })),
  sqliteInsertRow: vi.fn(async () => ({ ok: true })),
  sqliteUpdateCell: vi.fn(async () => ({ ok: true })),
  sqliteExec: vi.fn(async () => ({ version: 1, kind: "rows", columns: ["n"], rows: [[1]], truncated: false })),
  getVaultTree: vi.fn(async () => ({ tree: [{ type: "file", name: "state.sqlite", path: "state.sqlite", kind: "sqlite" }] }))
}));
vi.mock("../api/client", () => ({ api }));

import { setAlgoConfig } from "../app/algoConfig";
import { matchShellKey } from "../app/keymap";
import { SqliteBrowser } from "./SqliteBrowser";
import { DataTool } from "./underhood/tools";
import { Suspense } from "react";

beforeEach(() => {
  vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => {
    callback(0);
    return 0;
  });
  // jsdom draws no layout, so it has no scrollIntoView.
  Element.prototype.scrollIntoView = () => undefined;
  for (const fn of Object.values(api)) fn.mockClear();
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

async function mount(editGate: boolean) {
  render(<SqliteBrowser path="state.sqlite" onError={vi.fn()} {...(editGate ? { editGate: true } : {})} />);
  await screen.findByText("first");
}

describe("Data opens read-only (F1)", () => {
  it("shows no ✕, no + row and no SQL console until edits are allowed", async () => {
    await mount(true);
    expect(screen.queryByTitle("delete row")).toBeNull();
    expect(screen.queryByText("+ row")).toBeNull();
    expect(screen.queryByPlaceholderText(/SELECT/)).toBeNull();
    const toggle = screen.getByRole("checkbox", { name: /allow edits/i }) as HTMLInputElement;
    expect(toggle.checked).toBe(false);
    // Enter on a cell does not open an edit either.
    const grid = screen.getByRole("grid");
    fireEvent.keyDown(grid, { key: "Enter" });
    expect(screen.queryByText("EDIT")).toBeNull();
    expect(api.sqliteDeleteRow).not.toHaveBeenCalled();
    expect(api.sqliteExec).not.toHaveBeenCalled();
  });

  it("offers the edits once Allow edits is on", async () => {
    await mount(true);
    fireEvent.click(screen.getByRole("checkbox", { name: /allow edits/i }));
    const remove = screen.getAllByTitle("delete row")[0];
    await act(async () => {
      fireEvent.click(remove);
    });
    expect(api.sqliteDeleteRow).toHaveBeenCalledWith("state.sqlite", "notes", 1);
    expect(screen.getByPlaceholderText(/SELECT/)).toBeTruthy();
  });

  it("keeps the browser as it was where no gate is asked for", async () => {
    await mount(false);
    expect(screen.queryByRole("checkbox", { name: /allow edits/i })).toBeNull();
    expect(screen.getAllByTitle("delete row")).toHaveLength(2);
    expect(screen.getByPlaceholderText(/SELECT/)).toBeTruthy();
  });
});

describe("the grid leaves modified keys to the shell (F8)", () => {
  it("lets Ctrl+K reach the palette and does not move the selection", async () => {
    const seen: string[] = [];
    const onWindowKey = (event: KeyboardEvent) => {
      const binding = matchShellKey(event, "simple", false);
      if (binding) seen.push(binding.id);
    };
    window.addEventListener("keydown", onWindowKey);
    try {
      await mount(true);
      const grid = screen.getByRole("grid");
      grid.focus();
      // Move down to the second row first, so a stolen Ctrl+K ("k" = up) shows.
      fireEvent.keyDown(grid, { key: "j" });
      const selectedBefore = document.querySelector("[aria-selected='true']")?.textContent;
      fireEvent.keyDown(grid, { key: "k", ctrlKey: true });
      expect(seen).toContain("palette.ctrl-k");
      expect(document.querySelector("[aria-selected='true']")?.textContent).toBe(selectedBefore);
      // Plain k still moves up.
      fireEvent.keyDown(grid, { key: "k" });
      expect(document.querySelector("[aria-selected='true']")?.textContent).not.toBe(selectedBefore);
    } finally {
      window.removeEventListener("keydown", onWindowKey);
    }
  });
});

describe("Under the hood → Data", () => {
  it("mounts the browser behind Allow edits", async () => {
    render(
      <Suspense fallback={null}>
        <DataTool onError={vi.fn()} />
      </Suspense>
    );
    await screen.findByText("first");
    expect((screen.getByRole("checkbox", { name: /allow edits/i }) as HTMLInputElement).checked).toBe(false);
    expect(screen.queryByTitle("delete row")).toBeNull();
  });
});

// Fix round 2 (whole-stage verify 20261021-114726-Jrt7sA, item 1): F8's
// modifier guard applies only in the simple shell. Classic's browser takes
// Ctrl/Cmd/Alt + its keys exactly as the base did (c80c54cbb): Ctrl+K and
// Ctrl+ArrowUp move the selection up.
describe("classic keeps the grid's modified keys (fix round 2)", () => {
  beforeEach(() => {
    setAlgoConfig({ ui: { shell: "classic" } });
  });
  afterEach(() => {
    setAlgoConfig({});
  });

  const selectedText = () => document.querySelector("[aria-selected='true']")?.textContent;

  it.each([
    ["Ctrl+K", { key: "k", ctrlKey: true }],
    ["Ctrl+ArrowUp", { key: "ArrowUp", ctrlKey: true }],
    ["Cmd+K", { key: "k", metaKey: true }],
    ["Alt+ArrowUp", { key: "ArrowUp", altKey: true }]
  ])("moves the selection up on %s, as the base did", async (_name, init) => {
    await mount(false);
    const grid = screen.getByRole("grid");
    grid.focus();
    const top = selectedText();
    fireEvent.keyDown(grid, { key: "j" });
    const second = selectedText();
    expect(second).not.toBe(top);
    fireEvent.keyDown(grid, init);
    expect(selectedText()).toBe(top);
  });

  it("moves down on Ctrl+J and Ctrl+ArrowDown too", async () => {
    await mount(false);
    const grid = screen.getByRole("grid");
    grid.focus();
    const top = selectedText();
    fireEvent.keyDown(grid, { key: "j", ctrlKey: true });
    expect(selectedText()).not.toBe(top);
    fireEvent.keyDown(grid, { key: "k" });
    expect(selectedText()).toBe(top);
    fireEvent.keyDown(grid, { key: "ArrowDown", ctrlKey: true });
    expect(selectedText()).not.toBe(top);
  });
});
