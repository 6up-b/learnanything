// The key router (spec §5.4, §18.2): every chord reaches its owner scope and no other, the typing
// scope passes only the Alt chords marked for it, focus mode passes the reading view's keys, the
// bare-Alt tap clears while a 400 ms hold shows which-key, and modifiers come from key events.
import { describe, expect, it } from "vitest";
import { shellBindings } from "../../../app/keymap";
import {
  BareAltTracker,
  DESK_BINDINGS,
  ModifierTracker,
  SCOPE_ORDER,
  WHICH_KEY_HOLD_MS,
  isTypingTarget,
  openScopes,
  resolveKey,
  type DeskScope,
  type KeyLike,
  type ScopeState,
  type Timers,
} from "./router";

function key(init: Partial<KeyLike>): KeyLike {
  return { key: "", code: "", altKey: false, ctrlKey: false, metaKey: false, shiftKey: false, ...init };
}

function eventFor(chord: (typeof DESK_BINDINGS)[number]["chord"]): KeyLike {
  return key({
    key: chord.key ?? "",
    code: chord.code ?? "",
    altKey: Boolean(chord.alt),
    ctrlKey: Boolean(chord.ctrl),
    shiftKey: Boolean(chord.shift),
  });
}

const mods = (event: KeyLike) => ({ alt: event.altKey, ctrl: event.ctrlKey || event.metaKey });

function stateFor(scope: DeskScope): ScopeState {
  return scope === "reading" ? {} : { [scope]: true } as ScopeState;
}

