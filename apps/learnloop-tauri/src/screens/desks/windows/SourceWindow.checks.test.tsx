// Quick checks in a source window on a desk, with real bodies (spec §21.1 "quick checks, authored questions: inside
// source windows"): a desk shows no Guide rail unless a panel is opened for the book, so a check the Guide would show
// first shows in the window under its section, and runs its whole round there: think it through, record the answer,
// and "Done with this check", after which what it showed stays, folded, where it was.
import { cleanup, fireEvent, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReaderGuidePlanDto } from "../../../api/dto";
import { answers, inputsOf, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_GUIDES, FIXTURE_SOURCES } from "../../../fixtures/desks/sources";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const { book } = FIXTURE_SOURCES;
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };
const PROMPT = "Before you read: what should weights from scores add up to?";

function guide(): ReaderGuidePlanDto {
  const base = FIXTURE_GUIDES[book.extractionId];
  return {
    ...base,
    sections: base.sections.map((section, index) => (index === 0 ? {
      ...section,
      question: { placement: "owner_reviewed", practiceItemId: "pi_weights", prompt: PROMPT, reason: "a question placed before this section", readingPhase: "before_section", placementEventId: "pe_1", learningObjectId: "lo_1" },
    } : section)),
  } as ReaderGuidePlanDto;
}

beforeEach(() => {
  resetSidecar();
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
  answers.set("reader_guide_plan", () => guide());
  answers.set("reader_present_question", () => ({ administrationId: "adm_1" }));
  answers.set("reader_submit_question", () => ({ eventId: "ev_1" }));
  answers.set("reader_mark_section_progress", () => ({ progress: { completedAt: null }, enqueuedGeneration: false, batchId: null }));
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const winEl = () => document.querySelector<HTMLElement>('[data-desk-window="w_book"]')!;

async function openBook() {
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never]]) });
  await settleDesk(0, 20);
  await waitFor(() => expect(winEl().querySelector(`[data-span-id="${book.extractionId}_s1_1"]`)).toBeTruthy());
  return desk;
}

it("a check the Guide would show first shows in the window under its section, and runs its round there", async () => {
  await openBook();
  await waitFor(() => expect(winEl().querySelector(`[data-quick-check="${book.extractionId}_s1"]`)).not.toBeNull());
  const card = winEl().querySelector<HTMLElement>(`[data-quick-check="${book.extractionId}_s1"]`)!;
  expect(card.textContent).toContain(PROMPT);
  // In its section: after the section's opening, before the next section.
  const nextHeading = winEl().querySelector(`[data-span-id="${book.extractionId}_s2_h"]`)!;
  expect(card.compareDocumentPosition(nextHeading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  fireEvent.click(within(card).getByRole("button", { name: /think it through/ }));
  await settleDesk(0, 3);
  expect(inputsOf("reader_present_question")).toEqual([expect.objectContaining({ practiceItemId: "pi_weights", readingPhase: "before_section" })]);
  fireEvent.change(within(card).getByPlaceholderText("Answer in your own words…"), { target: { value: "to one" } });
  fireEvent.click(within(card).getByRole("button", { name: /record answer/ }));
  await settleDesk(0, 3);
  expect(inputsOf("reader_submit_question")).toEqual([expect.objectContaining({ administrationId: "adm_1", response: "to one" })]);
  fireEvent.click(await within(card).findByRole("button", { name: "Done with this check" }));
  await settleDesk(0, 4);
  // What it showed stays, folded, in the window.
  await waitFor(() => expect(within(winEl()).getByTestId("closed-check")).toBeTruthy());
  expect(within(winEl()).getByTestId("closed-check").textContent).toContain("to one");
  expect(inputsOf("reader_mark_section_progress").some((input) => input.sectionId === `${book.extractionId}_s1`)).toBe(true);
});

it("an authored question offered before its section is answered and compared with the source in the window", async () => {
  const AUTHORED = {
    placement: "auto_authored", authoredQuestionId: "aq_1", prompt: "What do the weights from softmax add up to?",
    expectedAnswer: "One: each is positive and they are normalized by their sum.", reason: "A quick check.", spanIds: [`${book.extractionId}_s1_2`],
    readingPhase: "before_section",
  };
  answers.set("reader_guide_plan", () => {
    const base = FIXTURE_GUIDES[book.extractionId];
    return { ...base, sections: base.sections.map((section, index) => (index === 0 ? { ...section, question: AUTHORED } : section)) } as ReaderGuidePlanDto;
  });
  answers.set("reader_authored_question_action", () => ({}));
  await openBook();
  await waitFor(() => expect(winEl().querySelector(`[data-quick-check="${book.extractionId}_s1"]`)).not.toBeNull());
  const card = winEl().querySelector<HTMLElement>(`[data-quick-check="${book.extractionId}_s1"]`)!;
  fireEvent.click(within(card).getByRole("button", { name: /think it through/ }));
  fireEvent.change(within(card).getByPlaceholderText("Answer in your own words…"), { target: { value: "one" } });
  fireEvent.click(within(card).getByRole("button", { name: /compare with the source/ }));
  await settleDesk(0, 4);
  expect(within(card).getByText(AUTHORED.expectedAnswer)).toBeTruthy();
  expect(inputsOf("reader_authored_question_action")).toEqual([expect.objectContaining({ questionId: "aq_1", action: "answered", response: "one" })]);
});
