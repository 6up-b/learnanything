// The selection box ("what do you want to do with this?"): words typed only to
// find an action in its list are not kept as a highlight's note; anything
// more the learner writes is, as before, and the list says which it is.
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ScopedSource } from "../desks/source/ScopedSource";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import { readerIntentContractFixture as intent } from "../../fixtures/readerIntentContract";
import type { SourceLibraryCard } from "../../api/dto";
import { findJargon } from "../../copy/denyList";
import { resetReaderActivityForTests } from "./activity";
import { INTENT_COPY, onlyNamesAnAction } from "./intentPalette";

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

describe("words typed to find an action are not kept as a note (UX-51)", () => {
  it("typing 'highlight' and picking highlight from the list saves no note, and the list says why", async () => {
    const { box } = await openBox();
    fireEvent.keyDown(window, { key: "Tab" });
    const palette = await screen.findByRole("group", { name: INTENT_COPY.paletteLabel });
    fireEvent.change(box, { target: { value: "highlight" } });
    expect(within(palette).getByText("“highlight” only finds an action: it isn't kept as a note.")).toBeTruthy();
    fireEvent.click(within(palette).getByRole("button", { name: "highlight" }));
    await waitFor(() => expect(api.readerCapture).toHaveBeenCalledTimes(1));
    expect(api.readerCapture.mock.calls[0][0]).toMatchObject({ learnerText: "" });
  });

  it("the start of an action's name, or the name with 'this', is not a note either; the Enter route keeps the same rule", async () => {
    api.readerRouteIntent.mockResolvedValue({
      state: "done", routingId: "r_note", speculative: false, action: "highlight", status: "routed", reason: null,
      intention: null, group: "mark", label: "highlight", effect: { kind: "highlight" }, latencyMs: 9,
    });
    const { box } = await openBox();
    fireEvent.change(box, { target: { value: "Highlight this" } });
    fireEvent.keyDown(box, { key: "Enter" });
    await waitFor(() => expect(api.readerCapture).toHaveBeenCalledTimes(1));
    expect(api.readerCapture.mock.calls[0][0]).toMatchObject({ learnerText: "" });
  });

  it("words that are more than an action's name are the note, as before", async () => {
    const { box } = await openBox();
    fireEvent.keyDown(window, { key: "Tab" });
    const palette = await screen.findByRole("group", { name: INTENT_COPY.paletteLabel });
    fireEvent.change(box, { target: { value: "the gaps between arrivals matter" } });
    expect(within(palette).getByText("A highlight or a note keeps your words as its note.")).toBeTruthy();
    fireEvent.click(within(palette).getByRole("button", { name: "note" }));
    await waitFor(() => expect(api.readerCapture).toHaveBeenCalledTimes(1));
    expect(api.readerCapture.mock.calls[0][0]).toMatchObject({ learnerText: "the gaps between arrivals matter" });
  });

  it("the rule, on the palette's own names", () => {
    const groups = intent.palette;
    for (const words of ["highlight", "Highlight", "highl", "note", "note this", "highlight it", "confusing", "  mark ", "highlight."]) {
      expect(onlyNamesAnAction(words, groups), words).toBe(true);
    }
    for (const words of ["", "the gaps matter", "highlight because the gaps matter", "important for the exam"]) {
      expect(onlyNamesAnAction(words, groups), words).toBe(false);
    }
  });

  it("its words are plain", () => {
    for (const line of [INTENT_COPY.whereThisGoes, "“highlight” only finds an action: it isn't kept as a note.", "A highlight or a note keeps your words as its note."]) {
      expect(findJargon(line)).toEqual([]);
    }
  });
});
