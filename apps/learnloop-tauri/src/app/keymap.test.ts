// UX Phase 2 (docs/specs/ux_learnloop_v1.md §5.4, §10 2.1): one shared key
// map. Every shell-level binding is data here, per shell; this file
// enumerates them, checks that no two collide, that every shortcut the
// classic shell has still works in the simple shell or has a documented
// replacement, and that no screen binds a modifier chord the shell also
// binds without being listed as a scoped override.
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { setAlgoConfig } from "./algoConfig";
import {
  CLASSIC_REPLACEMENTS,
  SCOPED_OVERRIDES,
  matchShellKey,
  screenLeavesKey,
  shellBindings,
  type KeyBinding
} from "./keymap";

function keydown(init: KeyboardEventInit): KeyboardEvent {
  return new KeyboardEvent("keydown", { bubbles: true, cancelable: true, ...init });
}

function chordsOf(bindings: KeyBinding[]): string[] {
  return bindings.map((binding) => binding.keys);
}

describe("the shell key map", () => {
  it("lists every classic binding exactly as the base shell had them", () => {
    expect(chordsOf(shellBindings("classic"))).toEqual([
      "Ctrl+P",
      "Alt+S",
      ":",
      "Alt+1",
      "Alt+2",
      "Alt+3",
      "Alt+4",
      "Alt+5",
      "Alt+6",
      "Alt+7",
      "Alt+9",
      "Alt+0",
      "Ctrl+O",
      "Ctrl+V"
    ]);
  });

  it("gives the simple shell the four places, the palette on Ctrl+K and settings on Ctrl+,", () => {
    const simple = shellBindings("simple");
    const byKeys = new Map(simple.map((binding) => [binding.keys, binding]));
    expect(byKeys.get("Alt+1")?.action).toEqual({ kind: "place", place: "today" });
    expect(byKeys.get("Alt+2")?.action).toEqual({ kind: "place", place: "library" });
    expect(byKeys.get("Alt+3")?.action).toEqual({ kind: "place", place: "reader" });
    expect(byKeys.get("Alt+4")?.action).toEqual({ kind: "place", place: "progress" });
    expect(byKeys.get("Ctrl+K")?.action).toEqual({ kind: "palette" });
    expect(byKeys.get("Ctrl+P")?.action).toEqual({ kind: "palette" });
    expect(byKeys.get("Ctrl+,")?.action).toEqual({ kind: "settings" });
    expect(byKeys.get("Alt+S")?.action).toEqual({ kind: "settings" });
    // The old Alt+5…0 open the matching Under-the-hood tool (§5.4).
    expect(byKeys.get("Alt+5")?.action).toEqual({ kind: "tool", tool: "proposals" });
    expect(byKeys.get("Alt+6")?.action).toEqual({ kind: "tool", tool: "registry" });
    expect(byKeys.get("Alt+7")?.action).toEqual({ kind: "place", place: "library" });
    expect(byKeys.get("Alt+9")?.action).toEqual({ kind: "place", place: "reader" });
    expect(byKeys.get("Alt+0")?.action).toEqual({ kind: "tool", tool: "maintain" });
  });

  it("has no two bindings on one chord in either shell", () => {
    for (const shell of ["simple", "classic"] as const) {
      const chords = chordsOf(shellBindings(shell));
      expect(new Set(chords).size, `${shell}: ${chords.join(" ")}`).toBe(chords.length);
    }
  });

  it("keeps every classic shortcut in the simple shell, or documents its replacement", () => {
    const simple = shellBindings("simple");
    for (const classic of shellBindings("classic")) {
      const same = simple.find((binding) => binding.keys === classic.keys);
      const sameAction = same && JSON.stringify(same.action) === JSON.stringify(classic.action);
      if (sameAction) continue;
      expect(CLASSIC_REPLACEMENTS[classic.id], `classic ${classic.keys} (${classic.label}) needs a replacement`).toBeTruthy();
    }
  });

  it("matches the classic predicates exactly: Ctrl+P and Alt+S even while typing, the rest only outside text", () => {
    const typing = true;
    expect(matchShellKey(keydown({ key: "p", ctrlKey: true }), "classic", typing)?.keys).toBe("Ctrl+P");
    expect(matchShellKey(keydown({ key: "P", metaKey: true, shiftKey: true }), "classic", typing)?.keys).toBe("Ctrl+P");
    expect(matchShellKey(keydown({ key: "s", altKey: true }), "classic", typing)?.keys).toBe("Alt+S");
    expect(matchShellKey(keydown({ key: ":" }), "classic", typing)).toBeNull();
    expect(matchShellKey(keydown({ key: ":", shiftKey: true }), "classic", false)?.keys).toBe(":");
    expect(matchShellKey(keydown({ key: "3", altKey: true }), "classic", typing)).toBeNull();
    expect(matchShellKey(keydown({ key: "3", altKey: true }), "classic", false)?.action).toEqual({ kind: "tab", tab: "graph" });
    // Golden Path stays hidden: Alt+8 is not a binding while SHOW_GOLDEN_PATH is off.
    expect(matchShellKey(keydown({ key: "8", altKey: true }), "classic", false)).toBeNull();
    // Classic has no Ctrl+K and no Ctrl+, (byte-identical to the base shell).
    expect(matchShellKey(keydown({ key: "k", ctrlKey: true }), "classic", false)).toBeNull();
    expect(matchShellKey(keydown({ key: ",", ctrlKey: true }), "classic", false)).toBeNull();
  });

  it("matches the simple chords, and leaves events a screen already handled alone", () => {
    expect(matchShellKey(keydown({ key: "k", ctrlKey: true }), "simple", true)?.action).toEqual({ kind: "palette" });
    expect(matchShellKey(keydown({ key: ",", ctrlKey: true }), "simple", false)?.action).toEqual({ kind: "settings" });
    expect(matchShellKey(keydown({ key: "4", altKey: true }), "simple", false)?.action).toEqual({ kind: "place", place: "progress" });
    // From inside an answer box too (the harness walk: practice keeps the focus in its box).
    expect(matchShellKey(keydown({ key: "4", altKey: true }), "simple", true)?.action).toEqual({ kind: "place", place: "progress" });
    expect(matchShellKey(keydown({ key: "0", altKey: true }), "simple", true)?.action).toEqual({ kind: "tool", tool: "maintain" });
    expect(matchShellKey(keydown({ key: ":", shiftKey: true }), "simple", true)).toBeNull();
    const handled = keydown({ key: "k", ctrlKey: true });
    handled.preventDefault();
    expect(matchShellKey(handled, "simple", false)).toBeNull();
  });

  it("does not dispatch Add's own chords from the shell listener (useGlobalAdd owns them)", () => {
    expect(matchShellKey(keydown({ key: "o", ctrlKey: true }), "simple", false)).toBeNull();
    expect(matchShellKey(keydown({ key: "o", ctrlKey: true }), "classic", false)).toBeNull();
  });
});

