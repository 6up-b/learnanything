// DeskShell in jsdom (spec §18.2): the key router reaching the workspace, the writes the outbox sends,
// a conflict taking the server's state, first-run desks, the typing scope, hidden desks and which-key.
// Layout, pixels and real iframes are the real-webview harness's (scripts/desk_harness/run.py).
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useEffect, useState } from "react";
import type { DeskStateDto, SourceLibraryCard } from "../../api/dto";
import { FixtureDeskServer, fixtureDeskState } from "../../fixtures/desks/workspace";
import { FIXTURE_LIBRARY, FIXTURE_SOURCES } from "../../fixtures/desks/sources";
import { DeskShell, groundingFor, type CompanionTransport, type DeskTransport, type PaneRenderInput } from "./DeskShell";
import { fromDeskState } from "./model/workspace";
import { Poller } from "../../api/poller";
import { useListenerHub, useScopeClaim, type ClaimedScope } from "./lifecycle";
import { usePadsHost } from "./pads/host";
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
    // `p` (your path) arrives with the goal lens.
    const p = new KeyboardEvent("keydown", { key: "p", code: "KeyP", bubbles: true, cancelable: true });
    act(() => {
      window.dispatchEvent(p);
    });
    expect(p.defaultPrevented).toBe(false);
    expect(heardKeys.fx_w_book).toContain("p");
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
    // Built now (the pads), so on the panel; a chord whose feature is not built yet is not.
    expect(screen.getByText("new pad")).toBeTruthy();
    expect(screen.queryByText("insert ▶ timestamp")).toBeNull();
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
    // The gathered windows, then the new desk's running pad in its stack (every desk has one).
    expect(gathered?.slots.slice(0, 3).map((slot) => slot.windows[0].windowId)).toEqual(["fx_w_book", "fx_w_guide", "fx_w_path"]);
    expect(gathered?.slots[3]?.windows[0].kind).toBe("pad_stack");
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

describe("RD2 fix round: a card moved to another desk's first slot lands there (finding 6)", () => {
  it("alt+shift+j on the first card puts it first on the desk below, on the server too", async () => {
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
    expect(attention?.slots[0].windows[0].windowId).toBe("fx_w_book");
  });
});

describe("RD2 fix round: opened beside is remembered (finding 7)", () => {
  it("a window opened beside the focus keeps that window as its origin, on the server, and draws the relation", async () => {
    const { server } = mount(new FixtureDeskServer(), { reducedMotion: true });
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.click(screen.getByRole("button", { name: "+ open beside" }));
    fireEvent.click(screen.getByRole("button", { name: /⇄ compare/ }));
    await flush();
    const opened = server.state().desks[0].slots.flatMap((slot) => slot.windows).find((window) => window.content?.kind === "panel" && window.content.panel === "library");
    expect(opened?.view?.openedBeside).toBe("fx_w_book");
  });
});

describe("RD2 fix round: the overview's selection is always a card on show (finding 12)", () => {
  it("with the first desk empty, the overview still selects a card and the keys move it", async () => {
    const server = new FixtureDeskServer();
    const first = server.state().desks[0];
    let version = first.version;
    const ids = first.slots.flatMap((slot) => slot.windows.map((window) => window.windowId));
    server.apply({ clientId: "setup", seq: 1, ops: ids.map((windowId) => ({ op: "close_window" as const, deskId: first.deskId, windowId, expectedVersion: version++ })) });
    mount(server, { reducedMotion: true });
    await screen.findByTestId("pane-fx_w_video2").catch(() => undefined);
    alt("KeyO", "o");
    expect(overviewOn()).toBe(true);
    expect(document.querySelector(".ov-selected")).not.toBeNull();
    const before = document.querySelector(".ov-selected")?.getAttribute("data-desk-slot-window");
    press("l", "KeyL");
    expect(document.querySelector(".ov-selected")?.getAttribute("data-desk-slot-window")).not.toBe(before);
  });

  it("a card moved down with alt+shift+j stays in view: the camera follows it", async () => {
    mount(new FixtureDeskServer(), { reducedMotion: true, initialViewport: { width: 1600, height: 420 } });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyO", "o");
    const moveDown = () => act(() => {
      fireEvent.keyDown(window, { key: "Alt", code: "AltLeft", altKey: true });
      fireEvent.keyDown(window, { key: "J", code: "KeyJ", altKey: true, shiftKey: true });
      fireEvent.keyUp(window, { key: "J", code: "KeyJ", altKey: true, shiftKey: true });
      fireEvent.keyUp(window, { key: "Alt", code: "AltLeft" });
    });
    moveDown();
    moveDown();
    await flush();
    const selected = document.querySelector(".ov-selected") as HTMLElement;
    expect(selected.getAttribute("data-desk-slot-desk")).toBe("fx_desk_backprop");
    const world = (document.querySelector("[data-desk-world]") as HTMLElement).style.transform;
    const [x, y, s] = world.match(/-?[\d.]+/g)!.map(Number);
    void x;
    const top = y + parseFloat(selected.style.top) * s;
    const bottom = top + parseFloat(selected.style.height) * s;
    expect(top).toBeGreaterThanOrEqual(0);
    expect(bottom).toBeLessThanOrEqual(420);
  });
});

