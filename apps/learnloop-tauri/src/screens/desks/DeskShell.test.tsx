// DeskShell in jsdom (spec §18.2): the key router reaching the workspace, the writes the outbox sends,
// a conflict taking the server's state, first-run desks, the typing scope, hidden desks and which-key.
// Layout, pixels and real iframes are the real-webview harness's (scripts/desk_harness/run.py).
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useEffect } from "react";
import type { DeskStateDto, SourceLibraryCard } from "../../api/dto";
import { FixtureDeskServer, fixtureDeskState } from "../../fixtures/desks/workspace";
import { FIXTURE_LIBRARY, FIXTURE_SOURCES } from "../../fixtures/desks/sources";
import { DeskShell, type DeskTransport, type PaneRenderInput } from "./DeskShell";
import { useListenerHub } from "./lifecycle";

vi.mock("../../api/client", () => ({ api: {} }));
vi.mock("./windows/SourceWindow", () => ({ SourceWindow: () => null }));
vi.mock("./windows/PanelWindow", () => ({ PANEL_TITLES: { guide: "Guide", notes: "Notes", path: "Reading path", library: "Library" }, LibraryPanel: () => null, PathPanel: () => null, RailHostPanel: () => null }));

const heardKeys: Record<string, string[]> = {};

/** A pane that shows its lifecycle state and records the keys its window-level listener hears. */
function Pane({ input }: { input: PaneRenderInput }) {
  const hub = useListenerHub();
  const id = input.window.windowId;
  useEffect(() => hub.listen("window", "keydown", (event: KeyboardEvent) => {
    (heardKeys[id] ??= []).push(event.key);
  }), [hub, id]);
  return <div data-testid={`pane-${id}`} data-state={input.lifecycle.state}>{id}</div>;
}

function transportFor(server: FixtureDeskServer, library: SourceLibraryCard[] = FIXTURE_LIBRARY): DeskTransport & { applied: number } {
  const transport = {
    applied: 0,
    state: async () => server.state(),
    apply: async (input: Parameters<FixtureDeskServer["apply"]>[0]) => {
      transport.applied += 1;
      return server.apply(input);
    },
    library: async () => library,
    resolveExtraction: async (sourceId: string) => Object.values(FIXTURE_SOURCES).find((source) => source.sourceId === sourceId)?.extractionId ?? sourceId,
  };
  return transport;
}

let mintCount = 0;
const mint = (prefix: string) => `${prefix}_${++mintCount}`;

function mount(server = new FixtureDeskServer(), props: Partial<Parameters<typeof DeskShell>[0]> = {}) {
  const transport = transportFor(server);
  const onError = vi.fn();
  const view = render(
    <DeskShell
      vaultKey={`vault-${Math.random()}`}
      onError={onError}
      transport={transport}
      renderPane={(input) => <Pane input={input} />}
      initialViewport={{ width: 1600, height: 960 }}
      mintId={mint}
      {...props}
    />,
  );
  return { server, transport, onError, view };
}

function state(id: string): string | null {
  return screen.getByTestId(`pane-${id}`).getAttribute("data-state");
}

function alt(code: string, key: string, init: KeyboardEventInit = {}, target: Window | HTMLElement = window) {
  act(() => {
    fireEvent.keyDown(target, { key: "Alt", code: "AltLeft", altKey: true });
    fireEvent.keyDown(target, { key, code, altKey: true, ...init });
    fireEvent.keyUp(target, { key, code, altKey: true, ...init });
    fireEvent.keyUp(target, { key: "Alt", code: "AltLeft" });
  });
}

