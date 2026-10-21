// UX Phase 2: one shared key map (docs/specs/ux_learnloop_v1.md §5.4, §10 2.1).
//
// Every shell-level binding is data here, per shell. App's single window
// listener dispatches through `matchShellKey`; `useGlobalAdd` reads its chord
// from here too; Keyboard & help lists these rows; and `keymap.test.ts`
// enumerates them for collisions and for the replacements of the classic
// keys. Screen-level keys (the key bars at the bottom of each screen) stay
// with their screens: the shell only owns chords that work everywhere.
//
// The classic bindings are the base shell's exactly (`ui.shell = "classic"`):
// the same chords, the same predicates (loose about extra modifiers where the
// base was), the same "not while typing" rules.
import { SHOW_GOLDEN_PATH, navTabs, type TopTab } from "../components/ui";
import { algoConfig } from "./algoConfig";
import type { Place, ShellMode, UthToolId } from "./shell";

export type KeyAction =
  | { kind: "palette" }
  | { kind: "settings" }
  | { kind: "addFiles" }
  | { kind: "pasteLink" }
  | { kind: "tab"; tab: TopTab }
  | { kind: "place"; place: Place }
  | { kind: "tool"; tool: UthToolId };

interface Chord {
  /** Compared case-insensitively against `event.key`. */
  key: string;
  /** Ctrl, or Cmd on a Mac (the base shell's `ctrlKey || metaKey`). */
  mod?: boolean;
  alt?: boolean;
}

export interface KeyBinding {
  id: string;
  /** How the key is written in help and tooltips. */
  keys: string;
  label: string;
  action: KeyAction;
  chord: Chord;
  /** Fires even while the learner is typing (Ctrl+P, Alt+S did in the base). */
  whileTyping: boolean;
  /** Which listener owns it: the shell's, or Add's (`useGlobalAdd`, which
   *  also reads the paste event and has its own enabling rules). */
  owner: "shell" | "useGlobalAdd";
}

function binding(
  id: string,
  keys: string,
  label: string,
  action: KeyAction,
  chord: Chord,
  options: { whileTyping?: boolean; owner?: KeyBinding["owner"] } = {}
): KeyBinding {
  return { id, keys, label, action, chord, whileTyping: options.whileTyping ?? false, owner: options.owner ?? "shell" };
}

/** Add's chords (UX Phase 1, §6.2): Ctrl+O chooses files; Ctrl+V outside a
 *  text field adds the link on the clipboard (a paste event, not a key). */
export const ADD_FILES_CHORD: Chord = { key: "o", mod: true };

function addBindings(): KeyBinding[] {
  return [
    binding("add.files", "Ctrl+O", "Add a file", { kind: "addFiles" }, ADD_FILES_CHORD, { owner: "useGlobalAdd" }),
    binding("add.paste", "Ctrl+V", "Add the link on the clipboard (no text field focused)", { kind: "pasteLink" }, { key: "v", mod: true }, { owner: "useGlobalAdd" })
  ];
}

function classicBindings(): KeyBinding[] {
  return [
    binding("palette.ctrl-p", "Ctrl+P", "Command palette", { kind: "palette" }, { key: "p", mod: true }, { whileTyping: true }),
    binding("settings.alt-s", "Alt+S", "Settings", { kind: "settings" }, { key: "s", alt: true }, { whileTyping: true }),
    binding("palette.colon", ":", "Command palette", { kind: "palette" }, { key: ":" }),
    // navTabs already leaves Golden Path out while it is hidden, so Alt+8
    // stays unbound, as in the base shell.
    ...navTabs.map((tab) =>
      binding(`tab.${tab.id}`, `Alt+${tab.key}`, tab.label, { kind: "tab", tab: tab.id }, { key: tab.key, alt: true })
    ),
    ...addBindings()
  ];
}

function simpleBindings(): KeyBinding[] {
  return [
    binding("palette.ctrl-p", "Ctrl+P", "Command palette", { kind: "palette" }, { key: "p", mod: true }, { whileTyping: true }),
    binding("palette.ctrl-k", "Ctrl+K", "Command palette", { kind: "palette" }, { key: "k", mod: true }, { whileTyping: true }),
    binding("settings.alt-s", "Alt+S", "Settings", { kind: "settings" }, { key: "s", alt: true }, { whileTyping: true }),
    binding("settings.ctrl-comma", "Ctrl+,", "Settings", { kind: "settings" }, { key: ",", mod: true }, { whileTyping: true }),
    binding("palette.colon", ":", "Command palette", { kind: "palette" }, { key: ":" }),
    // The places work from inside an answer box too (seen in the harness: a
    // practice question keeps the focus in its box, so Alt+4 did nothing).
    // Alt+digit types no text on Linux or Windows, and on a Mac Option+digit
    // gives another key, so it never matches. Classic keeps "not while typing".
    binding("place.today", "Alt+1", "Today", { kind: "place", place: "today" }, { key: "1", alt: true }, { whileTyping: true }),
    binding("place.library", "Alt+2", "Library", { kind: "place", place: "library" }, { key: "2", alt: true }, { whileTyping: true }),
    binding("place.reader", "Alt+3", "Reader", { kind: "place", place: "reader" }, { key: "3", alt: true }, { whileTyping: true }),
    binding("place.progress", "Alt+4", "Progress", { kind: "place", place: "progress" }, { key: "4", alt: true }, { whileTyping: true }),
    // The old Alt+5…0 keep working (§5.4): each opens what its tab became.
    binding("old.proposals", "Alt+5", "Study-map changes (was Proposals)", { kind: "tool", tool: "proposals" }, { key: "5", alt: true }, { whileTyping: true }),
    binding("old.registry", "Alt+6", "Subjects & topics (was Registry)", { kind: "tool", tool: "registry" }, { key: "6", alt: true }, { whileTyping: true }),
    binding("old.library", "Alt+7", "Library (was [7] Library)", { kind: "place", place: "library" }, { key: "7", alt: true }, { whileTyping: true }),
    ...(SHOW_GOLDEN_PATH
      ? [binding("old.golden", "Alt+8", "Golden path", { kind: "tool", tool: "golden" } as KeyAction, { key: "8", alt: true }, { whileTyping: true })]
      : []),
    binding("old.reader", "Alt+9", "Reader (was [9] Reader)", { kind: "place", place: "reader" }, { key: "9", alt: true }, { whileTyping: true }),
    binding("old.maintain", "Alt+0", "System health (was Maintain)", { kind: "tool", tool: "maintain" }, { key: "0", alt: true }, { whileTyping: true }),
    ...addBindings()
  ];
}

