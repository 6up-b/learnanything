// The learner's own question from a passage on a desk (row "quick checks, authored questions"; an orchestrator default
// the owner may change): Make it practice's sheet offers "write it myself" beside the model's draft, and taking it
// opens the Reader's own question card under the passage in its window, where the question and the learner's answer
// are saved for practice as the Notes rail saved them (reader.author_qa, on that passage); nothing is drafted.
import { cleanup, fireEvent, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { answers, inputsOf, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_SOURCES } from "../../../fixtures/desks/sources";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const { book } = FIXTURE_SOURCES;
const SECOND = `${book.extractionId}_s1_2`;
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };

beforeEach(() => {
  resetSidecar();
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
  answers.set("passage_knows", (input) => ({ version: 1, objectKey: "k", sourceIds: [book.sourceId], places: [{
    extractionId: book.extractionId, spanId: input.spanId, role: "prose",
    knows: { spanId: input.spanId, sectionId: `${book.extractionId}_s1`, annotations: [], padBlocks: [], exchanges: [], adjustments: [], gaps: [], passageLinks: [], figures: [],
      checksDue: [], notes: [], authoredQuestions: [], carried: [], exposure: { timesShown: 1, lastShownAt: null, withheld: false } },
  }] }));
  answers.set("reader_author_qa", () => ({ cardId: "card_1", practiceStatus: "scheduled" }));
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const winEl = () => document.querySelector<HTMLElement>('[data-desk-window="w_book"]')!;

it("write it myself opens the passage's own question card in its window, and saves the learner's question and answer", async () => {
  mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never]]) });
  await settleDesk(0, 20);
  const passage = await waitFor(() => winEl().querySelector<HTMLElement>(`[data-span-id="${SECOND}"]`)!);
  fireEvent.mouseDown(passage);
  fireEvent.contextMenu(passage, { clientX: 400, clientY: 300 });
  await settleDesk(0, 4);
  fireEvent.keyDown(window, { key: "p" });
  await settleDesk(0, 4);
  const sheet = await waitFor(() => document.querySelector<HTMLElement>('[role="dialog"].desk-sheet')!);
  fireEvent.click(sheet.querySelector<HTMLButtonElement>('[data-sheet-choice="mine"]')!);
  await settleDesk(0, 4);
  expect(inputsOf("reader_author_section_question")).toEqual([]);
  const card = await within(winEl()).findByRole("group", { name: "your own question" });
  // Under the passage it is about.
  expect(passage.compareDocumentPosition(card) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  const [question, answer] = within(card).getAllByRole("textbox");
  fireEvent.change(question, { target: { value: "Why are softmax weights positive?" } });
  fireEvent.change(answer, { target: { value: "Because the exponential is positive." } });
  fireEvent.click(within(card).getByRole("button", { name: /save for practice/ }));
  await settleDesk(0, 4);
  expect(inputsOf("reader_author_qa")).toEqual([expect.objectContaining({
    question: "Why are softmax weights positive?", answer: "Because the exponential is positive.", sourceId: book.sourceId,
    subjectId: `span:${book.extractionId}/${SECOND}`,
  })]);
});
