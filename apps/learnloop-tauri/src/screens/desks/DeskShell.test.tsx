// DeskShell in jsdom (spec §18.2): the key router reaching the workspace, the writes the outbox sends,
// a conflict taking the server's state, first-run desks, the typing scope, hidden desks and which-key.
// Layout, pixels and real iframes are the real-webview harness's (scripts/desk_harness/run.py).
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useEffect, useState } from "react";
import type { DeskStateDto, SourceLibraryCard } from "../../api/dto";
import { FixtureDeskServer, fixtureDeskState } from "../../fixtures/desks/workspace";
import { FIXTURE_LIBRARY, FIXTURE_SOURCES } from "../../fixtures/desks/sources";
import { DeskShell, type DeskTransport, type PaneRenderInput } from "./DeskShell";
import { useListenerHub, useScopeClaim, type ClaimedScope } from "./lifecycle";
import { useBareAltClear } from "../reader/bareAlt";

vi.mock("../../api/client", () => ({ api: {} }));
const sourceWindows = vi.hoisted(() => new Map<string, { onStatus: (next: { readingSpan?: string | null }) => void }>());
vi.mock("./windows/SourceWindow", () => ({
  SourceWindow: (props: { content: { extractionId: string }; onStatus: (next: { readingSpan?: string | null }) => void }) => {
    sourceWindows.set(props.content.extractionId, props);
    return null;
  },
}));
vi.mock("./windows/PanelWindow", () => ({ PANEL_TITLES: { guide: "Guide", notes: "Notes", path: "Reading path", library: "Library" }, LibraryPanel: () => null, PathPanel: () => null, RailHostPanel: () => null }));

const heardKeys: Record<string, string[]> = {};

