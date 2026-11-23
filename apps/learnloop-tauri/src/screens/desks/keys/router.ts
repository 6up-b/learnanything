// The workbench's key router (spec §5.4): the resolved scope and precedence matrix as data, the
// function that resolves one key event against the scopes that are open, the bare-Alt tap versus
// hold rule, and the modifier tracker (§5.5). Pure apart from the timers the Alt tracker is handed.
//
// One capture-phase listener in DeskShell owns every workbench key. The first matching scope wins,
// top to bottom; a key no scope takes goes on to the active window (its own listeners, registered
// through the shell's listener hub), and from there to the shell's chords (`app/keymap.ts`).

export type DeskScope = "notebook" | "check" | "menu" | "typing" | "arrange" | "pen" | "overview" | "focus" | "reading";

/** Highest first (spec §5.4's matrix). */
export const SCOPE_ORDER: readonly DeskScope[] = ["notebook", "check", "menu", "typing", "arrange", "pen", "overview", "focus", "reading"];

export type DeskAction =
  | { kind: "focusAlong"; direction: -1 | 1 }
  | { kind: "paneOrDesk"; direction: -1 | 1 }
  | { kind: "moveWindow"; direction: -1 | 1 }
  | { kind: "moveToDesk"; direction: -1 | 1 }
  | { kind: "toggleFocusMode" }
  | { kind: "closeWindow" }
  | { kind: "gather"; toNewDesk: boolean }
  | { kind: "overview" }
  | { kind: "overviewMove"; direction: "left" | "right" | "up" | "down" }
  | { kind: "overviewOpen"; focusMode: boolean }
  | { kind: "leaveOverview" }
  | { kind: "toggleRelations" }
  | { kind: "gatherPreview" }
  | { kind: "pair" }
  | { kind: "unpair" }
  | { kind: "newPad" }
  | { kind: "arrangePads" }
  | { kind: "sketchBlock" }
  | { kind: "timestamp" }
  | { kind: "pen" }
  | { kind: "companion"; atDock: boolean }
  | { kind: "search" }
  | { kind: "menu" }
  | { kind: "nextPad"; direction: -1 | 1 }
  | { kind: "path" }
  | { kind: "marginNote" }
  | { kind: "promoted" }
  | { kind: "follow" }
  | { kind: "playPause" }
  | { kind: "swap" }
  | { kind: "docZoom"; direction: -1 | 0 | 1 }
  | { kind: "leaveFocusMode" }
  | { kind: "drain" };

export interface Chord {
  /** `KeyboardEvent.code` for Alt chords (Alt+H types other characters on some layouts and on a Mac);
   * absent, `key` is compared with `KeyboardEvent.key`. */
  code?: string;
  key?: string;
  alt?: boolean;
  shift?: boolean;
  ctrl?: boolean;
}

export interface DeskBinding {
  id: string;
  /** As help and the which-key panel write it. */
  keys: string;
  label: string;
  chord: Chord;
  action: DeskAction;
  /** The scopes that own this chord. */
  scopes: readonly DeskScope[];
  /** The stage that builds what it does; absent, it works now. A chord whose feature is not built yet
   * is not taken: the key goes on to the window and the shell as before. */
  later?: string;
  /** Which-key's group (spec §5.4), or none for a key that is not on the panel. */
  group?: "move" | "windows" | "pads" | "media";
}

const ALT_TYPING: readonly DeskScope[] = ["typing", "focus", "reading"];
const READING: readonly DeskScope[] = ["reading"];

function alt(id: string, keys: string, label: string, code: string, action: DeskAction, scopes: readonly DeskScope[], extra: Partial<DeskBinding> = {}): DeskBinding {
  return { id, keys, label, chord: { code, alt: true, shift: false }, action, scopes, ...extra };
}

function bare(id: string, keys: string, label: string, key: string, action: DeskAction, scopes: readonly DeskScope[], extra: Partial<DeskBinding> = {}): DeskBinding {
  return { id, keys, label, chord: { key }, action, scopes, ...extra };
}

