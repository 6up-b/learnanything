// RW5a with RW7a in one Reader (the RW5a landing's interaction test): with
// both `figures` and `readingPaths` in the prompt contract, a figure stays
// inline under its passage in a section the Guide's path labels core, the
// palette carries both actions, and each action reaches only its own RPCs
// ("what matters here?" builds no figure; "make this explorable" re-reads no
// path).
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import { readerIntentContractFixture as intent } from "../../fixtures/readerIntentContract";
import type { FigureViewDto, ReadingPathDto, SourceLibraryCard } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";
import corpus from "./figures/figureGoldenCorpus.json";

const { api, plan } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerRouteIntent: vi.fn(), readerIntentRouting: vi.fn(), readerIntentOutcome: vi.fn(),
    readerSetMode: vi.fn(), readerReadingPath: vi.fn(), readerReadingPathSetDepth: vi.fn(), readerReadingPathOverride: vi.fn(),
    readerFigures: vi.fn(), readerFigureRequest: vi.fn(), readerFigureJob: vi.fn(), readerFigureJobCancel: vi.fn(),
  },
  plan: {
    sourceId: "src", extractionId: "ext", personalized: true, selectionBasis: "",
    goalContext: { goalId: "goal_mix", title: "Derive mixture distributions", goldenPathRunId: null, targetContractVersionId: null },
    sections: [], pendingDiagnosisAttemptIds: [],
  },
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? CONTRACT : { sources: [source.card] }, error: null }) }));
vi.mock("./readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./guidePlan", () => ({ readGuidePlan: () => Promise.resolve(plan), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const CONTRACT = {
  readerEnabled: true, inquiryEnabled: true, intent, activeReading: { foldBlocks: 3 },
  readingPaths: { enabled: true, depths: [{ id: "get_the_idea", label: "get the idea" }, { id: "learn_to_use_it", label: "learn to use it" }, { id: "fluency", label: "fluency" }] },
  figures: { predictions: true, region: true, revisions: true },
};
const source = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };
const BOX = "What do you want to do with this?";
const anchor = view.blocks[1].spanId as string;
const FLAGSHIP = corpus.figures.find((item) => item.id === "two_sided_exponential")!.spec;
const PATH: ReadingPathDto = {
  extractionId: view.extractionId, status: "ready", depth: "learn_to_use_it", depthLabel: "learn to use it", depthOrigin: "guide",
  intent: null, depths: [], goal: { id: "goal_mix", title: "Derive mixture distributions" },
  goalLine: "toward your goal: Derive mixture distributions",
  sections: [{ sectionId: "u1", title: "Symmetric matrices", startSpanId: anchor, label: "core", chip: "core",
    reason: "needed for the spectral theorem", reasonBy: "model", override: null, effectiveLabel: "core", exercise: null, words: 200, learningObjectIds: [] }],
  next: { text: "Next: read Symmetric matrices · about 1 min of reading", sectionId: "u1", spanId: null, exercise: null, minutes: 1 },
};

function figure(): FigureViewDto {
  return {
    figureId: "fig_1", extractionId: view.extractionId, spanIds: [anchor], anchorSpanId: anchor, region: null,
    origin: "selection", verification: "illustrative", kind: "illustrative",
    label: "AI-built illustration of an interpretation · not checked against the book", reason: null,
    unsupportedKind: null, supersedesId: null, revisionNote: null, versions: 1, createdAt: "2026-10-21T00:00:00",
    specJson: JSON.stringify(FLAGSHIP), demonstrates: "a demonstration", assumptions: [], predictions: [],
  };
}

function select(block: HTMLElement): void {
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
}

async function openPalette(): Promise<HTMLElement> {
  // The passage's own block (an earlier selection's quote may also be on screen).
  await screen.findAllByText(view.blocks[1].markdown);
  const passage = document.querySelector(`[data-span-id="${anchor}"]`) as HTMLElement;
  select(within(passage).getByText(view.blocks[1].markdown));
  await screen.findByRole("textbox", { name: BOX });
  fireEvent.keyDown(window, { key: "Tab" });
  return screen.findByRole("group", { name: "what do you want to do?" });
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
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
  api.readerSetMode.mockResolvedValue({ mode: "read" });
  api.readerReadingPath.mockResolvedValue(PATH);
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [figure()] });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });

it("a figure stays inline under its passage in a section the path labels core", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  expect(await screen.findByText(PATH.next!.text)).toBeTruthy();
  expect(api.readerReadingPath).toHaveBeenCalledWith({ extractionId: view.extractionId });
  await waitFor(() => expect(api.readerFigures).toHaveBeenCalledWith({ extractionId: view.extractionId }));
  const line = await screen.findByRole("button", { name: /interactive version/ });
  const slot = line.closest(`[data-figures-under="${anchor}"]`);
  expect(slot).not.toBeNull();
  const passage = document.querySelector(`[data-span-id="${anchor}"]`)!;
  expect(passage.compareDocumentPosition(slot!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  // The code-owned frame, whatever the path says about the section.
  expect(screen.getAllByText(/not checked against the book/).length).toBeGreaterThan(0);
});

it("the palette carries both actions and each reaches only its own RPCs", async () => {
  api.readerFigureRequest.mockResolvedValue({ jobId: "ljob_1", kind: "figure_build", askId: null, state: "done", result: { reused: true, figure: figure() } });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await screen.findByText(PATH.next!.text);
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  let palette = await openPalette();
  expect(within(palette).getByRole("button", { name: "show me…" })).toBeTruthy();
  const pathReads = api.readerReadingPath.mock.calls.length;
  await act(async () => { fireEvent.click(within(palette).getByRole("button", { name: "what matters here?" })); });
  await waitFor(() => expect(screen.getByText(PATH.next!.text).closest("[style*='display: none']")).toBeNull());
  expect(api.readerFigureRequest).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  palette = await openPalette();
  const afterPath = api.readerReadingPath.mock.calls.length;
  expect(afterPath).toBeGreaterThanOrEqual(pathReads);
  fireEvent.click(within(palette).getByRole("button", { name: "show me…" }));
  await waitFor(() => expect(api.readerFigureRequest).toHaveBeenCalledWith({ extractionId: view.extractionId, spanIds: [anchor], region: null }));
  expect(api.readerReadingPath.mock.calls.length).toBe(afterPath);
  expect(api.readerRouteIntent).not.toHaveBeenCalled();
}, 15_000);
