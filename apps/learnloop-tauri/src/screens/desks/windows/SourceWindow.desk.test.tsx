// A source window on a desk, with its real body (spec §7.1; §21.1's first row: "the existing ReaderScreen selection
// and capture tests, run against SourceWindow"). The desks mount the Reader's source pane in the window; nothing here
// stands in for the window, the pane or the desks, only for the sidecar (and for pdf.js, which jsdom cannot load):
//
// * a selection on the text is captured with its exact nodes and offsets, and the highlight is drawn at once;
// * a selection on the original PDF reaches the sidecar as the pane sent it, and highlights come from placements;
// * held-out material offers no model action, while highlight and note stay;
// * a highlight removed from the page can be undone, by the button or Ctrl+Z, in its own window;
// * a block whose extraction failed says so, and offers the original.
import { act, cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReaderRenderViewDto } from "../../../api/dto";
import { answers, inputsOf, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_SOURCES, FIXTURE_VIEWS } from "../../../fixtures/desks/sources";
import { readerIntentContractFixture } from "../../../fixtures/readerIntentContract";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
// pdf.js cannot load in jsdom: the original-PDF pane is a stand-in that keeps the props the Reader gives it, so a
// test selects as the pane would (exact nodes with code-point offsets) and reads the highlights the Reader draws.
const pane = vi.hoisted(() => ({ props: null as null | Record<string, unknown> }));
vi.mock("../../../components/PdfReaderPane", async () => {
  const { forwardRef, useImperativeHandle } = await import("react");
  return {
    PdfReaderPane: forwardRef(function FakePane(props: Record<string, unknown>, ref) {
      pane.props = props;
      useImperativeHandle(ref, () => ({ scrollToPage: () => undefined, scrollToSegment: () => undefined }));
      return <div data-testid="pdf-pane" />;
    }),
  };
});

const { book } = FIXTURE_SOURCES;
const VIEW = FIXTURE_VIEWS[book.sourceId];
const FIRST = `${book.extractionId}_s1_1`;
const SECOND = `${book.extractionId}_s1_2`;
const BOX = "What do you want to do with this?";
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };

const backend = { annotations: [] as unknown[], protection: null as null | { withheld: boolean; heldOutSpanIds: string[]; message: string | null } };

function textOf(spanId: string): string {
  return VIEW.blocks.find((block) => block.spanId === spanId)?.markdown ?? "";
}

function head(id: string, placement: unknown, kind = "highlight") {
  return {
    annotation: { id }, version: { annotationType: kind, learnerText: "" },
    anchor: { status: "exact", extractionId: book.extractionId },
    segments: [{ spanId: FIRST, exactQuote: "a score", geometryJson: null }], placement,
  };
}

beforeEach(() => {
  resetSidecar();
  pane.props = null;
  backend.annotations = [];
  backend.protection = null;
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
  answers.set("reader_prompt_contract", () => ({
    version: "fixture", context: "reader", readerEnabled: true, notSocraticByDefault: true, defaultAnswerMode: "answer_directly",
    answerModes: ["answer_directly"], mayReveal: [], manifestIncludes: [], manifestNeverIncludes: [], citations: "spans",
    exposureOnCommit: "none", inquiryEnabled: true, intent: readerIntentContractFixture, activeReading: { foldBlocks: 3 },
  }));
  answers.set("reader_render_view", () => ({ ...VIEW, ...(backend.protection ? { protection: backend.protection } : {}) } as ReaderRenderViewDto));
  answers.set("reader_source_annotations", () => ({ annotations: backend.annotations }));
  answers.set("reader_capture", (input) => {
    const nodes = (input.rawSelection as { nodes: Array<{ spanId: string; quote: string; start: number; end: number }> }).nodes;
    backend.annotations = [...backend.annotations, head("ann_new", {
      state: "here", flagSpanId: null,
      segments: nodes.map((node) => ({ spanId: node.spanId, codepointStart: node.start, codepointEnd: node.end, exactQuote: node.quote })),
    })];
    return { annotationId: "ann_new", outboxId: "o1", interactionEventId: "e1", anchorStatus: "exact", captureKind: "annotation", deduplicated: false, receipt: "saved" };
  });
  answers.set("reader_delete_intent_annotation", () => ({ eventId: "ev_del" }));
  answers.set("reader_restore_annotation", (input) => ({ annotationId: input.annotationId, restored: true, eventId: "ev_undo", listed: true }));
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.getSelection()?.removeAllRanges();
});