/** Every workbench chord (spec §5.4). `keymap.test.ts` reads this list for collisions with the shell. */
export const DESK_BINDINGS: readonly DeskBinding[] = [
  alt("move.left", "alt+h", "window left", "KeyH", { kind: "focusAlong", direction: -1 }, ALT_TYPING, { group: "move" }),
  alt("move.right", "alt+l", "window right", "KeyL", { kind: "focusAlong", direction: 1 }, ALT_TYPING, { group: "move" }),
  alt("move.down", "alt+j", "pane below, then the desk below", "KeyJ", { kind: "paneOrDesk", direction: 1 }, ["typing", "reading"], { group: "move" }),
  alt("move.up", "alt+k", "pane above, then the desk above", "KeyK", { kind: "paneOrDesk", direction: -1 }, ["typing", "reading"], { group: "move" }),
  alt("move.window-left", "alt+[", "move window left", "BracketLeft", { kind: "moveWindow", direction: -1 }, ["typing", "overview", "reading"], { group: "move" }),
  alt("move.window-right", "alt+]", "move window right", "BracketRight", { kind: "moveWindow", direction: 1 }, ["typing", "overview", "reading"], { group: "move" }),
  { id: "move.to-desk-below", keys: "alt+shift+j", label: "window to the desk below", chord: { code: "KeyJ", alt: true, shift: true }, action: { kind: "moveToDesk", direction: 1 }, scopes: ["overview"], group: "move" },
  { id: "move.to-desk-above", keys: "alt+shift+k", label: "window to the desk above", chord: { code: "KeyK", alt: true, shift: true }, action: { kind: "moveToDesk", direction: -1 }, scopes: ["overview"], group: "move" },
  alt("windows.focus", "alt+↵", "focus (full screen)", "Enter", { kind: "toggleFocusMode" }, ALT_TYPING, { group: "windows" }),
  alt("windows.close", "alt+w", "close (undo on the shelf)", "KeyW", { kind: "closeWindow" }, ["focus", "reading"], { group: "windows" }),
  alt("windows.gather", "alt+g", "gather", "KeyG", { kind: "gather", toNewDesk: false }, READING, { group: "windows" }),
  { id: "windows.gather-new", keys: "alt+shift+g", label: "gather to a new desk", chord: { code: "KeyG", alt: true, shift: true }, action: { kind: "gather", toNewDesk: true }, scopes: READING, group: "windows" },
  alt("windows.overview", "alt+o", "overview", "KeyO", { kind: "overview" }, ["overview", "focus", "reading"], { group: "windows" }),
  alt("windows.pair", "alt+,", "share a slot", "Comma", { kind: "pair" }, ["typing", "reading"], { group: "windows" }),
  alt("windows.unpair", "alt+.", "own slot", "Period", { kind: "unpair" }, ["typing", "reading"], { group: "windows" }),
  alt("pads.new", "alt+n", "new pad", "KeyN", { kind: "newPad" }, READING, { group: "pads" }),
  alt("pads.arrange", "alt+a", "arrange pads", "KeyA", { kind: "arrangePads" }, READING, { group: "pads" }),
  alt("pads.sketch", "alt+d", "sketch block", "KeyD", { kind: "sketchBlock" }, READING, { group: "pads" }),
  { id: "pads.drain", keys: "alt+shift+q", label: "close the desk's day (the drain)", chord: { code: "KeyQ", alt: true, shift: true }, action: { kind: "drain" }, scopes: READING, group: "pads" },
  alt("pads.timestamp", "alt+;", "insert ▶ timestamp", "Semicolon", { kind: "timestamp" }, READING, { later: "RD10", group: "pads" }),
  alt("pen.toggle", "alt+p", "pen mode", "KeyP", { kind: "pen" }, ["pen", "reading"], { later: "RD8a" }),
  alt("companion.typing", "alt+c", "the companion, while typing", "KeyC", { kind: "companion", atDock: false }, ["typing"]),
  bare("media.play", "space", "play or pause", " ", { kind: "playPause" }, READING, { group: "media" }),
  bare("reading.companion", "c", "companion here", "c", { kind: "companion", atDock: false }, READING),
  { id: "reading.companion-dock", keys: "shift+c", label: "companion at its dock", chord: { key: "C", shift: true }, action: { kind: "companion", atDock: true }, scopes: READING },
  bare("reading.search", "/", "search in context", "/", { kind: "search" }, READING),
  // The pad menu on a hovered pad line now; the source menu on a passage arrives with the menus (a key the
  // shell does not take goes on to the window).
  bare("reading.menu", ".", "the menu on the hovered object", ".", { kind: "menu" }, READING),
  bare("reading.menu-key", "menu key", "the menu on the hovered object", "ContextMenu", { kind: "menu" }, READING),
  { id: "reading.next-pad", keys: "ctrl+tab", label: "next pad", chord: { key: "Tab", ctrl: true, shift: false }, action: { kind: "nextPad", direction: 1 }, scopes: READING },
  { id: "reading.prev-pad", keys: "ctrl+shift+tab", label: "previous pad", chord: { key: "Tab", ctrl: true, shift: true }, action: { kind: "nextPad", direction: -1 }, scopes: READING },
  bare("reading.path", "p", "your path", "p", { kind: "path" }, READING, { later: "RD6" }),
  bare("reading.note", "n", "a margin note on the hovered passage", "n", { kind: "marginNote" }, READING, { later: "RD5" }),
  bare("reading.promoted", "b", "the first promoted action", "b", { kind: "promoted" }, READING, { later: "RD5" }),
  bare("reading.follow", "u", "follow along", "u", { kind: "follow" }, READING, { later: "RD10" }),
  bare("reading.overview", "o", "overview", "o", { kind: "overview" }, ["overview", "reading"]),
  bare("reading.swap", "x", "swap the two windows in view", "x", { kind: "swap" }, READING),
  // The overview (spec §6.2): h/j/k/l, the arrows or alt+h/j/k/l move the selection; ↵ opens it, alt+↵ in
  // focus mode; esc goes back to where the overview was entered from; b toggles the relations; g held
  // previews a gather.
  ...(["left", "down", "up", "right"] as const).flatMap((direction, index) => {
    const letter = "hjkl"[index];
    const arrow = { left: "ArrowLeft", down: "ArrowDown", up: "ArrowUp", right: "ArrowRight" }[direction];
    return [
      bare(`overview.${direction}`, letter, `select ${direction}`, letter, { kind: "overviewMove", direction }, ["overview"]),
      bare(`overview.${direction}-arrow`, arrow.replace("Arrow", "").toLowerCase(), `select ${direction}`, arrow, { kind: "overviewMove", direction }, ["overview"]),
      alt(`overview.alt-${direction}`, `alt+${letter}`, `select ${direction}`, `Key${letter.toUpperCase()}`, { kind: "overviewMove", direction }, ["overview"]),
    ];
  }),
  bare("overview.open", "↵", "open the selected card", "Enter", { kind: "overviewOpen", focusMode: false }, ["overview"]),
  alt("overview.open-focus", "alt+↵", "open it in focus mode", "Enter", { kind: "overviewOpen", focusMode: true }, ["overview"]),
  bare("overview.leave", "esc", "back to where you were", "Escape", { kind: "leaveOverview" }, ["overview"]),
  bare("overview.relations", "b", "relations on / off", "b", { kind: "toggleRelations" }, ["overview"]),
  bare("overview.gather-preview", "g (hold)", "preview a gather", "g", { kind: "gatherPreview" }, ["overview"]),
  bare("focus.zoom-in", "=", "document zoom in", "=", { kind: "docZoom", direction: 1 }, ["focus"]),
  bare("focus.zoom-in-plus", "+", "document zoom in", "+", { kind: "docZoom", direction: 1 }, ["focus"]),
  bare("focus.zoom-out", "-", "document zoom out", "-", { kind: "docZoom", direction: -1 }, ["focus"]),
  bare("focus.zoom-reset", "0", "document zoom 100 %", "0", { kind: "docZoom", direction: 0 }, ["focus"]),
  bare("focus.leave", "esc", "leave focus mode", "Escape", { kind: "leaveFocusMode" }, ["focus"]),
];

