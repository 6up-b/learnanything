// RW5c Codex review F4: "open the page" through the real Reader's callback, with two books. A checked
// equation can cite another book or an earlier reading of this one; its page must open from there.
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../../ReaderScreen";
import { setAlgoConfig } from "../../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../../fixtures/readerRenderView";
import { readerIntentContractFixture as intent } from "../../../fixtures/readerIntentContract";
import type { FigureViewDto, SourceLibraryCard } from "../../../api/dto";
import { resetReaderActivityForTests } from "../activity";
import policy from "../../../render/readerBlockPolicy.json";
import { youtubeVideoId } from "../../../components/sourceTail";

const { api, pane, plan, state } = vi.hoisted(() => ({
  pane: { scrollToPage: vi.fn(), scrollToSegment: vi.fn() },
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerRouteIntent: vi.fn(), readerIntentRouting: vi.fn(), readerIntentOutcome: vi.fn(),
    readerSetMode: vi.fn(), readerFigures: vi.fn(), readerFigureRequest: vi.fn(), readerFigureJob: vi.fn(), readerFigureJobCancel: vi.fn(),
    readerSavedPlace: vi.fn(), readerSaveProgress: vi.fn(),
  },
  plan: {
    sourceId: "src", extractionId: "ext", personalized: true, selectionBasis: "", goalContext: null,
    sections: [], pendingDiagnosisAttemptIds: [],
  },
  state: { sources: [] as unknown[] },
}));
vi.mock("../../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/core", () => ({ convertFileSrc: (path: string) => path }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? CONTRACT : { sources: state.sources }, error: null }) }));
vi.mock("../readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("../guidePlan", () => ({ readGuidePlan: () => Promise.resolve(plan), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("../useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../../components/PdfReaderPane", async () => {
  const { forwardRef, useImperativeHandle } = await import("react");
  return { PdfReaderPane: forwardRef(function FakePane(props: { inlineNotes?: { spanId: string; node: unknown }[] }, ref) {
    useImperativeHandle(ref, () => pane);
    return <div data-testid="pdf-pane">{(props.inlineNotes ?? []).map((note) => <div key={note.spanId}>{note.node as never}</div>)}</div>;
  }) };
});

const CONTRACT = { readerEnabled: true, inquiryEnabled: true, intent, activeReading: { foldBlocks: 3 }, figures: { predictions: true, region: true, revisions: true } };
const STRANG = { sourceId: view.sourceId, title: "Strang", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
const AXLER = { sourceId: "src_axler", title: "Axler", canonicalUri: "axler.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
const AXLER_VIEW = { ...view, sourceId: "src_axler", extractionId: "ext_axler", aliasedFrom: [], otherReadings: [] };
const anchor = view.blocks[1].spanId as string;
const SPEC = {
  spec_version: "ifs-v1", kind: "reconstructed", demonstrates: "how the curve moves", parameters: [],
  definitions: [{ name: "f", expr: "x" }],
  panels: [{ kind: "function_plot", x: { var: "x", min: 0, max: 1 }, series: [{ expr: "f", label: "panels.0.series.0" }] }],
};

function figure(extractionId: string, spanId: string): FigureViewDto {
  return {
    figureId: "fig_1", extractionId: view.extractionId, spanIds: [anchor], anchorSpanId: anchor, region: null,
    origin: "selection", verification: "illustrative", kind: "illustrative",
    label: "AI-built illustration of an interpretation · not checked against the book", reason: null,
    unsupportedKind: null, supersedesId: null, revisionNote: null, versions: 1, createdAt: "2026-10-21T00:00:00",
    specJson: JSON.stringify(SPEC), demonstrates: "how the curve moves", assumptions: [], predictions: [],
    sourceCheck: { status: "checked", certificationVersion: 1, reasons: [], recheckDue: false, rebuild: false },
    elements: [{ id: "panels.0.series.0", path: "panels.0.series.0", role: "book", tex: "f(x)", plain: "f(x)", voice: "source",
      definition: "f", equation: "f(x)=x", source: { extractionId, spanId, page: 87 } }],
  } as unknown as FigureViewDto;
}

async function pressOpenThePage(onError = vi.fn()) {
  render(<ReaderScreen initialSource={{ card: STRANG, spanId: anchor }} onError={onError} />);
  const line = await screen.findByRole("button", { name: /interactive version/ });
  fireEvent.click(line);
  fireEvent.click(await screen.findByRole("button", { name: /how this was checked/ }));
  const before = api.readerRenderView.mock.calls.length;
  fireEvent.click(await screen.findByRole("button", { name: "open the page" }));
  return { before, onError };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  pane.scrollToPage.mockReset();
  pane.scrollToSegment.mockReset();
  resetReaderActivityForTests();
  state.sources = [STRANG, AXLER];
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  api.readerRenderView.mockImplementation(async (input: { extractionId: string }) => (
    input.extractionId === "ext_axler" || input.extractionId === "src_axler" ? AXLER_VIEW
      : input.extractionId === "ext_old" ? { ...view, extractionId: "ext_old" }
        : input.extractionId === "ext_gone" ? Promise.reject(new Error("No extraction resolves")) : view));
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerIntentOutcome.mockResolvedValue({ routingId: "r", recorded: true });
  api.readerSetMode.mockResolvedValue({ mode: "read" });
  api.readerSaveProgress.mockResolvedValue({});
  api.readerSavedPlace.mockResolvedValue({ extractionId: view.extractionId, spanId: anchor, status: "exact" });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); });

