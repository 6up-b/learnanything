// The phone's section list names a web page's sections in words, as the desktop's Reader does: the
// extraction stores them under their heading's slug ("modeling-the-elevator-problem") and "(intro)".
import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import type { ReaderGuideSectionDto } from "@desktop/api/dto";
import { SectionList } from "./SectionList";

afterEach(cleanup);

const section = (id: string, label: string): ReaderGuideSectionDto => ({
  id, label, startSpanId: `${id}s`, endSpanId: `${id}s`, spanIds: [`${id}s`], question: null, suggestedPassages: []
});

it("UX-24: the section list says the page's sections in words, and a book's titles as they are", () => {
  const sections = [
    section("u1", "(intro)"), section("u2", "modeling-the-elevator-problem"), section("u3", "external-links"),
    section("u4", "7.1 Symmetric matrices and variance")
  ];
  render(<SectionList sections={sections} progress={null} current="u2" onPick={() => undefined} onClose={() => undefined} />);
  const list = screen.getByRole("list", { name: "Sections" });
  const names = within(list).getAllByRole("button").map((button) => button.querySelector("span")?.textContent);
  expect(names).toEqual(["Introduction", "Modeling the elevator problem", "External links", "7.1 Symmetric matrices and variance"]);
  expect(list.textContent).not.toMatch(/elevator-problem|external-links|\(intro\)/);
});