describe("the resolved scope and precedence matrix", () => {
  it("lists the scopes highest first, with the reading view always open beneath", () => {
    expect(SCOPE_ORDER).toEqual(["notebook", "check", "menu", "typing", "arrange", "pen", "overview", "focus", "reading"]);
    expect(openScopes({})).toEqual(["reading"]);
    expect(openScopes({ typing: true, focus: true })).toEqual(["typing", "focus", "reading"]);
  });

  it("gives every chord one binding per scope: no two bindings of a scope share a chord", () => {
    for (const scope of SCOPE_ORDER) {
      const seen = new Map<string, string>();
      for (const binding of DESK_BINDINGS.filter((each) => each.scopes.includes(scope))) {
        const id = JSON.stringify(binding.chord);
        expect(seen.get(id), `${scope}: ${binding.id} and ${seen.get(id)}`).toBeUndefined();
        seen.set(id, binding.id);
      }
    }
  });

  it("reaches each chord's owner in each scope it names, and no other binding", () => {
    for (const binding of DESK_BINDINGS) {
      for (const scope of binding.scopes) {
        const event = eventFor(binding.chord);
        const resolved = resolveKey(event, stateFor(scope), mods(event));
        expect(resolved?.binding.id, `${binding.id} in ${scope}`).toBe(binding.id);
        expect(resolved?.scope).toBe(scope);
      }
    }
  });

  it("the typing scope keeps every bare key and passes only its Alt chords", () => {
    const typing: ScopeState = { typing: true };
    for (const bare of ["c", "x", "/", " ", "p", "n", "b", "o"]) {
      expect(resolveKey(key({ key: bare }), typing, { alt: false, ctrl: false }), bare).toBeNull();
    }
    for (const code of ["KeyH", "KeyL", "KeyJ", "KeyK", "BracketLeft", "BracketRight", "Comma", "Period", "Enter"]) {
      expect(resolveKey(key({ code, altKey: true }), typing, { alt: true, ctrl: false })?.scope, code).toBe("typing");
    }
    // alt+w closes nothing while typing.
    expect(resolveKey(key({ code: "KeyW", altKey: true }), typing, { alt: true, ctrl: false })).toBeNull();
  });

  it("focus mode owns = - 0 esc and alt+h/l, and passes the reading view's keys", () => {
    const focus: ScopeState = { focus: true };
    expect(resolveKey(key({ key: "=" }), focus, { alt: false, ctrl: false })?.binding.action).toEqual({ kind: "docZoom", direction: 1 });
    expect(resolveKey(key({ key: "Escape" }), focus, { alt: false, ctrl: false })?.binding.action).toEqual({ kind: "leaveFocusMode" });
    expect(resolveKey(key({ key: "x" }), focus, { alt: false, ctrl: false })?.scope).toBe("reading");
    // Outside focus mode the zoom keys and esc are not the workbench's.
    expect(resolveKey(key({ key: "=" }), {}, { alt: false, ctrl: false })).toBeNull();
    expect(resolveKey(key({ key: "Escape" }), {}, { alt: false, ctrl: false })).toBeNull();
  });

  it("an open menu, check card or arrange overlay passes nothing to the workbench", () => {
    for (const blocker of ["menu", "check", "arrange", "notebook"] as const) {
      const state: ScopeState = { [blocker]: true };
      expect(resolveKey(key({ code: "KeyH", altKey: true }), state, { alt: true, ctrl: false }), blocker).toBeNull();
      expect(resolveKey(key({ key: "x" }), state, { alt: false, ctrl: false }), blocker).toBeNull();
    }
  });

  it("pen mode passes every key", () => {
    expect(resolveKey(key({ key: "x" }), { pen: true }, { alt: false, ctrl: false })?.scope).toBe("reading");
  });

  it("a modifier tracked from the keys counts when the event says otherwise (WebKitGTK)", () => {
    const tracker = new ModifierTracker();
    tracker.keydown({ key: "Alt" });
    const bareH = key({ code: "KeyH" });
    expect(resolveKey(bareH, {}, tracker.read(bareH))?.binding.id).toBe("move.left");
    tracker.blur();
    expect(resolveKey(bareH, {}, tracker.read(bareH))).toBeNull();
    tracker.keydown({ key: "Control" });
    expect(tracker.read()).toEqual({ alt: false, ctrl: true });
    tracker.keyup({ key: "Control" });
    expect(tracker.read({ metaKey: true })).toEqual({ alt: false, ctrl: true });
  });

  it("collides with no shell chord: Alt+S stays Settings, so arranging pads is alt+a", () => {
    const shellChords = new Set<string>();
    for (const shell of ["simple", "classic"] as const) {
      for (const binding of shellBindings(shell)) {
        if (binding.chord.alt) shellChords.add(`alt+${binding.chord.key.toLowerCase()}`);
        if (binding.chord.mod) shellChords.add(`ctrl+${binding.chord.key.toLowerCase()}`);
      }
    }
    for (const binding of DESK_BINDINGS) {
      const letter = binding.chord.code?.replace(/^Key/, "").toLowerCase() ?? binding.chord.key?.toLowerCase();
      if (binding.chord.alt) expect(shellChords.has(`alt+${letter}`), binding.id).toBe(false);
      if (binding.chord.ctrl) expect(shellChords.has(`ctrl+${letter}`), binding.id).toBe(false);
    }
    expect(DESK_BINDINGS.find((binding) => binding.id === "pads.arrange")?.keys).toBe("alt+a");
  });

  it("names the stage of every chord whose feature is not built yet", () => {
    const later = DESK_BINDINGS.filter((binding) => binding.later).map((binding) => `${binding.keys}:${binding.later}`);
    // RD2 built the overview, gather and moving a card to another desk: none of them waits any more.
    expect(later.filter((entry) => entry.endsWith(":RD2"))).toEqual([]);
    // RD3 built the companion and search: c, shift+c, alt+c and / wait no more.
    expect(later.filter((entry) => entry.endsWith(":RD3"))).toEqual([]);
    // RD4 built the pads: new pad, arrange, sketch, the pad tabs, the drain and the menu on a pad line.
    expect(later.filter((entry) => entry.endsWith(":RD4"))).toEqual([]);
    expect(later).toContain("alt+;:RD10");
    const built = DESK_BINDINGS.filter((binding) => !binding.later).map((binding) => binding.keys);
    expect(built).toEqual(expect.arrayContaining(["alt+h", "alt+l", "alt+j", "alt+k", "alt+[", "alt+]", "alt+↵", "alt+w", "alt+,", "alt+.", "space", "x", "=", "-", "0", "esc", "alt+o", "o", "alt+g", "alt+shift+g", "alt+shift+j", "alt+shift+k", "b", "g (hold)", "↵", "c", "shift+c", "alt+c", "/", "alt+n", "alt+a", "alt+d", "alt+shift+q", "."]));
  });

  it("the overview owns its navigation keys and passes the reading view's keys nowhere", () => {
    const ov: ScopeState = { overview: true };
    for (const [key, code, alt] of [["h", "KeyH", false], ["ArrowDown", "ArrowDown", false], ["l", "KeyL", true]] as const) {
      const event = key.length === 1 ? { key, code, altKey: alt, ctrlKey: false, metaKey: false, shiftKey: false } : { key, code, altKey: false, ctrlKey: false, metaKey: false, shiftKey: false };
      expect(resolveKey(event, ov, { alt, ctrl: false })?.binding.action.kind, key).toBe("overviewMove");
    }
    expect(resolveKey(key({ key: "Enter", code: "Enter" }), ov, { alt: false, ctrl: false })?.binding.action).toEqual({ kind: "overviewOpen", focusMode: false });
    expect(resolveKey(key({ key: "Enter", code: "Enter", altKey: true }), ov, { alt: true, ctrl: false })?.binding.action).toEqual({ kind: "overviewOpen", focusMode: true });
    expect(resolveKey(key({ key: "Escape", code: "Escape" }), ov, { alt: false, ctrl: false })?.binding.action).toEqual({ kind: "leaveOverview" });
    expect(resolveKey(key({ key: "b", code: "KeyB" }), ov, { alt: false, ctrl: false })?.binding.action).toEqual({ kind: "toggleRelations" });
    // The reading view's swap and close are not the overview's.
    expect(resolveKey(key({ key: "x", code: "KeyX" }), ov, { alt: false, ctrl: false })).toBeNull();
    expect(resolveKey(key({ code: "KeyW", altKey: true }), ov, { alt: true, ctrl: false })).toBeNull();
    // Outside the overview, h is the window's (a bare letter) and alt+h moves the focus.
    expect(resolveKey(key({ key: "h", code: "KeyH" }), {}, { alt: false, ctrl: false })).toBeNull();
    expect(resolveKey(key({ code: "KeyH", altKey: true }), {}, { alt: true, ctrl: false })?.binding.id).toBe("move.left");
  });
});

