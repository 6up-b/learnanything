// A highlight's note in the Reader: what the learner writes in the Notes
// rail's box after a passage is highlighted (or noted) is saved on that
// highlight, by a control that says so or when the box loses focus.
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ScopedSource } from "../desks/source/ScopedSource";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import { readerIntentContractFixture as intent } from "../../fixtures/readerIntentContract";
import type { SourceLibraryCard } from "../../api/dto";
import { findJargon } from "../../copy/denyList";
import { resetReaderActivityForTests } from "./activity";
import { INTENT_COPY } from "./intentPalette";

const { api, contract } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerRouteIntent: vi.fn(), readerIntentRouting: vi.fn(), readerIntentOutcome: vi.fn(),
    readerInvokePreset: vi.fn(), readerCapture: vi.fn(), readerEditAnnotation: vi.fn(), readerActiveQuestion: vi.fn(),
    readerActiveQuestionStatus: vi.fn(), readerSetMode: vi.fn(),
  },
  contract: { value: {} as Record<string, unknown> },
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? contract.value : { sources: [source.card] }, error: null }) }));
vi.mock("./readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const source = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };
const BOX = "What do you want to do with this?";
const SAVED = /✓ saved · choose another action or select another passage/;
const WORDS = "Equal counts do not mean equal chances for the first thing I happen to see.";

function select(block: HTMLElement): void {
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
}

async function openBox() {
  render(<ScopedSource initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  select(block);
  const box = await screen.findByRole("textbox", { name: BOX });
  return { block, box: box as HTMLInputElement };
}

async function pickFromPalette(name: string) {
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: INTENT_COPY.paletteLabel });
  fireEvent.click(within(palette).getByRole("button", { name }));
}

function openNotes() {
  fireEvent.mouseDown(screen.getByRole("button", { name: "notes" }));
  fireEvent.click(screen.getByRole("button", { name: "notes" }));
}

/** The Notes rail's note box (its placeholder changes once the passage is highlighted). */
function noteBox(): HTMLTextAreaElement {
  return screen.getByPlaceholderText(/note/) as HTMLTextAreaElement;
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
  contract.value = { readerEnabled: true, inquiryEnabled: true, intent, activeReading: { foldBlocks: 3 } };
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerIntentOutcome.mockResolvedValue({ routingId: "r", recorded: true });
  api.readerSetMode.mockResolvedValue({ mode: "skim" });
  api.readerCapture.mockResolvedValue({ annotationId: "ann_1", anchorStatus: "exact" });
  api.readerEditAnnotation.mockResolvedValue({ annotationId: "ann_1" });
  api.readerInvokePreset.mockResolvedValue({ annotationId: "ann_p", anchorStatus: "exact", arc: null });
});
afterEach(() => { cleanup(); vi.useRealTimers(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });

describe("a note typed after the passage is highlighted is saved on that highlight (UX-50)", () => {
  it("after 'note' from the box's list: the words typed in the Notes box are saved by 'save note', and 'saved' never shows above unsaved words", async () => {
    await openBox();
    await pickFromPalette("note");
    await waitFor(() => expect(api.readerCapture).toHaveBeenCalledTimes(1));
    openNotes();
    expect(await screen.findByText(SAVED)).toBeTruthy();
    fireEvent.change(noteBox(), { target: { value: WORDS } });
    // Unsaved words: no "saved" line, and a control that says what it does.
    expect(screen.queryByText(SAVED)).toBeNull();
    const save = screen.getByRole("button", { name: "save note" }) as HTMLButtonElement;
    expect(save.disabled).toBe(false);
    fireEvent.click(save);
    await waitFor(() => expect(api.readerEditAnnotation).toHaveBeenCalledTimes(1));
    expect(api.readerEditAnnotation).toHaveBeenCalledWith({ annotationId: "ann_1", learnerText: WORDS });
    expect(await screen.findByText(SAVED)).toBeTruthy();
    expect(screen.getByText(`your note: “${WORDS}”`)).toBeTruthy();
    expect(noteBox().value).toBe("");
    expect(api.readerCapture).toHaveBeenCalledTimes(1); // no second highlight
  });

  it("leaving the box with words in it saves them, once", async () => {
    await openBox();
    openNotes();
    fireEvent.click(screen.getByRole("button", { name: "highlight" }));
    await waitFor(() => expect(api.readerCapture).toHaveBeenCalledTimes(1));
    expect(api.readerCapture.mock.calls[0][0]).toMatchObject({ learnerText: "" });
    const box = noteBox();
    fireEvent.focus(box);
    fireEvent.change(box, { target: { value: WORDS } });
    fireEvent.blur(box);
    await waitFor(() => expect(api.readerEditAnnotation).toHaveBeenCalledTimes(1));
    expect(api.readerEditAnnotation).toHaveBeenCalledWith({ annotationId: "ann_1", learnerText: WORDS });
    expect(await screen.findByText(SAVED)).toBeTruthy();
    fireEvent.blur(noteBox());
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(api.readerEditAnnotation).toHaveBeenCalledTimes(1);
  });

  it("a note written before highlighting goes with the highlight as before; more words later are added to it", async () => {
    await openBox();
    openNotes();
    fireEvent.change(noteBox(), { target: { value: "first thought" } });
    expect(screen.queryByText(SAVED)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "highlight" }));
    await waitFor(() => expect(api.readerCapture).toHaveBeenCalledTimes(1));
    expect(api.readerCapture.mock.calls[0][0]).toMatchObject({ learnerText: "first thought" });
    expect(await screen.findByText("your note: “first thought”")).toBeTruthy();
    expect((screen.getByRole("button", { name: "highlighted ✓" }) as HTMLButtonElement).disabled).toBe(true);
    fireEvent.change(noteBox(), { target: { value: "second thought" } });
    fireEvent.click(screen.getByRole("button", { name: "save note" }));
    await waitFor(() => expect(api.readerEditAnnotation).toHaveBeenCalledTimes(1));
    expect(api.readerEditAnnotation).toHaveBeenCalledWith({ annotationId: "ann_1", learnerText: "first thought\n\nsecond thought" });
  });

  it("after a mark that is not a highlight, words in the box are not called saved: 'highlight' still sends them", async () => {
    await openBox();
    openNotes();
    fireEvent.click(screen.getByRole("button", { name: "mark confusing" }));
    await waitFor(() => expect(api.readerInvokePreset).toHaveBeenCalledTimes(1));
    expect(await screen.findByText(SAVED)).toBeTruthy();
    fireEvent.change(noteBox(), { target: { value: WORDS } });
    expect(screen.queryByText(SAVED)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "highlight" }));
    await waitFor(() => expect(api.readerCapture).toHaveBeenCalledTimes(1));
    expect(api.readerCapture.mock.calls[0][0]).toMatchObject({ learnerText: WORDS });
    expect(api.readerEditAnnotation).not.toHaveBeenCalled();
  });

  it("its words are plain", () => {
    for (const line of ["save note", "your note: “a”", "add a note to this highlight…", "add to your note on this highlight…"]) {
      expect(findJargon(line)).toEqual([]);
    }
  });
});