// ── Screens against the shell's modifier chords ─────────────────────────
// A screen-level handler that binds a chord the shell also binds would fire
// both (the shell's window listener runs first). The only tolerated overlaps
// are the ones listed in SCOPED_OVERRIDES: the screen's handler sits on an
// element and stops the event before it reaches the window.

const SRC = join(__dirname, "..");
const SHELL_FILES = new Set(["app/App.tsx", "app/keymap.ts", "app/useGlobalAdd.ts", "components/CommandPalette.tsx"]);

function sourceFiles(dir: string, rel = ""): string[] {
  const out: string[] = [];
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    const relPath = rel ? `${rel}/${name}` : name;
    if (statSync(path).isDirectory()) {
      out.push(...sourceFiles(path, relPath));
    } else if (/\.(ts|tsx)$/.test(name) && !/\.test\.(ts|tsx)$/.test(name) && !name.endsWith(".d.ts")) {
      out.push(relPath);
    }
  }
  return out;
}

function shellModifierLetters(): Set<string> {
  const letters = new Set<string>();
  for (const shell of ["simple", "classic"] as const) {
    for (const binding of shellBindings(shell)) {
      const match = /^Ctrl\+(.)$/.exec(binding.keys);
      if (match) letters.add(match[1].toLowerCase());
    }
  }
  return letters;
}