/** A pane that shows its lifecycle state and records the keys its window-level listener hears. */
function Pane({ input }: { input: PaneRenderInput }) {
  const hub = useListenerHub();
  const id = input.window.windowId;
  useEffect(() => {
    const offs = [
      hub.listen("window", "keydown", (event: KeyboardEvent) => {
        (heardKeys[id] ??= []).push(event.key);
      }),
      hub.listen("window", "keyup", (event: KeyboardEvent) => {
        (heardKeys[id] ??= []).push(`up:${event.key}`);
      }, true),
    ];
    return () => offs.forEach((off) => off());
  }, [hub, id]);
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
    // The windows render in a stable order (by id); the first slot is read from its place.
    await waitFor(() => expect(document.querySelector('[data-desk-slot="fx_desk_softmax:0:0"]')?.getAttribute("data-desk-slot-window")).toBe("fx_w_paper"));
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
    // Not built yet (RD4), so not on the panel.
    expect(screen.queryByText("new pad")).toBeNull();
    act(() => {
      fireEvent.keyUp(window, { key: "Alt", code: "AltLeft" });
    });
    expect(screen.queryByRole("dialog", { name: "alt keys" })).toBeNull();
    expect(heardKeys.fx_w_book ?? []).not.toContain("up:Alt");
    // A tap's release does reach the window (its capture-clearing gesture).
    act(() => {
      fireEvent.keyDown(window, { key: "Alt", code: "AltLeft", altKey: true });
      fireEvent.keyUp(window, { key: "Alt", code: "AltLeft" });
    });
    expect(heardKeys.fx_w_book).toContain("up:Alt");
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

// -- the overview (RD2) -----------------------------------------------------------------------------

class ManualFrames {
  queue: Array<{ handle: number; callback: (now: number) => void }> = [];
  now = 0;
  private next = 1;
  request = (callback: (now: number) => void): number => {
    const handle = this.next++;
    this.queue.push({ handle, callback });
    return handle;
  };
  cancel = (handle: number): void => {
    this.queue = this.queue.filter((entry) => entry.handle !== handle);
  };
  run(count = 60) {
    for (let i = 0; i < count && this.queue.length > 0; i += 1) {
      act(() => {
        this.now += 1000 / 60;
        const due = this.queue;
        this.queue = [];
        for (const entry of due) entry.callback(this.now);
      });
    }
  }
}

function overviewOn(): boolean {
  return document.querySelector("[data-desk-shell]")?.getAttribute("data-overview") === "on";
}

function press(key: string, code: string, init: KeyboardEventInit = {}) {
  act(() => {
    fireEvent.keyDown(window, { key, code, ...init });
    fireEvent.keyUp(window, { key, code, ...init });
  });
}

describe("the overview", () => {
  it("alt+o zooms out: every window becomes a preview card; esc zooms back to where it was", async () => {
    const frames = new ManualFrames();
    mount(new FixtureDeskServer(), { frameClock: frames, reducedMotion: false });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyL", "l");
    alt("KeyO", "o");
    expect(overviewOn()).toBe(false);
    frames.run();
    expect(overviewOn()).toBe(true);
    expect(state("fx_w_book")).toBe("preview");
    expect(state("fx_w_video")).toBe("preview");
    // The windows' content is not on show; the cards are.
    expect(document.querySelectorAll(".desk-card").length).toBeGreaterThan(0);
    press("Escape", "Escape");
    frames.run();
    expect(overviewOn()).toBe(false);
    expect(state("fx_w_video")).toBe("active");
    expect(state("fx_w_book")).toBe("visible");
  });

  it("h/j/k/l move the selection; ↵ opens the selected card on its desk", async () => {
    const frames = new ManualFrames();
    const { server } = mount(new FixtureDeskServer(), { frameClock: frames, reducedMotion: false });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyO", "o");
    frames.run();
    press("j", "KeyJ");
    expect(document.querySelector(".ov-selected")?.getAttribute("data-desk-slot-desk")).toBe("fx_desk_attention");
    press("l", "KeyL");
    press("Enter", "Enter");
    frames.run(90);
    expect(overviewOn()).toBe(false);
    expect(state("fx_w_paper2")).toBe("active");
    await flush();
    const attention = server.state().desks.find((desk) => desk.deskId === "fx_desk_attention");
    expect(attention?.focusWindowId).toBe("fx_w_paper2");
  });

  it("reduced motion: no zoom, the view crossfades at once", async () => {
    mount(new FixtureDeskServer(), { reducedMotion: true });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyO", "o");
    expect(overviewOn()).toBe(true);
    expect(document.querySelector("[data-desk-world]")?.classList.contains("desk-fadeswap")).toBe(true);
    press("Escape", "Escape");
    expect(overviewOn()).toBe(false);
  });

  it("alt+shift+j moves the selected card to the desk below", async () => {
    const { server } = mount(new FixtureDeskServer(), { reducedMotion: true });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyO", "o");
    act(() => {
      fireEvent.keyDown(window, { key: "Alt", code: "AltLeft", altKey: true });
      fireEvent.keyDown(window, { key: "J", code: "KeyJ", altKey: true, shiftKey: true });
      fireEvent.keyUp(window, { key: "J", code: "KeyJ", altKey: true, shiftKey: true });
      fireEvent.keyUp(window, { key: "Alt", code: "AltLeft" });
    });
    await flush();
    const attention = server.state().desks.find((desk) => desk.deskId === "fx_desk_attention");
    expect(attention?.slots.flatMap((slot) => slot.windows.map((window) => window.windowId))).toContain("fx_w_book");
  });

  it("b toggles the relations: unrelated cards recede only while they are on", async () => {
    mount(new FixtureDeskServer(), { reducedMotion: true });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyO", "o");
    expect(document.querySelectorAll(".ov-recede").length).toBeGreaterThan(0);
    press("b", "KeyB");
    expect(document.querySelectorAll(".ov-recede").length).toBe(0);
  });

  it("g held previews a gather: dashed ghosts where the linked cards would go, gone on release", async () => {
    mount(new FixtureDeskServer(), { reducedMotion: true });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyO", "o");
    act(() => {
      fireEvent.keyDown(window, { key: "g", code: "KeyG" });
    });
    expect(document.querySelectorAll(".desk-ov-ghost").length).toBe(2);
    act(() => {
      fireEvent.keyUp(window, { key: "g", code: "KeyG" });
    });
    expect(document.querySelectorAll(".desk-ov-ghost").length).toBe(0);
  });

  it("a key pressed during a zoom settles it at once", async () => {
    const frames = new ManualFrames();
    mount(new FixtureDeskServer(), { frameClock: frames, reducedMotion: false });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyO", "o");
    frames.run(3);
    press("q", "KeyQ");
    expect(overviewOn()).toBe(true);
  });
});

describe("gather", () => {
  it("alt+g brings the focus's linked windows beside it; ↺ ungather puts the order back", async () => {
    const { server } = mount();
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyG", "g");
    await flush();
    const order = () => server.state().desks[0].slots.map((slot) => slot.windows[0].windowId);
    expect(order()).toEqual(["fx_w_book", "fx_w_guide", "fx_w_path", "fx_w_video", "fx_w_paper", "fx_w_pads"]);
    fireEvent.click(screen.getByRole("button", { name: "↺ ungather" }));
    await flush();
    expect(order()).toEqual(["fx_w_book", "fx_w_video", "fx_w_paper", "fx_w_guide", "fx_w_path", "fx_w_pads"]);
  });

  it("alt+shift+g moves the focus and its linked windows to a new desk", async () => {
    const { server } = mount();
    await screen.findByTestId("pane-fx_w_book");
    act(() => {
      fireEvent.keyDown(window, { key: "Alt", code: "AltLeft", altKey: true });
      fireEvent.keyDown(window, { key: "G", code: "KeyG", altKey: true, shiftKey: true });
      fireEvent.keyUp(window, { key: "G", code: "KeyG", altKey: true, shiftKey: true });
      fireEvent.keyUp(window, { key: "Alt", code: "AltLeft" });
    });
    await flush();
    const gathered = server.state().desks.find((desk) => desk.title.startsWith("gathered · "));
    expect(gathered?.slots.map((slot) => slot.windows[0].windowId)).toEqual(["fx_w_book", "fx_w_guide", "fx_w_path"]);
    expect(gathered?.focusWindowId).toBe("fx_w_book");
    expect(server.state().desks[0].slots.map((slot) => slot.windows[0].windowId)).toEqual(["fx_w_video", "fx_w_paper", "fx_w_pads"]);
  });
});

describe("the wheel", () => {
  it("alt + a sideways swipe pans the strip and snaps to the nearest window after 120 ms, which takes the focus", async () => {
    const { server } = mount();
    await screen.findByTestId("pane-fx_w_book");
    const stage = document.querySelector("[data-desk-stage]") as HTMLElement;
    const swipe = new WheelEvent("wheel", { deltaX: 700, deltaY: 10, altKey: true, bubbles: true, cancelable: true });
    act(() => {
      stage.dispatchEvent(swipe);
    });
    expect(swipe.defaultPrevented).toBe(true);
    expect(screen.getByRole("status").textContent).toContain("alt + swipe");
    expect(state("fx_w_book")).toBe("active");
    await act(async () => {
      vi.advanceTimersByTime(130);
    });
    expect(state("fx_w_video")).toBe("active");
    await flush();
    expect(server.state().desks[0].focusWindowId).toBe("fx_w_video");
  });

  it("alt + a vertical touchpad scroll starts the zoom and follows the fingers; a plain scroll does nothing", async () => {
    const frames = new ManualFrames();
    mount(new FixtureDeskServer(), { frameClock: frames, reducedMotion: false });
    await screen.findByTestId("pane-fx_w_book");
    const stage = document.querySelector("[data-desk-stage]") as HTMLElement;
    const plain = new WheelEvent("wheel", { deltaY: 30, bubbles: true, cancelable: true });
    act(() => {
      stage.dispatchEvent(plain);
    });
    expect(plain.defaultPrevented).toBe(false);
    // The first event decides a gesture until it ends (80 ms idle).
    await act(async () => {
      vi.advanceTimersByTime(100);
    });
    act(() => {
      stage.dispatchEvent(new WheelEvent("wheel", { deltaY: 6, altKey: true, bubbles: true, cancelable: true }));
    });
    expect(document.querySelector("[data-desk-shell]")?.classList.contains("zooming")).toBe(true);
    expect(screen.getByRole("status").textContent).toContain("alt + scroll · zooming out");
    frames.run(5);
    // Lifting the fingers short of 40 % springs back.
    await act(async () => {
      vi.advanceTimersByTime(100);
    });
    frames.run(90);
    expect(overviewOn()).toBe(false);
  });
});

// -- the RD1 fix round --------------------------------------------------------------------------------

describe("fix round: saving", () => {
  it("compare with nothing typed opens the library pane, never an invalid compare reference (finding 1)", async () => {
    const { server } = mount();
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.click(screen.getByRole("button", { name: "+ open beside" }));
    fireEvent.click(screen.getByRole("button", { name: /⇄ compare/ }));
    await flush();
    const opened = server.batches.flatMap((batch) => batch.ops).filter((op) => op.op === "open_window");
    expect(opened).toHaveLength(1);
    const content = opened[0].op === "open_window" ? opened[0].content : undefined;
    expect(content).toEqual({ kind: "panel", panel: "library" });
  });

  it("an undo offer for a close the server refused goes away (finding 11)", async () => {
    const server = new FixtureDeskServer();
    mount(server);
    await screen.findByTestId("pane-fx_w_book");
    // Another installation renames the desk first: our close is stale.
    server.apply({ clientId: "other-device", seq: 1, ops: [{ op: "rename_desk", deskId: "fx_desk_softmax", title: "elsewhere", expectedVersion: 1 }] });
    alt("KeyW", "w");
    expect(screen.getByRole("button", { name: /undo close/ })).toBeTruthy();
    await flush();
    await flush();
    expect(screen.getByTestId("pane-fx_w_book")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /undo close/ })).toBeNull();
  });

  it("leaving the desks before a change is sent and coming back keeps one numbering (finding 5)", async () => {
    const server = new FixtureDeskServer();
    const transport = transportFor(server);
    const props = { vaultKey: "vault-remount", onError: vi.fn(), transport, renderPane: (input: PaneRenderInput) => <Pane input={input} />, initialViewport: { width: 1600, height: 960 }, mintId: mint };
    const first = render(<DeskShell {...props} />);
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyL", "l");
    first.unmount();
    render(<DeskShell {...props} />);
    await screen.findByTestId("pane-fx_w_book");
    alt("BracketRight", "]");
    await flush();
    await flush();
    expect(server.batches.map((batch) => batch.seq)).toEqual([1, 2]);
    expect(new Set(server.batches.map((batch) => batch.clientId)).size).toBe(1);
  });
});

