// The tutor that looks things up, through the desks' companion (spec §8; §21.1 "the companion, retrieval_intent
// unchanged; existing tests through companion.ask"), with real bodies: an answer that looked in the learner's books
// shows its verbatim excerpt (opening the passage), its bridge and its abstention line; "another way" and "that didn't
// help…" ask again from that answer with the alternative and remediate intents; the personalized chip is sent with
// every ask while retrieval is on. With the tutor's switches off, none of it shows and nothing extra is sent.
import { act, cleanup, fireEvent, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { answers, inputsOf, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_SOURCES } from "../../../fixtures/desks/sources";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const { book } = FIXTURE_SOURCES;
const FIRST = `${book.extractionId}_s1_1`;
const TEMPERATURE = `${book.extractionId}_s3_1`;
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };

const tutor = { retrieval: true, abstained: false };

function view() {
  return {
    modes: tutor.abstained ? ["grounded"] : ["excerpt", "grounded", "bridge"],
    excerpt: tutor.abstained ? null : { extractionId: book.extractionId, spanId: TEMPERATURE, quote: "Dividing every score by a temperature", label: "Softmax, a short book · 3 Temperature", relation: null, sourceId: book.sourceId },
    bridgeMd: tutor.abstained ? null : "This is the scaling you worked on yesterday.",
    abstained: tutor.abstained, abstentionLine: tutor.abstained ? "Your books don't treat this; this is LearnLoop's own explanation." : null,
    droppedExcerpt: null, droppedBridge: null, intent: "explain", personalized: true, retrieval: {},
  };
}

beforeEach(() => {
  resetSidecar();
  tutor.retrieval = true;
  tutor.abstained = false;
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
  answers.set("reader_prompt_contract", () => ({
    version: "fixture", context: "reader", readerEnabled: true, notSocraticByDefault: true, defaultAnswerMode: "answer_directly",
    answerModes: ["answer_directly"], mayReveal: [], manifestIncludes: [], manifestNeverIncludes: [], citations: "spans",
    exposureOnCommit: "none", inquiryEnabled: true,
    ...(tutor.retrieval ? { readerTutor: { retrieval: true, offers: false, anotherWay: true, personalizedDefault: true, tryNextStep: false, manifestIncludes: [] } } : {}),
  }));
  const jobs = new Map<string, number>();
  answers.set("companion_ask", (input) => {
    jobs.set(String(input.requestId), jobs.size + 1);
    return { version: 1, requestId: input.requestId, status: "running", done: false, partialMd: "", citations: [], streamedPieces: 0, questionEventId: null, sent: true, contextRecorded: null, kept: false, answer: null, error: null };
  });
  answers.set("companion_ask_job", (input) => {
    const n = jobs.get(String(input.requestId)) ?? 0;
    return {
      version: 1, requestId: input.requestId, status: "done", done: true, partialMd: "An answer.", citations: [], streamedPieces: 1,
      questionEventId: `q_${n}`, sent: true, contextRecorded: true, kept: true, error: null,
      answer: {
        eventId: `ev_${n}`, readerAnswerEventId: `ans_${n}`, answerMd: `Answer ${n}.`, answerMode: "answer_directly", citations: [], manifest: {},
        warmedSurfaceIds: [], burnedSurfaceIds: [], hintEquivalent: false, remaining: null, ...(tutor.retrieval ? { tutor: view() } : {}),
      },
    };
  });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.getSelection()?.removeAllRanges();
});

const companionEl = () => document.querySelector<HTMLElement>('[aria-label="the companion"]')!;

async function openAndAsk(question: string) {
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never]]) });
  await settleDesk(0, 20);
  const host = await waitFor(() => document.querySelector<HTMLElement>(`[data-desk-window="w_book"] [data-span-id="${FIRST}"]`)!);
  const range = document.createRange();
  range.selectNodeContents(host);
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(host);
  fireEvent.keyDown(window, { key: "c" });
  await ask(desk, question);
  return desk;
}

async function ask(desk: ReturnType<typeof mountRealDesk>, question: string) {
  const box = await waitFor(() => document.querySelector<HTMLTextAreaElement>('[aria-label="ask about this"]')!);
  fireEvent.change(box, { target: { value: question } });
  fireEvent.keyDown(box, { key: "Enter" });
  await poll(desk);
}