/** What is open, as the router reads it. Each flag turns one scope of the matrix on. */
export interface ScopeState {
  notebook?: boolean;
  check?: boolean;
  menu?: boolean;
  typing?: boolean;
  arrange?: boolean;
  pen?: boolean;
  overview?: boolean;
  focus?: boolean;
}

/** The scopes open now, highest first; the reading view is always open beneath them. */
export function openScopes(state: ScopeState): DeskScope[] {
  return SCOPE_ORDER.filter((scope) => scope === "reading" || Boolean(state[scope as keyof ScopeState]));
}

export interface KeyLike {
  key: string;
  code: string;
  altKey: boolean;
  ctrlKey: boolean;
  metaKey: boolean;
  shiftKey: boolean;
}

function chordMatches(chord: Chord, event: KeyLike, mods: { alt: boolean; ctrl: boolean }): boolean {
  const altDown = mods.alt;
  const ctrlDown = mods.ctrl || event.metaKey;
  if (Boolean(chord.alt) !== altDown) return false;
  if (Boolean(chord.ctrl) !== ctrlDown) return false;
  if (chord.code) {
    if (chord.shift !== undefined && chord.shift !== event.shiftKey) return false;
    return event.code === chord.code;
  }
  if (chord.shift !== undefined && chord.shift !== event.shiftKey) return false;
  return event.key === chord.key;
}