describe("fix round: windows are never remounted (finding 2)", () => {
  const mounts: Record<string, number> = {};
  function Draft({ input }: { input: PaneRenderInput }) {
    const id = input.window.windowId;
    useEffect(() => {
      mounts[id] = (mounts[id] ?? 0) + 1;
    }, [id]);
    return <input aria-label={`draft ${id}`} defaultValue="" />;
  }

  it("a draft survives pairing, unpairing and focus mode, and its window mounts once", async () => {
    for (const key of Object.keys(mounts)) delete mounts[key];
    mount(new FixtureDeskServer(), { renderPane: (input) => <Draft input={input} /> });
    const book = (await screen.findByLabelText("draft fx_w_book")) as HTMLInputElement;
    const video = screen.getByLabelText("draft fx_w_video") as HTMLInputElement;
    fireEvent.change(book, { target: { value: "half a thought" } });
    fireEvent.change(video, { target: { value: "a note on the video" } });
    alt("Comma", ",");
    alt("Period", ".");
    alt("Enter", "Enter");
    act(() => {
      fireEvent.keyDown(window, { key: "Escape", code: "Escape" });
    });
    alt("Comma", ",");
    alt("Enter", "Enter");
    expect(screen.getByLabelText("draft fx_w_book")).toBe(book);
    expect(book.value).toBe("half a thought");
    // The partner of a focused pane stays mounted too.
    expect(screen.getByLabelText("draft fx_w_video")).toBe(video);
    expect(video.value).toBe("a note on the video");
    expect(mounts.fx_w_book).toBe(1);
    expect(mounts.fx_w_video).toBe(1);
  });
});

