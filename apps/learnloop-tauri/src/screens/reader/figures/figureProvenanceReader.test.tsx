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

const { api, plan, state } = vi.hoisted(() => ({
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
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? CONTRACT : { sources: state.sources }, error: null }) }));
vi.mock("../readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("../guidePlan", () => ({ readGuidePlan: () => Promise.resolve(plan), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("../useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

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
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [figure("ext_axler", "a7")] });
  const { before, onError } = await pressOpenThePage();
  await waitFor(() => expect(api.readerRenderView.mock.calls.slice(before).map((call) => call[0].extractionId)).toContain("src_axler"));
  expect(api.readerGetProgress).toHaveBeenCalledWith({ extractionId: "ext_axler" });
  expect(onError).not.toHaveBeenCalled();
});

it("an earlier reading of the open book reopens it and translates the span, never peeking it as this reading's", async () => {
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [figure("ext_old", "old_span")] });
  await pressOpenThePage();
  await waitFor(() => expect(api.readerSavedPlace).toHaveBeenCalledWith(expect.objectContaining({ sourceId: view.sourceId, spanId: "old_span", extractionId: "ext_old" })));
});

it("the open reading's own equation peeks its passage with no new read", async () => {
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [figure(view.extractionId, view.blocks[2].spanId as string)] });
  const { before, onError } = await pressOpenThePage();
  await screen.findByRole("navigation", { name: "Detour" });
  expect(api.readerRenderView.mock.calls.length).toBe(before);
  expect(onError).not.toHaveBeenCalled();
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
