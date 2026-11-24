// Asking about a book on a desk, with real bodies (spec §8, §21.1 "the companion, branches kept; the detour strip and
// alt+← stay inside source windows"): the companion asks, and its answers act on the book's window as the old Ask
// rail's did. A claim of the open book peeks there, so the window's detour strip shows the way back and Alt+← walks
// it; a follow-up (a branch) joins the window's detours, and coming back to where the learner was asks "does this make
// sense now?" under that passage; "still unclear" asks again in the companion, branching from the question.
import { act, cleanup, fireEvent, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { answers, inputsOf, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_SOURCES, FIXTURE_VIEWS } from "../../../fixtures/desks/sources";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const { book } = FIXTURE_SOURCES;
const VIEW = FIXTURE_VIEWS[book.sourceId];
const FIRST = `${book.extractionId}_s1_1`;
const TEMPERATURE = `${book.extractionId}_s3_2`;
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };

const tutor = { asked: 0 };

beforeEach(() => {
  resetSidecar();
  tutor.asked = 0;
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
  // The tutor answers at once, citing the temperature passage; its exchange is the Reader's own (its id names it).
  const jobs = new Map<string, Record<string, unknown>>();
  answers.set("companion_ask", (input) => {
    tutor.asked += 1;
    jobs.set(String(input.requestId), { ...input, n: tutor.asked });
    return { version: 1, requestId: input.requestId, status: "running", done: false, partialMd: "", citations: [], streamedPieces: 0, questionEventId: null, sent: true, contextRecorded: null, kept: false, answer: null, error: null };
  });
  answers.set("companion_ask_job", (input) => {
    const job = jobs.get(String(input.requestId))!;
    const citations = [{ extractionId: book.extractionId, spanId: TEMPERATURE, label: "the temperature passage" }];
    return {
      version: 1, requestId: input.requestId, status: "done", done: true, partialMd: "An answer.", citations, streamedPieces: 1,
      questionEventId: `q_${job.n}`, sent: true, contextRecorded: true, kept: true, error: null,
      answer: {
        eventId: `ev_${job.n}`, readerAnswerEventId: `ans_${job.n}`, parentExchangeId: job.parentExchangeId ?? null,
        answerMd: `Answer ${job.n}.`, answerMode: "answer_directly", citations, manifest: {}, warmedSurfaceIds: [], burnedSurfaceIds: [], hintEquivalent: false, remaining: null,
      },
    };
  });
  answers.set("reader_restore_source", () => ({ ok: true }));
  answers.set("reader_reconnect_answer", (input) => ({ rootExchangeId: input.exchangeId, resolution: input.answer === "yes" ? "understood" : "open" }));
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.getSelection()?.removeAllRanges();
});

const winEl = () => document.querySelector<HTMLElement>('[data-desk-window="w_book"]')!;
const blockIn = (spanId: string) => winEl().querySelector<HTMLElement>(`[data-span-id="${spanId}"]`)!;

async function openBook() {
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never]]) });
  await settleDesk(0, 20);
  await waitFor(() => expect(blockIn(FIRST)).toBeTruthy());
  return desk;
}

/** Select a passage's words and ask the companion about them (c, then the question and ↵). */
async function askAbout(desk: ReturnType<typeof mountRealDesk>, question: string) {
  const host = blockIn(FIRST);
  const text = host.querySelector("p, div, span")?.firstChild ?? host.firstChild;
  const range = document.createRange();
  range.selectNodeContents(host);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(host);
  void text;
  const shown = document.querySelector('[aria-label="the companion"]');
  if (!shown || shown.getAttribute("data-companion-mode") === "hidden") fireEvent.keyDown(window, { key: "c" });
  const box = await waitFor(() => document.querySelector<HTMLTextAreaElement>('[aria-label="ask about this"]')!);
  fireEvent.change(box, { target: { value: question } });
  fireEvent.keyDown(box, { key: "Enter" });
  await settleDesk(0, 4);
  await act(async () => {
    await desk.poller.tick();
  });
  await settleDesk(0, 4);
}

it("a claim of the open book peeks in its window: the strip shows the way back, and Alt+← walks it", async () => {
  const desk = await openBook();
  await askAbout(desk, "why the exponential?");
  const claim = await waitFor(() => Array.from(document.querySelectorAll<HTMLButtonElement>("button.claim")).find((button) => button.textContent?.includes("the temperature passage"))!);
  fireEvent.click(claim);
  await settleDesk(0, 4);
  const strip = within(winEl()).getByRole("navigation", { name: "Detour" });
  expect(strip.textContent).toContain("Scores into weights");
  fireEvent.keyDown(window, { key: "ArrowLeft", altKey: true });
  await settleDesk(0, 4);
  expect(inputsOf("reader_restore_source")).toEqual([{ extractionId: book.extractionId, spanId: FIRST }]);
});

