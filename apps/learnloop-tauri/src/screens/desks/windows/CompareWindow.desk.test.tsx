// The Compare window on a desk, with its real body (spec §21.1, "Library ask, compare, keep, roles": "Compare and keep
// tests against the Compare window"). The desks mount the library pane in the window and a book window beside it;
// only the sidecar is faked:
//
// * asking there runs the library ask anchored on the passage the window was opened on, and each hit shows its role;
// * two pinned passages compare by point, and "keep comparison ⇄" keeps it with its context: the book open beside
//   reads its marks again and shows ⇄ on the passage, with no reload;
// * "practice this ▸" hands the shell a learner pick in the asked book, at the asked passage, and that book's window
//   takes the focus.
import { cleanup, fireEvent, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { CompareTableDto, LibraryAskDto } from "../../../api/dto";
import { answers, inputsOf, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_SOURCES } from "../../../fixtures/desks/sources";
import { readerIntentContractFixture } from "../../../fixtures/readerIntentContract";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const { book, paper } = FIXTURE_SOURCES;
const FIRST = `${book.extractionId}_s1_1`;
const PAPER_FIRST = `${paper.extractionId}_p1_1`;
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };
const COMPARE_WINDOW = { windowId: "w_compare", pane: 0, kind: "compare", active: true,
  view: { compareAnchor: { extractionId: book.extractionId, spanIds: [FIRST], sourceId: book.sourceId, revisionId: "rev_fx" } },
  content: { kind: "compare", query: "why exponentials" } };

function hit(key: string, sourceId: string, sourceTitle: string, text: string, role: string) {
  const [extractionId, spanId] = key.split(":");
  return { key, extractionId, spanId, sourceId, sourceTitle, section: "1", page: 1, text, role, group: "Foundation", expansion: null,
    learningObjectIds: [], authorship: "source" as const, label: "source-authored" };
}

const ASK: LibraryAskDto = {
  askId: "la_1", query: "why exponentials", entry: "library_search", status: "ok", policy: "reading", personalized: true, basis: "keyword + meaning",
  learningObjectIds: [], extractionId: book.extractionId, anchorSpanIds: [FIRST],
  hits: [
    hit(`${book.extractionId}:${FIRST}`, book.sourceId, "Softmax", "Exponentials turn differences into ratios.", "worked_example"),
    { ...hit(`${paper.extractionId}:${PAPER_FIRST}`, paper.sourceId, "Attention", "Scores pass through a softmax.", "definition"),
      proposedRole: { role: "counterexample", label: "model's label" } as never },
  ],
  groups: {
    sources: [
      { sourceId: book.sourceId, sourceTitle: "Softmax", groups: [{ group: "Worked example", keys: [`${book.extractionId}:${FIRST}`] }] },
      { sourceId: paper.sourceId, sourceTitle: "Attention", groups: [{ group: "Foundation", keys: [`${paper.extractionId}:${PAPER_FIRST}`] }] },
    ],
    expansions: [],
  },
  expansions: [], expandGraph: false, sourceCount: 2, passageCount: 2,
};

const TABLE: CompareTableDto = {
  askId: "la_1", status: "ok", comparisonId: "scmp_1", header: "differences kept · each line quotes its own source",
  rows: [
    { sourceId: book.sourceId, sourceTitle: "Softmax", key: `${book.extractionId}:${FIRST}`, page: 1, isOpenSource: true,
      contributes: [{ line: "the ratio view", quote: "differences into ratios", authorship: "ai" }], assumes: [], differs: [] },
    { sourceId: paper.sourceId, sourceTitle: "Attention", key: `${paper.extractionId}:${PAPER_FIRST}`, page: 1, isOpenSource: false,
      contributes: [{ line: "the mechanism", quote: "pass through a softmax", authorship: "ai" }], assumes: [], differs: [] },
  ],
  alsoDiscussedIn: [], unverifiedSources: [], droppedPins: [], droppedLineCount: 0, kept: null,
};

const done = <T,>(result: T, kind: string) => ({ jobId: `ljob_${kind}`, kind, askId: "la_1", state: "done" as const, result });
const backend = { kept: false };