async function flush() {
  await act(async () => {
    vi.advanceTimersByTime(300);
    await Promise.resolve();
  });
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  for (const key of Object.keys(heardKeys)) delete heardKeys[key];
  const values = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => void values.set(key, value),
    removeItem: (key: string) => void values.delete(key),
    clear: () => values.clear(),
  });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("the desks on screen", () => {
  it("reads desk.state and gives each window its lifecycle state", async () => {
    mount();
    await screen.findByTestId("pane-fx_w_book");
    expect(state("fx_w_book")).toBe("active");
    expect(state("fx_w_video")).toBe("visible");
    expect(state("fx_w_paper")).toBe("offscreen");
    // The other desks are not mounted until visited.
    expect(screen.queryByTestId("pane-fx_w_video2")).toBeNull();
  });

  it("alt+h/l, alt+], alt+, and alt+. reach the workspace, and the outbox sends them in order", async () => {
    const { server } = mount();
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyL", "l");
    expect(state("fx_w_video")).toBe("active");
    alt("BracketRight", "]");
    alt("Comma", ",");
    await flush();
    const desk = server.state().desks[0];
    expect(desk.slots.map((slot) => slot.windows.map((window) => window.windowId))).toEqual([
      ["fx_w_book"], ["fx_w_paper"], ["fx_w_video", "fx_w_guide"], ["fx_w_path"], ["fx_w_pads"],
    ]);
    // One batch per change, numbered in order; each op expects the version the one before it left.
    expect(server.batches.map((batch) => batch.seq)).toEqual([1, 2, 3]);
    expect(server.batches.flatMap((batch) => batch.ops).map((op) => [op.op, op.expectedVersion])).toEqual([
      ["set_focus", 1], ["move_window", 2], ["pair", 3],
    ]);
    alt("Period", ".");
    await flush();
    expect(server.state().desks[0].slots.map((slot) => slot.windows.length)).toEqual([1, 1, 1, 1, 1, 1]);
    expect(server.batches.map((batch) => batch.seq)).toEqual([1, 2, 3, 4]);
  });

  it("a conflict takes the server's state", async () => {
    const server = new FixtureDeskServer();
    mount(server);
    await screen.findByTestId("pane-fx_w_book");
    // Another installation moved the paper to the front meanwhile.
    server.apply({ clientId: "other-device", seq: 1, ops: [{ op: "move_window", deskId: "fx_desk_softmax", windowId: "fx_w_paper", toSlot: 0, expectedVersion: 1 }] });
    alt("BracketRight", "]");
    await flush();
    await waitFor(() => expect(screen.getAllByText(/fx_w_/).map((node) => node.textContent)[0]).toBe("fx_w_paper"));
    const order = server.state().desks[0].slots.map((slot) => slot.windows[0].windowId);
    expect(order[0]).toBe("fx_w_paper");
  });

  it("alt+w closes the focused window; the shelf's undo puts it back in its slot", async () => {
    const { server } = mount();
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyW", "w");
    expect(screen.queryByTestId("pane-fx_w_book")).toBeNull();
    expect(state("fx_w_video")).toBe("active");
    fireEvent.click(screen.getByRole("button", { name: /undo close/ }));
    await flush();
    expect(state("fx_w_book")).toBe("active");
    expect(server.state().desks[0].slots[0].windows[0].windowId).toBe("fx_w_book");
  });

  it("alt+j past a lone window goes to the desk below: its windows become active, the first desk's hidden", async () => {
    mount();
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyJ", "j");
    await screen.findByTestId("pane-fx_w_video2");
    expect(state("fx_w_video2")).toBe("active");
    expect(state("fx_w_book")).toBe("hidden");
    alt("KeyK", "k");
    expect(state("fx_w_book")).toBe("active");
  });
});

