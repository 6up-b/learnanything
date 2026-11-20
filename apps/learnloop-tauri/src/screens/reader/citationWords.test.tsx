// Ask's source chips under an answer name a web page's section in words, as
// the Contents and the path do, and a one-section reading by its title alone,
// never by a slug or "root".
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ReaderAskBranches, type ReaderExchange } from "./ReaderAskBranches";
import type { TutorRailProps } from "./TutorAnswer";
import { citationWords } from "./readerShared";
import { findJargon } from "../../copy/denyList";

vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
afterEach(cleanup);

const exchange: ReaderExchange = {
  id: "x1", parentExchangeId: null, extractionId: "ext_elevator", spanId: "p1", selectionSpanIds: ["p1"],
  selectionQuoteMd: null, question: "Why is the first elevator usually going up?", answerMd: "Because of where you stand.",
  answerMode: "answer_directly", createdAt: null,
  citations: [
    // A passage of the open reading (the walk's "· modeling-the-elevator-problem").
    { extractionId: "ext_elevator", spanId: "p2", label: "Wikipedia Elevator Paradox · modeling-the-elevator-problem" },
    // Another book's passage, retrieved: a one-section reading (the walk's "· root").
    { extractionId: "ext_ula", spanId: "q1", sourceId: "src_ula", label: "Understanding Linear Algebra Symmetric Matrices And Variance · root" },
    // A book's own section name stays as it is.
    { extractionId: "ext_axler", spanId: "r1", sourceId: "src_axler", label: "Axler · 5.C Eigenspaces" },
  ],
};

it("the chips name the section in words and a one-section reading by its title (retainer-3 #46)", () => {
  const tutor = { onOpenPassage: vi.fn() } as unknown as TutorRailProps;
  render(<ReaderAskBranches exchanges={[exchange]} query="" collapsedIds={new Set()} busy={false}
    onFollowUp={vi.fn()} onShowPassage={vi.fn()} onToggle={vi.fn()} tutor={tutor} />);
  expect(screen.getByRole("button", { name: "source: Wikipedia Elevator Paradox · Modeling the elevator problem" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "source: Understanding Linear Algebra Symmetric Matrices And Variance" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "source: Axler · 5.C Eigenspaces" })).toBeTruthy();
  const text = document.body.textContent ?? "";
  expect(text).not.toMatch(/modeling-the-elevator-problem|· root/);
  expect(findJargon(text)).toEqual([]);
});

it("the label's words: a slug in words, '(intro)' as Introduction, 'root' dropped, a title alone or a book's section unchanged", () => {
  expect(citationWords("Wikipedia Elevator Paradox · modeling-the-elevator-problem")).toBe("Wikipedia Elevator Paradox · Modeling the elevator problem");
  expect(citationWords("Wikipedia Elevator Paradox · (intro)")).toBe("Wikipedia Elevator Paradox · Introduction");
  expect(citationWords("Some Notes · root")).toBe("Some Notes");
  expect(citationWords("Some Notes")).toBe("Some Notes");
  expect(citationWords("Axler · 5.C Eigenspaces")).toBe("Axler · 5.C Eigenspaces");
  // A title with its own "·" keeps it; only the last part is the section.
  expect(citationWords("Notes · Week 2 · the-real-world-case")).toBe("Notes · Week 2 · The real world case");
});