describe("RD2 fix round: cancelled pointer gestures (findings 14, 15)", () => {
  // jsdom has no PointerEvent: a MouseEvent with a pointer id carries the coordinates.
  beforeEach(() => {
    vi.stubGlobal("PointerEvent", class extends MouseEvent {
      pointerId: number;
      constructor(type: string, init: PointerEventInit = {}) {
        super(type, init);
        this.pointerId = init.pointerId ?? 0;
      }
    });
  });
  it("a card drag that is cancelled puts the card back and moves it no more", async () => {
    mount(new FixtureDeskServer(), { reducedMotion: true });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyO", "o");
    const stage = document.querySelector("[data-desk-stage]") as HTMLElement;
    const card = document.querySelector('[data-desk-slot-window="fx_w_video"]') as HTMLElement;
    act(() => {
      fireEvent.pointerDown(card, { clientX: 100, clientY: 100, pointerId: 1 });
      fireEvent.pointerMove(stage, { clientX: 160, clientY: 140, pointerId: 1 });
    });
    expect(card.style.transform).not.toBe("");
    act(() => {
      fireEvent.pointerCancel(stage, { pointerId: 1 });
    });
    expect(card.style.transform).toBe("");
    expect(card.style.zIndex).toBe("");
    act(() => {
      fireEvent.pointerMove(stage, { clientX: 260, clientY: 240, pointerId: 1 });
    });
    expect(card.style.transform).toBe("");
  });

  it("the window losing focus cancels a card drag; an element blurring as the press moves the focus does not", async () => {
    mount(new FixtureDeskServer(), { reducedMotion: true });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyO", "o");
    const stage = document.querySelector("[data-desk-stage]") as HTMLElement;
    const card = document.querySelector('[data-desk-slot-window="fx_w_video"]') as HTMLElement;
    act(() => {
      fireEvent.pointerDown(card, { clientX: 100, clientY: 100, pointerId: 1 });
      fireEvent.pointerMove(stage, { clientX: 160, clientY: 140, pointerId: 1 });
      fireEvent.blur(window);
    });
    expect(card.style.transform).toBe("");
    // A click on a card while a shelf button loses the focus still opens the card.
    const shelfButton = screen.getByRole("button", { name: "attention" });
    act(() => shelfButton.focus());
    act(() => {
      fireEvent.pointerDown(card, { clientX: 100, clientY: 100, pointerId: 2 });
      fireEvent.blur(shelfButton);
      fireEvent.pointerUp(stage, { clientX: 100, clientY: 100, pointerId: 2 });
    });
    expect(overviewOn()).toBe(false);
    expect(state("fx_w_video")).toBe("active");
  });

  it("a cancelled ctrl+drag scrub settles the zoom instead of leaving it mid-way", async () => {
    const frames = new ManualFrames();
    mount(new FixtureDeskServer(), { frameClock: frames, reducedMotion: false });
    await screen.findByTestId("pane-fx_w_book");
    const stage = document.querySelector("[data-desk-stage]") as HTMLElement;
    act(() => {
      fireEvent.keyDown(window, { key: "Control", code: "ControlLeft", ctrlKey: true });
      fireEvent.pointerDown(stage, { ctrlKey: true, clientX: 10, clientY: 10, pointerId: 1 });
      fireEvent.pointerMove(stage, { ctrlKey: true, clientX: 10, clientY: 60, pointerId: 1 });
    });
    expect(shellHas("zooming")).toBe(true);
    act(() => {
      fireEvent.pointerCancel(stage, { pointerId: 1 });
    });
    frames.run(90);
    expect(shellHas("zooming")).toBe(false);
  });

  it("ctrl+drag starting on a sliver scrubs the zoom, and the sliver's click is not taken as well", async () => {
    const frames = new ManualFrames();
    mount(new FixtureDeskServer(), { frameClock: frames, reducedMotion: false });
    await screen.findByTestId("pane-fx_w_book");
    const sliver = document.querySelector(".desk-sliver") as HTMLElement;
    expect(sliver).not.toBeNull();
    act(() => {
      fireEvent.keyDown(window, { key: "Control", code: "ControlLeft", ctrlKey: true });
      fireEvent.pointerDown(sliver, { ctrlKey: true, clientX: 10, clientY: 10, pointerId: 1 });
      fireEvent.pointerMove(sliver, { ctrlKey: true, clientX: 10, clientY: 60, pointerId: 1 });
    });
    expect(shellHas("zooming")).toBe(true);
    act(() => {
      fireEvent.pointerUp(sliver, { ctrlKey: true, clientX: 10, clientY: 60, pointerId: 1 });
      fireEvent.click(sliver, { ctrlKey: true });
    });
    frames.run(90);
    expect(state("fx_w_book")).toBe("active");
  });
});

describe("RD2 fix round: miniatures (finding 13)", () => {
  function CountingPane({ input }: { input: PaneRenderInput }) {
    const [count, setCount] = useState(0);
    return (
      <div data-testid={`pane-${input.window.windowId}`} data-state={input.lifecycle.state}>
        <button type="button" onClick={() => setCount((value) => value + 1)}>{`count ${input.window.windowId} ${count}`}</button>
      </div>
    );
  }
  const host = (windowId: string) => document.querySelector(`[data-desk-slot-window="${windowId}"] .desk-card`) as HTMLElement;

  it("a picture is rebuilt after the window's content changed, though its status did not", async () => {
    mount(new FixtureDeskServer(), { reducedMotion: true, renderPane: (input) => <CountingPane input={input} /> });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyO", "o");
    await act(async () => {
      vi.advanceTimersByTime(150);
    });
    expect(host("fx_w_book").textContent).toContain("count fx_w_book 0");
    press("Escape", "Escape");
    fireEvent.click(screen.getByRole("button", { name: "count fx_w_book 0" }));
    await flush();
    alt("KeyO", "o");
    await act(async () => {
      vi.advanceTimersByTime(150);
    });
    expect(host("fx_w_book").textContent).toContain("count fx_w_book 1");
  });

  it("a card moved between two opened desks keeps its picture", async () => {
    mount(new FixtureDeskServer(), { reducedMotion: true, renderPane: (input) => <CountingPane input={input} /> });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyJ", "j");
    await screen.findByTestId("pane-fx_w_video2");
    alt("KeyK", "k");
    alt("KeyO", "o");
    await act(async () => {
      vi.advanceTimersByTime(150);
    });
    expect(host("fx_w_book").textContent).toContain("count fx_w_book 0");
    act(() => {
      fireEvent.keyDown(window, { key: "Alt", code: "AltLeft", altKey: true });
      fireEvent.keyDown(window, { key: "J", code: "KeyJ", altKey: true, shiftKey: true });
      fireEvent.keyUp(window, { key: "J", code: "KeyJ", altKey: true, shiftKey: true });
      fireEvent.keyUp(window, { key: "Alt", code: "AltLeft" });
    });
    await act(async () => {
      vi.advanceTimersByTime(150);
    });
    expect(host("fx_w_book").textContent).toContain("count fx_w_book 0");
  });

  it("no picture is put in while a zoom runs: a build due during an exit waits for its commit", async () => {
    const frames = new ManualFrames();
    mount(new FixtureDeskServer(), { frameClock: frames, reducedMotion: false, renderPane: (input) => <CountingPane input={input} /> });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyO", "o");
    frames.run();
    expect(overviewOn()).toBe(true);
    press("Escape", "Escape");
    expect(shellHas("zooming")).toBe(true);
    await act(async () => {
      vi.advanceTimersByTime(150);
    });
    expect(host("fx_w_book").textContent).not.toContain("count fx_w_book");
  });
});

describe("RD2 fix round: a resize during a zoom (finding 3)", () => {
  it("settles the zoom first, so the new layout is laid out at rest, never under the old plan's transforms", async () => {
    const frames = new ManualFrames();
    mount(new FixtureDeskServer(), { frameClock: frames, reducedMotion: false });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyO", "o");
    frames.run(3);
    expect(shellHas("zooming")).toBe(true);
    const stage = document.querySelector("[data-desk-stage]") as HTMLElement;
    Object.defineProperty(stage, "clientWidth", { value: 1200, configurable: true });
    Object.defineProperty(stage, "clientHeight", { value: 800, configurable: true });
    act(() => {
      window.dispatchEvent(new Event("resize"));
    });
    expect(shellHas("zooming")).toBe(false);
    const boxes = [...document.querySelectorAll<HTMLElement>("[data-desk-slot]")];
    expect(boxes.every((box) => box.style.transform === "")).toBe(true);
  });
});

// -- RD3b: the companion and search ---------------------------------------------------------------------

/** A pane with passages a selection can land in (the windows' own content is mocked away). */
function PassagePane({ input }: { input: PaneRenderInput }) {
  const id = input.window.windowId;
  return (
    <div data-testid={`pane-${id}`} data-state={input.lifecycle.state}>
      <p data-span-id={`${id}_s1`}>{`the first passage of ${id}`}</p>
      <p data-span-id={`${id}_s2`}>{`the second passage of ${id}`}</p>
    </div>
  );
}

function selectIn(windowId: string, span = 1) {
  const p = document.querySelector(`[data-span-id="${windowId}_s${span}"]`) as HTMLElement;
  const range = document.createRange();
  range.selectNodeContents(p);
  const selection = window.getSelection() as Selection;
  selection.removeAllRanges();
  selection.addRange(range);
}