describe("the key router", () => {
  it("only the active window hears keys; a hidden desk's window hears none", async () => {
    mount();
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyJ", "j");
    await screen.findByTestId("pane-fx_w_video2");
    act(() => {
      fireEvent.keyDown(window, { key: "q", code: "KeyQ" });
    });
    expect(heardKeys.fx_w_video2).toContain("q");
    expect(heardKeys.fx_w_book ?? []).not.toContain("q");
    expect(heardKeys.fx_w_video ?? []).not.toContain("q");
  });

  it("while typing, a bare x stays in the field and alt+l still moves the focus", async () => {
    mount();
    await screen.findByTestId("pane-fx_w_book");
    const box = document.createElement("input");
    document.body.appendChild(box);
    const x = new KeyboardEvent("keydown", { key: "x", code: "KeyX", bubbles: true, cancelable: true });
    act(() => {
      box.dispatchEvent(x);
    });
    expect(x.defaultPrevented).toBe(false);
    alt("KeyL", "l", {}, box);
    expect(state("fx_w_video")).toBe("active");
    box.remove();
  });

  it("x swaps the two windows in view", async () => {
    const { server } = mount();
    await screen.findByTestId("pane-fx_w_book");
    act(() => {
      fireEvent.keyDown(window, { key: "x", code: "KeyX" });
    });
    await flush();
    expect(server.state().desks[0].slots.slice(0, 2).map((slot) => slot.windows[0].windowId)).toEqual(["fx_w_video", "fx_w_book"]);
  });

  it("a chord whose feature comes later is not taken: it goes on to the window", async () => {
    mount();
    await screen.findByTestId("pane-fx_w_book");
    const c = new KeyboardEvent("keydown", { key: "c", code: "KeyC", bubbles: true, cancelable: true });
    act(() => {
      window.dispatchEvent(c);
    });
    expect(c.defaultPrevented).toBe(false);
    expect(heardKeys.fx_w_book).toContain("c");
  });

  it("Alt held 400 ms shows which-key, and the release reaches no window", async () => {
    mount();
    await screen.findByTestId("pane-fx_w_book");
    act(() => {
      fireEvent.keyDown(window, { key: "Alt", code: "AltLeft", altKey: true });
    });
    act(() => {
      vi.advanceTimersByTime(400);
    });
    expect(screen.getByRole("dialog", { name: "alt keys" })).toBeTruthy();
    expect(screen.getByText("window left")).toBeTruthy();
    // Not built yet, so not on the panel.
    expect(screen.queryByText("overview")).toBeNull();
    const before = (heardKeys.fx_w_book ?? []).length;
    act(() => {
      fireEvent.keyUp(window, { key: "Alt", code: "AltLeft" });
    });
    expect(screen.queryByRole("dialog", { name: "alt keys" })).toBeNull();
    expect((heardKeys.fx_w_book ?? []).length).toBe(before);
  });

  it("alt+↵ enters focus mode (only the focused window is active) and esc leaves it", async () => {
    mount();
    await screen.findByTestId("pane-fx_w_book");
    alt("Enter", "Enter");
    expect(document.querySelector("[data-desk-shell]")?.getAttribute("data-focus-mode")).toBe("on");
    expect(state("fx_w_book")).toBe("active");
    expect(state("fx_w_video")).toBe("offscreen");
    act(() => {
      fireEvent.keyDown(window, { key: "Escape", code: "Escape" });
    });
    expect(document.querySelector("[data-desk-shell]")?.getAttribute("data-focus-mode")).toBe("off");
    expect(state("fx_w_video")).toBe("visible");
  });
});

describe("first run", () => {
  it("a vault with no desks gets one, holding the book read last", async () => {
    const empty: DeskStateDto = { version: 1, desks: [], runningPadIds: [], serverSeq: [] };
    const server = new FixtureDeskServer(empty);
    mount(server, { firstSourceId: FIXTURE_SOURCES.book.sourceId });
    await flush();
    await waitFor(() => expect(server.state().desks).toHaveLength(1));
    const desk = server.state().desks[0];
    expect(desk.title).toBe("new desk · Softmax, a short");
    expect(desk.slots[0].windows[0].content).toMatchObject({ kind: "source", sourceId: FIXTURE_SOURCES.book.sourceId, extractionId: FIXTURE_SOURCES.book.extractionId });
    expect(server.batches[0].ops.map((op) => op.op)).toEqual(["create_desk", "open_window", "set_focus"]);
  });

  it("with no book read yet, the desk is empty and says how to open one", async () => {
    const server = new FixtureDeskServer({ version: 1, desks: [], runningPadIds: [], serverSeq: [] });
    mount(server);
    expect(await screen.findByText(/This desk is empty/)).toBeTruthy();
  });

  it("continues the client's sequence from the server's head", async () => {
    const start = fixtureDeskState();
    const server = new FixtureDeskServer(start);
    window.localStorage.setItem("learnloop.desks.client.vault-seq", "client-seq");
    server.apply({ clientId: "client-seq", seq: 1, ops: [{ op: "rename_desk", deskId: "fx_desk_softmax", title: "renamed", expectedVersion: 1 }] });
    mount(server, { vaultKey: "vault-seq" });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyL", "l");
    await flush();
    expect(server.batches.map((batch) => [batch.clientId, batch.seq])).toEqual([["client-seq", 1], ["client-seq", 2]]);
  });
});
