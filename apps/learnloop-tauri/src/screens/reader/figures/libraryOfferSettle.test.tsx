// RW5b fix round 2, F9: a library "make this explorable" press in the Reader
// settles on how it actually ended -- the figure built, the request refused,
// the detour's book did not open, or figures went off before it could be
// requested -- and never keeps saying "building it under the passage" for a
// build that is not running. The harness is libraryExercisesReader.test.tsx's.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../../ReaderScreen";
import { setAlgoConfig } from "../../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../../fixtures/readerRenderView";
import { readerIntentContractFixture as intent } from "../../../fixtures/readerIntentContract";
import type { FigureViewDto, LibraryAskDto, LibraryNotesDto, SourceLibraryCard } from "../../../api/dto";
import { resetReaderActivityForTests } from "../activity";
import { LIBRARY_EXPLORABLE_COPY } from "../LibraryAnswer";
import corpus from "./figureGoldenCorpus.json";

const { api, contract } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerRouteIntent: vi.fn(), readerIntentRouting: vi.fn(), readerIntentOutcome: vi.fn(),
    readerSetMode: vi.fn(), readerSearchSources: vi.fn(),
    readerLibraryAsk: vi.fn(), readerLibraryAskNotes: vi.fn(), readerLibraryCompare: vi.fn(), readerLibraryAskTutor: vi.fn(),
    readerLibraryJob: vi.fn(), readerLibraryJobCancel: vi.fn(),
    findPractice: vi.fn(), recordProposalImpressions: vi.fn(), getSpanView: vi.fn(), readerSavedPlace: vi.fn(),
    readerFigures: vi.fn(), readerFigureRequest: vi.fn(), readerFigureJob: vi.fn(), readerFigureJobCancel: vi.fn(),
  },
  contract: { value: {} as Record<string, unknown> },
}));
vi.mock("../../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? contract.value : { sources: [source.card, other] }, error: null }) }));
vi.mock("../readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("../guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("../useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const source = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };
const other = { sourceId: "src_other", title: "Other Book", canonicalUri: "other.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
const BOX = "What do you want to do with this?";
const HERE = "ext_symmetric:span_spectral_worked";
const THERE = "ext_other:o1";
const FIGURES = { predictions: true, region: true, revisions: true, offers: true };

function hit(key: string, sourceId: string, sourceTitle: string, text: string, extra: Record<string, unknown> = {}) {
  const [extractionId, spanId] = key.split(":");
  return { key, extractionId, spanId, sourceId, sourceTitle, section: "Chapter 5", page: 3, text, role: "equation",
    group: "Foundation", expansion: null, learningObjectIds: [], authorship: "source" as const, label: "source-authored", ...extra };
}

const ASK: LibraryAskDto = {
  askId: "la_1", query: "symmetric matrices", entry: "where_else_explained", status: "ok", policy: "reading",
  personalized: false, basis: "keyword", learningObjectIds: [], extractionId: view.extractionId, anchorSpanIds: ["span_symmetric_prose"],
  hits: [
    hit(THERE, "src_other", "Other Book", "A symmetric matrix equals its transpose."),
    hit(HERE, view.sourceId, "Matrices", "Worked: diagonalize a symmetric matrix."),
  ],
  groups: {
    sources: [
      { sourceId: "src_other", sourceTitle: "Other Book", groups: [{ group: "Foundation", keys: [THERE] }] },
      { sourceId: view.sourceId, sourceTitle: "Matrices", groups: [{ group: "Foundation", keys: [HERE] }] },
    ],
    expansions: [],
  },
  expansions: [], expandGraph: false, sourceCount: 2, passageCount: 2,
};

const NOTES: LibraryNotesDto = {
  askId: "la_1", status: "judged", order: [HERE, THERE],
  notes: [
    { key: THERE, verdict: "contributes", ledgerId: "lac_1", line: "gives the transpose definition", roles: [], speaksTo: null, label: "LearnLoop's model", explorable: true },
    { key: HERE, verdict: "contributes", ledgerId: "lac_2", line: "works one example through", roles: [], speaksTo: null, label: "LearnLoop's model", explorable: true },
  ],
};

function done<T>(result: T, kind = "ask") {
  return { jobId: `ljob_${kind}`, kind, askId: "la_1", state: "done" as const, result };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => { resolve = r; });
  return { promise, resolve };
}

function figure(): FigureViewDto {
  return {
    figureId: "fig_1", extractionId: view.extractionId, spanIds: ["span_spectral_worked"], anchorSpanId: "span_spectral_worked", region: null,
    origin: "library", verification: "illustrative", kind: "illustrative",
    label: "AI-built illustration of an interpretation · not checked against the book", reason: null,
    unsupportedKind: null, supersedesId: null, revisionNote: null, versions: 1, createdAt: "2026-10-23T00:00:00",
    specJson: JSON.stringify(corpus.figures.find((item) => item.id === "two_sided_exponential")!.spec),
    demonstrates: "a demonstration", assumptions: [], predictions: [],
  };
}

function select(block: HTMLElement): void {
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
}

/** The library pane's answer, its notes landed, with both offers showing. */
async function libraryAnswer(onError = vi.fn()) {
  const page = render(<ReaderScreen initialSource={source} onError={onError} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  select(block);
  await screen.findByRole("textbox", { name: BOX });
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  fireEvent.click(within(palette).getByRole("button", { name: "where else is this explained?" }));
  const pane = await screen.findByRole("region", { name: "ask your library" });
  await within(pane).findByText("gives the transpose definition");
  return Object.assign(pane, { rerenderPage: () => page.rerender(<ReaderScreen initialSource={source} onError={onError} />) });
}

function press(pane: HTMLElement, key: string): void {
  const button = pane.querySelector(`[data-library-explorable="${key}"]`) as HTMLElement | null;
  expect(button).not.toBeNull();
  fireEvent.click(button!);
}

function offerLine(pane: HTMLElement, key: string): string {
  return (pane.querySelector(`[data-library-hit="${key}"]`) as HTMLElement).textContent ?? "";
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
  contract.value = { readerEnabled: true, inquiryEnabled: true, intent, activeReading: { foldBlocks: 3 },
    libraryAsk: { expandGraph: false, personalizedDefault: false, compare: false }, figures: FIGURES };
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
  api.readerLibraryAsk.mockResolvedValue(done(ASK));
  api.readerLibraryAskNotes.mockResolvedValue(done(NOTES, "notes"));
  api.readerLibraryJobCancel.mockResolvedValue({ jobId: "ljob_x", kind: "notes", askId: "la_1", state: "cancelled", result: null });
  api.recordProposalImpressions.mockResolvedValue({ recorded: 1 });
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [] });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });

it("a press in this book that the server refuses says it was not built and offers the button again", async () => {
  api.readerFigureRequest.mockRejectedValue({ code: "not_offered", message: "That passage was not offered as an explorable figure.", retryable: false });
  const pane = await libraryAnswer();
  press(pane, HERE);
  await waitFor(() => expect(api.readerFigureRequest).toHaveBeenCalledWith({
    extractionId: view.extractionId, spanIds: ["span_spectral_worked"], origin: "library", offerRef: "la_1" }));
  await waitFor(() => expect(offerLine(pane, HERE)).not.toContain(LIBRARY_EXPLORABLE_COPY.building));
  expect(offerLine(pane, HERE)).toContain(LIBRARY_EXPLORABLE_COPY.lapsed.not_built);
  expect(pane.querySelector(`[data-library-explorable="${HERE}"]`)).not.toBeNull();
});

it("a press in this book says building until the figure lands, then that it was built", async () => {
  const job = deferred<unknown>();
  api.readerFigureRequest.mockReturnValue(job.promise);
  const pane = await libraryAnswer();
  press(pane, HERE);
  await waitFor(() => expect(api.readerFigureRequest).toHaveBeenCalledTimes(1));
  expect(offerLine(pane, HERE)).toContain(LIBRARY_EXPLORABLE_COPY.building);
  await act(async () => { job.resolve({ jobId: "j1", kind: "figure_build", askId: null, state: "done", result: { figure: figure(), reused: false } }); });
  await waitFor(() => expect(offerLine(pane, HERE)).not.toContain(LIBRARY_EXPLORABLE_COPY.building));
  expect(offerLine(pane, HERE)).toContain(LIBRARY_EXPLORABLE_COPY.built);
});

it("a detour whose book does not open says so, builds nothing, and offers the button again", async () => {
  api.readerRenderView.mockImplementation(({ extractionId }: { extractionId: string }) =>
    extractionId === "src_other" ? Promise.reject({ code: "not_found", message: "That source is gone.", retryable: false }) : Promise.resolve(view));
  const onError = vi.fn();
  const pane = await libraryAnswer(onError);
  press(pane, THERE);
  await waitFor(() => expect(onError).toHaveBeenCalled());
  await waitFor(() => expect(offerLine(pane, THERE)).not.toContain(LIBRARY_EXPLORABLE_COPY.building));
  expect(offerLine(pane, THERE)).toContain(LIBRARY_EXPLORABLE_COPY.lapsed.not_opened);
  expect(pane.querySelector(`[data-library-explorable="${THERE}"]`)).not.toBeNull();
  expect(api.readerFigureRequest).not.toHaveBeenCalled();
});

it("a detour whose book opens after figures went off lapses (it does not build when they come back)", async () => {
  const opened = deferred<unknown>();
  api.readerRenderView.mockImplementation(({ extractionId }: { extractionId: string }) =>
    extractionId === "src_other" ? opened.promise : Promise.resolve(view));
  const pane = await libraryAnswer();
  press(pane, THERE);
  await waitFor(() => expect(api.readerRenderView).toHaveBeenCalledWith({ extractionId: "src_other" }));
  // Figures switched off while the book was opening.
  contract.value = { ...contract.value, figures: undefined };
  const otherView = { ...view, sourceId: "src_other", extractionId: "ext_other" };
  await act(async () => { opened.resolve(otherView); });
  await screen.findByText(view.blocks[1].markdown);
  // Back on: the lapsed press stays lapsed (no build the learner did not see start).
  contract.value = { ...contract.value, figures: FIGURES };
  pane.rerenderPage();
  const again = await screen.findByRole("region", { name: "ask your library" });
  await waitFor(() => expect(again.querySelector(`[data-library-explorable="${THERE}"]`)).not.toBeNull());
  await act(async () => { await new Promise((resolve) => setTimeout(resolve, 20)); });
  expect(api.readerFigureRequest).not.toHaveBeenCalled();
  await waitFor(() => expect(offerLine(again, THERE)).toContain(LIBRARY_EXPLORABLE_COPY.lapsed.figures_off));
});
