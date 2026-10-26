// RW5a on the Reader (spec §8.1, §8.6; UX §4.7, S9; W12, U13): "make this
// explorable" from a selection's palette builds in the background and lands
// inline under its passage; with figures.enabled off (no `figures` in the
// contract) the Reader is as before: no action, no figure RPC, nothing drawn.
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../../ReaderScreen";
import { readerRenderViewFixture as view } from "../../../fixtures/readerRenderView";
import { readerIntentContractFixture as intent } from "../../../fixtures/readerIntentContract";
import type { FigureViewDto, ReaderIntentContractDto, SourceLibraryCard } from "../../../api/dto";
import { resetReaderActivityForTests } from "../activity";
import corpus from "./figureGoldenCorpus.json";

const { api, contract } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerRouteIntent: vi.fn(), readerIntentRouting: vi.fn(), readerIntentOutcome: vi.fn(),
    readerSetMode: vi.fn(),
    readerFigures: vi.fn(), readerFigureRequest: vi.fn(), readerFigureJob: vi.fn(), readerFigureJobCancel: vi.fn(),
    figureRequest: vi.fn(),
  },
  contract: { value: {} as Record<string, unknown> },
}));
vi.mock("../../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? contract.value : { sources: [source.card] }, error: null }) }));
vi.mock("../readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("../guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("../useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const source = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };
const BOX = "What do you want to do with this?";
const FLAGSHIP = corpus.figures.find((item) => item.id === "two_sided_exponential")!.spec;
const anchor = view.blocks[1].spanId as string;

function figure(): FigureViewDto {
  return {
    figureId: "fig_1", extractionId: view.extractionId, spanIds: [anchor], anchorSpanId: anchor, region: null,
    origin: "selection", verification: "illustrative", kind: "illustrative",
    label: "AI-built illustration of an interpretation · not checked against the book", reason: null,
    unsupportedKind: null, supersedesId: null, revisionNote: null, versions: 1, createdAt: "2026-10-21T00:00:00",
    specJson: JSON.stringify(FLAGSHIP), demonstrates: "a demonstration", assumptions: [], predictions: [],
  };
}

/** The intent contract without RW5a's action: the base's palette. */
function withoutFigure(base: ReaderIntentContractDto): ReaderIntentContractDto {
  return { ...base, palette: base.palette.map((group) => ({ ...group, actions: group.actions.filter((action) => action.effect.kind !== "figure") })) };
}

function select(block: HTMLElement): void {
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
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
  api.readerFigures.mockResolvedValue({ extractionId: view.extractionId, figures: [] });
});
afterEach(cleanup);

it("make this explorable runs a build and the figure lands under its passage", async () => {
  contract.value = { readerEnabled: true, inquiryEnabled: true, intent, figures: { predictions: true, region: true, revisions: true } };
  api.readerFigureRequest.mockResolvedValue({ jobId: "ljob_1", kind: "figure_build", askId: null, state: "done", result: { reused: false, figure: figure() } });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  await waitFor(() => expect(api.readerFigures).toHaveBeenCalledWith({ extractionId: view.extractionId }));
  select(block);
  await screen.findByRole("textbox", { name: BOX });
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  fireEvent.click(within(palette).getByRole("button", { name: "show me…" }));
  await waitFor(() => expect(api.readerFigureRequest).toHaveBeenCalledWith({ extractionId: view.extractionId, spanIds: [anchor], region: null }));
  const line = await screen.findByRole("button", { name: /interactive version/ });
  // Inline under its passage: the figure's slot follows the passage's block.
  const slot = line.closest(`[data-figures-under="${anchor}"]`);
  expect(slot).not.toBeNull();
  const passage = document.querySelector(`[data-span-id="${anchor}"]`)!;
  expect(passage.compareDocumentPosition(slot!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
});

it("RW5d P1: show me with words sends the selection and the words jointly (G-SM6)", async () => {
  contract.value = { readerEnabled: true, inquiryEnabled: true, intent,
    figures: { predictions: true, region: true, revisions: true, showMe: true } };
  api.figureRequest.mockResolvedValue({ jobId: "ljob_2", kind: "figure_build", askId: null, state: "done",
    result: { reused: false, figure: { ...figure(), origin: "show_me", goalText: "but with p near 1", goalAuthor: "learner", grounding: "anchor", passages: [] } } });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  select(block);
  const box = await screen.findByRole("textbox", { name: BOX });
  fireEvent.change(box, { target: { value: "but with p near 1" } });
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  fireEvent.click(within(palette).getByRole("button", { name: "show me…" }));
  await waitFor(() => expect(api.figureRequest).toHaveBeenCalledWith({
    goalText: "but with p near 1", origin: "show_me", anchor: { extractionId: view.extractionId, spanIds: [anchor], region: null },
    readingAt: null, offerRef: null,
  }));
  expect(api.readerFigureRequest).not.toHaveBeenCalled();
  // The collapsed line quotes the learner's words, outside the code-owned badge.
  const goal = await screen.findByText("but with p near 1", { selector: "[data-figure-goal] *" });
  expect(goal.closest("[data-figure-badge]")).toBeNull();
});

it("switched off, the Reader has no figure action, calls no figure RPC and draws nothing", async () => {
  contract.value = { readerEnabled: true, inquiryEnabled: true, intent: withoutFigure(intent) };
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  select(block);
  await screen.findByRole("textbox", { name: BOX });
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  expect(within(palette).queryByRole("button", { name: "show me…" })).toBeNull();
  await new Promise((resolve) => setTimeout(resolve, 20));
  for (const name of ["readerFigures", "readerFigureRequest", "readerFigureJob", "readerFigureJobCancel"] as const) {
    expect(api[name]).not.toHaveBeenCalled();
  }
  expect(document.querySelector("[data-figures-under]")).toBeNull();
});
