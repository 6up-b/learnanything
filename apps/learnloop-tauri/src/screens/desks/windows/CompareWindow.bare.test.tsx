// A Compare window opened with no book open, on a desk with its real body: the desks' home of the old standalone
// Reader's library page (its list of books, where Shift+Enter in the search box asked the library). These cases
// moved here from the Reader's tests when the standalone frame was retired (docs/reviews/reader-rd-retire.md,
// Phase 2 step 2); each names the case it came from. Only the sidecar is faked:
//
// * the window asks across the library: no reading, no passages (libraryAsk.test.tsx, "Shift+Enter in the library
//   search asks your library instead of searching");
// * a practice proposal can be picked, at the answer's first passage (libraryAsk.test.tsx, "on the library page, a
//   practice proposal can be picked (F10)");
// * keep and reopen work there (compareKeep.test.tsx, "keep and reopen work on the library page with no book open
//   (F3)"), and its comparison offers the notes' your-take band, reading no book's marks (compareKeep.test.tsx, "C2:
//   the library page's comparison with no book open offers the notes' your-take band (F10)");
// * both exercise actions open the exercise's book (libraryExercisesReader.test.tsx, "on the library page both
//   exercise actions open the exercise's book (F1)").
import { cleanup, fireEvent, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { CompareTableDto, LibraryAskDto } from "../../../api/dto";
import { setAlgoConfig } from "../../../app/algoConfig";
import { answers, inputsOf, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_SOURCES } from "../../../fixtures/desks/sources";
import { readerIntentContractFixture } from "../../../fixtures/readerIntentContract";
import { KEEP_COPY } from "../../reader/CompareKeep";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const { book, paper } = FIXTURE_SOURCES;
const BOOK_SPAN = `${book.extractionId}_s2_1`;
const PAPER_SPAN = `${paper.extractionId}_p1_1`;
const PAPER_KEY = `${paper.extractionId}:${PAPER_SPAN}`;
const BOOK_KEY = `${book.extractionId}:${BOOK_SPAN}`;
// Opened bare: a question, no passage it was opened on, and no book window on the desk.
const COMPARE_WINDOW = { windowId: "w_compare", pane: 0, kind: "compare", active: true, view: {}, content: { kind: "compare", query: "why exponentials" } };
const NOTES = { enabled: true, meaning: false, pocketNotesLabel: "handwritten · transcribed by Pocket Notes", takePrefix: "From your note" };

function hit(key: string, sourceId: string, sourceTitle: string, text: string) {
  const [extractionId, spanId] = key.split(":");
  return { key, extractionId, spanId, sourceId, sourceTitle, section: "1", page: 1, text, role: "definition", group: "Foundation", expansion: null,
    learningObjectIds: [], authorship: "source" as const, label: "source-authored" };
}

const ASK: LibraryAskDto = {
  askId: "la_1", query: "why exponentials", entry: "library_search", status: "ok", policy: "reading", personalized: true, basis: "keyword + meaning",
  learningObjectIds: [], extractionId: null, anchorSpanIds: [],
  hits: [
    hit(PAPER_KEY, paper.sourceId, "Attention", "Scores pass through a softmax."),
    hit(BOOK_KEY, book.sourceId, "Softmax", "Differences in scores become ratios of weights."),
  ],
  groups: {
    sources: [
      { sourceId: paper.sourceId, sourceTitle: "Attention", groups: [{ group: "Foundation", keys: [PAPER_KEY] }] },
      { sourceId: book.sourceId, sourceTitle: "Softmax", groups: [{ group: "Foundation", keys: [BOOK_KEY] }] },
    ],
    expansions: [],
  },
  expansions: [], expandGraph: false, sourceCount: 2, passageCount: 2,
};

const TABLE: CompareTableDto = {
  askId: "la_1", status: "ok", comparisonId: "scmp_1", header: "differences kept · each line quotes its own source",
  rows: [
    { sourceId: paper.sourceId, sourceTitle: "Attention", key: PAPER_KEY, page: 1, isOpenSource: false,
      contributes: [{ line: "the mechanism", quote: "pass through a softmax", authorship: "ai" }], assumes: [], differs: [] },
    { sourceId: book.sourceId, sourceTitle: "Softmax", key: BOOK_KEY, page: 1, isOpenSource: false,
      contributes: [{ line: "the ratio view", quote: "ratios of weights", authorship: "ai" }], assumes: [], differs: [] },
  ],
  alsoDiscussedIn: [], unverifiedSources: [], droppedPins: [], droppedLineCount: 0, kept: null,
};

const kept = (askId: string) => ({
  askId, keptAt: "2026-10-03T09:00:00Z",
  objects: [{ id: "so_1", key: PAPER_KEY, objectType: "claim", sourceTitle: "Attention" }, { id: "so_2", key: BOOK_KEY, objectType: "definition", sourceTitle: "Softmax" }],
  relations: [{ id: "sor_1", relationType: "refines", fine: "different_assumptions" }],
  takes: [], notKept: 0, status: "proposed", label: "kept as proposals · nothing changes your map until you review them",
});

function exercise(key: string, sourceId: string, extractionId: string, span: string, statement: string) {
  return { kind: "source_exercise", key, extractionId, spanIds: [span], sourceId, revisionId: "rev", sourceTitle: "Attention",
    label: "Exercise 1", page: 4, statement, rationale: null, labelLine: "From the book · not yet in your practice" };
}
const fresh = { exposed: false, reasons: [], label: null, note: null, offeredAs: "check_on_your_own", exposureRuleVersion: "reading_exposure_v1" };
const done = <T,>(result: T, kind: string) => ({ jobId: `ljob_${kind}`, kind, askId: "la_1", state: "done" as const, result });
const contract = { extra: {} as Record<string, unknown> };

beforeEach(() => {
  resetSidecar();
  contract.extra = {};
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
  answers.set("reader_prompt_contract", () => ({
    version: "fixture", context: "reader", readerEnabled: true, notSocraticByDefault: true, defaultAnswerMode: "answer_directly",
    answerModes: ["answer_directly"], mayReveal: [], manifestIncludes: [], manifestNeverIncludes: [], citations: "spans",
    exposureOnCommit: "none", inquiryEnabled: true, intent: readerIntentContractFixture, activeReading: { foldBlocks: 3 },
    libraryAsk: { expandGraph: false, personalizedDefault: true, compare: true },
    compareKeep: { library: true, tutor: true, perspectives: true, maxPerspectives: 4 },
    ...contract.extra,
  }));
  answers.set("reader_library_ask", () => done(ASK, "ask"));
  answers.set("reader_library_ask_notes", () => done({ askId: "la_1", status: "judged", notes: [], order: [] }, "notes"));
  answers.set("reader_library_compare", () => done(TABLE, "compare"));
  answers.set("reader_kept_comparisons", (input) => ({ extractionId: input.extractionId, label: "a comparison you kept", marks: [] }));
  answers.set("record_proposal_impressions", () => ({ recorded: 1 }));
  answers.set("reader_intent_outcome", () => ({ routingId: "r", recorded: true }));
  answers.set("workbench_open", () => new Promise(() => undefined));
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
});

/** The book windows on the desk, by the reading each holds. */
const holding = (spanId: string) => Array.from(document.querySelectorAll<HTMLElement>("[data-desk-window]"))
  .filter((each) => each.querySelector(`[data-span-id="${spanId}"]`))
  .map((each) => each.getAttribute("data-desk-window"));

async function askBare(reader: Record<string, unknown> = {}) {
  const asked = inputsOf("reader_library_ask").length;
  const desk = mountRealDesk({ state: oneDesk([[COMPARE_WINDOW as never]]), props: { reader: reader as never } });
  await settleDesk(0, 20);
  const compare = document.querySelector<HTMLElement>('[data-desk-window="w_compare"]')!;
  const box = await within(compare).findByRole("textbox", { name: "ask your library" });
  fireEvent.submit(box.closest("form")!);
  await settleDesk(0, 10);
  await waitFor(() => expect(inputsOf("reader_library_ask").length).toBe(asked + 1));
  await within(compare).findByText("Scores pass through a softmax.");
  return { desk, compare };
}

async function compareBothPins(compare: HTMLElement) {
  await waitFor(() => expect(within(compare).getAllByRole("button", { name: "pin" })).toHaveLength(2));
  for (const pin of within(compare).getAllByRole("button", { name: "pin" })) fireEvent.click(pin);
  fireEvent.click(within(compare).getByRole("button", { name: /compare pinned \(2\)/ }));
  await settleDesk(0, 10);
}

// Moved from libraryAsk.test.tsx, "Shift+Enter in the library search asks your library instead of searching".
it("opened with no book open it asks across the library, on no reading and no passage", async () => {
  await askBare();
  expect(inputsOf("reader_library_ask")[0]).toMatchObject({ query: "why exponentials", entry: "library_search", extractionId: null, spanIds: [] });
});

// Moved from libraryAsk.test.tsx, "on the library page, a practice proposal can be picked (F10)".
it("with no book open a practice proposal can be picked, at the answer's first passage (F10)", async () => {
  answers.set("find_practice", () => ({ version: 1, status: "ok", proposalId: "pp_1", items: [
    { rank: 1, practiceItemId: "pi_1", learningObjectId: "lo_attn", learningObjectTitle: "Attention", practiceMode: "short_answer",
      prompt: "Why does attention average with softmax weights?", facetIds: [], rationale: null },
  ] }));
  const onCheckMe = vi.fn();
  const { compare } = await askBare({ onCheckMe });
  fireEvent.click(within(compare).getByRole("button", { name: /practice this question/ }));
  await settleDesk(0, 10);
  fireEvent.click(await within(compare).findByRole("button", { name: /practice this ▸/ }));
  await settleDesk(0, 10);
  // The learner pick, coming back to the answer's first passage.
  expect(onCheckMe).toHaveBeenCalledWith(expect.objectContaining({
    practiceItemId: "pi_1", proposalId: "pp_1", spanId: PAPER_SPAN, card: expect.objectContaining({ sourceId: paper.sourceId }),
  }));
});

// Moved from compareKeep.test.tsx, "keep and reopen work on the library page with no book open (F3)".
it("keep and reopen work in a Compare window with no book open (F3)", async () => {
  answers.set("reader_library_ask", () => done({ ...ASK, comparedOn: [{ askId: "la_0", keptAt: "2026-10-03T09:00:00Z", keys: [PAPER_KEY] }] }, "ask"));
  answers.set("reader_library_compare_reopen", () => ({ ...TABLE, askId: "la_0", kept: kept("la_0"), query: "softmax vs averaging" }));
  answers.set("reader_library_compare_keep", () => ({ askId: "la_1", alreadyKept: false, addedTakes: 0, kept: kept("la_1") }));
  const { compare } = await askBare();
  // "you compared these on …" reopens a table that can be removed.
  const line = await within(compare).findByText(/you compared these on 3 Oct/);
  fireEvent.click(within(line).getByRole("button", { name: KEEP_COPY.reopen }));
  await settleDesk(0, 10);
  await within(compare).findByText("“softmax vs averaging”");
  expect(within(compare).getByRole("button", { name: KEEP_COPY.remove })).toBeTruthy();
  // A new comparison here can be kept.
  await compareBothPins(compare);
  await waitFor(() => expect(within(compare).getAllByRole("table", { name: "how your sources treat this" }).length).toBeGreaterThan(1));
  fireEvent.click(within(compare).getByRole("button", { name: KEEP_COPY.keep }));
  await settleDesk(0, 10);
  expect(inputsOf("reader_library_compare_keep")).toHaveLength(1);
});

// Moved from compareKeep.test.tsx, "C2: the library page's comparison with no book open offers the notes' your-take band (F10)".
it("C2: a Compare window's comparison with no book open offers the notes' your-take band, reading no book's marks (F10)", async () => {
  contract.extra = { notes: NOTES };
  answers.set("notes_marks", (input) => ({ extractionId: input.extractionId, marks: [] }));
  answers.set("notes_passages", () => ({ notes: [{
    linkId: "nl_1", noteKey: "/n/a.org#Softmax", targetKind: "passage", learningObjectId: "lo", extractionId: paper.extractionId,
    sectionId: "sec", spanId: PAPER_SPAN, goalId: "g", authorship: "ai", byLabel: "linked by LearnLoop's model",
    how: "restates", howWords: null, howLine: null, line: "your note from 3 Oct",
    note: { title: "Attention", heading: "Softmax", capturedOn: "2026-10-03", dateLabel: "3 Oct", origin: "vault",
            originLabel: null, text: "Softmax weights sum to one.", truncated: false },
    takeText: "From your note “Attention › Softmax”, 3 Oct: “Softmax weights sum to one.”" }] }));
  const { compare } = await askBare();
  await compareBothPins(compare);
  await waitFor(() => expect(inputsOf("notes_passages").length).toBeGreaterThan(0));
  expect(await within(compare).findByText("Softmax weights sum to one.", { exact: false })).toBeTruthy();
  expect(within(compare).getAllByRole("button", { name: "use as my take" }).length).toBeGreaterThan(0);
  expect(inputsOf("notes_marks")).toHaveLength(0); // no book open: no reading's marks are read
});

// Moved from libraryExercisesReader.test.tsx, "on the library page both exercise actions open the exercise's book (F1)".
it("with no book open both exercise actions open the exercise's book (F1)", async () => {
  setAlgoConfig({ workbench: { enabled: true } } as never);
  contract.extra = { libraryExercises: { fallback: false } };
  answers.set("find_practice", () => ({ version: 1, status: "ok", proposalId: "pp_1", items: [], sourceExercises: [
    exercise("srcex:there", paper.sourceId, paper.extractionId, PAPER_SPAN, "Compute attention for two tokens."),
  ] }));
  answers.set("reader_exercise_candidates", () => done({ version: 1, proposalId: "pp_1", withheld: 0, candidates: [
    { key: "srcex:there", extractionId: paper.extractionId, spanIds: [], sourceId: paper.sourceId, revisionId: "rev", exposure: fresh },
  ] }, "exercise_candidates"));
  const onUseExercise = vi.fn();
  const workbench = { practiceSessionId: "ps_1", onSubmitted: vi.fn() };
  const candidate = async () => {
    const { desk, compare } = await askBare({ onUseExercise, workbench });
    fireEvent.click(within(compare).getByRole("button", { name: /practice this question/ }));
    await settleDesk(0, 10);
    return { desk, card: await within(compare).findByTestId("exercise-candidate") };
  };
  // "Open in the book": the exercise's own book opens at it, in a window beside.
  const first = await candidate();
  expect(holding(PAPER_SPAN)).toHaveLength(0);
  fireEvent.click(within(first.card).getByRole("button", { name: /open in the book/ }));
  await settleDesk(0, 10);
  await waitFor(() => expect(holding(PAPER_SPAN)).toHaveLength(1));
  expect(first.desk.errors).toEqual([]);
  cleanup();
  // "Use this one": the shell gets the exercise, and its book opens too.
  const second = await candidate();
  expect(holding(PAPER_SPAN)).toHaveLength(0);
  fireEvent.click(within(second.card).getByRole("button", { name: /use this one/ }));
  await settleDesk(0, 10);
  expect(onUseExercise).toHaveBeenCalledWith(expect.objectContaining({
    key: "srcex:there", sourceId: paper.sourceId, card: expect.objectContaining({ sourceId: paper.sourceId }),
  }));
  await waitFor(() => expect(holding(PAPER_SPAN)).toHaveLength(1));
  expect(second.desk.errors).toEqual([]);
});