function companionFakes() {
  const reads: string[] = [];
  let answerNow = false;
  const transport = {
    companionAsk: vi.fn(async (input: { requestId: string }) => ({ version: 1, requestId: input.requestId, status: "queued", done: false, partialMd: "", citations: [], streamedPieces: 0, questionEventId: null, kept: false, answer: null, error: null })),
    companionAskJob: vi.fn(async ({ requestId }: { requestId: string }) => {
      reads.push(requestId);
      return answerNow
        ? { version: 1, requestId, status: "done", done: true, partialMd: "Because the factor cancels.", citations: [], streamedPieces: 0, questionEventId: "q1", kept: false,
            answer: { eventId: "e1", readerAnswerEventId: "a1", answerMd: "Because the factor cancels.", answerMode: "answer_directly", citations: [{ extractionId: FIXTURE_SOURCES.book.extractionId, spanId: "fx_w_book_s2", label: "the passage" }], manifest: {}, warmedSurfaceIds: [], burnedSurfaceIds: [], hintEquivalent: false, remaining: null },
            error: null }
        : { version: 1, requestId, status: "running", done: false, partialMd: "", citations: [], streamedPieces: 2, questionEventId: null, kept: false, answer: null, error: null };
    }),
    companionAskCancel: vi.fn(),
    companionHistory: vi.fn(async () => ({ version: 1, days: [], cursor: null })),
    searchEverything: vi.fn(async (input: { query: string }) => ({
      version: 1, query: input.query,
      groups: [{ group: "sources", label: "sources in your library", basis: "words", status: "ok", more: false,
        rows: [{ ref: { kind: "source", sourceId: FIXTURE_SOURCES.paper.sourceId, extractionId: FIXTURE_SOURCES.paper.extractionId }, target: null, sourceId: FIXTURE_SOURCES.paper.sourceId, extractionId: FIXTURE_SOURCES.paper.extractionId, title: "Attention as averaging", readerEnabled: true, openOnDeskIds: [], onThisDesk: false }] }],
      meaning: { status: "unavailable", jobId: null, unavailable: [{ group: "pads", reason: "no meaning index of pad text" }] },
    })),
    searchJob: vi.fn(),
  };
  const poller = new Poller({ setInterval: () => 1, clearInterval: () => undefined });
  return { transport, poller, reads, answer: () => { answerNow = true; } };
}

function mountCompanion(extra: Partial<Parameters<typeof DeskShell>[0]> = {}) {
  const fakes = companionFakes();
  const mounted = mount(new FixtureDeskServer(), {
    renderPane: (input) => <PassagePane input={input} />,
    companion: fakes.transport as unknown as CompanionTransport,
    poller: fakes.poller,
    reducedMotion: false,
    ...extra,
  });
  return { ...mounted, ...fakes };
}

const panel = () => document.querySelector("[data-desk-companion]") as HTMLElement | null;
const panelBox = () => {
  const element = panel();
  return element ? [element.style.left, element.style.top, element.style.width, element.style.height].join(",") : null;
};

describe("the laptop strip (below 1400 px the shelf is a rail; spec §5.6)", () => {
  it("opens over the rail with its own ☰ inside, and esc closes it through the key router", async () => {
    mount(new FixtureDeskServer(), { initialViewport: { width: 1280, height: 800 } });
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.click(screen.getByRole("button", { name: "show the strip" }));
    const strip = document.querySelector(".desk-shelf-overlay");
    expect(strip?.querySelector("button[aria-label='hide the strip']")).not.toBeNull();
    press("Escape", "Escape");
    expect(document.querySelector(".desk-shelf-overlay")).toBeNull();
    expect(screen.getByRole("button", { name: "show the strip" })).not.toBeNull();
  });

  it("its own ☰ closes it by pointer", async () => {
    mount(new FixtureDeskServer(), { initialViewport: { width: 1280, height: 800 } });
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.click(screen.getByRole("button", { name: "show the strip" }));
    fireEvent.click(document.querySelector(".desk-shelf-overlay button[aria-label='hide the strip']")!);
    expect(document.querySelector(".desk-shelf-overlay")).toBeNull();
  });
});

describe("RD3b: the companion's summon, dissolve and dock (spec §8.3)", () => {
  it("c with a selection opens it anchored at the selection, with the selection as its chip", async () => {
    mountCompanion();
    await screen.findByTestId("pane-fx_w_book");
    selectIn("fx_w_book");
    press("c", "KeyC");
    expect(panel()?.getAttribute("data-companion-mode")).toBe("anchored");
    expect(panel()?.className).toContain("summon");
    expect(panel()?.textContent).toContain("asking about");
    expect(panel()?.textContent).toContain("the first passage of fx_w_book");
  });

  it("shift+c with a selection opens it at its dock, with the selection as its chip (§8.6)", async () => {
    mountCompanion();
    await screen.findByTestId("pane-fx_w_book");
    selectIn("fx_w_book");
    press("C", "KeyC", { shiftKey: true });
    expect(panel()?.getAttribute("data-companion-mode")).toBe("docked");
    expect(panel()?.textContent).toContain("asking about");
    expect(panel()?.textContent).toContain("the first passage of fx_w_book");
  });

  it("c again dissolves it where it is: it never passes through its dock, then goes", async () => {
    mountCompanion();
    await screen.findByTestId("pane-fx_w_book");
    selectIn("fx_w_book");
    press("c", "KeyC");
    const anchored = panelBox();
    press("c", "KeyC");
    expect(panel()?.className).toContain("leaving-dissolve");
    expect(panelBox()).toBe(anchored);
    await act(async () => {
      vi.advanceTimersByTime(300);
    });
    expect(panel()).toBeNull();
    expect(document.querySelector("[data-desk-companion-tab]")).not.toBeNull();
  });

  it("shift+c opens it at its dock; c sends it back to the drawer; the tab reopens it", async () => {
    mountCompanion();
    await screen.findByTestId("pane-fx_w_book");
    press("C", "KeyC", { shiftKey: true });
    expect(panel()?.getAttribute("data-companion-mode")).toBe("docked");
    press("c", "KeyC");
    expect(panel()?.className).toContain("leaving-hide");
    await act(async () => {
      vi.advanceTimersByTime(300);
    });
    fireEvent.click(document.querySelector("[data-desk-companion-tab]") as HTMLElement);
    expect(panel()?.getAttribute("data-companion-mode")).toBe("docked");
  });

  it("a docked companion never moves when the learner pans, reorders, pairs, gathers or switches desks", async () => {
    mountCompanion();
    await screen.findByTestId("pane-fx_w_book");
    press("C", "KeyC", { shiftKey: true });
    const docked = panelBox();
    alt("KeyL", "l");
    expect(panelBox()).toBe(docked);
    alt("BracketRight", "]");
    expect(panelBox()).toBe(docked);
    alt("Comma", ",");
    expect(panelBox()).toBe(docked);
    alt("Period", ".");
    alt("KeyG", "g");
    expect(panelBox()).toBe(docked);
    alt("KeyJ", "j");
    await screen.findByTestId("pane-fx_w_video2");
    expect(panelBox()).toBe(docked);
    act(() => {
      document.querySelector("[data-desk-stage]")?.dispatchEvent(new Event("scroll"));
    });
    expect(panelBox()).toBe(docked);
  });

  it("an anchored companion hands off to its dock when the view moves", async () => {
    mountCompanion();
    await screen.findByTestId("pane-fx_w_book");
    selectIn("fx_w_book");
    press("c", "KeyC");
    expect(panel()?.getAttribute("data-companion-mode")).toBe("anchored");
    // The focus moving to the window beside, already in view, moves no view: it stays anchored.
    alt("KeyL", "l");
    expect(panel()?.getAttribute("data-companion-mode")).toBe("anchored");
    // The next one is off screen: the strip pans, and the companion goes to its dock.
    alt("KeyL", "l");
    expect(panel()?.getAttribute("data-companion-mode")).toBe("docked");
  });

  it("an anchored companion hands off when its text scrolls away, but not in its first 250 ms", async () => {
    mountCompanion();
    await screen.findByTestId("pane-fx_w_book");
    selectIn("fx_w_book");
    press("c", "KeyC");
    const scroll = () => act(() => {
      document.querySelector('[data-span-id="fx_w_book_s1"]')?.dispatchEvent(new Event("scroll", { bubbles: false }));
    });
    scroll();
    expect(panel()?.getAttribute("data-companion-mode")).toBe("anchored");
    await act(async () => {
      vi.advanceTimersByTime(300);
    });
    scroll();
    expect(panel()?.getAttribute("data-companion-mode")).toBe("docked");
  });

  it("the overview shows it as the pill", async () => {
    mountCompanion({ reducedMotion: true });
    await screen.findByTestId("pane-fx_w_book");
    press("C", "KeyC", { shiftKey: true });
    alt("KeyO", "o");
    expect(document.querySelector("[data-desk-companion-pill]")?.className).toContain("on");
  });
});