async function openBookWindow() {
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never]]) });
  await settleDesk(0, 20);
  const win = document.querySelector<HTMLElement>('[data-desk-window="w_book"]')!;
  await waitFor(() => expect(win.textContent?.includes(textOf(FIRST).slice(0, 30)) || win.querySelector('[data-testid="pdf-pane"]')).toBeTruthy());
  return { desk, win };
}

function blockIn(win: HTMLElement, spanId: string): HTMLElement {
  return win.querySelector<HTMLElement>(`[data-span-id="${spanId}"]`)!;
}

/** A drag over a passage's words, as the browser reports it: a range on the text, then the mouse up. */
function selectWords(win: HTMLElement, spanId: string, words: string) {
  const host = blockIn(win, spanId);
  const walker = document.createTreeWalker(host, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode() as Text | null; node; node = walker.nextNode() as Text | null) {
    const at = node.data.indexOf(words);
    if (at < 0) continue;
    const range = document.createRange();
    range.setStart(node, at);
    range.setEnd(node, at + words.length);
    window.getSelection()!.removeAllRanges();
    window.getSelection()!.addRange(range);
    fireEvent.mouseDown(host);
    fireEvent.mouseUp(host);
    return;
  }
  throw new Error(`no text node holds “${words}”`);
}

async function runFromPalette(win: HTMLElement, label: string) {
  const box = await within(win).findByRole("textbox", { name: BOX });
  fireEvent.keyDown(box, { key: "Tab" });
  const palette = await within(win).findByRole("group", { name: "what do you want to do?" });
  fireEvent.click(within(palette).getByRole("button", { name: label }));
  await settleDesk(0, 6);
}

it("a selection on the text is captured with its exact nodes and offsets, and the highlight is drawn at once", async () => {
  const { win } = await openBookWindow();
  selectWords(win, FIRST, "one number per class");
  await runFromPalette(win, "highlight");
  const [capture] = inputsOf("reader_capture");
  const text = textOf(FIRST);
  const start = Array.from(text.slice(0, text.indexOf("one number per class"))).length;
  expect(capture).toMatchObject({
    action: "highlight", sourceId: book.sourceId, extractionId: book.extractionId,
    rawSelection: { extractionId: book.extractionId, nodes: [{ spanId: FIRST, quote: "one number per class", start, end: start + 20 }] },
  });
  // Drawn on its passage at once (the annotated wash), in this window; the passage beside it is not.
  await waitFor(() => expect(blockIn(win, FIRST).style.background).toBe("rgba(245, 166, 35, 0.04)"));
  expect(blockIn(win, SECOND).style.background).toBe("");
});

/** The book as a PDF-native source: the original's blocks on its pages, as reader.pdf_view sends them. */
function asPdf() {
  answers.set("reader_pdf_view", () => ({
    version: 1, available: true, fileName: "sha256-fx", extractionId: book.extractionId, sourceId: book.sourceId, revisionId: VIEW.revisionId,
    blocks: [FIRST, SECOND].map((spanId, page) => ({ spanId, page, bbox: [72, 100, 540, 160], blockType: "Text", text: textOf(spanId) })),
    pageSpans: [{ spanId: FIRST, page: 0 }, { spanId: SECOND, page: 1 }],
    ...(backend.protection ? { protection: backend.protection } : {}),
  }));
}

type PaneProps = {
  highlights?: Array<{ id: string; state: string; segments: unknown[] }>;
  onTextSelection: (selection: unknown) => void;
  onHighlightRemove: (id: string) => void;
};
const paneProps = () => pane.props as unknown as PaneProps;

/** What the pane hands over for the words `quote` of a passage. */
function selectOnPage(spanId: string, quote: string) {
  const text = textOf(spanId);
  const start = Array.from(text.slice(0, text.indexOf(quote))).length;
  const node = { spanId, quote, start, end: start + Array.from(quote).length };
  act(() => paneProps().onTextSelection({ spanId, quote, nodes: [node], text: quote }));
  return node;
}