describe("fix round: the hosted content's scopes reach the router (finding 8)", () => {
  const claims: Record<string, ClaimedScope> = {};
  function ClaimingPane({ input }: { input: PaneRenderInput }) {
    const id = input.window.windowId;
    const [menu, setMenu] = useState(false);
    const scope = menu ? "menu" : claims[id];
    useScopeClaim(scope ?? "typing", scope !== undefined);
    return (
      <>
        <Pane input={input} />
        <button type="button" onClick={() => setMenu(true)}>{`open menu ${id}`}</button>
      </>
    );
  }
  afterEach(() => {
    for (const key of Object.keys(claims)) delete claims[key];
  });

  it("an intent box open over a selection takes the typed key: x reaches it and swaps nothing", async () => {
    claims.fx_w_book = "typing";
    const { server } = mount(new FixtureDeskServer(), { renderPane: (input) => <ClaimingPane input={input} /> });
    await screen.findByTestId("pane-fx_w_book");
    act(() => {
      fireEvent.keyDown(window, { key: "x", code: "KeyX" });
    });
    await flush();
    expect(heardKeys.fx_w_book).toContain("x");
    expect(server.batches).toEqual([]);
  });

  it("an open menu in focus mode takes esc: focus mode stays and the menu hears it", async () => {
    mount(new FixtureDeskServer(), { renderPane: (input) => <ClaimingPane input={input} /> });
    await screen.findByTestId("pane-fx_w_book");
    alt("Enter", "Enter");
    const box = () => document.querySelector('[data-desk-slot-window="fx_w_book"]');
    expect(box()?.className).toContain("focused-full");
    fireEvent.click(screen.getByRole("button", { name: "open menu fx_w_book" }));
    act(() => {
      fireEvent.keyDown(window, { key: "Escape", code: "Escape" });
    });
    expect(heardKeys.fx_w_book).toContain("Escape");
    expect(box()?.className).toContain("focused-full");
  });
});