it("another book's equation opens that book, on the cited reading's span", async () => {
  api.readerSavedPlace.mockResolvedValue({ extractionId: "ext_axler", spanId: view.blocks[2].spanId, status: "exact" });
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [figure("ext_axler", "a7")] });
  const { before, onError } = await pressOpenThePage();
  await waitFor(() => expect(api.readerGetProgress).toHaveBeenCalledWith({ extractionId: "ext_axler" }));
  expect(api.readerRenderView.mock.calls.slice(before).map((call) => call[0].extractionId)).toContain("ext_axler");
  expect(onError).not.toHaveBeenCalled();
});

it("an earlier reading of the open book translates the span and peeks it here, never as this reading's own span", async () => {
  const translated = view.blocks[2].spanId as string;
  api.readerSavedPlace.mockResolvedValue({ extractionId: view.extractionId, spanId: translated, status: "exact" });
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [figure("ext_old", "old_span")] });
  const { onError } = await pressOpenThePage();
  await screen.findByRole("navigation", { name: "Detour" });
  expect(api.readerSavedPlace).toHaveBeenCalledWith(expect.objectContaining({ sourceId: view.sourceId, spanId: "old_span", extractionId: "ext_old", toExtractionId: view.extractionId }));
  expect(onError).not.toHaveBeenCalled();
});

// Sol verify V3: three readings. A is open, C completed since, the figure cites B. Whatever was
// validated is what opens, so a stale translation or a running head on C can't get past the guard.
it("an earlier reading is validated on the reading that stays open: a newer one is never opened", async () => {
  const translated = view.blocks[2].spanId as string;
  const C = { ...view, extractionId: "ext_c", blocks: [{ ...view.blocks[0], spanId: translated, blockType: "PageHeader" }] };
  api.readerRenderView.mockImplementation(async (input: { extractionId: string }) => (
    input.extractionId === "ext_b" ? { ...view, extractionId: "ext_b" } : view));
  api.readerSavedPlace.mockResolvedValue({ extractionId: view.extractionId, spanId: translated, status: "exact" });
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [figure("ext_b", "b_span")] });
  const { before, onError } = await pressOpenThePage();
  // From here the sidecar would resolve the book to C: the press must not ask it to.
  api.readerRenderView.mockImplementation(async (input: { extractionId: string }) => (
    input.extractionId === "ext_b" ? { ...view, extractionId: "ext_b" } : C));
  await screen.findByRole("navigation", { name: "Detour" });
  expect(api.readerRenderView.mock.calls.slice(before).map((call) => call[0].extractionId)).toEqual(["ext_b"]);
  expect(api.readerGetProgress).not.toHaveBeenCalledWith({ extractionId: "ext_c" });
  expect(onError).not.toHaveBeenCalled();
});