class FakeTimers implements Timers {
  time = 0;
  private queue: Array<{ at: number; fn: () => void; id: number }> = [];
  private next = 1;
  set(fn: () => void, ms: number): unknown {
    const id = this.next++;
    this.queue.push({ at: this.time + ms, fn, id });
    return id;
  }
  clear(handle: unknown): void {
    this.queue = this.queue.filter((entry) => entry.id !== handle);
  }
  now(): number {
    return this.time;
  }
  advance(ms: number): void {
    this.time += ms;
    const due = this.queue.filter((entry) => entry.at <= this.time);
    this.queue = this.queue.filter((entry) => entry.at > this.time);
    for (const entry of due) entry.fn();
  }
}

describe("the bare-Alt rule", () => {
  function setup() {
    const timers = new FakeTimers();
    const shown: string[] = [];
    const tracker = new BareAltTracker(timers, () => shown.push("show"), () => shown.push("hide"));
    return { timers, shown, tracker };
  }

  it("a tap under 400 ms is a tap (the capture clears) and shows nothing", () => {
    const { timers, shown, tracker } = setup();
    tracker.keydown({ key: "Alt" });
    timers.advance(WHICH_KEY_HOLD_MS - 1);
    expect(tracker.release({ key: "Alt" })).toBe("tap");
    expect(shown).toEqual([]);
  });

  it("a hold of 400 ms shows which-key, and its release is a hold that never clears", () => {
    const { timers, shown, tracker } = setup();
    tracker.keydown({ key: "Alt" });
    timers.advance(WHICH_KEY_HOLD_MS);
    expect(shown).toEqual(["show"]);
    expect(tracker.holding).toBe(true);
    expect(tracker.release({ key: "Alt" })).toBe("hold");
    expect(shown).toEqual(["show", "hide"]);
  });

  it("any other key while Alt is down is a chord, and hides which-key", () => {
    const { timers, shown, tracker } = setup();
    tracker.keydown({ key: "Alt" });
    timers.advance(WHICH_KEY_HOLD_MS + 10);
    tracker.keydown({ key: "h" });
    expect(shown).toEqual(["show", "hide"]);
    expect(tracker.release({ key: "Alt" })).toBe("chord");
  });

  it("a pointer press or the window losing focus cancels the press", () => {
    const { tracker } = setup();
    tracker.keydown({ key: "Alt" });
    tracker.cancel();
    expect(tracker.release({ key: "Alt" })).toBe("cancelled");
    expect(tracker.release({ key: "Alt" })).toBeNull();
  });

  it("an auto-repeated Alt keydown does not restart the hold", () => {
    const { timers, shown, tracker } = setup();
    tracker.keydown({ key: "Alt" });
    timers.advance(300);
    tracker.keydown({ key: "Alt", repeat: true });
    timers.advance(100);
    expect(shown).toEqual(["show"]);
  });
});