it("a selection on the original PDF reaches the sidecar as the pane sent it, and the highlight is drawn from its placement", async () => {
  asPdf();
  const { win } = await openBookWindow();
  await waitFor(() => expect(pane.props).not.toBeNull());
  // The window's own view switch, the only header a source window keeps.
  expect(within(win).getByText("extracted text →")).toBeTruthy();
  const node = selectOnPage(FIRST, "a score");
  await runFromPalette(win, "highlight");
  expect(inputsOf("reader_capture")[0].rawSelection).toEqual({ extractionId: book.extractionId, nodes: [node] });
  await waitFor(() => expect(paneProps().highlights?.find((each) => each.id === "ann_new")?.segments).toEqual([{ spanId: FIRST, start: node.start, end: node.end }]));
  expect(inputsOf("reader_source_annotations").every((input) => input.extractionId === book.extractionId)).toBe(true);
});

it("on held-out material the palette offers no model action; highlight and note stay", async () => {
  backend.protection = { withheld: false, heldOutSpanIds: [SECOND], message: "This passage is held out for your exam." };
  const { win } = await openBookWindow();
  selectWords(win, SECOND, "positive and add up to one");
  const box = await within(win).findByRole("textbox", { name: BOX });
  fireEvent.keyDown(box, { key: "Tab" });
  const palette = await within(win).findByRole("group", { name: "what do you want to do?" });
  const offered = within(palette).getAllByRole("button").map((button) => button.textContent?.trim());
  const modelActions = readerIntentContractFixture.palette.flatMap((group) => group.actions).filter((action) => action.model).map((action) => action.label);
  expect(offered.filter((label) => modelActions.includes(label ?? ""))).toEqual([]);
  expect(offered).toEqual(expect.arrayContaining(["highlight", "note"]));
  fireEvent.keyDown(box, { key: "Escape" });
  // A passage that is not held out offers them again.
  selectWords(win, FIRST, "one number per class");
  const again = await within(win).findByRole("textbox", { name: BOX });
  fireEvent.keyDown(again, { key: "Tab" });
  const next = await within(win).findByRole("group", { name: "what do you want to do?" });
  expect(within(next).getAllByRole("button").some((button) => modelActions.includes(button.textContent?.trim() ?? ""))).toBe(true);
});

it("a highlight removed from the page can be undone in its window, by the button or by Ctrl+Z", async () => {
  asPdf();
  const placed = head("ann_here", { state: "here", flagSpanId: null, segments: [{ spanId: FIRST, codepointStart: 2, codepointEnd: 12, exactQuote: "classifier" }] });
  backend.annotations = [placed];
  const { win } = await openBookWindow();
  await waitFor(() => expect(paneProps().highlights?.map((each) => each.id)).toEqual(["ann_here"]));
  backend.annotations = [];
  act(() => paneProps().onHighlightRemove("ann_here"));
  await settleDesk(0, 4);
  expect(inputsOf("reader_delete_intent_annotation")).toEqual([{ annotationId: "ann_here" }]);
  expect(within(win).getByRole("status").textContent).toContain("Highlight removed.");
  backend.annotations = [placed];
  fireEvent.click(within(win).getByRole("button", { name: "undo" }));
  await settleDesk(0, 4);
  expect(inputsOf("reader_restore_annotation")).toEqual([{ annotationId: "ann_here", deleteEventId: "ev_del" }]);
  await waitFor(() => expect(paneProps().highlights?.map((each) => each.id)).toEqual(["ann_here"]));
  // Again, undone with Ctrl+Z this time: the desks pass the chord to the window it belongs to.
  backend.annotations = [];
  act(() => paneProps().onHighlightRemove("ann_here"));
  await settleDesk(0, 4);
  fireEvent.keyDown(window, { key: "z", ctrlKey: true });
  await settleDesk(0, 4);
  expect(inputsOf("reader_restore_annotation")).toHaveLength(2);
});

it("a block whose extraction failed says so on the text, and offers the original page where there is one", async () => {
  answers.set("reader_render_view", () => ({
    ...VIEW, blocks: VIEW.blocks.map((block) => (block.spanId === SECOND ? { ...block, health: { status: "failed", recommendedView: "original", reasonFlags: ["garbled"] } } : block)),
  } as ReaderRenderViewDto));
  asPdf();
  const { win } = await openBookWindow();
  fireEvent.click(within(win).getByText("extracted text →"));
  await settleDesk(0, 3);
  const failed = blockIn(win, SECOND);
  expect(failed.textContent).toContain("failed · original");
  fireEvent.click(within(failed).getByRole("button", { name: "extracted text unreliable — view original →" }));
  await settleDesk(0, 3);
  // Back on the original, at that passage.
  expect(within(win).getByTestId("pdf-pane")).toBeTruthy();
  expect(within(win).getByText("extracted text →")).toBeTruthy();
});
