// The intent box over a selection in a source window on a desk, with real bodies (spec §7.1; §21.1 "intent box,
// active reading: inside source windows"): every routed action has a destination the learner sees without a Guide or
// Notes panel. An ask goes to the desk's companion, asked at once in the routed answer mode; an active-reading
// question shows under the passages it is about, in the window; "what matters here?" opens the reading's path.
import { cleanup, fireEvent, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { answers, inputsOf, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_SOURCES } from "../../../fixtures/desks/sources";
import { readerIntentContractFixture } from "../../../fixtures/readerIntentContract";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const { book } = FIXTURE_SOURCES;
const FIRST = `${book.extractionId}_s1_1`;
const BOX = "What do you want to do with this?";
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };

beforeEach(() => {
  resetSidecar();
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
  answers.set("reader_prompt_contract", () => ({
    version: "fixture", context: "reader", readerEnabled: true, notSocraticByDefault: true, defaultAnswerMode: "answer_directly",
    answerModes: ["answer_directly", "help_me_reason"], mayReveal: [], manifestIncludes: [], manifestNeverIncludes: [], citations: "spans",
    exposureOnCommit: "none", inquiryEnabled: true, intent: readerIntentContractFixture, activeReading: { foldBlocks: 2 },
    readingPaths: { enabled: true, depths: [] },
  }));
  answers.set("companion_ask", (input) => ({ version: 1, requestId: input.requestId, status: "running", done: false, partialMd: "", citations: [], streamedPieces: 0, questionEventId: null, sent: true, contextRecorded: null, kept: false, answer: null, error: null }));
  answers.set("reader_active_question", (input) => ({
    style: input.style, anchorSpanIds: input.spanIds, foldedSpanIds: [], status: "exists", batchId: null, message: null,
    question: {
      id: "aq1", extractionId: book.extractionId, sectionId: `${book.extractionId}_s1`, status: "proposed", questionMd: "What would the weights be for equal scores?",
      expectedAnswerMd: "Equal shares.", spanIds: input.spanIds, practiceItemId: null, answeredAt: null, scopeKind: "selection", questionStyle: input.style,
      anchorSpanIds: input.spanIds, responseMd: null, selfCheck: null, answerBasis: "model", escalationLearningObjectId: null, missed: false,
    },
  }));
  answers.set("reader_intent_outcome", () => ({ routingId: "r", recorded: true }));
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.getSelection()?.removeAllRanges();
});

const winEl = () => document.querySelector<HTMLElement>('[data-desk-window="w_book"]')!;
const blockIn = (spanId: string) => winEl().querySelector<HTMLElement>(`[data-span-id="${spanId}"]`)!;

async function openAndSelect() {
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never]]) });
  await settleDesk(0, 20);
  await waitFor(() => expect(blockIn(FIRST)).toBeTruthy());
  const range = document.createRange();
  range.selectNodeContents(blockIn(FIRST));
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(blockIn(FIRST));
  const box = await within(winEl()).findByRole("textbox", { name: BOX });
  return { desk, box: box as HTMLInputElement };
}

async function choose(box: HTMLInputElement, label: string, words = "") {
  if (words) fireEvent.change(box, { target: { value: words } });
  fireEvent.keyDown(box, { key: "Tab" });
  const palette = await within(winEl()).findByRole("group", { name: "what do you want to do?" });
  fireEvent.click(within(palette).getByRole("button", { name: label }));
  await settleDesk(0, 6);
}

it("a routed ask goes to the desk's companion, asked at once on the selection in the routed answer mode", async () => {
  const { box } = await openAndSelect();
  await choose(box, "ask · help me reason", "why are the weights positive?");
  expect(inputsOf("reader_ask")).toEqual([]);
  expect(inputsOf("companion_ask")).toEqual([expect.objectContaining({
    question: "why are the weights positive?", extractionId: book.extractionId, spanId: FIRST, selectionSpanIds: [FIRST], answerMode: "help_me_reason",
  })]);
  expect(document.querySelector('[aria-label="the companion"]')?.getAttribute("data-companion-mode")).not.toBe("hidden");
});

it("an active-reading question shows in the window, under the passages it is about, with no Notes panel", async () => {
  const { box } = await openAndSelect();
  await choose(box, "let me try the next step");
  expect(inputsOf("reader_active_question")[0]).toMatchObject({ extractionId: book.extractionId, spanIds: [FIRST], style: "next_step" });
  const card = await within(winEl()).findByRole("region", { name: "let me try the next step" });
  expect(card.textContent).toContain("What would the weights be for equal scores?");
  // Under its passage, before the next one.
  const passage = blockIn(FIRST);
  expect(passage.compareDocumentPosition(card) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  const next = winEl().querySelector<HTMLElement>(`[data-span-id="${book.extractionId}_s1_2"]`)!;
  expect(card.compareDocumentPosition(next) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  fireEvent.click(within(card).getByRole("button", { name: "close" }));
  await settleDesk(0, 2);
  expect(within(winEl()).queryByRole("region", { name: "let me try the next step" })).toBeNull();
});

it("“what matters here?” opens the reading's path on the desk", async () => {
  const { desk, box } = await openAndSelect();
  await choose(box, "what matters here?");
  await settleDesk(0, 6);
  // A window beside the book, its frame titled for the reading path.
  const opened = Array.from(document.querySelectorAll<HTMLElement>("[data-desk-window]")).filter((each) => each.getAttribute("data-desk-window") !== "w_book");
  expect(opened.map((each) => each.querySelector(".desk-pane-head")?.textContent ?? "")).toEqual(expect.arrayContaining([expect.stringContaining("Reading path")]));
  void desk;
});
