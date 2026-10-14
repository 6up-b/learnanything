// RW3a's restraint rules, pure (spec §6.1; UX §4.4, §10 S8): at most one
// LearnLoop mark per screenful (G13, the spacing), never on the passage the
// learner was restored to, never while skimming, never in the workbench's
// source pane (G14), the density ladder and its "fewer" step, and the fixed
// copy every cue surface shows (G16: what connects, never what is lacking).
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, it } from "vitest";
import type { ReaderCueDto } from "../../api/dto";
import {
  CUE_COPY, CUE_DENSITIES, DENSITY_BUDGET, PDF_LEFT_OUT_LINE_PX, PDF_PAGE_GAP_PX, pdfPageTops, pdfPassageTop, placeCueMarks,
  stepDown, stepMark, type PdfPageLayout,
} from "./cues";

function cue(spanId: string, rank: number): ReaderCueDto {
  return {
    cueId: `cue_${spanId}`, kind: "revisit", spanId, sectionId: "u1", learningObjectId: "lo", learningObjectTitle: "Densities",
    targetId: "err", rank, sectionRank: rank, note: "Connects to something you worked on: Densities.",
    because: "Because: your answer on 2 Oct · from the Guide's citations",
    label: "Note on this paragraph: Connects to something you worked on: Densities. Because: your answer on 2 Oct · from the Guide's citations",
    earlier: { attemptId: null, practiceItemId: null, prompt: null, answer: null, answeredAt: null, answeredOn: "2 Oct", statement: null, statementPending: false },
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

// The original's spacing (review F5): each page's own size, loaded with the
// document (never from what has been drawn), at the pane's width, with the
// pane's gap between pages and its "pages left out" line.
const LETTER = { widthPoints: 612, heightPoints: 792 };
const LANDSCAPE = { widthPoints: 792, heightPoints: 612 };
const A4 = { widthPoints: 595, heightPoints: 842 };

it("the original's spacing: consecutive landscape pages are closer than a letter-page model says", () => {
  const layout: PdfPageLayout = { widthPx: 600, pages: [{ page: 0, ...LANDSCAPE }, { page: 1, ...LANDSCAPE }] };
  const tops = pdfPageTops(layout);
  const first = pdfPassageTop(tops, 0, 100) as number;
  const second = pdfPassageTop(tops, 1, 100) as number;
  // A landscape letter page drawn 600px wide is 463.6px tall: the marks are ~478px apart.
  expect(second - first).toBeCloseTo(612 * (600 / 792) + PDF_PAGE_GAP_PX, 6);
  expect(second - first).toBeLessThan(600);
  // So in a 600px reading area they share a screenful: only the higher-ranked is drawn.
  const placed = placeCueMarks({
    ...base, viewportHeight: 600, marks: [cue("p0", 0), cue("p1", 1)],
    positionOf: (spanId) => pdfPassageTop(tops, spanId === "p0" ? 0 : 1, 100),
  });
  expect(placed.shown.map((entry) => entry.spanId)).toEqual(["p0"]);
  expect(placed.suppressed.map((entry) => entry.reason)).toEqual(["spacing"]);
});

it("the original's spacing: mixed page sizes add up page by page, each at its own scale", () => {
  const layout: PdfPageLayout = {
    widthPx: 612,
    pages: [{ page: 0, ...LETTER }, { page: 1, ...LANDSCAPE }, { page: 2, ...A4 }, { page: 5, ...LETTER, leftOutBefore: true }],
  };
  const tops = pdfPageTops(layout);
  const landscapeHeight = 612 * (612 / 792);
  const a4Height = 842 * (612 / 595);
  expect(pdfPassageTop(tops, 0, 100)).toBeCloseTo(100, 6);
  expect(pdfPassageTop(tops, 1, 100)).toBeCloseTo(792 + PDF_PAGE_GAP_PX + 100 * (612 / 792), 6);
  expect(pdfPassageTop(tops, 2, 100)).toBeCloseTo(792 + landscapeHeight + 2 * PDF_PAGE_GAP_PX + 100 * (612 / 595), 6);
  // Pages 3-4 are not in the extraction: the pane's "pages left out" line sits above page 5.
  expect(pdfPassageTop(tops, 5, 0)).toBeCloseTo(792 + landscapeHeight + a4Height + 3 * PDF_PAGE_GAP_PX + PDF_LEFT_OUT_LINE_PX, 6);
  // A page the pane does not show (or whose size is not known yet) has no place.
  expect(pdfPassageTop(tops, 3, 100)).toBeNull();
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
