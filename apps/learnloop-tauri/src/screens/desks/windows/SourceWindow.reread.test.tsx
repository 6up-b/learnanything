// The Reader's retirement, review fix round (blocker 1, ledger RDX-6): a book's window names the reading it shows. A
// window saved on reading E1 of a book read again since (E2) rendered E2 by its source while every reader of the window
// (a cold check's protection, the companion, a pad link) took E1 from the saved reference: a check sent E1 with E2's
// passages, the server's lookup missed, and the passage could show unveiled. Restore names the current reading (the
// saved place translated onto it); a window whose Reader shows another reading than its reference names is put right;
// and a check names each book's window by the reading its page renders. Real desks over the fixture server.
import { cleanup, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { answers, inputsOf, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_SOURCES } from "../../../fixtures/desks/sources";
import { LIVE_DESK_TRANSPORT, renderedContent, type DeskTransport } from "../DeskShell";
import { FixtureDeskServer } from "../../../fixtures/desks/workspace";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const { book } = FIXTURE_SOURCES;
const OLD_READING = "fx_ext_softmax_before_reread";
const OLD_SPAN = "old_s1_2";
const NEW_SPAN = "fx_ext_softmax_s1_2";
const STALE_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: { spanId: OLD_SPAN },
  content: { kind: "source", sourceId: book.sourceId, extractionId: OLD_READING, view: "render" } };

type Server = ReturnType<typeof mountRealDesk>["server"];
const storedBooks = (server: Server) => server.state().desks[0].slots.flatMap((slot) => slot.windows)
  .filter((window) => window.kind === "source") as Array<{ windowId: string; view: Record<string, unknown>; content: { extractionId: string } }>;

beforeEach(() => {
  resetSidecar();
  answers.set("reader_saved_place", (input) => ({ version: 1, sourceId: book.sourceId, fromExtractionId: input.extractionId, fromSpanId: input.spanId,
    extractionId: book.extractionId, spanId: input.spanId === OLD_SPAN ? NEW_SPAN : null, status: input.spanId === OLD_SPAN ? "current" : "stale", matchKind: "alias" }));
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("a window saved on an earlier reading is restored naming the reading it shows, at its place translated onto it", async () => {
  const desk = mountRealDesk({ state: oneDesk([[STALE_WINDOW as never]]) });
  await settleDesk(0, 20);
  await waitFor(() => expect(storedBooks(desk.server).map((window) => window.content.extractionId)).toEqual([book.extractionId]));
  expect(storedBooks(desk.server)[0].view.spanId).toBe(NEW_SPAN);
  expect(inputsOf("reader_saved_place")[0]).toMatchObject({ spanId: OLD_SPAN, extractionId: OLD_READING, toExtractionId: book.extractionId });
  // Its page renders that reading, and says so where a check reads its passages.
  const shown = document.querySelector(`[data-desk-window="${storedBooks(desk.server)[0].windowId}"] [data-rendered-extraction]`);
  expect(shown?.getAttribute("data-rendered-extraction")).toBe(book.extractionId);
});

it("a window whose Reader shows another reading than its reference names is put right (restore could not tell)", async () => {
  // The restore's read of the current reading fails; the window mounts on the saved reference and its Reader opens the
  // book's current reading.
  const server = new FixtureDeskServer(oneDesk([[STALE_WINDOW as never]]));
  const transport: DeskTransport = {
    ...LIVE_DESK_TRANSPORT,
    state: async () => server.state(),
    apply: async (input) => server.apply(input as never),
    applyPad: async (input) => server.applyPad(input as never),
    padGet: async ({ padId }) => server.padGet(padId),
    resolveExtraction: async () => { throw new Error("busy"); },
  };
  mountRealDesk({ props: { transport } });
  await settleDesk(0, 30);
  await waitFor(() => expect(storedBooks(server as never).map((window) => window.content.extractionId)).toEqual([book.extractionId]));
});

it("a cold check names a book's window by the reading its page renders, never the reference's", () => {
  document.body.innerHTML = `<div data-desk-window="w1"><div data-rendered-extraction="E2"><p data-span-id="e2_s1">…</p></div></div>`;
  expect(renderedContent("w1", { kind: "source", extractionId: "E1" })).toEqual({ kind: "source", extractionId: "E2" });
  expect(renderedContent("w1", { kind: "pad" })).toEqual({ kind: "pad" });
  // A window not on the page (another desk) keeps its reference: its passages are not sent either.
  expect(renderedContent("w2", { kind: "source", extractionId: "E1" })).toEqual({ kind: "source", extractionId: "E1" });
});

// Major 7 (RDX-7): a return to an earlier reading's passage (a Today citation, feedback, the plan) lands at it on the
// reading the book has now, through the saved-place translation, for a new window and for one already open.
const EARLIER = "that passage was on an earlier reading of this book";
it("an open request for a passage of an earlier reading opens the book's new window at it, translated", async () => {
  const desk = mountRealDesk({ state: oneDesk([]) });
  await settleDesk(0, 12);
  desk.rerender({ openRequest: { seq: 4, sourceId: book.sourceId, spanId: OLD_SPAN, reading: OLD_READING } });
  await settleDesk(0, 20);
  await waitFor(() => expect(storedBooks(desk.server)).toHaveLength(1));
  expect(storedBooks(desk.server)[0]).toMatchObject({ content: { extractionId: book.extractionId }, view: { spanId: NEW_SPAN } });
  expect(document.body.textContent).not.toContain(EARLIER);
});

it("an open request for a passage of an earlier reading jumps the book's open window to it, translated", async () => {
  const current = { ...STALE_WINDOW, view: {}, content: { ...STALE_WINDOW.content, extractionId: book.extractionId } };
  const desk = mountRealDesk({ state: oneDesk([[current as never]]) });
  await settleDesk(0, 20);
  desk.rerender({ openRequest: { seq: 4, sourceId: book.sourceId, spanId: OLD_SPAN, reading: OLD_READING } });
  await settleDesk(0, 20);
  await waitFor(() => expect(inputsOf("reader_saved_place").some((input) => input.spanId === OLD_SPAN)).toBe(true));
  expect(document.body.textContent).not.toContain(EARLIER);
  expect(storedBooks(desk.server)).toHaveLength(1);
});
