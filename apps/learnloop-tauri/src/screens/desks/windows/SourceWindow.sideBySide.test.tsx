// Side by side on a desk, with real bodies (spec §21.1, "Side by side": "Two windows in view, or a pair (§5.2)";
// "Side-by-side tests adapted to two windows"). The v1 Reader's second pane is not rebuilt: the other book opens in
// a window paired with the first, and the desk hosts what the pane did between the two. Only the sidecar is faked:
//
// * Ctrl+\ (the first-correspondent shortcut) opens the section's first judged correspondent in a window paired with
//   the book (one slot, two panes); the book keeps its own place;
// * follow along: the book crossing into a new section moves its pair, once, to that book's first judged
//   correspondent; the moved window does not answer back; Ctrl+Shift+L turns following off for the pair;
// * F6 moves the focus to the other window of the pair;
// * each window acts on its own book: a highlight made in the paired window is that book's (second-pane targeting).
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

const { book, paper } = FIXTURE_SOURCES;
const BOOK_S2_FIRST = `${book.extractionId}_s2_1`;
const BOX = "What do you want to do with this?";
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };

/** The book's sections and the paper's judged correspondent for each. */
const CORRESPONDENT: Record<string, string> = { [`${book.extractionId}_s1`]: "p1", [`${book.extractionId}_s2`]: "p2", [`${book.extractionId}_s3`]: "p3" };
/** Sections whose correspondents answer only when the test releases them (a slow answer). */
const held = new Map<string, () => void>();


beforeEach(() => {
  resetSidecar();
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
  answers.set("reader_prompt_contract", () => ({
    version: "fixture", context: "reader", readerEnabled: true, notSocraticByDefault: true, defaultAnswerMode: "answer_directly",
    answerModes: ["answer_directly"], mayReveal: [], manifestIncludes: [], manifestNeverIncludes: [], citations: "spans",
    exposureOnCommit: "none", inquiryEnabled: true, intent: readerIntentContractFixture, activeReading: { foldBlocks: 3 },
    sideBySide: { enabled: true },
  }));
  held.clear();
  answers.set("reader_correspondents", async (input) => {
    if (held.has(String(input.sectionId))) await new Promise<void>((release) => held.set(String(input.sectionId), release));
    const section = CORRESPONDENT[String(input.sectionId)];
    const sections = section ? [{
      extractionId: paper.extractionId, sectionId: `${paper.extractionId}_${section}`, title: `${section} Attention`, sourceId: paper.sourceId,
      sourceTitle: "Attention", read: false, jump: { extractionId: paper.extractionId, sectionId: `${paper.extractionId}_${section}`, spanId: `${paper.extractionId}_${section}_1` },
      treatment: "explains", by: "judge",
    }] : [];
    return { extractionId: input.extractionId, sectionId: input.sectionId, status: sections.length ? "judged" : "none", search: null, checkableLearningObjectIds: [],
      learningObjects: sections.length ? [{ learningObjectId: "lo_softmax", title: "Softmax", sources: [{ sourceId: paper.sourceId, sourceTitle: "Attention", sections }] }] : [] };
  });
  answers.set("reader_capture", () => ({ annotationId: "ann_1", outboxId: "o1", interactionEventId: "e1", anchorStatus: "exact", captureKind: "annotation", deduplicated: false, receipt: "saved" }));
  answers.set("reader_intent_outcome", () => ({ routingId: "r", recorded: true }));
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.getSelection()?.removeAllRanges();
});

const winOf = (id: string) => document.querySelector<HTMLElement>(`[data-desk-window="${id}"]`);
const slotOf = (el: Element) => el.closest("[data-desk-slot]")?.getAttribute("data-desk-slot")?.split(":") ?? [];
const focusedWindow = () => document.querySelector(".desk-window.focus [data-desk-window]")?.getAttribute("data-desk-window");
/** The window holding the paper (its passages rendered). */
const paperWindow = () => Array.from(document.querySelectorAll<HTMLElement>("[data-desk-window]"))
  .find((each) => each.querySelector(`[data-span-id^="${paper.extractionId}_"]`)) ?? null;