beforeEach(() => {
  resetSidecar();
  backend.kept = false;
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
  answers.set("reader_prompt_contract", () => ({
    version: "fixture", context: "reader", readerEnabled: true, notSocraticByDefault: true, defaultAnswerMode: "answer_directly",
    answerModes: ["answer_directly"], mayReveal: [], manifestIncludes: [], manifestNeverIncludes: [], citations: "spans",
    exposureOnCommit: "none", inquiryEnabled: true, intent: readerIntentContractFixture, activeReading: { foldBlocks: 3 },
    libraryAsk: { expandGraph: false, personalizedDefault: true, compare: true },
    compareKeep: { library: true, tutor: true, perspectives: true, maxPerspectives: 4 },
  }));
  answers.set("reader_library_ask", () => done(ASK, "ask"));
  answers.set("reader_library_ask_notes", () => done({ askId: "la_1", status: "judged", notes: [], order: [] }, "notes"));
  answers.set("reader_library_compare", () => done(TABLE, "compare"));
  answers.set("reader_library_compare_keep", () => {
    backend.kept = true;
    return { askId: "la_1", alreadyKept: false, addedTakes: 0, kept: { askId: "la_1", keptAt: "2026-11-23T09:00:00Z", objects: [], relations: [], takes: [],
      notKept: 0, status: "proposed", label: "kept as proposals · nothing changes your map until you review them" } };
  });
  answers.set("reader_kept_comparisons", (input) => ({
    extractionId: input.extractionId, label: "a comparison you kept",
    marks: backend.kept && input.extractionId === book.extractionId
      ? [{ spanId: FIRST, askIds: ["la_1"], keptAt: "2026-11-23T09:00:00Z", otherSources: ["Attention"] }] : [],
  }));
  answers.set("find_practice", () => ({ version: 1, status: "ok", proposalId: "pp_1", sourceExercises: [], items: [
    { rank: 1, practiceItemId: "pi_softmax", learningObjectId: "lo_softmax", learningObjectTitle: "Softmax", practiceMode: "free_response",
      prompt: "Why does softmax exponentiate?", facetIds: [], rationale: null },
  ] }));
  answers.set("record_proposal_impressions", () => ({ recorded: 1 }));
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

async function openCompare(onCheckMe = vi.fn()) {
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never], [COMPARE_WINDOW as never]]), props: { reader: { onCheckMe } } });
  await settleDesk(0, 20);
  const compare = document.querySelector<HTMLElement>('[data-desk-window="w_compare"]')!;
  const bookWin = document.querySelector<HTMLElement>('[data-desk-window="w_book"]')!;
  const box = await within(compare).findByRole("textbox", { name: "ask your library" });
  fireEvent.submit(box.closest("form")!);
  await settleDesk(0, 10);
  await waitFor(() => expect(inputsOf("reader_library_ask").length).toBe(1));
  return { desk, compare, bookWin, onCheckMe };
}

it("asks the library anchored on the passage it was opened on, and each hit shows its role", async () => {
  const { compare } = await openCompare();
  expect(inputsOf("reader_library_ask")[0]).toMatchObject({ query: "why exponentials", extractionId: book.extractionId, spanIds: [FIRST] });
  // A passage's role: its group, or the role LearnLoop's model proposed, labelled as the model's (RW4e).
  await waitFor(() => expect(compare.textContent).toContain("counterexample (model's label)"));
  expect(compare.textContent).toContain("foundation · 1 · p.1");
});

it("compares pinned passages by point and keeps the comparison: the book beside shows its ⇄ at once", async () => {
  const { compare, bookWin } = await openCompare();
  await waitFor(() => expect(within(compare).getAllByRole("button", { name: "pin" })).toHaveLength(2));
  for (const pin of within(compare).getAllByRole("button", { name: "pin" })) fireEvent.click(pin);
  fireEvent.click(within(compare).getByRole("button", { name: /compare pinned/ }));
  await settleDesk(0, 10);
  await waitFor(() => expect(compare.querySelector("[data-compare-table]")).toBeTruthy());
  expect(bookWin.querySelector(`[data-kept-mark="${FIRST}"]`)).toBeNull();
  fireEvent.click(within(compare).getByRole("button", { name: /keep comparison ⇄/ }));
  await settleDesk(0, 10);
  expect(inputsOf("reader_library_compare_keep")).toHaveLength(1);
  // The keep carries the comparison's own context: the question asked here and its passages.
  expect(inputsOf("reader_library_compare_keep")[0]).toMatchObject({ askId: "la_1" });
  await waitFor(() => expect(bookWin.querySelector(`[data-kept-mark="${FIRST}"]`)).toBeTruthy());
});

it("practice this ▸ hands the shell a pick in the asked book at the asked passage, and that book's window takes the focus", async () => {
  const onCheckMe = vi.fn();
  const { compare } = await openCompare(onCheckMe);
  await waitFor(() => expect(within(compare).getByRole("button", { name: /practice this question/ })).toBeTruthy());
  fireEvent.click(within(compare).getByRole("button", { name: /practice this question/ }));
  await settleDesk(0, 10);
  const pick = await within(compare).findByRole("button", { name: /practice this ▸/ });
  fireEvent.click(pick);
  await settleDesk(0, 6);
  expect(onCheckMe).toHaveBeenCalledWith(expect.objectContaining({
    practiceItemId: "pi_softmax", proposalId: "pp_1", spanId: FIRST, card: expect.objectContaining({ sourceId: book.sourceId }),
    reading: { sourceId: book.sourceId, revisionId: "rev_fx", extractionId: book.extractionId },
  }));
  await waitFor(() => expect(document.querySelector(".desk-window.focus [data-desk-window]")?.getAttribute("data-desk-window")).toBe("w_book"));
  // The book was already on the desk: focused there, never opened a second time.
  expect(document.querySelectorAll('[data-desk-window="w_book"]')).toHaveLength(1);
});