describe("RD3b: asking (the job contract through the poller)", () => {
  it("Enter asks about the selection at once; the answer comes through the poller; a claim opens beside", async () => {
    const { transport, poller, answer, server } = mountCompanion();
    await screen.findByTestId("pane-fx_w_book");
    selectIn("fx_w_book", 1);
    press("c", "KeyC");
    const input = screen.getByLabelText("ask about this") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "why does it cancel?" } });
    fireEvent.keyDown(input, { key: "Enter", code: "Enter" });
    expect(panel()?.textContent).toContain("why does it cancel?");
    // Shown at once, waiting while the desk's writes are acknowledged (none are queued here), then asking.
    expect(panel()?.querySelector('[data-exchange-status="waiting"]')).not.toBeNull();
    await act(async () => {
      for (let i = 0; i < 6; i += 1) await Promise.resolve();
    });
    expect(panel()?.querySelector('[data-exchange-status="asking"]')).not.toBeNull();
    expect(transport.companionAsk).toHaveBeenCalledWith(expect.objectContaining({ surface: "desk", deskId: "fx_desk_softmax", extractionId: FIXTURE_SOURCES.book.extractionId, spanId: "fx_w_book_s1", question: "why does it cancel?", selectionQuote: "the first passage of fx_w_book" }));
    await act(async () => {
      await poller.tick();
    });
    expect(panel()?.textContent).toContain("2 pieces so far");
    answer();
    await act(async () => {
      await poller.tick();
    });
    expect(panel()?.querySelector('[data-exchange-status="answered"]')?.textContent).toContain("Because the factor cancels.");
    fireEvent.click(screen.getByRole("button", { name: /§ the passage/ }));
    await flush();
    // The cited passage's source is the book, already on the desk: it takes the focus (no second window).
    expect(server.state().desks[0].focusWindowId).toBe("fx_w_book");
  });

  it("a question waits until the desk writes it depends on are acknowledged, shown as waiting, and is asked after them", async () => {
    const { transport, answer: _answer, server } = mountCompanion();
    const order: string[] = [];
    const deskApply = server.apply.bind(server);
    server.apply = (input) => {
      order.push(`apply:${input.ops.map((op) => op.op).join(",")}`);
      return deskApply(input);
    };
    transport.companionAsk.mockImplementation(async (input: { requestId: string }) => {
      order.push("ask");
      return { version: 1, requestId: input.requestId, status: "queued", done: false, partialMd: "", citations: [], streamedPieces: 0, questionEventId: null, kept: false, answer: null, error: null };
    });
    await screen.findByTestId("pane-fx_w_book");
    // The focus moves (a desk write, queued for the idle flush) and the learner asks at once.
    alt("KeyL", "l");
    alt("KeyH", "h");
    selectIn("fx_w_book", 1);
    press("c", "KeyC");
    const input = screen.getByLabelText("ask about this") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "right away?" } });
    fireEvent.keyDown(input, { key: "Enter", code: "Enter" });
    expect(panel()?.querySelector('[data-exchange-status="waiting"]')).not.toBeNull();
    expect(order).toEqual([]);
    await act(async () => {
      for (let i = 0; i < 6; i += 1) await Promise.resolve();
    });
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    expect(order.length).toBeGreaterThan(1);
    expect(order[order.length - 1]).toBe("ask");
    expect(order.slice(0, -1).every((entry) => entry.startsWith("apply:"))).toBe(true);
  });

  it("a history anchor whose book is on no desk opens it beside, its source read from the passage's reading", async () => {
    const server = new FixtureDeskServer();
    const resolved: string[] = [];
    const { transport } = mountCompanion({
      transport: { ...transportFor(server), sourceOfExtraction: async (extractionId: string) => {
        resolved.push(extractionId);
        return "fx_src_elsewhere";
      } },
    });
    transport.companionHistory.mockResolvedValue({ version: 1, cursor: null, days: [{ date: "2026-11-20", desks: [{ deskId: null, exchanges: [{
      questionEventId: "q9", questionMd: "an old question", answerFirstSentence: "", answerStatus: "answered", context: "reader", surface: "reader", where: "in the Reader",
      origin: "live", goalId: null, padBlockIds: [], anchor: { extractionId: "fx_ext_elsewhere", spanId: "fx_ext_elsewhere_s2", quality: "exact_selection" }, createdAt: "2026-11-20T10:00:00Z" }] }] }] } as never);
    await screen.findByTestId("pane-fx_w_book");
    press("C", "KeyC", { shiftKey: true });
    fireEvent.click(screen.getByRole("tab", { name: "history" }));
    await flush();
    fireEvent.click(await screen.findByRole("button", { name: "§ the passage ↗" }));
    await flush();
    await flush();
    expect(resolved).toEqual(["fx_ext_elsewhere"]);
    const opened = server.batches.flatMap((batch) => batch.ops).find((op) => op.op === "open_window");
    expect(opened && opened.op === "open_window" ? opened.content : null).toMatchObject({ kind: "source", sourceId: "fx_src_elsewhere", extractionId: "fx_ext_elsewhere" });
  });

  it("a question whose window closes is read no more; nor is any once the shell detaches", async () => {
    const { poller, reads, view } = mountCompanion();
    await screen.findByTestId("pane-fx_w_book");
    selectIn("fx_w_book");
    press("c", "KeyC");
    const input = screen.getByLabelText("ask about this") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "a question" } });
    fireEvent.keyDown(input, { key: "Enter", code: "Enter" });
    await flush();
    await act(async () => {
      await poller.tick();
    });
    const before = reads.length;
    expect(before).toBeGreaterThan(0);
    // Close the window it was asked from (alt+w closes the focus).
    alt("KeyW", "w");
    await flush();
    expect(screen.queryByTestId("pane-fx_w_book")).toBeNull();
    await act(async () => {
      await poller.tick();
    });
    expect(reads.length).toBe(before);
    view.unmount();
    await act(async () => {
      await poller.tick();
    });
    expect(reads.length).toBe(before);
    expect(poller.size).toBe(0);
  });

  it("detached, the shell's threads stop polling; mounted again, they are followed again", async () => {
    const { poller, reads, view } = mountCompanion();
    await screen.findByTestId("pane-fx_w_book");
    selectIn("fx_w_book");
    press("c", "KeyC");
    const input = screen.getByLabelText("ask about this") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "still there?" } });
    fireEvent.keyDown(input, { key: "Enter", code: "Enter" });
    await flush();
    expect(poller.size).toBe(1);
    view.unmount();
    expect(poller.size).toBe(0);
    await act(async () => {
      await poller.tick();
    });
    expect(reads).toHaveLength(0);
  });

  it("a question from a window whose desk is left is not read until the learner comes back (paused windows ask nothing)", async () => {
    const { poller, reads } = mountCompanion();
    await screen.findByTestId("pane-fx_w_book");
    selectIn("fx_w_book");
    press("c", "KeyC");
    const input = screen.getByLabelText("ask about this") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "a question" } });
    fireEvent.keyDown(input, { key: "Enter", code: "Enter" });
    await act(async () => {
      await Promise.resolve();
    });
    alt("KeyJ", "j");
    await screen.findByTestId("pane-fx_w_video2");
    await act(async () => {
      await poller.tick();
    });
    expect(reads).toEqual([]);
    alt("KeyK", "k");
    await act(async () => {
      await poller.tick();
    });
    expect(reads.length).toBe(1);
  });

  it("typing in the companion's input: a bare c stays in the field, alt+c still hides it", async () => {
    mountCompanion();
    await screen.findByTestId("pane-fx_w_book");
    press("C", "KeyC", { shiftKey: true });
    const input = screen.getByLabelText("ask about this") as HTMLInputElement;
    act(() => input.focus());
    act(() => {
      fireEvent.keyDown(input, { key: "c", code: "KeyC" });
    });
    expect(panel()?.getAttribute("data-companion-mode")).toBe("docked");
    alt("KeyC", "c", {}, input);
    expect(panel()?.className).toContain("leaving-hide");
  });
});

