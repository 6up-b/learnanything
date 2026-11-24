// A book still being prepared in a window of its own, and the stored windows of a retired kind restored to their
// workbench home (the Reader's retirement, phase 2 step 2), with real bodies: the desks over the fixture server, every
// Reader read through the app's api client to the fake sidecar.
import { cleanup, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { invoke as fixtureInvoke } from "../../../fixtures/desks/fakeCore";
import { answers, inputsOf, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_LIBRARY, FIXTURE_SOURCES } from "../../../fixtures/desks/sources";
import type { SourceLibraryCard } from "../../../api/dto";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => <div data-testid="original-pages" /> }));

const { book, paper } = FIXTURE_SOURCES;
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };

let library: SourceLibraryCard[];
const preparing = (card: SourceLibraryCard): SourceLibraryCard => ({
  ...card, readiness: "preparing" as SourceLibraryCard["readiness"], extractionStatus: "running",
  statusLine: { text: "Reading the pages · 3 of 12", tone: "working", action: null } as SourceLibraryCard["statusLine"],
});

beforeEach(() => {
  resetSidecar();
  library = FIXTURE_LIBRARY.map((card) => (card.sourceId === paper.sourceId ? preparing(card) : card));
  answers.set("get_source_library", () => ({ version: 1, sources: library }));
  answers.set("reader_pdf_view", () => ({ available: true, fileName: "paper.pdf", blocks: [] }));
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

// The desk's windows but its running pad's stack (the desks ensure one on a desk that has none).
const windowIds = () => Array.from(document.querySelectorAll<HTMLElement>("[data-desk-window]"))
  .filter((each) => !each.closest(".desk-window")?.querySelector("[data-pad-stack]"))
  .map((each) => each.getAttribute("data-desk-window"));
type Server = ReturnType<typeof mountRealDesk>["server"];
const storedWindows = (server: Server) => server.state().desks[0].slots
  .map((slot) => slot.windows.filter((each) => each.kind !== "pad_stack")).filter((slot) => slot.length > 0);
const focusedWindow = () => document.querySelector(".desk-window.focus [data-desk-window]")?.getAttribute("data-desk-window") ?? null;

it("a book still being prepared opens in a window of its own, with its original and its progress, and becomes the book's window when ready", async () => {
  vi.useFakeTimers({ toFake: ["setInterval", "clearInterval"] });
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never]]) });
  await settleDesk(0, 20);
  desk.rerender({ openRequest: { seq: 3, sourceId: paper.sourceId, spanId: null, reading: null } });
  await settleDesk(0, 12);
  // Its own window, focused: the original's pages and the status line, no reading yet, no "← Library" (closing the
  // window is the way out).
  await waitFor(() => expect(screen.getByRole("status").textContent).toContain("Reading the pages · 3 of 12"));
  const preparingWindow = focusedWindow();
  expect(document.querySelector(`[data-desk-window="${preparingWindow}"] [data-testid="original-pages"]`)).not.toBeNull();
  expect(screen.queryByText("← Library")).toBeNull();
  expect(preparingWindow).not.toBe("w_book");
  await waitFor(() => expect(storedWindows(desk.server).flat().find((each) => each.windowId === preparingWindow)?.content)
    .toEqual({ kind: "preparing", sourceId: paper.sourceId }), { timeout: 4000 });
  expect(document.querySelector(`[data-desk-window="${preparingWindow}"]`)?.textContent).not.toContain("extracted text");
  // Asked for again: the same window is focused, no second one.
  desk.rerender({ openRequest: { seq: 4, sourceId: paper.sourceId, spanId: null, reading: null } });
  await settleDesk(0, 8);
  expect(windowIds()).toHaveLength(2);

  // Ready: the book's window takes its place, focused, the original still on screen where the learner was (the
  // Reader's hand-over), with the way to the text; the preparing window is gone for good.
  library = FIXTURE_LIBRARY;
  vi.advanceTimersByTime(3000);
  vi.useRealTimers();
  await settleDesk(0, 20);
  await waitFor(() => expect(focusedWindow()).not.toBe(preparingWindow));
  const opened = focusedWindow();
  await waitFor(() => expect(document.querySelector(`[data-desk-window="${opened}"]`)?.textContent).toContain("extracted text →"));
  expect(document.querySelector(`[data-desk-window="${opened}"]`)?.textContent).not.toContain("Reading the pages");
  expect(opened).not.toBe(preparingWindow);
  expect(windowIds()).toEqual(expect.arrayContaining(["w_book", opened]));
  expect(windowIds()).toHaveLength(2);
  await waitFor(() => expect(storedWindows(desk.server).map((slot) => slot.map((each) => each.content)))
    .toEqual([[BOOK_WINDOW.content], [{ kind: "source", sourceId: paper.sourceId, extractionId: paper.extractionId, view: "render" }]]), { timeout: 4000 });
  expect(desk.errors).toEqual([]);
});

it("a stored reading-path panel restores as the book's own path, in the book's window when the desk has it", async () => {
  const pathPanel = { windowId: "w_path", pane: 0, kind: "panel", active: true, view: {}, content: { kind: "panel", panel: "path", extractionId: book.extractionId } };
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never], [pathPanel as never]]) });
  await settleDesk(0, 30);
  // The panel is gone; the book's window shows its path (the depth asked first).
  expect(windowIds()).toEqual(["w_book"]);
  await waitFor(() => expect(document.querySelector('[data-desk-window="w_book"]')?.textContent).toContain("How deep"));
  await waitFor(() => expect(storedWindows(desk.server).map((slot) => slot.map((each) => each.windowId))).toEqual([["w_book"]]), { timeout: 4000 });
  expect(desk.errors).toEqual([]);
});