/** Side by side's own asks (Ctrl+\'s with the search fallback, following's without); other surfaces ask too. */
const correspondentsAsked = () => inputsOf("reader_correspondents").filter((input) => String(input.sectionId).startsWith(`${String(input.extractionId)}_`))
  .map((input) => `${input.sectionId}${input.searchFallback ? " (search)" : ""}`);
/** The section a window's frame says it is in. */
const headOf = (win: Element) => win.closest(".desk-window")?.querySelector(".desk-pane-head")?.textContent ?? "";

/** The learner scrolls a window's reading until `spanId` is under the reading marker (jsdom lays nothing out: the
 * passages' boxes are given), once the opening jump's settle time has passed (a jump is not reading). */
async function scrollTo(win: HTMLElement, spanId: string) {
  await new Promise((resolve) => setTimeout(resolve, 1600));
  const scroller = win.querySelector<HTMLElement>(`[data-span-id="${spanId}"]`)!.closest<HTMLElement>(".ll-scroll")!;
  scroller.getBoundingClientRect = () => ({ top: 0, bottom: 800, left: 0, right: 600, height: 800, width: 600, x: 0, y: 0, toJSON: () => ({}) }) as DOMRect;
  for (const block of Array.from(scroller.querySelectorAll<HTMLElement>("[data-span-id]"))) {
    const shown = block.getAttribute("data-span-id") === spanId;
    block.getBoundingClientRect = () => ({ top: shown ? 300 : -2000, bottom: shown ? 340 : -1960, left: 0, right: 600, height: 40, width: 600,
      x: 0, y: shown ? 300 : -2000, toJSON: () => ({}) }) as DOMRect;
  }
  fireEvent.wheel(scroller);
  fireEvent.scroll(scroller);
  await settleDesk(0, 10);
  await new Promise((resolve) => setTimeout(resolve, 40));
  await settleDesk(0, 10);
}

function select(win: HTMLElement, spanId: string) {
  const block = win.querySelector<HTMLElement>(`[data-span-id="${spanId}"]`)!;
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseDown(block);
  fireEvent.mouseUp(block);
}

async function openPair() {
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never]]) });
  await settleDesk(0, 20);
  await waitFor(() => expect(winOf("w_book")?.querySelector(`[data-span-id="${book.extractionId}_s1_1"]`)).toBeTruthy());
  fireEvent.keyDown(window, { key: "\\", ctrlKey: true });
  await settleDesk(0, 20);
  await waitFor(() => expect(paperWindow()).toBeTruthy());
  return { desk, paper: paperWindow()!, bookWin: winOf("w_book")! };
}

it("Ctrl+\\ opens the section's first correspondent in a window paired with the book", async () => {
  const { paper: paperWin, bookWin } = await openPair();
  expect(correspondentsAsked()).toEqual([`${book.extractionId}_s1 (search)`]);
  // One slot, two panes: the book on top, the paper below; the book keeps its book.
  const [deskOfBook, slotOfBook, paneOfBook] = slotOf(bookWin);
  const [deskOfPaper, slotOfPaper, paneOfPaper] = slotOf(paperWin);
  expect([deskOfPaper, slotOfPaper]).toEqual([deskOfBook, slotOfBook]);
  expect([paneOfBook, paneOfPaper]).toEqual(["0", "1"]);
  expect(bookWin.querySelector(`[data-span-id="${book.extractionId}_s1_1"]`)).toBeTruthy();
  // No second pane inside the book's window.
  expect(bookWin.querySelector("[data-side-by-side-pane]")).toBeNull();
  await waitFor(() => expect(headOf(paperWin)).toContain("1 Attention as a weighted average"));
});

