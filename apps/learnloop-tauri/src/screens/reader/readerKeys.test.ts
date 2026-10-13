// UX Phase 1 re-test (#9): the Reader's key bar said "release ctrl capture box
// union · alt+drag sweep blocks". It says what each key gets the learner.
import { expect, it } from "vitest";
import { findJargon } from "../../copy/denyList";
import { readerKeyBarKeys } from "./readerKeys";

const INTERNAL = /union|sweep|capture box|blocks?\b/i;

it.each([true, false])("the key bar speaks plainly (pdf surface: %s)", (pdf) => {
  const keys = readerKeyBarKeys(pdf);
  const text = keys.map((k) => `${k.key} ${k.label}`).join(" · ");
  expect(text).not.toMatch(INTERNAL);
  expect(findJargon(text)).toEqual([]);
  expect(keys.map((k) => k.key)).not.toContain("release ctrl");
  expect(keys.find((k) => k.key === "ctrl+drag")?.label).toBe("select by drawing boxes");
});

it("names the whole-paragraph selection only where the PDF offers it", () => {
  expect(readerKeyBarKeys(true).find((k) => k.key === "alt+drag")?.label).toBe("select whole paragraphs");
  expect(readerKeyBarKeys(false).some((k) => k.key === "alt+drag")).toBe(false);
});