describe("fix round: one Alt tracker (finding 9)", () => {
  const cleared: string[] = [];
  function CapturePane({ input }: { input: PaneRenderInput }) {
    useBareAltClear(() => cleared.push(input.window.windowId));
    return <Pane input={input} />;
  }

  it("an Alt chord the shell takes never reaches the Reader as a bare-Alt tap; a real tap still clears", async () => {
    cleared.length = 0;
    mount(new FixtureDeskServer(), { renderPane: (input) => <CapturePane input={input} /> });
    await screen.findByTestId("pane-fx_w_book");
    alt("BracketRight", "]");
    expect(cleared).toEqual([]);
    act(() => {
      fireEvent.keyDown(window, { key: "Alt", code: "AltLeft", altKey: true });
      fireEvent.keyUp(window, { key: "Alt", code: "AltLeft" });
    });
    expect(cleared).toEqual(["fx_w_book"]);
  });
});

describe("fix round: a window that loses activation loses the DOM's input (finding 4)", () => {
  function InputPane({ input }: { input: PaneRenderInput }) {
    return (
      <>
        <Pane input={input} />
        <input aria-label={`compose ${input.window.windowId}`} />
      </>
    );
  }

  it("switching desks moves the focus out of the old desk's input into the new active window, and the old desk is inert", async () => {
    mount(new FixtureDeskServer(), { renderPane: (input) => <InputPane input={input} /> });
    const compose = (await screen.findByLabelText("compose fx_w_book")) as HTMLInputElement;
    act(() => compose.focus());
    expect(document.activeElement).toBe(compose);
    alt("KeyJ", "j");
    await screen.findByTestId("pane-fx_w_video2");
    expect(document.activeElement).not.toBe(compose);
    expect(document.activeElement?.closest("[data-desk-window]")?.getAttribute("data-desk-window")).toBe("fx_w_video2");
    expect(document.querySelector('[data-desk-window="fx_w_book"]')?.hasAttribute("inert")).toBe(true);
    expect(document.querySelector('[data-desk-window="fx_w_video2"]')?.hasAttribute("inert")).toBe(false);
  });

  it("moving the activation to the next window on the same desk takes the focus with it", async () => {
    mount(new FixtureDeskServer(), { renderPane: (input) => <InputPane input={input} /> });
    const compose = (await screen.findByLabelText("compose fx_w_book")) as HTMLInputElement;
    act(() => compose.focus());
    alt("KeyL", "l");
    expect(document.activeElement?.closest("[data-desk-window]")?.getAttribute("data-desk-window")).toBe("fx_w_video");
    // A visible, inactive window stays clickable (not inert); only paused ones are.
    expect(document.querySelector('[data-desk-window="fx_w_book"]')?.hasAttribute("inert")).toBe(false);
    expect(document.querySelector('[data-desk-window="fx_w_paper"]')?.hasAttribute("inert")).toBe(true);
  });
});