describe("the typing scope's targets", () => {
  it("is an input, a textarea, an editor or a part marked as typing", () => {
    const input = document.createElement("input");
    const div = document.createElement("div");
    const marked = document.createElement("div");
    marked.setAttribute("data-desk-typing", "");
    const inside = document.createElement("span");
    marked.appendChild(inside);
    expect(isTypingTarget(input)).toBe(true);
    expect(isTypingTarget(div)).toBe(false);
    expect(isTypingTarget(inside)).toBe(true);
    expect(isTypingTarget(null)).toBe(false);
  });
});

describe("the companion's and search's keys (RD3)", () => {
  const mods = { alt: false, ctrl: false };
  const key = (k: string, code: string, extra: Partial<KeyboardEventInit> = {}) => ({ key: k, code, altKey: false, ctrlKey: false, metaKey: false, shiftKey: false, ...extra });

  it("in the reading view c summons the companion, shift+c docks it and / opens search", () => {
    expect(resolveKey(key("c", "KeyC"), {}, mods)?.binding.action).toEqual({ kind: "companion", atDock: false });
    expect(resolveKey(key("C", "KeyC", { shiftKey: true }), {}, mods)?.binding.action).toEqual({ kind: "companion", atDock: true });
    expect(resolveKey(key("/", "Slash"), {}, mods)?.binding.action).toEqual({ kind: "search" });
  });

  it("while typing, a bare c and / stay in the field; alt+c still reaches the companion", () => {
    expect(resolveKey(key("c", "KeyC"), { typing: true }, mods)).toBeNull();
    expect(resolveKey(key("/", "Slash"), { typing: true }, mods)).toBeNull();
    expect(resolveKey(key("c", "KeyC", { altKey: true }), { typing: true }, { alt: true, ctrl: false })?.binding.action).toEqual({ kind: "companion", atDock: false });
  });

  it("an open search panel (the menu scope) takes every key: nothing reaches the desk, not even c or alt+o", () => {
    expect(resolveKey(key("c", "KeyC"), { menu: true }, mods)).toBeNull();
    expect(resolveKey(key("o", "KeyO", { altKey: true }), { menu: true }, { alt: true, ctrl: false })).toBeNull();
    expect(resolveKey(key("/", "Slash"), { menu: true }, mods)).toBeNull();
  });

  it("in focus mode c and / pass through to the reading view; in the overview they do nothing", () => {
    expect(resolveKey(key("c", "KeyC"), { focus: true }, mods)?.binding.action).toEqual({ kind: "companion", atDock: false });
    expect(resolveKey(key("/", "Slash"), { focus: true }, mods)?.binding.action).toEqual({ kind: "search" });
    expect(resolveKey(key("c", "KeyC"), { overview: true }, mods)).toBeNull();
  });

  it("a typing scope a window claims with the focus still on the page (the Reader's intent box over a selection) lets c, shift+c and / through; real typing keeps them", () => {
    const claimed: ScopeState = { typingClaim: true };
    expect(resolveKey(key("c", "KeyC"), claimed, mods)?.binding.action).toEqual({ kind: "companion", atDock: false });
    expect(resolveKey(key("C", "KeyC", { shiftKey: true }), claimed, mods)?.binding.action).toEqual({ kind: "companion", atDock: true });
    expect(resolveKey(key("/", "Slash"), claimed, mods)?.binding.action).toEqual({ kind: "search" });
    // Every other bare key stays the claim's (x would swap, o would zoom out).
    expect(resolveKey(key("x", "KeyX"), claimed, mods)).toBeNull();
    expect(resolveKey(key("o", "KeyO"), claimed, mods)).toBeNull();
    // The DOM focus in an editor: typing, whatever is claimed.
    expect(resolveKey(key("c", "KeyC"), { typing: true, typingClaim: true }, mods)).toBeNull();
    expect(resolveKey(key("/", "Slash"), { typing: true, typingClaim: true }, mods)).toBeNull();
    // An open menu still takes them.
    expect(resolveKey(key("c", "KeyC"), { typingClaim: true, menu: true }, mods)).toBeNull();
  });

  it("alt+c is no shell chord, and c is no shell letter (no collision with keymap.ts)", () => {
    const binding = DESK_BINDINGS.find((each) => each.id === "companion.typing");
    expect(binding?.chord).toMatchObject({ alt: true, code: "KeyC" });
  });
});
