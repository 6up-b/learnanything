// Last time here, wrap up and the digest on a desk, with real bodies (spec §21.1 "the recap card in the source window
// on return; wrap up at the desk drain", §10.12): a desk shows no Guide rail unless a panel is opened for the book, so
// the recap card shows at the top of the book's window when the learner comes back, and is recorded as shown once,
// only there; `w` opens the session's Wrap up in the window; closing the desk's day (the drain) shows today's pads
// first, then each reading's Wrap up with its chips working.
import { cleanup, fireEvent, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setAlgoConfig } from "../../../app/algoConfig";
import { answers, inputsOf, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_SOURCES } from "../../../fixtures/desks/sources";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const { book } = FIXTURE_SOURCES;
const FIRST = `${book.extractionId}_s1_1`;
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };
const SESSION = { sessionId: "v1", extractionId: book.extractionId, visitIds: ["v1"], startedAt: "2026-11-22T20:00:00Z", endedAt: "2026-11-22T20:40:00Z", minutes: 40 };
const RECAP = {
  recapVersion: "rw6a-recap-v1", extractionId: book.extractionId, session: SESSION,
  continueAt: { sectionId: `${book.extractionId}_s2`, label: "2 Why the exponential" },
  stillOpen: [{ rootExchangeId: "r1", questionEventId: "q1", questionMd: "does the constant always cancel?", spanId: FIRST, anchorSpanIds: [FIRST], openedAt: "2026-11-22T20:05:00Z" }],
  unfinished: [], worthASecondLook: [], sinceLastTime: { demonstrated: [], checksRetired: [] },
};
const WRAP_UP = {
  version: 1, wrapUpVersion: "rw6a-wrap-up-v1", available: true, extractionId: book.extractionId, session: SESSION, resolved: [],
  stillOpen: [{ rootExchangeId: "r1", questionMd: "does the constant always cancel?", spanIds: [FIRST], actions: [
    { action: "resolve", rpc: "reader.set_inquiry_status", params: { resolution: "resolved", trigger: "chip" } },
    { action: "keep_open" },
  ] }],
  worthReinforcing: [],
};

beforeEach(() => {
  resetSidecar();
  setAlgoConfig({ recap: { enabled: true, wrapUpEnabled: true } });
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
  answers.set("reader_recap", () => ({ version: 1, recap: RECAP, dismissed: false }));
  answers.set("reader_recap_event", (input) => ({ version: 1, eventId: "ev", event: input.event }));
  answers.set("reader_wrap_up", () => WRAP_UP);
  answers.set("reader_set_inquiry_status", (input) => ({ exchangeId: input.exchangeId, resolution: input.resolution }));
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
});

const winEl = () => document.querySelector<HTMLElement>('[data-desk-window="w_book"]')!;
const shown = () => inputsOf("reader_recap_event").filter((input) => input.event === "recap_shown").length;

async function openBook() {
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never]]) });
  await settleDesk(0, 20);
  await waitFor(() => expect(winEl().querySelector(`[data-span-id="${FIRST}"]`)).toBeTruthy());
  return desk;
}

it("coming back to a book, the recap card shows at the top of its window and is recorded as shown once", async () => {
  await openBook();
  await waitFor(() => expect(winEl().querySelector("[data-recap-card]")).not.toBeNull());
  const card = winEl().querySelector<HTMLElement>("[data-recap-card]")!;
  expect(card.textContent).toContain("does the constant always cancel?");
  // Above the reading.
  expect(card.compareDocumentPosition(winEl().querySelector(`[data-span-id="${FIRST}"]`)!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  await waitFor(() => expect(shown()).toBe(1));
  await settleDesk(0, 4);
  expect(shown()).toBe(1);
});

it("w opens the session's Wrap up in the window", async () => {
  await openBook();
  await settleDesk(0, 4);
  fireEvent.keyDown(window, { key: "w" });
  const wrap = await waitFor(() => within(winEl()).getByRole("region", { name: "Wrap up" }));
  expect(wrap.textContent).toContain("does the constant always cancel?");
  expect(inputsOf("reader_recap_event").map((input) => input.event)).toContain("wrap_up_opened");
});

it("closing the desk's day shows today's pads first, then the reading's Wrap up, its chips working", async () => {
  await openBook();
  await settleDesk(0, 4);
  fireEvent.keyDown(window, { key: "Q", code: "KeyQ", altKey: true, shiftKey: true });
  await waitFor(() => expect(document.querySelector(".desk-drain")).not.toBeNull());
  const drain = document.querySelector<HTMLElement>(".desk-drain")!;
  const wrap = await waitFor(() => within(drain).getByRole("region", { name: "Wrap up" }));
  // The pads come before anything is asked.
  expect(drain.querySelector(".head")!.compareDocumentPosition(wrap) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  // It names its book.
  expect(wrap.closest("[data-drain-wrap-up]")?.textContent).toContain("Softmax, a short book");
  fireEvent.click(within(wrap).getByRole("button", { name: /resolve|understood|got it/i }));
  await settleDesk(0, 4);
  expect(inputsOf("reader_set_inquiry_status")).toEqual([expect.objectContaining({ exchangeId: "r1", resolution: "resolved" })]);
});