/** What a scope passes on when it does not own a key (spec §5.4's "passes through" column). */
function passesThrough(scope: DeskScope, binding: DeskBinding): boolean {
  switch (scope) {
    // A notebook frame passes only its bridge messages; a check card, a menu and the arrange overlay pass
    // nothing to the workbench (the check card blocks the overview and zoom outright).
    case "notebook":
    case "check":
    case "menu":
    case "arrange":
      return false;
    // Typing passes only the Alt chords marked for it.
    case "typing":
      return false;
    // Pen mode passes every key; the overview passes the shell's chords (none of these); focus mode passes
    // the reading-view keys.
    case "pen":
    case "focus":
      return true;
    case "overview":
      return false;
    case "reading":
      return false;
  }
}

export interface Resolution {
  binding: DeskBinding;
  scope: DeskScope;
}

/** The binding this key event reaches, and the scope that owns it; null when no workbench scope takes
 * it (the key goes on to the window and the shell). The first open scope that owns a matching chord
 * wins; a scope that owns nothing for it either stops the key there or passes it down. */
export function resolveKey(event: KeyLike, state: ScopeState, mods: { alt: boolean; ctrl: boolean }): Resolution | null {
  const matching = DESK_BINDINGS.filter((binding) => chordMatches(binding.chord, event, mods));
  if (matching.length === 0) return null;
  for (const scope of openScopes(state)) {
    const owned = matching.find((binding) => binding.scopes.includes(scope));
    if (owned) return { binding: owned, scope };
    if (!matching.some((binding) => passesThrough(scope, binding))) return null;
  }
  return null;
}

// -- modifiers (spec §5.5): tracked from key events, cleared on blur ----------------------------

/** WebKitGTK may report altKey/ctrlKey false on touchpad scrolls, so Alt and Ctrl are tracked from
 * key events and ORed with the event's own flags. */
export class ModifierTracker {
  private altDown = false;
  private ctrlDown = false;

  keydown(event: Pick<KeyLike, "key">): void {
    if (event.key === "Alt" || event.key === "AltGraph") this.altDown = true;
    if (event.key === "Control" || event.key === "Meta") this.ctrlDown = true;
  }