describe("RD3b: search in context (spec §9.3)", () => {
  it("/ opens it; while it is open its keys are its own: x swaps nothing and alt+l moves no focus", async () => {
    const { server } = mountCompanion();
    await screen.findByTestId("pane-fx_w_book");
    press("/", "Slash");
    expect(screen.getByRole("dialog", { name: "search in context" })).toBeTruthy();
    act(() => {
      fireEvent.keyDown(window, { key: "x", code: "KeyX" });
    });
    alt("KeyL", "l");
    await flush();
    expect(server.batches).toEqual([]);
    expect(state("fx_w_book")).toBe("active");
  });

  it("words come back grouped, with open on this desk first; ↓ and ↵ open the chosen result, or go to it where it is open", async () => {
    const { server, transport } = mountCompanion();
    await screen.findByTestId("pane-fx_w_book");
    press("/", "Slash");
    const input = screen.getByLabelText("search every source, note, pad, thread and past exchange");
    fireEvent.change(input, { target: { value: "att" } });
    await act(async () => {
      vi.advanceTimersByTime(200);
      await Promise.resolve();
    });
    expect(transport.searchEverything).toHaveBeenCalledWith({ query: "att", deskId: "fx_desk_softmax" });
    const groups = [...document.querySelectorAll("[data-search-group]")].map((group) => group.getAttribute("data-search-group"));
    expect(groups[0]).toBe("open");
    expect(groups).toContain("sources");
    expect(document.querySelector(".desk-search-foot")?.textContent).toContain("no meaning index of pad text");
    // The first row is the open window; ↓ to the library's source, ↵ opens it beside.
    const openRows = document.querySelectorAll('[data-search-group="open"] [data-search-row]').length;
    for (let i = 0; i < openRows; i += 1) fireEvent.keyDown(input, { key: "ArrowDown" });
    fireEvent.keyDown(input, { key: "Enter" });
    await flush();
    // The paper is already on this desk: it takes the focus, and no second window opens.
    expect(server.batches.flatMap((batch) => batch.ops).some((op) => op.op === "open_window")).toBe(false);
    expect(server.state().desks[0].focusWindowId).toBe("fx_w_paper");
  });

  it("a result not on the desk opens beside the focus", async () => {
    const { server, transport } = mountCompanion();
    await screen.findByTestId("pane-fx_w_book");
    transport.searchEverything.mockResolvedValueOnce({
      version: 1, query: "masks",
      groups: [{ group: "sources", label: "sources in your library", basis: "words", status: "ok", more: false,
        rows: [{ ref: { kind: "video", sourceId: FIXTURE_SOURCES.video2.sourceId, extractionId: FIXTURE_SOURCES.video2.extractionId }, target: null, sourceId: FIXTURE_SOURCES.video2.sourceId, extractionId: FIXTURE_SOURCES.video2.extractionId, title: "Masks", readerEnabled: true, openOnDeskIds: ["fx_desk_attention"], onThisDesk: false }] }],
      meaning: { status: "unavailable", jobId: null, unavailable: [] },
    } as never);
    press("/", "Slash");
    const input = screen.getByLabelText("search every source, note, pad, thread and past exchange");
    fireEvent.change(input, { target: { value: "masks" } });
    await act(async () => {
      vi.advanceTimersByTime(200);
      await Promise.resolve();
    });
    fireEvent.keyDown(input, { key: "Enter" });
    await flush();
    const opened = server.batches.flatMap((batch) => batch.ops).find((op) => op.op === "open_window");
    expect(opened && opened.op === "open_window" ? opened.content : null).toMatchObject({ kind: "video", sourceId: FIXTURE_SOURCES.video2.sourceId });
  });

  it("a note result opens its note by its identity: a Reader note at its passage in its book, an inbox note said where it lives", async () => {
    const { server, transport } = mountCompanion();
    await screen.findByTestId("pane-fx_w_book");
    const noteRows = [
      { ref: { kind: "video", sourceId: FIXTURE_SOURCES.video2.sourceId, extractionId: FIXTURE_SOURCES.video2.extractionId }, target: { spanId: "fx_v2_c3", noteKey: "annotation:an7", annotationId: "an7" },
        noteKind: "note", noteKey: "annotation:an7", noteRefKind: "annotation", title: "masks", heading: null, snippet: "masks hide the future", capturedOn: null, byMeaning: false },
      { ref: { kind: "panel", panel: "notes" }, target: { noteKey: "capture:cap3", captureId: "cap3" },
        noteKind: "note", noteKey: "capture:cap3", noteRefKind: "capture", title: "masks, again", heading: null, snippet: "ask about causal masks", capturedOn: "2026-11-20", byMeaning: false },
    ];
    for (const index of [0, 1]) {
      transport.searchEverything.mockResolvedValueOnce({
        version: 1, query: "masks",
        groups: [{ group: "notes", label: "your notes", basis: "words", status: "ok", more: false, rows: [noteRows[index]] }],
        meaning: { status: "unavailable", jobId: null, unavailable: [] },
      } as never);
    }
    const search = async (title: string) => {
      press("/", "Slash");
      const input = screen.getByLabelText("search every source, note, pad, thread and past exchange");
      fireEvent.change(input, { target: { value: "masks" } });
      await act(async () => {
        vi.advanceTimersByTime(200);
        await Promise.resolve();
      });
      // The note's row (the window opened by the first search is in "open on this desk" above it).
      const row = [...document.querySelectorAll<HTMLElement>("[data-search-row]")].find((each) => each.textContent?.includes(title));
      fireEvent.click(row as HTMLElement);
      await flush();
    };
    await search("masks hide");
    const opened = server.batches.flatMap((batch) => batch.ops).filter((op) => op.op === "open_window");
    expect(opened).toHaveLength(1);
    expect(opened[0].op === "open_window" ? [opened[0].content, opened[0].view] : null).toMatchObject([
      { kind: "video", sourceId: FIXTURE_SOURCES.video2.sourceId }, { spanId: "fx_v2_c3", noteKey: "annotation:an7", annotationId: "an7" },
    ]);
    await act(async () => {
      vi.advanceTimersByTime(500);
    });
    await search("ask about causal masks");
    // No desk window shows an inbox note: nothing opens (no unbound Notes panel), and it says where the note is.
    expect(server.batches.flatMap((batch) => batch.ops).filter((op) => op.op === "open_window")).toHaveLength(1);
    expect(document.querySelector(".desk-toast")?.textContent).toMatch(/inbox note/);
  });

  it("esc closes it", async () => {
    mountCompanion({ reducedMotion: true });
    await screen.findByTestId("pane-fx_w_book");
    press("/", "Slash");
    fireEvent.keyDown(screen.getByLabelText("search every source, note, pad, thread and past exchange"), { key: "Escape" });
    expect(screen.queryByRole("dialog", { name: "search in context" })).toBeNull();
  });
});

