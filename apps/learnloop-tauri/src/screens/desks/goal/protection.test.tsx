// RD6's fix round (spec §12.6.1, decision D15): with a cold check due on an LO, the server masks every text-bearing field
// of the band, the lens and the path (curriculum.goal_lens_protection). This checks the client adds nothing back: the
// band, the "you are reading" line (whose place words come from the window, the book's own heading), the path view and
// the why card render no text, title or attribute naming the masked LO or its section.
import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { GoalBandDto, GoalLensDto } from "../../../api/dto";
import { FixtureGoal } from "../../../fixtures/desks/goal";
import { FIXTURE_SOURCES } from "../../../fixtures/desks/sources";
import { GoalBand } from "./GoalBand";
import { WhyCard } from "./marks";
import { hereLine, indexLens } from "./model";
import { PathView } from "./PathView";

const BOOK = FIXTURE_SOURCES.book.extractionId;
const MASKED = "lo_fx_softmax";
const NEUTRAL_LO = "a topic with a cold check due";
const NEUTRAL_SECTION = "a section held until its cold check";
const HELD_REASON = "A cold check is due on a topic here. Why it matters comes back once you've answered it.";
afterEach(cleanup);

/** The band and lens as the server sends them while MASKED's check is due (goal_lens_protection's rules). */
function masked(): { band: GoalBandDto; lens: GoalLensDto; names: string[] } {
  const goal = new FixtureGoal();
  const band = goal.band();
  const lens = goal.lens(BOOK);
  const dot = band.learningObjects!.find((each) => each.learningObjectId === MASKED)!;
  const line = band.path!.lines.find((each) => each.learningObjectId === MASKED)!;
  // What may not appear anywhere: the LO's title and the titles of the sections that treat it.
  const names = [dot.title!, line.section.title, ...line.alternates.map((alternate) => alternate.title)];
  const heldSections = new Set([line.section.sectionId, ...line.alternates.map((alternate) => alternate.sectionId)]);
  const neutral = <T extends { title: string }>(section: T): T => ({ ...section, title: NEUTRAL_SECTION, treatmentWords: "", treatment: null, difference: "" });
  band.learningObjects = band.learningObjects!.map((each) => (each.learningObjectId === MASKED
    ? { ...each, title: null, readinessLine: null, held: true, primary: each.primary ? { ...each.primary, title: NEUTRAL_SECTION } : null } : each));
  band.path = { ...band.path!, lines: band.path!.lines.map((each) => (each.learningObjectId === MASKED
    ? { ...each, title: NEUTRAL_LO, phrase: "", reason: null, held: true, section: neutral(each.section), alternates: each.alternates.map(neutral),
        exercise: each.exercise ? { ...each.exercise, label: "an exercise held until its cold check" } : null }
    : { ...each, section: heldSections.has(each.section.sectionId) ? neutral(each.section) : each.section })) };
  if (band.next?.kind === "section" && band.next.learningObjectId === MASKED) band.next = { ...band.next, section: { ...band.next.section, title: NEUTRAL_SECTION } };
  lens.levels = lens.levels.map((level) => (level.loIds.includes(MASKED) || heldSections.has(level.sectionId)
    ? { ...level, held: true, title: NEUTRAL_SECTION, reasonMd: HELD_REASON, coverageLine: null, learnerLine: null, determiningLoId: null,
        learningObjects: level.learningObjects.map((entry) => ({ ...entry, title: null, held: true })) }
    : level));
  return { band, lens, names };
}

function leaks(names: string[]): string[] {
  const found: string[] = [];
  const all = [document.body, ...document.body.querySelectorAll("*")];
  for (const name of names) {
    const wanted = name.toLowerCase();
    if ((document.body.textContent ?? "").toLowerCase().includes(wanted)) found.push(`text: ${name}`);
    for (const element of all) {
      for (const attribute of [...element.attributes]) {
        if (attribute.value.toLowerCase().includes(wanted)) found.push(`${element.tagName.toLowerCase()}[${attribute.name}]: ${name}`);
      }
    }
  }
  return found;
}

describe("a masked LO, rendered", () => {
  it("is named nowhere in the band, its you-are-reading line, the path view or the why card", () => {
    const { band, lens, names } = masked();
    const index = indexLens(lens)!;
    const held = lens.levels.find((level) => level.loIds.includes(MASKED))!;
    // The window's own place words are the book's heading of the held section: they must not reach the band.
    const here = hereLine(index, held.startSpanId, held.title === NEUTRAL_SECTION ? names[1] : "", band);
    render(
      <div>
        <GoalBand band={band} goals={new FixtureGoal().goals().goals} here={here} dimOn onToggleDim={vi.fn()} onPath={vi.fn()} onDepth={vi.fn()}
          onOpenLo={vi.fn()} onNext={vi.fn()} onChooseGoal={vi.fn()} onMapIt={vi.fn()} />
        <PathView band={band} here={MASKED} notNeeded={[]} onClose={vi.fn()} onDepth={vi.fn()} onOpen={vi.fn()} onUseInstead={vi.fn()}
          onReadAnyway={vi.fn()} onAddPhrase={vi.fn()} />
        <WhyCard why={{ section: held, extractionId: BOOK, windowId: "w", rect: { left: 10, top: 200, right: 13, bottom: 260 } }} band={band} />
      </div>,
    );
    expect(here?.where).toBe(NEUTRAL_SECTION);
    expect(leaks(names)).toEqual([]);
    // It is still there, held: the dot, the path row and the card say a check is due.
    expect(document.querySelector(`[data-gstop='${MASKED}']`)).toBeTruthy();
    expect(document.body.textContent).toContain(NEUTRAL_LO);
  });
});