it("a translation the sidecar puts on any other reading opens nothing", async () => {
  api.readerSavedPlace.mockResolvedValue({ extractionId: "ext_c", spanId: view.blocks[2].spanId, status: "exact" });
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [figure("ext_old", "old_span")] });
  const { before, onError } = await pressOpenThePage();
  await waitFor(() => expect(onError).toHaveBeenCalledWith(expect.stringContaining("couldn't be opened")));
  expect(api.readerRenderView.mock.calls.slice(before).map((call) => call[0].extractionId)).toEqual(["ext_old"]);
  expect(screen.queryByRole("navigation", { name: "Detour" })).toBeNull();
});

it("a translated place whose words changed says so, as a search hit's does", async () => {
  api.readerSavedPlace.mockResolvedValue({ extractionId: view.extractionId, spanId: view.blocks[2].spanId, status: "needs_reanchor" });
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [figure("ext_old", "old_span")] });
  await pressOpenThePage();
  await screen.findByText(/This book was read again: you're near the passage you found/);
});

it("another book opens on the reading validated, not one a source id resolves to later", async () => {
  const validated = { ...AXLER_VIEW, extractionId: "ext_axler_y" };
  const newer = { ...AXLER_VIEW, extractionId: "ext_axler_z", blocks: [{ ...view.blocks[0], spanId: "a7", blockType: "PageHeader" }] };
  api.readerRenderView.mockImplementation(async (input: { extractionId: string }) => (
    input.extractionId === "ext_axler_x" ? { ...AXLER_VIEW, extractionId: "ext_axler_x" }
      : input.extractionId === "ext_axler_y" ? validated
        : input.extractionId === "src_axler" ? newer : view));
  api.readerSavedPlace.mockResolvedValue({ extractionId: "ext_axler_y", spanId: view.blocks[2].spanId, status: "exact" });
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [figure("ext_axler_x", "a7")] });
  const { before, onError } = await pressOpenThePage();
  await waitFor(() => expect(api.readerGetProgress).toHaveBeenCalledWith({ extractionId: "ext_axler_y" }));
  expect(api.readerRenderView.mock.calls.slice(before).map((call) => call[0].extractionId)).not.toContain("src_axler");
  expect(onError).not.toHaveBeenCalled();
});

// Sol verify V2: an already-mounted original where another passage has a box and the cited one doesn't.
const OTHER_BOX = { spanId: view.blocks[1].spanId, page: 3, bbox: [0, 0, 1, 1], polygon: null, pageWidth: 612, pageHeight: 792, kind: "text" };
function pdfManifest(pageSpans: { spanId: string; page: number }[]) {
  return { version: 1, available: true, fileName: "sha256-strang", extractionId: view.extractionId, sourceId: view.sourceId, revisionId: "rev", blocks: [OTHER_BOX], pageSpans };
}

it("on the original, a passage with no box goes to its page", async () => {
  const cited = view.blocks[2].spanId as string;
  api.readerPdfView.mockResolvedValue(pdfManifest([{ spanId: cited, page: 87 }]));
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [figure(view.extractionId, cited)] });
  const { onError } = await pressOpenThePage();
  await waitFor(() => expect(pane.scrollToPage).toHaveBeenCalledWith(87, 0));
  expect(pane.scrollToSegment.mock.calls.map((call) => call[1])).not.toContain(cited);
  expect(onError).not.toHaveBeenCalled();
});

it("on the original, a passage with no box and no page goes to the extracted text, which holds it", async () => {
  const cited = view.blocks[2].spanId as string;
  api.readerPdfView.mockResolvedValue(pdfManifest([]));
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [figure(view.extractionId, cited)] });
  const { onError } = await pressOpenThePage();
  await screen.findByText("original pdf →");
  await waitFor(() => expect(Element.prototype.scrollIntoView).toHaveBeenCalled());
  const target = vi.mocked(Element.prototype.scrollIntoView).mock.contexts.slice(-1)[0] as HTMLElement;
  expect(target.getAttribute("data-span-id")).toBe(cited);
  expect(pane.scrollToPage).not.toHaveBeenCalled();
  expect(onError).not.toHaveBeenCalled();
});

it("the open reading's own equation peeks its passage with no new read", async () => {
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [figure(view.extractionId, view.blocks[2].spanId as string)] });
  const { before, onError } = await pressOpenThePage();
  await screen.findByRole("navigation", { name: "Detour" });
  expect(api.readerRenderView.mock.calls.length).toBe(before);
  expect(onError).not.toHaveBeenCalled();
});