/** Every shell-level binding of a shell, in the order the listener tries them. */
export function shellBindings(shell: ShellMode): KeyBinding[] {
  return shell === "classic" ? classicBindings() : simpleBindings();
}

/** What became of each classic shortcut whose meaning moved in the simple
 *  shell (by classic binding id). Every other classic key works unchanged. */
export const CLASSIC_REPLACEMENTS: Readonly<Record<string, string>> = {
  "tab.start": "Alt+1 opens Today, which shows Start until a session is open (Phase 3 merges them).",
  "tab.today": "Today is Alt+1 (Alt+2 is Library).",
  "tab.graph": "The Graph screen is Progress, Alt+4; its editor is also under the hood (Concept graph editor).",
  "tab.ingest": "⋯ → Under the hood → Imports & builds, or the palette (\"imports\"). Alt+4 is Progress.",
  "tab.proposals": "Alt+5 still opens it: Under the hood → Study-map changes.",
  "tab.registry": "Alt+6 still opens it: Under the hood → Subjects & topics.",
  "tab.library": "Alt+7 still opens the Library (also Alt+2).",
  "tab.reader": "Alt+9 still opens the Reader (also Alt+3).",
  "tab.maintain": "Alt+0 still opens it: Under the hood → System health."
};

/** Screen-level handlers that bind a chord the shell also binds, and why the
 *  two never both fire: each sits on an element and stops the event before
 *  it reaches the shell's window listener (and the simple shell skips an
 *  event a screen already handled). Checked by `keymap.test.ts`. */
export const SCOPED_OVERRIDES: ReadonlyArray<{ file: string; keys: string; where: string; note: string }> = [
  {
    file: "screens/workbench/Workbench.tsx",
    keys: "Ctrl+K",
    where: "the Reader workbench, with help on",
    note: "Check my work. The workbench's own handler stops the event, so the palette stays shut there; Ctrl+P and : still open it."
  }
];

/** For a screen's window-level key listener: whether to leave this event to
 *  the shell (fix round 2, whole-stage verify 20261021-114726-Jrt7sA item 4).
 *  In the simple shell a screen's plain keys never take a modified key
 *  (every shell chord holds Ctrl, Cmd or Alt) or an event a handler before
 *  it already took (the shell's listener marks each chord it runs with
 *  preventDefault). Without this, Alt+2 went to the Library AND Today read
 *  the "2" as "practise the second item". Classic answers false, so every
 *  base screen key stays exactly as it was.
 *
 *  Why the screens check rather than the shell calling
 *  stopImmediatePropagation: window listeners run in the order they were
 *  added, and nothing fixes that order. A screen listener added before the
 *  shell's would still see the chord first, and its preventDefault would then
 *  make the shell skip the chord altogether. The check here works in any
 *  order; `keymap.test.ts` scans for window listeners that take a shell
 *  chord's key and ignore modifiers. Stopping the event would also hide it
 *  from listeners that only watch the modifier state. */
export function screenLeavesKey(event: KeyboardEvent): boolean {
  if (algoConfig().shell === "classic") return false;
  return event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey;
}

export function matchesChord(chord: Chord, event: KeyboardEvent): boolean {
  if (event.key.toLowerCase() !== chord.key.toLowerCase()) return false;
  if (chord.mod && !(event.ctrlKey || event.metaKey)) return false;
  if (chord.alt && !event.altKey) return false;
  return true;
}

/** The shell binding a keydown triggers, or null. `typing` is whether the
 *  event's target is a text field (app/keyboard.ts `isTypingTarget`). */
export function matchShellKey(event: KeyboardEvent, shell: ShellMode, typing: boolean): KeyBinding | null {
  // A screen that already handled the key keeps it (simple shell only: the
  // base shell never checked, and classic stays as it was).
  if (shell === "simple" && event.defaultPrevented) return null;
  for (const candidate of shellBindings(shell)) {
    if (candidate.owner !== "shell") continue;
    if (typing && !candidate.whileTyping) continue;
    if (matchesChord(candidate.chord, event)) return candidate;
  }
  return null;
}
