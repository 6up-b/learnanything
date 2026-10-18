// Adaptive hints H2b, G-H12 (spec_adaptive_hints_v1 §11): the wording lint
// covers every new string the practice screen's hint panel shows. No label or
// line says "you don't understand", "you struggle" or "weak" (the sidecar's
// list, learnloop.hints.kinds.FORBIDDEN_WORDING, read here so the two never
// drift), and worked help says "worked help ◌" before it is taken.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, it } from "vitest";
import { FORBIDDEN_WORDING, HELP_STYLE_COPY, HINT_COPY, SHORTCUT_COPY } from "./hintCopy";

const ROOT = join(__dirname, "..", "..", "..", "..", "..");

function banned(text: string): string | undefined {
  const lower = text.toLowerCase();
  return FORBIDDEN_WORDING.find((phrase) => lower.includes(phrase));
}

it("mirrors the sidecar's forbidden wording exactly", () => {
  const kinds = readFileSync(join(ROOT, "src", "learnloop", "hints", "kinds.py"), "utf8");
  const tuple = kinds.match(/FORBIDDEN_WORDING = \(([^)]*)\)/);
  expect(tuple).not.toBeNull();
  const python = [...(tuple?.[1] ?? "").matchAll(/"([^"]+)"/g)].map((match) => match[1]);
  expect(python).toEqual([...FORBIDDEN_WORDING]);
});

it("G-H12: no fixed string of the hint panel judges the learner", () => {
  const strings = [
    ...Object.values(HINT_COPY),
    ...SHORTCUT_COPY.flatMap((entry) => [entry.label, entry.does]),
    ...HELP_STYLE_COPY.flatMap((entry) => [entry.label, entry.line])
  ];
  expect(strings.length).toBeGreaterThan(25);
  for (const text of strings) expect(banned(text), text).toBeUndefined();
});

it("G-H12: the panel's files carry no other learner-facing literal that judges", () => {
  for (const file of ["HintPanel.tsx", "useAdaptiveHints.ts", "hintCopy.ts"]) {
    // The lint's own list is the one place the phrases may appear.
    const source = readFileSync(join(__dirname, file), "utf8")
      .split("\n").filter((line) => !line.includes("FORBIDDEN_WORDING =")).join("\n");
    const literals = (source.match(/"[^"\n]{3,}"/g) ?? []).filter((literal) => literal.includes(" "));
    for (const literal of literals) expect(banned(literal), `${file}: ${literal}`).toBeUndefined();
  }
});

it("G-H12: the sidecar's kind labels and picks pass the same lint, and worked help is marked", () => {
  const kinds = readFileSync(join(ROOT, "src", "learnloop", "hints", "kinds.py"), "utf8");
  const labels = [...kinds.matchAll(/Kind\("[a-z_]+", \([0-9, ]+\), "([^"]+)"/g)].map((match) => match[1]);
  expect(labels).toHaveLength(12);
  for (const label of labels) expect(banned(label), label).toBeUndefined();
  expect(kinds).toContain('WORKED_HELP_MARK = "worked help ◌"');
});