  keyup(event: Pick<KeyLike, "key">): void {
    if (event.key === "Alt" || event.key === "AltGraph") this.altDown = false;
    if (event.key === "Control" || event.key === "Meta") this.ctrlDown = false;
  }

  blur(): void {
    this.altDown = false;
    this.ctrlDown = false;
  }

  read(event?: Partial<Pick<KeyLike, "altKey" | "ctrlKey" | "metaKey">>): { alt: boolean; ctrl: boolean } {
    return { alt: this.altDown || Boolean(event?.altKey), ctrl: this.ctrlDown || Boolean(event?.ctrlKey) || Boolean(event?.metaKey) };
  }
}

// -- the bare-Alt rule (spec §5.4): a tap under 400 ms clears, a hold shows which-key ------------

/** Alt held this long alone shows the which-key panel; a shorter tap is the capture-clearing tap. */
export const WHICH_KEY_HOLD_MS = 400;

export interface Timers {
  set(fn: () => void, ms: number): unknown;
  clear(handle: unknown): void;
  now(): number;
}

export const REAL_TIMERS: Timers = {
  set: (fn, ms) => window.setTimeout(fn, ms),
  clear: (handle) => window.clearTimeout(handle as number),
  now: () => Date.now(),
};

/** What one bare Alt press came to. */
export type AltOutcome = "tap" | "hold" | "chord" | "cancelled";

/** Follows bare Alt presses. `onHold` fires once Alt has been held alone for 400 ms (which-key shows);
 * `release` says what the press was when Alt comes up: a tap (clear), a hold (which-key hides and
 * nothing clears), a chord (another key was pressed), or cancelled (a pointer press or blur). */
export class BareAltTracker {
  private pressedAt: number | null = null;
  private spoiled: AltOutcome | null = null;
  private held = false;
  private timer: unknown = null;

  constructor(private readonly timers: Timers, private readonly onHold: () => void, private readonly onHoldEnd: () => void) {}

  keydown(event: Pick<KeyLike, "key"> & { repeat?: boolean }): void {
    if (event.key === "Alt") {
      if (event.repeat || this.pressedAt !== null) return;
      this.pressedAt = this.timers.now();
      this.spoiled = null;
      this.held = false;
      this.timer = this.timers.set(() => {
        if (this.pressedAt === null || this.spoiled) return;
        this.held = true;
        this.onHold();
      }, WHICH_KEY_HOLD_MS);
      return;
    }
    if (this.pressedAt !== null && !this.spoiled) this.spoil("chord");
  }

  /** A pointer press or the window losing focus while Alt is down. */
  cancel(): void {
    if (this.pressedAt !== null && !this.spoiled) this.spoil("cancelled");
  }

  release(event: Pick<KeyLike, "key">): AltOutcome | null {
    if (event.key !== "Alt" || this.pressedAt === null) return null;
    const held = this.held || this.timers.now() - this.pressedAt >= WHICH_KEY_HOLD_MS;
    const outcome: AltOutcome = this.spoiled ?? (held ? "hold" : "tap");
    this.reset();
    return outcome;
  }

  get holding(): boolean {
    return this.held;
  }

  reset(): void {
    if (this.timer !== null) this.timers.clear(this.timer);
    const wasHeld = this.held;
    this.timer = null;
    this.pressedAt = null;
    this.spoiled = null;
    this.held = false;
    if (wasHeld) this.onHoldEnd();
  }

  private spoil(outcome: AltOutcome): void {
    this.spoiled = outcome;
    if (this.timer !== null) this.timers.clear(this.timer);
    this.timer = null;
    if (this.held) {
      this.held = false;
      this.onHoldEnd();
    }
  }
}

/** Whether a key event's target is a place the learner types (spec §5.4's typing scope). */
export function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  return target.closest("input, textarea, select, [contenteditable]:not([contenteditable=\"false\"]), [data-desk-typing]") !== null;
}