describe("fix round: a reading place still waiting to be saved survives leaving the desks (finding 5)", () => {
  it("leaving the desks before the idle save sends the place anyway", async () => {
    const server = new FixtureDeskServer();
    const transport = transportFor(server);
    const view = render(<DeskShell vaultKey="vault-view-save" onError={vi.fn()} transport={transport} initialViewport={{ width: 1600, height: 960 }} mintId={mint} />);
    await waitFor(() => expect(sourceWindows.size).toBeGreaterThan(0));
    const book = [...sourceWindows.entries()].find(([extractionId]) => extractionId === FIXTURE_SOURCES.book.extractionId)?.[1];
    expect(book).toBeDefined();
    act(() => book!.onStatus({ readingSpan: `${FIXTURE_SOURCES.book.extractionId}_s2_1` }));
    view.unmount();
    await flush();
    await flush();
    const saved = server.state().desks.flatMap((desk) => desk.slots.flatMap((slot) => slot.windows)).find((window) => window.windowId === "fx_w_book");
    expect(saved?.view?.spanId).toBe(`${FIXTURE_SOURCES.book.extractionId}_s2_1`);
  });
});

// -- the RD2 fix round --------------------------------------------------------------------------------

function wheel(init: WheelEventInit) {
  const stage = document.querySelector("[data-desk-stage]") as HTMLElement;
  const event = new WheelEvent("wheel", { bubbles: true, cancelable: true, ...init });
  act(() => {
    stage.dispatchEvent(event);
  });
  return event;
}

function shellHas(name: string): boolean {
  return document.querySelector("[data-desk-shell]")?.classList.contains(name) ?? false;
}

describe("RD2 fix round: input in the overview (finding 1)", () => {
  it("no window hears keys while the overview shows: the reading focus is a preview card", async () => {
    mount(new FixtureDeskServer(), { reducedMotion: true });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyO", "o");
    expect(overviewOn()).toBe(true);
    for (const key of Object.keys(heardKeys)) delete heardKeys[key];
    act(() => {
      fireEvent.keyDown(window, { key: "z", code: "KeyZ", ctrlKey: true });
    });
    expect(heardKeys.fx_w_book ?? []).not.toContain("z");
  });
});

describe("RD2 fix round: one transition at a time (finding 2)", () => {
  it("an exit's late cleanup never dismantles the zoom that started after it", async () => {
    const frames = new ManualFrames();
    mount(new FixtureDeskServer(), { frameClock: frames, reducedMotion: false });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyO", "o");
    frames.run();
    expect(overviewOn()).toBe(true);
    press("Escape", "Escape");
    frames.run(2);
    // o settles the exit and starts entering again at once.
    press("o", "KeyO");
    expect(shellHas("zooming")).toBe(true);
    // The exit's cleanup was due two frames after its commit.
    frames.run(3);
    expect(shellHas("zooming")).toBe(true);
    frames.run();
    expect(overviewOn()).toBe(true);
  });
});