it("a passage this page doesn't show says so: no jump to a dropped block (Astra review A1)", async () => {
  const head = { ...view.blocks[0], spanId: "head", displayNodeId: "node-head", blockType: "PageHeader", markdown: "The identity" };
  api.readerRenderView.mockImplementation(async () => ({ ...view, blocks: [...view.blocks, head] }));
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [figure(view.extractionId, "head")] });
  const { onError } = await pressOpenThePage();
  await waitFor(() => expect(onError).toHaveBeenCalledWith(expect.stringContaining("couldn't be opened")));
  expect(screen.queryByRole("navigation", { name: "Detour" })).toBeNull();
});

it("another reading's span that lands on a dropped block, or on none, says so and opens nothing (Astra review A1)", async () => {
  const head = { ...view.blocks[0], spanId: "head", displayNodeId: "node-head", blockType: "TableOfContents", markdown: "Contents" };
  api.readerRenderView.mockImplementation(async () => ({ ...view, blocks: [...view.blocks, head] }));
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [figure("ext_old", "old_span")] });
  for (const landed of [{ extractionId: view.extractionId, spanId: "head", status: "current" }, { extractionId: view.extractionId, spanId: anchor, status: "stale" }]) {
    api.readerSavedPlace.mockResolvedValue(landed);
    const { onError } = await pressOpenThePage();
    await waitFor(() => expect(onError).toHaveBeenCalledWith(expect.stringContaining("couldn't be opened")));
    expect(api.readerGetProgress.mock.calls.length).toBe(1);
    cleanup();
    api.readerGetProgress.mockClear();
  }
});

it("the page drops furniture from the shared policy and shows every type the check may read", async () => {
  const types = [...policy.furniture, ...policy.markdown, "ATypeNobodyMet"];
  const typed = types.map((blockType, index) => (
    { ...view.blocks[0], spanId: `typed${index}`, displayNodeId: `node-typed${index}`, blockType, markdown: `block of type ${blockType}` }));
  api.readerRenderView.mockImplementation(async () => ({ ...view, blocks: typed }));
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [] });
  const { container } = render(<ReaderScreen initialSource={{ card: STRANG, spanId: `typed${policy.furniture.length}` }} onError={vi.fn()} />);
  await waitFor(() => expect(container.querySelector(`[data-span-id="typed${policy.furniture.length}"]`)).not.toBeNull());
  // The page has always shown a type it has never met; the check reads only the markdown list (test_rw5c_block_policy).
  types.forEach((blockType, index) => {
    const shown = container.querySelector(`[data-span-id="typed${index}"]`);
    if (policy.furniture.includes(blockType)) expect(shown).toBeNull();
    else expect(shown?.textContent).toContain(`block of type ${blockType}`);
  });
  expect(new Set(policy.furniture).size + new Set(policy.markdown).size).toBe(new Set([...policy.furniture, ...policy.markdown]).size);
});

it("a source the watch surface opens matches the policy's plain-text pattern, and a book does not", () => {
  const plainText = new RegExp(policy.plainTextSourceUri, "i");
  for (const uri of ["https://www.youtube.com/watch?v=abc", "https://youtu.be/abc", "https://m.youtube.com/shorts/abc", "https://www.youtube.com/live/abc"]) {
    expect(youtubeVideoId(uri)).not.toBeNull();
    expect(plainText.test(uri)).toBe(true);
  }
  for (const uri of ["book.pdf", "file:///a/youtube.pdf", "https://example.org/youtube.com"]) {
    expect(youtubeVideoId(uri)).toBeNull();
  }
  expect(plainText.test("book.pdf") || plainText.test("file:///a/youtube.pdf")).toBe(false);
});

it("a page that cannot be opened says so, never a dead press", async () => {
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [figure("ext_axler", "a7")] });
  state.sources = [STRANG];
  const { onError } = await pressOpenThePage();
  await waitFor(() => expect(onError).toHaveBeenCalledWith(expect.stringContaining("couldn't be opened")));
  cleanup();
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [figure("ext_gone", "a7")] });
  const gone = await pressOpenThePage();
  await waitFor(() => expect(gone.onError).toHaveBeenCalledWith(expect.stringContaining("No extraction resolves")));
});