describe("RD4b: pads in the desks", () => {
  function padsTransport(server: FixtureDeskServer) {
    const calls: Array<[string, unknown]> = [];
    return {
      calls,
      transport: {
        padProposals: async (input: { padId: string }) => ({ version: 1, padId: input.padId, proposals: [] }),
        proposalLabel: async () => ({}),
        padSubmitBlock: async () => ({}) as never,
        carriedCarry: async (input: unknown) => {
          calls.push(["carriedCarry", input]);
          return { carried: {} as never, created: true };
        },
        requestTeachBack: async () => ({ practiceItemId: "tb" }),
        passageUnionRange: async () => ({ sections: [], spans: [] }) as never,
        authorPracticeItem: async () => ({ practiceItemId: "x" }),
        workbenchOpenProblems: async () => ({ problems: [] }),
        submitTeachBackTurn: async () => ({ done: true }) as never,
        getSession: async () => ({ checkpoint: null }) as never,
        passageContent: async () => ({ version: 1, extractionId: "", sourceId: null, title: null, withheld: false, spans: [] }) as never,
        padDrain: async ({ deskId }: { deskId: string }) => ({
          version: 1, deskId, day: "2026-11-23",
          pads: [{ padId: "fx_pad_running", kind: "running", title: "running", kept: false, version: 1, firstLine: "softmax keeps the winner", lastLine: "is it the same move?", carryCandidate: "is it the same move?", updatedAt: "2026-11-23T10:00:00Z" }],
        }) as never,
        carriedList: async () => ({ carried: [], shelfLimit: 3 }),
        carriedMark: async (_input: unknown) => ({}),
        figureRequest: async () => ({ jobId: "j", kind: "figure_build", askId: null, state: "done", result: { figure: null, reused: false } }) as never,
        readerFigureJob: async () => ({ jobId: "j", kind: "figure_build", askId: null, state: "done", result: null }) as never,
      },
      deskTransport: {
        ...transportFor(server),
        applyPad: async (input: Parameters<FixtureDeskServer["applyPad"]>[0]) => server.applyPad(input),
        padGet: async ({ padId }: { padId: string }) => server.padGet(padId),
      },
    };
  }

  it("alt+n away from a pad stack opens a new pad in a stack window beside the focus, and focuses it", async () => {
    const server = new FixtureDeskServer();
    const fakes = padsTransport(server);
    mount(server, { transport: fakes.deskTransport, padsTransport: fakes.transport });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyN", "n");
    await flush();
    const created = server.padBatches.flatMap((batch) => batch.ops).find((op) => op.op === "create_pad");
    expect(created).toMatchObject({ op: "create_pad", kind: "named", title: "Scratchpad · new notes", homeDeskId: "fx_desk_softmax" });
    const desk = server.state().desks.find((each) => each.deskId === "fx_desk_softmax");
    const slots = desk?.slots ?? [];
    const stackWindow = slots.flatMap((slot) => slot.windows).find((window) => window.windowId === desk?.focusWindowId);
    expect(stackWindow?.kind).toBe("pad_stack");
    expect(stackWindow?.stack).toEqual([{ kind: "pad", padId: server.padBatches[0].padId }]);
    // Beside the book: the slot after it.
    const slotOf = (windowId: string) => slots.findIndex((slot) => slot.windows.some((window) => window.windowId === windowId));
    expect(slotOf(stackWindow?.windowId ?? "")).toBe(slotOf("fx_w_book") + 1);
  });

  it("alt+shift+q opens the drain: one key keeps a pad, another carries its last question; while open the desk's keys wait", async () => {
    const server = new FixtureDeskServer();
    const fakes = padsTransport(server);
    mount(server, { transport: fakes.deskTransport, padsTransport: fakes.transport });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyQ", "Q", { shiftKey: true });
    const drain = await screen.findByRole("dialog", { name: "closing softmax and cross-entropy" });
    expect(drain.textContent).toContain("Closing “softmax and cross-entropy”");
    expect(drain.textContent).toContain("carry “is it the same move?”");
    // The drain owns the keys: alt+l does not move the focus while it is open.
    alt("KeyL", "l");
    await flush();
    expect(server.state().desks[0].focusWindowId).toBe("fx_w_book");
    press("1", "Digit1");
    press("k", "KeyK");
    await waitFor(() => expect(drain.textContent).toContain("kept"));
    await flush();
    expect(server.padBatches.flatMap((batch) => batch.ops)).toEqual([{ op: "keep", expectedVersion: 1 }]);
    press("Escape", "Escape");
    expect(screen.queryByRole("dialog", { name: "closing softmax and cross-entropy" })).toBeNull();
  });

  it("the shelf's CARRIED shows at most the attention limit, each since its date, and says how many more", async () => {
    const server = new FixtureDeskServer();
    const fakes = padsTransport(server);
    const question = (n: number) => ({ carriedId: `c${n}`, text: `question ${n}?`, originKind: "typed", originRef: null, anchor: null, deskId: null, since: "2026-11-20T10:00:00Z", state: "carried", carried: true, version: 1, updatedAt: "2026-11-20T10:00:00Z" });
    fakes.transport.carriedList = async () => ({ carried: [1, 2, 3, 4].map(question) as never, shelfLimit: 3 });
    mount(server, { transport: fakes.deskTransport, padsTransport: fakes.transport });
    await screen.findByTestId("pane-fx_w_book");
    const shelf = await waitFor(() => {
      const found = document.querySelector("[data-shelf-carried]") as HTMLElement | null;
      expect(found).not.toBeNull();
      return found as HTMLElement;
    });
    expect(shelf.querySelectorAll(".q")).toHaveLength(3);
    expect(shelf.textContent).toContain("since 20 Nov");
    // The rest is a working link to every carried question (not a mention of the library).
    expect(within(shelf).getByRole("button", { name: /all carried questions \(1 more\)/ })).toBeTruthy();
  });

  it("the shelf's link opens every carried question, page by page, each with fruitful, not now and let it go", async () => {
    const server = new FixtureDeskServer();
    const fakes = padsTransport(server);
    const question = (n: number) => ({ carriedId: `c${n}`, text: `question ${n}?`, originKind: "typed", originRef: null, anchor: null, deskId: null, since: "2026-11-20T10:00:00Z", state: "carried", carried: true, version: n, updatedAt: "2026-11-20T10:00:00Z" });
    const pages: Array<string | undefined> = [];
    fakes.transport.carriedList = (async (input: { cursor?: string }) => {
      pages.push(input.cursor);
      return input.cursor ? { carried: [question(5)], shelfLimit: 3, cursor: null } : { carried: [1, 2, 3, 4].map(question), shelfLimit: 3, cursor: "c4" };
    }) as never;
    const marks: unknown[] = [];
    fakes.transport.carriedMark = async (input: unknown) => {
      marks.push(input);
      return {};
    };
    mount(server, { transport: fakes.deskTransport, padsTransport: fakes.transport });
    await screen.findByTestId("pane-fx_w_book");
    await flush();
    const shelf = document.querySelector("[data-shelf-carried]") as HTMLElement;
    expect(shelf.querySelectorAll(".q")).toHaveLength(3);
    fireEvent.click(screen.getByRole("button", { name: /all carried questions/ }));
    const list = await screen.findByRole("dialog", { name: "carried questions" });
    expect(list.querySelectorAll("[data-carried-row]")).toHaveLength(4);
    fireEvent.click(screen.getByRole("button", { name: /older/ }));
    await flush();
    expect(list.querySelectorAll("[data-carried-row]")).toHaveLength(5);
    expect(pages).toContain("c4");
    const row = list.querySelector('[data-carried-row="c2"]') as HTMLElement;
    fireEvent.click(within(row).getByRole("button", { name: "let it go" }));
    await flush();
    expect(marks[marks.length - 1]).toMatchObject({ carriedId: "c2", event: "let_go", expectedVersion: 2 });
    expect(list.querySelector('[data-carried-row="c2"]')).toBeNull();
  });

  it("a passage's ✎ marks come from the passage union (no pad loaded), an alias that needs re-anchoring marked as such", async () => {
    const server = new FixtureDeskServer();
    const fakes = padsTransport(server);
    const asked: unknown[] = [];
    fakes.transport.passageUnionRange = (async (input: unknown) => {
      asked.push(input);
      return { version: 1, extractionId: FIXTURE_SOURCES.book.extractionId, sections: [], spans: [
        { spanId: "fx_w_book_s1", sectionId: null, annotations: [], exchanges: [], adjustments: [], padBlocks: [{ blockId: "b_old", padId: "p_old", kind: "text", provenance: "learner", eventId: "e1", annotationId: null, alias: "needs_reanchor" }] },
        { spanId: "fx_w_book_s2", sectionId: null, annotations: [], exchanges: [], adjustments: [], padBlocks: [{ blockId: "b9", padId: "p9", kind: "source_quote", provenance: "source", eventId: "e2", annotationId: null, alias: "exact" }] },
      ] };
    }) as never;
    mount(server, { transport: fakes.deskTransport, padsTransport: fakes.transport, renderPane: (input) => <PassagePane input={input} /> });
    await screen.findByTestId("pane-fx_w_book");
    await flush();
    await flush();
    expect(asked.some((input) => (input as { extractionId: string }).extractionId === FIXTURE_SOURCES.book.extractionId)).toBe(true);
    const marks = [...document.querySelectorAll<HTMLElement>(".desk-pmark.pad")];
    expect(marks).toHaveLength(2);
    expect(marks.filter((mark) => mark.classList.contains("reanchor"))).toHaveLength(1);
    expect(marks.find((mark) => mark.classList.contains("reanchor"))?.getAttribute("title")).toMatch(/re-anchor/);
  });

  it("a carried question comes back as a quiet ◌ beside its passage: shown once is logged as surfaced, and it can be let go", async () => {
    const server = new FixtureDeskServer();
    const fakes = padsTransport(server);
    const marks: unknown[] = [];
    fakes.transport.carriedList = async () => ({ carried: [{ carriedId: "c1", text: "does it work for any base?", originKind: "typed", originRef: null, anchor: { extraction_id: FIXTURE_SOURCES.book.extractionId, span_id: "fx_w_book_s2" }, deskId: null, since: "2026-11-21T10:00:00Z", state: "carried", carried: true, version: 3, updatedAt: "2026-11-21T10:00:00Z" }] as never, shelfLimit: 3 });
    fakes.transport.carriedMark = async (input: unknown) => {
      marks.push(input);
      return {};
    };
    mount(server, { transport: fakes.deskTransport, padsTransport: fakes.transport, renderPane: (input) => <PassagePane input={input} /> });
    await screen.findByTestId("pane-fx_w_book");
    const mark = await screen.findByRole("button", { name: "a question you carried" });
    await flush();
    await flush();
    expect(marks.filter((each) => (each as { event: string }).event === "surfaced")).toHaveLength(1);
    fireEvent.click(mark);
    expect(screen.getByText(/you carried: does it work for any base\? · since 21 Nov/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "let it go" }));
    await flush();
    expect(marks[marks.length - 1]).toMatchObject({ carriedId: "c1", event: "let_go", expectedVersion: 3 });
  });

  it("the drain says carried or kept only once it is saved; a failed carry keeps its controls and says why", async () => {
    const server = new FixtureDeskServer();
    const fakes = padsTransport(server);
    fakes.transport.carriedCarry = async () => {
      throw { code: "sidecar_unavailable", message: "LearnLoop is not running" };
    };
    mount(server, { transport: fakes.deskTransport, padsTransport: fakes.transport });
    await screen.findByTestId("pane-fx_w_book");
    alt("KeyQ", "Q", { shiftKey: true });
    const drain = await screen.findByRole("dialog", { name: "closing softmax and cross-entropy" });
    press("1", "Digit1");
    press("c", "KeyC");
    await flush();
    await flush();
    expect(drain.textContent).not.toContain("carried");
    expect(drain.textContent).toContain("LearnLoop is not running");
    expect(drain.querySelector("[data-drain-pad] .acts")).not.toBeNull();
  });

  it("an answer proposes a diff into the desk's running pad; accept writes it as the tutor's words", async () => {
    const server = new FixtureDeskServer();
    const fakes = padsTransport(server);
    const { poller, answer } = mountCompanion({ transport: fakes.deskTransport, padsTransport: fakes.transport });
    await screen.findByTestId("pane-fx_w_book");
    selectIn("fx_w_book", 1);
    press("c", "KeyC");
    const input = screen.getByLabelText("ask about this") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "why does it cancel?" } });
    fireEvent.keyDown(input, { key: "Enter", code: "Enter" });
    await act(async () => {
      await Promise.resolve();
    });
    answer();
    await act(async () => {
      await poller.tick();
    });
    const diff = await waitFor(() => {
      const found = document.querySelector("[data-diff]") as HTMLElement | null;
      expect(found).not.toBeNull();
      return found as HTMLElement;
    });
    expect(diff.textContent).toContain("Add this to your pad");
    expect(diff.textContent).toContain("+ Because the factor cancels.");
    fireEvent.click(screen.getByRole("button", { name: "accept" }));
    await waitFor(() => expect(diff.textContent).toContain("accepted"));
    await flush();
    const inserted = server.padBatches.flatMap((batch) => batch.ops).find((op) => op.op === "insert_block");
    expect(inserted).toMatchObject({ op: "insert_block", kind: "tutor_quote", provenance: "tutor", bodyMd: "Because the factor cancels." });
    expect(server.padBatches[0].padId).toBe("fx_pad_running");
  });
});

