// Cases of the standalone Reader's tests that need a source window on a desk, with real bodies, moved here when the
// standalone frame was retired (docs/reviews/reader-rd-retire.md, Phase 2 step 2); each names the case it came from.
// Only the sidecar is faked:
//
// * a book window whose reading is still loading says which book is opening, in one line, never a list of books, and
//   shows the reading once it lands (ReaderScreen.followsLearner.test.tsx, "opening a book shows that book opening,
//   not a second list of books").
import { cleanup, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { invoke as fixtureInvoke } from "../../../fixtures/desks/fakeCore";
import { answers, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_LIBRARY, FIXTURE_SOURCES } from "../../../fixtures/desks/sources";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const { book } = FIXTURE_SOURCES;
const FIRST = `${book.extractionId}_s1_1`;
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };
const TITLE = FIXTURE_LIBRARY.find((card) => card.sourceId === book.sourceId)!.title;

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

const winEl = () => document.querySelector<HTMLElement>('[data-desk-window="w_book"]')!;

// Moved from ReaderScreen.followsLearner.test.tsx, "opening a book shows that book opening, not a second list of books"
// (the standalone frame's opening view is the window's own opening line on the desks).
it("a book window still opening says which book, in one line, never a list of books, and then shows its reading", async () => {
  let release: () => void = () => undefined;
  const gate = new Promise<void>((resolve) => { release = resolve; });
  answers.set("reader_render_view", async (input) => {
    await gate;
    return fixtureInvoke("reader_render_view", { input });
  });
  mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never]]) });
  await settleDesk(0, 20);
  await waitFor(() => expect(winEl().textContent).toContain(`◐ Opening ${TITLE}…`));
  // No list of books, and no other book's name, while it opens.
  for (const card of FIXTURE_LIBRARY.filter((each) => each.sourceId !== book.sourceId)) expect(winEl().textContent).not.toContain(card.title);
  expect(winEl().textContent).not.toMatch(/Pick up where you left off|search all sources/);
  expect(winEl().querySelector(`[data-span-id="${FIRST}"]`)).toBeNull();
  release();
  await settleDesk(0, 20);
  await waitFor(() => expect(winEl().querySelector(`[data-span-id="${FIRST}"]`)).toBeTruthy());
  expect(winEl().textContent).not.toContain("◐ Opening");
});