it("a follow-up joins the window's detours, and coming back asks “does this make sense now?” under where the learner was", async () => {
  const desk = await openBook();
  await askAbout(desk, "why the exponential?");
  await askAbout(desk, "and with another base?");
  expect(inputsOf("companion_ask").map((input) => input.parentExchangeId)).toEqual([null, "ans_1"]);
  const strip = within(winEl()).getByRole("navigation", { name: "Detour" });
  expect(strip.textContent).toContain("why the exponential?");
  expect(strip.textContent).toContain("and with another base?");
  fireEvent.keyDown(window, { key: "ArrowLeft", altKey: true });
  fireEvent.keyDown(window, { key: "ArrowLeft", altKey: true });
  await settleDesk(0, 4);
  const line = await waitFor(() => within(winEl()).getByRole("group", { name: "Does this make sense now?" }));
  expect(line.getAttribute("data-reconnect")).toBe("inline");
  fireEvent.click(within(line).getByRole("button", { name: "yes" }));
  await settleDesk(0, 3);
  expect(inputsOf("reader_reconnect_answer")).toEqual([expect.objectContaining({ exchangeId: "ans_1", answer: "yes", via: "inline" })]);
});

it("“still unclear” with words asks again in the companion, branching from the question", async () => {
  const desk = await openBook();
  await askAbout(desk, "why the exponential?");
  await askAbout(desk, "and with another base?");
  fireEvent.keyDown(window, { key: "ArrowLeft", altKey: true });
  fireEvent.keyDown(window, { key: "ArrowLeft", altKey: true });
  await settleDesk(0, 4);
  const line = await waitFor(() => within(winEl()).getByRole("group", { name: "Does this make sense now?" }));
  fireEvent.click(within(line).getByRole("button", { name: /still unclear/ }));
  fireEvent.change(within(line).getByRole("textbox", { name: "What's still unclear?" }), { target: { value: "the ratio part" } });
  fireEvent.click(within(line).getByRole("button", { name: "ask this ^↵" }));
  await settleDesk(0, 4);
  expect(inputsOf("companion_ask").slice(-1)[0]).toMatchObject({ question: "the ratio part", parentExchangeId: "ans_1", extractionId: book.extractionId });
  void VIEW;
});

it("the palette's Ask while the desks are the Reader summons the companion on the reading in view, never toggling it away", async () => {
  const desk = await openBook();
  expect(document.querySelector('[aria-label="the companion"]')?.getAttribute("data-companion-mode") ?? "hidden").toBe("hidden");
  desk.rerender({ askRequest: 1 });
  await settleDesk(0, 3);
  const companion = document.querySelector('[aria-label="the companion"]')!;
  expect(companion.getAttribute("data-companion-mode")).not.toBe("hidden");
  // Asked again, it stays.
  desk.rerender({ askRequest: 2 });
  await settleDesk(0, 3);
  expect(document.querySelector('[aria-label="the companion"]')?.getAttribute("data-companion-mode")).not.toBe("hidden");
});

// The Reader's retirement, review fix round (major 13, ledger RDX-18): a book alone on its desk has no rail on screen;
// "quick check" on the inline reconnect used to start a check whose question, answer and cancel lived only in the Ask
// rail. It is asked and answered under the passage now.
it("RDX-18: a quick check chosen on the inline reconnect is asked and answered under the passage, with no rail on screen", async () => {
  answers.set("reader_reconnect_answer", (input) => (input.answer === "quick_check"
    ? { rootExchangeId: input.exchangeId, resolution: "open", status: "ready", batchId: null,
      question: { id: "iq_1", extractionId: book.extractionId, sectionId: "s1", status: "proposed", questionMd: "Why does the exponential keep the order?",
        expectedAnswerMd: "It is increasing.", spanIds: [TEMPERATURE], practiceItemId: null, answeredAt: null, scopeKind: "inquiry" } }
    : { rootExchangeId: input.exchangeId, resolution: "open" }));
  const desk = await openBook();
  await askAbout(desk, "why the exponential?");
  await askAbout(desk, "and with another base?");
  fireEvent.keyDown(window, { key: "ArrowLeft", altKey: true });
  fireEvent.keyDown(window, { key: "ArrowLeft", altKey: true });
  await settleDesk(0, 4);
  const line = await waitFor(() => within(winEl()).getByRole("group", { name: "Does this make sense now?" }));
  fireEvent.click(within(line).getByRole("button", { name: /quick check/ }));
  await settleDesk(0, 6);
  expect(inputsOf("reader_reconnect_answer")).toEqual([expect.objectContaining({ answer: "quick_check" })]);
  await waitFor(() => expect(winEl().textContent).toContain("Why does the exponential keep the order?"));
});