describe("RD4 review: asking from a pad line", () => {
  const ws = (() => {
    const state = fixtureDeskState();
    return { ...fromDeskState(state), closed: {} };
  })();
  it("an anchored pad line grounds the question in its passage, with the pad block named", () => {
    const grounding = groundingFor(ws, { spanIds: [], windowId: "fx_w_pads", pad: { padId: "fx_pad_running", blockId: "fx_b_r2", anchor: { extractionId: "fx_ext_softmax", spanId: "fx_ext_softmax_s1_3" } } }, ws.windows.fx_w_pads, {});
    expect(grounding).toMatchObject({ reason: null, extractionId: "fx_ext_softmax", spanId: "fx_ext_softmax_s1_3", padBlockId: "fx_b_r2" });
  });

  it("an unanchored pad line is asked beside the desk's book (where the learner reads), the line named", () => {
    const grounding = groundingFor(ws, { spanIds: [], windowId: "fx_w_pads", pad: { padId: "fx_pad_running", blockId: "fx_b_r1", anchor: null } }, ws.windows.fx_w_pads, { fx_w_book: { readingSpan: "fx_ext_softmax_s2_1" } });
    expect(grounding).toMatchObject({ reason: null, extractionId: "fx_ext_softmax", spanId: "fx_ext_softmax_s2_1", windowId: "fx_w_pads", spanWindowId: "fx_w_book", padBlockId: "fx_b_r1" });
  });

  it("an unanchored pad line on a desk with no book or video says why it cannot ask", () => {
    const empty = { ...ws, windows: { fx_w_pads: ws.windows.fx_w_pads } };
    const grounding = groundingFor(empty, { spanIds: [], windowId: "fx_w_pads", pad: { padId: "fx_pad_running", blockId: "fx_b_r1", anchor: null } }, ws.windows.fx_w_pads, {});
    expect(grounding.reason).toMatch(/linked to no passage/);
  });
});

