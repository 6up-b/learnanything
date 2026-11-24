// Exercises from my sources in a book window on a desk, with its real body (spec §21.1, "Exercises from my sources":
// "Exercise rows in book windows"; RW4b). The desks mount the Reader's source pane in the window; only the sidecar is
// faked:
//
// * "practice this question" in the window's library answer lists the textbook's exercise rows (candidate discovery);
// * "use this one" on an exercise of this book hands the shell the exercise and its book, and the window stays on it;
// * "use this one" on an exercise of another book hands it over and opens that book in a window beside (never in
//   place of this window's book), and the shell's queued exercise opens there, in that book's window only;
// * "open in the book" opens the other book beside, at the exercise.
import { cleanup, fireEvent, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { LibraryAskDto } from "../../../api/dto";
import { setAlgoConfig } from "../../../app/algoConfig";
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
const SECOND = `${book.extractionId}_s1_2`;
const PAPER_SPAN = `${paper.extractionId}_p1_1`;
const BOX = "What do you want to do with this?";
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };

const ASK: LibraryAskDto = {
  askId: "la_1", query: "softmax", entry: "where_else_explained", status: "ok", policy: "reading", personalized: true, basis: "keyword + meaning",
  learningObjectIds: [], extractionId: book.extractionId, anchorSpanIds: [FIRST],
  hits: [{ key: `${paper.extractionId}:${PAPER_SPAN}`, extractionId: paper.extractionId, spanId: PAPER_SPAN, sourceId: paper.sourceId, sourceTitle: "Attention",
    section: "1", page: 1, text: "Scores pass through a softmax.", role: "definition", group: "Foundation", expansion: null, learningObjectIds: [],
    authorship: "source", label: "source-authored" } as never],
  groups: { sources: [{ sourceId: paper.sourceId, sourceTitle: "Attention", groups: [{ group: "Foundation", keys: [`${paper.extractionId}:${PAPER_SPAN}`] }] }], expansions: [] },
  expansions: [], expandGraph: false, sourceCount: 1, passageCount: 1,
};

function exercise(key: string, sourceId: string, extractionId: string, span: string, statement: string) {
  return { kind: "source_exercise", key, extractionId, spanIds: [span], sourceId, revisionId: "rev", sourceTitle: sourceId === paper.sourceId ? "Attention" : "Softmax",
    label: "Exercise 1", page: 4, statement, rationale: null, labelLine: "From the book · not yet in your practice" };
}
const fresh = { exposed: false, reasons: [], label: null, note: null, offeredAs: "check_on_your_own", exposureRuleVersion: "reading_exposure_v1" };
const done = <T,>(result: T, kind: string) => ({ jobId: `ljob_${kind}`, kind, askId: "la_1", state: "done" as const, result });

beforeEach(() => {
  resetSidecar();
  setAlgoConfig({ workbench: { enabled: true } } as never);
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
  answers.set("reader_prompt_contract", () => ({
    version: "fixture", context: "reader", readerEnabled: true, notSocraticByDefault: true, defaultAnswerMode: "answer_directly",
    answerModes: ["answer_directly"], mayReveal: [], manifestIncludes: [], manifestNeverIncludes: [], citations: "spans",
    exposureOnCommit: "none", inquiryEnabled: true, intent: readerIntentContractFixture, activeReading: { foldBlocks: 3 },
    libraryAsk: { expandGraph: false, personalizedDefault: true, compare: true }, libraryExercises: { fallback: false },
  }));
  answers.set("reader_library_ask", () => done(ASK, "ask"));
  answers.set("reader_library_ask_notes", () => done({ askId: "la_1", status: "judged", notes: [], order: [] }, "notes"));
  answers.set("record_proposal_impressions", () => ({ recorded: 1 }));
  answers.set("reader_intent_outcome", () => ({ routingId: "r", recorded: true }));
  answers.set("find_practice", () => ({ version: 1, status: "ok", proposalId: "pp_1", items: [], sourceExercises: [
    exercise("srcex:here", book.sourceId, book.extractionId, SECOND, "Show the weights sum to one."),
    exercise("srcex:there", paper.sourceId, paper.extractionId, PAPER_SPAN, "Compute attention for two tokens."),
  ] }));
  answers.set("reader_exercise_candidates", () => done({ version: 1, proposalId: "pp_1", withheld: 0, candidates: [
    { key: "srcex:here", extractionId: book.extractionId, spanIds: [], sourceId: book.sourceId, revisionId: "rev", exposure: fresh },
    { key: "srcex:there", extractionId: paper.extractionId, spanIds: [], sourceId: paper.sourceId, revisionId: "rev", exposure: fresh },
  ] }, "exercise_candidates"));
  answers.set("workbench_open", () => new Promise(() => undefined));
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
  window.getSelection()?.removeAllRanges();
});

