// UX Phase 2 fix round 4 (whole-stage verify 20261021-134216-8mdDfN item 1):
// the simple shell's chrome is a key-isolated region.
//
// The simple shell draws controls the screens know nothing about: the places,
// + Add and ^K in the nav, the ⋯ menu, the notices and their Try again, the
// Under-the-hood list, Keyboard & help and the palette. Screens bind plain
// keys on the window (Start's Enter begins a session, Today's Enter and
// digits open an item, Esc steps back), so a key pressed on one of those
// controls also reached the screen: Enter on ^K began a session. Round 2
// fixed this for one menu; the class came back for every other control.
//
// Every chrome part carries `data-shell-chrome`. One handler on one root
// (this element, around everything the simple shell renders) stops the
// propagation of any key event whose target is inside a chrome part. React
// runs it after the chrome's own handlers (the ⋯ menu's Esc, the palette's
// input), and it never prevents the default, so native activation still
// works: Enter on a button, a link or a menu item, and Space on a button. The
// event just goes no further: no window or document listener of a screen
// sees it. The shell's own chords (Ctrl, Cmd or Alt held, and ":") still go
// through, so Ctrl+K, Alt+1…4 and Ctrl+O work with the focus on a chrome
// control. Screens leave modified keys to the shell (round 2,
// `screenLeavesKey`).
//
// Why a bubble-phase handler at the root, not a capture-phase one: React
// delegates every handler, the chrome's own included, to its container. A
// native listener that stopped the event on the way down (capture) or before
// it reached the container would also silence the chrome's own handlers.
// React's bubble pass runs at the container, before any window or document
// bubble listener, so stopping it there isolates the chrome and keeps its
// handlers. Window listeners registered for the capture phase run before any
// element sees the event and are beyond any element's reach; the few that
// exist are overlays, pinned with their reasons in app/shellChrome.test.ts.
//
// Classic draws none of this and renders no root: base, by construction.
import type { KeyboardEvent as ReactKeyboardEvent, ReactNode } from "react";
import { matchShellKey } from "./keymap";

export const SHELL_CHROME_ATTRIBUTE = "data-shell-chrome";

export function inShellChrome(target: EventTarget | null): boolean {
  return target instanceof Element && target.closest(`[${SHELL_CHROME_ATTRIBUTE}]`) !== null;
}

/** Fix round 5: the chrome keeps only the keys the focused control itself
 *  consumes. A plain control (a place, + Add, ^K, ⋯, a notice's buttons, an
 *  Under-the-hood tool) consumes Enter and Space, its activation. An open
 *  menu, the palette and Keyboard & help (parts marked "dialog") consume
 *  every plain key: Esc, the arrows and typing. Every other key goes on, and
 *  the screens' own target rule (`screenLeavesKey`) leaves a key aimed at a
 *  control that is not theirs. */
function consumedHere(event: ReactKeyboardEvent<HTMLElement>): boolean {
  const target = event.target as Element;
  if (target.closest(`[${SHELL_CHROME_ATTRIBUTE}="dialog"], [role="menu"]`)) return true;
  return (event.key === "Enter" || event.key === " ") && target.closest('button, a[href], [role="button"], [role="menuitem"]') !== null;
}

const MODIFIER_KEYS: ReadonlySet<string> = new Set(["Control", "Meta", "Alt", "Shift"]);

function isolate(event: ReactKeyboardEvent<HTMLElement>): void {
  if (!inShellChrome(event.target)) return;
  if (event.ctrlKey || event.metaKey || event.altKey) return;
  // A modifier's own release goes on, so listeners that track a held
  // modifier (the PDF marquee's Ctrl, the Reader's bare Alt) see it end.
  if (MODIFIER_KEYS.has(event.key)) return;
  if (event.type === "keydown" && matchShellKey(event.nativeEvent, "simple", false)) return;
  if (!consumedHere(event)) return;
  event.stopPropagation();
}


export function ShellChromeRoot({ children }: { children: ReactNode }) {
  return (
    <div className="shell-chrome-root" style={{ display: "contents" }} onKeyDown={isolate} onKeyUp={isolate} onKeyPress={isolate}>
      {children}
    </div>
  );
}