describe("RD4 review: the running pad and stack membership on the desks", () => {
  it("a desk with no running pad in its stacks gets one ensured (an idempotent desk op) when it opens", async () => {
    const state = fixtureDeskState();
    const server = new FixtureDeskServer({ ...state, runningPadIds: [] });
    mount(server, { transport: { ...transportFor(server), padGet: async ({ padId }: { padId: string }) => server.padGet(padId) } });
    await screen.findByTestId("pane-fx_w_book");
    await flush();
    const ensured = server.batches.flatMap((batch) => batch.ops).filter((op) => op.op === "ensure_running_pad");
    expect(ensured).toHaveLength(1);
    expect(ensured[0]).toMatchObject({ op: "ensure_running_pad", deskId: "fx_desk_softmax", title: "running" });
  });

  it("a desk whose stacks hold its running pad sends nothing", async () => {
    const server = new FixtureDeskServer();
    mount(server);
    await screen.findByTestId("pane-fx_w_book");
    await flush();
    expect(server.batches.flatMap((batch) => batch.ops).some((op) => op.op === "ensure_running_pad")).toBe(false);
  });

  it("pads an earlier build kept in a stack window's view join its stack by add_to_stack", async () => {
    const state = fixtureDeskState();
    const desk = state.desks[0];
    const stackSlot = desk.slots.find((slot) => slot.windows.some((window) => window.kind === "pad_stack"))!;
    stackSlot.windows = stackSlot.windows.map((window) => (window.kind === "pad_stack" ? { ...window, view: { addedPads: ["fx_pad_deriving", "fx_pad_lifted_old"] } } : window));
    const server = new FixtureDeskServer(state);
    mount(server);
    await screen.findByTestId("pane-fx_w_book");
    await flush();
    const added = server.batches.flatMap((batch) => batch.ops).filter((op) => op.op === "add_to_stack");
    // fx_pad_deriving is already in the stack: only the other one is added.
    expect(added.map((op) => (op as { entry: { padId: string } }).entry.padId)).toEqual(["fx_pad_lifted_old"]);
  });
});

describe("RD4 review: a pad's back-link reopens its source", () => {
  function BackLinkPane({ input, target }: { input: PaneRenderInput; target: [string, string, number | undefined, string | undefined] }) {
    const host = usePadsHost();
    return (
      <div data-testid={`pane-${input.window.windowId}`} data-state={input.lifecycle.state}>
        <button type="button" onClick={() => host?.openPassage(...target)}>{`back from ${input.window.windowId}`}</button>
      </div>
    );
  }

  it("a quote's back-link to a source on no desk opens it beside, at the stored passage", async () => {
    const server = new FixtureDeskServer();
    mount(server, { renderPane: (input) => <BackLinkPane input={input} target={["fx_ext_closed", "fx_ext_closed_s4", undefined, "fx_src_closed"]} /> });
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.click(screen.getByText("back from fx_w_book"));
    await flush();
    const opened = server.batches.flatMap((batch) => batch.ops).find((op) => op.op === "open_window");
    expect(opened && opened.op === "open_window" ? [opened.content, opened.view] : null).toMatchObject([{ kind: "source", sourceId: "fx_src_closed", extractionId: "fx_ext_closed" }, { spanId: "fx_ext_closed_s4" }]);
  });

  it("a video piece's back-link with no source id reads it from the reading and opens the video at its time", async () => {
    const server = new FixtureDeskServer();
    const library = [...FIXTURE_LIBRARY, { ...FIXTURE_LIBRARY[0], sourceId: "fx_src_closed_video", title: "a closed video", kindNoun: "video", acquisitionKind: "youtube" }];
    mount(server, {
      transport: { ...transportFor(server, library as never), sourceOfExtraction: async () => "fx_src_closed_video" },
      renderPane: (input) => <BackLinkPane input={input} target={["fx_ext_closed_video", "fx_ext_closed_video_c3", 72, undefined]} />,
    });
    await screen.findByTestId("pane-fx_w_book");
    fireEvent.click(screen.getByText("back from fx_w_book"));
    await flush();
    await flush();
    const opened = server.batches.flatMap((batch) => batch.ops).find((op) => op.op === "open_window");
    expect(opened && opened.op === "open_window" ? opened.content : null).toMatchObject({ kind: "video", sourceId: "fx_src_closed_video", extractionId: "fx_ext_closed_video", t: 72 });
  });
});
