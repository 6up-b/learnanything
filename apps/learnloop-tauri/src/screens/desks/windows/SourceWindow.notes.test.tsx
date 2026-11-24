// The learner's notes in a source window on a desk, with real bodies (spec §7.1 "margin notes", §21.1 "Notes rail:
// margin notes, search, What this knows"): a desk shows no Notes rail unless a panel is opened for the book, so the
// window's margin carries the learner's words. A passage with a note or highlight shows "›" in its margin; it opens
// a small card there with the words, to edit, delete (with undo) or, when the book was read again and the words moved,
// re-anchor; a highlight opened on the original PDF opens the same card.
import { act, cleanup, fireEvent, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { answers, inputsOf, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_SOURCES, FIXTURE_VIEWS } from "../../../fixtures/desks/sources";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
const pane = vi.hoisted(() => ({ props: null as null | Record<string, unknown> }));
vi.mock("../../../components/PdfReaderPane", async () => {
  const { forwardRef, useImperativeHandle } = await import("react");
  return {
    PdfReaderPane: forwardRef(function FakePane(props: Record<string, unknown>, ref) {
      pane.props = props;
      useImperativeHandle(ref, () => ({ scrollToPage: () => undefined, scrollToSegment: () => undefined }));
      // The pane draws its inline notes under their passages; the stand-in draws them in order.
      const notes = (props.inlineNotes as Array<{ spanId: string; node: unknown }> | undefined) ?? [];
      return <div data-testid="pdf-pane">{notes.map((note, index) => <div key={index} data-inline-note={note.spanId}>{note.node as never}</div>)}</div>;
    }),
  };
});

const { book } = FIXTURE_SOURCES;
const VIEW = FIXTURE_VIEWS[book.sourceId];
const FIRST = `${book.extractionId}_s1_1`;
const SECOND = `${book.extractionId}_s1_2`;
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };

const backend = { annotations: [] as unknown[], pdf: false };

function head(id: string, spanId: string, options: { kind?: string; text?: string; status?: string } = {}) {
  return {
    annotation: { id }, version: { annotationType: options.kind ?? "interpretation", learnerText: options.text ?? "" },
    anchor: { status: options.status ?? "exact", extractionId: book.extractionId },
    segments: [{ spanId, exactQuote: "a score", geometryJson: null }],
    placement: { state: "here", flagSpanId: null, segments: [{ spanId, codepointStart: 0, codepointEnd: 10, exactQuote: "A classifi" }] },
  };
}

beforeEach(() => {
  resetSidecar();
  pane.props = null;
  backend.annotations = [head("ann_note", FIRST, { text: "scores are not trust" })];
  backend.pdf = false;
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
  answers.set("reader_source_annotations", () => ({ annotations: backend.annotations }));
  answers.set("reader_edit_annotation", (input) => ({ annotationId: input.annotationId, status: "exact" }));
  answers.set("reader_delete_intent_annotation", () => ({ eventId: "ev_del" }));
  answers.set("reader_restore_annotation", (input) => ({ annotationId: input.annotationId, restored: true, eventId: "ev_undo", listed: true }));
  answers.set("reader_reanchor", (input) => ({ annotationId: input.annotationId, status: "exact" }));
  answers.set("reader_pdf_view", () => (backend.pdf ? {
    version: 1, available: true, fileName: "sha256-fx", extractionId: book.extractionId, sourceId: book.sourceId, revisionId: VIEW.revisionId,
    blocks: [FIRST, SECOND].map((spanId, page) => ({ spanId, page, bbox: [72, 100, 540, 160], blockType: "Text", text: "" })),
    pageSpans: [{ spanId: FIRST, page: 0 }, { spanId: SECOND, page: 1 }],
  } : { available: false }));
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const winEl = () => document.querySelector<HTMLElement>('[data-desk-window="w_book"]')!;

async function openBook() {
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never]]) });
  await settleDesk(0, 20);
  await waitFor(() => expect(winEl().querySelector(`[data-span-id="${FIRST}"]`) ?? winEl().querySelector('[data-testid="pdf-pane"]')).toBeTruthy());
  return desk;
}

const markOn = (spanId: string) => winEl().querySelector<HTMLButtonElement>(`[data-span-id="${spanId}"] [data-window-note-mark]`);

it("a passage with the learner's note shows › in its margin, which opens the note there to edit", async () => {
  await openBook();
  await waitFor(() => expect(markOn(FIRST)).not.toBeNull());
  expect(markOn(SECOND)).toBeNull();
  fireEvent.click(markOn(FIRST)!);
  const card = await within(winEl()).findByRole("group", { name: "your notes on this passage" });
  expect(card.textContent).toContain("scores are not trust");
  fireEvent.click(within(card).getByRole("button", { name: "edit note" }));
  fireEvent.change(within(card).getByPlaceholderText("your note…"), { target: { value: "scores rank; softmax weighs" } });
  fireEvent.click(within(card).getByRole("button", { name: "save ↵" }));
  await settleDesk(0, 4);
  expect(inputsOf("reader_edit_annotation")).toEqual([{ annotationId: "ann_note", learnerText: "scores rank; softmax weighs" }]);
});