describe("RD2 fix round: the world's camera has one animator (finding 4)", () => {
  it("after keyboard navigation in the overview, the world's CSS transition is off once a zoom starts", async () => {
    const frames = new ManualFrames();
    mount(new FixtureDeskServer(), { frameClock: frames, reducedMotion: false });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyO", "o");
    frames.run();
    press("j", "KeyJ");
    const world = () => document.querySelector("[data-desk-world]") as HTMLElement;
    expect(world().classList.contains("pan-ease")).toBe(true);
    press("Enter", "Enter");
    frames.run(2);
    expect(shellHas("zooming")).toBe(true);
    expect(world().classList.contains("pan-ease")).toBe(false);
  });
});

describe("RD2 fix round: the wheel through the real router (findings 9, 10, 11)", () => {
  it("a touchpad pinch (ctrl+wheel with no Ctrl key held) is classed as a pinch", async () => {
    const frames = new ManualFrames();
    mount(new FixtureDeskServer(), { frameClock: frames, reducedMotion: false });
    await screen.findByTestId("pane-fx_w_book");
    wheel({ deltaY: 4, ctrlKey: true });
    expect(screen.getByRole("status").textContent).toContain("pinch · zooming out");
  });

  it("with Ctrl held, ctrl+wheel is ctrl + scroll, not a pinch", async () => {
    const frames = new ManualFrames();
    mount(new FixtureDeskServer(), { frameClock: frames, reducedMotion: false });
    await screen.findByTestId("pane-fx_w_book");
    act(() => {
      fireEvent.keyDown(window, { key: "Control", code: "ControlLeft", ctrlKey: true });
    });
    wheel({ deltaY: 4, ctrlKey: true });
    expect(screen.getByRole("status").textContent).toContain("ctrl + scroll · zooming out");
  });

  it("reduced motion: an alt-wheel zoom crossfades to the overview at once, with no zoom", async () => {
    const frames = new ManualFrames();
    mount(new FixtureDeskServer(), { frameClock: frames, reducedMotion: true });
    await screen.findByTestId("pane-fx_w_book");
    wheel({ deltaY: 6, altKey: true });
    expect(shellHas("zooming")).toBe(false);
    expect(frames.queue.length).toBe(0);
    expect(overviewOn()).toBe(true);
  });

  it("reduced motion: a ctrl+drag on the background crossfades, with no zoom", async () => {
    const frames = new ManualFrames();
    mount(new FixtureDeskServer(), { frameClock: frames, reducedMotion: true });
    await screen.findByTestId("pane-fx_w_book");
    const stage = document.querySelector("[data-desk-stage]") as HTMLElement;
    act(() => {
      fireEvent.keyDown(window, { key: "Control", code: "ControlLeft", ctrlKey: true });
      fireEvent.pointerDown(stage, { ctrlKey: true, clientX: 10, clientY: 10, pointerId: 1 });
      fireEvent.pointerMove(stage, { ctrlKey: true, clientX: 10, clientY: 200, pointerId: 1 });
      fireEvent.pointerUp(stage, { ctrlKey: true, clientX: 10, clientY: 200, pointerId: 1 });
    });
    expect(shellHas("zooming")).toBe(false);
    expect(frames.queue.length).toBe(0);
    expect(overviewOn()).toBe(true);
  });

  it("an alt-wheel gesture is no bare-Alt tap: the capture stays", async () => {
    const cleared: string[] = [];
    function CapturePane({ input }: { input: PaneRenderInput }) {
      useBareAltClear(() => cleared.push(input.window.windowId));
      return <Pane input={input} />;
    }
    const frames = new ManualFrames();
    mount(new FixtureDeskServer(), { frameClock: frames, reducedMotion: false, renderPane: (input) => <CapturePane input={input} /> });
    await screen.findByTestId("pane-fx_w_book");
    act(() => {
      fireEvent.keyDown(window, { key: "Alt", code: "AltLeft", altKey: true });
    });
    wheel({ deltaX: 300, deltaY: 2, altKey: true });
    act(() => {
      fireEvent.keyUp(window, { key: "Alt", code: "AltLeft" });
    });
    expect(cleared).toEqual([]);
  });
});
