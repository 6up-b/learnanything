// The goal lens's pure helpers (spec §12.2-§12.5): indexing a whole-reading goal.lens, filtering it to the
// passages in view, dimming, the why card's lines, the band's lines and the callouts.
import { describe, expect, it } from "vitest";
import { FixtureGoal } from "../../../fixtures/desks/goal";
import { FIXTURE_SOURCES } from "../../../fixtures/desks/sources";
import type { GoalLensSectionDto } from "../../../api/dto";
import {
  calloutFor,
  countsLine,
  deeperDepthLabel,
  dotTitle,
  hereLine,
  indexLens,
  isDimmed,
  levelsInRange,
  markKind,
  nextLine,
  truncate,
  whyLevelLine,
} from "./model";

const BOOK = FIXTURE_SOURCES.book.extractionId;

function fixture(depth: "get_the_idea" | "learn_to_use_it" = "learn_to_use_it") {
  const goal = new FixtureGoal();
  goal.depth = depth;
  return { goal, band: goal.band(), lens: goal.lens(BOOK) };
}

describe("one whole-reading lens, filtered client-side", () => {
  it("indexes every passage under its section and each section's start", () => {
    const { lens } = fixture();
    const index = indexLens(lens)!;
    expect(index.bySpan.get(`${BOOK}_s1_2`)?.level).toBe("core");
    expect(index.bySpan.get(`${BOOK}_s1_h`)?.sectionId).toBe(`${BOOK}_s1`);
    expect(index.starts.get(`${BOOK}_s5_h`)?.level).toBe("core");
    expect(indexLens(null)).toBeNull();
  });

  it("filters a visible range to its sections, once each, in reading order, asking nothing", () => {
    const index = indexLens(fixture().lens);
    const inView = levelsInRange(index, [`${BOOK}_s3_4`, `${BOOK}_s4_h`, `${BOOK}_s4_1`, `${BOOK}_s4_2`, "elsewhere"]);
    expect(inView.map((section) => section.sectionId)).toEqual([`${BOOK}_s3`, `${BOOK}_s4`]);
    expect(levelsInRange(null, [`${BOOK}_s1_1`])).toEqual([]);
  });
});

describe("marks, dimming and the why", () => {
  it("draws one mark per level and none for an unmapped section", () => {
    expect(["core", "supporting", "skippable", "later", "already_shown", "partial", "unmapped"].map((level) => markKind(level as GoalLensSectionDto["level"])))
      .toEqual(["core", "sup", "skip", "later", "shown", "partial", null]);
  });

  it("dims skippable and later text while dimming is on, never a section read anyway", () => {
    const { goal } = fixture();
    const skippable = indexLens(goal.lens(BOOK))!.bySpan.get(`${BOOK}_s6_1`);
    expect(isDimmed(skippable, true)).toBe(true);
    expect(isDimmed(skippable, false)).toBe(false);
    goal.sectionChoice({ goalId: "g", extractionId: BOOK, sectionId: `${BOOK}_s6`, choice: "read_anyway", operationId: "op_00000001" });
    expect(isDimmed(indexLens(goal.lens(BOOK))!.bySpan.get(`${BOOK}_s6_1`), true)).toBe(false);
    expect(isDimmed(indexLens(goal.lens(BOOK))!.bySpan.get(`${BOOK}_s1_1`), true)).toBe(false);
  });

  it("names the deeper depth a later passage is kept at", () => {
    const { band, lens } = fixture("get_the_idea");
    const later = indexLens(lens)!.bySpan.get(`${BOOK}_s4_1`)!;
    expect(later.level).toBe("later");
    expect(deeperDepthLabel(band)).toBe("learn to use it");
    expect(whyLevelLine(later, band)).toBe("Needed only at learn to use it");
    expect(whyLevelLine(indexLens(lens)!.bySpan.get(`${BOOK}_s1_1`)!, band)).toBe("core for your goal");
  });
});

describe("the band's lines", () => {
  it("counts the LOs within the depth and says what is next", () => {
    const { band } = fixture();
    expect(countsLine(band)).toBe("5 topics · 1 likely · 4 untested");
    expect(countsLine(fixture("get_the_idea").band)).toBe("3 topics · 1 likely · 2 untested");
    expect(nextLine(band)).toEqual({ text: "§ Softmax, a short book 4 Cross-entropy", kind: "section" });
    expect(nextLine({ ...band, next: { kind: "checks", count: 2, check: null } }).text).toBe("◇ 2 cold checks due · answer in Today");
    expect(nextLine({ ...band, next: { kind: "path_read" } })).toEqual({ text: "No cold checks due. No further reading suggested on this path.", kind: "read" });
  });

  it("maps the reading position through the lens", () => {
    const { band, lens } = fixture();
    const index = indexLens(lens);
    expect(hereLine(index, `${BOOK}_s1_2`, null, band)).toEqual({ where: "1 Scores into weights", lo: "Turn scores into softmax weights", tag: null, loId: "lo_fx_softmax" });
    expect(hereLine(index, `${BOOK}_s4_1`, null, band)?.tag).toBe("Background");
    expect(hereLine(index, `${BOOK}_s6_1`, null, band)).toEqual({ where: "6 Computing it safely", lo: null, tag: "Not needed for your goal", loId: null });
    expect(hereLine(index, null, null, band)).toBeNull();
  });

  it("never names an LO with a due check", () => {
    const { band } = fixture();
    const dot = { ...band.learningObjects![0], title: null, held: true };
    expect(dotTitle(dot)).toBe("a topic with a cold check due");
    expect(truncate("x".repeat(50), 44)).toHaveLength(44);
  });
});

describe("callouts", () => {
  it("speaks the path's own reason at a section the path places, and nothing elsewhere", () => {
    const index = indexLens(fixture().lens)!;
    expect(calloutFor(index.starts.get(`${BOOK}_s1_h`)!)).toEqual({
      label: "for your goal · Main reading",
      body: "The formula you'll write: exponentiate each score and divide by the sum. Main reading for “Turn scores into softmax weights”.",
      held: false,
    });
    expect(calloutFor(index.starts.get(`${BOOK}_s4_h`)!)?.label).toBe("for your goal · Background");
    expect(calloutFor(index.starts.get(`${BOOK}_s6_h`)!)).toBeNull();
    expect(calloutFor(index.starts.get(`${BOOK}_s2_h`)!)).toBeNull();
    const held = { ...index.starts.get(`${BOOK}_s1_h`)!, held: true, reasonMd: "Details are hidden while a cold check is due." };
    expect(calloutFor(held)).toEqual({ label: "for your goal", body: "Details are hidden while a cold check is due.", held: true });
  });
});