const winOf = (id: string) => document.querySelector<HTMLElement>(`[data-desk-window="${id}"]`)!;
/** The book windows on the desk, by the reading each holds (a pad stack is not one). */
const bookWindows = () => Array.from(document.querySelectorAll<HTMLElement>("[data-desk-window]"))
  .filter((each) => each.querySelector("[data-span-id]"))
  .map((each) => ({ id: each.getAttribute("data-desk-window"), spans: Array.from(each.querySelectorAll("[data-span-id]")).map((span) => span.getAttribute("data-span-id")) }));
const holding = (spanId: string) => bookWindows().filter((each) => each.spans.includes(spanId)).map((each) => each.id);

async function candidateRows(onUseExercise = vi.fn()) {
  const workbench = { practiceSessionId: "ps_1", onSubmitted: vi.fn() };
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never]]), props: { reader: { onUseExercise, workbench } } });
  await settleDesk(0, 20);
  const win = winOf("w_book");
  await waitFor(() => expect(win.querySelector(`[data-span-id="${FIRST}"]`)).toBeTruthy());
  const block = win.querySelector<HTMLElement>(`[data-span-id="${FIRST}"]`)!;
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
  const box = await within(win).findByRole("textbox", { name: BOX });
  fireEvent.keyDown(box, { key: "Tab" });
  const palette = await within(win).findByRole("group", { name: "what do you want to do?" });
  fireEvent.click(within(palette).getByRole("button", { name: "where else is this explained?" }));
  await settleDesk(0, 10);
  fireEvent.click(await within(win).findByRole("button", { name: /practice this question/ }));
  await settleDesk(0, 10);
  const cards = await within(win).findAllByTestId("exercise-candidate");
  return { desk, win, cards, onUseExercise, workbench };
}

it("lists the textbook's exercise rows in the book window, and use this one hands over an exercise of this book", async () => {
  const { cards, onUseExercise } = await candidateRows();
  expect(cards).toHaveLength(2);
  fireEvent.click(within(cards[0]).getByRole("button", { name: /use this one/ }));
  await settleDesk(0, 4);
  expect(onUseExercise).toHaveBeenLastCalledWith(expect.objectContaining({
    key: "srcex:here", entry: "practice_this", stemMd: "Show the weights sum to one.", sourceId: book.sourceId,
    sourceExercise: { proposalId: "pp_1", extractionId: book.extractionId, spanIds: [SECOND] },
    card: expect.objectContaining({ sourceId: book.sourceId }),
  }));
  // Its own book: no other book opens.
  expect(bookWindows().map((each) => each.id)).toEqual(["w_book"]);
});

it("use this one on another book's exercise opens that book beside, where the queued exercise opens (and only there)", async () => {
  const { desk, cards, onUseExercise, workbench, win } = await candidateRows();
  fireEvent.click(within(cards[1]).getByRole("button", { name: /use this one/ }));
  await settleDesk(0, 10);
  const request = onUseExercise.mock.calls[onUseExercise.mock.calls.length - 1][0];
  expect(request).toMatchObject({ key: "srcex:there", sourceId: paper.sourceId, card: expect.objectContaining({ sourceId: paper.sourceId }) });
  // A window of its own beside the book, which keeps its book.
  await waitFor(() => expect(holding(PAPER_SPAN)).toHaveLength(1));
  expect(holding(PAPER_SPAN)).not.toContain("w_book");
  expect(win.querySelector(`[data-span-id="${FIRST}"]`)).toBeTruthy();
  // The shell queues the exercise (as the app does on "use this one"): the paper's window opens it, the book's does not.
  desk.rerender({ reader: { onUseExercise, workbench: { ...workbench, exercise: request } } });
  await settleDesk(0, 20);
  await waitFor(() => expect(inputsOf("workbench_open")).toHaveLength(1));
  expect(inputsOf("workbench_open")[0]).toMatchObject({ entry: "practice_this", stemMd: "Compute attention for two tokens.",
    sourceExercise: expect.objectContaining({ proposalId: "pp_1", extractionId: paper.extractionId, spanIds: [PAPER_SPAN] }) });
});

it("open in the book opens another book's exercise beside", async () => {
  const { cards, win } = await candidateRows();
  fireEvent.click(within(cards[1]).getByRole("button", { name: /open in the book/ }));
  await settleDesk(0, 10);
  await waitFor(() => expect(holding(PAPER_SPAN)).toHaveLength(1));
  expect(holding(PAPER_SPAN)).not.toContain("w_book");
  expect(win.querySelector(`[data-span-id="${FIRST}"]`)).toBeTruthy();
});