async function poll(desk: ReturnType<typeof mountRealDesk>) {
  await settleDesk(0, 4);
  await act(async () => {
    await desk.poller.tick();
  });
  await settleDesk(0, 4);
}

it("an answer that looked in the books shows the excerpt, which opens its passage, and the bridge", async () => {
  await openAndAsk("why divide by a temperature?");
  const answer = await waitFor(() => companionEl().querySelector<HTMLElement>('[data-exchange-status="answered"]')!);
  const excerpt = within(answer).getByText("Dividing every score by a temperature");
  expect(excerpt.closest("[data-excerpt]")).not.toBeNull();
  expect(answer.textContent).toContain("from your books");
  expect(answer.textContent).toContain("This is the scaling you worked on yesterday.");
  fireEvent.click(within(answer).getByRole("button", { name: /open in your book/ }));
  await settleDesk(0, 3);
  // The excerpt's passage is in the book's window already: a peek there, its strip the way back.
  expect(within(document.querySelector<HTMLElement>('[data-desk-window="w_book"]')!).getByRole("navigation", { name: "Detour" })).toBeTruthy();
});

it("another way and that didn't help… ask again from the answer, with the alternative and remediate intents", async () => {
  const desk = await openAndAsk("why divide by a temperature?");
  const answer = await waitFor(() => companionEl().querySelector<HTMLElement>('[data-exchange-status="answered"]')!);
  fireEvent.click(within(answer).getByRole("button", { name: "another way" }));
  await poll(desk);
  expect(inputsOf("companion_ask")[1]).toMatchObject({ question: "Explain it another way", parentExchangeId: "ans_1", retrievalIntent: "alternative", extractionId: book.extractionId });
  // On the passage the answer was about.
  expect(inputsOf("companion_ask")[1].spanId).toBe(inputsOf("companion_ask")[0].spanId);
  const second = companionEl().querySelectorAll<HTMLElement>('[data-exchange-status="answered"]')[1];
  fireEvent.click(within(second).getByRole("button", { name: "that didn't help…" }));
  fireEvent.change(within(second).getByPlaceholderText("optional: what's still unclear…"), { target: { value: "the ratio, not the scale" } });
  fireEvent.click(within(second).getByRole("button", { name: /ask again/ }));
  await poll(desk);
  expect(inputsOf("companion_ask")[2]).toMatchObject({ question: "the ratio, not the scale", parentExchangeId: "ans_2", retrievalIntent: "remediate" });
});

it("an answer that found nothing in the books says so", async () => {
  tutor.abstained = true;
  await openAndAsk("what is a tensor?");
  const answer = await waitFor(() => companionEl().querySelector<HTMLElement>('[data-exchange-status="answered"]')!);
  expect(answer.textContent).toContain("Your books don't treat this; this is LearnLoop's own explanation.");
  expect(answer.querySelector("[data-excerpt]")).toBeNull();
});

it("the personalized chip goes with every ask while the tutor looks things up, and the learner can switch it", async () => {
  const desk = await openAndAsk("first");
  const chip = within(companionEl()).getByRole("button", { name: "personalized ●" });
  expect(chip.getAttribute("aria-pressed")).toBe("true");
  expect(inputsOf("companion_ask")[0]).toMatchObject({ personalized: true });
  fireEvent.click(chip);
  expect(within(companionEl()).getByRole("button", { name: "personalized ○" }).getAttribute("aria-pressed")).toBe("false");
  await ask(desk, "second");
  expect(inputsOf("companion_ask")[1]).toMatchObject({ personalized: false });
});

it("with the tutor's retrieval off: no chip, no excerpt or controls, and nothing extra sent", async () => {
  tutor.retrieval = false;
  await openAndAsk("why divide by a temperature?");
  const answer = await waitFor(() => companionEl().querySelector<HTMLElement>('[data-exchange-status="answered"]')!);
  expect(within(companionEl()).queryByRole("button", { name: /personalized/ })).toBeNull();
  expect(within(answer).queryByRole("button", { name: "another way" })).toBeNull();
  expect(inputsOf("companion_ask")[0]).not.toHaveProperty("personalized");
  expect(inputsOf("companion_ask")[0]).not.toHaveProperty("retrievalIntent");
});