it("lists every screen binding of a shell chord as a scoped override", () => {
  const letters = shellModifierLetters();
  const found: string[] = [];
  for (const file of sourceFiles(SRC)) {
    if (SHELL_FILES.has(file)) continue;
    const lines = readFileSync(join(SRC, file), "utf8").split("\n");
    lines.forEach((line) => {
      if (!/ctrl|metaKey/i.test(line)) return;
      for (const match of line.matchAll(/key(?:\.toLowerCase\(\))?\s*===\s*"(.)"/g)) {
        const letter = match[1].toLowerCase();
        if (letters.has(letter) && !/!\s*\(?\s*(?:event\.)?(?:ctrlKey|ctrl)\b/.test(line)) found.push(`${file}: Ctrl+${letter.toUpperCase()}`);
      }
    });
  }
  const listed = new Set(SCOPED_OVERRIDES.map((override) => `${override.file}: ${override.keys}`));
  expect(found.filter((entry) => !listed.has(entry))).toEqual([]);
});

// ── Window listeners that take a shell chord's key whatever the modifiers ──
// Fix round 2 (whole-stage verify 20261021-114726-Jrt7sA item 4): the scan
// above only saw explicit Ctrl comparisons. Today's window listener read
// Alt+2 as "practise item 2" (it matched /^[1-9]$/ and ignored modifiers),
// so the shell went to the Library and Today also picked an item. Every
// window-level keydown listener that takes the key of a shell chord (the
// digits of Alt+1…0, the letters of Ctrl+K/P/O/V and Alt+S, the comma of
// Ctrl+,) must either call `screenLeavesKey(event)` or check the modifiers
// where it takes that key.

function handlerBody(source: string, name: string): string | null {
  const pattern = new RegExp(`(?:const|function)\\s+${name}\\b[^{]*?\\{`, "g");
  let last: RegExpExecArray | null = null;
  for (let match = pattern.exec(source); match; match = pattern.exec(source)) last = match;
  if (!last) return null;
  let index = last.index + last[0].length;
  let depth = 1;
  while (index < source.length && depth > 0) {
    if (source[index] === "{") depth += 1;
    else if (source[index] === "}") depth -= 1;
    index += 1;
  }
  return source.slice(last.index, index);
}

function chordBaseKeys(): Set<string> {
  const keys = new Set<string>();
  for (const shell of ["simple", "classic"] as const) {
    for (const binding of shellBindings(shell)) {
      if (binding.chord.mod || binding.chord.alt) keys.add(binding.chord.key.toLowerCase());
    }
  }
  return keys;
}

/** The keys a handler takes, each with the line that takes it. */
function takenKeys(body: string): Array<{ key: string; line: string }> {
  const out: Array<{ key: string; line: string }> = [];
  for (const line of body.split("\n")) {
    for (const match of line.matchAll(/key(?:\.toLowerCase\(\))?\s*===\s*"([^"]+)"/g)) out.push({ key: match[1].toLowerCase(), line });
    for (const match of line.matchAll(/\[([^\]]*)\]\.includes\(\s*\w+\.key/g)) {
      for (const literal of match[1].matchAll(/"([^"]+)"/g)) out.push({ key: literal[1].toLowerCase(), line });
    }
    for (const match of line.matchAll(/case\s+"([^"]+)"\s*:/g)) out.push({ key: match[1].toLowerCase(), line });
    for (const match of line.matchAll(/\/\^\[(\d)-(\d)\]\$\/\.test\(/g)) {
      for (let digit = Number(match[1]); digit <= Number(match[2]); digit += 1) out.push({ key: String(digit), line });
    }
  }
  return out;
}

const MODIFIER_ON_LINE = /altKey|ctrlKey|metaKey|\bctrl\b|\bmodifier\b/;
const MODIFIER_EARLY_RETURN = /if\s*\([^)]*(?:altKey|ctrlKey|metaKey|\bctrl\b|\bmodifier\b)[^)]*\)\s*return/;