it("a note deleted from its card can be undone in the window", async () => {
  await openBook();
  await waitFor(() => expect(markOn(FIRST)).not.toBeNull());
  fireEvent.click(markOn(FIRST)!);
  const card = await within(winEl()).findByRole("group", { name: "your notes on this passage" });
  backend.annotations = [];
  fireEvent.click(within(card).getByRole("button", { name: "delete" }));
  await settleDesk(0, 4);
  expect(inputsOf("reader_delete_intent_annotation")).toEqual([{ annotationId: "ann_note" }]);
  await waitFor(() => expect(markOn(FIRST)).toBeNull());
  backend.annotations = [head("ann_note", FIRST, { text: "scores are not trust" })];
  fireEvent.click(within(within(winEl()).getByRole("status")).getByRole("button", { name: "undo" }));
  await settleDesk(0, 4);
  expect(inputsOf("reader_restore_annotation")).toEqual([{ annotationId: "ann_note", deleteEventId: "ev_del" }]);
  await waitFor(() => expect(markOn(FIRST)).not.toBeNull());
});

it("a note whose words moved when the book was read again says so and re-anchors from its card", async () => {
  backend.annotations = [head("ann_moved", FIRST, { text: "keep this", status: "needs_reanchor" })];
  await openBook();
  await waitFor(() => expect(markOn(FIRST)).not.toBeNull());
  fireEvent.click(markOn(FIRST)!);
  const card = await within(winEl()).findByRole("group", { name: "your notes on this passage" });
  expect(card.textContent).toContain("anchor needs review");
  fireEvent.click(within(card).getByRole("button", { name: "re-anchor to this version" }));
  await settleDesk(0, 4);
  expect(inputsOf("reader_reanchor")).toEqual([{ annotationId: "ann_moved", newExtractionId: book.extractionId }]);
});

it("a highlight opened on the original PDF opens its card in the window", async () => {
  backend.pdf = true;
  await openBook();
  await waitFor(() => expect((pane.props?.highlights as unknown[] | undefined)?.length).toBe(1));
  act(() => (pane.props!.onHighlightOpen as (id: string) => void)("ann_note"));
  const card = await within(winEl()).findByRole("group", { name: "your notes on this passage" });
  expect(card.textContent).toContain("scores are not trust");
  // Editing at once, as the rail opened it.
  expect(within(card).getByPlaceholderText("your note…")).toBeTruthy();
});

it("a window opened for a note (a search result names it) opens that note's card, being edited", async () => {
  const desk = mountRealDesk({ state: oneDesk([[{ ...BOOK_WINDOW, view: { spanId: FIRST, annotationId: "ann_note" } } as never]]) });
  await settleDesk(0, 20);
  const card = await within(winEl()).findByRole("group", { name: "your notes on this passage" });
  expect(within(card).getByPlaceholderText("your note…")).toBeTruthy();
  void desk;
});

it("a margin note written from the desks' n shows its › in the window at once, and opens there", async () => {
  backend.annotations = [];
  answers.set("reader_capture", (input) => {
    backend.annotations = [head("ann_new", SECOND, { text: String(input.learnerText ?? "") })];
    return { annotationId: "ann_new", outboxId: "o1", interactionEventId: "e1", anchorStatus: "exact", captureKind: "annotation", deduplicated: false, receipt: "saved" };
  });
  await openBook();
  await waitFor(() => expect(winEl().querySelector(`[data-span-id="${SECOND}"]`)).toBeTruthy());
  fireEvent.mouseOver(winEl().querySelector(`[data-span-id="${SECOND}"]`)!);
  fireEvent.keyDown(window, { key: "n" });
  // The note waits for the passage's protection (its first promoted read) before the sheet opens.
  await waitFor(() => expect(document.querySelector('[role="dialog"][aria-label="› note in margin"]')).not.toBeNull());
  const sheet = document.querySelector<HTMLElement>('[role="dialog"][aria-label="› note in margin"]')!;
  fireEvent.change(within(sheet).getByRole("textbox", { name: "your note" }), { target: { value: "weights, not votes" } });
  fireEvent.click(within(sheet).getByText("keep it"));
  await settleDesk(0, 6);
  await waitFor(() => expect(markOn(SECOND)).not.toBeNull());
  fireEvent.click(markOn(SECOND)!);
  expect((await within(winEl()).findByRole("group", { name: "your notes on this passage" })).textContent).toContain("weights, not votes");
});
