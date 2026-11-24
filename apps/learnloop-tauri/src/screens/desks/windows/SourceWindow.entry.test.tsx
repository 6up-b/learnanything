// The app's ways into the Reader while the desks are the Reader (the audit's entry points; spec §21.1), with real
// bodies: each asks the desks to open a book (the shelf, Today's threads and citations, a return from feedback) or to
// search (a lesson's "Look in my library"), and the desks do it on the desk in view, once per request, however many
// times they are shown again: a book already open is focused at the passage; another opens beside; a passage found
// on an earlier reading of the book is not opened as one of the reading the book now has.
import { cleanup, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_SOURCES } from "../../../fixtures/desks/sources";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const { book, paper } = FIXTURE_SOURCES;
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };

beforeEach(() => {
  resetSidecar();
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const windowsShowing = (sourceId: string) => Array.from(document.querySelectorAll<HTMLElement>("[data-desk-window]"))
  .filter((each) => each.querySelector(`[data-extraction-id]`)?.getAttribute("data-extraction-id") === Object.values(FIXTURE_SOURCES).find((s) => s.sourceId === sourceId)?.extractionId);
const focusedWindow = () => document.querySelector(".desk-window.focus [data-desk-window]")?.getAttribute("data-desk-window") ?? null;

it("a book asked for from outside opens beside on the desk in view, focused, and the same request is not repeated when the desks are shown again", async () => {
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never]]) });
  await settleDesk(0, 20);
  desk.rerender({ openRequest: { seq: 7, sourceId: paper.sourceId, spanId: `${paper.extractionId}_p1_2`, reading: null } });
  await settleDesk(0, 10);
  await waitFor(() => expect(windowsShowing(paper.sourceId).length).toBe(1));
  const opened = windowsShowing(paper.sourceId)[0].getAttribute("data-desk-window");
  expect(focusedWindow()).toBe(opened);
  // Shown again with the same request (the app's tab came back): nothing more opens.
  desk.rerender({ openRequest: { seq: 7, sourceId: paper.sourceId, spanId: `${paper.extractionId}_p1_2`, reading: null } });
  await settleDesk(0, 6);
  expect(windowsShowing(paper.sourceId).length).toBe(1);
});

it("a book already open is focused at the passage asked for", async () => {
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never]]) });
  await settleDesk(0, 20);
  (Element.prototype.scrollIntoView as ReturnType<typeof vi.fn>).mockClear();
  desk.rerender({ openRequest: { seq: 8, sourceId: book.sourceId, spanId: `${book.extractionId}_s3_2`, reading: null } });
  await settleDesk(0, 10);
  expect(windowsShowing(book.sourceId).length).toBe(1);
  expect(focusedWindow()).toBe("w_book");
  // The passage is the window's active one (its amber bar), where the reading now is.
  const passage = document.querySelector<HTMLElement>(`[data-desk-window="w_book"] [data-span-id="${book.extractionId}_s3_2"]`)!;
  await waitFor(() => expect(passage.style.borderLeft).toContain("var(--amber)"));
});

it("a lesson's Look in my library opens the desks' search with its words", async () => {
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never]]) });
  await settleDesk(0, 20);
  desk.rerender({ openRequest: { seq: 9, sourceId: null, spanId: null, reading: null, phrase: "temperature in softmax" } });
  await settleDesk(0, 6);
  await waitFor(() => expect(document.querySelector("[data-desk-search]")).not.toBeNull());
  expect((document.querySelector("[data-desk-search] input") as HTMLInputElement | null)?.value).toBe("temperature in softmax");
});
