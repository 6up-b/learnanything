// The goal lens on the shelf (spec §12.3): a row's bar at its right edge, a line on what the source is for, and the
// path's ranges on the minimap; and the shelf row's lens read from a reading's lens.
import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { FixtureGoal } from "../../../fixtures/desks/goal";
import { FIXTURE_SOURCES } from "../../../fixtures/desks/sources";
import { Shelf, type ShelfRow } from "../Shelf";
import { indexLens, shelfGoal } from "./model";

afterEach(cleanup);

describe("a shelf row through the lens", () => {
  it("names how many LOs a reading is primary for and draws the path's ranges as fractions of it", () => {
    const goal = new FixtureGoal();
    const book = shelfGoal(indexLens(goal.lens(FIXTURE_SOURCES.book.extractionId)))!;
    expect(book.mark).toBe("core");
    expect(book.line).toBe("primary for 2 of your LOs");
    // Sections 1-5 are on the path (core or supporting), section 6 is not: one merged range.
    expect(book.ranges).toHaveLength(1);
    expect(book.ranges[0][0]).toBe(0);
    expect(book.ranges[0][1]).toBeLessThan(1);
    const video = shelfGoal(indexLens(goal.lens(FIXTURE_SOURCES.video.extractionId)))!;
    expect([video.mark, video.line]).toEqual(["sup", "another way"]);
    expect(shelfGoal(indexLens({ ...goal.lens("fx_ext_nowhere") }))).toEqual({ mark: null, line: "not mapped for this goal yet", ranges: [] });
    expect(shelfGoal(null)).toBeNull();
  });

  it("calls a source not needed only when every section is known not needed", () => {
    const lens = new FixtureGoal().lens(FIXTURE_SOURCES.book.extractionId);
    const skip = { level: "skippable" as const, mapping: "mapped" as const, reasonKey: "out_of_scope" as const, determiningLoId: null };
    const allSkip = { ...lens, levels: lens.levels.map((level) => ({ ...level, ...skip })) };
    expect(shelfGoal(indexLens(allSkip))!.line).toBe("not needed for your goal");
    // One section not mapped (or partly): what it holds is unknown, so the source is not called not needed.
    const oneOpen = { ...allSkip, levels: allSkip.levels.map((level, index) => (index === 0 ? { ...level, level: "unmapped" as const, mapping: "unmapped" as const } : level)) };
    expect([shelfGoal(indexLens(oneOpen))!.mark, shelfGoal(indexLens(oneOpen))!.line]).toEqual(["partial", "partly mapped for this goal"]);
    const later = { ...oneOpen, levels: oneOpen.levels.map((level, index) => (index === 1 ? { ...level, level: "later" as const } : level)) };
    expect(shelfGoal(indexLens(later))!.line).toBe("partly mapped for this goal");
  });

  it("draws the mark, the ranges and the line on the row's own markup", () => {
    const row: ShelfRow = { windowId: "w", slot: 0, glyph: "§", kind: "book", title: "Softmax, a short book", state: "focus", progress: 0.3,
      where: "1 Scores into weights", goal: { mark: "core", line: "primary for 4 of your LOs", ranges: [[0, 0.5], [0.7, 0.8]] } };
    render(<Shelf rows={[row, { ...row, windowId: "x", slot: 1, state: null, progress: null, goal: { mark: "skip", line: "not needed for your goal", ranges: [] } }]}
      folded={false} undo={null} onFocus={() => undefined} onReorder={() => undefined} />);
    const first = document.querySelector("[data-shelf-window='w']")!;
    expect(first.className).toBe("desk-src open prim g-core");
    expect(first.querySelector(".gm.sh")).toBeTruthy();
    expect([...first.querySelectorAll(".bar .gr")].map((range) => (range as HTMLElement).style.left + " " + (range as HTMLElement).style.width)).toEqual(["0% 50%", "70% 10%"]);
    expect(first.querySelector(".gwl")!.textContent).toBe("◎ primary for 4 of your LOs");
    const second = document.querySelector("[data-shelf-window='x']")!;
    expect(second.className).toBe("desk-src g-skip");
    expect(second.querySelector(".bar")).toBeNull();
  });

  it("without a lens the row is as before", () => {
    render(<Shelf rows={[{ windowId: "w", slot: 0, glyph: "§", kind: "book", title: "A", state: null, progress: null, where: null }]}
      folded={false} undo={null} onFocus={() => undefined} onReorder={() => undefined} />);
    const row = document.querySelector("[data-shelf-window='w']")!;
    expect(row.className).toBe("desk-src");
    expect(row.querySelector(".gm, .gwl, .bar")).toBeNull();
  });
});
