// UX Phase 2 (docs/specs/ux_learnloop_v1.md §5.1, §10 2.4): the palette lists
// plain commands first; the learnloop shell and its CLI pass-through need a
// leading ">", so plain words never run a CLI command (audit B.0). The
// classic shell keeps the palette exactly as it was.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const api = vi.hoisted(() => ({
  runCliCommand: vi.fn(async () => ({ stdout: "3 batches", stderr: "", exitCode: 0 })),
  getConceptGraph: vi.fn(async () => ({ concepts: [] })),
  goalsList: vi.fn(async () => ({ goals: [] })),
  getRuntimeHealth: vi.fn(async () => ({
    vaultLoaded: true,
    database: { ok: true, migrationsApplied: 217, latestMigration: 217 },
    codex: { ready: true, actualRevision: "abc", model: null, status: "ready" }
  }))
}));
vi.mock("../api/client", () => ({ api }));

import { CommandPalette, type PaletteCommand } from "./CommandPalette";

beforeEach(() => {
  const store = new Map<string, string>();
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

function commands(): PaletteCommand[] {
  return [
    { id: "add", label: "Add a book, paper or video", keys: "Ctrl+O", run: vi.fn() },
    { id: "continue", label: "Continue reading", hint: "Linear Algebra Done Right", run: vi.fn() },
    { id: "plan", label: "Start today's plan", run: vi.fn() },
    { id: "check", label: "Check what I already know", run: vi.fn() },
    { id: "settings", label: "Open settings", keys: "Ctrl+,", run: vi.fn() },
    { id: "underhood", label: "Under the hood", run: vi.fn() },
    { id: "tool:proposals", label: "Study-map changes", hint: "under the hood · was Proposals", keywords: ["proposals"], run: vi.fn() }
  ];
}

function renderPalette(shell: "simple" | "classic", plain = commands()) {
  const props = {
    open: true,
    session: null,
    entityIds: [],
    practiceItemIds: [],
    subjects: [],
    onClose: vi.fn(),
    onGoto: vi.fn(),
    onOpenPractice: vi.fn(),
    onOpenCalibration: vi.fn(),
    onOpenAdjudication: vi.fn(),
    onInspect: vi.fn(),
    onAsk: vi.fn(() => false),
    onError: vi.fn()
  };
  render(<CommandPalette {...props} shell={shell} plainCommands={plain} />);
  return { props, plain };
}

function input(): HTMLInputElement {
  return screen.getByRole("textbox") as HTMLInputElement;
}

async function typeAndEnter(value: string) {
  fireEvent.change(input(), { target: { value, selectionStart: value.length } });
  await act(async () => {
    fireEvent.keyDown(input(), { key: "Enter" });
  });
}

describe("simple shell", () => {
  it("opens on the plain commands, in order, before anything else", () => {
    renderPalette("simple");
    const options = screen.getAllByRole("option").map((option) => option.querySelector(".palette-label")?.textContent);
    expect(options).toEqual([
      "Add a book, paper or video",
      "Continue reading",
      "Start today's plan",
      "Check what I already know",
      "Open settings",
      "Under the hood",
      "Study-map changes"
    ]);
    expect(screen.getByText(/> for learnloop commands/)).toBeTruthy();
  });

  it("filters by words, including an old name, and runs the chosen command on Enter", async () => {
    const { plain, props } = renderPalette("simple");
    await typeAndEnter("proposals");
    expect(plain[6].run).toHaveBeenCalledTimes(1);
    expect(props.onClose).toHaveBeenCalled();
    expect(api.runCliCommand).not.toHaveBeenCalled();
  });

  it("never runs a CLI command for plain words", async () => {
    renderPalette("simple");
    await typeAndEnter("doctor");
    await typeAndEnter("accept 01ABC");
    expect(api.runCliCommand).not.toHaveBeenCalled();
    expect(api.getRuntimeHealth).not.toHaveBeenCalled();
    expect(screen.getByText(/No command matches/)).toBeTruthy();
  });

  it("runs the learnloop shell behind '>', CLI pass-through included", async () => {
    renderPalette("simple");
    await typeAndEnter("> proposals");
    expect(api.runCliCommand).toHaveBeenCalledWith(["proposals"]);
    await typeAndEnter(">doctor");
    expect(api.getRuntimeHealth).toHaveBeenCalled();
  });

  it("completes shell commands after '>'", () => {
    renderPalette("simple");
    fireEvent.change(input(), { target: { value: "> doc", selectionStart: 5 } });
    expect(screen.getByText("doctor", { selector: ".cli-completion-text" })).toBeTruthy();
    fireEvent.keyDown(input(), { key: "Tab" });
    expect(input().value).toBe("> doctor ");
  });

  it("moves through the list with the arrows", async () => {
    const { plain } = renderPalette("simple");
    fireEvent.keyDown(input(), { key: "ArrowDown" });
    fireEvent.keyDown(input(), { key: "ArrowDown" });
    await act(async () => {
      fireEvent.keyDown(input(), { key: "Enter" });
    });
    expect(plain[2].run).toHaveBeenCalledTimes(1);
  });
});

describe("classic shell (unchanged)", () => {
  it("runs plain words as learnloop commands, as before", async () => {
    renderPalette("classic");
    await typeAndEnter("proposals");
    expect(api.runCliCommand).toHaveBeenCalledWith(["proposals"]);
    expect(screen.queryByRole("option")).toBeNull();
  });
});