it("follow along moves the pair once when the book crosses into a new section; the moved window does not answer back", async () => {
  const { bookWin, paper: paperWin } = await openPair();
  await scrollTo(bookWin, BOOK_S2_FIRST);
  await waitFor(() => expect(headOf(paperWin)).toContain("2 Why divide by the square root"));
  // Asked once for the book's new section (judged only); never for the paper's section the move put in view.
  expect(correspondentsAsked()).toEqual([`${book.extractionId}_s1 (search)`, `${book.extractionId}_s2`]);
});

it("a late answer for an earlier crossing never moves a window the learner has scrolled, nor overrides a newer crossing", async () => {
  const { bookWin, paper: paperWin } = await openPair();
  // The learner's own hand on the paper while the book's crossing is being answered: the answer moves nothing.
  held.set(`${book.extractionId}_s2`, () => undefined);
  await scrollTo(bookWin, BOOK_S2_FIRST);
  expect(correspondentsAsked()).toContain(`${book.extractionId}_s2`);
  fireEvent.wheel(paperWin.querySelector<HTMLElement>(".ll-scroll")!);
  held.get(`${book.extractionId}_s2`)!();
  await settleDesk(0, 20);
  expect(headOf(paperWin)).toContain("1 Attention as a weighted average");
  // A newer crossing (into section 3) answered first: the earlier one's late answer does not take the paper back.
  held.set(`${book.extractionId}_s2`, () => undefined);
  await scrollTo(bookWin, `${book.extractionId}_s1_1`);
  await scrollTo(bookWin, BOOK_S2_FIRST);
  await scrollTo(bookWin, `${book.extractionId}_s3_1`);
  await waitFor(() => expect(headOf(paperWin)).toContain("3 "));
  held.get(`${book.extractionId}_s2`)!();
  await settleDesk(0, 20);
  expect(headOf(paperWin)).not.toContain("2 Why divide by the square root");
  expect(headOf(paperWin)).toContain("3 ");
}, 20_000);

it("Ctrl+Shift+L turns following off for the pair, and F6 moves the focus to the other window", async () => {
  const { bookWin, paper: paperWin } = await openPair();
  // The paired window took the focus when it opened; F6 there goes back to the book, and again to the paper.
  expect(focusedWindow()).toBe(paperWin.getAttribute("data-desk-window"));
  fireEvent.keyDown(window, { key: "F6" });
  await settleDesk(0, 6);
  expect(focusedWindow()).toBe("w_book");
  fireEvent.keyDown(window, { key: "L", ctrlKey: true, shiftKey: true });
  await settleDesk(0, 6);
  await scrollTo(bookWin, BOOK_S2_FIRST);
  expect(headOf(bookWin)).toContain("2 ");
  expect(correspondentsAsked()).toEqual([`${book.extractionId}_s1 (search)`]);
  expect(headOf(paperWin)).not.toContain("2 Why divide by the square root");
  fireEvent.keyDown(window, { key: "F6" });
  await settleDesk(0, 6);
  expect(focusedWindow()).toBe(paperWin.getAttribute("data-desk-window"));
});

it("a highlight made in the paired window is that book's (each window acts on its own book)", async () => {
  const { paper: paperWin } = await openPair();
  select(paperWin, `${paper.extractionId}_p1_1`);
  const box = await within(paperWin).findByRole("textbox", { name: BOX });
  fireEvent.keyDown(box, { key: "Tab" });
  const palette = await within(paperWin).findByRole("group", { name: "what do you want to do?" });
  fireEvent.click(within(palette).getByRole("button", { name: "highlight" }));
  await settleDesk(0, 8);
  await waitFor(() => expect(inputsOf("reader_capture")).toHaveLength(1));
  expect(inputsOf("reader_capture")[0]).toMatchObject({ sourceId: paper.sourceId, extractionId: paper.extractionId });
});
