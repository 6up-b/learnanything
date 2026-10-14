// RW3a's restraint rules, pure (spec §6.1; UX §4.4, §10 S8): at most one
// LearnLoop mark per screenful (G13, the spacing), never on the passage the
// learner was restored to, never while skimming, never in the workbench's
// source pane (G14), the density ladder and its "fewer" step, and the fixed
// copy every cue surface shows (G16: what connects, never what is lacking).
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, it } from "vitest";
import type { ReaderCueDto } from "../../api/dto";
import { CUE_COPY, CUE_DENSITIES, DENSITY_BUDGET, pdfPassageTop, placeCueMarks, stepDown, stepMark } from "./cues";

function cue(spanId: string, rank: number): ReaderCueDto {
  return {
    cueId: `cue_${spanId}`, kind: "revisit", spanId, sectionId: "u1", learningObjectId: "lo", learningObjectTitle: "Densities",
    targetId: "err", rank, sectionRank: rank, note: "Connects to something you worked on: Densities.",
    because: "Because: your answer on 2 Oct · from the Guide's citations",
    label: "Note on this paragraph: Connects to something you worked on: Densities. Because: your answer on 2 Oct · from the Guide's citations",
    earlier: { attemptId: null, practiceItemId: null, prompt: null, answeredAt: null, answeredOn: "2 Oct", statement: null, statementPending: false },
  };
}

const AT: Record<string, number> = { a: 100, b: 400, c: 1500, d: 1700, e: 3000 };
const base = {
  muted: false, working: false, restoredSpanId: null, onePerViewport: true,
  positionOf: (spanId: string) => AT[spanId] ?? null, viewportHeight: 800,
};

it("G13 spacing: a lower-ranked mark within one screenful of a higher-ranked one is not shown", () => {
  // Ranked c, a, b, d, e: c (1500) first; a (100) is far; b (400) is within
  // 800 of a; d (1700) within 800 of c; e (3000) is far.
  const marks = [cue("c", 0), cue("a", 1), cue("b", 2), cue("d", 3), cue("e", 4)];
  const placed = placeCueMarks({ ...base, marks });
  expect(placed.shown.map((entry) => entry.spanId)).toEqual(["a", "c", "e"]); // reading order
  expect(placed.suppressed.map(({ cue: entry, reason }) => [entry.spanId, reason])).toEqual([["b", "spacing"], ["d", "spacing"]]);
  // Pairwise, no two drawn marks share a screenful.
  const ys = placed.shown.map((entry) => AT[entry.spanId]);
  for (const y of ys) for (const other of ys) if (y !== other) expect(Math.abs(y - other)).toBeGreaterThanOrEqual(800);
});

it("G13 spacing: with one_per_viewport off the sidecar's per-section budget alone decides", () => {
  const marks = [cue("a", 0), cue("b", 1)];
  expect(placeCueMarks({ ...base, marks, onePerViewport: false }).shown.map((entry) => entry.spanId)).toEqual(["a", "b"]);
});

it("G14: never on the passage the learner was restored to, and the next mark takes its place", () => {
  const marks = [cue("a", 0), cue("b", 1)];
  const placed = placeCueMarks({ ...base, marks, restoredSpanId: "a" });
  expect(placed.shown.map((entry) => entry.spanId)).toEqual(["b"]);
  expect(placed.suppressed).toEqual([{ cue: marks[0], reason: "restored_line" }]);
});

it("G14: skim mutes every mark, and so does the workbench's source pane", () => {
  const marks = [cue("a", 0), cue("e", 1)];
  const skim = placeCueMarks({ ...base, marks, muted: true });
  expect(skim.shown).toEqual([]);
  expect(skim.suppressed.map((entry) => entry.reason)).toEqual(["skim", "skim"]);
  const working = placeCueMarks({ ...base, marks, working: true });
  expect(working.shown).toEqual([]);
  expect(working.suppressed.map((entry) => entry.reason)).toEqual(["working", "working"]);
});

it("a passage with no place to draw (a page-only original) shows no mark", () => {
  const placed = placeCueMarks({ ...base, marks: [cue("zz", 0), cue("a", 1)] });
  expect(placed.shown.map((entry) => entry.spanId)).toEqual(["a"]);
  expect(placed.suppressed[0].reason).toBe("no_place");
});

it("the density ladder: off, fewer, normal, more = 0, 1, 2, 4; fewer steps down one notch", () => {
  expect(CUE_DENSITIES.map((density) => DENSITY_BUDGET[density])).toEqual([0, 1, 2, 4]);
  expect(CUE_DENSITIES.map(stepDown)).toEqual(["off", "off", "fewer", "normal"]);
});

it("Alt+↓ / Alt+↑ step through the drawn marks in reading order", () => {
  expect(stepMark(3, -1, 1)).toBe(0);
  expect(stepMark(3, -1, -1)).toBe(2);
  expect(stepMark(3, 0, 1)).toBe(1);
  expect(stepMark(3, 2, 1)).toBeNull();
  expect(stepMark(3, 0, -1)).toBeNull();
  expect(stepMark(0, -1, 1)).toBeNull();
});

it("the original's spacing models letter pages at the pane's width, never what has been drawn", () => {
  const width = 612;
  expect(pdfPassageTop(0, 100, width)).toBe(100);
  expect(pdfPassageTop(1, 100, width)).toBe(792 + 14 + 100);
  expect(pdfPassageTop(1, 100, width * 2)).toBe(2 * (792 + 100) + 14);
});

// Trait words, and about the learner's work, verdict words (spec G16, UX U6);
// no counts of open or unfinished things, never "overdue" (U12).
const BANNED = /\b(weak|you don'?t understand|you struggle|you always|wrong|error|errors|mistake|mistakes|confused|failed|failure|overdue)\b/i;

it("G16 lint: every fixed string on a cue surface says what connects, never what is lacking", () => {
  const strings: string[] = Object.values(CUE_COPY);
  expect(strings.length).toBeGreaterThan(20);
  for (const text of strings) expect(text).not.toMatch(BANNED);
  expect(CUE_COPY.legendRevisit).toContain("from the Guide's citations");
  expect(CUE_COPY.checkMeHint).toContain("on your own");
});

it("G16 lint: the cue components carry no other learner-facing literal that judges", () => {
  for (const file of ["MarginMark.tsx", "ReaderCueSettings.tsx", "useReaderCues.ts"]) {
    const source = readFileSync(join(__dirname, file), "utf8");
    // Sentence-like literals (a space inside); single-token codes such as a
    // check's "failed" phase are not copy.
    const literals = (source.match(/"[^"\n]{3,}"/g) ?? []).filter((literal) => literal.includes(" "));
    for (const literal of literals) expect(literal).not.toMatch(BANNED);
  }
});

it("G14: the mark's CSS draws a static glyph (no text node to quote, nothing that moves)", () => {
  const css = readFileSync(join(__dirname, "..", "..", "styles", "app.css"), "utf8");
  const rules = css.split("}").filter((rule) => rule.includes(".ll-reader-cue-mark"));
  expect(rules.length).toBeGreaterThan(0);
  expect(rules.join("}")).toContain('content: "◌┆"');
  for (const rule of rules) expect(rule).not.toMatch(/animation|transition|@keyframes/);
});
