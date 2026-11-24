// The workbench's nouns (the owner's naming decision, 2026-11-23: "companion, pad, saved question, cold check"): what a
// learner reads on the desks and in the lesson view says pad (never scratchpad), saved question and save for later
// (never carried question or carry), the companion for the ask surface (the tutor only as who answers), and cold check
// for a check on your own. The code keeps its own names (carried_*, the scratchpad classes, the "carry" verb id); only
// what a learner reads is scanned: string literals that read as words (a space, or a capital first) outside class
// names and imports, and JSX text. The glossary is in docs/reviews/reader-workbench-copy-audit.md.
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const SRC = join(__dirname, "../..");
const ROOTS = ["screens/desks", "screens/LessonView.tsx"];

/** Each retired word, with what replaced it. */
const RETIRED: Array<{ pattern: RegExp; instead: string }> = [
  { pattern: /scratch ?pads?/i, instead: "pad / pads" },
  { pattern: /\bcarr(?:y|ies|ied|ying)\b/i, instead: "save for later / saved question" },
  { pattern: /\b(?:checks?|questions?) on your own\b/i, instead: "cold check" },
  { pattern: /\b(?:in|to|ask|open it in) the tutor\b|\bthe tutor waits\b|◇ tutor\b/i, instead: "the companion (the tutor only names who answers)" },
];

function files(path: string): string[] {
  const full = join(SRC, path);
  if (!statSync(full).isDirectory()) return [path];
  return readdirSync(full).flatMap((entry) => files(join(path, entry)));
}

/** The source with its comments blanked (line count kept), so a comment never reads as learner text. */
function withoutComments(source: string): string {
  let out = "";
  let i = 0;
  let quote: string | null = null;
  while (i < source.length) {
    const ch = source[i];
    if (quote) {
      out += ch;
      if (ch === "\\") {
        out += source[i + 1] ?? "";
        i += 2;
        continue;
      }
      if (ch === quote) quote = null;
      i += 1;
      continue;
    }
    if (ch === '"' || ch === "'" || ch === "`") {
      quote = ch;
      out += ch;
      i += 1;
      continue;
    }
    if (ch === "/" && source[i + 1] === "/" && source[i - 1] !== ":") {
      while (i < source.length && source[i] !== "\n") i += 1;
      continue;
    }
    if (ch === "/" && source[i + 1] === "*") {
      const end = source.indexOf("*/", i + 2);
      const body = source.slice(i, end < 0 ? source.length : end + 2);
      out += body.replace(/[^\n]/g, " ");
      i += body.length;
      continue;
    }
    out += ch;
    i += 1;
  }
  return out;
}

/** What a learner can read in a file: its word-like string literals (not class names or imports) and its JSX text. */
function learnerText(source: string): Array<{ line: number; text: string }> {
  const code = withoutComments(source);
  const lineAt = (offset: number) => code.slice(0, offset).split("\n").length;
  const out: Array<{ line: number; text: string }> = [];
  for (const match of code.matchAll(/"((?:[^"\\\n]|\\.)*)"|'((?:[^'\\\n]|\\.)*)'|`((?:[^`\\]|\\.)*)`/g)) {
    const text = (match[1] ?? match[2] ?? match[3] ?? "").replace(/\$\{[^}]*\}/g, " ");
    const before = code.slice(Math.max(0, (match.index ?? 0) - 24), match.index);
    if (/className[=:]\s*\{?\s*$|classList\.\w+\(\s*$|from\s*$|import\(\s*$|data-[\w-]+[=:]\s*$/.test(before)) continue;
    // Words a learner reads: two words or more, or a capitalised label; a key or an id is neither.
    if ((text.match(/[A-Za-z]{2,}/g) ?? []).length < 2 && !/^[A-Z]/.test(text)) continue;
    out.push({ line: lineAt(match.index ?? 0), text });
  }
  // JSX text: between a tag's end and the next tag (an arrow's `=>` or a generic's `<T>` is not one).
  for (const match of code.matchAll(/(?<![=-])>([^<>{}]*[A-Za-z][^<>{}]*)(?=<[/A-Za-z]|\{)/g)) {
    // A type's closing `>` followed by more type is code, not text.
    if (/\[\]|\):|=>|\b(?:const|return|function)\b/.test(match[1])) continue;
    out.push({ line: lineAt(match.index ?? 0), text: match[1] });
  }
  // ...and the words after an expression, up to the closing tag ("{n}c</kbd> carry “{line}”</button>").
  for (const match of code.matchAll(/\}([^<>{}\n;=()]*[A-Za-z][^<>{}\n;=()]*)(?=<\/)/g)) {
    out.push({ line: lineAt(match.index ?? 0), text: match[1] });
  }
  return out;
}

describe("the workbench's nouns", () => {
  const sources = ROOTS.flatMap(files).filter((file) => /\.tsx?$/.test(file) && !/\.test\.tsx?$/.test(file));

  it("scans the desks and the lesson view", () => {
    expect(sources.length).toBeGreaterThan(50);
    expect(sources).toContain("screens/LessonView.tsx");
  });

  it("no learner-facing string uses a retired word", () => {
    const found: string[] = [];
    for (const file of sources) {
      for (const { line, text } of learnerText(readFileSync(join(SRC, file), "utf8"))) {
        for (const { pattern, instead } of RETIRED) {
          if (pattern.test(text)) found.push(`${file}:${line}: “${text.trim().slice(0, 80)}” (say ${instead})`);
        }
      }
    }
    expect(found).toEqual([]);
  });

  it("the scan reads what a learner reads, and leaves the code's names alone", () => {
    const sample = [
      'const a = <button type="button" title="Open carried question">◌</button>;',
      'const b = { id: "carry", kind: "carried", className: "desk-pmark carried" };',
      "const c = <h4><span>Carried</span></h4>;",
      'import { CarriedList } from "./carried/related";',
      "// a carried question in a comment",
      "const d = `move to scratchpad ${x}`;",
      "const e = (f: () => void) => g<T>(f);",
      "function h(w: Array<{ id: string }>, links: Link[], carried: Carried[]): Placed[] {}",
      "const k = `carried:${a}:${b}`;",
      "const m = <div>you carried: {q.text} · since {when}</div>;",
      "const n = <button><kbd>{i}c</kbd> carry “{line}”</button>;",
    ].join("\n");
    const texts = learnerText(sample).map((each) => each.text.trim());
    expect(texts).toEqual(expect.arrayContaining(["Open carried question", "Carried", "move to scratchpad", "you carried:", "carry “"]));
    expect(texts.some((text) => /desk-pmark|carry$|^carried$|related|comment/.test(text))).toBe(false);
  });
});