function windowListenersIgnoringModifiers(files: Array<{ file: string; source: string }>): string[] {
  const keys = chordBaseKeys();
  const found: string[] = [];
  for (const { file, source } of files) {
    for (const match of source.matchAll(/window\.addEventListener\(\s*"keydown"\s*,\s*([^,)]+)/g)) {
      const name = match[1].trim();
      if (!/^\w+$/.test(name)) {
        found.push(`${file}: an inline keydown listener (name it so this scan can read it)`);
        continue;
      }
      const body = handlerBody(source, name);
      if (body === null) {
        found.push(`${file}: ${name} (handler not found)`);
        continue;
      }
      if (/screenLeavesKey\(/.test(body) || MODIFIER_EARLY_RETURN.test(body)) continue;
      for (const taken of takenKeys(body)) {
        if (keys.has(taken.key) && !MODIFIER_ON_LINE.test(taken.line)) found.push(`${file}: ${name} takes "${taken.key}" whatever the modifiers`);
      }
    }
  }
  return [...new Set(found)];
}

it("finds no window keydown listener that takes a shell chord's key and ignores the modifiers", () => {
  const files = sourceFiles(SRC)
    .filter((file) => !SHELL_FILES.has(file))
    .map((file) => ({ file, source: readFileSync(join(SRC, file), "utf8") }));
  expect(windowListenersIgnoringModifiers(files)).toEqual([]);
});

it("catches the Today listener as it was (a digit or a letter taken whatever the modifiers)", () => {
  const before = `
    const onKey = (event: KeyboardEvent) => {
      if (["k", "ArrowUp"].includes(event.key)) up();
      else if (/^[1-9]$/.test(event.key)) pick(Number(event.key));
    };
    window.addEventListener("keydown", onKey);`;
  expect(windowListenersIgnoringModifiers([{ file: "screens/Old.tsx", source: before }])).toEqual(
    expect.arrayContaining(['screens/Old.tsx: onKey takes "k" whatever the modifiers', 'screens/Old.tsx: onKey takes "2" whatever the modifiers'])
  );
  const guarded = before.replace("(event: KeyboardEvent) => {", "(event: KeyboardEvent) => {\n      if (screenLeavesKey(event)) return;");
  expect(windowListenersIgnoringModifiers([{ file: "screens/Old.tsx", source: guarded }])).toEqual([]);
});

describe("screenLeavesKey", () => {
  function event(init: KeyboardEventInit, prevented = false): KeyboardEvent {
    const created = keydown(init);
    if (prevented) created.preventDefault();
    return created;
  }

  it("leaves modified and already-handled keys to the shell in the simple shell", () => {
    setAlgoConfig({});
    expect(screenLeavesKey(event({ key: "2", altKey: true }))).toBe(true);
    expect(screenLeavesKey(event({ key: "k", ctrlKey: true }))).toBe(true);
    expect(screenLeavesKey(event({ key: "p", metaKey: true }))).toBe(true);
    expect(screenLeavesKey(event({ key: ":" }, true))).toBe(true);
    expect(screenLeavesKey(event({ key: "2" }))).toBe(false);
    expect(screenLeavesKey(event({ key: "A", shiftKey: true }))).toBe(false);
  });

  it("leaves nothing in classic: the base screens' keys stay as they were", () => {
    setAlgoConfig({ ui: { shell: "classic" } });
    try {
      expect(screenLeavesKey(event({ key: "2", altKey: true }))).toBe(false);
      expect(screenLeavesKey(event({ key: "k", ctrlKey: true }, true))).toBe(false);
    } finally {
      setAlgoConfig({});
    }
  });
});