it("a stored reading-path panel with no window of its book on the desk restores as that book's window, path open, in its place", async () => {
  const paperWindow = { ...BOOK_WINDOW, windowId: "w_paper", content: { kind: "source", sourceId: paper.sourceId, extractionId: paper.extractionId, view: "render" } };
  library = FIXTURE_LIBRARY;
  const pathPanel = { windowId: "w_path", pane: 0, kind: "panel", active: true, view: {}, content: { kind: "panel", panel: "path", extractionId: book.extractionId } };
  const desk = mountRealDesk({ state: oneDesk([[paperWindow as never], [pathPanel as never]]) });
  await settleDesk(0, 30);
  await waitFor(() => expect(storedWindows(desk.server).map((slot) => slot.map((each) => each.content))).toEqual([[paperWindow.content], [{ kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" }]]), { timeout: 4000 });
  // The book's source was asked of its reading (a panel named the reading alone).
  expect(inputsOf("reader_render_view").some((input) => input.extractionId === book.extractionId)).toBe(true);
  const restored = windowIds().find((id) => id !== "w_paper")!;
  await waitFor(() => expect(document.querySelector(`[data-desk-window="${restored}"]`)?.textContent).toContain("How deep"));
});

it("a window of a kind this version does not know is kept: the book's window when it names one, else shown inert and named", async () => {
  const unknown = { windowId: "w_future", pane: 0, kind: "whiteboard", active: true, view: {}, content: { kind: "whiteboard", boardId: "b1" } };
  const naming = { windowId: "w_scan", pane: 0, kind: "original_scan", active: true, view: {}, content: { kind: "original_scan", sourceId: paper.sourceId } };
  library = FIXTURE_LIBRARY;
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never], [unknown as never], [naming as never]]) });
  await settleDesk(0, 30);
  await waitFor(() => expect(storedWindows(desk.server).map((slot) => slot.map((each) => each.content)))
    .toEqual([[BOOK_WINDOW.content], [unknown.content], [{ kind: "source", sourceId: paper.sourceId, extractionId: paper.extractionId, view: "render" }]]), { timeout: 4000 });
  expect(document.querySelector('[data-desk-window="w_future"]')?.textContent).toContain("a whiteboard window");
  expect(document.querySelector(".desk-toast")?.textContent).toContain("Kept but not shown: a whiteboard window");
  expect(desk.errors).toEqual([]);
});

// Review fix round (major 20, ledger RDX-9): what each stored kind actually shows. A panel of a kind this version does
// not know is inert (never a live Library panel); a comparison named only by its id and a figure's notebook, which no
// body here opens by id, are inert and named, not an empty composer or a silent fallback.
it("a stored unknown panel, a kept comparison by id and a figure's notebook show inert and are named", async () => {
  const outline = { windowId: "w_outline", pane: 0, kind: "panel", active: true, view: {}, content: { kind: "panel", panel: "outline" } };
  const kept = { windowId: "w_kept", pane: 0, kind: "compare", active: true, view: {}, content: { kind: "compare", comparisonId: "cmp_1" } };
  const figure = { windowId: "w_fig", pane: 0, kind: "figure_notebook", active: true, view: {}, content: { kind: "figure_notebook", figureId: "fig_1" } };
  library = FIXTURE_LIBRARY;
  mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never], [outline as never], [kept as never], [figure as never]]) });
  await settleDesk(0, 30);
  await waitFor(() => expect(document.querySelector(".desk-toast")?.textContent).toContain("Kept but not shown"));
  const toast = document.querySelector(".desk-toast")?.textContent ?? "";
  for (const name of ["an outline window", "a kept comparison", "a figure's notebook"]) expect(toast).toContain(name);
  expect(document.querySelector('[data-desk-window="w_outline"]')?.textContent).toContain("an outline window");
  expect(document.querySelector('[data-desk-window="w_outline"] input')).toBeNull();
  expect(document.querySelector('[data-desk-window="w_kept"]')?.textContent).toContain("a kept comparison");
  expect(document.querySelector('[data-desk-window="w_kept"] input')).toBeNull();
  expect(document.querySelector('[data-desk-window="w_fig"]')?.textContent).toContain("a figure's notebook");
});

// Review fix round (major 16, ledger RDX-19): a path panel restored while the book's guide and settings are still being
// read keeps its request until the path shows; it used to be dropped on the first, refused, try.
it("a stored reading-path panel restored while the guide is still loading opens the path once it is there", async () => {
  let release: () => void = () => undefined;
  const gate = new Promise<void>((resolve) => { release = resolve; });
  for (const command of ["reader_prompt_contract", "reader_guide_plan"]) {
    answers.set(command, async (input) => {
      await gate;
      return fixtureInvoke(command, { input });
    });
  }
  const pathPanel = { windowId: "w_path", pane: 0, kind: "panel", active: true, view: {}, content: { kind: "panel", panel: "path", extractionId: book.extractionId } };
  mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never], [pathPanel as never]]) });
  await settleDesk(0, 30);
  release();
  await settleDesk(0, 30);
  await waitFor(() => expect(document.querySelector('[data-desk-window="w_book"]')?.textContent).toContain("How deep"));
});
